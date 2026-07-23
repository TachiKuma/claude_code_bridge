from __future__ import annotations


def build_tmux_backend(binding, *, tmux_backend_cls):
    try:
        return tmux_backend_cls(socket_name=binding.tmux_socket_name, socket_path=binding.tmux_socket_path)
    except TypeError:
        return tmux_backend_cls()


def build_rmux_backend(binding, *, rmux_backend_cls):
    try:
        return rmux_backend_cls(namespace=binding.tmux_socket_name, socket_path=binding.tmux_socket_path)
    except TypeError:
        return rmux_backend_cls()


def mux_backend_from_runtime_ref(runtime_ref: str | None) -> str | None:
    value = str(runtime_ref or '').strip()
    if ':' not in value:
        return None
    backend = value.split(':', 1)[0].strip().lower()
    return backend if backend in {'tmux', 'rmux', 'psmux'} else None


def mux_target_pane_id(binding, *, runtime_ref: str) -> str:
    pane = runtime_ref.split(':', 1)[1] if ':' in runtime_ref else ''
    return str(binding.active_pane_id or binding.pane_id or pane).strip()


def tmux_target_pane_id(binding, *, runtime_ref: str) -> str:
    return mux_target_pane_id(binding, runtime_ref=runtime_ref)


__all__ = [
    'build_rmux_backend',
    'build_tmux_backend',
    'mux_backend_from_runtime_ref',
    'mux_target_pane_id',
    'tmux_target_pane_id',
]
