from __future__ import annotations

from terminal_runtime.mux_backend_contract import MuxCommandError, MuxNamespaceRef, MuxPaneRef, MuxWindowInfo
from terminal_runtime.placeholders import pane_placeholder_argv
from terminal_runtime.rmux_backend_runtime.errors import (
    is_not_found_detail,
    malformed_output_error,
    map_rmux_result_error,
    not_found_error,
)


def namespace_ref(
    *,
    session_name: str,
    namespace_id: str | None = None,
    socket_path: str | None = None,
    namespace: str | None = None,
) -> MuxNamespaceRef:
    session = _require_text(session_name, "session_name")
    if socket_path:
        ipc_kind = "named_pipe" if _looks_like_windows_pipe(socket_path) else "socket_path"
        ipc_ref = socket_path
    else:
        ipc_kind = "socket_name"
        ipc_ref = namespace or session
    return {
        "backend_family": "tmux-family",
        "backend_impl": "rmux",
        "namespace_id": _require_text(namespace_id or session, "namespace_id"),
        "session_name": session,
        "ipc_kind": ipc_kind,  # type: ignore[typeddict-item]
        "ipc_ref": ipc_ref,
    }


def prepare_server(backend, *, timeout_s: float | None = None) -> None:
    backend._require_capability("prepare_server", ("start-server",))
    backend._run_checked(["start-server"], operation="prepare_server", timeout_s=timeout_s)


def ensure_server_policy(
    backend,
    *,
    namespace: MuxNamespaceRef | None = None,
    timeout_s: float | None = None,
) -> None:
    del namespace
    backend._require_capability("ensure_server_policy", ("set-option", "set-window-option"))
    backend._run_checked(
        ["set-option", "-g", "destroy-unattached", "off"],
        operation="ensure_server_policy",
        timeout_s=timeout_s,
    )
    for option, value in (
        ("mouse", "on"),
        ("history-limit", "50000"),
        ("focus-events", "on"),
    ):
        backend._run_checked(
            ["set-option", "-g", option, value],
            operation="ensure_server_policy",
            timeout_s=timeout_s,
        )
    backend._run_checked(
        ["set-window-option", "-g", "mode-keys", "vi"],
        operation="ensure_server_policy",
        timeout_s=timeout_s,
    )


def create_session(
    backend,
    *,
    session_name: str,
    project_root: str,
    window_name: str | None = None,
    terminal_size: tuple[int, int] | None = None,
) -> MuxNamespaceRef:
    session = _require_text(session_name, "session_name")
    window = str(window_name or "").strip()
    required = ("new-session", "new-window") if window else ("new-session",)
    backend._require_capability("create_session", required)
    width, height = _resolved_session_size(terminal_size)
    args = ["new-session", "-d", "-x", str(width), "-y", str(height), "-s", session]
    if window:
        args.extend(["-n", window])
    args.extend(["-c", str(project_root), *pane_placeholder_argv()])
    backend._run_checked(args, operation="create_session")
    return backend.namespace_ref(session_name=session)


def attach_namespace(backend, *, namespace: MuxNamespaceRef, window_name: str | None = None) -> int:
    backend._require_capability("attach_namespace", ("attach-session",))
    target = _session_window_target(namespace["session_name"], window_name)
    result = backend._client.run(["attach-session", "-t", target], foreground=True)
    if result.returncode == 0:
        return 0
    raise map_rmux_result_error(
        result,
        operation="attach_namespace",
        ipc_ref=backend._ipc_ref(),
        daemon_evidence=backend.daemon_evidence,
    )


def destroy_namespace(backend, namespace: MuxNamespaceRef) -> None:
    backend._require_capability("destroy_namespace", ("kill-session",))
    backend._run_checked(["kill-session", "-t", namespace["session_name"]], operation="destroy_namespace")


def namespace_exists(backend, namespace: MuxNamespaceRef, *, timeout_s: float | None = None) -> bool:
    return session_alive(backend, namespace, timeout_s=timeout_s)


def session_alive(backend, namespace: MuxNamespaceRef, *, timeout_s: float | None = None) -> bool:
    backend._require_capability("session_alive", ("has-session",))
    result = backend._run_unchecked(["has-session", "-t", namespace["session_name"]], timeout_s=timeout_s)
    if result.returncode == 0:
        return True
    detail = (result.stderr or result.stdout or "").strip()
    if not detail or is_not_found_detail(detail):
        return False
    raise map_rmux_result_error(
        result,
        operation="session_alive",
        ipc_ref=backend._ipc_ref(),
        daemon_evidence=backend.daemon_evidence,
    )


def session_root_pane(
    backend,
    namespace: MuxNamespaceRef,
    *,
    timeout_s: float | None = None,
) -> MuxPaneRef:
    del timeout_s
    panes = backend.list_panes(namespace)
    if not panes:
        raise not_found_error(
            operation="session_root_pane",
            detail=f"rmux session {namespace['session_name']!r} has no panes",
            ipc_ref=backend._ipc_ref(),
            evidence={"session_name": namespace["session_name"]},
        )
    return panes[0]


def kill_server(backend, namespace: MuxNamespaceRef | None = None) -> bool:
    if namespace is not None:
        try:
            destroy_namespace(backend, namespace)
            return True
        except MuxCommandError:
            return False
    backend._require_capability("kill_server", ("kill-server",))
    try:
        backend._run_checked(["kill-server"], operation="kill_server")
    except MuxCommandError:
        return False
    return True


def list_windows(backend, namespace: MuxNamespaceRef) -> tuple[MuxWindowInfo, ...]:
    backend._require_capability("list_windows", ("list-windows",))
    result = backend._run_checked(
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
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) != 5:
            raise malformed_output_error(
                operation="list_windows",
                detail=f"rmux list-windows returned malformed row: {line!r}",
                result=result,
                ipc_ref=backend._ipc_ref(),
                daemon_evidence=backend.daemon_evidence,
            )
        windows.append(
            {
                "session_name": namespace["session_name"],
                "window_name": parts[0],
                "active": parts[1] in {"1", "true", "True", "yes", "on"},
                "pane_count": _int_or_zero(parts[2]),
                "project_root": parts[3],
                "layout": parts[4] or None,
            }
        )
    return tuple(windows)


def ensure_window(
    backend,
    namespace: MuxNamespaceRef,
    *,
    window_name: str,
    project_root: str,
    select: bool = False,
) -> MuxWindowInfo:
    backend._require_capability("ensure_window", ("list-windows", "new-window"))
    name = _require_text(window_name, "window_name")
    for record in backend.list_windows(namespace):
        if record["window_name"] == name:
            if select:
                backend.select_window(namespace, target=_session_window_target(namespace["session_name"], name))
            return record
    args = ["new-window", "-d", "-t", namespace["session_name"], "-n", name, "-c", str(project_root), *pane_placeholder_argv()]
    backend._run_checked(args, operation="ensure_window")
    if select:
        backend.select_window(namespace, target=_session_window_target(namespace["session_name"], name))
    return next(
        (record for record in backend.list_windows(namespace) if record["window_name"] == name),
        {
            "session_name": namespace["session_name"],
            "window_name": name,
            "active": bool(select),
            "pane_count": 1,
            "project_root": str(project_root),
            "layout": None,
        },
    )


def kill_window(backend, namespace: MuxNamespaceRef, *, target: str) -> None:
    del namespace
    backend._require_capability("kill_window", ("kill-window",))
    backend._run_checked(["kill-window", "-t", _require_text(target, "target")], operation="kill_window")


def window_root_pane(
    backend,
    namespace: MuxNamespaceRef,
    *,
    window_name: str,
    timeout_s: float | None = None,
) -> MuxPaneRef:
    del timeout_s
    panes = backend.list_panes(namespace, window_name=window_name)
    if not panes:
        raise not_found_error(
            operation="window_root_pane",
            detail=f"rmux window {window_name!r} has no panes",
            ipc_ref=backend._ipc_ref(),
            evidence={"session_name": namespace["session_name"], "window_name": window_name},
        )
    return panes[0]


def select_window(backend, namespace: MuxNamespaceRef, *, target: str) -> None:
    del namespace
    backend._require_capability("select_window", ("select-window",))
    backend._run_checked(["select-window", "-t", _require_text(target, "target")], operation="select_window")


def _session_window_target(session_name: str, window_name: str | None = None) -> str:
    session = _require_text(session_name, "session_name")
    window = str(window_name or "").strip()
    return f"{session}:{window}" if window else session


def _require_text(value: str | None, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name} is required")
    return text


def _resolved_session_size(terminal_size: tuple[int, int] | None) -> tuple[int, int]:
    if terminal_size is None:
        return 160, 48
    try:
        width = int(terminal_size[0])
        height = int(terminal_size[1])
    except Exception:
        return 160, 48
    if width < 40 or height < 15:
        return 160, 48
    return width, height


def _int_or_zero(value: str) -> int:
    try:
        return int(value)
    except ValueError:
        return 0


def _looks_like_windows_pipe(value: str) -> bool:
    return str(value or "").replace("/", "\\").startswith("\\\\.\\pipe\\")


__all__ = [
    "attach_namespace",
    "create_session",
    "destroy_namespace",
    "ensure_server_policy",
    "ensure_window",
    "kill_server",
    "kill_window",
    "list_windows",
    "namespace_exists",
    "namespace_ref",
    "prepare_server",
    "select_window",
    "session_alive",
    "session_root_pane",
    "window_root_pane",
]
