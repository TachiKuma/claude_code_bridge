from __future__ import annotations

from typing import Any

from ccbd.services.runtime_recovery_policy import runtime_daemon_ref


RMUX_BACKEND_IMPLS = frozenset({'rmux', 'psmux'})
PROCESS_RECOVERY_HEALTHS = frozenset({'process-dead', 'process-missing', 'job-exited'})
NAMESPACE_RECOVERY_HEALTHS = frozenset({'namespace-missing', 'namespace-crashed', 'namespace-foreign'})
DAEMON_DIAGNOSTIC_HEALTHS = frozenset({'daemon-unavailable', 'daemon-generation-mismatch'})


def runtime_backend_impl(runtime) -> str:
    value = _clean(getattr(runtime, 'backend_impl', None) or getattr(runtime, 'terminal_backend', None))
    if value:
        return value.lower()
    namespace_ref = runtime_namespace_ref(runtime)
    value = _clean(namespace_ref.get('backend_impl') if namespace_ref else None)
    if value:
        return value.lower()
    return 'tmux'


def runtime_namespace_ref(runtime) -> dict[str, object] | None:
    namespace_ref = getattr(runtime, 'namespace_ref', None)
    if isinstance(namespace_ref, dict) and namespace_ref:
        return dict(namespace_ref)
    return None


def runtime_pane_ref(runtime) -> dict[str, object] | None:
    pane_ref = getattr(runtime, 'pane_ref', None)
    if isinstance(pane_ref, dict) and pane_ref:
        return dict(pane_ref)
    pane_id = runtime_active_pane_id(runtime)
    if pane_id is None:
        return None
    return {
        'backend_impl': runtime_backend_impl(runtime),
        'pane_id': pane_id,
    }


def runtime_active_pane_id(runtime) -> str | None:
    pane_ref = getattr(runtime, 'pane_ref', None)
    if isinstance(pane_ref, dict):
        pane_id = _clean(pane_ref.get('pane_id') or pane_ref.get('id'))
        if pane_id:
            return pane_id
    backend_impl = runtime_backend_impl(runtime)
    for field_name in ('active_pane_id', 'pane_id'):
        pane_id = _clean(getattr(runtime, field_name, None))
        if not pane_id:
            continue
        if backend_impl in RMUX_BACKEND_IMPLS or pane_id.startswith('%'):
            return pane_id
    runtime_ref = _clean(getattr(runtime, 'runtime_ref', None))
    if runtime_ref.startswith('tmux:%'):
        return runtime_ref[len('tmux:') :]
    if backend_impl in RMUX_BACKEND_IMPLS and ':' in runtime_ref:
        return runtime_ref.split(':', 1)[1] or None
    return None


def runtime_belongs_to_namespace_session(runtime, *, session_name: str) -> bool:
    expected = _clean(session_name)
    if not expected:
        return False
    namespace_ref = runtime_namespace_ref(runtime)
    if not namespace_ref:
        return False
    candidates = {
        _clean(namespace_ref.get('session_name')),
        _clean(namespace_ref.get('namespace_id')),
        _clean(namespace_ref.get('id')),
    }
    return expected in candidates


def build_runtime_evidence_ledger(runtime) -> dict[str, object]:
    health = _clean(getattr(runtime, 'health', None)).lower()
    backend_impl = runtime_backend_impl(runtime)
    namespace_ref = runtime_namespace_ref(runtime)
    pane_ref = runtime_pane_ref(runtime)
    process_ref = _dict_or_none(getattr(runtime, 'process_ref', None))
    daemon_ref = runtime_daemon_ref(runtime)
    if daemon_ref is None and backend_impl in RMUX_BACKEND_IMPLS and getattr(runtime, 'daemon_generation', None) is not None:
        daemon_ref = {'generation': getattr(runtime, 'daemon_generation', None)}
    return {
        'backend_impl': backend_impl,
        'namespace_ref': namespace_ref,
        'pane_ref': pane_ref,
        'process_ref': process_ref,
        'daemon_ref': daemon_ref,
        'pane_health': _pane_health(runtime, health, pane_ref),
        'process_health': _process_health(runtime, health, process_ref),
        'namespace_health': _namespace_health(health, namespace_ref),
        'daemon_health': _daemon_health(health, daemon_ref),
    }


def runtime_has_explicit_evidence(runtime) -> bool:
    health = _clean(getattr(runtime, 'health', None)).lower()
    return (
        runtime_backend_impl(runtime) in RMUX_BACKEND_IMPLS
        or runtime_namespace_ref(runtime) is not None
        or _dict_or_none(getattr(runtime, 'pane_ref', None)) is not None
        or _dict_or_none(getattr(runtime, 'process_ref', None)) is not None
        or _dict_or_none(getattr(runtime, 'daemon_ref', None)) is not None
        or health in PROCESS_RECOVERY_HEALTHS
        or health in NAMESPACE_RECOVERY_HEALTHS
        or health in DAEMON_DIAGNOSTIC_HEALTHS
    )


def details_with_evidence_ledger(runtime, details: dict[str, object] | None = None) -> dict[str, object]:
    payload = dict(details or {})
    if runtime_has_explicit_evidence(runtime):
        payload.setdefault('evidence_ledger', build_runtime_evidence_ledger(runtime))
    return payload


def _pane_health(runtime, health: str, pane_ref: dict[str, object] | None) -> str:
    if health == 'pane-dead':
        return 'dead'
    if health == 'pane-missing':
        return 'missing'
    if health == 'pane-foreign':
        return 'foreign'
    pane_state = _clean(getattr(runtime, 'pane_state', None)).lower()
    if pane_state in {'alive', 'missing', 'dead', 'foreign', 'unknown'}:
        return pane_state
    if pane_ref is not None:
        return 'alive'
    return 'unknown'


def _process_health(runtime, health: str, process_ref: dict[str, object] | None) -> str:
    if health == 'process-dead' or health == 'job-exited':
        return 'dead'
    if health == 'process-missing':
        return 'missing'
    if process_ref is None:
        return 'unknown'
    value = _clean(process_ref.get('health') or process_ref.get('state') or process_ref.get('status')).lower()
    if value in {'alive', 'dead', 'missing', 'unknown'}:
        return value
    if process_ref.get('pid') is not None:
        return 'alive'
    return 'unknown'


def _namespace_health(health: str, namespace_ref: dict[str, object] | None) -> str:
    if health == 'namespace-missing':
        return 'missing'
    if health == 'namespace-crashed':
        return 'crashed'
    if health == 'namespace-foreign':
        return 'foreign'
    return 'alive' if namespace_ref is not None else 'unknown'


def _daemon_health(health: str, daemon_ref: dict[str, object] | None) -> str:
    if health == 'daemon-unavailable':
        return 'dead'
    if health == 'daemon-generation-mismatch':
        return 'generation-mismatch'
    if daemon_ref is None:
        return 'unknown'
    value = _clean(daemon_ref.get('health') or daemon_ref.get('state') or daemon_ref.get('status')).lower()
    if value in {'alive', 'dead', 'generation-mismatch', 'unowned', 'unknown'}:
        return value
    if value in {'healthy', 'starting'}:
        return 'alive'
    if value in {'missing', 'unreachable', 'crashed'}:
        return 'dead'
    if value == 'stale':
        return 'generation-mismatch'
    if value == 'foreign':
        return 'unowned'
    return 'unknown'


def _dict_or_none(value: Any) -> dict[str, object] | None:
    if isinstance(value, dict) and value:
        return dict(value)
    return None


def _clean(value: object) -> str:
    return str(value or '').strip()


__all__ = [
    'DAEMON_DIAGNOSTIC_HEALTHS',
    'NAMESPACE_RECOVERY_HEALTHS',
    'PROCESS_RECOVERY_HEALTHS',
    'RMUX_BACKEND_IMPLS',
    'build_runtime_evidence_ledger',
    'details_with_evidence_ledger',
    'runtime_active_pane_id',
    'runtime_backend_impl',
    'runtime_belongs_to_namespace_session',
    'runtime_has_explicit_evidence',
    'runtime_namespace_ref',
    'runtime_pane_ref',
]
