from __future__ import annotations

import os

from terminal_runtime.tmux import tmux_family_base
from terminal_runtime.tmux_backend import TmuxBackend


class PsmuxBackend(TmuxBackend):
    backend_family = "tmux"
    backend_impl = "psmux"

    def __init__(
        self,
        *,
        namespace: str | None = None,
        socket_name: str | None = None,
        socket_path: str | None = None,
        executable: str | None = None,
    ):
        resolved_namespace = (
            namespace
            or socket_name
            or os.environ.get("CCB_RMUX_NAMESPACE")
            or os.environ.get("CCB_PSMUX_NAMESPACE")
            or os.environ.get("CCB_TMUX_SOCKET")
            or ""
        ).strip() or None
        super().__init__(socket_name=resolved_namespace, socket_path=None)
        self._declared_socket_path = (socket_path or "").strip() or None
        self._executable = (
            executable
            or os.environ.get("CCB_RMUX_BIN")
            or os.environ.get("CCB_PSMUX_BIN")
            or "rmux"
        )

    def _tmux_base(self) -> list[str]:
        return tmux_family_base(
            self._executable,
            socket_name=self._socket_name,
            socket_path=self._socket_path,
        )

    def _command_env(self) -> dict[str, str]:
        env = super()._command_env()
        env.pop("CCB_TMUX_CONFIG", None)
        return env


__all__ = ["PsmuxBackend"]
