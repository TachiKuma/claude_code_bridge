from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from typing import Any

from terminal_runtime.mux_backend_contract import (
    MuxCapabilities,
    MuxCommandError,
    MuxErrorCategory,
    MuxNamespaceRef,
    MuxPaneRef,
    MuxWindowInfo,
    SplitDirection,
)
from terminal_runtime.placeholders import pane_placeholder_argv
from terminal_runtime.tmux import expand_backend_path, normalize_split_direction
from terminal_runtime.tmux_compat import is_tmux_compat_subset
from terminal_runtime.tmux_readiness import (
    TmuxCommandError,
    TmuxTransientServerUnavailable,
    is_tmux_absent_server_text,
    is_tmux_missing_session_text,
    is_tmux_transient_server_error_text,
    tmux_failure_detail,
    tmux_object_ready_poll_interval_s,
    tmux_object_ready_timeout_s,
)
from terminal_runtime.tmux_server_policy import (
    CLIPBOARD_PIPE_COMMAND,
    TMUX_ENVIRONMENT_KEYS,
)


class TmuxMuxBackendAdapter:
    backend_family = "tmux-family"
    backend_impl = "tmux"

    def __init__(self, tmux_backend) -> None:
        self._backend = tmux_backend

    @property
    def tmux_backend(self):
        return self._backend

    @property
    def socket_path(self) -> str | None:
        path = str(getattr(self._backend, "_socket_path", "") or getattr(self._backend, "socket_path", "") or "").strip()
        return expand_backend_path(path) if path else None

    @property
    def socket_name(self) -> str | None:
        return str(getattr(self._backend, "_socket_name", "") or getattr(self._backend, "socket_name", "") or "").strip() or None

    def namespace_ref(
        self,
        *,
        session_name: str,
        namespace_id: str | None = None,
    ) -> MuxNamespaceRef:
        session = _require_text(session_name, "session_name")
        socket_path = self.socket_path
        socket_name = self.socket_name
        if socket_path:
            ipc_kind = "unix_socket"
            ipc_ref = socket_path
        else:
            ipc_kind = "socket_name"
            ipc_ref = socket_name or "<default>"
        return {
            "backend_family": "tmux-family",
            "backend_impl": "tmux",
            "namespace_id": _require_text(namespace_id or session, "namespace_id"),
            "session_name": session,
            "ipc_kind": ipc_kind,
            "ipc_ref": ipc_ref,
        }

    def pane_ref(
        self,
        pane_id: str,
        *,
        session_name: str,
        window_name: str | None = None,
    ) -> MuxPaneRef:
        pane = _require_text(pane_id, "pane_id")
        return {
            "backend_impl": "tmux",
            "pane_id": pane,
            "session_name": _require_text(session_name, "session_name"),
            "window_name": str(window_name).strip() if window_name is not None else None,
        }

    def capabilities(self) -> MuxCapabilities:
        return {
            "backend_impl": "tmux",
            "command_status": {
                "start-server": "supported",
                "new-session": "supported",
                "has-session": "supported",
                "list-windows": "supported",
                "new-window": "supported",
                "list-panes": "supported",
                "split-window": "supported",
                "select-layout": "supported",
                "swap-pane": "supported",
                "send-keys": "supported",
                "capture-pane": "supported",
                "respawn-pane": "supported",
                "pipe-pane": "supported",
            },
            "semantic_status": {
                "namespace_lifecycle": "supported",
                "window_layout": "supported",
                "pane_io": "supported",
                "presentation": "supported",
                "logging": "supported",
                "diagnostics": "supported",
            },
            "blocking_gaps": [],
        }

    def prepare_server(self, *, timeout_s: float | None = None) -> None:
        self._run_ready(["start-server"], operation="prepare_server", timeout_s=timeout_s)

    def ensure_server_policy(
        self,
        namespace: MuxNamespaceRef | None = None,
        *,
        timeout_s: float | None = None,
    ) -> None:
        del namespace
        self._run_ready(
            ["set-option", "-g", "destroy-unattached", "off"],
            operation="ensure_server_policy",
            timeout_s=timeout_s,
        )
        for option, value in (
            ("mouse", "on"),
            ("history-limit", "50000"),
            ("set-clipboard", "on"),
            ("focus-events", "on"),
            ("escape-time", "10"),
            ("allow-passthrough", "on"),
        ):
            self._run_optional(["set-option", "-g", option, value], operation="ensure_server_policy", timeout_s=timeout_s)
        if is_tmux_compat_subset(self._backend):
            return
        self._apply_environment_policy(timeout_s=timeout_s)
        if not self._run_optional(
            ["set-window-option", "-g", "mode-keys", "vi"],
            operation="ensure_server_policy",
            timeout_s=timeout_s,
        ):
            return
        for args in (
            ["bind-key", "-T", "copy-mode-vi", "v", "send-keys", "-X", "begin-selection"],
            ["bind-key", "-T", "copy-mode-vi", "C-v", "send-keys", "-X", "rectangle-toggle"],
            *(
                ["bind-key", "-T", "copy-mode-vi", key, "send-keys", "-X", "copy-pipe-and-cancel", CLIPBOARD_PIPE_COMMAND]
                for key in ("y", "Enter", "MouseDragEnd1Pane")
            ),
            *(["bind-key", key, "select-pane", direction] for key, direction in (("h", "-L"), ("j", "-D"), ("k", "-U"), ("l", "-R"))),
            *(["bind-key", "-r", key, "resize-pane", direction, "5"] for key, direction in (("H", "-L"), ("J", "-D"), ("K", "-U"), ("L", "-R"))),
        ):
            self._run_optional(args, operation="ensure_server_policy", timeout_s=timeout_s)

    def create_session(
        self,
        *,
        session_name: str,
        project_root: str,
        window_name: str | None = None,
        terminal_size: tuple[int, int] | None = None,
    ) -> MuxNamespaceRef:
        session = _require_text(session_name, "session_name")
        width, height = _resolved_session_size(terminal_size)
        args = ["new-session", "-d", "-x", str(width), "-y", str(height), "-s", session]
        window = str(window_name or "").strip()
        if window:
            args.extend(["-n", window])
        args.extend(["-c", str(project_root), *pane_placeholder_argv()])
        self._run_ready(args, operation="create_session")
        namespace = self.namespace_ref(session_name=session)
        if not self.session_alive(namespace):
            raise MuxCommandError(
                category="not-found",
                backend_impl="tmux",
                operation="create_session",
                detail=f"failed to observe tmux session {session!r} after creation",
                ipc_ref=namespace["ipc_ref"],
                evidence={"session_name": session},
            )
        return namespace

    def attach_namespace(
        self,
        namespace: MuxNamespaceRef,
        *,
        window_name: str | None = None,
    ) -> int:
        target = _session_window_target(namespace["session_name"], window_name)
        try:
            result = self._backend._tmux_run(["attach", "-t", target], check=False, capture=False)
        except Exception as exc:
            raise self._map_error(exc, operation="attach_namespace", tmux_args=["attach", "-t", target]) from exc
        return int(getattr(result, "returncode", 0) or 0)

    def destroy_namespace(self, namespace: MuxNamespaceRef) -> None:
        self._run_checked(["kill-session", "-t", namespace["session_name"]], operation="destroy_namespace")

    def namespace_exists(
        self,
        namespace: MuxNamespaceRef,
        *,
        timeout_s: float | None = None,
    ) -> bool:
        return self.session_alive(namespace, timeout_s=timeout_s)

    def session_alive(
        self,
        namespace: MuxNamespaceRef,
        *,
        timeout_s: float | None = None,
    ) -> bool:
        try:
            return bool(
                self._wait_until(
                    lambda: self._session_alive_once(namespace),
                    operation="session_alive",
                    timeout_s=timeout_s,
                )
            )
        except MuxCommandError:
            raise

    def session_root_pane(
        self,
        namespace: MuxNamespaceRef,
        *,
        timeout_s: float | None = None,
    ) -> MuxPaneRef:
        pane_id = self._wait_until(lambda: self._root_pane_once(namespace["session_name"]), operation="session_root_pane", timeout_s=timeout_s)
        if not pane_id:
            raise MuxCommandError(
                category="not-found",
                backend_impl="tmux",
                operation="session_root_pane",
                detail=f"failed to resolve root pane for tmux session {namespace['session_name']!r}",
                ipc_ref=namespace["ipc_ref"],
            )
        return self.pane_ref(str(pane_id), session_name=namespace["session_name"], window_name=None)

    def kill_server(self, namespace: MuxNamespaceRef | None = None) -> bool:
        target_args = ["kill-session", "-t", namespace["session_name"]] if namespace is not None else ["kill-server"]
        try:
            self._run_checked(target_args, operation="kill_server")
            self._cleanup_socket_path()
            return True
        except MuxCommandError:
            return False

    def list_windows(self, namespace: MuxNamespaceRef) -> tuple[MuxWindowInfo, ...]:
        result = self._run_ready(
            [
                "list-windows",
                "-t",
                namespace["session_name"],
                "-F",
                "#{window_name}\t#{window_active}\t#{window_panes}\t#{pane_current_path}\t#{window_layout}",
            ],
            operation="list_windows",
        )
        windows: list[MuxWindowInfo] = []
        for line in str(getattr(result, "stdout", "") or "").splitlines():
            parts = line.split("\t")
            if len(parts) != 5:
                continue
            try:
                pane_count = int(parts[2])
            except ValueError:
                pane_count = 0
            windows.append(
                {
                    "session_name": namespace["session_name"],
                    "window_name": parts[0],
                    "active": parts[1] in {"1", "true", "True"},
                    "pane_count": pane_count,
                    "project_root": parts[3],
                    "layout": parts[4] or None,
                }
            )
        return tuple(windows)

    def ensure_window(
        self,
        namespace: MuxNamespaceRef,
        *,
        window_name: str,
        project_root: str,
        select: bool = False,
    ) -> MuxWindowInfo:
        for record in self.list_windows(namespace):
            if record["window_name"] != window_name:
                continue
            if select:
                self.select_window(namespace, target=_session_window_target(namespace["session_name"], window_name))
            return record
        self._run_ready(
            [
                "new-window",
                "-d",
                "-t",
                namespace["session_name"],
                "-n",
                window_name,
                "-c",
                str(project_root),
                *pane_placeholder_argv(),
            ],
            operation="ensure_window",
        )
        if select:
            self.select_window(namespace, target=_session_window_target(namespace["session_name"], window_name))
        return next(
            (record for record in self.list_windows(namespace) if record["window_name"] == window_name),
            {
                "session_name": namespace["session_name"],
                "window_name": window_name,
                "active": bool(select),
                "pane_count": 1,
                "project_root": str(project_root),
                "layout": None,
            },
        )

    def kill_window(self, namespace: MuxNamespaceRef, *, target: str) -> None:
        self._run_ready(["kill-window", "-t", target], operation="kill_window")

    def list_panes(
        self,
        namespace: MuxNamespaceRef,
        *,
        window_name: str | None = None,
    ) -> tuple[MuxPaneRef, ...]:
        target = _session_window_target(namespace["session_name"], window_name)
        result = self._run_ready(
            ["list-panes", "-t", target, "-F", "#{pane_id}\t#{window_name}"],
            operation="list_panes",
        )
        refs: list[MuxPaneRef] = []
        for line in str(getattr(result, "stdout", "") or "").splitlines():
            parts = line.split("\t")
            pane_id = (parts[0] if parts else "").strip()
            if not pane_id:
                continue
            refs.append(
                self.pane_ref(
                    pane_id,
                    session_name=namespace["session_name"],
                    window_name=(parts[1].strip() if len(parts) > 1 and parts[1].strip() else window_name),
                )
            )
        return tuple(refs)

    def window_root_pane(
        self,
        namespace: MuxNamespaceRef,
        *,
        window_name: str,
        timeout_s: float | None = None,
    ) -> MuxPaneRef:
        target = _session_window_target(namespace["session_name"], window_name)
        pane_id = self._wait_until(lambda: self._root_pane_once(target), operation="window_root_pane", timeout_s=timeout_s)
        if not pane_id:
            raise MuxCommandError(
                category="not-found",
                backend_impl="tmux",
                operation="window_root_pane",
                detail=f"failed to resolve root pane for tmux target {target!r}",
                ipc_ref=namespace["ipc_ref"],
            )
        return self.pane_ref(str(pane_id), session_name=namespace["session_name"], window_name=window_name)

    def select_window(self, namespace: MuxNamespaceRef, *, target: str) -> None:
        del namespace
        self._run_ready(["select-window", "-t", target], operation="select_window")

    def split_pane(
        self,
        parent: MuxPaneRef | str,
        *,
        direction: SplitDirection,
        percent: int,
        cmd: str | None = None,
        cwd: str | None = None,
    ) -> MuxPaneRef | str:
        _flag, semantic_direction = normalize_split_direction(direction)
        parent_pane_id = _pane_id(parent)
        try:
            pane_id = self._backend.split_pane(
                parent_pane_id,
                direction=semantic_direction,
                percent=max(1, min(99, int(percent))),
                cmd=cmd,
                cwd=cwd,
            )
        except Exception as exc:
            raise self._map_error(exc, operation="split_pane", tmux_args=["split-window"]) from exc
        if isinstance(parent, dict):
            return self.pane_ref(str(pane_id), session_name=parent["session_name"], window_name=parent.get("window_name"))
        return str(pane_id)

    def reflow_window(
        self,
        namespace: MuxNamespaceRef,
        *,
        window_name: str,
        layout: str,
        expected_panes: tuple[MuxPaneRef, ...] = (),
    ) -> None:
        if expected_panes:
            observed = {pane["pane_id"] for pane in self.list_panes(namespace, window_name=window_name)}
            missing = [pane["pane_id"] for pane in expected_panes if pane["pane_id"] not in observed]
            if missing:
                raise MuxCommandError(
                    category="not-found",
                    backend_impl="tmux",
                    operation="reflow_window",
                    detail=f"expected pane is not in target window: {', '.join(missing)}",
                    ipc_ref=namespace["ipc_ref"],
                    evidence={"missing_panes": missing},
                )
        self.select_layout(namespace, window_name=window_name, layout=layout)

    def select_layout(
        self,
        namespace: MuxNamespaceRef,
        *,
        window_name: str,
        layout: str,
    ) -> None:
        target = _session_window_target(namespace["session_name"], window_name)
        self._run_checked(["select-layout", "-t", target, layout], operation="select_layout")

    def move_pane(self, pane: MuxPaneRef, *, target: str) -> None:
        self._run_checked(["move-pane", "-s", pane["pane_id"], "-t", target], operation="move_pane")

    def swap_pane(self, source: MuxPaneRef, *, target: MuxPaneRef) -> None:
        self._run_checked(["swap-pane", "-s", source["pane_id"], "-t", target["pane_id"]], operation="swap_pane")

    def send_text(self, pane: MuxPaneRef | str, text: str) -> None:
        pane_id = _pane_id(pane)
        try:
            self._backend.send_text(pane_id, text)
        except Exception as exc:
            raise self._map_error(exc, operation="send_text", tmux_args=["send-keys", "-t", pane_id]) from exc

    def send_key(self, pane: MuxPaneRef | str, key: str) -> bool:
        pane_id = _pane_id(pane)
        try:
            return bool(self._backend.send_key(pane_id, key))
        except Exception as exc:
            raise self._map_error(exc, operation="send_key", tmux_args=["send-keys", "-t", pane_id, key]) from exc

    def get_current_pane_id(self) -> str:
        try:
            return str(self._backend.get_current_pane_id())
        except Exception as exc:
            raise self._map_error(exc, operation="get_current_pane_id") from exc

    def is_alive(self, pane: MuxPaneRef | str) -> bool:
        pane_id = _pane_id(pane)
        try:
            return bool(self._backend.is_alive(pane_id))
        except Exception as exc:
            raise self._map_error(exc, operation="is_alive", tmux_args=["has-session", "-t", pane_id]) from exc

    def is_tmux_pane_alive(self, pane_id: str) -> bool:
        return self.is_alive(pane_id)

    def activate(self, pane: MuxPaneRef | str) -> None:
        pane_id = _pane_id(pane)
        try:
            self._backend.activate(pane_id)
        except Exception as exc:
            raise self._map_error(exc, operation="activate", tmux_args=["select-pane", "-t", pane_id]) from exc

    def create_pane(
        self,
        cmd: str,
        cwd: str,
        direction: str = "right",
        percent: int = 50,
        parent_pane: str | None = None,
    ) -> str:
        try:
            return str(
                self._backend.create_pane(
                    cmd,
                    cwd,
                    direction=direction,
                    percent=percent,
                    parent_pane=parent_pane,
                )
            )
        except Exception as exc:
            raise self._map_error(exc, operation="create_pane", tmux_args=["split-window"]) from exc

    def capture_pane(self, pane: MuxPaneRef | str, *, lines: int = 20) -> str | None:
        pane_id = _pane_id(pane)
        try:
            return self._backend.get_text(pane_id, lines=lines)
        except Exception as exc:
            raise self._map_error(exc, operation="capture_pane", tmux_args=["capture-pane", "-t", pane_id]) from exc

    def get_text(self, pane: MuxPaneRef | str, lines: int = 20) -> str | None:
        return self.capture_pane(pane, lines=lines)

    def respawn_pane(
        self,
        pane: MuxPaneRef | str,
        *,
        cmd: str,
        cwd: str | None = None,
        remain_on_exit: bool = True,
    ) -> None:
        pane_id = _pane_id(pane)
        try:
            self._backend.respawn_pane(pane_id, cmd=cmd, cwd=cwd, remain_on_exit=remain_on_exit)
        except Exception as exc:
            raise self._map_error(exc, operation="respawn_pane", tmux_args=["respawn-pane", "-t", pane_id]) from exc

    def kill_pane(self, pane: MuxPaneRef | str) -> None:
        pane_id = _pane_id(pane)
        try:
            self._backend.kill_pane(pane_id)
        except Exception as exc:
            raise self._map_error(exc, operation="kill_pane", tmux_args=["kill-pane", "-t", pane_id]) from exc

    def kill_tmux_pane(self, pane_id: str) -> None:
        self.kill_pane(pane_id)

    def set_pane_title(self, pane: MuxPaneRef | str, title: str) -> None:
        pane_id = _pane_id(pane)
        try:
            self._backend.set_pane_title(pane_id, title)
        except Exception as exc:
            raise self._map_error(exc, operation="set_pane_title", tmux_args=["select-pane", "-t", pane_id]) from exc

    def set_pane_user_option(self, pane: MuxPaneRef | str, name: str, value: str) -> None:
        pane_id = _pane_id(pane)
        try:
            self._backend.set_pane_user_option(pane_id, name, value)
        except Exception as exc:
            raise self._map_error(exc, operation="set_pane_user_option", tmux_args=["set-option", "-p", "-t", pane_id]) from exc

    def set_pane_style(
        self,
        pane: MuxPaneRef | str,
        *,
        border_style: str | None = None,
        active_border_style: str | None = None,
    ) -> None:
        pane_id = _pane_id(pane)
        try:
            self._backend.set_pane_style(
                pane_id,
                border_style=border_style,
                active_border_style=active_border_style,
            )
        except Exception as exc:
            raise self._map_error(exc, operation="set_pane_style", tmux_args=["select-pane", "-t", pane_id]) from exc

    def set_pane_identity(
        self,
        pane: MuxPaneRef | str,
        *,
        title: str,
        user_options: dict[str, str],
        border_style: str | None = None,
        active_border_style: str | None = None,
    ) -> None:
        pane_id = _pane_id(pane)
        try:
            self._backend.set_pane_identity(
                pane_id,
                title=title,
                user_options=user_options,
                border_style=border_style,
                active_border_style=active_border_style,
            )
        except Exception as exc:
            raise self._map_error(exc, operation="set_pane_identity", tmux_args=["set-option", "-p", "-t", pane_id]) from exc

    def ensure_pane_log(self, pane: MuxPaneRef | str) -> str | None:
        pane_id = _pane_id(pane)
        try:
            path = self._backend.ensure_pane_log(pane_id)
        except Exception as exc:
            raise self._map_error(exc, operation="ensure_pane_log", tmux_args=["pipe-pane", "-t", pane_id]) from exc
        return str(path) if path is not None else None

    def pane_log_path(self, pane: MuxPaneRef | str) -> str | None:
        pane_id = _pane_id(pane)
        try:
            path = self._backend.pane_log_path(pane_id)
        except Exception as exc:
            raise self._map_error(exc, operation="pane_log_path", tmux_args=["pipe-pane", "-t", pane_id]) from exc
        return str(path) if path is not None else None

    def describe_pane(
        self,
        pane: MuxPaneRef | str,
        *,
        user_options: tuple[str, ...] = (),
    ) -> dict[str, str] | None:
        pane_id = _pane_id(pane)
        try:
            return self._backend.describe_pane(pane_id, user_options=user_options)
        except Exception as exc:
            raise self._map_error(exc, operation="describe_pane", tmux_args=["list-panes", "-t", pane_id]) from exc

    def describe_window_panes(
        self,
        namespace: MuxNamespaceRef,
        *,
        window_name: str,
        user_options: tuple[str, ...] = (),
    ) -> tuple[dict[str, str], ...]:
        option_fields = tuple(str(option) for option in user_options)
        format_parts = (
            "#{pane_id}",
            "#{pane_index}",
            "#{pane_left}",
            "#{pane_top}",
            "#{pane_width}",
            "#{pane_height}",
            "#{window_name}",
            *tuple(f"#{{{option}}}" for option in option_fields),
        )
        target = _session_window_target(namespace["session_name"], window_name)
        result = self._run_checked(
            ["list-panes", "-t", target, "-F", "\t".join(format_parts)],
            operation="describe_window_panes",
        )
        records: list[dict[str, str]] = []
        for line in str(getattr(result, "stdout", "") or "").splitlines():
            parts = line.split("\t")
            if len(parts) < 7:
                continue
            record = {
                "pane_id": parts[0],
                "pane_index": parts[1],
                "pane_left": parts[2],
                "pane_top": parts[3],
                "pane_width": parts[4],
                "pane_height": parts[5],
                "window_name": parts[6],
            }
            for index, option in enumerate(option_fields, start=7):
                record[option] = parts[index] if index < len(parts) else ""
            records.append(record)
        return tuple(records)

    def _apply_environment_policy(self, *, timeout_s: float | None = None) -> None:
        self._run_optional(
            ["set-option", "-g", "update-environment", " ".join(TMUX_ENVIRONMENT_KEYS)],
            operation="ensure_server_policy",
            timeout_s=timeout_s,
        )
        for key in TMUX_ENVIRONMENT_KEYS:
            value = os.environ.get(key)
            if value:
                self._run_optional(["set-environment", "-g", key, value], operation="ensure_server_policy", timeout_s=timeout_s)

    def _session_alive_once(self, namespace: MuxNamespaceRef) -> bool:
        result = self._backend._tmux_run(["has-session", "-t", namespace["session_name"]], check=False, capture=True)
        if int(getattr(result, "returncode", 1) or 0) == 0:
            return True
        detail = _completed_detail(result)
        if is_tmux_absent_server_text(detail) or is_tmux_missing_session_text(detail) or not detail:
            return False
        if is_tmux_transient_server_error_text(detail):
            raise TmuxTransientServerUnavailable("tmux server unavailable", detail=detail, command=self._command(["has-session", "-t", namespace["session_name"]]))
        raise TmuxCommandError(detail, args=["has-session", "-t", namespace["session_name"]], detail=detail, command=self._command(["has-session", "-t", namespace["session_name"]]))

    def _root_pane_once(self, target: str) -> str | None:
        result = self._run_checked(["list-panes", "-t", target, "-F", "#{pane_id}"], operation="window_root_pane")
        pane_id = ((str(getattr(result, "stdout", "") or "").splitlines() or [""])[0]).strip()
        return pane_id or None

    def _run_optional(self, args: list[str], *, operation: str, timeout_s: float | None = None) -> bool:
        try:
            self._run_ready(args, operation=operation, timeout_s=timeout_s)
        except MuxCommandError:
            return False
        return True

    def _run_ready(self, args: list[str], *, operation: str, timeout_s: float | None = None):
        return self._wait_until_ready(lambda: self._run_checked(args, operation=operation), operation=operation, timeout_s=timeout_s)

    def _run_checked(self, args: list[str], *, operation: str):
        try:
            result = self._backend._tmux_run(args, check=False, capture=True)
        except Exception as exc:
            raise self._map_error(exc, operation=operation, tmux_args=args) from exc
        if int(getattr(result, "returncode", 1) or 0) == 0:
            return result
        detail = tmux_failure_detail(result, args)
        raise self._map_error(
            TmuxCommandError(detail, args=args, detail=detail, socket_path=self.socket_path, command=self._command(args)),
            operation=operation,
            tmux_args=args,
            completed_process=result,
        )

    def _wait_until(self, probe, *, operation: str, timeout_s: float | None = None):
        deadline = time.monotonic() + tmux_object_ready_timeout_s(timeout_s)
        last_transient: TmuxTransientServerUnavailable | None = None
        while True:
            try:
                value = probe()
            except TmuxTransientServerUnavailable as exc:
                last_transient = exc
                value = None
            if value is not None:
                return value
            if time.monotonic() >= deadline:
                if last_transient is not None:
                    raise self._map_error(last_transient, operation=operation) from last_transient
                return None
            time.sleep(tmux_object_ready_poll_interval_s())

    def _wait_until_ready(self, action, *, operation: str, timeout_s: float | None = None):
        deadline = time.monotonic() + tmux_object_ready_timeout_s(timeout_s)
        last_error: Exception | None = None
        while True:
            try:
                return action()
            except MuxCommandError as exc:
                last_error = exc
            if time.monotonic() >= deadline:
                break
            time.sleep(tmux_object_ready_poll_interval_s())
        if last_error is not None:
            raise last_error
        raise MuxCommandError(
            category="command-failed",
            backend_impl="tmux",
            operation=operation,
            detail=f"{operation} timed out",
            ipc_ref=self._ipc_ref(),
        )

    def _map_error(
        self,
        exc: BaseException,
        *,
        operation: str,
        tmux_args: list[str] | tuple[str, ...] | None = None,
        completed_process: object | None = None,
    ) -> MuxCommandError:
        if isinstance(exc, MuxCommandError):
            return exc
        detail = _error_detail(exc, completed_process=completed_process)
        evidence = _error_evidence(exc, tmux_args=tmux_args, completed_process=completed_process)
        if "command" not in evidence and tmux_args:
            command = self._command(tmux_args)
            if command:
                evidence["command"] = command
        evidence.setdefault("socket_path", self.socket_path)
        evidence.setdefault("socket_name", self.socket_name)
        evidence.setdefault("ipc_kind", self._ipc_kind())
        evidence.setdefault("ipc_ref", self._ipc_ref())
        return MuxCommandError(
            category=_error_category(exc, detail),
            backend_impl="tmux",
            operation=operation,
            detail=detail,
            ipc_ref=self._ipc_ref(),
            command=evidence.get("command"),
            evidence=evidence,
        )

    def _command(self, args: list[str] | tuple[str, ...]) -> tuple[str, ...] | None:
        tmux_base = getattr(self._backend, "_tmux_base", None)
        if not callable(tmux_base):
            return None
        try:
            return tuple(str(item) for item in [*tmux_base(), *args])
        except Exception:
            return None

    def _ipc_kind(self) -> str:
        return "unix_socket" if self.socket_path else "socket_name"

    def _ipc_ref(self) -> str:
        return self.socket_path or self.socket_name or "<default>"

    def _cleanup_socket_path(self) -> None:
        socket_path = self.socket_path
        if not socket_path:
            return
        for _ in range(30):
            if not os.path.exists(socket_path):
                return
            time.sleep(0.1)
        try:
            if os.path.exists(socket_path):
                os.unlink(socket_path)
        except OSError:
            pass


def _require_text(value: str | None, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name} is required")
    return text


def _pane_id(pane: MuxPaneRef | str) -> str:
    if isinstance(pane, dict):
        return _require_text(pane.get("pane_id"), "pane_id")
    return _require_text(str(pane), "pane_id")


def _resolved_session_size(terminal_size: tuple[int, int] | None) -> tuple[int, int]:
    default = (160, 48)
    if terminal_size is None:
        return default
    try:
        width = int(terminal_size[0])
        height = int(terminal_size[1])
    except Exception:
        return default
    if width < 40 or height < 15:
        return default
    return width, height


def _session_window_target(session_name: str, window_name: str | None = None) -> str:
    session = _require_text(session_name, "session_name")
    window = str(window_name or "").strip()
    return f"{session}:{window}" if window else session


def _completed_detail(completed_process: object) -> str:
    stderr = str(getattr(completed_process, "stderr", "") or "").strip()
    stdout = str(getattr(completed_process, "stdout", "") or "").strip()
    return stderr or stdout


def _error_detail(exc: BaseException, *, completed_process: object | None = None) -> str:
    if completed_process is not None:
        detail = _completed_detail(completed_process)
        if detail:
            return detail
    detail = str(getattr(exc, "detail", "") or "").strip()
    if detail:
        return detail
    return str(exc).strip() or type(exc).__name__


def _error_category(exc: BaseException, detail: str) -> MuxErrorCategory:
    lowered = detail.lower()
    if isinstance(exc, TmuxTransientServerUnavailable) or is_tmux_transient_server_error_text(detail):
        return "transient-unavailable"
    if is_tmux_absent_server_text(detail):
        return "transient-unavailable"
    if isinstance(exc, subprocess.TimeoutExpired):
        return "transient-unavailable"
    if isinstance(exc, FileNotFoundError):
        return "unsupported"
    if is_tmux_missing_session_text(detail) or "can't find pane" in lowered or "can't find window" in lowered or "pane not found" in lowered or "window not found" in lowered:
        return "not-found"
    if "permission denied" in lowered or "access denied" in lowered or "operation not permitted" in lowered:
        return "permission"
    if "unknown command" in lowered or "invalid option" in lowered or "not supported" in lowered or "unsupported" in lowered:
        return "unsupported"
    return "command-failed"


def _error_evidence(
    exc: BaseException,
    *,
    tmux_args: list[str] | tuple[str, ...] | None,
    completed_process: object | None,
) -> dict[str, Any]:
    command_value = getattr(exc, "command", None) or getattr(exc, "cmd", None) or ()
    command = tuple(str(item) for item in command_value) if isinstance(command_value, (list, tuple)) else ((str(command_value),) if command_value else ())
    args = tuple(str(item) for item in (tmux_args or getattr(exc, "tmux_args", ()) or ()))
    evidence: dict[str, Any] = {
        "original_exception_type": type(exc).__name__,
        "tmux_args": args,
    }
    if command:
        evidence["command"] = command
    if completed_process is not None:
        evidence["returncode"] = int(getattr(completed_process, "returncode", 1) or 0)
        evidence["stdout"] = str(getattr(completed_process, "stdout", "") or "")
        evidence["stderr"] = str(getattr(completed_process, "stderr", "") or "")
    if isinstance(exc, subprocess.CalledProcessError):
        evidence["returncode"] = int(exc.returncode)
        evidence["stdout"] = str(exc.stdout or "")
        evidence["stderr"] = str(exc.stderr or "")
    if isinstance(exc, subprocess.TimeoutExpired):
        evidence["timeout"] = exc.timeout
        evidence["stdout"] = str(exc.stdout or "")
        evidence["stderr"] = str(exc.stderr or "")
    return evidence


__all__ = ["TmuxMuxBackendAdapter"]
