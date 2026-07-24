from __future__ import annotations

import platform
import subprocess
from dataclasses import dataclass
from typing import Callable, Sequence

from terminal_runtime.env import subprocess_kwargs


_RMUX_STDIO_AWARE_LIFECYCLE_COMMANDS = {"start-server", "new-session"}
_RMUX_FOREGROUND_ATTACH_COMMANDS = {"attach", "attach-session"}


@dataclass(frozen=True)
class RmuxCommandResult:
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str
    stdout_bytes: bytes | None = None
    stderr_bytes: bytes | None = None


class RmuxRunner:
    def __init__(
        self,
        *,
        rmux_bin: str = "rmux",
        run_fn: Callable[..., subprocess.CompletedProcess[str]] | None = None,
    ) -> None:
        self._rmux_bin = str(rmux_bin or "rmux")
        self._run_fn = run_fn if run_fn is not None else subprocess.run

    def run(
        self,
        args: Sequence[str],
        *,
        input_text: str | None = None,
        timeout_s: float | None = None,
        foreground: bool = False,
    ) -> RmuxCommandResult:
        command = (self._rmux_bin, *tuple(str(arg) for arg in args))
        try:
            cp = run_rmux_subprocess(
                list(command),
                run_fn=self._run_fn,
                input=input_text,
                capture=not foreground,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout_s,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            return RmuxCommandResult(
                command=command,
                returncode=124,
                stdout=_timeout_stream(exc.stdout),
                stderr=_timeout_stream(exc.stderr) or f"timeout after {timeout_s}s",
            )
        return RmuxCommandResult(
            command=command,
            returncode=int(getattr(cp, "returncode", 1) or 0),
            stdout=str(getattr(cp, "stdout", "") or ""),
            stderr=str(getattr(cp, "stderr", "") or ""),
        )


def run_rmux_subprocess(
    command: Sequence[str],
    *,
    run_fn: Callable[..., subprocess.CompletedProcess] = subprocess.run,
    capture: bool = False,
    check: bool = False,
    input: str | bytes | None = None,
    timeout: float | None = None,
    env: dict[str, str] | None = None,
    text: bool | None = None,
    encoding: str | None = None,
    errors: str | None = None,
):
    args = [str(item) for item in command]
    kwargs: dict[str, object] = {"check": check}
    if input is not None:
        kwargs["input"] = input
    if timeout is not None:
        kwargs["timeout"] = timeout
    if env is not None:
        kwargs["env"] = env
    if text is not None:
        kwargs["text"] = text
    if encoding is not None:
        kwargs["encoding"] = encoding
    if errors is not None:
        kwargs["errors"] = errors

    if _uses_inherited_stdio(args, capture=capture):
        return run_fn(args, **kwargs)
    kwargs.update(subprocess_kwargs())
    if _uses_devnull_stdio(args, capture=capture):
        return run_fn(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **kwargs)
    if capture:
        return run_fn(args, capture_output=True, **kwargs)
    return run_fn(args, **kwargs)


def rmux_command_name(command: Sequence[str]) -> str:
    for item in command:
        token = str(item or "").strip()
        if token in _RMUX_STDIO_AWARE_LIFECYCLE_COMMANDS or token in _RMUX_FOREGROUND_ATTACH_COMMANDS:
            return token
    return ""


def logical_key_sequence_for_rmux(key: str) -> tuple[str, ...]:
    normalized = str(key or "").strip().lower()
    if normalized in {"c-d", "ctrl-d"}:
        return ("C-z", "Enter")
    if normalized in {"c-c", "ctrl-c"}:
        return ("C-c",)
    return (str(key or "").strip(),)


def client_tail_nonempty_lines(text: str, lines: int) -> str:
    count = max(1, int(lines))
    visible_lines = [line for line in str(text or "").splitlines() if line.strip()]
    return "\n".join(visible_lines[-count:])


def _uses_inherited_stdio(command: Sequence[str], *, capture: bool) -> bool:
    del capture
    return rmux_command_name(command) in _RMUX_FOREGROUND_ATTACH_COMMANDS


def _uses_devnull_stdio(command: Sequence[str], *, capture: bool) -> bool:
    if not capture or platform.system().lower() != "windows":
        return False
    return rmux_command_name(command) in _RMUX_STDIO_AWARE_LIFECYCLE_COMMANDS


def _timeout_stream(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


__all__ = [
    "RmuxCommandResult",
    "RmuxRunner",
    "client_tail_nonempty_lines",
    "logical_key_sequence_for_rmux",
    "rmux_command_name",
    "run_rmux_subprocess",
]
