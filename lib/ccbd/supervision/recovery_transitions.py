from __future__ import annotations

from agents.models import AgentState
from ccbd.services.runtime_recovery_policy import (
    DAEMON_RECOVERY_HEALTHS,
    NAMESPACE_RECOVERY_HEALTHS,
    PROCESS_RECOVERY_HEALTHS,
    PROVIDER_RECOVERY_BLOCKED_RUNTIME_HEALTHS,
    daemon_recovery_allowed,
    normalized_runtime_health,
)

from .recovery_context import RecoveryContext
from .evidence import runtime_has_explicit_evidence
from .recovery_events import append_recovery_event

SUCCESS_RUNTIME_HEALTHS = frozenset({'healthy', 'restored'})


def start_recovery(
    ctx: RecoveryContext,
    *,
    attempted_at: str,
    prior_health: str,
):
    recovering = ctx.upsert_if_changed_fn(
        ctx.runtime,
        reconcile_state='recovering',
        last_reconcile_at=attempted_at,
        lifecycle_state='recovering',
    )
    append_recovery_event(
        ctx,
        event_kind='recover_started',
        occurred_at=attempted_at,
        runtime=recovering,
        prior_health=prior_health,
        result_health=prior_health,
    )
    return recovering


def attempt_recovery_action(ctx: RecoveryContext, *, recovering):
    current_health = normalized_runtime_health(recovering)
    if ctx.should_reflow_project_namespace_fn(recovering):
        ctx.remount_project_fn(f'pane_recovery:{ctx.agent_name}')
        return ctx.registry.get(ctx.agent_name), None
    if current_health in NAMESPACE_RECOVERY_HEALTHS:
        return recovering, current_health
    if current_health in DAEMON_RECOVERY_HEALTHS and not daemon_recovery_allowed(recovering):
        return recovering, 'daemon-recovery-unowned'
    refreshed = ctx.runtime_service.refresh_provider_binding(ctx.agent_name, recover=True)
    if refreshed is None:
        return None, None
    if normalized_runtime_health(refreshed) in PROVIDER_RECOVERY_BLOCKED_RUNTIME_HEALTHS:
        return refreshed, str(
            getattr(refreshed, 'last_failure_reason', None)
            or normalized_runtime_health(refreshed)
        )
    if normalized_runtime_health(refreshed) in PROCESS_RECOVERY_HEALTHS:
        return refreshed, str(getattr(refreshed, 'last_failure_reason', None) or normalized_runtime_health(refreshed))
    if ctx.should_reflow_project_namespace_fn(recovering, recovered=refreshed):
        ctx.remount_project_fn(f'pane_recovery:{ctx.agent_name}')
        return ctx.registry.get(ctx.agent_name), None
    return refreshed, None


def mark_recovery_missing(
    ctx: RecoveryContext,
    *,
    recovering,
    attempted_at: str,
    restart_count: int,
    prior_health: str,
) -> str:
    failed = ctx.upsert_if_changed_fn(
        recovering,
        reconcile_state='degraded',
        restart_count=restart_count,
        last_reconcile_at=attempted_at,
        last_failure_reason='runtime-missing-after-recover',
        lifecycle_state='degraded',
    )
    append_recovery_event(
        ctx,
        event_kind='recover_failed',
        occurred_at=attempted_at,
        runtime=failed,
        prior_health=prior_health,
        result_health='unmounted',
        details={'reason': 'runtime-missing-after-recover'},
    )
    return 'unmounted'


def mark_daemon_degraded(
    ctx: RecoveryContext,
    *,
    attempted_at: str,
    prior_health: str,
) -> str:
    degraded = ctx.upsert_if_changed_fn(
        ctx.runtime,
        reconcile_state='degraded',
        last_reconcile_at=attempted_at,
        last_failure_reason='daemon-recovery-unowned',
        lifecycle_state='degraded',
    )
    append_recovery_event(
        ctx,
        event_kind='daemon_degraded',
        occurred_at=attempted_at,
        runtime=degraded,
        prior_health=prior_health,
        result_health=prior_health,
        details={
            'reason': 'daemon-recovery-unowned',
            'action': 'degraded_only',
            'ownership': 'shared_or_unowned',
        },
    )
    return degraded.health


def mark_recovery_succeeded(
    ctx: RecoveryContext,
    *,
    refreshed,
    attempted_at: str,
    restart_count: int,
    prior_health: str,
    next_health: str,
) -> str:
    stabilized = ctx.upsert_if_changed_fn(
        refreshed,
        reconcile_state='steady',
        restart_count=restart_count,
        last_reconcile_at=attempted_at,
        last_failure_reason=None,
        lifecycle_state=refreshed.state.value,
    )
    append_recovery_event(
        ctx,
        event_kind='recover_succeeded',
        occurred_at=attempted_at,
        runtime=stabilized,
        prior_health=prior_health,
        result_health=next_health,
        details={
            'restart_count': stabilized.restart_count,
            **_recovery_action_details(prior_health, runtime=stabilized),
        },
    )
    return stabilized.health


def mark_recovery_failed(
    ctx: RecoveryContext,
    *,
    refreshed,
    attempted_at: str,
    restart_count: int,
    prior_health: str,
    next_health: str,
    failure_reason: str | None,
) -> str:
    next_health = normalized_runtime_health(refreshed) or next_health
    recovery_blocked = next_health in PROVIDER_RECOVERY_BLOCKED_RUNTIME_HEALTHS
    failure_runtime = ctx.upsert_if_changed_fn(
        refreshed,
        reconcile_state='blocked' if recovery_blocked else 'degraded',
        restart_count=restart_count,
        last_reconcile_at=attempted_at,
        last_failure_reason=failure_reason or next_health or prior_health or 'recover-failed',
        lifecycle_state='degraded' if refreshed.state is AgentState.DEGRADED else refreshed.lifecycle_state,
    )
    append_recovery_event(
        ctx,
        event_kind='recover_failed',
        occurred_at=attempted_at,
        runtime=failure_runtime,
        prior_health=prior_health,
        result_health=next_health,
        details={
            'reason': failure_runtime.last_failure_reason or 'recover-failed',
            **_recovery_action_details(prior_health, runtime=failure_runtime, failure_reason=failure_reason),
        },
    )
    return failure_runtime.health


def _recovery_action_details(
    prior_health: str,
    *,
    runtime,
    failure_reason: str | None = None,
) -> dict[str, object]:
    if prior_health in DAEMON_RECOVERY_HEALTHS:
        if failure_reason == 'daemon-recovery-unowned':
            return {'action': 'degraded_only', 'ownership': 'shared_or_unowned'}
        return {'action': 'daemon_recover'}
    if prior_health in PROCESS_RECOVERY_HEALTHS:
        return {'action': 'provider_restart'}
    if prior_health in NAMESPACE_RECOVERY_HEALTHS:
        return {'action': 'namespace_recover'}
    if prior_health in {'pane-dead', 'pane-missing', 'pane-foreign'} and runtime_has_explicit_evidence(runtime):
        return {'action': 'pane_recover'}
    return {}


__all__ = [
    'SUCCESS_RUNTIME_HEALTHS',
    'attempt_recovery_action',
    'mark_daemon_degraded',
    'mark_recovery_failed',
    'mark_recovery_missing',
    'mark_recovery_succeeded',
    'start_recovery',
]
