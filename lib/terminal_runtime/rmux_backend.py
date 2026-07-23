from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping

from terminal_runtime.mux_backend_contract import (
    MuxCapabilities,
    MuxCommandError,
    MuxNamespaceRef,
    MuxPaneRef,
    MuxWindowInfo,
    SplitDirection,
)
from terminal_runtime.rmux_backend_runtime.capabilities import (
    RmuxCapabilityGate,
    default_rmux_capability_gate,
)
from terminal_runtime.rmux_backend_runtime.client import (
    RmuxCommandClient,
    RmuxSubprocessCommandClient,
)
from terminal_runtime.rmux_backend_runtime.io import (
    RmuxCaptureResult,
    capture_pane,
    ensure_pane_log,
    pane_log_path,
    send_key,
    send_text,
)
from terminal_runtime.rmux_backend_runtime.namespace import (
    attach_namespace,
    create_session,
    destroy_namespace,
    ensure_server_policy,
    ensure_window,
    kill_server,
    kill_window,
    list_windows,
    namespace_exists,
    namespace_ref,
    prepare_server,
    select_window,
    session_alive,
    session_root_pane,
    window_root_pane,
)
from terminal_runtime.rmux_backend_runtime.panes import (
    describe_pane,
    describe_window_panes,
    kill_pane,
    list_panes,
    move_pane,
    reflow_window,
    respawn_pane,
    select_layout,
    split_pane,
    swap_pane,
)
from terminal_runtime.rmux_backend_runtime.presentation import (
    set_pane_identity,
    set_pane_style,
    set_pane_title,
    set_pane_user_option,
)
from terminal_runtime.windows_shell_log_builder import WindowsCommandBuilder


class RmuxBackend:
    backend_family = "tmux-family"
    backend_impl = "rmux"

    def __init__(
        self,
        *,
        namespace: str | None = None,
        socket_name: str | None = None,
        socket_path: str | None = None,
        executable: str | None = None,
        command_client: RmuxCommandClient | None = None,
        command_status: Mapping[str, str] | None = None,
        semantic_status: Mapping[str, str] | None = None,
        blocking_gaps: list[str] | tuple[str, ...] | None = None,
        capability_report_ref: str | None = None,
        daemon_evidence: Mapping[str, object] | None = None,
        project_root: str | Path | None = None,
        log_command_builder: WindowsCommandBuilder | None = None,
    ) -> None:
        resolved_namespace = (
            namespace
            or socket_name
            or os.environ.get("CCB_RMUX_NAMESPACE")
            or os.environ.get("CCB_PSMUX_NAMESPACE")
            or os.environ.get("CCB_TMUX_SOCKET")
            or ""
        ).strip() or None
        resolved_socket_path = _rmux_socket_path(str(socket_path or "").strip() or None)
        resolved_executable = (
            executable
            or os.environ.get("CCB_RMUX_BIN")
            or os.environ.get("CCB_PSMUX_BIN")
            or "rmux"
        )
        self.namespace = resolved_namespace
        self.socket_path = resolved_socket_path
        self.executable = str(resolved_executable or "rmux")
        self.daemon_evidence = dict(daemon_evidence or {})
        self._log_command_builder = log_command_builder
        self._capability_gate = (
            RmuxCapabilityGate(
                command_status=command_status,
                semantic_status=semantic_status,
                blocking_gaps=blocking_gaps,
                source_ref=capability_report_ref,
            )
            if command_status is not None or semantic_status is not None or blocking_gaps is not None
            else default_rmux_capability_gate(project_root)
        )
        self._client = command_client or RmuxSubprocessCommandClient(
            executable=self.executable,
            namespace=self.namespace,
            socket_path=self.socket_path,
        )
        self._capability_gate.require(
            "RmuxBackend.__init__",
            ("start-server", "new-session", "has-session", "list-windows", "list-panes"),
            backend_impl=self.backend_impl,
            ipc_ref=self._ipc_ref(),
            daemon_evidence=self.daemon_evidence,
        )

    def capabilities(self) -> MuxCapabilities:
        return self._capability_gate.capabilities()

    def namespace_ref(
        self,
        *,
        session_name: str,
        namespace_id: str | None = None,
    ) -> MuxNamespaceRef:
        return namespace_ref(
            session_name=session_name,
            namespace_id=namespace_id,
            socket_path=self.socket_path,
            namespace=self.namespace,
        )

    def pane_ref(
        self,
        pane_id: str,
        *,
        session_name: str,
        window_name: str | None = None,
    ) -> MuxPaneRef:
        pane = _require_text(pane_id, "pane_id")
        return {
            "backend_impl": "rmux",
            "pane_id": pane,
            "session_name": _require_text(session_name, "session_name"),
            "window_name": str(window_name).strip() if window_name is not None else None,
        }

    def prepare_server(self, *, timeout_s: float | None = None) -> None:
        prepare_server(self, timeout_s=timeout_s)

    def ensure_server_policy(
        self,
        namespace: MuxNamespaceRef | None = None,
        *,
        timeout_s: float | None = None,
    ) -> None:
        ensure_server_policy(self, namespace=namespace, timeout_s=timeout_s)

    def create_session(
        self,
        *,
        session_name: str,
        project_root: str,
        window_name: str | None = None,
        terminal_size: tuple[int, int] | None = None,
    ) -> MuxNamespaceRef:
        return create_session(
            self,
            session_name=session_name,
            project_root=project_root,
            window_name=window_name,
            terminal_size=terminal_size,
        )

    def attach_namespace(
        self,
        namespace: MuxNamespaceRef,
        *,
        window_name: str | None = None,
    ) -> int:
        return attach_namespace(self, namespace=namespace, window_name=window_name)

    def destroy_namespace(self, namespace: MuxNamespaceRef) -> None:
        destroy_namespace(self, namespace)

    def namespace_exists(
        self,
        namespace: MuxNamespaceRef,
        *,
        timeout_s: float | None = None,
    ) -> bool:
        return namespace_exists(self, namespace, timeout_s=timeout_s)

    def session_alive(
        self,
        namespace: MuxNamespaceRef,
        *,
        timeout_s: float | None = None,
    ) -> bool:
        return session_alive(self, namespace, timeout_s=timeout_s)

    def session_root_pane(
        self,
        namespace: MuxNamespaceRef,
        *,
        timeout_s: float | None = None,
    ) -> MuxPaneRef:
        return session_root_pane(self, namespace, timeout_s=timeout_s)

    def kill_server(self, namespace: MuxNamespaceRef | None = None) -> bool:
        return kill_server(self, namespace)

    def list_windows(self, namespace: MuxNamespaceRef) -> tuple[MuxWindowInfo, ...]:
        return list_windows(self, namespace)

    def ensure_window(
        self,
        namespace: MuxNamespaceRef,
        *,
        window_name: str,
        project_root: str,
        select: bool = False,
    ) -> MuxWindowInfo:
        return ensure_window(
            self,
            namespace,
            window_name=window_name,
            project_root=project_root,
            select=select,
        )

    def kill_window(self, namespace: MuxNamespaceRef, *, target: str) -> None:
        kill_window(self, namespace, target=target)

    def list_panes(
        self,
        namespace: MuxNamespaceRef,
        *,
        window_name: str | None = None,
    ) -> tuple[MuxPaneRef, ...]:
        return list_panes(self, namespace, window_name=window_name)

    def window_root_pane(
        self,
        namespace: MuxNamespaceRef,
        *,
        window_name: str,
        timeout_s: float | None = None,
    ) -> MuxPaneRef:
        return window_root_pane(self, namespace, window_name=window_name, timeout_s=timeout_s)

    def select_window(self, namespace: MuxNamespaceRef, *, target: str) -> None:
        select_window(self, namespace, target=target)

    def split_pane(
        self,
        parent: MuxPaneRef,
        *,
        direction: SplitDirection,
        percent: int,
        cmd: str | None = None,
        cwd: str | None = None,
    ) -> MuxPaneRef:
        return split_pane(self, parent, direction=direction, percent=percent, cmd=cmd, cwd=cwd)

    def reflow_window(
        self,
        namespace: MuxNamespaceRef,
        *,
        window_name: str,
        layout: str,
        expected_panes: tuple[MuxPaneRef, ...] = (),
    ) -> None:
        reflow_window(self, namespace, window_name=window_name, layout=layout, expected_panes=expected_panes)

    def select_layout(
        self,
        namespace: MuxNamespaceRef,
        *,
        window_name: str,
        layout: str,
    ) -> None:
        select_layout(self, namespace, window_name=window_name, layout=layout)

    def move_pane(self, pane: MuxPaneRef, *, target: str) -> None:
        move_pane(self, pane, target=target)

    def swap_pane(self, source: MuxPaneRef, *, target: MuxPaneRef) -> None:
        swap_pane(self, source, target=target)

    def respawn_pane(
        self,
        pane: MuxPaneRef,
        *,
        cmd: str,
        cwd: str | None = None,
        remain_on_exit: bool = True,
    ) -> None:
        respawn_pane(self, pane, cmd=cmd, cwd=cwd, remain_on_exit=remain_on_exit)

    def kill_pane(self, pane: MuxPaneRef) -> None:
        kill_pane(self, pane)

    def send_text(
        self,
        pane: MuxPaneRef,
        text: str,
        *,
        submit: bool = True,
        timeout_s: float | None = None,
    ) -> None:
        send_text(self, pane, text, submit=submit, timeout_s=timeout_s)

    def send_key(
        self,
        pane: MuxPaneRef,
        key: str,
        *,
        timeout_s: float | None = None,
    ) -> bool:
        return send_key(self, pane, key, timeout_s=timeout_s)

    def capture_pane(
        self,
        pane: MuxPaneRef,
        *,
        lines: int | None = None,
        start: int | None = None,
        end: int | None = None,
        ansi: bool = False,
        timeout_s: float | None = None,
    ) -> RmuxCaptureResult:
        return capture_pane(
            self,
            pane,
            lines=lines,
            start=start,
            end=end,
            ansi=ansi,
            timeout_s=timeout_s,
        )

    def get_text(self, pane: MuxPaneRef, *, lines: int = 20) -> str | None:
        return self.capture_pane(pane, lines=lines)["text"]

    def pane_log_path(self, pane: MuxPaneRef) -> str | None:
        path = pane_log_path(self, pane)
        return str(path) if path is not None else None

    def ensure_pane_log(
        self,
        pane: MuxPaneRef,
        *,
        log_path: str | Path | None = None,
        timeout_s: float | None = None,
    ) -> str | None:
        path = ensure_pane_log(
            self,
            pane,
            log_path=log_path,
            command_builder=self._log_command_builder,
            timeout_s=timeout_s,
        )
        return str(path) if path is not None else None

    def set_pane_title(self, pane: MuxPaneRef, title: str) -> None:
        set_pane_title(self, pane, title)

    def set_pane_user_option(self, pane: MuxPaneRef, name: str, value: str) -> None:
        set_pane_user_option(self, pane, name, value)

    def set_pane_style(
        self,
        pane: MuxPaneRef,
        *,
        border_style: str | None = None,
        active_border_style: str | None = None,
    ) -> None:
        set_pane_style(
            self,
            pane,
            border_style=border_style,
            active_border_style=active_border_style,
        )

    def set_pane_identity(
        self,
        pane: MuxPaneRef,
        *,
        title: str,
        user_options: dict[str, str],
        border_style: str | None = None,
        active_border_style: str | None = None,
    ) -> None:
        set_pane_identity(
            self,
            pane,
            title=title,
            user_options=user_options,
            border_style=border_style,
            active_border_style=active_border_style,
        )

    def describe_pane(
        self,
        pane: MuxPaneRef,
        *,
        user_options: tuple[str, ...] = (),
    ) -> dict[str, str] | None:
        return describe_pane(self, pane, user_options=user_options)

    def describe_window_panes(
        self,
        namespace: MuxNamespaceRef,
        *,
        window_name: str,
        user_options: tuple[str, ...] = (),
    ) -> tuple[dict[str, str], ...]:
        return describe_window_panes(self, namespace, window_name=window_name, user_options=user_options)

    def _run_checked(self, args: list[str], *, operation: str, timeout_s: float | None = None):
        return self._client.run_checked(
            args,
            operation=operation,
            timeout_s=timeout_s,
            ipc_ref=self._ipc_ref(),
            daemon_evidence=self.daemon_evidence,
        )

    def _run_unchecked(self, args: list[str], *, timeout_s: float | None = None):
        return self._client.run(args, timeout_s=timeout_s)

    def _require_capability(self, operation: str, commands: tuple[str, ...] | list[str]) -> None:
        self._capability_gate.require(
            operation,
            tuple(commands),
            backend_impl=self.backend_impl,
            ipc_ref=self._ipc_ref(),
            daemon_evidence=self.daemon_evidence,
        )

    def _ipc_ref(self) -> str:
        if self.socket_path:
            return self.socket_path
        return self.namespace or "<default>"


def _require_text(value: str | None, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name} is required")
    return text


def _rmux_socket_path(value: str | None) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    if os.name != "nt":
        return text
    normalized = text.replace("/", "\\")
    return text if normalized.startswith("\\\\.\\pipe\\") else None


__all__ = ["RmuxBackend", "RmuxCaptureResult"]
