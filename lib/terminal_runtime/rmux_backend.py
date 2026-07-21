from __future__ import annotations

import os
import subprocess

from runtime_observability import record_startup_operations
from terminal_runtime.psmux_backend import PsmuxBackend
from terminal_runtime.rmux_runner import (
    client_tail_nonempty_lines,
    logical_key_sequence_for_rmux,
    run_rmux_subprocess,
)


class RmuxBackend(PsmuxBackend):
    backend_family = "tmux"
    backend_impl = "rmux"

    def __init__(
        self,
        *,
        namespace: str | None = None,
        socket_name: str | None = None,
        socket_path: str | None = None,
        executable: str | None = None,
    ):
        super().__init__(
            namespace=namespace,
            socket_name=socket_name,
            socket_path=socket_path,
            executable=executable or os.environ.get("CCB_RMUX_BIN") or "rmux",
        )

    def _tmux_run(
        self,
        args: list[str],
        *,
        check: bool = False,
        capture: bool = False,
        input_bytes: bytes | None = None,
        timeout: float | None = None,
    ) -> subprocess.CompletedProcess:
        record_startup_operations(
            {
                "tmux_backend_command_attempt_count": 1,
                "tracked_startup_subprocess_spawn_attempt_count": 1,
            }
        )
        try:
            result = run_rmux_subprocess(
                [*self._tmux_base(), *args],
                check=check,
                capture=capture,
                input=input_bytes,
                timeout=timeout,
                env=self._command_env(),
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except subprocess.SubprocessError:
            _record_rmux_subprocess_started()
            raise
        _record_rmux_subprocess_started()
        return result

    def send_key(self, pane_id: str, key: str) -> bool:
        sequence = logical_key_sequence_for_rmux(key)
        if not pane_id or not sequence or not sequence[0]:
            return False
        try:
            cp = self._tmux_run(["send-keys", "-t", pane_id, *sequence], capture=True, timeout=2.0)
            return cp.returncode == 0
        except Exception:
            return False

    def get_pane_content(self, pane_id: str, lines: int = 20) -> str | None:
        if not pane_id:
            return None
        try:
            cp = self._tmux_run(["capture-pane", "-t", pane_id, "-p"], capture=True)
        except Exception:
            return None
        if int(getattr(cp, "returncode", 1) or 0) != 0:
            return None
        text = self._ANSI_RE.sub("", str(getattr(cp, "stdout", "") or ""))
        return client_tail_nonempty_lines(text, lines)

    def attach_session_foreground(self, session_name: str) -> int:
        session = str(session_name or "").strip()
        if not session:
            return 1
        return int(self._tmux_run(["attach-session", "-t", session], check=False, capture=False).returncode or 0)


def _record_rmux_subprocess_started() -> None:
    record_startup_operations(
        {
            "tmux_backend_command_count": 1,
            "tmux_backend_subprocess_spawn_count": 1,
            "tracked_startup_subprocess_spawn_count": 1,
        }
    )


__all__ = ["RmuxBackend"]
