from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import Any

from agents.models import AgentRuntime
from ccbd.project_focus.tmux import backend_for_namespace
from ccbd.services.project_namespace_state_runtime.namespace_projection import (
    HERDR_BACKEND_FAMILY,
    resolved_namespace_backend_family,
)
from platforms.windows.herdr.runtime.contracts import (
    HerdrRuntimeBinding,
    HerdrRuntimeBoundPane,
)
from platforms.windows.herdr.runtime.events import (
    HerdrRuntimeEventProjector,
    poll_runtime_snapshot,
)


@dataclass(frozen=True)
class HerdrSnapshotPollingResult:
    polled: bool
    changed_pane_ids: tuple[str, ...] = ()
    updated_agents: tuple[str, ...] = ()
    skipped_reason: str | None = None
    failure_reason: str | None = None


class _SnapshotCaptureBackend:
    def __init__(self, backend: object) -> None:
        self._backend = backend
        self.snapshot: Mapping[str, object] | None = None

    def runtime_snapshot(self) -> Mapping[str, object] | None:
        snapshot_fn = getattr(self._backend, 'runtime_snapshot', None)
        if not callable(snapshot_fn):
            return None
        snapshot = snapshot_fn()
        if isinstance(snapshot, Mapping):
            self.snapshot = snapshot
        return snapshot


def poll_herdr_runtime_snapshots(*, registry, namespace_controller) -> HerdrSnapshotPollingResult:
    if registry is None or namespace_controller is None:
        return HerdrSnapshotPollingResult(polled=False, skipped_reason='missing_dependencies')
    namespace = namespace_controller.load()
    if not _namespace_is_herdr(namespace):
        return HerdrSnapshotPollingResult(polled=False, skipped_reason='non_herdr_namespace')
    runtimes = _herdr_bound_runtimes(registry, namespace)
    if not runtimes:
        return HerdrSnapshotPollingResult(polled=False, skipped_reason='no_bound_runtimes')
    binding = _binding_for_runtimes(registry, namespace, runtimes)
    if binding is None:
        return HerdrSnapshotPollingResult(polled=False, skipped_reason='no_binding')
    backend = backend_for_namespace(namespace_controller._backend_factory, namespace)
    if not callable(getattr(backend, 'runtime_snapshot', None)):
        return HerdrSnapshotPollingResult(polled=False, skipped_reason='snapshot_unsupported')

    projector = HerdrRuntimeEventProjector(binding)
    capture = _SnapshotCaptureBackend(backend)
    try:
        changed_pane_ids = poll_runtime_snapshot(projector, binding, capture)
    except Exception as exc:
        failure = f'herdr_snapshot_polling: {type(exc).__name__}: {exc}'
        updated = _record_polling_failure(registry, runtimes, failure_reason=failure)
        return HerdrSnapshotPollingResult(
            polled=True,
            updated_agents=updated,
            failure_reason=failure,
        )

    snapshot = capture.snapshot
    if snapshot is None:
        return HerdrSnapshotPollingResult(polled=True)
    owned_snapshot = _snapshot_for_binding(snapshot, binding=binding)
    updated = _persist_snapshot_changes(
        registry,
        runtimes,
        snapshot=owned_snapshot,
        projector=projector,
    )
    return HerdrSnapshotPollingResult(
        polled=True,
        changed_pane_ids=tuple(changed_pane_ids),
        updated_agents=updated,
    )


def _namespace_is_herdr(namespace) -> bool:
    if namespace is None:
        return False
    return (
        resolved_namespace_backend_family(
            getattr(namespace, 'backend_impl', None),
            getattr(namespace, 'namespace_backend_family', None),
        )
        == HERDR_BACKEND_FAMILY
    )


def _herdr_bound_runtimes(registry, namespace) -> tuple[AgentRuntime, ...]:
    result: list[AgentRuntime] = []
    project_id = str(getattr(namespace, 'project_id', '') or '').strip()
    for runtime in registry.list_all():
        if project_id and str(getattr(runtime, 'project_id', '') or '').strip() != project_id:
            continue
        if not _runtime_pane_id(runtime):
            continue
        result.append(runtime)
    return tuple(result)


def _binding_for_runtimes(
    registry,
    namespace,
    runtimes: tuple[AgentRuntime, ...],
) -> HerdrRuntimeBinding | None:
    generation = _positive_int(
        getattr(namespace, 'namespace_epoch', None),
        fallback=1,
    )
    panes = tuple(_bound_pane_for_runtime(registry, runtime) for runtime in runtimes)
    panes = tuple(pane for pane in panes if pane is not None)
    if not panes:
        return None
    namespace_ref = namespace.namespace_ref() if callable(getattr(namespace, 'namespace_ref', None)) else {}
    session_name = _text(
        namespace_ref.get('session_name') if isinstance(namespace_ref, Mapping) else None,
        getattr(namespace, 'namespace_session_name', None),
        getattr(namespace, 'tmux_session_name', None),
    )
    workspace_id = _text(
        namespace_ref.get('namespace_id') if isinstance(namespace_ref, Mapping) else None,
        getattr(namespace, 'namespace_id', None),
        getattr(namespace, 'tmux_session_name', None),
    )
    server_id = _text(
        namespace_ref.get('ipc_ref') if isinstance(namespace_ref, Mapping) else None,
        session_name,
        workspace_id,
    )
    frontend = getattr(namespace, 'frontend', None)
    return HerdrRuntimeBinding(
        project_id=_text(getattr(namespace, 'project_id', None)) or None,
        server_id=server_id or 'herdr',
        server_version='unknown',
        api_schema='Herdr API',
        session_name=session_name or 'herdr',
        workspace_id=workspace_id or session_name or 'herdr',
        runtime_generation=generation,
        ready=True,
        capabilities={},
        panes=panes,
        frontend=dict(frontend) if isinstance(frontend, Mapping) else None,
    )


def _bound_pane_for_runtime(registry, runtime: AgentRuntime) -> HerdrRuntimeBoundPane | None:
    pane_id = _runtime_pane_id(runtime)
    if not pane_id:
        return None
    provider = _text(getattr(runtime, 'provider', None))
    if not provider:
        try:
            provider = _text(getattr(registry.spec_for(runtime.agent_name), 'provider', None))
        except Exception:
            provider = ''
    state = _runtime_seed_state(runtime, pane_id=pane_id)
    return HerdrRuntimeBoundPane(
        slot=_text(getattr(runtime, 'slot_key', None), runtime.agent_name),
        pane_id=pane_id,
        agent_id=runtime.agent_name,
        provider_kind=provider or 'unknown',
        state=state or 'unknown',
        state_seq=_runtime_seed_seq(runtime, pane_id=pane_id),
    )


def _persist_snapshot_changes(
    registry,
    runtimes: tuple[AgentRuntime, ...],
    *,
    snapshot: dict[str, object],
    projector: HerdrRuntimeEventProjector,
) -> tuple[str, ...]:
    updated: list[str] = []
    for runtime in runtimes:
        pane_id = _runtime_pane_id(runtime)
        status = projector.status_for_pane(pane_id) if pane_id else None
        current_snapshot = getattr(runtime, 'herdr_runtime_snapshot', None)
        pane_state = 'alive' if status is not None else _missing_pane_state(snapshot, pane_id)
        next_runtime = replace(
            runtime,
            herdr_runtime_snapshot=snapshot,
            pane_state=pane_state or runtime.pane_state,
            last_failure_reason=None
            if _is_herdr_polling_failure(getattr(runtime, 'last_failure_reason', None))
            else runtime.last_failure_reason,
        )
        if current_snapshot == snapshot and next_runtime == runtime:
            continue
        saved = registry.upsert_authority(next_runtime)
        if saved != runtime:
            updated.append(runtime.agent_name)
    return tuple(updated)


def _snapshot_for_binding(
    snapshot: Mapping[str, object],
    *,
    binding: HerdrRuntimeBinding,
) -> dict[str, object]:
    result = dict(snapshot)
    pane_ids = {pane.pane_id for pane in binding.panes}
    panes = snapshot.get('panes')
    if not isinstance(panes, list):
        return result
    result['panes'] = [
        dict(pane)
        for pane in panes
        if isinstance(pane, Mapping)
        and str(pane.get('pane_id') or '').strip() in pane_ids
        and _snapshot_pane_matches_binding(pane, binding=binding)
    ]
    return result


def _snapshot_pane_matches_binding(
    pane: Mapping[str, object],
    *,
    binding: HerdrRuntimeBinding,
) -> bool:
    for key, expected in (
        ('workspace_id', binding.workspace_id),
        ('session_name', binding.session_name),
    ):
        value = _text(pane.get(key))
        if value and value != expected:
            return False
    return True


def _record_polling_failure(
    registry,
    runtimes: tuple[AgentRuntime, ...],
    *,
    failure_reason: str,
) -> tuple[str, ...]:
    snapshot = {
        'schema_version': 1,
        'runtime_state': 'unknown',
        'source': 'herdr_snapshot_polling',
        'poll_error': failure_reason,
    }
    updated: list[str] = []
    for runtime in runtimes:
        next_runtime = replace(
            runtime,
            herdr_runtime_snapshot=snapshot,
            pane_state='unknown',
            health='unknown',
            last_failure_reason=failure_reason,
        )
        saved = registry.upsert_authority(next_runtime)
        if saved != runtime:
            updated.append(runtime.agent_name)
    return tuple(updated)


def _missing_pane_state(snapshot: Mapping[str, object], pane_id: str | None) -> str | None:
    if not pane_id:
        return None
    panes = snapshot.get('panes')
    if not isinstance(panes, list):
        return None
    return 'missing'


def _runtime_pane_id(runtime: AgentRuntime) -> str | None:
    return _text(getattr(runtime, 'active_pane_id', None), getattr(runtime, 'pane_id', None)) or None


def _runtime_seed_state(runtime: AgentRuntime, *, pane_id: str) -> str:
    snapshot_state = _snapshot_pane_value(
        getattr(runtime, 'herdr_runtime_snapshot', None),
        pane_id=pane_id,
        keys=('runtime_state', 'state', 'herdr_runtime_state'),
    )
    if snapshot_state:
        return snapshot_state.lower()
    for container in (getattr(runtime, 'pane_ref', None), getattr(runtime, 'provider_runtime_backend_ref', None)):
        if not isinstance(container, Mapping):
            continue
        for key in ('runtime_state', 'state', 'herdr_runtime_state'):
            value = _text(container.get(key))
            if value:
                return value.lower()
    return _text(getattr(runtime, 'pane_state', None)) or 'unknown'


def _runtime_seed_seq(runtime: AgentRuntime, *, pane_id: str) -> int:
    snapshot_seq = _snapshot_pane_value(
        getattr(runtime, 'herdr_runtime_snapshot', None),
        pane_id=pane_id,
        keys=('state_seq', 'seq'),
    )
    try:
        if snapshot_seq is not None:
            seq = int(snapshot_seq)
            if seq >= 0:
                return seq
    except (TypeError, ValueError):
        pass
    for container in (getattr(runtime, 'pane_ref', None), getattr(runtime, 'provider_runtime_backend_ref', None)):
        if not isinstance(container, Mapping):
            continue
        for key in ('state_seq', 'seq'):
            value = container.get(key)
            try:
                seq = int(value)
            except (TypeError, ValueError):
                continue
            if seq >= 0:
                return seq
    return 0


def _snapshot_pane_value(
    snapshot: object,
    *,
    pane_id: str,
    keys: tuple[str, ...],
) -> Any | None:
    if not isinstance(snapshot, Mapping):
        return None
    panes = snapshot.get('panes')
    if not isinstance(panes, list):
        return None
    for pane in panes:
        if not isinstance(pane, Mapping):
            continue
        if _text(pane.get('pane_id')) != pane_id:
            continue
        for key in keys:
            value = pane.get(key)
            if value is not None and str(value).strip():
                return value
        return None
    return None


def _positive_int(value: object, *, fallback: int) -> int:
    try:
        result = int(value or 0)
    except (TypeError, ValueError):
        return fallback
    return result if result > 0 else fallback


def _text(*values: object) -> str:
    for value in values:
        text = str(value or '').strip()
        if text:
            return text
    return ''


def _is_herdr_polling_failure(value: object) -> bool:
    return str(value or '').startswith('herdr_snapshot_polling:')


__all__ = [
    'HerdrSnapshotPollingResult',
    'poll_herdr_runtime_snapshots',
]
