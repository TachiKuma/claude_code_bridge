from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from .tmux_panes import launch_pane


def launch_runtime_pane(
    backend,
    *,
    spec_name: str,
    assigned_pane_id: str | None,
    assigned_pane_ref: Mapping[str, object] | None,
    start_cmd: str,
    run_cwd: Path,
    create_detached_tmux_pane_fn,
    pane_meets_minimum_size_fn,
    best_effort_kill_tmux_pane_fn,
    allow_detached_fallback: bool,
):
    if _is_herdr_pane_ref(assigned_pane_ref):
        pane_ref = dict(assigned_pane_ref or {})
        backend.respawn_pane(
            pane_ref,
            command=_command_argv(start_cmd),
            cwd=str(run_cwd),
            env={},
        )
        _best_effort_capture_pane(backend, pane_ref)
        return pane_ref
    return launch_pane(
        backend,
        spec_name=spec_name,
        assigned_pane_id=assigned_pane_id,
        start_cmd=start_cmd,
        run_cwd=run_cwd,
        create_detached_tmux_pane_fn=create_detached_tmux_pane_fn,
        pane_meets_minimum_size_fn=pane_meets_minimum_size_fn,
        best_effort_kill_tmux_pane_fn=best_effort_kill_tmux_pane_fn,
        allow_detached_fallback=allow_detached_fallback,
    )


def pane_runtime_id(pane) -> str:
    if isinstance(pane, Mapping):
        return str(pane.get('pane_id') or '').strip()
    return str(pane or '').strip()


def _is_herdr_pane_ref(value) -> bool:
    return isinstance(value, Mapping) and str(value.get('backend_impl') or '').strip() == 'herdr'


def _command_argv(start_cmd: str) -> list[str]:
    command = str(start_cmd or '').strip()
    return [command] if command else []


def _best_effort_capture_pane(backend, pane_ref: Mapping[str, object]) -> None:
    capture = getattr(backend, 'capture_pane', None)
    if not callable(capture):
        return
    try:
        capture(dict(pane_ref), lines=1)
    except Exception:
        return


__all__ = [
    'launch_runtime_pane',
    'pane_runtime_id',
]
