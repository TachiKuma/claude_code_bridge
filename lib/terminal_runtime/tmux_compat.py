from __future__ import annotations

import shutil


def is_tmux_compat_subset(backend) -> bool:
    backend_impl = str(getattr(backend, 'backend_impl', '') or '').strip().lower()
    if backend_impl == 'psmux':
        return True
    tmux_base = getattr(backend, '_tmux_base', None)
    if not callable(tmux_base):
        return False
    try:
        command = tmux_base()
    except Exception:
        return False
    items = [str(item) for item in command]
    executable = items[0] if items else ''
    resolved_executable = shutil.which(executable) if executable else None
    executable_text = ' '.join([executable, str(resolved_executable or '')]).replace('\\', '/').lower()
    return '/psmux/' in executable_text or '/rmux/' in executable_text


__all__ = ['is_tmux_compat_subset']
