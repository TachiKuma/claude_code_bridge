from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

RUNTIME_MANIFEST_SCHEMA = "ccb.herdr.runtime-manifest.v1"
RUNTIME_BINDING_SCHEMA = "herdr.runtime-binding.v1"


@dataclass(frozen=True)
class HerdrRuntimeManifestService:
    id: str
    command: tuple[str, ...]
    cwd: str
    ready: dict[str, object]

    def __post_init__(self) -> None:
        _require_text(self.id, "service.id")
        _require_text(self.cwd, "service.cwd")
        if not self.command or any(not str(item).strip() for item in self.command):
            raise ValueError("service.command must contain non-empty argv entries")

    def to_record(self) -> dict[str, object]:
        return {
            "id": self.id,
            "command": list(self.command),
            "cwd": self.cwd,
            "ready": dict(self.ready),
        }

    @classmethod
    def from_record(cls, payload: Mapping[str, object]) -> HerdrRuntimeManifestService:
        command = payload.get("command")
        ready = payload.get("ready")
        return cls(
            id=_text(payload.get("id")),
            command=tuple(str(item) for item in command) if isinstance(command, list) else (),
            cwd=_text(payload.get("cwd")),
            ready=dict(ready) if isinstance(ready, Mapping) else {},
        )


@dataclass(frozen=True)
class HerdrRuntimeEnvRef:
    name: str
    source: str

    def __post_init__(self) -> None:
        _require_text(self.name, "env_ref.name")
        _require_text(self.source, "env_ref.source")

    def to_record(self) -> dict[str, object]:
        return {"name": self.name, "source": self.source}

    @classmethod
    def from_record(cls, payload: Mapping[str, object]) -> HerdrRuntimeEnvRef:
        return cls(name=_text(payload.get("name")), source=_text(payload.get("source")))


@dataclass(frozen=True)
class HerdrRuntimeManifestPane:
    slot: str
    agent_name: str
    provider_kind: str
    command: tuple[str, ...]
    cwd: str
    role: str = "agent"
    env_refs: tuple[HerdrRuntimeEnvRef, ...] = ()
    restart: dict[str, object] | None = None

    def __post_init__(self) -> None:
        _require_text(self.slot, "pane.slot")
        _require_text(self.agent_name, "pane.agent_name")
        _require_text(self.provider_kind, "pane.provider_kind")
        _require_text(self.cwd, "pane.cwd")
        if not self.command or any(not str(item).strip() for item in self.command):
            raise ValueError("pane.command must contain non-empty argv entries")

    def to_record(self) -> dict[str, object]:
        record: dict[str, object] = {
            "slot": self.slot,
            "agent_name": self.agent_name,
            "provider_kind": self.provider_kind,
            "command": list(self.command),
            "cwd": self.cwd,
            "role": self.role,
            "env_refs": [ref.to_record() for ref in self.env_refs],
        }
        if self.restart is not None:
            record["restart"] = dict(self.restart)
        return record

    @classmethod
    def from_record(cls, payload: Mapping[str, object]) -> HerdrRuntimeManifestPane:
        _reject_raw_env(payload)
        command = payload.get("command")
        env_refs = payload.get("env_refs")
        restart = payload.get("restart")
        return cls(
            slot=_text(payload.get("slot")),
            agent_name=_text(payload.get("agent_name")),
            provider_kind=_text(payload.get("provider_kind")),
            command=tuple(str(item) for item in command) if isinstance(command, list) else (),
            cwd=_text(payload.get("cwd")),
            role=_text(payload.get("role")) or "agent",
            env_refs=tuple(
                HerdrRuntimeEnvRef.from_record(item)
                for item in env_refs
                if isinstance(item, Mapping)
            )
            if isinstance(env_refs, list)
            else (),
            restart=dict(restart) if isinstance(restart, Mapping) else None,
        )


@dataclass(frozen=True)
class HerdrRuntimeManifestWorkspace:
    name: str
    cwd: str
    panes: tuple[HerdrRuntimeManifestPane, ...]

    def __post_init__(self) -> None:
        _require_text(self.name, "workspace.name")
        _require_text(self.cwd, "workspace.cwd")

    def to_record(self) -> dict[str, object]:
        return {
            "name": self.name,
            "cwd": self.cwd,
            "panes": [pane.to_record() for pane in self.panes],
        }

    @classmethod
    def from_record(cls, payload: Mapping[str, object]) -> HerdrRuntimeManifestWorkspace:
        panes = payload.get("panes")
        return cls(
            name=_text(payload.get("name")),
            cwd=_text(payload.get("cwd")),
            panes=tuple(
                HerdrRuntimeManifestPane.from_record(item)
                for item in panes
                if isinstance(item, Mapping)
            )
            if isinstance(panes, list)
            else (),
        )


@dataclass(frozen=True)
class HerdrRuntimeManifest:
    project_id: str
    project_root: str
    session_name: str
    generation: int
    workspaces: tuple[HerdrRuntimeManifestWorkspace, ...]
    services: tuple[HerdrRuntimeManifestService, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.project_id, "project_id")
        _require_text(self.project_root, "project_root")
        _require_text(self.session_name, "session_name")
        _require_positive_int(self.generation, "generation")

    def to_record(self) -> dict[str, object]:
        return {
            "schema": RUNTIME_MANIFEST_SCHEMA,
            "project_id": self.project_id,
            "project_root": self.project_root,
            "session_name": self.session_name,
            "generation": self.generation,
            "services": [service.to_record() for service in self.services],
            "workspaces": [workspace.to_record() for workspace in self.workspaces],
        }

    @classmethod
    def from_record(cls, payload: Mapping[str, object]) -> HerdrRuntimeManifest:
        if payload.get("schema") != RUNTIME_MANIFEST_SCHEMA:
            raise ValueError(f"manifest schema must be {RUNTIME_MANIFEST_SCHEMA}")
        services = payload.get("services")
        workspaces = payload.get("workspaces")
        return cls(
            project_id=_text(payload.get("project_id")),
            project_root=_text(payload.get("project_root")),
            session_name=_text(payload.get("session_name")),
            generation=int(payload.get("generation", 0)),
            workspaces=tuple(
                HerdrRuntimeManifestWorkspace.from_record(item)
                for item in workspaces
                if isinstance(item, Mapping)
            )
            if isinstance(workspaces, list)
            else (),
            services=tuple(
                HerdrRuntimeManifestService.from_record(item)
                for item in services
                if isinstance(item, Mapping)
            )
            if isinstance(services, list)
            else (),
        )


@dataclass(frozen=True)
class HerdrRuntimeBoundPane:
    slot: str
    pane_id: str
    agent_id: str
    provider_kind: str
    state: str
    state_seq: int

    def __post_init__(self) -> None:
        _require_text(self.slot, "bound_pane.slot")
        _require_text(self.pane_id, "bound_pane.pane_id")
        _require_text(self.agent_id, "bound_pane.agent_id")
        _require_text(self.provider_kind, "bound_pane.provider_kind")
        _require_text(self.state, "bound_pane.state")

    def to_record(self) -> dict[str, object]:
        return {
            "slot": self.slot,
            "pane_id": self.pane_id,
            "agent_id": self.agent_id,
            "provider_kind": self.provider_kind,
            "state": self.state,
            "state_seq": self.state_seq,
        }

    @classmethod
    def from_record(cls, payload: Mapping[str, object]) -> HerdrRuntimeBoundPane:
        return cls(
            slot=_text(payload.get("slot")),
            pane_id=_text(payload.get("pane_id")),
            agent_id=_text(payload.get("agent_id")),
            provider_kind=_text(payload.get("provider_kind")),
            state=_text(payload.get("state")) or "unknown",
            state_seq=int(payload.get("state_seq", 0)),
        )


@dataclass(frozen=True)
class HerdrRuntimeBinding:
    server_id: str
    server_version: str
    api_schema: str
    session_name: str
    workspace_id: str
    runtime_generation: int
    ready: bool
    capabilities: dict[str, object]
    panes: tuple[HerdrRuntimeBoundPane, ...]
    frontend: dict[str, object] | None = None
    project_id: str | None = None

    def __post_init__(self) -> None:
        if self.project_id is not None:
            _require_text(self.project_id, "project_id")
        _require_text(self.server_id, "server_id")
        _require_text(self.server_version, "server_version")
        _require_text(self.api_schema, "api_schema")
        _require_text(self.session_name, "session_name")
        _require_text(self.workspace_id, "workspace_id")
        _require_positive_int(self.runtime_generation, "runtime_generation")

    def to_record(self) -> dict[str, object]:
        record: dict[str, object] = {
            "schema": RUNTIME_BINDING_SCHEMA,
            "project_id": self.project_id,
            "server_id": self.server_id,
            "server_version": self.server_version,
            "api_schema": self.api_schema,
            "session_name": self.session_name,
            "workspace_id": self.workspace_id,
            "runtime_generation": self.runtime_generation,
            "ready": self.ready,
            "capabilities": dict(self.capabilities),
            "panes": [pane.to_record() for pane in self.panes],
        }
        if self.frontend is not None:
            record["frontend"] = _redacted_frontend(self.frontend)
        return record

    def matches_runtime_identity(
        self,
        *,
        project_id: str | None = None,
        session_name: str,
        workspace_id: str,
        pane_id: str,
        slot: str,
        provider_kind: str,
        runtime_generation: int,
    ) -> bool:
        if self.project_id and project_id is not None and self.project_id != str(project_id).strip():
            return False
        if self.session_name != str(session_name).strip():
            return False
        if self.workspace_id != str(workspace_id).strip():
            return False
        if self.runtime_generation != int(runtime_generation):
            return False
        pane_target = str(pane_id).strip()
        slot_target = str(slot).strip()
        provider_target = str(provider_kind).strip()
        return any(
            pane.pane_id == pane_target
            and pane.slot == slot_target
            and pane.provider_kind == provider_target
            for pane in self.panes
        )

    @classmethod
    def from_record(cls, payload: Mapping[str, object]) -> HerdrRuntimeBinding:
        if payload.get("schema") != RUNTIME_BINDING_SCHEMA:
            raise ValueError(f"binding schema must be {RUNTIME_BINDING_SCHEMA}")
        panes = payload.get("panes")
        capabilities = payload.get("capabilities")
        return cls(
            project_id=_optional_text(payload.get("project_id")),
            server_id=_text(payload.get("server_id")),
            server_version=_text(payload.get("server_version")),
            api_schema=_text(payload.get("api_schema")),
            session_name=_text(payload.get("session_name")),
            workspace_id=_text(payload.get("workspace_id")),
            runtime_generation=int(payload.get("runtime_generation", 0)),
            ready=bool(payload.get("ready", False)),
            capabilities=dict(capabilities) if isinstance(capabilities, Mapping) else {},
            panes=tuple(
                HerdrRuntimeBoundPane.from_record(item)
                for item in panes
                if isinstance(item, Mapping)
            )
            if isinstance(panes, list)
            else (),
            frontend=_redacted_frontend(payload.get("frontend")),
        )


@dataclass(frozen=True)
class HerdrRuntimeEvent:
    event_type: str
    event_id: str
    server_id: str
    session_name: str
    workspace_id: str
    pane_id: str
    agent_id: str
    provider_kind: str
    runtime_generation: int
    seq: int
    state: str
    occurred_at: str

    def __post_init__(self) -> None:
        _require_text(self.event_type, "event_type")
        _require_text(self.event_id, "event_id")
        _require_text(self.server_id, "server_id")
        _require_text(self.session_name, "session_name")
        _require_text(self.workspace_id, "workspace_id")
        _require_text(self.pane_id, "pane_id")
        _require_text(self.agent_id, "agent_id")
        _require_text(self.provider_kind, "provider_kind")
        _require_positive_int(self.runtime_generation, "runtime_generation")
        _require_text(self.state, "state")
        _require_text(self.occurred_at, "occurred_at")

    def to_record(self) -> dict[str, object]:
        return {
            "event_type": self.event_type,
            "event_id": self.event_id,
            "server_id": self.server_id,
            "session_name": self.session_name,
            "workspace_id": self.workspace_id,
            "pane_id": self.pane_id,
            "agent_id": self.agent_id,
            "provider_kind": self.provider_kind,
            "runtime_generation": self.runtime_generation,
            "seq": self.seq,
            "state": self.state,
            "occurred_at": self.occurred_at,
        }

    @classmethod
    def from_record(cls, payload: Mapping[str, object]) -> HerdrRuntimeEvent:
        return cls(
            event_type=_text(payload.get("event_type")),
            event_id=_text(payload.get("event_id")),
            server_id=_text(payload.get("server_id")),
            session_name=_text(payload.get("session_name")),
            workspace_id=_text(payload.get("workspace_id")),
            pane_id=_text(payload.get("pane_id")),
            agent_id=_text(payload.get("agent_id")),
            provider_kind=_text(payload.get("provider_kind")),
            runtime_generation=int(payload.get("runtime_generation", 0)),
            seq=int(payload.get("seq", 0)),
            state=_text(payload.get("state")) or "unknown",
            occurred_at=_text(payload.get("occurred_at")),
        )


def _text(value: object) -> str:
    return str(value or "").strip()


def _optional_text(value: object) -> str | None:
    text = _text(value)
    return text or None


def _require_text(value: str, field_name: str) -> None:
    if not _text(value):
        raise ValueError(f"{field_name} must be non-empty")


def _require_positive_int(value: int, field_name: str) -> None:
    if not isinstance(value, int) or value < 1:
        raise ValueError(f"{field_name} must be a positive integer")


def _reject_raw_env(payload: Mapping[str, object]) -> None:
    for key in ("env", "environment", "secrets"):
        if key in payload:
            raise ValueError("manifest panes must use env_refs instead of raw environment values")


def _redacted_frontend(value: object) -> dict[str, object] | None:
    if not isinstance(value, Mapping):
        return None
    allowed = {
        "kind",
        "status",
        "mux_available",
        "pane_id",
        "window_id",
        "workspace",
        "spawn_target",
        "launch_mode",
        "fallback",
        "fallback_reason",
        "reason",
        "probe_status",
        "previous_frontend_probe_status",
        "previous_frontend_probe_reason",
    }
    result: dict[str, object] = {}
    for key in allowed:
        item = value.get(key)
        if item is None:
            continue
        if isinstance(item, bool):
            result[key] = item
        elif isinstance(item, int):
            result[key] = item
        else:
            text = str(item).strip()
            if text:
                result[key] = text
    return result or None


__all__ = [
    "HerdrRuntimeBinding",
    "HerdrRuntimeBoundPane",
    "HerdrRuntimeEnvRef",
    "HerdrRuntimeEvent",
    "HerdrRuntimeManifest",
    "HerdrRuntimeManifestPane",
    "HerdrRuntimeManifestService",
    "HerdrRuntimeManifestWorkspace",
    "RUNTIME_BINDING_SCHEMA",
    "RUNTIME_MANIFEST_SCHEMA",
]
