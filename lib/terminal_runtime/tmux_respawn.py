from __future__ import annotations

from terminal_runtime.windows_shell_log_builder import (
    append_stderr_redirection as _append_stderr_redirection,
    build_respawn_tmux_args as _build_respawn_tmux_args,
    build_shell_command as _build_shell_command,
    resolve_shell as _resolve_shell,
    resolve_shell_flags as _resolve_shell_flags,
)


def normalize_start_dir(cwd: str | None) -> str:
    start_dir = (cwd or "").strip()
    if start_dir in ("", "."):
        return ""
    return start_dir


def append_stderr_redirection(cmd_body: str, stderr_log_path: str | None) -> tuple[str, str | None]:
    return _append_stderr_redirection(cmd_body, stderr_log_path)


def resolve_shell(*, env_shell: str, tmux_default_shell: str, process_shell: str, fallback_shell: str) -> str:
    return _resolve_shell(
        env_shell=env_shell,
        tmux_default_shell=tmux_default_shell,
        process_shell=process_shell,
        fallback_shell=fallback_shell,
    ).shell


def resolve_shell_flags(*, shell: str, flags_raw: str) -> list[str]:
    return _resolve_shell_flags(shell=shell, flags_raw=flags_raw)


def build_shell_command(*, shell: str, flags: list[str], cmd_body: str) -> str:
    return _build_shell_command(shell=shell, flags=flags, cmd_body=cmd_body)


def build_respawn_tmux_args(*, pane_id: str, start_dir: str, full_command: str) -> list[str]:
    return _build_respawn_tmux_args(pane_id=pane_id, start_dir=start_dir, full_command=full_command)
