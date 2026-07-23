from __future__ import annotations

from pathlib import Path

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


def _runtime(
    agent_name: str,
    *,
    project_id: str,
    layout: PathLayout,
    health: str,
    daemon_ref: dict[str, object],
) -> AgentRuntime:
    return AgentRuntime(
        agent_name=agent_name,
        state=AgentState.DEGRADED,
        pid=101,
        started_at='2026-03-18T00:00:00Z',
        last_seen_at='2026-03-18T00:00:00Z',
        runtime_ref='rmux:pane-a',
        session_ref=str(layout.ccbd_tmux_session_name),
        workspace_path=str(layout.workspace_path(agent_name)),
        project_id=project_id,
        backend_type='pane-backed',
        queue_depth=0,
        socket_path=None,
        health=health,
        backend_impl='rmux',
        namespace_ref={
            'backend_impl': 'rmux',
            'namespace_id': layout.ccbd_tmux_session_name,
            'session_name': layout.ccbd_tmux_session_name,
            'ipc_kind': 'named_pipe',
            'ipc_ref': layout.ccbd_tmux_session_name,
        },
        pane_ref={'backend_impl': 'rmux', 'pane_id': 'pane-a'},
        active_pane_id='pane-a',
        process_ref={'pid': 101, 'health': 'alive'},
        daemon_ref=daemon_ref,
    )


def test_shared_rmux_daemon_crash_records_degraded_only_without_refresh(tmp_path: Path, monkeypatch) -> None:
    project_root = tmp_path / 'repo-rmux-shared-daemon'
    project_root.mkdir()
    project = bootstrap_project(project_root)
    layout = PathLayout(project_root)
    config = _provider_config('codex')
    registry = AgentRegistry(layout, config)
    runtime_service = RuntimeService(layout, registry, project.project_id, clock=lambda: '2026-03-18T00:00:00Z')
    registry.upsert(
        _runtime(
            'codex',
            project_id=project.project_id,
            layout=layout,
            health='daemon-unavailable',
            daemon_ref={
                'backend_impl': 'rmux',
                'daemon_id': 'shared-daemon',
                'scope': 'shared',
                'health': 'crashed',
            },
        )
    )
    refresh_calls: list[str] = []

    def _refresh(agent_name: str, *, recover: bool = False):
        refresh_calls.append(f'{agent_name}:{recover}')
        return registry.get(agent_name)

    monkeypatch.setattr(runtime_service, 'refresh_provider_binding', _refresh)
    loop = RuntimeSupervisionLoop(
        project_id=project.project_id,
        layout=layout,
        config=config,
        registry=registry,
        runtime_service=runtime_service,
        clock=lambda: '2026-03-18T00:00:10Z',
        generation_getter=lambda: 12,
    )

    assert loop.reconcile_once() == {'codex': 'daemon-unavailable'}
    assert refresh_calls == []
    events = SupervisionEventStore(layout).read_all()
    assert len(events) == 1
    assert events[0].event_kind == 'daemon_degraded'
    assert events[0].details['action'] == 'degraded_only'
    assert events[0].details['ownership'] == 'shared_or_unowned'
    assert events[0].details['evidence_ledger']['daemon_health'] == 'dead'
    persisted = registry.get('codex')
    assert persisted is not None
    assert persisted.restart_count == 0
    assert persisted.reconcile_state == 'degraded'


def test_shared_rmux_daemon_generation_approval_does_not_enable_recovery(
    tmp_path: Path,
    monkeypatch,
) -> None:
    project_root = tmp_path / 'repo-rmux-shared-approved-daemon'
    project_root.mkdir()
    project = bootstrap_project(project_root)
    layout = PathLayout(project_root)
    config = _provider_config('codex')
    registry = AgentRegistry(layout, config)
    runtime_service = RuntimeService(layout, registry, project.project_id, clock=lambda: '2026-03-18T00:00:00Z')
    registry.upsert(
        _runtime(
            'codex',
            project_id=project.project_id,
            layout=layout,
            health='daemon-generation-mismatch',
            daemon_ref={
                'backend_impl': 'rmux',
                'daemon_id': 'shared-daemon',
                'scope': 'shared',
                'health': 'stale',
                'generation_approved': True,
            },
        )
    )
    refresh_calls: list[str] = []

    def _refresh(agent_name: str, *, recover: bool = False):
        refresh_calls.append(f'{agent_name}:{recover}')
        return registry.get(agent_name)

    monkeypatch.setattr(runtime_service, 'refresh_provider_binding', _refresh)
    loop = RuntimeSupervisionLoop(
        project_id=project.project_id,
        layout=layout,
        config=config,
        registry=registry,
        runtime_service=runtime_service,
        clock=lambda: '2026-03-18T00:00:10Z',
        generation_getter=lambda: 12,
    )

    assert loop.reconcile_once() == {'codex': 'daemon-generation-mismatch'}
    assert refresh_calls == []
    events = SupervisionEventStore(layout).read_all()
    assert events[-1].event_kind == 'daemon_degraded'
    assert events[-1].details['action'] == 'degraded_only'
    assert events[-1].details['evidence_ledger']['daemon_health'] == 'generation-mismatch'


def test_project_owned_rmux_daemon_generation_mismatch_uses_recovery_refresh(
    tmp_path: Path,
    monkeypatch,
) -> None:
    project_root = tmp_path / 'repo-rmux-owned-daemon'
    project_root.mkdir()
    project = bootstrap_project(project_root)
    layout = PathLayout(project_root)
    config = _provider_config('codex')
    registry = AgentRegistry(layout, config)
    runtime_service = RuntimeService(layout, registry, project.project_id, clock=lambda: '2026-03-18T00:00:00Z')
    runtime = _runtime(
        'codex',
        project_id=project.project_id,
        layout=layout,
        health='daemon-generation-mismatch',
        daemon_ref={
            'backend_impl': 'rmux',
            'daemon_id': 'project-daemon',
            'scope': 'project',
            'health': 'stale',
            'generation_approved': True,
        },
    )
    registry.upsert(runtime)
    refresh_calls: list[str] = []

    def _refresh(agent_name: str, *, recover: bool = False):
        refresh_calls.append(f'{agent_name}:{recover}')
        current = registry.get(agent_name)
        assert current is not None
        recovered = AgentRuntime(
            **{
                **current.__dict__,
                'state': AgentState.IDLE,
                'health': 'healthy',
                'daemon_ref': {
                    'backend_impl': 'rmux',
                    'daemon_id': 'project-daemon-2',
                    'scope': 'project',
                    'health': 'healthy',
                },
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
        generation_getter=lambda: 13,
    )

    assert loop.reconcile_once() == {'codex': 'healthy'}
    assert refresh_calls == ['codex:True']
    events = SupervisionEventStore(layout).read_all()
    assert events[-1].event_kind == 'recover_succeeded'
    assert events[-1].details['action'] == 'daemon_recover'
    assert events[0].details['evidence_ledger']['daemon_health'] == 'generation-mismatch'


def test_runtime_service_attach_persists_daemon_ref_from_real_attach_path(tmp_path: Path) -> None:
    project_root = tmp_path / 'repo-rmux-daemon-attach'
    project_root.mkdir()
    project = bootstrap_project(project_root)
    layout = PathLayout(project_root)
    config = _provider_config('codex')
    registry = AgentRegistry(layout, config)
    runtime_service = RuntimeService(layout, registry, project.project_id, clock=lambda: '2026-03-18T00:00:00Z')

    runtime = runtime_service.attach(
        agent_name='codex',
        workspace_path=str(layout.workspace_path('codex')),
        backend_type='pane-backed',
        runtime_ref='rmux:pane-a',
        health='daemon-generation-mismatch',
        backend_impl='rmux',
        namespace_ref={
            'backend_impl': 'rmux',
            'namespace_id': 'ns-1',
            'session_name': 'ns-1',
            'backend_daemon_evidence': {
                'health': 'stale',
                'daemon_ref': {
                    'backend_impl': 'rmux',
                    'daemon_id': 'project-daemon',
                    'scope': 'project',
                    'generation_approved': True,
                },
            },
        },
        pane_ref={'backend_impl': 'rmux', 'pane_id': 'pane-a'},
    )

    assert runtime.daemon_ref == {
        'backend_impl': 'rmux',
        'daemon_id': 'project-daemon',
        'scope': 'project',
        'generation_approved': True,
        'health': 'stale',
    }
    assert registry.get('codex').daemon_ref == runtime.daemon_ref
