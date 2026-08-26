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
from ccbd.services.herdr_snapshot_polling import (
    poll_herdr_runtime_events,
    poll_herdr_runtime_snapshots,
)
from ccbd.services.project_namespace_runtime.models import ProjectNamespace
from ccbd.services.project_namespace_state import ProjectNamespaceState
from ccbd.services.registry import AgentRegistry
from project.ids import compute_project_id
from storage.paths import PathLayout


NOW = '2026-08-24T12:00:00Z'


class _NamespaceController:
    def __init__(self, namespace: ProjectNamespace, backend: object) -> None:
        self._namespace = namespace
        self._backend_factory = lambda **_kwargs: backend

    def load(self) -> ProjectNamespace:
        return self._namespace


class _SnapshotBackend:
    backend_impl = 'herdr'

    def __init__(self, snapshot: dict[str, object]) -> None:
        self.snapshot = snapshot
        self.calls = 0

    def runtime_snapshot(self) -> dict[str, object]:
        self.calls += 1
        return self.snapshot


class _NoSnapshotBackend:
    backend_impl = 'herdr'


class _FailingSnapshotBackend:
    backend_impl = 'herdr'

    def runtime_snapshot(self) -> dict[str, object]:
        raise RuntimeError('socket unavailable')


class _EventsBackend(_SnapshotBackend):
    backend_impl = 'herdr'

    def __init__(
        self,
        snapshot: dict[str, object],
        *,
        events: object = None,
        capability: str = 'supported',
    ) -> None:
        super().__init__(snapshot)
        self.events = [] if events is None else events
        self.capability = capability

    def runtime_capabilities(self) -> dict[str, str]:
        return {'runtime_events': self.capability}

    def runtime_events(self) -> object:
        self.calls += 1
        return self.events


def _spec(name: str, provider: str) -> AgentSpec:
    return AgentSpec(
        name=name,
        provider=provider,
        target='.',
        workspace_mode=WorkspaceMode.INPLACE,
        workspace_root=None,
        runtime_mode=RuntimeMode.PANE_BACKED,
        restore_default=RestoreMode.AUTO,
        permission_default=PermissionMode.MANUAL,
        queue_policy=QueuePolicy.SERIAL_PER_AGENT,
    )


def _config() -> ProjectConfig:
    agents = {
        'agent1': _spec('agent1', 'codex'),
        'agent2': _spec('agent2', 'claude'),
    }
    return ProjectConfig(
        version=2,
        default_agents=('agent1', 'agent2'),
        agents=agents,
        cmd_enabled=False,
        layout_spec='agent1:codex, agent2:claude',
    )


def _runtime(agent_name: str, *, project_id: str, pane_id: str) -> AgentRuntime:
    return AgentRuntime(
        agent_name=agent_name,
        state=AgentState.IDLE,
        pid=100,
        started_at=NOW,
        last_seen_at=NOW,
        runtime_ref=f'herdr:{pane_id}',
        session_ref='ccb-herdr',
        workspace_path='/tmp/workspace',
        project_id=project_id,
        backend_type='herdr',
        queue_depth=0,
        socket_path=None,
        health='healthy',
        provider=None,
        terminal_backend='herdr',
        pane_id=pane_id,
        pane_state='alive',
        reconcile_state='steady',
        runtime_generation=5,
    )


def _namespace(project_id: str) -> ProjectNamespace:
    return ProjectNamespace.from_state(
        ProjectNamespaceState(
            project_id=project_id,
            namespace_epoch=5,
            tmux_socket_path='',
            tmux_session_name='ccb-herdr',
            namespace_backend_family='herdr-native',
            backend_impl='herdr',
            namespace_id='workspace-1',
            namespace_session_name='ccb-herdr',
            namespace_ipc_kind='herdr_socket',
            namespace_ipc_ref='herdr://ccb-herdr',
            layout_version=3,
            workspace_window_name='workspace',
            ui_attachable=True,
        )
    )


def _registry(tmp_path: Path) -> tuple[PathLayout, ProjectConfig, AgentRegistry]:
    project_root = tmp_path / 'repo'
    project_root.mkdir()
    layout = PathLayout(project_root)
    config = _config()
    return layout, config, AgentRegistry(layout, config)


def test_herdr_snapshot_polling_persists_snapshot_and_invalidates_project_view_revision(tmp_path: Path) -> None:
    layout, config, registry = _registry(tmp_path)
    project_id = compute_project_id(layout.project_root)
    registry.upsert(_runtime('agent1', project_id=project_id, pane_id='pane-1'))
    revision = registry.project_view_revision
    snapshot = {
        'panes': [
            {'pane_id': 'pane-1', 'workspace_id': 'workspace-1', 'state': 'blocked', 'seq': 2},
        ],
    }
    backend = _SnapshotBackend(snapshot)
    controller = _NamespaceController(_namespace(project_id), backend)

    result = poll_herdr_runtime_snapshots(
        registry=registry,
        namespace_controller=controller,
    )

    runtime = registry.get('agent1')
    assert result.polled is True
    assert result.changed_pane_ids == ('pane-1',)
    assert result.updated_agents == ('agent1',)
    assert runtime is not None
    assert runtime.herdr_runtime_snapshot == snapshot
    assert runtime.pane_state == 'alive'
    assert registry.project_view_revision == revision + 1
    assert AgentRegistry(layout, config).get('agent1').herdr_runtime_snapshot == snapshot  # type: ignore[union-attr]

    second = poll_herdr_runtime_snapshots(
        registry=registry,
        namespace_controller=controller,
    )

    assert second.changed_pane_ids == ()
    assert second.updated_agents == ()
    assert registry.project_view_revision == revision + 1
    assert backend.calls == 2


def test_herdr_snapshot_polling_noops_when_backend_has_no_snapshot(tmp_path: Path) -> None:
    layout, _config_value, registry = _registry(tmp_path)
    project_id = compute_project_id(layout.project_root)
    registry.upsert(_runtime('agent1', project_id=project_id, pane_id='pane-1'))
    revision = registry.project_view_revision

    result = poll_herdr_runtime_snapshots(
        registry=registry,
        namespace_controller=_NamespaceController(_namespace(project_id), _NoSnapshotBackend()),
    )

    assert result.polled is False
    assert result.skipped_reason == 'snapshot_unsupported'
    assert registry.get('agent1').herdr_runtime_snapshot is None  # type: ignore[union-attr]
    assert registry.project_view_revision == revision


def test_herdr_snapshot_polling_does_not_persist_foreign_workspace_pane_state(tmp_path: Path) -> None:
    layout, _config_value, registry = _registry(tmp_path)
    project_id = compute_project_id(layout.project_root)
    registry.upsert(_runtime('agent1', project_id=project_id, pane_id='shared-pane'))
    snapshot = {
        'panes': [
            {
                'pane_id': 'shared-pane',
                'workspace_id': 'other-workspace',
                'state': 'blocked',
                'seq': 2,
            },
        ],
    }

    result = poll_herdr_runtime_snapshots(
        registry=registry,
        namespace_controller=_NamespaceController(_namespace(project_id), _SnapshotBackend(snapshot)),
    )

    runtime = registry.get('agent1')
    assert result.updated_agents == ('agent1',)
    assert runtime is not None
    assert runtime.herdr_runtime_snapshot == {'panes': []}
    assert runtime.pane_state == 'missing'


def test_herdr_snapshot_polling_records_unknown_on_snapshot_failure(tmp_path: Path) -> None:
    layout, _config_value, registry = _registry(tmp_path)
    project_id = compute_project_id(layout.project_root)
    registry.upsert(_runtime('agent1', project_id=project_id, pane_id='pane-1'))

    result = poll_herdr_runtime_snapshots(
        registry=registry,
        namespace_controller=_NamespaceController(_namespace(project_id), _FailingSnapshotBackend()),
    )

    runtime = registry.get('agent1')
    assert result.polled is True
    assert result.failure_reason is not None
    assert result.updated_agents == ('agent1',)
    assert runtime is not None
    assert runtime.herdr_runtime_snapshot is not None
    assert runtime.herdr_runtime_snapshot['runtime_state'] == 'unknown'
    assert runtime.herdr_runtime_snapshot['source'] == 'herdr_snapshot_polling'
    assert runtime.pane_state == 'unknown'
    assert runtime.health == 'unknown'
    assert runtime.last_failure_reason == result.failure_reason


def test_herdr_runtime_events_polling_persists_event_derived_status_with_source(tmp_path: Path) -> None:
    layout, _config_value, registry = _registry(tmp_path)
    project_id = compute_project_id(layout.project_root)
    registry.upsert(_runtime('agent1', project_id=project_id, pane_id='pane-1'))
    backend = _EventsBackend(
        {
            'panes': [
                {'pane_id': 'pane-1', 'workspace_id': 'workspace-1', 'state': 'idle', 'seq': 1},
            ]
        },
        events=[
            {
                'event_id': 'evt-1',
                'server_id': 'herdr://ccb-herdr',
                'session_name': 'ccb-herdr',
                'workspace_id': 'workspace-1',
                'pane_id': 'pane-1',
                'agent_id': 'agent1',
                'provider_kind': 'codex',
                'runtime_generation': 5,
                'seq': 4,
                'state': 'blocked',
                'occurred_at': '2026-08-24T12:00:01Z',
            }
        ],
    )
    controller = _NamespaceController(_namespace(project_id), backend)

    result = poll_herdr_runtime_events(
        registry=registry,
        namespace_controller=controller,
    )

    runtime = registry.get('agent1')
    assert result.polled is True
    assert result.source == 'event'
    assert result.fallback_reason is None
    assert result.changed_pane_ids == ('pane-1',)
    assert runtime is not None
    assert runtime.herdr_runtime_snapshot is not None
    assert runtime.herdr_runtime_snapshot['source'] == 'event'
    assert runtime.herdr_runtime_snapshot['panes'][0]['runtime_state'] == 'blocked'
    assert runtime.herdr_runtime_snapshot['panes'][0]['seq'] == 4


def test_herdr_runtime_events_polling_falls_back_to_snapshot_polling_with_reason(
    tmp_path: Path,
) -> None:
    layout, _config_value, registry = _registry(tmp_path)
    project_id = compute_project_id(layout.project_root)
    registry.upsert(_runtime('agent1', project_id=project_id, pane_id='pane-1'))
    backend = _EventsBackend(
        {
            'panes': [
                {'pane_id': 'pane-1', 'workspace_id': 'workspace-1', 'state': 'blocked', 'seq': 3},
            ]
        },
        capability='unsupported',
    )
    controller = _NamespaceController(_namespace(project_id), backend)

    result = poll_herdr_runtime_events(
        registry=registry,
        namespace_controller=controller,
    )

    runtime = registry.get('agent1')
    assert result.polled is True
    assert result.source == 'snapshot_polling'
    assert result.fallback_reason == 'runtime_events_unsupported'
    assert runtime is not None
    assert runtime.herdr_runtime_snapshot is not None
    assert runtime.herdr_runtime_snapshot['source'] == 'snapshot_polling'
    assert runtime.herdr_runtime_snapshot['fallback_reason'] == 'runtime_events_unsupported'


def test_herdr_runtime_events_polling_falls_back_when_event_batch_is_invalid(
    tmp_path: Path,
) -> None:
    layout, _config_value, registry = _registry(tmp_path)
    project_id = compute_project_id(layout.project_root)
    registry.upsert(_runtime('agent1', project_id=project_id, pane_id='pane-1'))
    backend = _EventsBackend(
        {
            'panes': [
                {'pane_id': 'pane-1', 'workspace_id': 'workspace-1', 'state': 'working', 'seq': 8},
            ]
        },
        events={'not': 'a list'},
    )
    controller = _NamespaceController(_namespace(project_id), backend)

    result = poll_herdr_runtime_events(
        registry=registry,
        namespace_controller=controller,
    )

    runtime = registry.get('agent1')
    assert result.polled is True
    assert result.source == 'snapshot_polling'
    assert result.fallback_reason == 'subscription_failed:invalid_event_batch'
    assert runtime is not None
    assert runtime.herdr_runtime_snapshot is not None
    assert runtime.herdr_runtime_snapshot['source'] == 'snapshot_polling'
    assert runtime.herdr_runtime_snapshot['fallback_reason'] == 'subscription_failed:invalid_event_batch'
    assert runtime.herdr_runtime_snapshot['panes'][0]['runtime_state'] == 'working'


def test_herdr_runtime_events_polling_preserves_agent_explain_snapshot_source(
    tmp_path: Path,
) -> None:
    layout, _config_value, registry = _registry(tmp_path)
    project_id = compute_project_id(layout.project_root)
    registry.upsert(_runtime('agent1', project_id=project_id, pane_id='pane-1'))
    backend = _EventsBackend(
        {
            'panes': [
                {
                    'pane_id': 'pane-1',
                    'workspace_id': 'workspace-1',
                    'agent_status': 'idle',
                    'runtime_state': 'working',
                    'source': 'agent_explain',
                    'seq': 20,
                },
            ]
        },
        capability='unsupported',
    )
    controller = _NamespaceController(_namespace(project_id), backend)

    result = poll_herdr_runtime_events(
        registry=registry,
        namespace_controller=controller,
    )

    runtime = registry.get('agent1')
    assert result.polled is True
    assert result.source == 'snapshot_polling'
    assert result.fallback_reason == 'runtime_events_unsupported'
    assert runtime is not None
    assert runtime.herdr_runtime_snapshot is not None
    pane = runtime.herdr_runtime_snapshot['panes'][0]
    assert pane['runtime_state'] == 'working'
    assert pane['source'] == 'agent_explain'
    assert pane['seq'] == 20
