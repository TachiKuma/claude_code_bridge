from __future__ import annotations

from terminal_runtime.mux_backend_contract import MuxNamespaceRef, MuxPaneRef, SplitDirection
from terminal_runtime.rmux_backend_runtime.errors import malformed_output_error, not_found_error


def list_panes(
    backend,
    namespace: MuxNamespaceRef,
    *,
    window_name: str | None = None,
) -> tuple[MuxPaneRef, ...]:
    backend._require_capability("list_panes", ("list-panes",))
    target = _session_window_target(namespace["session_name"], window_name)
    result = backend._run_checked(
        ["list-panes", "-t", target, "-F", "#{pane_id}\t#{window_name}"],
        operation="list_panes",
    )
    refs: list[MuxPaneRef] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if not parts[0].strip():
            raise malformed_output_error(
                operation="list_panes",
                detail=f"rmux list-panes returned malformed row: {line!r}",
                result=result,
                ipc_ref=backend._ipc_ref(),
                daemon_evidence=backend.daemon_evidence,
            )
        refs.append(
            backend.pane_ref(
                parts[0].strip(),
                session_name=namespace["session_name"],
                window_name=(parts[1].strip() if len(parts) > 1 and parts[1].strip() else window_name),
            )
        )
    return tuple(refs)


def split_pane(
    backend,
    parent: MuxPaneRef,
    *,
    direction: SplitDirection,
    percent: int,
    cmd: str | None = None,
    cwd: str | None = None,
) -> MuxPaneRef:
    backend._require_capability("split_pane", ("split-window",))
    flag = _split_flag(direction)
    split_percent = max(1, min(99, int(percent)))
    args = [
        "split-window",
        flag,
        "-p",
        str(split_percent),
        "-t",
        _pane_id(parent),
        "-P",
        "-F",
        "#{pane_id}",
    ]
    if cwd:
        args.extend(["-c", str(cwd)])
    if cmd:
        args.append(str(cmd))
    result = backend._run_checked(args, operation="split_pane")
    pane_id = _first_stdout_token(result.stdout)
    if not pane_id:
        raise malformed_output_error(
            operation="split_pane",
            detail="rmux split-window did not return pane id",
            result=result,
            ipc_ref=backend._ipc_ref(),
            daemon_evidence=backend.daemon_evidence,
        )
    return backend.pane_ref(
        pane_id,
        session_name=parent["session_name"],
        window_name=parent.get("window_name"),
    )


def respawn_pane(
    backend,
    pane: MuxPaneRef,
    *,
    cmd: str,
    cwd: str | None = None,
    remain_on_exit: bool = True,
) -> None:
    backend._require_capability("respawn_pane", ("respawn-pane",))
    args = ["respawn-pane", "-k", "-t", _pane_id(pane)]
    if remain_on_exit:
        args.append("-P")
    if cwd:
        args.extend(["-c", str(cwd)])
    args.append(_require_text(cmd, "cmd"))
    backend._run_checked(args, operation="respawn_pane")


def kill_pane(backend, pane: MuxPaneRef) -> None:
    backend._require_capability("kill_pane", ("kill-pane",))
    backend._run_checked(["kill-pane", "-t", _pane_id(pane)], operation="kill_pane")


def reflow_window(
    backend,
    namespace: MuxNamespaceRef,
    *,
    window_name: str,
    layout: str,
    expected_panes: tuple[MuxPaneRef, ...] = (),
) -> None:
    if expected_panes:
        observed = {pane["pane_id"] for pane in backend.list_panes(namespace, window_name=window_name)}
        missing = [pane["pane_id"] for pane in expected_panes if pane["pane_id"] not in observed]
        if missing:
            raise not_found_error(
                operation="reflow_window",
                detail=f"expected pane is not in target window: {', '.join(missing)}",
                ipc_ref=backend._ipc_ref(),
                evidence={"missing_panes": missing, "window_name": window_name},
            )
    select_layout(backend, namespace, window_name=window_name, layout=layout)


def select_layout(
    backend,
    namespace: MuxNamespaceRef,
    *,
    window_name: str,
    layout: str,
) -> None:
    backend._require_capability("select_layout", ("select-layout",))
    backend._run_checked(
        ["select-layout", "-t", _session_window_target(namespace["session_name"], window_name), _require_text(layout, "layout")],
        operation="select_layout",
    )


def move_pane(backend, pane: MuxPaneRef, *, target: str) -> None:
    backend._require_capability("move_pane", ("move-pane",))
    backend._run_checked(["move-pane", "-s", _pane_id(pane), "-t", _require_text(target, "target")], operation="move_pane")


def swap_pane(backend, source: MuxPaneRef, *, target: MuxPaneRef) -> None:
    backend._require_capability("swap_pane", ("swap-pane",))
    backend._run_checked(["swap-pane", "-s", _pane_id(source), "-t", _pane_id(target)], operation="swap_pane")


def describe_pane(
    backend,
    pane: MuxPaneRef,
    *,
    user_options: tuple[str, ...] = (),
) -> dict[str, str] | None:
    records = describe_window_panes(
        backend,
        {"session_name": pane["session_name"]},
        window_name=pane.get("window_name") or "",
        user_options=user_options,
    )
    for record in records:
        if record.get("pane_id") == pane["pane_id"]:
            return record
    return None


def describe_window_panes(
    backend,
    namespace: MuxNamespaceRef,
    *,
    window_name: str,
    user_options: tuple[str, ...] = (),
) -> tuple[dict[str, str], ...]:
    backend._require_capability("describe_window_panes", ("list-panes",))
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
    target = _session_window_target(namespace["session_name"], window_name or None)
    result = backend._run_checked(
        ["list-panes", "-t", target, "-F", "\t".join(format_parts)],
        operation="describe_window_panes",
    )
    records: list[dict[str, str]] = []
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) < 7:
            raise malformed_output_error(
                operation="describe_window_panes",
                detail=f"rmux list-panes returned malformed describe row: {line!r}",
                result=result,
                ipc_ref=backend._ipc_ref(),
                daemon_evidence=backend.daemon_evidence,
            )
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


def _split_flag(direction: str) -> str:
    normalized = str(direction or "").strip().lower()
    if normalized == "right":
        return "-h"
    if normalized == "bottom":
        return "-v"
    raise ValueError(f"split_pane direction must be right or bottom, got {direction!r}")


def _pane_id(pane: MuxPaneRef) -> str:
    return _require_text(pane.get("pane_id"), "pane_id")


def _session_window_target(session_name: str, window_name: str | None = None) -> str:
    session = _require_text(session_name, "session_name")
    window = str(window_name or "").strip()
    return f"{session}:{window}" if window else session


def _first_stdout_token(stdout: str) -> str:
    return ((stdout.splitlines() or [""])[0]).strip()


def _require_text(value: str | None, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name} is required")
    return text


__all__ = [
    "describe_pane",
    "describe_window_panes",
    "kill_pane",
    "list_panes",
    "move_pane",
    "reflow_window",
    "respawn_pane",
    "select_layout",
    "split_pane",
    "swap_pane",
]
