from __future__ import annotations

import subprocess
from typing import Callable, Protocol, Sequence

from terminal_runtime.mux_backend_contract import MuxCommandError
from terminal_runtime.rmux_backend_runtime.errors import map_rmux_error, map_rmux_result_error
from terminal_runtime.rmux_runner import RmuxCommandResult, run_rmux_subprocess
from terminal_runtime.tmux import tmux_family_base


class RmuxCommandClient(Protocol):
    def run(
        self,
        args: Sequence[str],
        *,
        input_text: str | None = None,
        timeout_s: float | None = None,
        foreground: bool = False,
    ) -> RmuxCommandResult: ...

    def run_checked(
        self,
        args: Sequence[str],
        *,
        operation: str,
        timeout_s: float | None,
        ipc_ref: str | None,
        daemon_evidence: dict[str, object] | None = None,
    ) -> RmuxCommandResult: ...


class RmuxSubprocessCommandClient:
    def __init__(
        self,
        *,
        executable: str = "rmux",
        namespace: str | None = None,
        socket_path: str | None = None,
        run_fn: Callable[..., subprocess.CompletedProcess] = subprocess.run,
    ) -> None:
        self._executable = str(executable or "rmux")
        self._namespace = str(namespace or "").strip() or None
        self._socket_path = str(socket_path or "").strip() or None
        self._run_fn = run_fn

    def run(
        self,
        args: Sequence[str],
        *,
        input_text: str | None = None,
        timeout_s: float | None = None,
        foreground: bool = False,
    ) -> RmuxCommandResult:
        command = tuple(
            tmux_family_base(
                self._executable,
                socket_name=self._namespace,
                socket_path=self._socket_path,
            )
            + [str(arg) for arg in args]
        )
        try:
            cp = run_rmux_subprocess(
                command,
                run_fn=self._run_fn,
                input=input_text,
                timeout=timeout_s,
                capture=not foreground,
                check=False,
                text=True,
                encoding="utf-8",
                errors="replace",
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

    def run_checked(
        self,
        args: Sequence[str],
        *,
        operation: str,
        timeout_s: float | None,
        ipc_ref: str | None,
        daemon_evidence: dict[str, object] | None = None,
    ) -> RmuxCommandResult:
        try:
            result = self.run(args, timeout_s=timeout_s)
        except Exception as exc:
            raise map_rmux_error(
                exc,
                operation=operation,
                ipc_ref=ipc_ref,
                daemon_evidence=daemon_evidence,
            ) from exc
        if result.returncode == 0:
            return result
        raise map_rmux_result_error(
            result,
            operation=operation,
            ipc_ref=ipc_ref,
            daemon_evidence=daemon_evidence,
        )


def _timeout_stream(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


__all__ = ["RmuxCommandClient", "RmuxSubprocessCommandClient"]
