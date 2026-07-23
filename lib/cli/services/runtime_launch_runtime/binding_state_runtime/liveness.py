from __future__ import annotations

from .common import (
    build_rmux_backend,
    build_tmux_backend,
    mux_backend_from_runtime_ref,
    mux_target_pane_id,
)


def binding_runtime_alive(binding, *, tmux_backend_cls, rmux_backend_cls=None) -> bool:
    identity_state = str(getattr(binding, 'provider_identity_state', None) or '').strip().lower()
    if identity_state and identity_state not in {'match', 'rotated_in_process'}:
        return False
    runtime_ref = str(binding.runtime_ref or '').strip()
    if not runtime_ref:
        return False
    backend_impl = mux_backend_from_runtime_ref(runtime_ref)
    if backend_impl is None:
        return True
    pane_state = str(binding.pane_state or '').strip().lower()
    if pane_state not in {'', 'alive'}:
        return False
    target = mux_target_pane_id(binding, runtime_ref=runtime_ref)
    if backend_impl == 'tmux' and not target.startswith('%'):
        return False
    try:
        if backend_impl == 'tmux':
            backend = build_tmux_backend(binding, tmux_backend_cls=tmux_backend_cls)
        elif rmux_backend_cls is not None:
            backend = build_rmux_backend(binding, rmux_backend_cls=rmux_backend_cls)
        else:
            return False
        return backend.is_tmux_pane_alive(target)
    except Exception:
        return False


__all__ = ['binding_runtime_alive']
