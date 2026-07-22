from __future__ import annotations

from typing import Literal, Mapping, TypedDict


RmuxDaemonScope = Literal['shared', 'project']
RmuxDaemonEndpointKind = Literal['named_pipe', 'tcp_loopback', 'local_socket', 'unknown']
RmuxDaemonDiscoverySource = Literal['namespace_state', 'backend_probe', 'start_result', 'health_probe', 'cleanup']
RmuxDaemonHealth = Literal['healthy', 'starting', 'missing', 'unreachable', 'crashed', 'stale', 'foreign', 'unknown']
RmuxDaemonCapabilityStatus = Literal['supported', 'partial', 'unsupported', 'unknown']
RmuxCleanupScope = Literal['none', 'namespace', 'project', 'daemon']
RmuxDaemonAction = Literal['leave_running', 'shutdown']
RmuxCleanupStep = Literal['provider_job_evidence', 'namespace_session', 'daemon_cleanup', 'diagnostics']
RmuxCleanupStatus = Literal['planned', 'completed', 'partial', 'failed', 'skipped']


class RmuxDaemonRef(TypedDict):
    backend_impl: Literal['rmux']
    daemon_id: str
    scope: RmuxDaemonScope
    endpoint_kind: RmuxDaemonEndpointKind
    endpoint_ref: str | None
    version: str | None


class RmuxDaemonEvidence(TypedDict):
    daemon_ref: RmuxDaemonRef
    discovery_source: RmuxDaemonDiscoverySource
    health: RmuxDaemonHealth
    project_id: str | None
    namespace_id: str | None
    daemon_process_evidence: dict[str, object] | None
    capability_status: RmuxDaemonCapabilityStatus
    crash_reason: str | None
    cleanup_scope: RmuxCleanupScope
    diagnostics: dict[str, object]


class RmuxCleanupPlan(TypedDict):
    cleanup_scope: Literal['namespace', 'project', 'daemon']
    targets: list[dict[str, object]]
    daemon_action: RmuxDaemonAction
    force_daemon: bool
    force_reason: str | None
    ordered_steps: list[RmuxCleanupStep]
    status: RmuxCleanupStatus
    diagnostics: dict[str, object]


_DAEMON_SCOPES = {'shared', 'project'}
_ENDPOINT_KINDS = {'named_pipe', 'tcp_loopback', 'local_socket', 'unknown'}
_DISCOVERY_SOURCES = {'namespace_state', 'backend_probe', 'start_result', 'health_probe', 'cleanup'}
_HEALTH_VALUES = {'healthy', 'starting', 'missing', 'unreachable', 'crashed', 'stale', 'foreign', 'unknown'}
_CAPABILITY_VALUES = {'supported', 'partial', 'unsupported', 'unknown'}
_CLEANUP_SCOPES = {'none', 'namespace', 'project', 'daemon'}


def build_rmux_daemon_ref(
    *,
    daemon_id: object,
    scope: object = 'shared',
    endpoint_kind: object = 'unknown',
    endpoint_ref: object = None,
    version: object = None,
) -> RmuxDaemonRef:
    daemon = _clean_text(daemon_id) or 'unknown'
    return {
        'backend_impl': 'rmux',
        'daemon_id': daemon,
        'scope': _literal(scope, allowed=_DAEMON_SCOPES, default='shared'),
        'endpoint_kind': _literal(endpoint_kind, allowed=_ENDPOINT_KINDS, default='unknown'),
        'endpoint_ref': _clean_text(endpoint_ref),
        'version': _clean_text(version),
    }


def build_rmux_daemon_evidence(
    *,
    daemon_ref: Mapping[str, object],
    discovery_source: object,
    health: object = 'unknown',
    project_id: object = None,
    namespace_id: object = None,
    daemon_process_evidence: Mapping[str, object] | None = None,
    capability_status: object = 'unknown',
    crash_reason: object = None,
    cleanup_scope: object = 'none',
    diagnostics: Mapping[str, object] | None = None,
) -> RmuxDaemonEvidence:
    ref = _daemon_ref_from_mapping(daemon_ref)
    return {
        'daemon_ref': ref,
        'discovery_source': _literal(discovery_source, allowed=_DISCOVERY_SOURCES, default='backend_probe'),
        'health': _literal(health, allowed=_HEALTH_VALUES, default='unknown'),
        'project_id': _clean_text(project_id),
        'namespace_id': _clean_text(namespace_id),
        'daemon_process_evidence': _daemon_process_evidence(daemon_process_evidence),
        'capability_status': _literal(capability_status, allowed=_CAPABILITY_VALUES, default='unknown'),
        'crash_reason': _clean_text(crash_reason),
        'cleanup_scope': _literal(cleanup_scope, allowed=_CLEANUP_SCOPES, default='none'),
        'diagnostics': dict(diagnostics or {}),
    }


def build_rmux_daemon_start_evidence(
    *,
    daemon_id: object,
    success: bool,
    scope: object = 'shared',
    endpoint_kind: object = 'unknown',
    endpoint_ref: object = None,
    version: object = None,
    project_id: object = None,
    namespace_id: object = None,
    capability_status: object = 'unknown',
    crash_reason: object = None,
    diagnostics: Mapping[str, object] | None = None,
) -> RmuxDaemonEvidence:
    reason = _clean_text(crash_reason)
    health = 'healthy' if success else ('crashed' if reason else 'unreachable')
    return build_rmux_daemon_evidence(
        daemon_ref=build_rmux_daemon_ref(
            daemon_id=daemon_id,
            scope=scope,
            endpoint_kind=endpoint_kind,
            endpoint_ref=endpoint_ref,
            version=version,
        ),
        discovery_source='start_result',
        health=health,
        project_id=project_id,
        namespace_id=namespace_id,
        capability_status=capability_status,
        crash_reason=reason,
        cleanup_scope='none',
        diagnostics={
            **dict(diagnostics or {}),
            'start_success': bool(success),
        },
    )


def build_rmux_cleanup_plan(
    *,
    namespace_ref: Mapping[str, object],
    daemon: Mapping[str, object],
    cleanup_scope: object = 'namespace',
    force_daemon: bool = False,
    force_reason: object = None,
    targets: list[Mapping[str, object]] | None = None,
    status: object = 'planned',
    diagnostics: Mapping[str, object] | None = None,
) -> RmuxCleanupPlan:
    scope = _literal(cleanup_scope, allowed={'namespace', 'project', 'daemon'}, default='namespace')
    reason = _clean_text(force_reason)
    if scope == 'daemon' and not force_daemon:
        raise ValueError('daemon cleanup requires force_daemon=True')
    if force_daemon and scope == 'daemon' and not reason:
        raise ValueError('force_reason is required for daemon cleanup')
    daemon_ref = dict(daemon.get('daemon_ref') or daemon)
    daemon_action: RmuxDaemonAction = 'shutdown' if scope == 'daemon' and force_daemon else 'leave_running'
    ordered_steps: list[RmuxCleanupStep] = ['provider_job_evidence', 'namespace_session']
    if daemon_action == 'shutdown':
        ordered_steps.append('daemon_cleanup')
    ordered_steps.append('diagnostics')
    plan_targets = _cleanup_targets(
        namespace_ref=namespace_ref,
        daemon_ref=daemon_ref,
        targets=targets or [],
        include_daemon=daemon_action == 'shutdown',
    )
    return {
        'cleanup_scope': scope,
        'targets': plan_targets,
        'daemon_action': daemon_action,
        'force_daemon': bool(force_daemon),
        'force_reason': reason,
        'ordered_steps': ordered_steps,
        'status': _literal(status, allowed={'planned', 'completed', 'partial', 'failed', 'skipped'}, default='planned'),
        'diagnostics': {
            **dict(diagnostics or {}),
            'backend_impl': 'rmux',
            'daemon_scope': _clean_text(daemon_ref.get('scope')) or 'shared',
            'daemon_id': _clean_text(daemon_ref.get('daemon_id')),
            'namespace_id': _clean_text(namespace_ref.get('namespace_id')),
            'daemon_cleanup_forced': bool(force_daemon and scope == 'daemon'),
            'force_reason': reason,
        },
    }


def backend_daemon_diagnostics(evidence: Mapping[str, object]) -> dict[str, object]:
    if not evidence:
        return {}
    daemon_ref = dict(evidence.get('daemon_ref') or {})
    if not daemon_ref:
        return {}
    daemon_impl = _clean_text(daemon_ref.get('backend_impl'))
    if daemon_impl != 'rmux':
        return {}
    return _compact_dict(
        {
            'backend_daemon_impl': daemon_impl,
            'backend_daemon_id': daemon_ref.get('daemon_id'),
            'backend_daemon_scope': daemon_ref.get('scope'),
            'backend_daemon_endpoint_kind': daemon_ref.get('endpoint_kind'),
            'backend_daemon_endpoint_ref': daemon_ref.get('endpoint_ref'),
            'backend_daemon_version': daemon_ref.get('version'),
            'backend_daemon_capability_status': evidence.get('capability_status'),
            'backend_daemon_health': evidence.get('health'),
            'backend_daemon_discovery_source': evidence.get('discovery_source'),
            'backend_daemon_crash_reason': evidence.get('crash_reason'),
            'backend_daemon_cleanup_scope': evidence.get('cleanup_scope'),
            'backend_daemon_action': evidence.get('daemon_action'),
        }
    )


def provider_health_daemon_diagnostics(
    diagnostics: Mapping[str, object] | None,
    evidence: Mapping[str, object],
) -> dict[str, object]:
    payload = dict(diagnostics or {})
    payload.update(backend_daemon_diagnostics(evidence))
    return payload


def _daemon_ref_from_mapping(value: Mapping[str, object]) -> RmuxDaemonRef:
    return build_rmux_daemon_ref(
        daemon_id=value.get('daemon_id'),
        scope=value.get('scope', 'shared'),
        endpoint_kind=value.get('endpoint_kind', 'unknown'),
        endpoint_ref=value.get('endpoint_ref'),
        version=value.get('version'),
    )


def _daemon_process_evidence(value: Mapping[str, object] | None) -> dict[str, object] | None:
    if value is None:
        return None
    payload = dict(value)
    payload['evidence_kind'] = 'rmux_daemon_process'
    payload.pop('job_id', None)
    payload.pop('runtime_generation', None)
    payload.pop('runtime_root', None)
    return payload


def _cleanup_targets(
    *,
    namespace_ref: Mapping[str, object],
    daemon_ref: Mapping[str, object],
    targets: list[Mapping[str, object]],
    include_daemon: bool,
) -> list[dict[str, object]]:
    payload = [dict(target) for target in targets]
    namespace_id = _clean_text(namespace_ref.get('namespace_id'))
    if namespace_id:
        payload.insert(
            0,
            {
                'kind': 'namespace',
                'namespace_id': namespace_id,
                'backend_impl': 'rmux',
            },
        )
    if include_daemon:
        payload.append(
            {
                'kind': 'daemon',
                'daemon_id': _clean_text(daemon_ref.get('daemon_id')),
                'endpoint_kind': _clean_text(daemon_ref.get('endpoint_kind')) or 'unknown',
                'endpoint_ref': _clean_text(daemon_ref.get('endpoint_ref')),
            }
        )
    return payload


def _literal(value: object, *, allowed: set[str], default: str) -> str:
    text = _clean_text(value) or default
    if text not in allowed:
        raise ValueError(f'unsupported value {text!r}')
    return text


def _compact_dict(payload: Mapping[str, object]) -> dict[str, object]:
    return {key: value for key, value in payload.items() if value is not None and value != ''}


def _clean_text(value: object) -> str | None:
    text = str(value or '').strip()
    return text or None


__all__ = [
    'RmuxCleanupPlan',
    'RmuxDaemonEvidence',
    'RmuxDaemonRef',
    'backend_daemon_diagnostics',
    'build_rmux_cleanup_plan',
    'build_rmux_daemon_evidence',
    'build_rmux_daemon_ref',
    'build_rmux_daemon_start_evidence',
    'provider_health_daemon_diagnostics',
]
