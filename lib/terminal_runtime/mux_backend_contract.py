from __future__ import annotations

from typing import Any, Literal, Protocol, TypedDict, runtime_checkable

BackendFamily = Literal["tmux-family"]
BackendImpl = Literal["tmux", "psmux", "rmux"]
IpcKind = Literal["unix_socket", "named_pipe", "socket_name", "socket_path", "none"]
CapabilityStatus = Literal["supported", "partial", "unsupported", "workaround"]
MuxErrorCategory = Literal[
    "transient-unavailable",
    "unsupported",
    "not-found",
    "permission",
    "command-failed",
]
SplitDirection = Literal["right", "bottom"]


class MuxNamespaceRef(TypedDict):
    backend_family: BackendFamily
    backend_impl: BackendImpl
    namespace_id: str
    session_name: str
    ipc_kind: IpcKind
    ipc_ref: str


class MuxPaneRef(TypedDict):
    backend_impl: BackendImpl
    pane_id: str
    session_name: str
    window_name: str | None


class MuxCapabilities(TypedDict):
    backend_impl: BackendImpl
    command_status: dict[str, CapabilityStatus]
    semantic_status: dict[str, CapabilityStatus]
    blocking_gaps: list[str]


class MuxWindowInfo(TypedDict):
    session_name: str
    window_name: str
    active: bool
    pane_count: int
    project_root: str
    layout: str | None


class MuxCommandError(Exception):
    def __init__(
        self,
        *,
        category: MuxErrorCategory,
        backend_impl: BackendImpl,
        operation: str,
        detail: str,
        ipc_ref: str | None = None,
        command: list[str] | tuple[str, ...] | None = None,
        evidence: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(f"{backend_impl} {operation} failed: {detail}")
        self.category = category
        self.backend_impl = backend_impl
        self.operation = operation
        self.detail = detail
        self.ipc_ref = ipc_ref
        self.command = tuple(command) if command is not None else None
        self.evidence = dict(evidence or {})


@runtime_checkable
class NamespaceLifecycle(Protocol):
    def prepare_server(self, *, timeout_s: float | None = None) -> None: ...

    def ensure_server_policy(
        self,
        namespace: MuxNamespaceRef | None = None,
        *,
        timeout_s: float | None = None,
    ) -> None: ...

    def create_session(
        self,
        *,
        session_name: str,
        project_root: str,
        window_name: str | None = None,
        terminal_size: tuple[int, int] | None = None,
    ) -> MuxNamespaceRef: ...

    def attach_namespace(
        self,
        namespace: MuxNamespaceRef,
        *,
        window_name: str | None = None,
    ) -> int: ...

    def destroy_namespace(self, namespace: MuxNamespaceRef) -> None: ...

    def namespace_exists(
        self,
        namespace: MuxNamespaceRef,
        *,
        timeout_s: float | None = None,
    ) -> bool: ...

    def session_alive(
        self,
        namespace: MuxNamespaceRef,
        *,
        timeout_s: float | None = None,
    ) -> bool: ...

    def session_root_pane(
        self,
        namespace: MuxNamespaceRef,
        *,
        timeout_s: float | None = None,
    ) -> MuxPaneRef: ...

    def kill_server(self, namespace: MuxNamespaceRef | None = None) -> bool: ...


@runtime_checkable
class WindowLayout(Protocol):
    def list_windows(self, namespace: MuxNamespaceRef) -> tuple[MuxWindowInfo, ...]: ...

    def ensure_window(
        self,
        namespace: MuxNamespaceRef,
        *,
        window_name: str,
        project_root: str,
        select: bool = False,
    ) -> MuxWindowInfo: ...

    def kill_window(self, namespace: MuxNamespaceRef, *, target: str) -> None: ...

    def list_panes(
        self,
        namespace: MuxNamespaceRef,
        *,
        window_name: str | None = None,
    ) -> tuple[MuxPaneRef, ...]: ...

    def window_root_pane(
        self,
        namespace: MuxNamespaceRef,
        *,
        window_name: str,
        timeout_s: float | None = None,
    ) -> MuxPaneRef: ...

    def select_window(self, namespace: MuxNamespaceRef, *, target: str) -> None: ...

    def split_pane(
        self,
        parent: MuxPaneRef,
        *,
        direction: SplitDirection,
        percent: int,
        cmd: str | None = None,
        cwd: str | None = None,
    ) -> MuxPaneRef: ...

    def reflow_window(
        self,
        namespace: MuxNamespaceRef,
        *,
        window_name: str,
        layout: str,
        expected_panes: tuple[MuxPaneRef, ...] = (),
    ) -> None: ...

    def select_layout(
        self,
        namespace: MuxNamespaceRef,
        *,
        window_name: str,
        layout: str,
    ) -> None: ...

    def move_pane(self, pane: MuxPaneRef, *, target: str) -> None: ...

    def swap_pane(self, source: MuxPaneRef, *, target: MuxPaneRef) -> None: ...


@runtime_checkable
class PaneIO(Protocol):
    def send_text(self, pane: MuxPaneRef, text: str) -> None: ...

    def send_key(self, pane: MuxPaneRef, key: str) -> bool: ...

    def capture_pane(self, pane: MuxPaneRef, *, lines: int = 20) -> str | None: ...

    def respawn_pane(
        self,
        pane: MuxPaneRef,
        *,
        cmd: str,
        cwd: str | None = None,
        remain_on_exit: bool = True,
    ) -> None: ...

    def kill_pane(self, pane: MuxPaneRef) -> None: ...


@runtime_checkable
class PanePresentation(Protocol):
    def set_pane_identity(
        self,
        pane: MuxPaneRef,
        *,
        title: str,
        user_options: dict[str, str],
        border_style: str | None = None,
        active_border_style: str | None = None,
    ) -> None: ...


@runtime_checkable
class PaneLogging(Protocol):
    def ensure_pane_log(self, pane: MuxPaneRef) -> str | None: ...

    def pane_log_path(self, pane: MuxPaneRef) -> str | None: ...


@runtime_checkable
class DiagnosticsCapability(Protocol):
    def capabilities(self) -> MuxCapabilities: ...

    def describe_pane(
        self,
        pane: MuxPaneRef,
        *,
        user_options: tuple[str, ...] = (),
    ) -> dict[str, str] | None: ...


@runtime_checkable
class MuxBackend(
    NamespaceLifecycle,
    WindowLayout,
    PaneIO,
    PanePresentation,
    PaneLogging,
    DiagnosticsCapability,
    Protocol,
):
    backend_family: BackendFamily
    backend_impl: BackendImpl


__all__ = [
    "BackendFamily",
    "BackendImpl",
    "CapabilityStatus",
    "DiagnosticsCapability",
    "IpcKind",
    "MuxBackend",
    "MuxCapabilities",
    "MuxCommandError",
    "MuxErrorCategory",
    "MuxNamespaceRef",
    "MuxPaneRef",
    "MuxWindowInfo",
    "NamespaceLifecycle",
    "PaneIO",
    "PaneLogging",
    "PanePresentation",
    "SplitDirection",
    "WindowLayout",
]
