from __future__ import annotations


MUX_RUNTIME_BACKENDS = {'tmux', 'rmux', 'psmux'}


def mux_backend_from_runtime_ref(runtime_ref: str | None) -> str | None:
    value = str(runtime_ref or '').strip()
    if ':' not in value:
        return None
    backend, _pane = value.split(':', 1)
    backend = backend.strip().lower()
    return backend if backend in MUX_RUNTIME_BACKENDS else None


def mux_pane_id_from_runtime_ref(runtime_ref: str | None) -> str | None:
    value = str(runtime_ref or '').strip()
    backend = mux_backend_from_runtime_ref(value)
    if backend is None:
        return None
    pane_id = value.split(':', 1)[1].strip()
    if not pane_id:
        return None
    if backend == 'tmux' and not pane_id.startswith('%'):
        return None
    return pane_id


def binding_pane_id(binding) -> str | None:
    backend = mux_backend_from_runtime_ref(getattr(binding, 'runtime_ref', None))
    for attr in ('active_pane_id', 'pane_id'):
        pane_id = str(getattr(binding, attr, None) or '').strip()
        if not pane_id:
            continue
        if backend == 'tmux' and not pane_id.startswith('%'):
            continue
        if backend in {'rmux', 'psmux'} or pane_id.startswith('%'):
            return pane_id
    return mux_pane_id_from_runtime_ref(getattr(binding, 'runtime_ref', None))


def tmux_backend_for_factory(tmux_backend_factory, *, socket_path: str):
    try:
        return tmux_backend_factory(socket_path=socket_path)
    except TypeError:
        return tmux_backend_factory()


def matching_project_namespace_record(
    *,
    binding,
    tmux_socket_path: str,
    tmux_session_name: str | None,
    workspace_window_id: str | None,
    agent_name: str,
    project_id: str,
    window_name: str | None,
    namespace_epoch: int | None,
    tmux_backend_factory,
    inspect_project_namespace_pane_fn,
    namespace_pane_records: dict[str, object] | None = None,
):
    pane_id = binding_pane_id(binding)
    if pane_id is None:
        return None
    session_name = str(tmux_session_name or '').strip()
    if not session_name:
        return None
    if window_name is not None and namespace_epoch is None:
        return None
    if namespace_pane_records is not None:
        record = namespace_pane_records.get(pane_id)
    else:
        backend = tmux_backend_for_factory(tmux_backend_factory, socket_path=tmux_socket_path)
        record = inspect_project_namespace_pane_fn(backend, pane_id)
    if record is None:
        return None
    if not record.matches(
        tmux_session_name=session_name,
        project_id=project_id,
        role='agent',
        slot_key=agent_name,
        window_name=window_name,
        managed_by='ccbd',
        window_id=None if window_name is not None else workspace_window_id,
        namespace_epoch=namespace_epoch if window_name is not None else None,
    ):
        return None
    return record


__all__ = [
    'binding_pane_id',
    'matching_project_namespace_record',
    'mux_backend_from_runtime_ref',
    'mux_pane_id_from_runtime_ref',
    'tmux_backend_for_factory',
]
