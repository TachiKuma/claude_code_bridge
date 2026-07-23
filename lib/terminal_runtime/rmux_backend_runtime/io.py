from __future__ import annotations

import os
from pathlib import Path
from typing import Literal, Protocol, TypedDict

from terminal_runtime.env import default_shell, is_windows, is_wsl
from terminal_runtime.mux_backend_contract import MuxCommandError, MuxPaneRef
from terminal_runtime.pane_logs import cleanup_pane_logs, maybe_trim_log, pane_log_path_for
from terminal_runtime.rmux_backend_runtime.errors import malformed_output_error
from terminal_runtime.rmux_backend_runtime.targets import canonical_pane_target
from terminal_runtime.rmux_runner import logical_key_sequence_for_rmux
from terminal_runtime.windows_shell_log_builder import (
    WindowsCommandBuilder,
    build_windows_shell_log_builder,
)


RmuxAnsiMode = Literal["plain", "ansi"]
RmuxTrimPolicy = Literal["preserve"]


class RmuxCaptureResult(TypedDict):
    text: str
    raw_bytes: bytes
    start_line: int | None
    end_line: int | None
    ansi_mode: RmuxAnsiMode
    trim_policy: RmuxTrimPolicy
    diagnostics: dict[str, object]


class RmuxLogCommandBuilder(Protocol):
    def build_pipe_log_command(self, log_path: Path) -> str: ...


_TEXT_CHUNK_SIZE = 4096
_KEY_ALIASES: dict[str, tuple[str, ...]] = {
    "enter": ("Enter",),
    "return": ("Enter",),
    "tab": ("Tab",),
    "escape": ("Escape",),
    "esc": ("Escape",),
    "backspace": ("BSpace",),
    "bspace": ("BSpace",),
    "delete": ("Delete",),
    "del": ("Delete",),
    "up": ("Up",),
    "down": ("Down",),
    "left": ("Left",),
    "right": ("Right",),
    "home": ("Home",),
    "end": ("End",),
    "pageup": ("PageUp",),
    "pagedown": ("PageDown",),
    "ctrl-c": ("C-c",),
    "c-c": ("C-c",),
    "ctrl-d": logical_key_sequence_for_rmux("ctrl-d"),
    "c-d": logical_key_sequence_for_rmux("ctrl-d"),
    "ctrl-u": ("C-u",),
    "c-u": ("C-u",),
    "ctrl-l": ("C-l",),
    "c-l": ("C-l",),
}


def send_text(
    backend,
    pane: MuxPaneRef,
    text: str,
    *,
    submit: bool = True,
    timeout_s: float | None = None,
) -> None:
    normalized = str(text or "")
    if not normalized:
        return
    backend._require_capability("send_text", ("send-keys",))
    pane_id = canonical_pane_target(backend, pane)
    for chunk in _chunks(normalized, _TEXT_CHUNK_SIZE):
        backend._run_checked(
            ["send-keys", "-t", pane_id, "-l", chunk],
            operation="send_text",
            timeout_s=timeout_s,
        )
    if submit:
        send_key(backend, pane, "Enter", timeout_s=timeout_s)


def send_key(
    backend,
    pane: MuxPaneRef,
    key: str,
    *,
    timeout_s: float | None = None,
) -> bool:
    sequence = _key_sequence(key)
    if not sequence:
        return False
    backend._require_capability("send_key", ("send-keys",))
    pane_id = canonical_pane_target(backend, pane)
    for item in sequence:
        backend._run_checked(
            ["send-keys", "-t", pane_id, item],
            operation="send_key",
            timeout_s=timeout_s,
        )
    return True


def capture_pane(
    backend,
    pane: MuxPaneRef,
    *,
    lines: int | None = None,
    start: int | None = None,
    end: int | None = None,
    ansi: bool = False,
    timeout_s: float | None = None,
) -> RmuxCaptureResult:
    backend._require_capability("capture_pane", ("capture-pane",))
    pane_id = canonical_pane_target(backend, pane)
    start_line, end_line = _capture_range(lines=lines, start=start, end=end)
    args = ["capture-pane", "-p", "-t", pane_id]
    if ansi:
        args.append("-e")
    if start_line is not None:
        args.extend(["-S", str(start_line)])
    if end_line is not None:
        args.extend(["-E", str(end_line)])
    result = backend._run_checked(args, operation="capture_pane", timeout_s=timeout_s)
    if result.stdout is None:
        raise malformed_output_error(
            operation="capture_pane",
            detail="rmux capture-pane returned no stdout stream",
            result=result,
            ipc_ref=backend._ipc_ref(),
            daemon_evidence=backend.daemon_evidence,
        )
    text = str(result.stdout)
    raw_bytes = result.stdout_bytes if result.stdout_bytes is not None else text.encode("utf-8", errors="replace")
    return {
        "text": text,
        "raw_bytes": raw_bytes,
        "start_line": start_line,
        "end_line": end_line,
        "ansi_mode": "ansi" if ansi else "plain",
        "trim_policy": "preserve",
        "diagnostics": {
            "operation": "capture_pane",
            "pane_id": pane_id,
            "command": tuple(result.command),
            "returncode": result.returncode,
            "stdout_bytes": len(raw_bytes),
            "raw_bytes_source": "stdout_bytes" if result.stdout_bytes is not None else "encoded_stdout",
            "daemon_evidence": dict(getattr(backend, "daemon_evidence", {}) or {}),
        },
    }


def pane_log_path(backend, pane: MuxPaneRef) -> Path | None:
    pane_id = canonical_pane_target(backend, pane)
    if not pane_id:
        return None
    return pane_log_path_for(pane_id, "rmux", getattr(backend, "namespace", None))


def ensure_pane_log(
    backend,
    pane: MuxPaneRef,
    *,
    log_path: Path | str | None = None,
    command_builder: RmuxLogCommandBuilder | None = None,
    timeout_s: float | None = None,
) -> Path | None:
    backend._require_capability("ensure_pane_log", ("pipe-pane",))
    pane_id = canonical_pane_target(backend, pane)
    resolved = Path(log_path).expanduser() if log_path is not None else pane_log_path(backend, pane)
    if resolved is None:
        return None
    try:
        cleanup_pane_logs(resolved.parent)
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.touch(exist_ok=True)
    except OSError as exc:
        raise MuxCommandError(
            category="permission",
            backend_impl="rmux",
            operation="ensure_pane_log",
            detail=str(exc),
            ipc_ref=backend._ipc_ref(),
            evidence={"log_path": str(resolved)},
        ) from exc
    builder = command_builder or build_default_log_command_builder()
    pipe_command = builder.build_pipe_log_command(resolved)
    backend._run_checked(
        ["pipe-pane", "-o", "-t", pane_id, pipe_command],
        operation="ensure_pane_log",
        timeout_s=timeout_s,
    )
    maybe_trim_log(resolved)
    return resolved


def build_default_log_command_builder() -> WindowsCommandBuilder:
    return build_windows_shell_log_builder(
        env=os.environ,
        default_shell_fn=lambda: default_shell(is_wsl_fn=is_wsl, is_windows_fn=is_windows),
    )


def _capture_range(
    *,
    lines: int | None,
    start: int | None,
    end: int | None,
) -> tuple[int | None, int | None]:
    if start is not None or end is not None:
        return start, end
    if lines is None:
        return None, None
    count = max(1, int(lines))
    return -count, None


def _key_sequence(key: str) -> tuple[str, ...]:
    normalized = str(key or "").strip()
    if not normalized:
        return ()
    return _KEY_ALIASES.get(normalized.lower(), ())


def _chunks(text: str, size: int) -> tuple[str, ...]:
    chunk_size = max(1, int(size))
    return tuple(text[index : index + chunk_size] for index in range(0, len(text), chunk_size))


__all__ = [
    "RmuxCaptureResult",
    "build_default_log_command_builder",
    "capture_pane",
    "ensure_pane_log",
    "pane_log_path",
    "send_key",
    "send_text",
]
