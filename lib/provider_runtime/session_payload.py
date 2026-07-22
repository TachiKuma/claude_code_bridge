from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, TypedDict


PROTECTED_SHARED_KEYS = frozenset(
    {
        "terminal",
        "backend_family",
        "backend_impl",
        "pane_ref",
        "namespace_ref",
        "compat",
        "pane_id",
        "tmux_session",
        "tmux_socket_name",
        "tmux_socket_path",
    }
)


class MuxPaneSessionRef(TypedDict, total=False):
    backend_impl: str | None
    pane_id: str | None
    session_name: str | None
    window_name: str | None


class MuxNamespaceSessionRef(TypedDict, total=False):
    backend_family: str | None
    backend_impl: str | None
    namespace_id: str | None
    session_name: str | None
    ipc_kind: str | None
    ipc_ref: str | None


class MuxSessionPayload(TypedDict):
    terminal: str
    backend_family: str
    backend_impl: str
    pane_ref: MuxPaneSessionRef
    namespace_ref: MuxNamespaceSessionRef
    compat: dict[str, object]


@dataclass(frozen=True)
class MuxSessionView:
    terminal: str
    backend_family: str | None
    backend_impl: str | None
    pane_ref: dict[str, object]
    namespace_ref: dict[str, object]
    compat: dict[str, object]
    pane_id: str | None
    session_name: str | None
    window_name: str | None
    namespace_id: str | None
    namespace_ipc_kind: str | None
    namespace_ipc_ref: str | None
    tmux_socket_name: str | None
    tmux_socket_path: str | None
    diagnostics: dict[str, object]


def build_mux_session_payload(
    *,
    backend_family: str = "tmux-family",
    backend_impl: str = "tmux",
    pane_id: str,
    session_name: str | None = None,
    window_name: str | None = None,
    namespace_id: str | None = None,
    namespace_ipc_kind: str | None = None,
    namespace_ipc_ref: str | None = None,
    tmux_socket_name: str | None = None,
    tmux_socket_path: str | None = None,
) -> dict[str, object]:
    pane = _clean_text(pane_id)
    if not pane:
        raise ValueError("pane_id is required")
    backend_family_value = _clean_text(backend_family) or "tmux-family"
    backend_impl_value = _clean_text(backend_impl) or "tmux"
    session = _clean_text(session_name)
    window = _clean_text(window_name)
    socket_name = _clean_text(tmux_socket_name)
    socket_path = _clean_path_text(tmux_socket_path)
    ipc_kind = _clean_text(namespace_ipc_kind) or ("unix_socket" if socket_path else ("socket_name" if socket_name else None))
    ipc_ref = _clean_text(namespace_ipc_ref) or socket_path or socket_name
    namespace = _clean_text(namespace_id) or session

    compat = _compact_dict(
        {
            "terminal": "tmux",
            "tmux_session": pane,
            "tmux_socket_name": socket_name,
            "tmux_socket_path": socket_path,
        }
    )
    payload: dict[str, object] = {
        "terminal": "mux",
        "backend_family": backend_family_value,
        "backend_impl": backend_impl_value,
        "pane_ref": _compact_dict(
            {
                "backend_impl": backend_impl_value,
                "pane_id": pane,
                "session_name": session,
                "window_name": window,
            }
        ),
        "namespace_ref": _compact_dict(
            {
                "backend_family": backend_family_value,
                "backend_impl": backend_impl_value,
                "namespace_id": namespace,
                "session_name": session,
                "ipc_kind": ipc_kind,
                "ipc_ref": ipc_ref,
            }
        ),
        "compat": compat,
        "pane_id": pane,
        "tmux_session": pane,
    }
    if socket_name:
        payload["tmux_socket_name"] = socket_name
    if socket_path:
        payload["tmux_socket_path"] = socket_path
    return payload


def merge_provider_payload(
    shared_payload: Mapping[str, object],
    provider_payload: Mapping[str, object] | None,
) -> dict[str, object]:
    payload = dict(shared_payload)
    conflicts: list[dict[str, object]] = []
    for key, value in (provider_payload or {}).items():
        if key not in PROTECTED_SHARED_KEYS:
            payload[key] = value
            continue
        if _jsonish_equal(payload.get(key), value):
            continue
        conflicts.append(
            {
                "key": str(key),
                "provider_value": value,
                "canonical_value": payload.get(key),
            }
        )
    if conflicts:
        diagnostics = dict(payload.get("payload_diagnostics") if isinstance(payload.get("payload_diagnostics"), dict) else {})
        diagnostics["protected_key_conflicts"] = conflicts
        payload["payload_diagnostics"] = diagnostics
    return payload


def mux_session_env(payload_or_view: Mapping[str, object] | MuxSessionView) -> dict[str, str]:
    view = payload_or_view if isinstance(payload_or_view, MuxSessionView) else project_session_payload(payload_or_view)
    env = {
        "CCB_MUX_BACKEND_FAMILY": view.backend_family,
        "CCB_MUX_BACKEND_IMPL": view.backend_impl,
        "CCB_MUX_PANE_ID": view.pane_id,
        "CCB_MUX_NAMESPACE_IPC_KIND": view.namespace_ipc_kind,
        "CCB_MUX_NAMESPACE_IPC_REF": view.namespace_ipc_ref,
    }
    return {key: value for key, value in env.items() if value}


def merge_missing_mux_session_fields(
    target: dict[str, object],
    source: Mapping[str, object] | None,
) -> None:
    view = project_session_payload(source)
    if _should_replace_terminal(target, view):
        target["terminal"] = view.terminal
    _set_missing_text(target, "backend_family", view.backend_family)
    _set_missing_text(target, "backend_impl", view.backend_impl)
    _set_missing_text(target, "pane_id", view.pane_id)
    _set_missing_text(
        target,
        "tmux_session",
        _clean_text((source or {}).get("tmux_session")) if isinstance(source, Mapping) else None,
    )
    if not _clean_text(target.get("tmux_session")):
        _set_missing_text(target, "tmux_session", view.pane_id)
    _set_missing_dict(target, "pane_ref", view.pane_ref)
    _set_missing_dict(target, "namespace_ref", view.namespace_ref)


def update_mux_session_pane_binding(data: dict[str, object], pane_id: str) -> None:
    pane = _clean_text(pane_id)
    if not pane:
        return
    data["pane_id"] = pane
    data["tmux_session"] = pane
    pane_ref = _dict(data.get("pane_ref"))
    pane_ref["pane_id"] = pane
    backend_impl = _clean_text(data.get("backend_impl")) or _clean_text(pane_ref.get("backend_impl"))
    if backend_impl:
        pane_ref["backend_impl"] = backend_impl
    data["pane_ref"] = pane_ref
    compat = _dict(data.get("compat"))
    compat["tmux_session"] = pane
    data["compat"] = compat


def session_uses_tmux_compatible_pane(data: Mapping[str, object] | None) -> bool:
    view = project_session_payload(data)
    if view.terminal == "tmux":
        return True
    return (view.backend_family or "").strip().lower() == "tmux-family"


def project_session_payload(data: Mapping[str, object] | None) -> MuxSessionView:
    payload = data if isinstance(data, Mapping) else {}
    pane_ref = _dict(payload.get("pane_ref"))
    namespace_ref = _dict(payload.get("namespace_ref"))
    compat = _dict(payload.get("compat"))
    diagnostics: dict[str, object] = {}

    terminal = _clean_text(payload.get("terminal")) or "tmux"
    backend_family = _clean_text(payload.get("backend_family")) or _clean_text(namespace_ref.get("backend_family"))
    backend_impl = _clean_text(payload.get("backend_impl")) or _clean_text(pane_ref.get("backend_impl")) or _clean_text(namespace_ref.get("backend_impl"))
    if terminal == "tmux" and not backend_impl:
        backend_impl = "tmux"
    if backend_impl and not backend_family:
        backend_family = "tmux-family"

    pane_id = _clean_text(pane_ref.get("pane_id")) or _clean_text(payload.get("pane_id")) or _clean_text(compat.get("tmux_session")) or _clean_text(payload.get("tmux_session"))
    session_name = _clean_text(pane_ref.get("session_name")) or _clean_text(namespace_ref.get("session_name"))
    window_name = _clean_text(pane_ref.get("window_name"))
    namespace_id = _clean_text(namespace_ref.get("namespace_id")) or session_name
    ipc_kind = _clean_text(namespace_ref.get("ipc_kind"))
    ipc_ref = _clean_text(namespace_ref.get("ipc_ref"))
    tmux_socket_name = _clean_text(compat.get("tmux_socket_name")) or _clean_text(payload.get("tmux_socket_name"))
    tmux_socket_path = _clean_path_text(compat.get("tmux_socket_path")) or _clean_path_text(payload.get("tmux_socket_path"))

    if not ipc_kind and (tmux_socket_path or tmux_socket_name):
        ipc_kind = "unix_socket" if tmux_socket_path else "socket_name"
    if not ipc_ref:
        ipc_ref = tmux_socket_path or tmux_socket_name

    _record_alias_mismatch(diagnostics, "pane_id", pane_id, payload.get("pane_id"))
    _record_alias_mismatch(diagnostics, "tmux_session", pane_id, payload.get("tmux_session"))
    _record_alias_mismatch(diagnostics, "tmux_socket_name", tmux_socket_name, payload.get("tmux_socket_name"))
    _record_alias_mismatch(diagnostics, "tmux_socket_path", tmux_socket_path, payload.get("tmux_socket_path"))

    if terminal == "tmux":
        terminal = "tmux"
    elif terminal != "mux":
        diagnostics["unknown_terminal"] = terminal

    return MuxSessionView(
        terminal=terminal,
        backend_family=backend_family,
        backend_impl=backend_impl,
        pane_ref=pane_ref,
        namespace_ref=namespace_ref,
        compat=compat,
        pane_id=pane_id,
        session_name=session_name,
        window_name=window_name,
        namespace_id=namespace_id,
        namespace_ipc_kind=ipc_kind,
        namespace_ipc_ref=ipc_ref,
        tmux_socket_name=tmux_socket_name,
        tmux_socket_path=tmux_socket_path,
        diagnostics=diagnostics,
    )


def _should_replace_terminal(target: Mapping[str, object], view: MuxSessionView) -> bool:
    current = _clean_text(target.get("terminal"))
    if not current:
        return True
    return current == "tmux" and view.terminal == "mux" and not _clean_text(target.get("backend_impl"))


def _set_missing_text(target: dict[str, object], key: str, value: object) -> None:
    text = _clean_text(value)
    if text and not _clean_text(target.get(key)):
        target[key] = text


def _set_missing_dict(target: dict[str, object], key: str, value: Mapping[str, object]) -> None:
    compacted = _compact_dict(value)
    if not compacted:
        return
    current = _dict(target.get(key))
    if not current:
        target[key] = compacted
        return
    for field, field_value in compacted.items():
        if not _clean_text(current.get(field)):
            current[field] = field_value
    target[key] = current


def _record_alias_mismatch(diagnostics: dict[str, object], key: str, canonical: object, alias: object) -> None:
    canonical_text = _clean_path_text(canonical) if key.endswith("_path") else _clean_text(canonical)
    alias_text = _clean_path_text(alias) if key.endswith("_path") else _clean_text(alias)
    if not canonical_text or not alias_text or canonical_text == alias_text:
        return
    mismatches = list(diagnostics.get("alias_mismatches") or [])
    mismatches.append({"key": key, "canonical_value": canonical_text, "alias_value": alias_text})
    diagnostics["alias_mismatches"] = mismatches


def _compact_dict(payload: Mapping[str, object]) -> dict[str, object]:
    return {key: value for key, value in payload.items() if value is not None and value != ""}


def _dict(value: object) -> dict[str, object]:
    return dict(value) if isinstance(value, Mapping) else {}


def _clean_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _clean_path_text(value: object) -> str | None:
    text = _clean_text(value)
    if not text:
        return None
    if not text.startswith("~"):
        return text
    try:
        return str(Path(text).expanduser())
    except Exception:
        return text


def _jsonish_equal(left: Any, right: Any) -> bool:
    return left == right


__all__ = [
    "MuxSessionPayload",
    "MuxSessionView",
    "PROTECTED_SHARED_KEYS",
    "build_mux_session_payload",
    "merge_missing_mux_session_fields",
    "merge_provider_payload",
    "mux_session_env",
    "project_session_payload",
    "session_uses_tmux_compatible_pane",
    "update_mux_session_pane_binding",
]
