from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from cli.services.workgroup_integration import (
    GitIntegrationError,
    VerificationCommand,
    WORKGROUP_GIT_TRANSACTION_SCHEMA,
    WorkgroupGitIntegration,
    WorkgroupNodeSpec,
)


BUNDLE_DIGEST = 'sha256:' + ('a' * 64)


def _git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ['git', '-C', str(cwd), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout.strip()


def _init_repo(tmp_path: Path) -> Path:
    root = tmp_path / 'repo'
    root.mkdir()
    (root / '.gitignore').write_text('.ccb/\n__pycache__/\n', encoding='utf-8')
    (root / 'README.md').write_text('base\n', encoding='utf-8')
    (root / 'protected.txt').write_text('protected\n', encoding='utf-8')
    _git(root, 'init')
    _git(root, 'config', 'user.email', 'test@example.com')
    _git(root, 'config', 'user.name', 'Test User')
    _git(root, 'add', '.')
    _git(root, 'commit', '-m', 'base')
    return root


def _node(
    index: int,
    *,
    allowed_paths: tuple[str, ...] | None = None,
    depends_on: tuple[str, ...] = (),
    integration_order: int | None = None,
) -> WorkgroupNodeSpec:
    return WorkgroupNodeSpec(
        node_id=f'node-{index:03d}',
        workgroup_id=f'wg-{index:03d}',
        depends_on=depends_on,
        allowed_paths=allowed_paths or (f'parts/node-{index:03d}.txt',),
        integration_order=integration_order or index * 10,
    )


def _kernel(
    root: Path,
    nodes: tuple[WorkgroupNodeSpec, ...],
    *,
    integration_verification: tuple[VerificationCommand, ...] = (),
    root_verification: tuple[VerificationCommand, ...] = (),
    verify_each_layer: bool = False,
) -> WorkgroupGitIntegration:
    return WorkgroupGitIntegration(
        project_root=root,
        state_path=root / '.ccb' / 'runtime' / 'loops' / 'loop-r2' / 'git-transaction.json',
        task_id='task-r2',
        loop_id='loop-r2',
        bundle_revision=1,
        bundle_digest=BUNDLE_DIGEST,
        nodes=nodes,
        integration_verification=integration_verification,
        root_verification=root_verification,
        verify_each_layer=verify_each_layer,
    )


def _node_record(kernel: WorkgroupGitIntegration, node_id: str) -> dict[str, object]:
    return kernel.state()['nodes'][node_id]


def _write_node_file(kernel: WorkgroupGitIntegration, node_id: str, relative: str, text: str) -> None:
    worktree = Path(str(_node_record(kernel, node_id)['worktree_path']))
    path = worktree / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def _review_and_finalize(kernel: WorkgroupGitIntegration, node_id: str) -> dict[str, object]:
    review = kernel.capture_review_input(node_id, worker_job_id=f'worker-{node_id}')
    kernel.record_review(
        node_id,
        reviewer_job_id=f'reviewer-{node_id}',
        result='pass',
        input_digest=str(review['input_digest']),
        tree_digest=str(review['tree_digest']),
    )
    return kernel.finalize_node(node_id)


def _prepare_changed_node(
    kernel: WorkgroupGitIntegration,
    spec: WorkgroupNodeSpec,
    *,
    relative: str | None = None,
    text: str | None = None,
) -> dict[str, object]:
    kernel.prepare_node(spec.node_id)
    target = relative or spec.allowed_paths[0]
    _write_node_file(kernel, spec.node_id, target, text or f'{spec.node_id}\n')
    return _review_and_finalize(kernel, spec.node_id)


@pytest.mark.parametrize('node_count', (1, 2, 3, 4))
def test_one_to_four_independent_nodes_integrate_promote_and_preserve_worktrees(
    tmp_path: Path,
    node_count: int,
) -> None:
    root = _init_repo(tmp_path)
    nodes = tuple(_node(index) for index in range(1, node_count + 1))
    kernel = _kernel(root, nodes)

    preflight = kernel.preflight()
    kernel.prepare_integration()
    for spec in reversed(nodes):
        _prepare_changed_node(kernel, spec)

    integrated = kernel.integrate_ready()
    promoted = kernel.promote()
    verified = kernel.verify_root()
    accepted = kernel.accept()

    assert preflight['schema'] == WORKGROUP_GIT_TRANSACTION_SCHEMA
    assert integrated['integration']['merge_order'] == [node.node_id for node in nodes]
    assert integrated['integration']['status'] == 'verified'
    assert promoted['root']['promotion']['status'] == 'applied'
    assert verified['root']['checks'][-1]['status'] == 'pass'
    assert accepted['status'] == 'accepted'
    assert _git(root, 'status', '--porcelain') == ''
    for spec in nodes:
        assert (root / spec.allowed_paths[0]).read_text(encoding='utf-8') == f'{spec.node_id}\n'
        record = accepted['nodes'][spec.node_id]
        assert record['status'] == 'integrated'
        assert record['reviewed_commit']
        assert record['reviewed_tree_digest'] == record['review']['tree_digest']
        assert Path(str(record['worktree_path'])).is_dir()

    active_path = Path(str(accepted['nodes'][nodes[0].node_id]['worktree_path']))
    blocked_cleanup = kernel.cleanup_readiness(
        evidence_captured=True,
        active_workspaces=(active_path,),
    )
    ready_cleanup = kernel.cleanup_readiness(evidence_captured=True)

    assert blocked_cleanup['eligible'] is False
    assert blocked_cleanup['reason'] == 'owned_worktree_active'
    assert ready_cleanup['eligible'] is True
    assert ready_cleanup['worktrees_preserved'] is True
    assert active_path.is_dir()


def test_mixed_dependency_graph_uses_current_integrated_head_and_stable_order(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    node_1 = _node(1, integration_order=20)
    node_2 = _node(2, integration_order=10)
    node_3 = _node(
        3,
        depends_on=('node-001', 'node-002'),
        integration_order=30,
    )
    check = VerificationCommand(
        'completed-wave',
        (
            sys.executable,
            '-c',
            'from pathlib import Path; '
            'assert all(Path(f"parts/node-{i:03d}.txt").is_file() for i in (1,2))',
        ),
        timeout_seconds=10,
    )
    kernel = _kernel(
        root,
        (node_1, node_2, node_3),
        integration_verification=(check,),
        verify_each_layer=True,
    )
    kernel.preflight()
    kernel.prepare_integration()
    _prepare_changed_node(kernel, node_1)
    _prepare_changed_node(kernel, node_2)

    first_wave = kernel.integrate_ready()
    first_head = first_wave['integration']['head']
    assert first_wave['integration']['merge_order'] == ['node-002', 'node-001']
    assert first_wave['status'] == 'integration_pending'

    kernel.prepare_node(node_3.node_id)
    dependent = _node_record(kernel, node_3.node_id)
    assert dependent['base_commit'] == first_head
    _write_node_file(kernel, node_3.node_id, node_3.allowed_paths[0], 'dependent\n')
    _review_and_finalize(kernel, node_3.node_id)

    final = kernel.integrate_ready()

    assert final['integration']['merge_order'] == ['node-002', 'node-001', 'node-003']
    assert [check['key'] for check in final['integration']['checks']] == ['layer-0', 'layer-1', 'final']
    assert all(check['status'] == 'pass' for check in final['integration']['checks'])
    assert final['nodes']['node-003']['base_commit'] == first_head
    integration_root = Path(str(final['integration']['worktree_path']))
    assert (integration_root / node_3.allowed_paths[0]).read_text(encoding='utf-8') == 'dependent\n'


def test_rejected_dirty_preflight_does_not_create_branches_or_worktrees(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    (root / 'user-change.txt').write_text('keep me\n', encoding='utf-8')
    kernel = _kernel(root, (_node(1),))
    before_head = _git(root, 'rev-parse', 'HEAD')
    before_branches = _git(root, 'branch', '--format=%(refname)')
    before_worktrees = _git(root, 'worktree', 'list', '--porcelain')

    with pytest.raises(GitIntegrationError) as exc_info:
        kernel.preflight()

    assert exc_info.value.code == 'dirty_project_root'
    assert _git(root, 'rev-parse', 'HEAD') == before_head
    assert _git(root, 'branch', '--format=%(refname)') == before_branches
    assert _git(root, 'worktree', 'list', '--porcelain') == before_worktrees
    assert (root / 'user-change.txt').read_text(encoding='utf-8') == 'keep me\n'
    assert kernel.state_path.exists() is False


def test_preflight_rejects_stale_controller_branch_without_resumable_state(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    kernel = _kernel(root, (_node(1),))
    stale_branch = f'ccb/workgroup/{kernel.transaction_key}/integration'
    _git(root, 'branch', stale_branch)

    with pytest.raises(GitIntegrationError) as exc_info:
        kernel.preflight()

    assert exc_info.value.code == 'controller_workspace_collision'
    assert {'kind': 'branch', 'value': stale_branch} in exc_info.value.details['collisions']
    assert kernel.state_path.exists() is False


def test_public_from_bundle_api_uses_explicit_semantic_digest(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    bundle = {
        'task_id': 'task-r2',
        'bundle_revision': 1,
        'nodes': [
            {
                'node_id': 'node-001',
                'workgroup_id': 'wg-001',
                'depends_on': [],
                'allowed_paths': ['parts/node-001.txt'],
                'integration_order': 10,
            }
        ],
    }

    kernel = WorkgroupGitIntegration.from_bundle(
        project_root=root,
        state_path=root / '.ccb' / 'runtime' / 'loops' / 'loop-r2' / 'git-transaction.json',
        loop_id='loop-r2',
        bundle=bundle,
        bundle_digest=BUNDLE_DIGEST,
    )
    state = kernel.preflight()

    assert state['task']['bundle_digest'] == BUNDLE_DIGEST
    assert list(state['nodes']) == ['node-001']


def test_durable_state_rejects_node_scope_drift(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    spec = _node(1)
    kernel = _kernel(root, (spec,))
    kernel.preflight()
    payload = json.loads(kernel.state_path.read_text(encoding='utf-8'))
    payload['nodes']['node-001']['allowed_paths'] = ['other.txt']
    kernel.state_path.write_text(json.dumps(payload), encoding='utf-8')

    with pytest.raises(GitIntegrationError) as exc_info:
        _kernel(root, (spec,)).state()

    assert exc_info.value.code == 'integration_state_node_drift'


def test_scope_violation_and_out_of_contract_deletion_block_before_review(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    spec = _node(1, allowed_paths=('parts/allowed.txt',))
    kernel = _kernel(root, (spec,))
    kernel.preflight()
    kernel.prepare_integration()
    kernel.prepare_node(spec.node_id)
    _write_node_file(kernel, spec.node_id, 'parts/allowed.txt', 'allowed\n')
    worktree = Path(str(_node_record(kernel, spec.node_id)['worktree_path']))
    (worktree / 'protected.txt').unlink()

    with pytest.raises(GitIntegrationError) as exc_info:
        kernel.capture_review_input(spec.node_id, worker_job_id='worker-1')

    assert exc_info.value.code == 'node_scope_violation'
    assert 'protected.txt' in exc_info.value.details['changed_paths']
    assert _git(worktree, 'rev-parse', 'HEAD') == kernel.state()['task']['base_commit']
    assert _git(worktree, 'rev-list', '--count', '--all', '--not', kernel.state()['task']['base_commit']) == '0'


def test_reviewer_input_and_tree_digests_are_exact_fences(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    spec = _node(1)
    kernel = _kernel(root, (spec,))
    kernel.preflight()
    kernel.prepare_integration()
    kernel.prepare_node(spec.node_id)
    _write_node_file(kernel, spec.node_id, spec.allowed_paths[0], 'first\n')
    review = kernel.capture_review_input(spec.node_id, worker_job_id='worker-1')

    with pytest.raises(GitIntegrationError) as mismatch:
        kernel.record_review(
            spec.node_id,
            reviewer_job_id='reviewer-1',
            result='pass',
            input_digest='sha256:' + ('b' * 64),
            tree_digest=str(review['tree_digest']),
        )
    assert mismatch.value.code == 'review_input_digest_mismatch'

    _write_node_file(kernel, spec.node_id, spec.allowed_paths[0], 'drifted\n')
    with pytest.raises(GitIntegrationError) as drift:
        kernel.record_review(
            spec.node_id,
            reviewer_job_id='reviewer-1',
            result='pass',
            input_digest=str(review['input_digest']),
            tree_digest=str(review['tree_digest']),
        )
    assert drift.value.code == 'reviewed_tree_drift'
    assert _node_record(kernel, spec.node_id)['reviewed_commit'] is None


def test_missing_reviewer_pass_cannot_create_controller_commit(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    spec = _node(1)
    kernel = _kernel(root, (spec,))
    kernel.preflight()
    kernel.prepare_integration()
    kernel.prepare_node(spec.node_id)
    _write_node_file(kernel, spec.node_id, spec.allowed_paths[0], 'pending\n')

    with pytest.raises(GitIntegrationError) as exc_info:
        kernel.finalize_node(spec.node_id)

    assert exc_info.value.code == 'missing_reviewer_pass'
    assert _node_record(kernel, spec.node_id)['reviewed_commit'] is None


def test_rework_review_lineage_is_preserved_and_duplicate_result_is_idempotent(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    spec = _node(1)
    kernel = _kernel(root, (spec,))
    kernel.preflight()
    kernel.prepare_integration()
    kernel.prepare_node(spec.node_id)
    _write_node_file(kernel, spec.node_id, spec.allowed_paths[0], 'first attempt\n')
    first = kernel.capture_review_input(spec.node_id, worker_job_id='worker-1')
    first_result = kernel.record_review(
        spec.node_id,
        reviewer_job_id='reviewer-1',
        result='rework',
        input_digest=str(first['input_digest']),
        tree_digest=str(first['tree_digest']),
    )
    duplicate = kernel.record_review(
        spec.node_id,
        reviewer_job_id='reviewer-1',
        result='rework',
        input_digest=str(first['input_digest']),
        tree_digest=str(first['tree_digest']),
    )
    assert duplicate == first_result

    _write_node_file(kernel, spec.node_id, spec.allowed_paths[0], 'second attempt\n')
    second = kernel.capture_review_input(spec.node_id, worker_job_id='worker-2')
    kernel.record_review(
        spec.node_id,
        reviewer_job_id='reviewer-2',
        result='pass',
        input_digest=str(second['input_digest']),
        tree_digest=str(second['tree_digest']),
    )
    finalized = kernel.finalize_node(spec.node_id)

    assert [review['result'] for review in finalized['reviews']] == ['rework', 'pass']
    assert finalized['reviewed_tree_digest'] == second['tree_digest']


def test_dirty_drift_after_reviewed_commit_blocks_integration(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    spec = _node(1)
    kernel = _kernel(root, (spec,))
    kernel.preflight()
    kernel.prepare_integration()
    finalized = _prepare_changed_node(kernel, spec)
    worktree = Path(str(finalized['worktree_path']))
    (worktree / spec.allowed_paths[0]).write_text('post-review drift\n', encoding='utf-8')

    with pytest.raises(GitIntegrationError) as exc_info:
        kernel.integrate_ready()

    assert exc_info.value.code == 'reviewed_commit_worktree_drift'
    assert kernel.state()['integration']['merge_order'] == []


def test_merge_conflict_is_structured_and_never_auto_resolved(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    file_node = _node(1, allowed_paths=('shared',), integration_order=10)
    directory_node = _node(2, allowed_paths=('shared/file.txt',), integration_order=20)
    kernel = _kernel(root, (file_node, directory_node))
    kernel.preflight()
    kernel.prepare_integration()
    _prepare_changed_node(kernel, file_node, relative='shared', text='file\n')
    _prepare_changed_node(kernel, directory_node, relative='shared/file.txt', text='child\n')

    with pytest.raises(GitIntegrationError) as exc_info:
        kernel.integrate_ready()

    state = kernel.state()
    integration_path = Path(str(state['integration']['worktree_path']))
    assert exc_info.value.code == 'integration_merge_conflict'
    assert state['status'] == 'replan_required'
    assert state['integration']['status'] == 'merge_conflict'
    assert state['integration']['merge_order'] == ['node-001']
    assert _git(integration_path, 'status', '--porcelain') == ''
    assert not (root / 'shared').exists()


def test_integration_verification_failure_never_promotes_root(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    spec = _node(1)
    failing = VerificationCommand(
        'fail-integration',
        (
            sys.executable,
            '-c',
            'import sys; print("integration-out"); print("integration-err", file=sys.stderr); '
            'raise SystemExit(7)',
        ),
        timeout_seconds=10,
    )
    kernel = _kernel(root, (spec,), integration_verification=(failing,))
    kernel.preflight()
    kernel.prepare_integration()
    _prepare_changed_node(kernel, spec)
    base = kernel.state()['task']['base_commit']

    with pytest.raises(GitIntegrationError) as exc_info:
        kernel.integrate_ready()

    state = kernel.state()
    assert exc_info.value.code == 'integration_verification_failed'
    assert state['status'] == 'integration_failed'
    assert state['integration']['checks'][-1]['results'][0]['exit_code'] == 7
    assert state['integration']['checks'][-1]['results'][0]['stdout'] == 'integration-out\n'
    assert state['integration']['checks'][-1]['results'][0]['stderr'] == 'integration-err\n'
    assert _git(root, 'rev-parse', 'HEAD') == base
    assert not (root / spec.allowed_paths[0]).exists()


def test_integration_verification_timeout_is_bounded_and_recorded(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    spec = _node(1)
    timeout = VerificationCommand(
        'timeout-integration',
        (sys.executable, '-c', 'import time; time.sleep(2)'),
        timeout_seconds=0.05,
    )
    kernel = _kernel(root, (spec,), integration_verification=(timeout,))
    kernel.preflight()
    kernel.prepare_integration()
    _prepare_changed_node(kernel, spec)

    with pytest.raises(GitIntegrationError) as exc_info:
        kernel.integrate_ready()

    result = kernel.state()['integration']['checks'][-1]['results'][0]
    assert exc_info.value.code == 'integration_verification_failed'
    assert result['timed_out'] is True
    assert result['exit_code'] is None
    assert result['result'] == 'failed'


def test_root_drift_blocks_promotion_without_overwriting_user_change(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    spec = _node(1)
    kernel = _kernel(root, (spec,))
    kernel.preflight()
    kernel.prepare_integration()
    _prepare_changed_node(kernel, spec)
    kernel.integrate_ready()
    base = kernel.state()['task']['base_commit']
    (root / 'user-local.txt').write_text('do not overwrite\n', encoding='utf-8')

    with pytest.raises(GitIntegrationError) as exc_info:
        kernel.promote()

    assert exc_info.value.code == 'root_drift_before_promotion'
    assert _git(root, 'rev-parse', 'HEAD') == base
    assert (root / 'user-local.txt').read_text(encoding='utf-8') == 'do not overwrite\n'
    assert not (root / spec.allowed_paths[0]).exists()


def test_root_branch_drift_blocks_promotion_even_when_head_is_unchanged(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    spec = _node(1)
    kernel = _kernel(root, (spec,))
    kernel.preflight()
    kernel.prepare_integration()
    _prepare_changed_node(kernel, spec)
    kernel.integrate_ready()
    base = kernel.state()['task']['base_commit']
    _git(root, 'switch', '-c', 'user/other-branch')
    assert _git(root, 'rev-parse', 'HEAD') == base

    with pytest.raises(GitIntegrationError) as exc_info:
        kernel.promote()

    assert exc_info.value.code == 'root_drift_before_promotion'
    assert exc_info.value.details['observed_branch'] == 'user/other-branch'
    assert _git(root, 'rev-parse', 'HEAD') == base


def test_root_verification_failure_restores_exact_pre_promotion_root(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    spec = _node(1)
    failing = VerificationCommand(
        'fail-root',
        (
            sys.executable,
            '-c',
            'raise SystemExit(9)',
        ),
        timeout_seconds=10,
    )
    kernel = _kernel(root, (spec,), root_verification=(failing,))
    kernel.preflight()
    kernel.prepare_integration()
    _prepare_changed_node(kernel, spec)
    kernel.integrate_ready()
    kernel.promote()
    base = kernel.state()['task']['base_commit']
    base_tree = kernel.state()['task']['base_tree_digest']

    with pytest.raises(GitIntegrationError) as exc_info:
        kernel.verify_root()

    state = kernel.state()
    assert exc_info.value.code == 'root_verification_failed'
    assert state['status'] == 'rolled_back'
    assert state['root']['rollback']['status'] == 'restored'
    assert state['root']['rollback']['tree_digest'] == base_tree
    assert _git(root, 'rev-parse', 'HEAD') == base
    assert _git(root, 'status', '--porcelain') == ''
    assert not (root / spec.allowed_paths[0]).exists()


def test_explicit_nonpass_rollback_after_root_verification(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    spec = _node(1)
    passing = VerificationCommand(
        'root-pass',
        (sys.executable, '-c', 'from pathlib import Path; assert Path("parts/node-001.txt").is_file()'),
        timeout_seconds=10,
    )
    kernel = _kernel(root, (spec,), root_verification=(passing,))
    kernel.preflight()
    kernel.prepare_integration()
    _prepare_changed_node(kernel, spec)
    kernel.integrate_ready()
    kernel.promote()
    kernel.verify_root()
    base = kernel.state()['task']['base_commit']

    rolled_back = kernel.rollback(reason='round_reviewer_rejected')

    assert rolled_back['status'] == 'rolled_back'
    assert rolled_back['root']['rollback']['reason'] == 'round_reviewer_rejected'
    assert _git(root, 'rev-parse', 'HEAD') == base
    assert not (root / spec.allowed_paths[0]).exists()


@pytest.mark.parametrize('checkpoint', ('after_node_commit', 'after_node_state_write'))
def test_node_finalize_replay_never_duplicates_controller_commit(
    tmp_path: Path,
    checkpoint: str,
) -> None:
    root = _init_repo(tmp_path)
    spec = _node(1)
    kernel = _kernel(root, (spec,))
    kernel.preflight()
    kernel.prepare_integration()
    kernel.prepare_node(spec.node_id)
    _write_node_file(kernel, spec.node_id, spec.allowed_paths[0], 'replay\n')
    review = kernel.capture_review_input(spec.node_id, worker_job_id='worker-1')
    kernel.record_review(
        spec.node_id,
        reviewer_job_id='reviewer-1',
        result='pass',
        input_digest=str(review['input_digest']),
        tree_digest=str(review['tree_digest']),
    )
    fired = False

    def crash(name: str, _state: dict[str, object]) -> None:
        nonlocal fired
        if name == checkpoint and not fired:
            fired = True
            raise RuntimeError(f'crash:{checkpoint}')

    kernel._checkpoint_hook = crash
    with pytest.raises(RuntimeError, match=f'crash:{checkpoint}'):
        kernel.finalize_node(spec.node_id)

    replay = _kernel(root, (spec,))
    replay.prepare_node(spec.node_id)
    finalized = replay.finalize_node(spec.node_id)
    worktree = Path(str(finalized['worktree_path']))
    base = replay.state()['task']['base_commit']

    assert finalized['reviewed_commit']
    assert _git(worktree, 'rev-list', '--count', f'{base}..HEAD') == '1'


def test_integration_merge_replay_records_existing_merge_without_duplication(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    spec = _node(1)
    kernel = _kernel(root, (spec,))
    kernel.preflight()
    kernel.prepare_integration()
    _prepare_changed_node(kernel, spec)
    fired = False

    def crash(name: str, _state: dict[str, object]) -> None:
        nonlocal fired
        if name == 'after_integration_merge' and not fired:
            fired = True
            raise RuntimeError('crash:merge')

    kernel._checkpoint_hook = crash
    with pytest.raises(RuntimeError, match='crash:merge'):
        kernel.integrate_ready()

    replay = _kernel(root, (spec,))
    replay.prepare_integration()
    state = replay.integrate_ready()
    integration = state['integration']
    worktree = Path(str(integration['worktree_path']))
    base = state['task']['base_commit']

    assert integration['merge_order'] == ['node-001']
    assert integration['merges'][0]['recovered'] is True
    assert _git(worktree, 'rev-list', '--first-parent', '--count', f'{base}..HEAD') == '1'


def test_promotion_replay_recovers_applied_delta_without_second_promotion(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    spec = _node(1)
    kernel = _kernel(root, (spec,))
    kernel.preflight()
    kernel.prepare_integration()
    _prepare_changed_node(kernel, spec)
    kernel.integrate_ready()
    integrated_head = kernel.state()['integration']['head']
    fired = False

    def crash(name: str, _state: dict[str, object]) -> None:
        nonlocal fired
        if name == 'after_root_promotion' and not fired:
            fired = True
            raise RuntimeError('crash:promotion')

    kernel._checkpoint_hook = crash
    with pytest.raises(RuntimeError, match='crash:promotion'):
        kernel.promote()
    assert _git(root, 'rev-parse', 'HEAD') == integrated_head

    replay = _kernel(root, (spec,))
    state = replay.promote()

    assert state['root']['promotion']['status'] == 'applied'
    assert state['root']['promotion']['recovered'] is True
    assert _git(root, 'rev-parse', 'HEAD') == integrated_head
