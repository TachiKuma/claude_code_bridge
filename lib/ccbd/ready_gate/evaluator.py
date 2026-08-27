"""Ready Gate 评估器。

严格三条件判定：binding 已写入且可校验 + provider 入口可接收任务
+ 至少一次 health/ping 成功。三个条件通过注入函数提供，便于单元测试。

默认注入实现（checks.py）供生产时使用，也单独可测。"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
import time

from ccbd.launch_plan.models import PrecomputeResult
from ccbd.models import CcbdStartupAgentResult

from .models import (
    AgentReadyDetail,
    AgentReadyState,
    AllReadyResult,
    ConcurrencyObservation,
    HealthProbeOutcome,
)


# 注入函数类型
BindingCheckFn = Callable[[CcbdStartupAgentResult], tuple[bool, tuple[str, ...]]]
ProviderReadyFn = Callable[[CcbdStartupAgentResult], HealthProbeOutcome]
PingFn = Callable[[CcbdStartupAgentResult], bool]


def _text(value: object) -> str:
    return str(value or '').strip()


def _binding_evidence(result: CcbdStartupAgentResult) -> tuple[str, ...]:
    """收集 binding 证据字段。"""
    evidence = []
    for field in ('runtime_ref', 'session_ref', 'binding_source'):
        if _text(getattr(result, field, None)):
            evidence.append(field)
    return tuple(evidence)


def default_binding_check(result: CcbdStartupAgentResult) -> tuple[bool, tuple[str, ...]]:
    """条件 1：binding 已写入且可校验。

    检查 runtime_ref / session_ref / binding_source 任一非空作为 binding 证据。
    """
    evidence = _binding_evidence(result)
    return bool(evidence), evidence


def default_provider_ready_fn(health_check_fn: Callable[[str], str] | None = None) -> ProviderReadyFn:
    """条件 2：provider 入口可接收任务。

    通过 health_check_fn(agent_name) 返回的 health == 'healthy' 判定。
    无注入时视为 ready。
    """

    def _check(result: CcbdStartupAgentResult) -> HealthProbeOutcome:
        agent_name = _text(result.agent_name)
        label: str | None = None
        health_ok = True
        if health_check_fn is not None:
            try:
                label = _text(health_check_fn(agent_name))
            except Exception:
                label = None
            health_ok = label == 'healthy'
        return HealthProbeOutcome(
            health_ok=health_ok,
            ping_ok=False,
            health_label=label,
            probe_ms=0.0,
        )

    return _check


def default_ping_fn(ping_fn: Callable[[CcbdStartupAgentResult], bool] | None = None) -> PingFn:
    """条件 3：至少一次 health/ping 成功。

    无注入时退化返回 True（向后兼容）。
    """
    if ping_fn is not None:
        return ping_fn
    return lambda _result: True


@dataclass(frozen=True)
class ReadyGateEvaluator:
    """Ready Gate 评估器。三个条件均通过注入函数提供。"""

    binding_check_fn: BindingCheckFn | None = None
    provider_ready_fn: ProviderReadyFn | None = None
    ping_fn: PingFn | None = None
    max_concurrency: int = 3
    clock: object = time.monotonic_ns

    def evaluate(
        self,
        *,
        startup_results: Sequence[CcbdStartupAgentResult],
        launch_plan_result: PrecomputeResult | None = None,
        target_order: Sequence[str] = (),
        probe_outcomes: Mapping[str, HealthProbeOutcome] | None = None,
        restart_required_agents: Sequence[str] = (),
    ) -> AllReadyResult:
        """评估所有目标 agent 的 ready 状态，产出 AllReadyResult。"""
        binding_check = self.binding_check_fn or default_binding_check
        provider_ready = self.provider_ready_fn or (
            default_provider_ready_fn(None)
        )
        ping = self.ping_fn or default_ping_fn(None)

        results_by_name = {
            _text(result.agent_name): result for result in startup_results
        }
        plan_by_name = dict(launch_plan_result.plans) if launch_plan_result is not None else {}
        probe_by_name = dict(probe_outcomes or {})
        restart_required = {
            _text(agent_name)
            for agent_name in restart_required_agents
            if _text(agent_name)
        }

        ordered = list(target_order) or sorted(
            set(results_by_name) | set(plan_by_name)
        )

        per_agent: dict[str, AgentReadyDetail] = {}
        failures: dict[str, str] = {}
        total_wait_ms = 0.0

        for agent_name in ordered:
            plan = plan_by_name.get(agent_name)
            state: AgentReadyState
            detail = self._evaluate_one(
                agent_name,
                result=results_by_name.get(agent_name),
                plan_status=getattr(plan, 'status', None) if plan is not None else None,
                plan_error=getattr(plan, 'error', None) if plan is not None else None,
                binding_check=binding_check,
                provider_ready=provider_ready,
                ping=ping,
                probe=probe_by_name.get(agent_name),
                restart_required=agent_name in restart_required,
            )
            per_agent[agent_name] = detail
            if detail.state is AgentReadyState.AGENT_FAILED and detail.failure_reason:
                failures[agent_name] = detail.failure_reason
            total_wait_ms = max(total_wait_ms, detail.concurrency_wait_ms)

        ready_agents = [
            name for name, detail in per_agent.items()
            if detail.ready_ms is not None
        ]
        total_ready_ms = (
            max(per_agent[name].ready_ms for name in ready_agents)
            if ready_agents else None
        )
        per_agent_ms = {
            name: detail.ready_ms
            for name, detail in per_agent.items()
            if detail.ready_ms is not None
        }
        all_ready = bool(per_agent) and all(
            detail.state is AgentReadyState.AGENT_READY
            for detail in per_agent.values()
        )

        concurrency = ConcurrencyObservation(
            max_workers=max(1, int(self.max_concurrency)),
            total_agents=len(ordered),
            measured_peak_in_flight=0,
            concurrency_wait_ms=total_wait_ms,
        )

        return AllReadyResult(
            all_ready=all_ready,
            per_agent=per_agent,
            total_ready_ms=total_ready_ms,
            per_agent_ms=per_agent_ms,
            stage_timings_ms={},
            concurrency=concurrency,
            failures=failures,
        )

    @staticmethod
    def _evaluate_one(
        agent_name: str,
        *,
        result: CcbdStartupAgentResult | None,
        plan_status: str | None,
        plan_error: str | None,
        binding_check: BindingCheckFn,
        provider_ready: ProviderReadyFn,
        ping: PingFn,
        probe: HealthProbeOutcome | None,
        restart_required: bool = False,
    ) -> AgentReadyDetail:
        # plan 状态优先
        if plan_status is not None and plan_status == 'skipped':
            return AgentReadyDetail(
                agent_name=agent_name,
                state=AgentReadyState.AGENT_SKIPPED,
                binding_verified=False,
                provider_ready=False,
                ping_succeeded=False,
                failure_reason=None,
                binding_evidence=(),
                probe=probe,
            )
        if plan_status is not None and plan_status == 'failed':
            return AgentReadyDetail(
                agent_name=agent_name,
                state=AgentReadyState.AGENT_FAILED,
                binding_verified=False,
                provider_ready=False,
                ping_succeeded=False,
                failure_reason=plan_error or 'precompute_failed',
                binding_evidence=(),
                probe=probe,
            )

        if result is None:
            return AgentReadyDetail(
                agent_name=agent_name,
                state=AgentReadyState.AGENT_FAILED,
                binding_verified=False,
                provider_ready=False,
                ping_succeeded=False,
                failure_reason='startup_result_missing',
                binding_evidence=(),
                probe=probe,
            )

        action = _text(result.action)
        health = _text(result.health)
        if action == 'failed' or health == 'failed':
            return AgentReadyDetail(
                agent_name=agent_name,
                state=AgentReadyState.AGENT_FAILED,
                binding_verified=False,
                provider_ready=False,
                ping_succeeded=False,
                failure_reason=_text(result.failure_reason) or f'startup_{action}',
                binding_evidence=(),
                probe=probe,
            )
        if action == 'deferred':
            return AgentReadyDetail(
                agent_name=agent_name,
                state=AgentReadyState.AGENT_WAITING,
                binding_verified=bool(_binding_evidence(result)),
                provider_ready=False,
                ping_succeeded=False,
                failure_reason=_text(result.failure_reason) or None,
                binding_evidence=_binding_evidence(result),
                probe=probe,
            )

        binding_ok, evidence = binding_check(result)
        if restart_required:
            return AgentReadyDetail(
                agent_name=agent_name,
                state=AgentReadyState.AGENT_WAITING,
                binding_verified=binding_ok,
                provider_ready=False,
                ping_succeeded=False,
                failure_reason='restart_required',
                binding_evidence=evidence,
                probe=probe,
            )

        outcome = probe if probe is not None else provider_ready(result)
        health_ok = outcome.health_ok
        ping_ok = outcome.ping_ok if probe is not None else ping(result)

        ready = binding_ok and health_ok and ping_ok
        if ready:
            return AgentReadyDetail(
                agent_name=agent_name,
                state=AgentReadyState.AGENT_READY,
                binding_verified=True,
                provider_ready=health_ok,
                ping_succeeded=ping_ok,
                failure_reason=None,
                binding_evidence=evidence,
                ready_ms=result.duration_ms,
                probe=outcome,
            )
        return AgentReadyDetail(
            agent_name=agent_name,
            state=AgentReadyState.AGENT_WAITING,
            binding_verified=binding_ok,
            provider_ready=health_ok,
            ping_succeeded=ping_ok,
            failure_reason=_text(result.failure_reason) or None,
            binding_evidence=evidence,
            probe=outcome,
        )


__all__ = [
    'ReadyGateEvaluator',
    'default_binding_check',
    'default_ping_fn',
    'default_provider_ready_fn',
    '_binding_evidence',
]
