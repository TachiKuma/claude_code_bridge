from __future__ import annotations

import time

from ccbd.models import CcbdStartupAgentResult
from terminal_runtime.tmux_identity import pane_visual

from .agent_runtime_binding import resolve_runtime_binding_state
from .agent_runtime_models import StartAgentExecution


def _namespace_assigned_pane_id(
    *,
    assigned_pane_id: str | None,
    stale_binding: bool,
    tmux_socket_path: str | None,
) -> str | None:
    if stale_binding:
        return None
    pane_id = str(assigned_pane_id or '').strip()
    if not pane_id or not pane_id.startswith('%'):
        return None
    if not str(tmux_socket_path or '').strip():
        return None
    return pane_id


def _binding_attr(binding, field_name: str):
    return getattr(binding, field_name, None) if binding is not None else None


def start_agent_runtime(
    *,
    context,
    command,
    runtime_service,
    agent_name: str,
    spec,
    plan,
    binding,
    raw_binding,
    stale_binding: bool,
    assigned_pane_id: str | None,
    style_index: int,
    project_id: str,
    tmux_socket_path: str | None,
    namespace_epoch: int | None,
    ensure_agent_runtime_fn,
    launch_binding_hint_fn,
    relabel_project_namespace_pane_fn,
    same_tmux_socket_path_fn,
    workspace_window_id: str | None = None,
    workspace_epoch: int | None = None,
    window_name: str | None = None,
    namespace_pane_records: dict[str, object] | None = None,
    provider_prepared: bool = False,
    provider_prepare_ms: float = 0.0,
    binding_reject_reason: str | None = None,
) -> StartAgentExecution:
    started_ns = time.monotonic_ns()
    original_pane_id = _binding_attr(binding, 'pane_id') or _binding_attr(binding, 'active_pane_id')
    original_namespace_record = (namespace_pane_records or {}).get(str(original_pane_id or ''))
    binding_state = resolve_runtime_binding_state(
        context=context,
        command=command,
        agent_name=agent_name,
        spec=spec,
        plan=plan,
        binding=binding,
        raw_binding=raw_binding,
        stale_binding=stale_binding,
        assigned_pane_id=assigned_pane_id,
        style_index=style_index,
        project_id=project_id,
        tmux_socket_path=tmux_socket_path,
        namespace_epoch=namespace_epoch,
        window_name=window_name,
        ensure_agent_runtime_fn=ensure_agent_runtime_fn,
        launch_binding_hint_fn=launch_binding_hint_fn,
        relabel_project_namespace_pane_fn=relabel_project_namespace_pane_fn,
        same_tmux_socket_path_fn=same_tmux_socket_path_fn,
        provider_prepared=provider_prepared,
        reused_pane_identity_current=_pane_identity_is_current(
            original_namespace_record,
            binding=binding,
            agent_name=agent_name,
            project_id=project_id,
            style_index=style_index,
            window_name=window_name,
            namespace_epoch=namespace_epoch,
        ),
    )
    namespace_pane_id = _namespace_assigned_pane_id(
        assigned_pane_id=assigned_pane_id,
        stale_binding=stale_binding,
        tmux_socket_path=tmux_socket_path,
    )
    namespace_runtime_ref = f'tmux:{namespace_pane_id}' if namespace_pane_id else None
    namespace_socket_path = str(tmux_socket_path or '').strip() or None
    binding_pane_id = _binding_attr(binding_state.binding, 'pane_id') or namespace_pane_id
    namespace_record = (namespace_pane_records or {}).get(str(binding_pane_id or ''))
    tmux_window_id = (
        getattr(namespace_record, 'window_id', None)
        or _binding_attr(binding_state.binding, 'tmux_window_id')
    )
    tmux_window_name = (
        window_name
        or getattr(namespace_record, 'ccb_window', None)
        or getattr(namespace_record, 'window_name', None)
        or _binding_attr(binding_state.binding, 'tmux_window_name')
    )
    attach_kwargs = dict(
        agent_name=agent_name,
        workspace_path=str(plan.workspace_path),
        backend_type=spec.runtime_mode.value,
        runtime_ref=binding_state.runtime_ref or namespace_runtime_ref,
        session_ref=binding_state.session_ref,
        health=binding_state.health,
        provider=spec.provider,
        runtime_root=_binding_attr(binding_state.binding, 'runtime_root'),
        runtime_pid=_binding_attr(binding_state.binding, 'runtime_pid'),
        terminal_backend=_binding_attr(binding_state.binding, 'terminal') or ('tmux' if namespace_pane_id else None),
        pane_id=_binding_attr(binding_state.binding, 'pane_id') or namespace_pane_id,
        active_pane_id=_binding_attr(binding_state.binding, 'active_pane_id') or namespace_pane_id,
        pane_title_marker=_binding_attr(binding_state.binding, 'pane_title_marker'),
        pane_state=_binding_attr(binding_state.binding, 'pane_state'),
        tmux_socket_name=_binding_attr(binding_state.binding, 'tmux_socket_name'),
        tmux_socket_path=_binding_attr(binding_state.binding, 'tmux_socket_path') or (
            namespace_socket_path if namespace_pane_id else None
        ),
        tmux_window_name=tmux_window_name,
        tmux_window_id=tmux_window_id,
        session_file=_binding_attr(binding_state.binding, 'session_file'),
        session_id=_binding_attr(binding_state.binding, 'session_id'),
        slot_key=agent_name,
        window_id=tmux_window_id or (workspace_window_id if window_name is None else None),
        workspace_epoch=workspace_epoch,
        lifecycle_state=binding_state.lifecycle_state,
        managed_by='ccbd',
        binding_source='provider-session',
    )
    registry = getattr(runtime_service, '_registry', None)
    existing = registry.get(agent_name) if registry is not None else None
    attempt_id = str(getattr(existing, 'mount_attempt_id', '') or '').strip() or None
    if attempt_id and getattr(existing, 'reconcile_state', None) == 'starting':
        runtime, applied = runtime_service.attach_mount_attempt_authority(
            attempt_id=attempt_id,
            **attach_kwargs,
        )
        if not applied:
            runtime = runtime or (registry.get(agent_name) if registry is not None else None)
    else:
        runtime = runtime_service.attach(**attach_kwargs)

    actions_taken = list(binding_state.actions_taken)
    reused_existing_binding = binding is not None and binding_state.agent_action == 'attached'
    if command.restore and binding_state.agent_action != 'degraded' and not reused_existing_binding:
        runtime_service.restore(agent_name)
        actions_taken.append(f'restore_runtime:{agent_name}')

    return StartAgentExecution(
        agent_result=CcbdStartupAgentResult(
            agent_name=agent_name,
            provider=spec.provider,
            action=binding_state.agent_action,
            health=binding_state.health,
            workspace_path=str(plan.workspace_path),
            runtime_ref=runtime.runtime_ref,
            session_ref=runtime.session_ref,
            lifecycle_state=runtime.lifecycle_state,
            desired_state=runtime.desired_state,
            reconcile_state=runtime.reconcile_state,
            binding_source=runtime.binding_source.value,
            terminal_backend=runtime.terminal_backend,
            tmux_socket_name=runtime.tmux_socket_name,
            tmux_socket_path=runtime.tmux_socket_path,
            tmux_window_name=runtime.tmux_window_name,
            tmux_window_id=runtime.tmux_window_id,
            pane_id=runtime.pane_id,
            active_pane_id=runtime.active_pane_id,
            pane_state=runtime.pane_state,
            runtime_pid=runtime.runtime_pid,
            runtime_root=runtime.runtime_root,
            failure_reason='stale_binding_unresolved' if binding_state.agent_action == 'degraded' else None,
            binding_reject_reason=(
                binding_reject_reason if binding_state.agent_action in {'launched', 'relaunched', 'degraded'} else None
            ),
            duration_ms=(time.monotonic_ns() - started_ns) / 1_000_000,
            provider_prepare_ms=provider_prepare_ms,
            provider_prepare_count=int(bool(provider_prepared)),
        ),
        actions_taken=tuple(actions_taken),
        socket_name=binding_state.socket_name or (namespace_socket_path if namespace_pane_id else None),
        runtime_pane_id=binding_state.runtime_pane_id or namespace_pane_id,
        project_socket_active_pane_id=binding_state.project_socket_active_pane_id or namespace_pane_id,
    )


def _pane_identity_is_current(
    record,
    *,
    binding,
    agent_name: str,
    project_id: str,
    style_index: int,
    window_name: str | None,
    namespace_epoch: int | None,
) -> bool:
    if record is None or binding is None:
        return False
    visual = pane_visual(
        project_id=project_id,
        slot_key=agent_name,
        order_index=style_index,
        is_cmd=False,
        role='agent',
    )
    expected = {
        'pane_title': agent_name,
        'agent_label': agent_name,
        'role': 'agent',
        'slot_key': agent_name,
        'project_id': project_id,
        'managed_by': 'ccbd',
        'label_style': visual.label_style,
        'border_style': visual.border_style,
        'active_border_style': visual.active_border_style,
    }
    if any(str(getattr(record, field, '') or '').strip() != value for field, value in expected.items()):
        return False
    if window_name is not None and str(getattr(record, 'ccb_window', '') or '').strip() != window_name:
        return False
    if namespace_epoch is not None and getattr(record, 'namespace_epoch', None) != int(namespace_epoch):
        return False
    ccb_session_id = str(getattr(binding, 'ccb_session_id', '') or '').strip()
    if ccb_session_id and str(getattr(record, 'ccb_session_id', '') or '').strip() != ccb_session_id:
        return False
    return True


__all__ = ['start_agent_runtime']
