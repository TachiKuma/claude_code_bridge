from __future__ import annotations

from copy import deepcopy

import pytest

from ccbd.services.project_namespace_state import ProjectNamespaceState
from provider_runtime.health import (
    ProgressState,
    ProviderCompletionState,
    ProviderHealthSnapshot,
)
from terminal_runtime.rmux_daemon_contract import (
    backend_daemon_diagnostics,
    build_rmux_cleanup_plan,
    build_rmux_daemon_evidence,
    build_rmux_daemon_ref,
    build_rmux_daemon_start_evidence,
    provider_health_daemon_diagnostics,
)


def test_rmux_daemon_evidence_contract_separates_daemon_process_from_provider_process_ref() -> None:
    ref = build_rmux_daemon_ref(
        daemon_id='rmux-shared-1',
        scope='shared',
        endpoint_kind='named_pipe',
        endpoint_ref=r'\\.\pipe\ccb-rmux',
        version='0.9.1',
    )
    evidence = build_rmux_daemon_evidence(
        daemon_ref=ref,
        discovery_source='backend_probe',
        health='healthy',
        project_id='proj-1',
        namespace_id='ns-1',
        daemon_process_evidence={
            'pid': 9001,
            'job_id': 'provider-job-id',
            'runtime_generation': 7,
            'source': 'probe',
        },
        capability_status='partial',
        cleanup_scope='none',
        diagnostics={'probe': 'ok'},
    )

    assert evidence['daemon_ref'] == ref
    assert evidence['discovery_source'] == 'backend_probe'
    assert evidence['health'] == 'healthy'
    assert evidence['daemon_process_evidence'] == {
        'pid': 9001,
        'source': 'probe',
        'evidence_kind': 'rmux_daemon_process',
    }
    assert 'job_id' not in evidence['daemon_process_evidence']
    assert 'runtime_generation' not in evidence['daemon_process_evidence']

    diagnostics = backend_daemon_diagnostics(evidence)
    assert diagnostics == {
        'backend_daemon_impl': 'rmux',
        'backend_daemon_id': 'rmux-shared-1',
        'backend_daemon_scope': 'shared',
        'backend_daemon_endpoint_kind': 'named_pipe',
        'backend_daemon_endpoint_ref': r'\\.\pipe\ccb-rmux',
        'backend_daemon_version': '0.9.1',
        'backend_daemon_capability_status': 'partial',
        'backend_daemon_health': 'healthy',
        'backend_daemon_discovery_source': 'backend_probe',
        'backend_daemon_cleanup_scope': 'none',
    }
    assert all(key.startswith('backend_daemon_') for key in diagnostics)


def test_start_result_evidence_success_and_failure_do_not_mutate_ccbd_authority() -> None:
    ccbd_authority = {
        'owner_daemon_instance_id': 'ccbd-owner-1',
        'lease_generation': 9,
    }
    before = deepcopy(ccbd_authority)

    success = build_rmux_daemon_start_evidence(
        daemon_id='rmux-started',
        success=True,
        endpoint_kind='tcp_loopback',
        endpoint_ref='127.0.0.1:5001',
        version='1.0.0',
        capability_status='supported',
        namespace_id='ns-1',
    )
    failed = build_rmux_daemon_start_evidence(
        daemon_id='rmux-failed',
        success=False,
        crash_reason='spawn-exited',
        capability_status='unknown',
        namespace_id='ns-1',
    )

    assert ccbd_authority == before
    assert success['discovery_source'] == 'start_result'
    assert success['health'] == 'healthy'
    assert success['daemon_ref']['endpoint_ref'] == '127.0.0.1:5001'
    assert success['daemon_ref']['version'] == '1.0.0'
    assert success['capability_status'] == 'supported'
    assert success['diagnostics']['start_success'] is True
    assert 'owner_daemon_instance_id' not in success['diagnostics']
    assert 'lease_generation' not in success['diagnostics']

    assert failed['health'] == 'crashed'
    assert failed['crash_reason'] == 'spawn-exited'
    assert failed['diagnostics']['start_success'] is False


def test_cleanup_plan_defaults_to_namespace_and_leaves_shared_daemon_running() -> None:
    daemon = build_rmux_daemon_evidence(
        daemon_ref=build_rmux_daemon_ref(
            daemon_id='shared-daemon',
            scope='shared',
            endpoint_kind='named_pipe',
            endpoint_ref='rmux-pipe',
        ),
        discovery_source='cleanup',
        health='healthy',
        namespace_id='ns-1',
        capability_status='supported',
        cleanup_scope='namespace',
    )

    plan = build_rmux_cleanup_plan(
        namespace_ref={'namespace_id': 'ns-1', 'pane_id': '%1'},
        daemon=daemon,
    )

    assert plan['cleanup_scope'] == 'namespace'
    assert plan['daemon_action'] == 'leave_running'
    assert plan['force_daemon'] is False
    assert 'daemon_cleanup' not in plan['ordered_steps']
    assert plan['ordered_steps'] == ['provider_job_evidence', 'namespace_session', 'diagnostics']
    assert {'kind': 'daemon', 'daemon_id': 'shared-daemon'} not in plan['targets']
    assert plan['targets'][0] == {
        'kind': 'namespace',
        'namespace_id': 'ns-1',
        'backend_impl': 'rmux',
    }


def test_project_scoped_cleanup_still_leaves_daemon_running() -> None:
    daemon = build_rmux_daemon_evidence(
        daemon_ref=build_rmux_daemon_ref(
            daemon_id='project-daemon',
            scope='project',
            endpoint_kind='named_pipe',
            endpoint_ref='project-pipe',
        ),
        discovery_source='cleanup',
        health='stale',
        namespace_id='ns-project',
        cleanup_scope='project',
    )

    plan = build_rmux_cleanup_plan(
        namespace_ref={'namespace_id': 'ns-project'},
        daemon=daemon,
        cleanup_scope='project',
    )

    assert daemon['daemon_ref']['scope'] == 'project'
    assert daemon['health'] == 'stale'
    assert plan['cleanup_scope'] == 'project'
    assert plan['daemon_action'] == 'leave_running'
    assert 'daemon_cleanup' not in plan['ordered_steps']


def test_cleanup_plan_requires_explicit_force_for_daemon_wide_shutdown() -> None:
    daemon = build_rmux_daemon_evidence(
        daemon_ref=build_rmux_daemon_ref(daemon_id='shared-daemon', scope='shared'),
        discovery_source='cleanup',
        cleanup_scope='daemon',
    )

    with pytest.raises(ValueError, match='force_daemon=True'):
        build_rmux_cleanup_plan(
            namespace_ref={'namespace_id': 'ns-1'},
            daemon=daemon,
            cleanup_scope='daemon',
        )

    with pytest.raises(ValueError, match='force_reason'):
        build_rmux_cleanup_plan(
            namespace_ref={'namespace_id': 'ns-1'},
            daemon=daemon,
            cleanup_scope='daemon',
            force_daemon=True,
        )

    plan = build_rmux_cleanup_plan(
        namespace_ref={'namespace_id': 'ns-1'},
        daemon=daemon,
        cleanup_scope='daemon',
        force_daemon=True,
        force_reason='owner-approved-shutdown',
    )

    assert plan['daemon_action'] == 'shutdown'
    assert plan['force_daemon'] is True
    assert plan['force_reason'] == 'owner-approved-shutdown'
    assert 'daemon_cleanup' in plan['ordered_steps']
    assert plan['targets'][-1]['kind'] == 'daemon'
    assert plan['diagnostics']['daemon_cleanup_forced'] is True
    assert plan['diagnostics']['force_reason'] == 'owner-approved-shutdown'


def test_namespace_summary_projects_backend_daemon_diagnostics_without_clobbering_authority_fields() -> None:
    evidence = build_rmux_daemon_evidence(
        daemon_ref=build_rmux_daemon_ref(
            daemon_id='rmux-crashed',
            scope='shared',
            endpoint_kind='named_pipe',
            endpoint_ref='rmux-pipe',
            version='0.9.1',
        ),
        discovery_source='health_probe',
        health='crashed',
        namespace_id='ns-1',
        capability_status='partial',
        crash_reason='daemon-exited',
        cleanup_scope='namespace',
    )
    state = ProjectNamespaceState(
        project_id='proj-1',
        namespace_epoch=3,
        tmux_socket_path='/legacy/tmux.sock',
        tmux_session_name='legacy-session',
        backend_impl='rmux',
        namespace_id='ns-1',
        namespace_ipc_kind='named_pipe',
        namespace_ipc_ref='rmux-pipe',
        backend_daemon_evidence=evidence,
    )

    record = state.to_record()
    restored = ProjectNamespaceState.from_record(record)
    summary = restored.summary_fields()

    assert summary['namespace_id'] == 'proj-1'
    assert summary['namespace_backend_impl'] == 'rmux'
    assert summary['namespace_tmux_socket_path'] == '/legacy/tmux.sock'
    assert summary['backend_daemon_id'] == 'rmux-crashed'
    assert summary['backend_daemon_health'] == 'crashed'
    assert summary['backend_daemon_crash_reason'] == 'daemon-exited'
    assert summary['backend_daemon_capability_status'] == 'partial'
    assert 'daemon_id' not in summary
    assert 'daemon_health' not in summary
    assert 'tmux_socket_path' not in summary


def test_default_tmux_namespace_summary_has_no_rmux_daemon_diagnostics() -> None:
    state = ProjectNamespaceState(
        project_id='proj-tmux',
        namespace_epoch=1,
        tmux_socket_path='/tmp/tmux.sock',
        tmux_session_name='ccb-tmux',
    )

    summary = state.summary_fields()

    assert summary['namespace_backend_impl'] == 'tmux'
    assert not any(key.startswith('backend_daemon_') for key in summary)


def test_backend_daemon_diagnostics_can_project_daemon_action() -> None:
    evidence = build_rmux_daemon_evidence(
        daemon_ref=build_rmux_daemon_ref(daemon_id='rmux-cleanup', scope='shared'),
        discovery_source='cleanup',
        health='healthy',
        cleanup_scope='daemon',
    )
    evidence['daemon_action'] = 'shutdown'

    diagnostics = backend_daemon_diagnostics(evidence)

    assert diagnostics['backend_daemon_action'] == 'shutdown'
    assert diagnostics['backend_daemon_cleanup_scope'] == 'daemon'


def test_provider_health_snapshot_can_carry_rmux_daemon_diagnostics_without_changing_runtime_health() -> None:
    evidence = build_rmux_daemon_start_evidence(
        daemon_id='rmux-unreachable',
        success=False,
        endpoint_kind='named_pipe',
        endpoint_ref='rmux-pipe',
        capability_status='unknown',
        namespace_id='ns-1',
    )
    snapshot = ProviderHealthSnapshot(
        job_id='job-1',
        provider='codex',
        agent_name='agent1',
        runtime_alive=True,
        session_reachable=True,
        progress_state=ProgressState.ACTIVELY_RUNNING,
        completion_state=ProviderCompletionState.NOT_COMPLETE,
        last_progress_at='2026-07-23T00:00:00Z',
        observed_at='2026-07-23T00:00:01Z',
        degraded_reason=None,
        diagnostics=provider_health_daemon_diagnostics({'ccbd_health': 'healthy'}, evidence),
    )

    record = snapshot.to_record()

    assert record['runtime_alive'] is True
    assert record['session_reachable'] is True
    assert record['degraded_reason'] is None
    assert record['diagnostics']['ccbd_health'] == 'healthy'
    assert record['diagnostics']['backend_daemon_health'] == 'unreachable'
    assert record['diagnostics']['backend_daemon_endpoint_ref'] == 'rmux-pipe'
