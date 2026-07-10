from __future__ import annotations

from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from cli.services.loop_orchestration_bundle import bundle_digest, task_input_digest
from cli.services.multi_workgroup_scheduler import (
    MultiWorkgroupScheduler,
    resume_pending_multi_workgroup_scheduler,
)
from cli.services.workgroup_integration import GitIntegrationError


class FakeIntegration:
    def __init__(self, bundle: dict[str, object], root: Path) -> None:
        self.bundle = bundle
        self.root = root
        self.calls: list[object] = []
        self.payload = {
            'status': 'new',
            'nodes': {
                node['node_id']: {
                    'status': 'planned',
                    'worktree_path': str(root / 'worktrees' / node['node_id']),
                    'branch': f'ccb/test/{node["node_id"]}',
                    'base_commit': 'base',
                    'reviewed_commit': None,
                }
                for node in bundle['nodes']
            },
            'integration': {'status': 'planned', 'head': 'base', 'merge_order': []},
            'root': {'promotion': None, 'checks': [], 'rollback': None},
        }

    def preflight(self):
        self.calls.append('preflight')
        return self.payload

    def prepare_integration(self):
        self.calls.append('prepare_integration')
        self.payload['integration']['status'] = 'ready'
        return self.payload

    def prepare_node(self, node_id: str):
        self.calls.append(('prepare_node', node_id))
        path = Path(self.payload['nodes'][node_id]['worktree_path'])
        path.mkdir(parents=True, exist_ok=True)
        self.payload['nodes'][node_id]['status'] = (
            self.payload['nodes'][node_id]['status']
            if self.payload['nodes'][node_id]['status'] != 'planned'
            else 'prepared'
        )
        return self.payload

    def capture_review_input(self, node_id: str, *, worker_job_id: str):
        self.calls.append(('capture_review_input', node_id, worker_job_id))
        return {
            'input_digest': f'sha256:input-{node_id}',
            'tree_digest': f'git-tree:sha1:{node_id}',
        }

    def record_review(self, node_id: str, **kwargs):
        self.calls.append(('record_review', node_id, kwargs['reviewer_job_id']))
        self.payload['nodes'][node_id]['status'] = 'review_passed'
        return kwargs

    def finalize_node(self, node_id: str):
        self.calls.append(('finalize_node', node_id))
        commit = f'commit-{node_id}'
        self.payload['nodes'][node_id]['status'] = 'integration_ready'
        self.payload['nodes'][node_id]['reviewed_commit'] = commit
        return {**self.payload['nodes'][node_id], 'reviewed_commit': commit}

    def integrate_ready(self):
        self.calls.append('integrate_ready')
        changed = True
        while changed:
            changed = False
            for node in self.bundle['nodes']:
                record = self.payload['nodes'][node['node_id']]
                if record['status'] != 'integration_ready':
                    continue
                if not all(
                    self.payload['nodes'][dep]['status'] == 'integrated'
                    for dep in node['depends_on']
                ):
                    continue
                record['status'] = 'integrated'
                self.payload['integration']['merge_order'].append(node['node_id'])
                changed = True
        if all(record['status'] == 'integrated' for record in self.payload['nodes'].values()):
            self.payload['integration']['status'] = 'verified'
        return self.payload

    def promote(self):
        self.calls.append('promote')
        self.payload['root']['promotion'] = {'status': 'applied'}
        return self.payload

    def verify_root(self):
        self.calls.append('verify_root')
        self.payload['root']['checks'] = [{'status': 'pass'}]
        return self.payload

    def accept(self):
        self.calls.append('accept')
        self.payload['status'] = 'accepted'
        return self.payload

    def rollback(self, *, reason: str):
        self.calls.append(('rollback', reason))
        self.payload['status'] = 'rolled_back'
        self.payload['root']['rollback'] = {'status': 'restored', 'reason': reason}
        return self.payload

    def close_without_promotion(self, *, result: str, reason: str):
        self.calls.append(('close_without_promotion', result, reason))
        self.payload['status'] = 'replan_required' if result == 'replan_required' else 'integration_failed'
        self.payload['closure'] = {'result': result, 'reason': reason}
        return self.payload

    def cleanup_readiness(self, *, evidence_captured: bool, active_workspaces):
        active = tuple(active_workspaces)
        self.calls.append(('cleanup_readiness', evidence_captured, active))
        return {'eligible': evidence_captured and not active, 'reason': 'eligible' if not active else 'active'}

    def cleanup(self, *, active_workspaces):
        active = tuple(active_workspaces)
        self.calls.append(('cleanup', active))
        return {'status': 'complete', 'active_workspaces': list(active)}

    def state(self):
        return self.payload


class Harness:
    def __init__(self, root: Path, bundle: dict[str, object], integration: FakeIntegration) -> None:
        self.root = root
        self.bundle = bundle
        self.integration = integration
        self.jobs: dict[tuple[str, str], dict[str, object]] = {}
        self.submissions: list[tuple[str, str]] = []
        self.bindings: list[dict[str, object]] = []
        self.imports: list[object] = []
        self.release = {'released_count': len(bundle['nodes']) * 2 + 1, 'retained_count': 0}
        self.observed_agents: list[dict[str, object]] = []
        self.current_capacity_digest = str(bundle['capacity_digest'])
        self.apply_status = 'ready'
        self.submit_failures: set[tuple[str, str]] = set()

    def services(self):
        return SimpleNamespace(
            workgroup_integration_factory=lambda _scheduler: self.integration,
            compile_workgroup_mount_demand=self.compile_demand,
            apply_workgroup_topology=lambda *_args: {'loop_topology_status': self.apply_status},
            release_workgroup_topology=lambda *_args: dict(self.release),
            workgroup_topology_status=lambda *_args: {'observed': {'agents': list(self.observed_agents)}},
            bind_workgroup_workspace=self.bind_workspace,
            submit_or_recover_ask_once=self.submit,
            plan_task=self.plan_task,
            task_text=lambda *_args: 'task execution evidence',
            workgroup_capacity_digest=lambda _context: self.current_capacity_digest,
        )

    def compile_demand(self, _root, bundle, *, active_node_ids, control_profiles=(), **_kwargs):
        active = list(active_node_ids)
        bindings = [
            {
                'node_id': node_id,
                'workgroup_id': f'wg-{node_id}',
                'attempt': 1,
                'workspace_group': f'compact-{node_id}',
                'worker_profile': 'coder',
                'reviewer_profile': 'code_reviewer',
                'worker_agent': f'compact-{node_id}-worker',
                'reviewer_agent': f'compact-{node_id}-reviewer',
                'window_name': 'ccb-exec',
                'pane_orders': {'coder': 0, 'code_reviewer': 1},
            }
            for node_id in active
        ]
        controls = (
            [{'profile': 'ccb_round_reviewer', 'agent': 'compact-round-reviewer'}]
            if control_profiles
            else []
        )
        return {
            'bindings': bindings,
            'control_bindings': controls,
            'mount_topology': {
                'schema': 'ccb.loop.agent_mount_topology.v1',
                'nodes': active,
                'controls': list(control_profiles),
            },
        }

    def bind_workspace(self, _context, **kwargs):
        self.bindings.append(kwargs)

    def submit(self, _context, *, target: str, purpose: str, node_id: str, **_kwargs):
        key = (node_id, purpose)
        if key not in self.jobs:
            self.submissions.append(key)
            self.jobs[key] = {
                'target': target,
                'purpose': purpose,
                'job_id': f'job-{node_id}-{purpose}',
                'status': 'running',
                'terminal': False,
                'reply': '',
            }
            if key in self.submit_failures:
                self.jobs[key].update(status='failed', terminal=True)
        return dict(self.jobs[key])

    def complete(self, node_id: str, purpose: str, *, reply: str = 'done', status: str = 'completed'):
        self.jobs[(node_id, purpose)].update(status=status, terminal=True, reply=reply)

    def plan_task(self, _context, command):
        assert command.action == 'task-import-round'
        self.imports.append(command)
        return {'status': 'done' if command.result == 'pass' else command.result, 'result': command.result}


def _record(root: Path) -> dict[str, object]:
    artifact = root / 'execution-contract.md'
    artifact.write_text('# Execution Contract\n\nVerification:\n- python -m unittest\n', encoding='utf-8')
    return {
        'task_id': 'task-g3',
        'task_revision': 1,
        'artifacts': {
            'task_packet': {'path': 'execution-contract.md', 'sha256': 'a'},
            'execution_contract': {'path': 'execution-contract.md', 'sha256': 'b'},
        },
    }


def _bundle(record: dict[str, object], count: int, *, mixed: bool = False) -> dict[str, object]:
    nodes = []
    for index in range(1, count + 1):
        node_id = f'node-{index:03d}'
        depends = ['node-001'] if mixed and index == 3 else []
        nodes.append(
            {
                'node_id': node_id,
                'workgroup_id': f'wg-{index:03d}',
                'worker_profile': 'coder',
                'reviewer_profile': 'code_reviewer',
                'depends_on': depends,
                'parallel_group': 'wave-2' if depends else 'wave-1',
                'work_packet_ref': 'execution-contract.md',
                'allowed_paths': [f'parts/{index}/'],
                'acceptance_refs': ['execution-contract.md'],
                'verification_refs': ['execution-contract.md'],
                'integration_order': index * 10,
            }
        )
    return {
        'schema': 'ccb.loop.orchestration_bundle.v1',
        'task_id': record['task_id'],
        'task_revision': 1,
        'task_digest': task_input_digest(record),
        'capacity_digest': 'sha256:' + ('c' * 64),
        'bundle_revision': 1,
        'selection': {
            'workgroup_count': count,
            'complexity': 'bounded',
            'cutability': 'high',
            'execution_shape': 'mixed_dag' if mixed else 'parallel',
            'rationale': 'bounded workgroups',
        },
        'nodes': nodes,
        'integration': {
            'verification_refs': ['execution-contract.md'],
            'project_root_verification_refs': ['execution-contract.md'],
        },
        'policy': {
            'max_node_rework_rounds': 1,
            'on_required_node_failure': 'partial_or_blocked',
            'on_structural_failure': 'replan_required',
        },
    }


def _scheduler(tmp_path: Path, count: int, *, mixed: bool = False):
    root = tmp_path / 'repo'
    root.mkdir()
    record = _record(root)
    bundle = _bundle(record, count, mixed=mixed)
    integration = FakeIntegration(bundle, root)
    harness = Harness(root, bundle, integration)
    context = SimpleNamespace(
        project=SimpleNamespace(project_root=root, project_id='project-g3'),
    )
    scheduler = MultiWorkgroupScheduler(
        context,
        loop_id='loop-g3',
        task_record=record,
        bundle=bundle,
        bundle_artifact={'bundle_digest': bundle_digest(bundle)},
        services=harness.services(),
    )
    return scheduler, harness, integration


@pytest.mark.parametrize('count', (1, 2, 3, 4))
def test_scheduler_submits_entire_ready_frontier_before_any_reviewer(tmp_path: Path, count: int) -> None:
    scheduler, harness, _integration = _scheduler(tmp_path, count)

    result = scheduler.run_once()

    expected = [(f'node-{index:03d}', 'worker') for index in range(1, count + 1)]
    assert harness.submissions == expected
    assert result['scheduler_action'] == 'submitted_ready_frontier'
    assert result['loop_runner_status'] == 'pending'
    assert all(node['worker_agent'].startswith('compact-') for node in result['nodes'].values())
    assert not any(purpose.startswith('reviewer') for _node_id, purpose in harness.submissions)
    assert {item['workspace_group'] for item in harness.bindings} == {
        f'compact-node-{index:03d}' for index in range(1, count + 1)
    }


def test_scheduler_orders_review_integration_round_release_and_cleanup(tmp_path: Path) -> None:
    scheduler, harness, integration = _scheduler(tmp_path, 2)
    scheduler.run_once()
    for node_id in ('node-001', 'node-002'):
        harness.complete(node_id, 'worker')

    pending_review = scheduler.run_once()
    assert harness.submissions[-2:] == [('node-001', 'reviewer'), ('node-002', 'reviewer')]
    assert pending_review['loop_runner_status'] == 'pending'
    for node_id in ('node-001', 'node-002'):
        harness.complete(node_id, 'reviewer', reply='status: pass')

    pending_round = scheduler.run_once()
    assert ('round', 'ccb_round_reviewer') in harness.submissions
    assert pending_round['controller_status'] == 'round_review_pending'
    harness.complete('round', 'ccb_round_reviewer', reply='round_result: pass')

    final = scheduler.run_once()

    assert final['round_result'] == 'pass'
    assert final['controller_status'] == 'pass'
    assert final['task_status'] == 'done'
    assert integration.payload['integration']['merge_order'] == ['node-001', 'node-002']
    assert integration.calls.index('promote') < integration.calls.index('verify_root') < integration.calls.index('accept')
    assert any(call[0] == 'cleanup_readiness' and call[2] == () for call in integration.calls if isinstance(call, tuple))
    assert ('cleanup', ()) in integration.calls


def test_mixed_dag_unblocks_dependent_while_independent_sibling_is_pending(tmp_path: Path) -> None:
    scheduler, harness, integration = _scheduler(tmp_path, 3, mixed=True)
    scheduler.run_once()
    assert harness.submissions == [('node-001', 'worker'), ('node-002', 'worker')]
    harness.complete('node-001', 'worker')
    scheduler.run_once()
    harness.complete('node-001', 'reviewer', reply='status: pass')

    result = scheduler.run_once()

    assert ('node-003', 'worker') in harness.submissions
    assert not harness.jobs[('node-002', 'worker')]['terminal']
    assert result['loop_runner_status'] == 'pending'
    assert integration.payload['nodes']['node-001']['status'] == 'integrated'


def test_bounded_rework_stays_on_same_compacted_agents_and_worktree(tmp_path: Path) -> None:
    scheduler, harness, _integration = _scheduler(tmp_path, 1)
    scheduler.run_once()
    harness.complete('node-001', 'worker')
    scheduler.run_once()
    harness.complete('node-001', 'reviewer', reply='status: rework_required')

    scheduler.run_once()

    assert harness.submissions[-1] == ('node-001', 'worker_rework')
    state = scheduler.run_once()['nodes']['node-001']
    assert state['worker_agent'] == 'compact-node-001-worker'
    assert state['worktree_path'].endswith('/worktrees/node-001')


def test_busy_release_passes_latest_active_workspaces_and_blocks_cleanup(tmp_path: Path) -> None:
    scheduler, harness, integration = _scheduler(tmp_path, 1)
    scheduler.run_once()
    harness.complete('node-001', 'worker')
    scheduler.run_once()
    harness.complete('node-001', 'reviewer', reply='status: pass')
    scheduler.run_once()
    harness.complete('round', 'ccb_round_reviewer', reply='round_result: pass')
    harness.release = {'released_count': 2, 'retained_count': 1}
    harness.observed_agents = [
        {'id': 'compact-node-001-worker', 'observed_state': 'present'},
    ]

    result = scheduler.run_once()

    worktree = Path(integration.payload['nodes']['node-001']['worktree_path'])
    assert result['controller_status'] == 'release_blocked'
    assert result['loop_runner_status'] == 'pending'
    assert ('cleanup_readiness', True, (worktree,)) in integration.calls
    assert not any(call[0] == 'cleanup' for call in integration.calls if isinstance(call, tuple))

    harness.release = {'released_count': 1, 'retained_count': 0}
    harness.observed_agents = []
    retried = scheduler.run_once()

    assert retried['controller_status'] == 'pass'
    assert ('cleanup', ()) in integration.calls


def test_result_import_crash_resumes_release_without_second_import(tmp_path: Path) -> None:
    scheduler, harness, integration = _scheduler(tmp_path, 1)
    scheduler.run_once()
    harness.complete('node-001', 'worker')
    scheduler.run_once()
    harness.complete('node-001', 'reviewer', reply='status: pass')
    scheduler.run_once()
    harness.complete('round', 'ccb_round_reviewer', reply='round_result: pass')
    fired = False

    def crash(name: str, _state: dict[str, object]) -> None:
        nonlocal fired
        if name == 'after_result_import' and not fired:
            fired = True
            raise RuntimeError('crash:after-result-import')

    scheduler._checkpoint_hook = crash
    with pytest.raises(RuntimeError, match='crash:after-result-import'):
        scheduler.run_once()
    assert len(harness.imports) == 1

    resume_services = harness.services()

    def resume_plan_task(context, command):
        if command.action == 'task-show':
            return {'task': scheduler.task_record}
        return harness.plan_task(context, command)

    resume_services.plan_task = resume_plan_task
    final = resume_pending_multi_workgroup_scheduler(
        scheduler.context,
        services=resume_services,
    )

    assert len(harness.imports) == 1
    assert final is not None
    assert final['controller_status'] == 'pass'
    assert ('cleanup', ()) in integration.calls


def test_cleanup_intent_crash_resumes_without_rechecking_readiness(tmp_path: Path) -> None:
    scheduler, harness, integration = _scheduler(tmp_path, 1)
    scheduler.run_once()
    harness.complete('node-001', 'worker')
    scheduler.run_once()
    harness.complete('node-001', 'reviewer', reply='status: pass')
    scheduler.run_once()
    harness.complete('round', 'ccb_round_reviewer', reply='round_result: pass')

    def crash(name: str, _state: dict[str, object]) -> None:
        if name == 'after_result_import':
            raise RuntimeError('crash:before-cleanup')

    scheduler._checkpoint_hook = crash
    with pytest.raises(RuntimeError, match='crash:before-cleanup'):
        scheduler.run_once()
    integration.payload['cleanup'] = {
        'schema': 'ccb.loop.workgroup_cleanup_intent.v1',
        'status': 'executing',
    }
    services = harness.services()

    def resume_plan_task(context, command):
        if command.action == 'task-show':
            return {'task': scheduler.task_record}
        return harness.plan_task(context, command)

    services.plan_task = resume_plan_task
    final = resume_pending_multi_workgroup_scheduler(
        scheduler.context,
        services=services,
    )

    assert final is not None
    assert final['controller_status'] == 'pass'
    assert not any(
        call[0] == 'cleanup_readiness'
        for call in integration.calls
        if isinstance(call, tuple)
    )
    assert ('cleanup', ()) in integration.calls


def test_scheduler_uses_real_r2_worktrees_commits_merge_promotion_and_cleanup(tmp_path: Path) -> None:
    root = tmp_path / 'real-repo'
    root.mkdir()
    record = _record(root)
    (root / '.gitignore').write_text('.ccb/\n', encoding='utf-8')
    _git(root, 'init')
    _git(root, 'config', 'user.name', 'Test User')
    _git(root, 'config', 'user.email', 'test@example.com')
    _git(root, 'add', '.')
    _git(root, 'commit', '-m', 'base')
    bundle = _bundle(record, 2)
    harness = Harness(root, bundle, FakeIntegration(bundle, root))
    services = harness.services()
    delattr(services, 'workgroup_integration_factory')
    context = SimpleNamespace(project=SimpleNamespace(project_root=root, project_id='project-real-r2'))
    scheduler = MultiWorkgroupScheduler(
        context,
        loop_id='loop-real-r2',
        task_record=record,
        bundle=bundle,
        bundle_artifact={'bundle_digest': bundle_digest(bundle)},
        services=services,
    )
    scheduler.run_once()
    state = scheduler.run_once()['nodes']
    for index, node_id in enumerate(('node-001', 'node-002'), start=1):
        path = Path(state[node_id]['worktree_path']) / f'parts/{index}/result.txt'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f'{node_id}\n', encoding='utf-8')
        harness.complete(node_id, 'worker')
    scheduler.run_once()
    for node_id in ('node-001', 'node-002'):
        harness.complete(node_id, 'reviewer', reply='status: pass')
    scheduler.run_once()
    harness.complete('round', 'ccb_round_reviewer', reply='round_result: pass')

    final = scheduler.run_once()

    assert final['controller_status'] == 'pass'
    assert (root / 'parts/1/result.txt').read_text(encoding='utf-8') == 'node-001\n'
    assert (root / 'parts/2/result.txt').read_text(encoding='utf-8') == 'node-002\n'
    integration_state = final['paths']['integration_state']
    assert Path(integration_state).is_file()
    assert final['cleanup']['result']['status'] == 'complete'
    assert len(final['cleanup']['removed_workspace_bindings']) == 2
    assert all(
        not Path(path).exists()
        for path in final['cleanup']['removed_workspace_bindings']
    )
    assert _git(root, 'status', '--porcelain') == ''


def test_malformed_round_review_rolls_back_and_imports_replan(tmp_path: Path) -> None:
    scheduler, harness, integration = _scheduler(tmp_path, 1)
    scheduler.run_once()
    harness.complete('node-001', 'worker')
    scheduler.run_once()
    harness.complete('node-001', 'reviewer', reply='status: pass')
    scheduler.run_once()
    harness.complete('round', 'ccb_round_reviewer', reply='looks good')

    final = scheduler.run_once()

    assert final['round_result'] == 'replan_required'
    assert ('rollback', 'round_reviewer:replan_required') in integration.calls
    assert harness.imports[-1].result == 'replan_required'


def test_capacity_drift_replans_without_submitting_more_provider_jobs(tmp_path: Path) -> None:
    scheduler, harness, integration = _scheduler(tmp_path, 2)
    scheduler.run_once()
    submitted = list(harness.submissions)
    harness.current_capacity_digest = 'sha256:' + ('d' * 64)

    result = scheduler.run_once()

    assert result['round_result'] == 'replan_required'
    assert result['round_result_source'] == 'scheduler_contract_invalid'
    assert harness.submissions == submitted
    assert ('close_without_promotion', 'replan_required', 'scheduler_contract_invalid') in integration.calls


def test_busy_topology_apply_remains_pending_and_retries_without_provider_submit(tmp_path: Path) -> None:
    scheduler, harness, _integration = _scheduler(tmp_path, 2)
    harness.apply_status = 'retained_busy'

    pending = scheduler.run_once()

    assert pending['controller_status'] == 'topology_pending'
    assert harness.submissions == []
    harness.apply_status = 'ready'
    resumed = scheduler.run_once()

    assert resumed['scheduler_action'] == 'submitted_ready_frontier'
    assert harness.submissions == [('node-001', 'worker'), ('node-002', 'worker')]


def test_scheduler_state_before_git_preflight_crash_replays_initialization(tmp_path: Path) -> None:
    scheduler, harness, integration = _scheduler(tmp_path, 2)
    fired = False

    def crash(name: str, _state: dict[str, object]) -> None:
        nonlocal fired
        if name == 'after_scheduler_state_before_git_preflight' and not fired:
            fired = True
            raise RuntimeError('crash:before-git-preflight')

    scheduler._checkpoint_hook = crash
    with pytest.raises(RuntimeError, match='crash:before-git-preflight'):
        scheduler.run_once()
    assert scheduler.state_path.is_file()
    assert integration.calls == []

    replay = MultiWorkgroupScheduler(
        scheduler.context,
        loop_id=scheduler.loop_id,
        task_record=scheduler.task_record,
        bundle=scheduler.bundle,
        bundle_artifact=scheduler.bundle_artifact,
        services=harness.services(),
    )
    result = replay.run_once()

    assert result['scheduler_action'] == 'submitted_ready_frontier'
    assert integration.calls[:2] == ['preflight', 'prepare_integration']


def test_one_frontier_submission_failure_does_not_hide_or_serialize_sibling_submit(
    tmp_path: Path,
) -> None:
    scheduler, harness, _integration = _scheduler(tmp_path, 2)
    harness.submit_failures.add(('node-001', 'worker'))

    result = scheduler.run_once()

    assert harness.submissions == [('node-001', 'worker'), ('node-002', 'worker')]
    assert result['nodes']['node-001']['status'] == 'worker_failed'
    assert result['nodes']['node-002']['status'] == 'worker_pending'


def test_rework_cycle_rechecks_same_tree_then_completes(tmp_path: Path) -> None:
    scheduler, harness, _integration = _scheduler(tmp_path, 1)
    scheduler.run_once()
    harness.complete('node-001', 'worker')
    scheduler.run_once()
    harness.complete('node-001', 'reviewer', reply='status: rework_required')
    scheduler.run_once()
    harness.complete('node-001', 'worker_rework')
    scheduler.run_once()
    assert harness.submissions[-1] == ('node-001', 'reviewer_recheck')
    harness.complete('node-001', 'reviewer_recheck', reply='status: pass')
    scheduler.run_once()
    harness.complete('round', 'ccb_round_reviewer', reply='round_result: pass')

    final = scheduler.run_once()

    assert final['round_result'] == 'pass'
    assert final['nodes']['node-001']['reviewed_commit'] == 'commit-node-001'


def test_independent_worker_failure_preserves_reviewed_sibling_as_partial(tmp_path: Path) -> None:
    scheduler, harness, integration = _scheduler(tmp_path, 2)
    scheduler.run_once()
    harness.complete('node-001', 'worker')
    harness.complete('node-002', 'worker', status='failed')
    scheduler.run_once()
    harness.complete('node-001', 'reviewer', reply='status: pass')

    final = scheduler.run_once()

    assert final['round_result'] == 'partial'
    assert final['nodes']['node-001']['status'] == 'integrated'
    assert final['nodes']['node-002']['status'] == 'worker_failed'
    assert integration.payload['root']['promotion'] is None


def test_structural_integration_failure_imports_replan_without_promotion(tmp_path: Path) -> None:
    scheduler, harness, integration = _scheduler(tmp_path, 1)
    scheduler.run_once()
    harness.complete('node-001', 'worker')
    scheduler.run_once()
    harness.complete('node-001', 'reviewer', reply='status: pass')

    def fail_integration():
        raise GitIntegrationError(
            'integration_merge_conflict',
            'integration.merge.node-001',
            'conflict',
        )

    integration.integrate_ready = fail_integration
    final = scheduler.run_once()

    assert final['round_result'] == 'replan_required'
    assert final['round_result_source'] == 'integration_merge_conflict'
    assert integration.payload['root']['promotion'] is None


def test_reviewer_pass_and_promotion_crash_windows_replay_without_duplicate_import(
    tmp_path: Path,
) -> None:
    scheduler, harness, integration = _scheduler(tmp_path, 1)
    scheduler.run_once()
    harness.complete('node-001', 'worker')
    scheduler.run_once()
    harness.complete('node-001', 'reviewer', reply='status: pass')
    fired_review = False

    def crash_review(name: str, _state: dict[str, object]) -> None:
        nonlocal fired_review
        if name == 'after_reviewer_pass_before_node_commit' and not fired_review:
            fired_review = True
            raise RuntimeError('crash:review-pass')

    scheduler._checkpoint_hook = crash_review
    with pytest.raises(RuntimeError, match='crash:review-pass'):
        scheduler.run_once()
    scheduler._checkpoint_hook = None
    fired_promotion = False

    def crash_promotion(name: str, _state: dict[str, object]) -> None:
        nonlocal fired_promotion
        if name == 'after_root_promotion_before_verification' and not fired_promotion:
            fired_promotion = True
            raise RuntimeError('crash:promotion')

    scheduler._checkpoint_hook = crash_promotion
    with pytest.raises(RuntimeError, match='crash:promotion'):
        scheduler.run_once()
    scheduler._checkpoint_hook = None
    scheduler.run_once()
    harness.complete('round', 'ccb_round_reviewer', reply='round_result: pass')

    final = scheduler.run_once()

    assert final['round_result'] == 'pass'
    assert len(harness.imports) == 1
    assert integration.calls.count(('finalize_node', 'node-001')) == 1


def _git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ['git', '-C', str(cwd), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout.strip()
