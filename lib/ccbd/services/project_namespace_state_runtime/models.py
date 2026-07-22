from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

from ccbd.models import SCHEMA_VERSION
from terminal_runtime.rmux_daemon_contract import backend_daemon_diagnostics

from .common import (
    NAMESPACE_EVENT_RECORD_TYPE,
    NAMESPACE_STATE_RECORD_TYPE,
    clean_text,
    require_record_type,
    require_schema_version,
)

NAMESPACE_BACKEND_FAMILY = 'tmux-family'


@dataclass(frozen=True)
class ProjectNamespaceState:
    project_id: str
    namespace_epoch: int
    tmux_socket_path: str
    tmux_session_name: str
    backend_impl: str = 'tmux'
    namespace_backend_family: str | None = None
    namespace_id: str | None = None
    namespace_session_name: str | None = None
    namespace_ipc_kind: str | None = None
    namespace_ipc_ref: str | None = None
    layout_version: int = 1
    layout_signature: str | None = None
    control_window_name: str | None = None
    control_window_id: str | None = None
    workspace_window_name: str | None = None
    workspace_window_id: str | None = None
    workspace_epoch: int = 1
    ui_attachable: bool = True
    last_started_at: str | None = None
    last_destroyed_at: str | None = None
    last_destroy_reason: str | None = None
    backend_daemon_evidence: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        backend_impl = clean_text(self.backend_impl) or 'tmux'
        namespace_backend_family = NAMESPACE_BACKEND_FAMILY
        require_non_empty_text(self.project_id, field_name='project_id')
        require_positive_int(self.namespace_epoch, field_name='namespace_epoch')
        require_non_empty_text(self.tmux_socket_path, field_name='tmux_socket_path')
        require_non_empty_text(self.tmux_session_name, field_name='tmux_session_name')
        require_non_empty_text(backend_impl, field_name='backend_impl')
        require_positive_int(self.layout_version, field_name='layout_version')
        if self.layout_signature is not None:
            require_non_empty_text(self.layout_signature, field_name='layout_signature')
        if self.control_window_name is not None:
            require_non_empty_text(self.control_window_name, field_name='control_window_name')
        if self.control_window_id is not None:
            require_non_empty_text(self.control_window_id, field_name='control_window_id')
        if self.workspace_window_name is not None:
            require_non_empty_text(self.workspace_window_name, field_name='workspace_window_name')
        if self.workspace_window_id is not None:
            require_non_empty_text(self.workspace_window_id, field_name='workspace_window_id')
        require_positive_int(self.workspace_epoch, field_name='workspace_epoch')
        namespace_id = str(self.project_id).strip()
        namespace_session_name = clean_text(self.namespace_session_name) or self.tmux_session_name
        namespace_ipc_kind = clean_text(self.namespace_ipc_kind)
        if not namespace_ipc_kind:
            namespace_ipc_kind = 'named_pipe' if backend_impl in {'rmux', 'psmux'} else 'unix_socket'
        namespace_ipc_ref = clean_text(self.namespace_ipc_ref)
        if not namespace_ipc_ref:
            namespace_ipc_ref = namespace_id if namespace_ipc_kind == 'named_pipe' else self.tmux_socket_path
        object.__setattr__(self, 'backend_impl', backend_impl)
        object.__setattr__(self, 'namespace_backend_family', namespace_backend_family)
        object.__setattr__(self, 'namespace_id', namespace_id)
        object.__setattr__(self, 'namespace_session_name', namespace_session_name)
        object.__setattr__(self, 'namespace_ipc_kind', namespace_ipc_kind)
        object.__setattr__(self, 'namespace_ipc_ref', namespace_ipc_ref)

    def with_started(self, *, occurred_at: str, ui_attachable: bool = True) -> ProjectNamespaceState:
        return replace(
            self,
            ui_attachable=bool(ui_attachable),
            last_started_at=str(occurred_at),
        )

    def with_destroyed(self, *, occurred_at: str, reason: str) -> ProjectNamespaceState:
        return replace(
            self,
            ui_attachable=False,
            last_destroyed_at=str(occurred_at),
            last_destroy_reason=str(reason or '').strip() or 'destroyed',
        )

    def to_record(self) -> dict[str, Any]:
        return {
            'schema_version': SCHEMA_VERSION,
            'record_type': NAMESPACE_STATE_RECORD_TYPE,
            'project_id': self.project_id,
            'namespace_epoch': self.namespace_epoch,
            'tmux_socket_path': self.tmux_socket_path,
            'tmux_session_name': self.tmux_session_name,
            'backend_impl': self.backend_impl,
            'namespace_backend_family': self.namespace_backend_family,
            'namespace_id': self.namespace_id,
            'namespace_session_name': self.namespace_session_name,
            'namespace_ipc_kind': self.namespace_ipc_kind,
            'namespace_ipc_ref': self.namespace_ipc_ref,
            'layout_version': self.layout_version,
            'layout_signature': self.layout_signature,
            'control_window_name': self.control_window_name,
            'control_window_id': self.control_window_id,
            'workspace_window_name': self.workspace_window_name,
            'workspace_window_id': self.workspace_window_id,
            'workspace_epoch': self.workspace_epoch,
            'ui_attachable': self.ui_attachable,
            'last_started_at': self.last_started_at,
            'last_destroyed_at': self.last_destroyed_at,
            'last_destroy_reason': self.last_destroy_reason,
            'backend_daemon_evidence': dict(self.backend_daemon_evidence or {}),
        }

    @classmethod
    def from_record(cls, payload: dict[str, Any]) -> ProjectNamespaceState:
        require_schema_version(payload)
        require_record_type(payload, record_type=NAMESPACE_STATE_RECORD_TYPE)
        return cls(
            project_id=str(payload['project_id']),
            namespace_epoch=int(payload['namespace_epoch']),
            tmux_socket_path=str(payload['tmux_socket_path']),
            tmux_session_name=str(payload['tmux_session_name']),
            backend_impl=clean_text(payload.get('backend_impl')) or 'tmux',
            namespace_backend_family=clean_text(payload.get('namespace_backend_family')) or NAMESPACE_BACKEND_FAMILY,
            namespace_id=clean_text(payload.get('namespace_id')),
            namespace_session_name=clean_text(payload.get('namespace_session_name')),
            namespace_ipc_kind=clean_text(payload.get('namespace_ipc_kind')),
            namespace_ipc_ref=clean_text(payload.get('namespace_ipc_ref')),
            layout_version=int(payload.get('layout_version', 1)),
            layout_signature=clean_text(payload.get('layout_signature')),
            control_window_name=clean_text(payload.get('control_window_name')),
            control_window_id=clean_text(payload.get('control_window_id')),
            workspace_window_name=clean_text(payload.get('workspace_window_name')),
            workspace_window_id=clean_text(payload.get('workspace_window_id')),
            workspace_epoch=int(payload.get('workspace_epoch', 1)),
            ui_attachable=bool(payload.get('ui_attachable', True)),
            last_started_at=clean_text(payload.get('last_started_at')),
            last_destroyed_at=clean_text(payload.get('last_destroyed_at')),
            last_destroy_reason=clean_text(payload.get('last_destroy_reason')),
            backend_daemon_evidence=record_backend_daemon_evidence(payload),
        )

    def summary_fields(self) -> dict[str, object]:
        return {
            'namespace_epoch': self.namespace_epoch,
            'namespace_backend_family': self.resolved_namespace_backend_family(),
            'namespace_backend_impl': self.backend_impl,
            'namespace_id': self.resolved_namespace_id(),
            'namespace_session_name': self.resolved_namespace_session_name(),
            'namespace_ipc_kind': self.resolved_namespace_ipc_kind(),
            'namespace_ipc_ref': self.resolved_namespace_ipc_ref(),
            'namespace_tmux_socket_path': self.tmux_socket_path,
            'namespace_tmux_session_name': self.tmux_session_name,
            'namespace_layout_version': self.layout_version,
            'namespace_control_window_name': self.control_window_name,
            'namespace_control_window_id': self.control_window_id,
            'namespace_workspace_window_name': self.workspace_window_name,
            'namespace_workspace_window_id': self.workspace_window_id,
            'namespace_workspace_epoch': self.workspace_epoch,
            'namespace_ui_attachable': self.ui_attachable,
            'namespace_last_started_at': self.last_started_at,
            'namespace_last_destroyed_at': self.last_destroyed_at,
            'namespace_last_destroy_reason': self.last_destroy_reason,
            **backend_daemon_diagnostics(self.backend_daemon_evidence),
        }

    def resolved_namespace_id(self) -> str:
        return str(self.namespace_id or self.project_id).strip()

    def resolved_namespace_backend_family(self) -> str:
        return NAMESPACE_BACKEND_FAMILY

    def resolved_namespace_session_name(self) -> str:
        return str(self.namespace_session_name or self.tmux_session_name).strip()

    def resolved_namespace_ipc_kind(self) -> str:
        kind = str(self.namespace_ipc_kind or '').strip()
        if kind:
            return kind
        return 'named_pipe' if self.backend_impl in {'rmux', 'psmux'} else 'unix_socket'

    def resolved_namespace_ipc_ref(self) -> str:
        ref = str(self.namespace_ipc_ref or '').strip()
        if ref:
            return ref
        if self.resolved_namespace_ipc_kind() == 'named_pipe':
            return self.resolved_namespace_id()
        return self.tmux_socket_path


@dataclass(frozen=True)
class ProjectNamespaceEvent:
    event_kind: str
    project_id: str
    occurred_at: str
    namespace_epoch: int | None = None
    namespace_backend_family: str | None = None
    backend_impl: str = 'tmux'
    namespace_id: str | None = None
    namespace_session_name: str | None = None
    namespace_ipc_kind: str | None = None
    namespace_ipc_ref: str | None = None
    tmux_socket_path: str | None = None
    tmux_session_name: str | None = None
    details: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        backend_impl = clean_text(self.backend_impl) or 'tmux'
        namespace_backend_family = NAMESPACE_BACKEND_FAMILY
        require_non_empty_text(self.event_kind, field_name='event_kind')
        require_non_empty_text(self.project_id, field_name='project_id')
        require_non_empty_text(self.occurred_at, field_name='occurred_at')
        if self.namespace_epoch is not None:
            require_positive_int(self.namespace_epoch, field_name='namespace_epoch')
        namespace_id = str(self.project_id).strip()
        namespace_session_name = clean_text(self.namespace_session_name) or clean_text(self.tmux_session_name)
        namespace_ipc_kind = clean_text(self.namespace_ipc_kind)
        if not namespace_ipc_kind:
            namespace_ipc_kind = 'named_pipe' if backend_impl in {'rmux', 'psmux'} else 'unix_socket'
        namespace_ipc_ref = clean_text(self.namespace_ipc_ref)
        if not namespace_ipc_ref:
            namespace_ipc_ref = namespace_id if namespace_ipc_kind == 'named_pipe' else clean_text(self.tmux_socket_path)
        object.__setattr__(self, 'backend_impl', backend_impl)
        object.__setattr__(self, 'namespace_backend_family', namespace_backend_family)
        object.__setattr__(self, 'namespace_id', namespace_id)
        object.__setattr__(self, 'namespace_session_name', namespace_session_name)
        object.__setattr__(self, 'namespace_ipc_kind', namespace_ipc_kind)
        object.__setattr__(self, 'namespace_ipc_ref', namespace_ipc_ref)

    def to_record(self) -> dict[str, Any]:
        return {
            'schema_version': SCHEMA_VERSION,
            'record_type': NAMESPACE_EVENT_RECORD_TYPE,
            'event_kind': self.event_kind,
            'project_id': self.project_id,
            'occurred_at': self.occurred_at,
            'namespace_epoch': self.namespace_epoch,
            'namespace_backend_family': self.namespace_backend_family,
            'backend_impl': self.backend_impl,
            'namespace_id': self.namespace_id,
            'namespace_session_name': self.namespace_session_name,
            'namespace_ipc_kind': self.namespace_ipc_kind,
            'namespace_ipc_ref': self.namespace_ipc_ref,
            'tmux_socket_path': self.tmux_socket_path,
            'tmux_session_name': self.tmux_session_name,
            'details': dict(self.details or {}),
        }

    @classmethod
    def from_record(cls, payload: dict[str, Any]) -> ProjectNamespaceEvent:
        require_schema_version(payload)
        require_record_type(payload, record_type=NAMESPACE_EVENT_RECORD_TYPE)
        details = record_details(payload)
        epoch = payload.get('namespace_epoch')
        return cls(
            event_kind=str(payload['event_kind']),
            project_id=str(payload['project_id']),
            occurred_at=str(payload['occurred_at']),
            namespace_epoch=int(epoch) if epoch is not None else None,
            namespace_backend_family=clean_text(payload.get('namespace_backend_family')) or NAMESPACE_BACKEND_FAMILY,
            backend_impl=clean_text(payload.get('backend_impl')) or 'tmux',
            namespace_id=clean_text(payload.get('namespace_id')),
            namespace_session_name=clean_text(payload.get('namespace_session_name')),
            namespace_ipc_kind=clean_text(payload.get('namespace_ipc_kind')),
            namespace_ipc_ref=clean_text(payload.get('namespace_ipc_ref')),
            tmux_socket_path=clean_text(payload.get('tmux_socket_path')),
            tmux_session_name=clean_text(payload.get('tmux_session_name')),
            details=details,
        )

    def summary_fields(self) -> dict[str, object]:
        return {
            'namespace_backend_family': self.namespace_backend_family or NAMESPACE_BACKEND_FAMILY,
            'namespace_backend_impl': self.backend_impl,
            'namespace_id': self.namespace_id,
            'namespace_session_name': self.namespace_session_name,
            'namespace_ipc_kind': self.namespace_ipc_kind,
            'namespace_ipc_ref': self.namespace_ipc_ref,
            'namespace_last_event_kind': self.event_kind,
            'namespace_last_event_at': self.occurred_at,
            'namespace_last_event_epoch': self.namespace_epoch,
            'namespace_last_event_socket_path': self.tmux_socket_path,
            'namespace_last_event_session_name': self.tmux_session_name,
        }


def require_non_empty_text(value: object, *, field_name: str) -> None:
    if not str(value or '').strip():
        raise ValueError(f'{field_name} cannot be empty')


def require_positive_int(value: int, *, field_name: str) -> None:
    if int(value) <= 0:
        raise ValueError(f'{field_name} must be positive')


def record_details(payload: dict[str, Any]) -> dict[str, object]:
    details = payload.get('details') or {}
    if not isinstance(details, dict):
        raise ValueError('details must be an object')
    return dict(details)


def record_backend_daemon_evidence(payload: dict[str, Any]) -> dict[str, object]:
    evidence = payload.get('backend_daemon_evidence') or {}
    if not isinstance(evidence, dict):
        raise ValueError('backend_daemon_evidence must be an object')
    return dict(evidence)


__all__ = ['ProjectNamespaceEvent', 'ProjectNamespaceState']
