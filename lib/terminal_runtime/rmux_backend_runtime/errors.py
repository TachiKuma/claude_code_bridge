from __future__ import annotations

import subprocess
from typing import Sequence

from terminal_runtime.mux_backend_contract import MuxCommandError, MuxErrorCategory
from terminal_runtime.rmux_runner import RmuxCommandResult


def map_rmux_result_error(
    result: RmuxCommandResult,
    *,
    operation: str,
    ipc_ref: str | None,
    daemon_evidence: dict[str, object] | None = None,
) -> MuxCommandError:
    detail = _result_detail(result)
    evidence: dict[str, object] = {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "command": result.command,
    }
    if daemon_evidence:
        evidence["daemon_evidence"] = dict(daemon_evidence)
    return MuxCommandError(
        category=error_category(detail),
        backend_impl="rmux",
        operation=operation,
        detail=detail,
        ipc_ref=ipc_ref,
        command=result.command,
        evidence=evidence,
    )


def map_rmux_error(
    exc: BaseException,
    *,
    operation: str,
    ipc_ref: str | None,
    daemon_evidence: dict[str, object] | None = None,
) -> MuxCommandError:
    if isinstance(exc, MuxCommandError):
        return exc
    detail = str(exc).strip() or type(exc).__name__
    command = _exception_command(exc)
    evidence: dict[str, object] = {"original_exception_type": type(exc).__name__}
    if command:
        evidence["command"] = command
    if isinstance(exc, subprocess.TimeoutExpired):
        evidence["timeout"] = exc.timeout
        evidence["stdout"] = _stream(exc.stdout)
        evidence["stderr"] = _stream(exc.stderr)
    if isinstance(exc, subprocess.CalledProcessError):
        evidence["returncode"] = int(exc.returncode)
        evidence["stdout"] = _stream(exc.stdout)
        evidence["stderr"] = _stream(exc.stderr)
    if daemon_evidence:
        evidence["daemon_evidence"] = dict(daemon_evidence)
    return MuxCommandError(
        category=error_category(detail, exc=exc),
        backend_impl="rmux",
        operation=operation,
        detail=detail,
        ipc_ref=ipc_ref,
        command=command,
        evidence=evidence,
    )


def malformed_output_error(
    *,
    operation: str,
    detail: str,
    result: RmuxCommandResult,
    ipc_ref: str | None,
    daemon_evidence: dict[str, object] | None = None,
) -> MuxCommandError:
    evidence: dict[str, object] = {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "command": result.command,
    }
    if daemon_evidence:
        evidence["daemon_evidence"] = dict(daemon_evidence)
    return MuxCommandError(
        category="command-failed",
        backend_impl="rmux",
        operation=operation,
        detail=detail,
        ipc_ref=ipc_ref,
        command=result.command,
        evidence=evidence,
    )


def not_found_error(
    *,
    operation: str,
    detail: str,
    ipc_ref: str | None,
    evidence: dict[str, object] | None = None,
) -> MuxCommandError:
    return MuxCommandError(
        category="not-found",
        backend_impl="rmux",
        operation=operation,
        detail=detail,
        ipc_ref=ipc_ref,
        evidence=evidence or {},
    )


def error_category(detail: str, *, exc: BaseException | None = None) -> MuxErrorCategory:
    lowered = str(detail or "").lower()
    if isinstance(exc, subprocess.TimeoutExpired):
        return "transient-unavailable"
    if isinstance(exc, FileNotFoundError):
        return "unsupported"
    if _looks_unreachable(lowered):
        return "transient-unavailable"
    if _looks_missing(lowered):
        return "not-found"
    if "permission denied" in lowered or "access denied" in lowered or "operation not permitted" in lowered:
        return "permission"
    if "unknown command" in lowered or "invalid option" in lowered or "not supported" in lowered or "unsupported" in lowered:
        return "unsupported"
    return "command-failed"


def is_missing_or_absent(detail: str) -> bool:
    lowered = str(detail or "").lower()
    return _looks_missing(lowered) or _looks_unreachable(lowered)


def is_not_found_detail(detail: str) -> bool:
    return _looks_missing(str(detail or "").lower())


def _result_detail(result: RmuxCommandResult) -> str:
    return (result.stderr or result.stdout or f"rmux command exited {result.returncode}").strip()


def _looks_unreachable(lowered: str) -> bool:
    return (
        "no server running" in lowered
        or "error connecting" in lowered
        or "connection refused" in lowered
        or "no such file or directory" in lowered
        or "pipe not found" in lowered
    )


def _looks_missing(lowered: str) -> bool:
    return (
        "can't find session" in lowered
        or "can't find window" in lowered
        or "can't find pane" in lowered
        or "session not found" in lowered
        or "window not found" in lowered
        or "pane not found" in lowered
    )


def _exception_command(exc: BaseException) -> tuple[str, ...] | None:
    value = getattr(exc, "cmd", None) or getattr(exc, "command", None)
    if isinstance(value, (list, tuple)):
        return tuple(str(item) for item in value)
    if value:
        return (str(value),)
    return None


def _stream(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def command_tuple(args: Sequence[str]) -> tuple[str, ...]:
    return tuple(str(arg) for arg in args)


__all__ = [
    "error_category",
    "is_not_found_detail",
    "is_missing_or_absent",
    "malformed_output_error",
    "map_rmux_error",
    "map_rmux_result_error",
    "not_found_error",
]
