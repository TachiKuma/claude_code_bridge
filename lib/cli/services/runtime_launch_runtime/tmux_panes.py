from __future__ import annotations

import os
import time
from pathlib import Path

from terminal_runtime.placeholders import pane_placeholder_argv
from terminal_runtime.tmux_server_policy import CLIPBOARD_PIPE_COMMAND, TMUX_ENVIRONMENT_KEYS

_PREPARED_DETACHED_TMUX_SERVER_KEYS: set[tuple[object, ...]] = set()


def launch_pane(
    backend,
    *,
    spec_name: str,
    assigned_pane_id: str | None,
    start_cmd: str,
    run_cwd: Path,
    create_detached_tmux_pane_fn,
    pane_meets_minimum_size_fn,
    best_effort_kill_tmux_pane_fn,
    allow_detached_fallback: bool,
) -> str:
    if assigned_pane_id:
        pane_id = str(assigned_pane_id)
        replacement = backend.respawn_pane(
            pane_id,
            cmd=start_cmd,
            cwd=str(run_cwd),
            remain_on_exit=True,
        )
        replacement_pane_id = str(replacement or '').strip()
        if replacement_pane_id.startswith('%'):
            return replacement_pane_id
        return pane_id
    if not allow_detached_fallback:
        raise RuntimeError(
            f'project namespace launch requires assigned tmux pane for {spec_name}'
        )
    return allocate_fresh_pane(
        backend,
        spec_name=spec_name,
        start_cmd=start_cmd,
        run_cwd=run_cwd,
        create_detached_tmux_pane_fn=create_detached_tmux_pane_fn,
        pane_meets_minimum_size_fn=pane_meets_minimum_size_fn,
        best_effort_kill_tmux_pane_fn=best_effort_kill_tmux_pane_fn,
        allow_detached_fallback=allow_detached_fallback,
    )


def allocate_fresh_pane(
    backend,
    *,
    spec_name: str,
    start_cmd: str,
    run_cwd: Path,
    create_detached_tmux_pane_fn,
    pane_meets_minimum_size_fn,
    best_effort_kill_tmux_pane_fn,
    allow_detached_fallback: bool,
) -> str:
    try:
        pane_id = backend.create_pane(start_cmd, str(run_cwd))
    except Exception as exc:
        if not should_fallback_to_detached_session(exc):
            raise
        return detached_pane(
            backend,
            spec_name=spec_name,
            start_cmd=start_cmd,
            run_cwd=run_cwd,
            create_detached_tmux_pane_fn=create_detached_tmux_pane_fn,
        )
    if pane_meets_minimum_size_fn(backend, pane_id):
        return pane_id
    best_effort_kill_tmux_pane_fn(backend, pane_id)
    if not allow_detached_fallback:
        raise RuntimeError(
            f'project namespace launch could not allocate stable tmux pane for {spec_name}'
        )
    return detached_pane(
        backend,
        spec_name=spec_name,
        start_cmd=start_cmd,
        run_cwd=run_cwd,
        create_detached_tmux_pane_fn=create_detached_tmux_pane_fn,
    )


def detached_pane(
    backend,
    *,
    spec_name: str,
    start_cmd: str,
    run_cwd: Path,
    create_detached_tmux_pane_fn,
) -> str:
    return create_detached_tmux_pane_fn(
        backend,
        cmd=start_cmd,
        cwd=run_cwd,
        session_name=f'ccb-{spec_name}',
    )


def prepare_detached_tmux_server(backend) -> None:
    if _is_mux_backend(backend):
        try:
            backend.ensure_server_policy()
        except Exception:
            pass
        return
    cache_key = _detached_tmux_server_prepare_key(backend)
    if cache_key in _PREPARED_DETACHED_TMUX_SERVER_KEYS:
        return

    prepared = True
    prepared = best_effort_tmux_run(backend, ['set-option', '-g', 'destroy-unattached', 'off']) and prepared
    prepared = best_effort_tmux_run(backend, ['set-option', '-g', 'mouse', 'on']) and prepared
    prepared = best_effort_tmux_run(backend, ['set-option', '-g', 'history-limit', '50000']) and prepared
    prepared = best_effort_tmux_run(backend, ['set-option', '-g', 'set-clipboard', 'on']) and prepared
    prepared = best_effort_tmux_run(backend, ['set-option', '-g', 'focus-events', 'on']) and prepared
    prepared = best_effort_tmux_run(backend, ['set-option', '-g', 'escape-time', '10']) and prepared
    prepared = best_effort_tmux_run(backend, ['set-option', '-g', 'allow-passthrough', 'on']) and prepared
    prepared = _best_effort_tmux_environment_policy(backend) and prepared
    prepared = best_effort_tmux_run(backend, ['set-window-option', '-g', 'mode-keys', 'vi']) and prepared
    prepared = best_effort_tmux_run(backend, ['bind-key', '-T', 'copy-mode-vi', 'v', 'send-keys', '-X', 'begin-selection']) and prepared
    prepared = best_effort_tmux_run(backend, ['bind-key', '-T', 'copy-mode-vi', 'C-v', 'send-keys', '-X', 'rectangle-toggle']) and prepared
    for key in ('y', 'Enter', 'MouseDragEnd1Pane'):
        prepared = best_effort_tmux_run(
            backend,
            ['bind-key', '-T', 'copy-mode-vi', key, 'send-keys', '-X', 'copy-pipe-and-cancel', CLIPBOARD_PIPE_COMMAND],
        ) and prepared
    for key, direction in (('h', '-L'), ('j', '-D'), ('k', '-U'), ('l', '-R')):
        prepared = best_effort_tmux_run(backend, ['bind-key', key, 'select-pane', direction]) and prepared
    for key, direction in (('H', '-L'), ('J', '-D'), ('K', '-U'), ('L', '-R')):
        prepared = best_effort_tmux_run(backend, ['bind-key', '-r', key, 'resize-pane', direction, '5']) and prepared


    if prepared:
        _PREPARED_DETACHED_TMUX_SERVER_KEYS.add(cache_key)


def _detached_tmux_server_prepare_key(backend) -> tuple[object, ...]:
    socket_path = str(getattr(backend, 'socket_path', '') or '').strip()
    socket_name = str(getattr(backend, 'socket_name', '') or '').strip()
    socket_key = ('path', socket_path) if socket_path else ('name', socket_name or '<default>')
    env_key = tuple((key, os.environ.get(key) or '') for key in TMUX_ENVIRONMENT_KEYS)
    return (*socket_key, env_key)


def best_effort_tmux_run(backend, argv: list[str]) -> bool:
    try:
        result = backend._tmux_run(argv, check=False)  # type: ignore[attr-defined]
    except Exception:
        return False
    return int(getattr(result, 'returncode', 0) or 0) == 0


def _best_effort_tmux_environment_policy(backend) -> bool:
    prepared = best_effort_tmux_run(backend, ['set-option', '-g', 'update-environment', ' '.join(TMUX_ENVIRONMENT_KEYS)])
    for key in TMUX_ENVIRONMENT_KEYS:
        value = os.environ.get(key)
        if value:
            prepared = best_effort_tmux_run(backend, ['set-environment', '-g', key, value]) and prepared
    return prepared


def create_detached_tmux_pane(backend, *, cmd: str, cwd: Path, session_name: str) -> str:
    target_session = f'{session_name}-{int(time.time() * 1000)}-{os.getpid()}'
    if _is_mux_backend(backend):
        namespace = backend.create_session(
            session_name=target_session,
            project_root=str(cwd),
            terminal_size=(160, 48),
        )
        prepare_detached_tmux_server(backend)
        pane = backend.session_root_pane(namespace)
        backend.respawn_pane(pane, cmd=cmd, cwd=str(cwd), remain_on_exit=True)
        return pane['pane_id']
    backend._tmux_run(  # type: ignore[attr-defined]
        ['new-session', '-d', '-x', '160', '-y', '48', '-s', target_session, '-c', str(cwd), *pane_placeholder_argv()],
        check=True,
    )
    prepare_detached_tmux_server(backend)
    result = backend._tmux_run(  # type: ignore[attr-defined]
        ['list-panes', '-t', target_session, '-F', '#{pane_id}'],
        capture=True,
        check=True,
    )
    pane_id = ((result.stdout or '').splitlines() or [''])[0].strip()
    if not pane_id:
        raise RuntimeError(
            f'failed to create detached tmux pane for session {target_session}'
        )
    backend.respawn_pane(pane_id, cmd=cmd, cwd=str(cwd), remain_on_exit=True)
    return pane_id


def pane_meets_minimum_size(
    backend,
    pane_id: str,
    *,
    min_width: int = 20,
    min_height: int = 8,
) -> bool:
    dimensions = pane_dimensions(backend, pane_id)
    if dimensions is None:
        return True
    width, height = dimensions
    return width >= min_width and height >= min_height


def pane_dimensions(backend, pane_id: str) -> tuple[int, int] | None:
    try:
        result = backend._tmux_run(  # type: ignore[attr-defined]
            ['display-message', '-p', '-t', pane_id, '#{pane_width}x#{pane_height}'],
            capture=True,
            check=True,
        )
    except Exception:
        return None
    raw = (result.stdout or '').strip().lower()
    try:
        width_text, height_text = raw.split('x', 1)
        width = int(width_text)
        height = int(height_text)
    except Exception:
        return None
    return width, height


def best_effort_kill_tmux_pane(backend, pane_id: str) -> None:
    try:
        backend.kill_tmux_pane(pane_id)
        return
    except Exception:
        pass
    try:
        backend._tmux_run(['kill-pane', '-t', pane_id], check=False)  # type: ignore[attr-defined]
    except Exception:
        pass


def should_fallback_to_detached_session(exc: Exception) -> bool:
    text = str(exc).strip().lower()
    return 'split-window failed' in text or 'no space for new pane' in text


def _is_mux_backend(backend) -> bool:
    return getattr(backend, 'backend_family', None) == 'tmux-family' and callable(getattr(backend, 'create_session', None))


__all__ = [
    'best_effort_kill_tmux_pane',
    'create_detached_tmux_pane',
    'launch_pane',
    'pane_meets_minimum_size',
    'prepare_detached_tmux_server',
]
