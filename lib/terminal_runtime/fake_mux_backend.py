from __future__ import annotations

from dataclasses import dataclass, field

from terminal_runtime.mux_backend_contract import (
    BackendImpl,
    CapabilityStatus,
    MuxCapabilities,
    MuxCommandError,
    MuxErrorCategory,
    MuxNamespaceRef,
    MuxPaneRef,
    MuxWindowInfo,
    SplitDirection,
)


@dataclass
class FakeMuxPane:
    pane_id: str
    session_name: str
    window_name: str
    cmd: str | None = None
    cwd: str | None = None
    alive: bool = True
    buffer: str = ""
    title: str = ""
    user_options: dict[str, str] = field(default_factory=dict)
    border_style: str | None = None
    active_border_style: str | None = None
    log_path: str | None = None

    def ref(self, backend_impl: BackendImpl) -> MuxPaneRef:
        return {
            "backend_impl": backend_impl,
            "pane_id": self.pane_id,
            "session_name": self.session_name,
            "window_name": self.window_name,
        }


@dataclass
class FakeMuxWindow:
    name: str
    project_root: str
    panes: list[str] = field(default_factory=list)
    active: bool = False
    layout: str | None = None


@dataclass
class FakeMuxNamespace:
    ref: MuxNamespaceRef
    project_root: str
    windows: dict[str, FakeMuxWindow] = field(default_factory=dict)


class FakeMuxBackend:
    backend_family = "tmux-family"

    def __init__(
        self,
        *,
        backend_impl: BackendImpl = "rmux",
        ipc_kind: str = "none",
        ipc_ref: str = "",
        command_status: dict[str, CapabilityStatus] | None = None,
        semantic_status: dict[str, CapabilityStatus] | None = None,
        blocking_gaps: list[str] | None = None,
    ) -> None:
        self.backend_impl = backend_impl
        self.ipc_kind = ipc_kind
        self.ipc_ref = ipc_ref
        self.namespaces: dict[str, FakeMuxNamespace] = {}
        self.panes: dict[str, FakeMuxPane] = {}
        self.event_log: list[dict[str, object]] = []
        self._next_pane_id = 1
        self._failures: dict[str, MuxCommandError] = {}
        self._capabilities: MuxCapabilities = {
            "backend_impl": backend_impl,
            "command_status": dict(command_status or {}),
            "semantic_status": dict(semantic_status or {}),
            "blocking_gaps": list(blocking_gaps or []),
        }

    def fail_next(
        self,
        operation: str,
        *,
        category: MuxErrorCategory = "command-failed",
        detail: str = "injected fake mux failure",
        command: list[str] | tuple[str, ...] | None = None,
        evidence: dict[str, object] | None = None,
    ) -> None:
        self._failures[operation] = MuxCommandError(
            category=category,
            backend_impl=self.backend_impl,
            operation=operation,
            detail=detail,
            ipc_ref=self.ipc_ref or None,
            command=command,
            evidence=evidence,
        )

    def prepare_server(self, *, timeout_s: float | None = None) -> None:
        self._maybe_fail("prepare_server")
        self._record("prepare_server", timeout_s=timeout_s)

    def ensure_server_policy(
        self,
        namespace: MuxNamespaceRef | None = None,
        *,
        timeout_s: float | None = None,
    ) -> None:
        self._maybe_fail("ensure_server_policy", namespace=namespace)
        self._record(
            "ensure_server_policy",
            session_name=(namespace or {}).get("session_name"),
            timeout_s=timeout_s,
        )

    def create_session(
        self,
        *,
        session_name: str,
        project_root: str,
        window_name: str | None = None,
        terminal_size: tuple[int, int] | None = None,
    ) -> MuxNamespaceRef:
        self._maybe_fail("create_session")
        session = self._require_name(session_name, "session_name")
        window = self._require_name(window_name or "main", "window_name")
        ref = self._namespace_ref(session)
        namespace = FakeMuxNamespace(ref=ref, project_root=project_root)
        namespace.windows[window] = FakeMuxWindow(
            name=window,
            project_root=project_root,
            active=True,
        )
        self.namespaces[session] = namespace
        root = self._new_pane(session_name=session, window_name=window, cwd=project_root)
        namespace.windows[window].panes.append(root.pane_id)
        self._record(
            "create_session",
            session_name=session,
            window_name=window,
            project_root=project_root,
            terminal_size=terminal_size,
            root_pane_id=root.pane_id,
        )
        return dict(ref)

    def attach_namespace(
        self,
        namespace: MuxNamespaceRef,
        *,
        window_name: str | None = None,
    ) -> int:
        self._maybe_fail("attach_namespace", namespace=namespace)
        self._namespace(namespace)
        if window_name:
            self.select_window(namespace, target=window_name)
        self._record(
            "attach_namespace",
            session_name=namespace["session_name"],
            window_name=window_name,
        )
        return 0

    def destroy_namespace(self, namespace: MuxNamespaceRef) -> None:
        self._maybe_fail("destroy_namespace", namespace=namespace)
        session = namespace["session_name"]
        existing = self.namespaces.pop(session, None)
        if existing is None:
            return
        for window in existing.windows.values():
            for pane_id in window.panes:
                self.panes.pop(pane_id, None)
        self._record("destroy_namespace", session_name=session)

    def namespace_exists(
        self,
        namespace: MuxNamespaceRef,
        *,
        timeout_s: float | None = None,
    ) -> bool:
        self._maybe_fail("namespace_exists", namespace=namespace)
        exists = namespace["session_name"] in self.namespaces
        self._record(
            "namespace_exists",
            session_name=namespace["session_name"],
            timeout_s=timeout_s,
            exists=exists,
        )
        return exists

    def session_alive(
        self,
        namespace: MuxNamespaceRef,
        *,
        timeout_s: float | None = None,
    ) -> bool:
        self._maybe_fail("session_alive", namespace=namespace)
        alive = namespace["session_name"] in self.namespaces
        self._record(
            "session_alive",
            session_name=namespace["session_name"],
            timeout_s=timeout_s,
            alive=alive,
        )
        return alive

    def session_root_pane(
        self,
        namespace: MuxNamespaceRef,
        *,
        timeout_s: float | None = None,
    ) -> MuxPaneRef:
        self._maybe_fail("session_root_pane", namespace=namespace)
        del timeout_s
        ns = self._namespace(namespace)
        active = self._active_window(ns)
        if not active.panes:
            self._raise_not_found("session_root_pane", "active window has no panes")
        return self.panes[active.panes[0]].ref(self.backend_impl)

    def kill_server(self, namespace: MuxNamespaceRef | None = None) -> bool:
        self._maybe_fail("kill_server", namespace=namespace)
        if namespace is None:
            had_namespaces = bool(self.namespaces)
            self.namespaces.clear()
            self.panes.clear()
            self._record("kill_server", session_name=None, killed=had_namespaces)
            return had_namespaces
        existed = namespace["session_name"] in self.namespaces
        self.destroy_namespace(namespace)
        self._record("kill_server", session_name=namespace["session_name"], killed=existed)
        return existed

    def list_windows(self, namespace: MuxNamespaceRef) -> tuple[MuxWindowInfo, ...]:
        self._maybe_fail("list_windows", namespace=namespace)
        ns = self._namespace(namespace)
        self._record("list_windows", session_name=namespace["session_name"])
        return tuple(self._window_info(namespace["session_name"], window) for window in ns.windows.values())

    def ensure_window(
        self,
        namespace: MuxNamespaceRef,
        *,
        window_name: str,
        project_root: str,
        select: bool = False,
    ) -> MuxWindowInfo:
        self._maybe_fail("ensure_window", namespace=namespace)
        ns = self._namespace(namespace)
        name = self._require_name(window_name, "window_name")
        window = ns.windows.get(name)
        if window is None:
            window = FakeMuxWindow(name=name, project_root=project_root)
            ns.windows[name] = window
            pane = self._new_pane(session_name=namespace["session_name"], window_name=name, cwd=project_root)
            window.panes.append(pane.pane_id)
        if select:
            self._set_active_window(ns, name)
        self._record(
            "ensure_window",
            session_name=namespace["session_name"],
            window_name=name,
            project_root=project_root,
            select=select,
        )
        return self._window_info(namespace["session_name"], window)

    def kill_window(self, namespace: MuxNamespaceRef, *, target: str) -> None:
        self._maybe_fail("kill_window", namespace=namespace)
        ns = self._namespace(namespace)
        window_name = self._target_window_name(target)
        window = ns.windows.pop(window_name, None)
        if window is None:
            return
        for pane_id in window.panes:
            self.panes.pop(pane_id, None)
        if not any(item.active for item in ns.windows.values()) and ns.windows:
            next(iter(ns.windows.values())).active = True
        self._record("kill_window", session_name=namespace["session_name"], window_name=window_name)

    def list_panes(
        self,
        namespace: MuxNamespaceRef,
        *,
        window_name: str | None = None,
    ) -> tuple[MuxPaneRef, ...]:
        self._maybe_fail("list_panes", namespace=namespace)
        ns = self._namespace(namespace)
        windows = [ns.windows[self._target_window_name(window_name)]] if window_name else ns.windows.values()
        refs: list[MuxPaneRef] = []
        for window in windows:
            refs.extend(self.panes[pane_id].ref(self.backend_impl) for pane_id in window.panes)
        self._record(
            "list_panes",
            session_name=namespace["session_name"],
            window_name=window_name,
            count=len(refs),
        )
        return tuple(refs)

    def window_root_pane(
        self,
        namespace: MuxNamespaceRef,
        *,
        window_name: str,
        timeout_s: float | None = None,
    ) -> MuxPaneRef:
        self._maybe_fail("window_root_pane", namespace=namespace)
        del timeout_s
        window = self._window(namespace, window_name)
        if not window.panes:
            self._raise_not_found("window_root_pane", f"window {window_name!r} has no panes")
        return self.panes[window.panes[0]].ref(self.backend_impl)

    def select_window(self, namespace: MuxNamespaceRef, *, target: str) -> None:
        self._maybe_fail("select_window", namespace=namespace)
        ns = self._namespace(namespace)
        window_name = self._target_window_name(target)
        self._set_active_window(ns, window_name)
        self._record("select_window", session_name=namespace["session_name"], window_name=window_name)

    def split_pane(
        self,
        parent: MuxPaneRef,
        *,
        direction: SplitDirection,
        percent: int,
        cmd: str | None = None,
        cwd: str | None = None,
    ) -> MuxPaneRef:
        self._maybe_fail("split_pane", pane=parent)
        if direction not in {"right", "bottom"}:
            raise ValueError(f"split_pane direction must be right or bottom, got {direction!r}")
        if percent <= 0 or percent >= 100:
            raise ValueError(f"split_pane percent must be between 1 and 99, got {percent!r}")
        parent_pane = self._pane(parent)
        pane = self._new_pane(
            session_name=parent_pane.session_name,
            window_name=parent_pane.window_name,
            cmd=cmd,
            cwd=cwd or parent_pane.cwd,
        )
        self._window(self._namespace_ref(parent_pane.session_name), parent_pane.window_name).panes.append(pane.pane_id)
        self._record(
            "split_pane",
            parent_pane_id=parent_pane.pane_id,
            pane_id=pane.pane_id,
            direction=direction,
            percent=percent,
            cmd=cmd,
            cwd=cwd,
        )
        return pane.ref(self.backend_impl)

    def reflow_window(
        self,
        namespace: MuxNamespaceRef,
        *,
        window_name: str,
        layout: str,
        expected_panes: tuple[MuxPaneRef, ...] = (),
    ) -> None:
        self._maybe_fail("reflow_window", namespace=namespace)
        window = self._window(namespace, window_name)
        expected = {pane["pane_id"] for pane in expected_panes}
        if expected and not expected.issubset(set(window.panes)):
            self._raise_not_found("reflow_window", "expected pane is not in target window")
        window.layout = layout
        self._record(
            "reflow_window",
            session_name=namespace["session_name"],
            window_name=window_name,
            layout=layout,
            expected_panes=tuple(sorted(expected)),
        )

    def select_layout(
        self,
        namespace: MuxNamespaceRef,
        *,
        window_name: str,
        layout: str,
    ) -> None:
        self._maybe_fail("select_layout", namespace=namespace)
        window = self._window(namespace, window_name)
        window.layout = layout
        self._record(
            "select_layout",
            session_name=namespace["session_name"],
            window_name=window_name,
            layout=layout,
        )

    def move_pane(self, pane: MuxPaneRef, *, target: str) -> None:
        self._maybe_fail("move_pane", pane=pane)
        item = self._pane(pane)
        target_window_name = self._target_window_name(target)
        namespace = self._namespace(self._namespace_ref(item.session_name))
        target_window = namespace.windows.get(target_window_name)
        if target_window is None:
            self._raise_not_found("move_pane", f"window {target_window_name!r} not found")
        source_window = self._window(self._namespace_ref(item.session_name), item.window_name)
        source_window.panes.remove(item.pane_id)
        target_window.panes.append(item.pane_id)
        item.window_name = target_window_name
        self._record(
            "move_pane",
            pane_id=item.pane_id,
            session_name=item.session_name,
            target_window=target_window_name,
        )

    def swap_pane(self, source: MuxPaneRef, *, target: MuxPaneRef) -> None:
        self._maybe_fail("swap_pane", pane=source)
        source_pane = self._pane(source)
        target_pane = self._pane(target)
        if source_pane.session_name != target_pane.session_name:
            self._raise_not_found("swap_pane", "cannot swap panes across namespaces")
        source_window = self._window(self._namespace_ref(source_pane.session_name), source_pane.window_name)
        target_window = self._window(self._namespace_ref(target_pane.session_name), target_pane.window_name)
        source_index = source_window.panes.index(source_pane.pane_id)
        target_index = target_window.panes.index(target_pane.pane_id)
        source_window.panes[source_index] = target_pane.pane_id
        target_window.panes[target_index] = source_pane.pane_id
        source_pane.window_name, target_pane.window_name = target_pane.window_name, source_pane.window_name
        self._record("swap_pane", source=source_pane.pane_id, target=target_pane.pane_id)

    def send_text(self, pane: MuxPaneRef, text: str) -> None:
        self._maybe_fail("send_text", pane=pane)
        item = self._pane(pane)
        item.buffer += text
        self._record("send_text", pane_id=item.pane_id, bytes=len(text.encode("utf-8")))

    def send_key(self, pane: MuxPaneRef, key: str) -> bool:
        self._maybe_fail("send_key", pane=pane)
        item = self._pane(pane)
        if not item.alive:
            return False
        item.buffer += f"<{key}>"
        self._record("send_key", pane_id=item.pane_id, key=key)
        return True

    def capture_pane(self, pane: MuxPaneRef, *, lines: int = 20) -> str | None:
        self._maybe_fail("capture_pane", pane=pane)
        item = self._pane(pane)
        if not item.alive:
            return None
        content_lines = item.buffer.splitlines()
        captured = "\n".join(content_lines[-lines:]) if lines > 0 else item.buffer
        self._record("capture_pane", pane_id=item.pane_id, lines=lines)
        return captured

    def respawn_pane(
        self,
        pane: MuxPaneRef,
        *,
        cmd: str,
        cwd: str | None = None,
        remain_on_exit: bool = True,
    ) -> None:
        self._maybe_fail("respawn_pane", pane=pane)
        item = self._pane(pane)
        item.cmd = cmd
        item.cwd = cwd or item.cwd
        item.alive = True
        item.buffer = ""
        self._record(
            "respawn_pane",
            pane_id=item.pane_id,
            cmd=cmd,
            cwd=cwd,
            remain_on_exit=remain_on_exit,
        )

    def kill_pane(self, pane: MuxPaneRef) -> None:
        self._maybe_fail("kill_pane", pane=pane)
        item = self._pane(pane)
        item.alive = False
        self._record("kill_pane", pane_id=item.pane_id)

    def set_pane_identity(
        self,
        pane: MuxPaneRef,
        *,
        title: str,
        user_options: dict[str, str],
        border_style: str | None = None,
        active_border_style: str | None = None,
    ) -> None:
        self._maybe_fail("set_pane_identity", pane=pane)
        item = self._pane(pane)
        item.title = title
        item.user_options.update(user_options)
        item.border_style = border_style
        item.active_border_style = active_border_style
        self._record(
            "set_pane_identity",
            pane_id=item.pane_id,
            title=title,
            user_options=dict(user_options),
            border_style=border_style,
            active_border_style=active_border_style,
        )

    def ensure_pane_log(self, pane: MuxPaneRef) -> str | None:
        self._maybe_fail("ensure_pane_log", pane=pane)
        item = self._pane(pane)
        if item.log_path is None:
            item.log_path = f"fake-mux://{item.session_name}/{item.pane_id}.log"
        self._record("ensure_pane_log", pane_id=item.pane_id, log_path=item.log_path)
        return item.log_path

    def pane_log_path(self, pane: MuxPaneRef) -> str | None:
        self._maybe_fail("pane_log_path", pane=pane)
        item = self._pane(pane)
        self._record("pane_log_path", pane_id=item.pane_id, log_path=item.log_path)
        return item.log_path

    def capabilities(self) -> MuxCapabilities:
        self._maybe_fail("capabilities")
        self._record("capabilities", backend_impl=self.backend_impl)
        return {
            "backend_impl": self._capabilities["backend_impl"],
            "command_status": dict(self._capabilities["command_status"]),
            "semantic_status": dict(self._capabilities["semantic_status"]),
            "blocking_gaps": list(self._capabilities["blocking_gaps"]),
        }

    def namespace_ref(
        self,
        *,
        session_name: str,
        namespace_id: str | None = None,
    ) -> MuxNamespaceRef:
        ref = self._namespace_ref(session_name)
        if namespace_id is not None:
            ref["namespace_id"] = self._require_name(namespace_id, "namespace_id")
        return ref

    def describe_pane(
        self,
        pane: MuxPaneRef,
        *,
        user_options: tuple[str, ...] = (),
    ) -> dict[str, str] | None:
        self._maybe_fail("describe_pane", pane=pane)
        try:
            item = self._pane(pane)
        except MuxCommandError:
            return None
        selected_options = {
            name: item.user_options.get(name, "")
            for name in user_options
        }
        self._record("describe_pane", pane_id=item.pane_id, user_options=user_options)
        return {
            "pane_id": item.pane_id,
            "session_name": item.session_name,
            "window_name": item.window_name,
            "pane_title": item.title,
            "alive": "1" if item.alive else "0",
            **selected_options,
        }

    def _namespace_ref(self, session_name: str) -> MuxNamespaceRef:
        return {
            "backend_family": "tmux-family",
            "backend_impl": self.backend_impl,
            "namespace_id": session_name,
            "session_name": session_name,
            "ipc_kind": self.ipc_kind,  # type: ignore[typeddict-item]
            "ipc_ref": self.ipc_ref,
        }

    def _new_pane(
        self,
        *,
        session_name: str,
        window_name: str,
        cmd: str | None = None,
        cwd: str | None = None,
    ) -> FakeMuxPane:
        pane_id = f"pane-{self._next_pane_id}"
        self._next_pane_id += 1
        pane = FakeMuxPane(
            pane_id=pane_id,
            session_name=session_name,
            window_name=window_name,
            cmd=cmd,
            cwd=cwd,
        )
        self.panes[pane_id] = pane
        return pane

    def _namespace(self, namespace: MuxNamespaceRef) -> FakeMuxNamespace:
        session = namespace["session_name"]
        existing = self.namespaces.get(session)
        if existing is None:
            self._raise_not_found("namespace", f"namespace {session!r} not found")
        return existing

    def _window(self, namespace: MuxNamespaceRef, window_name: str) -> FakeMuxWindow:
        ns = self._namespace(namespace)
        name = self._target_window_name(window_name)
        window = ns.windows.get(name)
        if window is None:
            self._raise_not_found("window", f"window {name!r} not found")
        return window

    def _pane(self, pane: MuxPaneRef) -> FakeMuxPane:
        item = self.panes.get(pane["pane_id"])
        if item is None:
            self._raise_not_found("pane", f"pane {pane['pane_id']!r} not found")
        return item

    def _active_window(self, namespace: FakeMuxNamespace) -> FakeMuxWindow:
        for window in namespace.windows.values():
            if window.active:
                return window
        self._raise_not_found("active_window", "namespace has no active window")

    def _set_active_window(self, namespace: FakeMuxNamespace, window_name: str) -> None:
        if window_name not in namespace.windows:
            self._raise_not_found("select_window", f"window {window_name!r} not found")
        for item in namespace.windows.values():
            item.active = item.name == window_name

    def _window_info(self, session_name: str, window: FakeMuxWindow) -> MuxWindowInfo:
        return {
            "session_name": session_name,
            "window_name": window.name,
            "active": window.active,
            "pane_count": len(window.panes),
            "project_root": window.project_root,
            "layout": window.layout,
        }

    def _maybe_fail(
        self,
        operation: str,
        *,
        namespace: MuxNamespaceRef | None = None,
        pane: MuxPaneRef | None = None,
    ) -> None:
        injected = self._failures.pop(operation, None)
        if injected is None:
            return
        evidence = dict(injected.evidence)
        if namespace is not None:
            evidence.setdefault("session_name", namespace["session_name"])
        if pane is not None:
            evidence.setdefault("pane_id", pane["pane_id"])
        raise MuxCommandError(
            category=injected.category,
            backend_impl=injected.backend_impl,
            operation=injected.operation,
            detail=injected.detail,
            ipc_ref=injected.ipc_ref,
            command=injected.command,
            evidence=evidence,
        )

    def _raise_not_found(self, operation: str, detail: str) -> None:
        raise MuxCommandError(
            category="not-found",
            backend_impl=self.backend_impl,
            operation=operation,
            detail=detail,
            ipc_ref=self.ipc_ref or None,
            evidence={},
        )

    def _record(self, operation: str, **fields: object) -> None:
        self.event_log.append({"operation": operation, **fields})

    @staticmethod
    def _require_name(value: str, field_name: str) -> str:
        text = str(value or "").strip()
        if not text:
            raise ValueError(f"{field_name} is required")
        return text

    @staticmethod
    def _target_window_name(target: str | None) -> str:
        text = str(target or "").strip()
        if ":" in text:
            return text.rsplit(":", 1)[1]
        return text


__all__ = [
    "FakeMuxBackend",
    "FakeMuxNamespace",
    "FakeMuxPane",
    "FakeMuxWindow",
]
