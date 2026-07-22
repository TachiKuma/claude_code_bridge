from __future__ import annotations

from .layouts_models import TmuxLayoutBackend
from .placeholders import pane_placeholder_argv


def resolve_root_pane(
    backend: TmuxLayoutBackend,
    *,
    cwd: str,
    root_pane_id: str | None,
    tmux_session_name: str | None,
    detached_session_name: str | None,
    inside_tmux: bool,
) -> tuple[str, bool, list[str]]:
    if root_pane_id:
        return root_pane_id, False, []
    try:
        return backend.get_current_pane_id(), False, []
    except Exception:
        root = detached_root_pane(
            backend,
            cwd=cwd,
            session_name=(tmux_session_name or detached_session_name or '').strip(),
        )
        return root, not inside_tmux, [root]


def detached_root_pane(backend: TmuxLayoutBackend, *, cwd: str, session_name: str) -> str:
    if session_name:
        mux_root = _detached_root_pane_via_mux_backend(backend, cwd=cwd, session_name=session_name)
        if mux_root is not None:
            return mux_root
        if not backend.is_alive(session_name):
            runner = getattr(backend, '_tmux_run')
            runner(
                ['new-session', '-d', '-s', session_name, '-c', cwd, *pane_placeholder_argv()],
                check=True,
            )
        runner = getattr(backend, '_tmux_run')
        cp = runner(
            ['list-panes', '-t', session_name, '-F', '#{pane_id}'],
            capture=True,
            check=True,
        )
        root = first_pane_id(cp.stdout or '')
    else:
        root = backend.create_pane('', cwd)
    if not root or not root.startswith('%'):
        raise RuntimeError('failed to allocate tmux root pane')
    return root


def _detached_root_pane_via_mux_backend(backend, *, cwd: str, session_name: str) -> str | None:
    if getattr(backend, 'backend_family', None) != 'tmux-family':
        return None
    namespace_ref = getattr(backend, 'namespace_ref', None)
    create_session = getattr(backend, 'create_session', None)
    session_alive = getattr(backend, 'session_alive', None)
    session_root_pane = getattr(backend, 'session_root_pane', None)
    if not all(callable(fn) for fn in (namespace_ref, create_session, session_alive, session_root_pane)):
        return None
    namespace = namespace_ref(session_name=session_name)
    if not session_alive(namespace):
        namespace = create_session(session_name=session_name, project_root=cwd)
    root = session_root_pane(namespace)
    return str(root.get('pane_id') or '').strip() or None


def first_pane_id(stdout: str) -> str:
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    return lines[0] if lines else ''


__all__ = [
    'resolve_root_pane',
]
