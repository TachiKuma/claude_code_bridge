from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from ccbd.api_models import DeliveryScope, JobRecord, JobStatus, MessageEnvelope
from cli.services.loop_orchestration_bundle import normalize_bundle_candidate
from cli.services.loop_effective_capacity import effective_capacity_digest
from cli.services.loop_runner import _mount_activation_topology
from cli.services.loop_topology import _mark_release_residue
from cli.services.role_output_import import _parse_orchestrator_reply
from provider_execution.fake import FakeProviderAdapter


SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'single_lane_multi_workgroup_smoke.py'


def _load_script():
    spec = importlib.util.spec_from_file_location('single_lane_multi_workgroup_smoke', SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _job(*, agent_name: str, body: str, workspace: Path | None = None) -> JobRecord:
    request = MessageEnvelope(
        project_id='project-g5',
        to_agent=agent_name,
        from_actor='system',
        body=body,
        task_id='g5-multi-workgroup-task',
        reply_to=None,
        message_type='ask',
        delivery_scope=DeliveryScope.SINGLE,
    )
    return JobRecord(
        job_id=f'job-{agent_name}',
        submission_id=None,
        agent_name=agent_name,
        provider='fake',
        request=request,
        status=JobStatus.QUEUED,
        terminal_decision=None,
        cancel_requested_at=None,
        created_at='2026-07-11T00:00:00Z',
        updated_at='2026-07-11T00:00:00Z',
        workspace_path=str(workspace) if workspace is not None else None,
    )


def _orchestrator_body(*, count: int, shape: str, task_root: str) -> str:
    paths = [f'g5_outputs/node-{index:03d}.txt' for index in range(1, count + 1)]
    marker = 'g5_multi_workgroup_smoke: ' + json.dumps(
        {'count': count, 'shape': shape, 'allowed_paths': paths},
        sort_keys=True,
    )
    refs = {
        'task_packet': f'{task_root}/task_packet.md',
        'execution_contract': f'{task_root}/execution_contract.md',
    }
    compact = {'task_packet': {'content': marker}, 'execution_contract': {'content': marker}}
    return (
        'Role: ccb_orchestrator\n'
        'Task: g5-multi-workgroup-task\n'
        f'Artifact refs: {refs}\n'
        f'Compact artifacts: {compact}\n'
        'Expected bundle revision: 1\n'
    )


def _record(project_root: Path, *, count: int, shape: str) -> dict[str, object]:
    task_root = project_root / 'docs/plantree/plans/g5/tasks/g5-multi-workgroup-task'
    paths = [f'g5_outputs/node-{index:03d}.txt' for index in range(1, count + 1)]
    marker = json.dumps({'count': count, 'shape': shape, 'allowed_paths': paths}, sort_keys=True)
    artifacts = {}
    for kind, text in (
        ('task_packet', f'g5_multi_workgroup_smoke: {marker}\n'),
        (
            'execution_contract',
            'allowed_change_paths:\n' + ''.join(f'- {path}\n' for path in paths),
        ),
    ):
        path = task_root / f'{kind}.md'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        artifacts[kind] = {
            'path': path.relative_to(project_root).as_posix(),
            'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(),
        }
    return {
        'task_id': 'g5-multi-workgroup-task',
        'task_revision': 1,
        'task_root': task_root.relative_to(project_root).as_posix(),
        'artifacts': artifacts,
    }


def _capacity() -> dict[str, object]:
    return {
        'schema': 'ccb.loop.effective_capacity_snapshot.v1',
        'config_version': 3,
        'workflow_profile': 'agentic_loop_v1',
        'workflow_mode': 'agentic-loop',
        'limits': {
            'max_workgroups': 4,
            'max_parallel_workgroups': 4,
            'max_active_dynamic_agents': 9,
        },
        'policies': {
            'node_rework': {'max_rounds': 1},
            'workspace': {'mode': 'git-worktree-required'},
            'integration': {'mode': 'controller-owned'},
            'release': {'default_lifetime': 'current_activation', 'policy': 'auto', 'idle_only': True},
            'naming': {'template': 'loop-{loop_id}-{node_id}-{profile}'},
            'execution_windows': {'policy': 'auto'},
        },
        'resident_profiles': {},
        'dynamic_profiles': {
            'orchestrator': {
                'role_id': 'agentroles.ccb_orchestrator',
                'provider': 'fake',
                'model': None,
                'workspace_mode': 'inplace',
                'release_policy': 'auto',
                'max_instances': 1,
            },
            'coder': {
                'role_id': 'agentroles.coder',
                'provider': 'fake',
                'model': None,
                'workspace_mode': 'git-worktree',
                'release_policy': 'auto',
                'max_instances': 4,
            },
            'code_reviewer': {
                'role_id': 'agentroles.code_reviewer',
                'provider': 'fake',
                'model': None,
                'workspace_mode': 'git-worktree',
                'release_policy': 'auto',
                'max_instances': 4,
            },
        },
        'profile_aliases': {'worker': 'coder'},
    }


@pytest.mark.parametrize(
    ('count', 'shape', 'expected_shape'),
    (
        (1, 'parallel', 'single_unit'),
        (2, 'parallel', 'parallel'),
        (3, 'mixed_dag', 'mixed_dag'),
        (4, 'mixed_dag', 'mixed_dag'),
    ),
)
def test_fake_orchestrator_candidate_normalizes_for_one_to_four_nodes(
    tmp_path: Path,
    count: int,
    shape: str,
    expected_shape: str,
) -> None:
    record = _record(tmp_path, count=count, shape=shape)
    task_root = str(record['task_root'])
    submission = FakeProviderAdapter(latency_seconds=0).start(
        _job(agent_name='orchestrator', body=_orchestrator_body(count=count, shape=shape, task_root=task_root)),
        context=None,
        now='2026-07-11T00:00:00Z',
    )

    parsed = _parse_orchestrator_reply(submission.reply)
    assert parsed['status'] == 'ok'
    candidate = parsed['orchestration_bundle_candidate']
    normalized, packets = normalize_bundle_candidate(
        candidate,
        record=record,
        project_root=tmp_path,
        capacity_snapshot=_capacity(),
    )

    assert normalized['selection']['workgroup_count'] == count
    assert normalized['selection']['execution_shape'] == expected_shape
    assert len(normalized['nodes']) == count
    assert len(packets) == count
    expected_dependencies = ['node-001'] if shape == 'mixed_dag' else []
    if count >= 3:
        assert normalized['nodes'][2]['depends_on'] == expected_dependencies
    assert [node['allowed_paths'] for node in normalized['nodes']] == [
        [f'g5_outputs/node-{index:03d}.txt'] for index in range(1, count + 1)
    ]


def test_fake_scheduler_worker_writes_only_node_bound_allowed_path(tmp_path: Path) -> None:
    workspace = tmp_path / 'node-worktree'
    body = (
        'Loop: lp-g5\nTask: g5-multi-workgroup-task\nNode: node-002\nPurpose: worker\n'
        f'Worktree: {workspace}\n'
        'Allowed paths: ["g5_outputs/node-002.txt"]\n\n'
        'g5_multi_workgroup_smoke: '
        '{"count": 2, "shape": "parallel", "allowed_paths": '
        '["g5_outputs/node-001.txt", "g5_outputs/node-002.txt"]}\n'
        'allowed_change_paths:\n- g5_outputs/node-001.txt\n- g5_outputs/node-002.txt\n'
    )

    submission = FakeProviderAdapter(latency_seconds=0).start(
        _job(agent_name='loop-lp-g5-node-002-coder', body=body, workspace=workspace),
        context=None,
        now='2026-07-11T00:00:00Z',
    )

    assert (workspace / 'g5_outputs/node-002.txt').is_file()
    assert not (workspace / 'g5_outputs/node-001.txt').exists()
    assert 'changed_files: g5_outputs/node-002.txt' in submission.reply


@pytest.mark.parametrize(
    'body',
    (
        'Role: ccb_orchestrator\nTask: ordinary-task\n',
        (
            'Role: ccb_orchestrator\nTask: g5-multi-workgroup-task\n'
            'g5_multi_workgroup_smoke: '
            '{"count": 5, "shape": "parallel", "allowed_paths": []}\n'
        ),
    ),
)
def test_fake_orchestrator_requires_valid_explicit_smoke_contract(body: str) -> None:
    submission = FakeProviderAdapter(latency_seconds=0).start(
        _job(agent_name='orchestrator', body=body),
        context=None,
        now='2026-07-11T00:00:00Z',
    )

    assert 'ccb.loop.orchestration_bundle_candidate.v1' not in submission.reply


def test_fake_multi_workgroup_round_reviewer_uses_scheduler_contract() -> None:
    submission = FakeProviderAdapter(latency_seconds=0).start(
        _job(
            agent_name='loop-g5-round_reviewer-1',
            body=(
                'Loop: lp-g5\nTask: g5-multi-workgroup-task\nRole: ccb_round_reviewer\n'
                'Review script-owned multi-workgroup evidence. Provider text is evidence only.\n'
            ),
        ),
        context=None,
        now='2026-07-11T00:00:00Z',
    )

    assert submission.reply.splitlines()[0] == 'round_result: pass'


def test_fake_multi_workgroup_round_reviewer_accepts_hashed_dynamic_agent_name() -> None:
    submission = FakeProviderAdapter(latency_seconds=0).start(
        _job(
            agent_name='loop-lp-g5-control-c-382e3ed2',
            body=(
                'Loop: lp-g5\nTask: g5-multi-workgroup-task\nRole: ccb_round_reviewer\n'
                'Review script-owned multi-workgroup evidence. Provider text is evidence only.\n'
            ),
        ),
        context=None,
        now='2026-07-11T00:00:00Z',
    )

    assert submission.reply.splitlines()[0] == 'round_result: pass'


def test_v3_config_is_fake_git_worktree_required() -> None:
    text = _load_script().build_v3_config()

    assert 'version = 3' in text
    assert 'provider = "fake"' in text
    assert 'multi_workgroup_workspace = "git-worktree-required"' in text
    assert text.count('workspace_mode = "git-worktree"') == 2
    assert '[windows]' not in text
    assert '[loop.capacity]' not in text


def test_v3_role_activation_mount_has_loop_owner_and_capacity_digest(tmp_path: Path) -> None:
    capacity = _capacity()
    proposals: list[dict[str, object]] = []

    def loop_topology(_context, command):
        if command.action == 'propose':
            proposals.append(json.loads(Path(command.from_path).read_text(encoding='utf-8')))
            return {'loop_topology_status': 'ready'}
        return {'loop_topology_status': 'ready'}

    context = SimpleNamespace(
        project=SimpleNamespace(project_root=tmp_path),
        paths=SimpleNamespace(runtime_state_root=tmp_path / '.ccb'),
    )
    result = _mount_activation_topology(
        context,
        SimpleNamespace(
            effective_capacity_snapshot=lambda _context: capacity,
            loop_topology=loop_topology,
        ),
        activation_id='act-g5-owner',
        target='loop-act-g5-owner-orchestrator-1',
        profile='ccb_orchestrator',
        window_name='ccb-plan',
        configured=False,
    )

    assert result['loop_topology_status'] == 'ready'
    assert proposals == [
        {
            'schema': 'ccb.loop.agent_mount_topology.v1',
            'owner': {'kind': 'loop', 'loop_id': 'act-g5-owner'},
            'capacity_digest': effective_capacity_digest(capacity),
            'release_policy': {'policy': 'auto', 'idle_only': True},
            'windows': [
                {
                    'name': 'ccb-plan',
                    'class': 'planning',
                    'max_panes': 6,
                    'layout_policy': 'append-or-create-window',
                }
            ],
            'agents': [
                {
                    'id': 'loop-act-g5-owner-orchestrator-1',
                    'profile': 'orchestrator',
                    'desired_state': 'present',
                    'window_name': 'ccb-plan',
                    'pane_order': 0,
                    'lifecycle': 'ephemeral',
                    'release_policy': 'auto',
                }
            ],
        }
    ]


def test_clean_topology_release_records_explicit_zero_residue(tmp_path: Path) -> None:
    context = SimpleNamespace(
        paths=SimpleNamespace(runtime_state_root=tmp_path / '.ccb'),
    )
    payload = _mark_release_residue(
        context,
        'lp-g5-clean',
        payload={
            'retained_count': 0,
            'observed': {'agents': [], 'retained_count': 0},
        },
    )

    assert payload['release_incomplete_count'] == 0
    assert payload['release_incomplete_agents'] == []
    assert payload['observed']['release_incomplete_count'] == 0


@pytest.mark.ccb_lifecycle_smoke
def test_real_cli_fake_multi_workgroup_mixed_dag_full_flow(tmp_path: Path) -> None:
    module = _load_script()
    project_root = tmp_path / 'g5-real-cli-fullflow'

    report = module.run_smoke(
        project_root=project_root,
        count=3,
        shape='mixed_dag',
        ccb_test=Path(__file__).resolve().parents[1] / 'ccb_test',
        command_timeout_s=240,
    )

    assert report['status'] == 'pass'
    assert report['bundle']['node_count'] == 3
    assert report['bundle']['dependencies']['node-003'] == ['node-001']
    assert report['round']['result'] == 'pass'
    assert report['release']['live_agents'] == []
    assert report['release']['dynamic_residue'] == []
    assert Path(report['paths']['report']).is_file()
