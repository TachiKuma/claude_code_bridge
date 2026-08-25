from __future__ import annotations

from dataclasses import dataclass

from ccbd.services.project_namespace_state_runtime.namespace_projection import (
    resolved_namespace_backend_family,
)
from platforms.windows.herdr.runtime.events import map_herdr_state_to_ccb


@dataclass(frozen=True)
class RuntimeStatusInput:
    project_id: str
    agent_name: str
    namespace: object | None
    runtime: object | None
    job: object | None
    callback_wait: object | None = None
    reload_drain: object | None = None
    provider_control: object | None = None
    provider_runtime_status: object | None = None


def build_runtime_status(input: RuntimeStatusInput) -> dict[str, object] | None:
    if not namespace_is_herdr(input.namespace):
        return None
    fact = herdr_agent_status_fact(input.runtime)
    raw_state = fact['agent_status']
    source = 'herdr_runtime' if raw_state is not None else 'missing_herdr_runtime_state'
    runtime_state = raw_state or 'unknown'
    frontend = namespace_frontend_status(input.namespace)
    pane_id = str(getattr(input.runtime, 'pane_id', '') or '').strip() or None
    generation = getattr(input.runtime, 'runtime_generation', None) or getattr(
        input.runtime,
        'binding_generation',
        None,
    )
    record: dict[str, object] = {
        'schema_version': 1,
        'state': map_herdr_state_to_ccb(runtime_state),
        'agent_status': runtime_state,
        'agent_status_source': fact.get('source') or source,
        'agent_status_seq': fact.get('seq'),
        'agent_status_fallback_reason': fact.get('fallback_reason'),
        'runtime_state': runtime_state,
        'source': source,
        'unseen_done': runtime_state == 'done',
        'job_status': (
            getattr(getattr(input.job, 'status', None), 'value', None)
            if input.job is not None
            else None
        ),
        'job_id': getattr(input.job, 'job_id', None) if input.job is not None else None,
        'chain_waiting_state': (
            input.callback_wait.state.value if input.callback_wait is not None else None
        ),
        'chain_waiting_child_job_id': (
            input.callback_wait.child_job_id if input.callback_wait is not None else None
        ),
        'chain_waiting_child_agent': _callback_child_agent(input.callback_wait),
        'chain_updated_at': (
            input.callback_wait.updated_at if input.callback_wait is not None else None
        ),
        'reload_drain': dict(input.reload_drain) if input.reload_drain is not None else None,
        'dispatch_blocked_by_reload_drain': input.reload_drain is not None,
        'provider_control': (
            dict(input.provider_control) if input.provider_control is not None else None
        ),
        'provider_runtime_state': getattr(input.provider_runtime_status, 'state', None),
        'provider_runtime_source': getattr(input.provider_runtime_status, 'source', None),
        'pane_id': pane_id,
        'runtime_generation': generation,
        'cache_key': {
            'project_id': input.project_id,
            'agent_name': input.agent_name,
            'runtime_generation': generation,
            'pane_id': pane_id,
        },
    }
    if frontend is not None:
        record['frontend_state'] = frontend.get('state')
        record['frontend_status'] = frontend
    return record


def namespace_is_herdr(namespace) -> bool:
    if namespace is None:
        return False
    family = resolved_namespace_backend_family(
        getattr(namespace, 'backend_impl', None),
        getattr(namespace, 'namespace_backend_family', None),
    )
    return family == 'herdr-native'


def namespace_frontend_status(namespace) -> dict[str, object] | None:
    if namespace is None:
        return None
    if not namespace_is_herdr(namespace):
        return None
    frontend = getattr(namespace, 'frontend', None)
    if not isinstance(frontend, dict):
        return {
            'kind': 'wezterm',
            'state': 'unknown',
            'reason': 'missing_frontend_binding',
        }
    status = str(frontend.get('status') or '').strip()
    if status == 'wezterm_tab_attached':
        state = 'wezterm_tab_attached'
    elif status == 'detached_fallback':
        state = 'detached_fallback'
    elif status == 'frontend_not_ready':
        state = 'frontend_not_ready'
    else:
        state = 'unknown'
    record: dict[str, object] = {
        'kind': str(frontend.get('kind') or 'wezterm'),
        'state': state,
    }
    for key in (
        'mux_available',
        'launch_mode',
        'fallback',
        'fallback_reason',
        'reason',
        'spawn_target',
        'window_id',
    ):
        if key in frontend:
            record[key] = frontend[key]
    return record


def herdr_runtime_state_fact(runtime) -> str | None:
    return herdr_agent_status_fact(runtime)['agent_status']


def herdr_agent_status_fact(runtime) -> dict[str, object | None]:
    fact: dict[str, object | None] = {
        'agent_status': None,
        'source': None,
        'seq': None,
        'fallback_reason': None,
    }
    if runtime is None:
        return fact
    for attr in ('herdr_runtime_state', 'herdr_state'):
        value = str(getattr(runtime, attr, '') or '').strip().lower()
        if value:
            fact['agent_status'] = value
            fact['source'] = 'runtime_attribute'
            return fact
    snapshot_fact = _herdr_agent_status_from_snapshot(
        getattr(runtime, 'herdr_runtime_snapshot', None),
        pane_id=getattr(runtime, 'pane_id', None),
    )
    if snapshot_fact['agent_status'] is not None:
        return snapshot_fact
    for container in (
        getattr(runtime, 'pane_ref', None),
        getattr(runtime, 'provider_runtime_backend_ref', None),
    ):
        if not isinstance(container, dict):
            continue
        for key in ('herdr_runtime_state', 'runtime_state', 'state'):
            value = str(container.get(key) or '').strip().lower()
            if value:
                fact['agent_status'] = value
                fact['source'] = str(container.get('source') or 'pane_ref').strip() or 'pane_ref'
                fact['seq'] = _optional_non_negative_int(container.get('seq'))
                fact['fallback_reason'] = _optional_text(container.get('fallback_reason'))
                return fact
    return fact


def _herdr_runtime_state_from_snapshot(snapshot, *, pane_id: object | None) -> str | None:
    value = _herdr_agent_status_from_snapshot(snapshot, pane_id=pane_id)['agent_status']
    return str(value) if value is not None else None


def _herdr_agent_status_from_snapshot(snapshot, *, pane_id: object | None) -> dict[str, object | None]:
    fact: dict[str, object | None] = {
        'agent_status': None,
        'source': None,
        'seq': None,
        'fallback_reason': None,
    }
    if not isinstance(snapshot, dict):
        return fact
    snapshot_source = _optional_text(snapshot.get('source')) or 'snapshot'
    fallback_reason = _optional_text(snapshot.get('fallback_reason'))
    target_pane_id = str(pane_id or '').strip()
    panes = snapshot.get('panes')
    if isinstance(panes, list):
        if target_pane_id:
            for pane in panes:
                if not isinstance(pane, dict):
                    continue
                current_pane_id = str(pane.get('pane_id') or '').strip()
                if current_pane_id != target_pane_id:
                    continue
                for key in ('runtime_state', 'state'):
                    value = str(pane.get(key) or '').strip().lower()
                    if value:
                        fact['agent_status'] = value
                        fact['source'] = _optional_text(pane.get('source')) or snapshot_source
                        fact['seq'] = _optional_non_negative_int(pane.get('seq'))
                        fact['fallback_reason'] = _optional_text(pane.get('fallback_reason')) or fallback_reason
                        return fact
            return fact
        for pane in panes:
            if not isinstance(pane, dict):
                continue
            for key in ('runtime_state', 'state'):
                value = str(pane.get(key) or '').strip().lower()
                if value:
                    fact['agent_status'] = value
                    fact['source'] = _optional_text(pane.get('source')) or snapshot_source
                    fact['seq'] = _optional_non_negative_int(pane.get('seq'))
                    fact['fallback_reason'] = _optional_text(pane.get('fallback_reason')) or fallback_reason
                    return fact
    for key in ('runtime_state', 'state'):
        value = str(snapshot.get(key) or '').strip().lower()
        if value:
            fact['agent_status'] = value
            fact['source'] = snapshot_source
            fact['seq'] = _optional_non_negative_int(snapshot.get('seq'))
            fact['fallback_reason'] = fallback_reason
            return fact
    return fact


def _optional_text(value: object) -> str | None:
    text = str(value or '').strip()
    return text or None


def _optional_non_negative_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def _callback_child_agent(callback_wait) -> str | None:
    if callback_wait is None:
        return None
    diagnostics = getattr(callback_wait, 'diagnostics', None)
    if isinstance(diagnostics, dict):
        value = str(diagnostics.get('child_agent') or '').strip()
        if value:
            return value
    for attr in ('child_agent', 'to_agent', 'target_agent', 'agent_name'):
        value = str(getattr(callback_wait, attr, '') or '').strip()
        if value:
            return value
    return None


__all__ = [
    'RuntimeStatusInput',
    'build_runtime_status',
    'herdr_agent_status_fact',
    'herdr_runtime_state_fact',
    'namespace_frontend_status',
    'namespace_is_herdr',
]
