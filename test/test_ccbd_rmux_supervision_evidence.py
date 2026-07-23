from __future__ import annotations

from agents.models import AgentRuntime, AgentState
from ccbd.supervision.evidence import build_runtime_evidence_ledger, runtime_active_pane_id


def _runtime(**overrides) -> AgentRuntime:
    payload = {
        'agent_name': 'codex',
        'state': AgentState.DEGRADED,
        'pid': 101,
        'started_at': '2026-03-18T00:00:00Z',
        'last_seen_at': '2026-03-18T00:00:00Z',
        'runtime_ref': 'rmux:pane-a',
        'session_ref': 'ccbd-session',
        'workspace_path': 'E:/repo/.ccb/worktrees/codex',
        'project_id': 'project',
        'backend_type': 'pane-backed',
        'queue_depth': 0,
        'socket_path': None,
        'health': 'pane-dead',
        'backend_impl': 'rmux',
        'namespace_ref': {
            'backend_impl': 'rmux',
            'namespace_id': 'ccbd-session',
            'session_name': 'ccbd-session',
            'ipc_kind': 'named_pipe',
            'ipc_ref': 'ccbd-session',
        },
        'pane_ref': {
            'backend_impl': 'rmux',
            'pane_id': 'pane-a',
            'window_name': 'workspace',
        },
        'process_ref': {
            'pid': 101,
            'health': 'alive',
        },
        'daemon_generation': 7,
    }
    payload.update(overrides)
    return AgentRuntime(**payload)


def test_runtime_evidence_ledger_splits_pane_process_namespace_and_daemon_health() -> None:
    ledger = build_runtime_evidence_ledger(_runtime())

    assert ledger['backend_impl'] == 'rmux'
    assert ledger['pane_health'] == 'dead'
    assert ledger['process_health'] == 'alive'
    assert ledger['namespace_health'] == 'alive'
    assert ledger['daemon_health'] == 'unknown'
    assert ledger['pane_ref'] == {'backend_impl': 'rmux', 'pane_id': 'pane-a', 'window_name': 'workspace'}
    assert ledger['process_ref'] == {'pid': 101, 'health': 'alive'}


def test_runtime_evidence_ledger_process_dead_takes_precedence_over_alive_pane() -> None:
    ledger = build_runtime_evidence_ledger(
        _runtime(
            health='process-dead',
            pane_ref={'backend_impl': 'rmux', 'pane_id': 'pane-a'},
            process_ref={'pid': 101, 'health': 'dead'},
        )
    )

    assert ledger['pane_health'] == 'alive'
    assert ledger['process_health'] == 'dead'


def test_runtime_active_pane_id_accepts_rmux_backend_local_id() -> None:
    assert runtime_active_pane_id(_runtime(active_pane_id='pane-b', pane_ref=None)) == 'pane-b'
