from __future__ import annotations

from .common import build_rmux_backend, build_tmux_backend, mux_backend_from_runtime_ref, mux_target_pane_id


def cleanup_stale_tmux_binding(binding, *, tmux_backend_cls, kill_tmux_pane_fn, rmux_backend_cls=None) -> None:
    if binding is None:
        return
    runtime_ref = str(binding.runtime_ref or '').strip()
    backend_impl = mux_backend_from_runtime_ref(runtime_ref)
    if backend_impl is None:
        return
    pane_state = str(binding.pane_state or '').strip().lower()
    identity_state = str(getattr(binding, 'provider_identity_state', None) or '').strip().lower()
    if pane_state not in {'dead', 'missing'} and identity_state not in {'mismatch', 'unknown'}:
        return
    pane_id = mux_target_pane_id(binding, runtime_ref=runtime_ref)
    if backend_impl == 'tmux' and not pane_id.startswith('%'):
        return
    try:
        if backend_impl == 'tmux':
            backend = build_tmux_backend(binding, tmux_backend_cls=tmux_backend_cls)
            kill_tmux_pane_fn(backend, pane_id)
            return
        if rmux_backend_cls is None:
            return
        backend = build_rmux_backend(binding, rmux_backend_cls=rmux_backend_cls)
        namespace = str(getattr(backend, 'namespace', '') or getattr(binding, 'tmux_socket_name', '') or '').strip()
        if not namespace:
            return
        pane_ref = backend.pane_ref(
            pane_id,
            session_name=namespace,
            window_name=str(getattr(binding, 'tmux_window_name', '') or '').strip() or None,
        )
        backend.kill_pane(pane_ref)
    except Exception:
        return


__all__ = ['cleanup_stale_tmux_binding']
