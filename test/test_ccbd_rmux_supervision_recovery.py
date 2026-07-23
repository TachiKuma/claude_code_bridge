from __future__ import annotations

from pathlib import Path
import pytest

from agents.models import (
    AgentRuntime,
    AgentSpec,
    AgentState,
    PermissionMode,
    ProjectConfig,
    QueuePolicy,
    RestoreMode,
    RuntimeMode,
    WorkspaceMode,
)
from ccbd.services.registry import AgentRegistry
from ccbd.services.runtime import RuntimeService
from ccbd.supervision import RuntimeSupervisionLoop, SupervisionEventStore
from project.resolver import bootstrap_project
from storage.paths import PathLayout


def _provider_config(*providers: str) -> ProjectConfig:
    agents: dict[str, AgentSpec] = {}
    for provider in providers:
        agents[provider] = AgentSpec(
            name=provider,
            provider=provider,
            target='.',
            workspace_mode=WorkspaceMode.GIT_WORKTREE,
            workspace_root=None,
            runtime_mode=RuntimeMode.PANE_BACKED,
            restore_default=RestoreMode.AUTO,
            permission_default=PermissionMode.MANUAL,
            queue_policy=QueuePolicy.SERIAL_PER_AGENT,
        )
    return ProjectConfig(version=2, default_agents=tuple(providers), agents=agents)


def _namespace_ref(layout: PathLayout) -> dict[str, object]:
    return {
        'backend_family': 'tmux-family',
        'backend_impl': 'rmux',
        'namespace_id': layout.ccbd_tmux_session_name,
        'session_name': layout.ccbd_tmux_session_name,
        'ipc_kind': 'named_pipe',
        'ipc_ref': layout.ccbd_tmux_session_name,
    }


def _runtime(
    agent_name: str,
    *,
    project_id: str,
    layout: PathLayout,
    health: str,
    pane_id: str = 'pane-a',
) -> AgentRuntime:
    return AgentRuntime(
        agent_name=agent_name,
        state=AgentState.DEGRADED if health != 'healthy' else AgentState.IDLE,
        pid=101,
        started_at='2026-03-18T00:00:00Z',
        last_seen_at='2026-03-18T00:00:00Z',
        runtime_ref=f'rmux:{pane_id}',
        session_ref=str(layout.ccbd_tmux_session_name),
        workspace_path=str(layout.workspace_path(agent_name)),
        project_id=project_id,
        backend_type='pane-backed',
        queue_depth=0,
        socket_path=None,
        health=health,
        backend_impl='rmux',
        namespace_ref=_namespace_ref(layout),
        pane_ref={'backend_impl': 'rmux', 'pane_id': pane_id},
        active_pane_id=pane_id,
        process_ref={'pid': 101, 'health': 'alive'},
    )


def test_rmux_foreign_pane_reflows_by_namespace_ref_without_tmux_socket(tmp_path: Path) -> None:
    project_root = tmp_path / 'repo-rmux-supervision-namespace'
    project_root.mkdir()
    project = bootstrap_project(project_root)
    layout = PathLayout(project_root)
    config = _provider_config('codex')
    registry = AgentRegistry(layout, config)
    runtime_service = RuntimeService(layout, registry, project.project_id, clock=lambda: '2026-03-18T00:00:00Z')
    registry.upsert(_runtime('codex', project_id=project.project_id, layout=layout, health='pane-foreign'))
    remount_calls: list[str] = []

    def _remount(reason: str) -> None:
        remount_calls.append(reason)
        current = registry.get('codex')
        assert current is not None
        registry.upsert_authority(
            AgentRuntime(
                **{
                    **current.__dict__,
                    'state': AgentState.IDLE,
                    'health': 'healthy',
                    'runtime_ref': 'rmux:pane-b',
                    'pane_ref': {'backend_impl': 'rmux', 'pane_id': 'pane-b'},
                    'active_pane_id': 'pane-b',
                    'last_failure_reason': None,
                }
            )
        )

    loop = RuntimeSupervisionLoop(
        project_id=project.project_id,
        layout=layout,
        config=config,
        registry=registry,
        runtime_service=runtime_service,
        remount_project_fn=_remount,
        clock=lambda: '2026-03-18T00:00:10Z',
        generation_getter=lambda: 8,
    )

    assert loop.reconcile_once() == {'codex': 'healthy'}
    assert remount_calls == ['pane_recovery:codex']
    events = SupervisionEventStore(layout).read_all()
    assert events[0].details['evidence_ledger']['namespace_ref']['backend_impl'] == 'rmux'


@pytest.mark.parametrize('health', ['pane-dead', 'pane-missing'])
def test_rmux_dead_or_missing_pane_recovers_without_percent_pane_id(
    tmp_path: Path,
    monkeypatch,
    health: str,
) -> None:
    project_root = tmp_path / f'repo-rmux-supervision-{health}'
    project_root.mkdir()
    project = bootstrap_project(project_root)
    layout = PathLayout(project_root)
    config = _provider_config('codex')
    registry = AgentRegistry(layout, config)
    runtime_service = RuntimeService(layout, registry, project.project_id, clock=lambda: '2026-03-18T00:00:00Z')
    registry.upsert(_runtime('codex', project_id=project.project_id, layout=layout, health=health, pane_id='pane-a'))
    calls: list[str] = []

    def _refresh(agent_name: str, *, recover: bool = False):
        calls.append(f'{agent_name}:{recover}')
        current = registry.get(agent_name)
        assert current is not None
        recovered = AgentRuntime(
            **{
                **current.__dict__,
                'state': AgentState.IDLE,
                'health': 'healthy',
                'runtime_ref': 'rmux:pane-b',
                'pane_ref': {'backend_impl': 'rmux', 'pane_id': 'pane-b'},
                'active_pane_id': 'pane-b',
                'last_failure_reason': None,
            }
        )
        registry.upsert_authority(recovered)
        return recovered

    monkeypatch.setattr(runtime_service, 'refresh_provider_binding', _refresh)
    loop = RuntimeSupervisionLoop(
        project_id=project.project_id,
        layout=layout,
        config=config,
        registry=registry,
        runtime_service=runtime_service,
        clock=lambda: '2026-03-18T00:00:10Z',
        generation_getter=lambda: 8,
    )

    assert loop.reconcile_once() == {'codex': 'healthy'}
    assert calls == ['codex:True']
    events = SupervisionEventStore(layout).read_all()
    assert events[0].details['evidence_ledger']['pane_ref']['pane_id'] == 'pane-a'
    assert events[-1].details['action'] == 'pane_recover'


def test_rmux_process_dead_recovers_even_when_pane_ref_is_present(tmp_path: Path, monkeypatch) -> None:
    project_root = tmp_path / 'repo-rmux-supervision-process'
    project_root.mkdir()
    project = bootstrap_project(project_root)
    layout = PathLayout(project_root)
    config = _provider_config('codex')
    registry = AgentRegistry(layout, config)
    runtime_service = RuntimeService(layout, registry, project.project_id, clock=lambda: '2026-03-18T00:00:00Z')
    runtime = _runtime('codex', project_id=project.project_id, layout=layout, health='process-dead')
    runtime.process_ref = {'pid': 101, 'health': 'dead'}
    registry.upsert(runtime)
    calls: list[str] = []

    def _refresh(agent_name: str, *, recover: bool = False):
        calls.append(f'{agent_name}:{recover}')
        current = registry.get(agent_name)
        assert current is not None
        recovered = AgentRuntime(
            **{
                **current.__dict__,
                'state': AgentState.IDLE,
                'health': 'healthy',
                'process_ref': {'pid': 202, 'health': 'alive'},
                'last_failure_reason': None,
            }
        )
        registry.upsert_authority(recovered)
        return recovered

    monkeypatch.setattr(runtime_service, 'refresh_provider_binding', _refresh)
    loop = RuntimeSupervisionLoop(
        project_id=project.project_id,
        layout=layout,
        config=config,
        registry=registry,
        runtime_service=runtime_service,
        clock=lambda: '2026-03-18T00:00:10Z',
        generation_getter=lambda: 9,
    )

    assert loop.reconcile_once() == {'codex': 'healthy'}
    assert calls == ['codex:True']
    events = SupervisionEventStore(layout).read_all()
    ledger = events[0].details['evidence_ledger']
    assert ledger['pane_health'] == 'alive'
    assert ledger['process_health'] == 'dead'


def test_rmux_namespace_crash_reflows_by_namespace_ref(tmp_path: Path) -> None:
    project_root = tmp_path / 'repo-rmux-supervision-namespace-crash'
    project_root.mkdir()
    project = bootstrap_project(project_root)
    layout = PathLayout(project_root)
    config = _provider_config('codex')
    registry = AgentRegistry(layout, config)
    runtime_service = RuntimeService(layout, registry, project.project_id, clock=lambda: '2026-03-18T00:00:00Z')
    registry.upsert(_runtime('codex', project_id=project.project_id, layout=layout, health='namespace-crashed'))
    remount_calls: list[str] = []

    def _remount(reason: str) -> None:
        remount_calls.append(reason)
        current = registry.get('codex')
        assert current is not None
        registry.upsert_authority(
            AgentRuntime(
                **{
                    **current.__dict__,
                    'state': AgentState.IDLE,
                    'health': 'healthy',
                    'last_failure_reason': None,
                }
            )
        )

    loop = RuntimeSupervisionLoop(
        project_id=project.project_id,
        layout=layout,
        config=config,
        registry=registry,
        runtime_service=runtime_service,
        remount_project_fn=_remount,
        clock=lambda: '2026-03-18T00:00:10Z',
        generation_getter=lambda: 10,
    )

    assert loop.reconcile_once() == {'codex': 'healthy'}
    assert remount_calls == ['pane_recovery:codex']
    events = SupervisionEventStore(layout).read_all()
    assert events[0].details['evidence_ledger']['namespace_health'] == 'crashed'


def test_rmux_namespace_missing_records_hard_diagnostics_when_reflow_blocked(tmp_path: Path) -> None:
    project_root = tmp_path / 'repo-rmux-supervision-namespace-missing'
    project_root.mkdir()
    project = bootstrap_project(project_root)
    layout = PathLayout(project_root)
    config = _provider_config('codex')
    registry = AgentRegistry(layout, config)
    runtime_service = RuntimeService(layout, registry, project.project_id, clock=lambda: '2026-03-18T00:00:00Z')
    registry.upsert(_runtime('codex', project_id=project.project_id, layout=layout, health='namespace-missing'))
    loop = RuntimeSupervisionLoop(
        project_id=project.project_id,
        layout=layout,
        config=config,
        registry=registry,
        runtime_service=runtime_service,
        remount_project_fn=None,
        clock=lambda: '2026-03-18T00:00:10Z',
        generation_getter=lambda: 10,
    )

    assert loop.reconcile_once() == {'codex': 'namespace-missing'}
    events = SupervisionEventStore(layout).read_all()
    assert events[-1].event_kind == 'recover_failed'
    assert events[-1].details['reason'] == 'namespace-missing'
    assert events[-1].details['action'] == 'namespace_recover'
    assert events[-1].details['evidence_ledger']['namespace_health'] == 'missing'
