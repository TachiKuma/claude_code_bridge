from __future__ import annotations

from agents.models import AgentState, RuntimeBindingSource, normalize_runtime_binding_source

PROVIDER_AUTH_REVOKED_RUNTIME_HEALTH = 'provider-auth-revoked'
PROVIDER_RECOVERY_BLOCKED_RUNTIME_HEALTH = 'provider-recovery-blocked'
PROCESS_RECOVERY_HEALTHS = frozenset({'process-dead', 'process-missing', 'job-exited'})
NAMESPACE_RECOVERY_HEALTHS = frozenset({'namespace-missing', 'namespace-crashed', 'namespace-foreign'})
DAEMON_RECOVERY_HEALTHS = frozenset({'daemon-unavailable', 'daemon-generation-mismatch'})
PROVIDER_RECOVERY_BLOCKED_RUNTIME_HEALTHS = frozenset(
    {
        PROVIDER_AUTH_REVOKED_RUNTIME_HEALTH,
        PROVIDER_RECOVERY_BLOCKED_RUNTIME_HEALTH,
    }
)
HARD_BLOCKED_RUNTIME_HEALTHS = frozenset({'session-missing'}) | PROVIDER_RECOVERY_BLOCKED_RUNTIME_HEALTHS
RECOVERABLE_RUNTIME_HEALTHS = (
    frozenset({'pane-dead', 'pane-missing'})
    | PROCESS_RECOVERY_HEALTHS
    | NAMESPACE_RECOVERY_HEALTHS
    | DAEMON_RECOVERY_HEALTHS
)


def normalized_runtime_health(runtime) -> str:
    return str(getattr(runtime, 'health', '') or '').strip().lower()


def should_attempt_background_recovery(runtime) -> bool:
    if runtime is None or getattr(runtime, 'state', None) is not AgentState.DEGRADED:
        return False
    binding_source = normalize_runtime_binding_source(
        getattr(runtime, 'binding_source', RuntimeBindingSource.PROVIDER_SESSION)
    )
    if binding_source is RuntimeBindingSource.EXTERNAL_ATTACH:
        return False
    health = normalized_runtime_health(runtime)
    if health in DAEMON_RECOVERY_HEALTHS:
        return daemon_recovery_allowed(runtime)
    return health in RECOVERABLE_RUNTIME_HEALTHS


def daemon_recovery_allowed(runtime) -> bool:
    daemon_ref = runtime_daemon_ref(runtime)
    if not isinstance(daemon_ref, dict) or not daemon_ref:
        return False
    scope = str(daemon_ref.get('scope') or daemon_ref.get('ownership') or '').strip().lower()
    if scope in {'project', 'owned'}:
        return True
    return False


def runtime_daemon_ref(runtime) -> dict[str, object] | None:
    daemon_ref = getattr(runtime, 'daemon_ref', None)
    if isinstance(daemon_ref, dict) and daemon_ref:
        return dict(daemon_ref)
    namespace_ref = getattr(runtime, 'namespace_ref', None)
    if isinstance(namespace_ref, dict):
        nested = namespace_ref.get('daemon_ref')
        if isinstance(nested, dict) and nested:
            return dict(nested)
        evidence = namespace_ref.get('backend_daemon_evidence')
        if isinstance(evidence, dict):
            nested = evidence.get('daemon_ref')
            if isinstance(nested, dict) and nested:
                payload = dict(nested)
                health = evidence.get('health') or evidence.get('daemon_health')
                if health is not None:
                    payload.setdefault('health', health)
                return payload
    return None


__all__ = [
    'HARD_BLOCKED_RUNTIME_HEALTHS',
    'DAEMON_RECOVERY_HEALTHS',
    'NAMESPACE_RECOVERY_HEALTHS',
    'PROCESS_RECOVERY_HEALTHS',
    'PROVIDER_AUTH_REVOKED_RUNTIME_HEALTH',
    'PROVIDER_RECOVERY_BLOCKED_RUNTIME_HEALTH',
    'PROVIDER_RECOVERY_BLOCKED_RUNTIME_HEALTHS',
    'RECOVERABLE_RUNTIME_HEALTHS',
    'daemon_recovery_allowed',
    'normalized_runtime_health',
    'runtime_daemon_ref',
    'should_attempt_background_recovery',
]
