from __future__ import annotations

from terminal_runtime.mux_backend_contract import MuxPaneRef


def canonical_pane_target(backend, pane: MuxPaneRef) -> str:
    canonical_pane = dict(pane)
    canonical_pane["pane_id"] = canonical_pane_id(backend, pane)
    return pane_target(canonical_pane)


def canonical_pane_id(backend, pane: MuxPaneRef) -> str:
    pane_id = _require_text(pane.get("pane_id"), "pane_id")
    if not (pane_id.startswith("%") and pane_id[1:].isdigit()):
        return pane_id
    session = str(pane.get("session_name") or "").strip()
    window = str(pane.get("window_name") or "").strip()
    if not session:
        return _pane_id_from_global_index(backend, pane_id=pane_id) or pane_id
    indexed = (
        _pane_id_from_window_index(backend, session=session, window=window, pane_id=pane_id)
        if window
        else _pane_id_from_session_index(backend, session=session, pane_id=pane_id)
    )
    if indexed:
        return indexed
    if not window:
        return pane_id
    displayed = _pane_id_from_display_message(backend, session=session, window=window, pane_id=pane_id)
    return displayed or pane_id


def pane_target(pane: MuxPaneRef) -> str:
    pane_id = _require_text(pane.get("pane_id"), "pane_id")
    if pane_id.startswith("%") and pane_id[1:].isdigit():
        session = str(pane.get("session_name") or "").strip()
        window = str(pane.get("window_name") or "").strip()
        if session and window:
            return f"{session}:{window}.{pane_id}"
    return pane_id


def _pane_id_from_window_index(backend, *, session: str, window: str, pane_id: str) -> str | None:
    try:
        result = backend._run_checked(
            [
                "list-panes",
                "-t",
                f"{session}:{window}",
                "-F",
                "#{pane_id}\t#{pane_index}",
            ],
            operation="canonicalize_pane",
        )
    except Exception:
        return None
    pane_index = pane_id[1:]
    for line in str(getattr(result, "stdout", "") or "").splitlines():
        parts = [part.strip() for part in line.split("\t")]
        observed_id = parts[0] if parts else ""
        observed_index = parts[1] if len(parts) > 1 else ""
        if observed_id == pane_id:
            return observed_id
        if pane_index.isdigit() and observed_index == pane_index and observed_id.startswith("%"):
            return observed_id
    return None


def _pane_id_from_global_index(backend, *, pane_id: str) -> str | None:
    try:
        result = backend._run_checked(
            [
                "list-panes",
                "-a",
                "-F",
                "#{pane_id}\t#{pane_index}",
            ],
            operation="canonicalize_pane",
        )
    except Exception:
        return None
    pane_index = pane_id[1:]
    matches: list[str] = []
    for line in str(getattr(result, "stdout", "") or "").splitlines():
        parts = [part.strip() for part in line.split("\t")]
        observed_id = parts[0] if parts else ""
        observed_index = parts[1] if len(parts) > 1 else ""
        if observed_id == pane_id:
            return observed_id
        if pane_index.isdigit() and observed_index == pane_index and observed_id.startswith("%"):
            matches.append(observed_id)
    return matches[0] if len(matches) == 1 else None


def _pane_id_from_session_index(backend, *, session: str, pane_id: str) -> str | None:
    try:
        result = backend._run_checked(
            [
                "list-panes",
                "-a",
                "-F",
                "#{session_name}\t#{pane_id}\t#{pane_index}",
            ],
            operation="canonicalize_pane",
        )
    except Exception:
        return None
    pane_index = pane_id[1:]
    for line in str(getattr(result, "stdout", "") or "").splitlines():
        parts = [part.strip() for part in line.split("\t")]
        observed_session = parts[0] if parts else ""
        observed_id = parts[1] if len(parts) > 1 else ""
        observed_index = parts[2] if len(parts) > 2 else ""
        if observed_session != session:
            continue
        if observed_id == pane_id:
            return observed_id
        if pane_index.isdigit() and observed_index == pane_index and observed_id.startswith("%"):
            return observed_id
    return None


def _pane_id_from_display_message(backend, *, session: str, window: str, pane_id: str) -> str | None:
    try:
        result = backend._run_checked(
            [
                "display-message",
                "-p",
                "-t",
                f"{session}:{window}.{pane_id}",
                "#{pane_id}",
            ],
            operation="canonicalize_pane",
        )
    except Exception:
        return None
    resolved = ((str(getattr(result, "stdout", "") or "").splitlines() or [""])[0]).strip()
    return resolved if resolved.startswith("%") else None


def _require_text(value: str | None, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name} is required")
    return text


__all__ = ["canonical_pane_id", "canonical_pane_target", "pane_target"]
