from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from terminal_runtime.mux_backend_contract import (
    CapabilityStatus,
    MuxCapabilities,
    MuxCommandError,
)

_SUMMARY_PATH = Path(".codestable/features/2026-07-19-rmux-route-approval/rmux-route-decision-summary.yaml")
_SUPPORTED = {"supported", "workaround"}


class RmuxCapabilityGate:
    def __init__(
        self,
        *,
        command_status: Mapping[str, str] | None = None,
        semantic_status: Mapping[str, str] | None = None,
        blocking_gaps: list[str] | tuple[str, ...] | None = None,
        source_ref: str | None = None,
    ) -> None:
        self.source_ref = str(source_ref or "").strip() or None
        self.command_status = {
            str(key): _capability_status(value)
            for key, value in dict(command_status or {}).items()
        }
        self.semantic_status = {
            str(key): _capability_status(value)
            for key, value in dict(semantic_status or {}).items()
        }
        self.blocking_gaps = [str(item) for item in (blocking_gaps or ())]

    def capabilities(self) -> MuxCapabilities:
        return {
            "backend_impl": "rmux",
            "command_status": dict(self.command_status),
            "semantic_status": dict(self.semantic_status),
            "blocking_gaps": list(self.blocking_gaps),
        }

    def require(
        self,
        operation: str,
        commands: tuple[str, ...],
        *,
        backend_impl: str,
        ipc_ref: str | None,
        daemon_evidence: dict[str, object] | None = None,
    ) -> None:
        missing = [
            command
            for command in commands
            if self.command_status.get(command, "unsupported") not in _SUPPORTED
        ]
        if not missing:
            return
        evidence: dict[str, object] = {
            "required_commands": tuple(commands),
            "unsupported_commands": tuple(missing),
            "command_status": {
                command: self.command_status.get(command, "unsupported")
                for command in missing
            },
            "capability_report_ref": self.source_ref,
        }
        if daemon_evidence:
            evidence["daemon_evidence"] = dict(daemon_evidence)
        raise MuxCommandError(
            category="unsupported",
            backend_impl="rmux",  # type: ignore[arg-type]
            operation=operation,
            detail=f"rmux capability unsupported for {operation}: {', '.join(missing)}",
            ipc_ref=ipc_ref,
            evidence=evidence,
        )


def default_rmux_capability_gate(project_root: str | Path | None = None) -> RmuxCapabilityGate:
    root = _repo_root(project_root)
    summary = root / _SUMMARY_PATH
    summary_data = _load_yaml_mapping(summary)
    report_ref = str(summary_data.get("capability_report") or "").strip()
    if not _summary_approved(summary_data) or not report_ref:
        return RmuxCapabilityGate(source_ref=None)
    report_path = root / report_ref
    report = _load_json_mapping(report_path)
    commands = _status_mapping(report.get("commands"))
    semantics = _status_mapping(report.get("semantics"))
    _apply_semantic_command_projection(commands, semantics)
    blocking_gaps = report.get("blocking_gaps")
    return RmuxCapabilityGate(
        command_status=commands,
        semantic_status=semantics,
        blocking_gaps=blocking_gaps if isinstance(blocking_gaps, list) else (),
        source_ref=report_ref,
    )


def _status_mapping(value: object) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, str] = {}
    for key, raw in value.items():
        if not isinstance(raw, dict):
            continue
        result[str(key)] = str(raw.get("status") or "unsupported")
    return result


def _apply_semantic_command_projection(commands: dict[str, str], semantics: dict[str, str]) -> None:
    projections = {
        "select-pane": "user_options_title",
        "kill-pane": "pane_death",
    }
    for command, semantic in projections.items():
        if command in commands:
            continue
        if semantics.get(semantic) == "supported":
            commands[command] = "workaround"


def _summary_approved(data: dict[str, object]) -> bool:
    facts = data.get("report_facts")
    handoff = data.get("parent_handoff")
    return (
        str(data.get("decision_status") or data.get("status") or "").strip().lower() == "approved"
        and isinstance(handoff, dict)
        and bool(handoff.get("route_approved"))
        and isinstance(facts, dict)
        and int(facts.get("blocking_gaps_count") or 0) == 0
    )


def _load_json_mapping(path: Path) -> dict[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError:
        return {}
    return data if isinstance(data, dict) else {}


def _load_yaml_mapping(path: Path) -> dict[str, object]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    try:
        import yaml  # type: ignore
    except ImportError:
        return _parse_simple_yaml(text)
    data = yaml.safe_load(text)
    return data if isinstance(data, dict) else {}


def _parse_simple_yaml(text: str) -> dict[str, object]:
    root: dict[str, object] = {}
    stack: list[tuple[int, dict[str, object]]] = [(-1, root)]
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith(("#", "- ")):
            continue
        if ":" not in raw_line:
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        key, _, raw_value = raw_line.strip().partition(":")
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        value = raw_value.strip().strip("\"'")
        if value:
            parent[key] = _parse_scalar(value)
        else:
            child: dict[str, object] = {}
            parent[key] = child
            stack.append((indent, child))
    return root


def _parse_scalar(value: str) -> object:
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    try:
        return int(value)
    except ValueError:
        return value


def _repo_root(project_root: str | Path | None = None) -> Path:
    current = Path(project_root).resolve() if project_root is not None else Path.cwd()
    for path in (current, *current.parents):
        if (path / ".git").exists() or (path / ".codestable").exists():
            return path
    return current


def _capability_status(value: object) -> CapabilityStatus:
    text = str(value or "unsupported").strip()
    if text in {"supported", "partial", "unsupported", "workaround"}:
        return text  # type: ignore[return-value]
    return "unsupported"


__all__ = ["RmuxCapabilityGate", "default_rmux_capability_gate"]
