from __future__ import annotations

from terminal_runtime.mux_backend_contract import MuxCommandError, MuxPaneRef
from terminal_runtime.rmux_backend_runtime.targets import canonical_pane_target


def set_pane_title(backend, pane: MuxPaneRef, title: str) -> None:
    backend._require_capability("set_pane_title", ("select-pane",))
    backend._run_checked(["select-pane", "-t", canonical_pane_target(backend, pane), "-T", title or ""], operation="set_pane_title")


def set_pane_user_option(backend, pane: MuxPaneRef, name: str, value: str) -> None:
    option = _normalize_user_option(name)
    if not option:
        return
    backend._require_capability("set_pane_user_option", ("set-option",))
    backend._run_checked(["set-option", "-p", "-t", canonical_pane_target(backend, pane), option, value or ""], operation="set_pane_user_option")


def set_pane_style(
    backend,
    pane: MuxPaneRef,
    *,
    border_style: str | None = None,
    active_border_style: str | None = None,
) -> None:
    backend._require_capability("set_pane_style", ("set-option", "set-window-option"))
    if border_style:
        backend._run_checked(
            ["set-option", "-p", "-t", canonical_pane_target(backend, pane), "pane-border-style", border_style],
            operation="set_pane_style",
        )
    if active_border_style:
        backend._run_checked(
            ["set-option", "-p", "-t", canonical_pane_target(backend, pane), "pane-active-border-style", active_border_style],
            operation="set_pane_style",
        )


def set_pane_identity(
    backend,
    pane: MuxPaneRef,
    *,
    title: str,
    user_options: dict[str, str],
    border_style: str | None = None,
    active_border_style: str | None = None,
) -> None:
    completed: list[str] = []
    try:
        set_pane_title(backend, pane, title)
        completed.append("title")
        for name, value in user_options.items():
            set_pane_user_option(backend, pane, name, value)
            completed.append(f"user_option:{name}")
        set_pane_style(
            backend,
            pane,
            border_style=border_style,
            active_border_style=active_border_style,
        )
        completed.append("style")
    except MuxCommandError as exc:
        evidence = dict(exc.evidence)
        evidence["completed_identity_steps"] = tuple(completed)
        evidence["failed_identity_step"] = exc.operation
        raise MuxCommandError(
            category=exc.category,
            backend_impl="rmux",
            operation="set_pane_identity",
            detail=exc.detail,
            ipc_ref=exc.ipc_ref,
            command=exc.command,
            evidence=evidence,
        ) from exc


def _normalize_user_option(name: str) -> str:
    text = str(name or "").strip()
    if not text:
        return ""
    return text if text.startswith("@") else f"@{text}"


__all__ = [
    "set_pane_identity",
    "set_pane_style",
    "set_pane_title",
    "set_pane_user_option",
]
