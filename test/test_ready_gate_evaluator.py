"""Ready Gate 评估器测试（核心场景）。"""

from __future__ import annotations

from ccbd.launch_plan.models import AgentLaunchPlan, PrecomputeResult
from ccbd.models import CcbdStartupAgentResult
from ccbd.ready_gate.evaluator import (
    ReadyGateEvaluator,
    default_binding_check,
)
from ccbd.ready_gate.models import (
    AgentReadyState,
    AllReadyResult,
    HealthProbeOutcome,
)


def _result(
    agent_name: str,
    *,
    action: str = 'launched',
    health: str = 'healthy',
    runtime_ref: str | None = 'tmux:%1',
    session_ref: str | None = 'sess1',
    binding_source: str | None = 'provider-session',
    failure_reason: str | None = None,
    duration_ms: float | None = 12.5,
) -> CcbdStartupAgentResult:
    return CcbdStartupAgentResult(
        agent_name=agent_name,
        provider='codex',
        action=action,
        health=health,
        workspace_path='/tmp/work',
        runtime_ref=runtime_ref,
        session_ref=session_ref,
        binding_source=binding_source,
        failure_reason=failure_reason,
        duration_ms=duration_ms,
    )


def _ready_probe() -> HealthProbeOutcome:
    return HealthProbeOutcome(health_ok=True, ping_ok=True, health_label='healthy', probe_ms=1.0)


# =============================================================================
# binding 条件
# =============================================================================


def test_binding_not_written_fails_gate_even_if_health_ok() -> None:
    """binding 未写入时 ready gate 不通过（即使 health 成功）。"""
    result = _result(
        'agent1',
        runtime_ref=None,
        session_ref=None,
        binding_source=None,
    )
    evaluator = ReadyGateEvaluator(
        binding_check_fn=default_binding_check,
        provider_ready_fn=lambda _r: _ready_probe(),
        ping_fn=lambda _r: True,
    )
    gate = evaluator.evaluate(
        startup_results=[result],
        target_order=['agent1'],
    )
    detail = gate.per_agent['agent1']
    assert detail.state is AgentReadyState.AGENT_WAITING
    assert detail.binding_verified is False


def test_binding_written_passes_binding_condition() -> None:
    """binding 已写入（有 runtime_ref）时 binding 条件通过。"""
    result = _result('agent1')
    evaluator = ReadyGateEvaluator(
        binding_check_fn=default_binding_check,
        provider_ready_fn=lambda _r: _ready_probe(),
        ping_fn=lambda _r: True,
    )
    gate = evaluator.evaluate(startup_results=[result], target_order=['agent1'])
    assert gate.per_agent['agent1'].binding_verified is True
    assert gate.per_agent['agent1'].state is AgentReadyState.AGENT_READY


# =============================================================================
# health ping 条件
# =============================================================================


def test_health_ping_not_done_fails_gate() -> None:
    """health ping 未完成时 ready gate 不通过。"""
    result = _result('agent1')
    evaluator = ReadyGateEvaluator(
        binding_check_fn=default_binding_check,
        provider_ready_fn=lambda _r: _ready_probe(),
        ping_fn=lambda _r: False,
    )
    gate = evaluator.evaluate(startup_results=[result], target_order=['agent1'])
    assert gate.per_agent['agent1'].state is AgentReadyState.AGENT_WAITING
    assert gate.per_agent['agent1'].ping_succeeded is False


def test_health_probe_fail_fails_gate() -> None:
    """provider health 未通过（pane-dead）时 ready gate 不通过。"""
    result = _result('agent1')
    evaluator = ReadyGateEvaluator(
        binding_check_fn=default_binding_check,
        provider_ready_fn=lambda _r: HealthProbeOutcome(health_ok=False, ping_ok=True, health_label='pane-dead'),
        ping_fn=lambda _r: True,
    )
    gate = evaluator.evaluate(startup_results=[result], target_order=['agent1'])
    assert gate.per_agent['agent1'].state is AgentReadyState.AGENT_WAITING
    assert gate.per_agent['agent1'].provider_ready is False


# =============================================================================
# partial ready 四态区分
# =============================================================================


def test_partial_ready_distinguishes_four_states() -> None:
    """partial ready 结果模型区分 ready/waiting/failed/skipped。"""
    ready = _result('a')
    waiting = _result('b')  # ping 失败 → waiting
    failed = _result('c', action='failed', health='failed', failure_reason='stale_binding_unresolved')

    waiting = _result(
        'b',
        runtime_ref=None,
        session_ref=None,
        binding_source=None,
    )  # binding 缺失 → waiting

    plan_a = AgentLaunchPlan(agent_name='d', launch_plan=None, fingerprint='fp', status='skipped')
    plan_result = PrecomputeResult(plans={'d': plan_a})

    evaluator = ReadyGateEvaluator(
        binding_check_fn=default_binding_check,
        provider_ready_fn=lambda _r: _ready_probe(),
        ping_fn=lambda _r: True,
    )
    gate = evaluator.evaluate(
        startup_results=[ready, waiting, failed],
        launch_plan_result=plan_result,
        target_order=['a', 'b', 'c', 'd'],
    )

    assert gate.per_agent['a'].state is AgentReadyState.AGENT_READY
    assert gate.per_agent['b'].state is AgentReadyState.AGENT_WAITING
    assert gate.per_agent['c'].state is AgentReadyState.AGENT_FAILED
    assert gate.per_agent['d'].state is AgentReadyState.AGENT_SKIPPED
    assert gate.all_ready is False


# =============================================================================
# 失败阶段区分 failure_reason
# =============================================================================


def test_failure_reason_distinguishes_stage() -> None:
    """启动失败按阶段区分 failure_reason。"""
    result = _result('agent9', action='failed', health='failed', failure_reason='stale_binding_unresolved')
    evaluator = ReadyGateEvaluator()
    gate = evaluator.evaluate(startup_results=[result], target_order=['agent9'])
    detail = gate.per_agent['agent9']
    assert detail.state is AgentReadyState.AGENT_FAILED
    assert detail.failure_reason == 'stale_binding_unresolved'
    assert 'agent9' in gate.failures


def test_result_missing_is_failed() -> None:
    """缺少 startup result 视为 failed。"""
    evaluator = ReadyGateEvaluator()
    gate = evaluator.evaluate(startup_results=[], target_order=['ghost'])
    assert gate.per_agent['ghost'].state is AgentReadyState.AGENT_FAILED
    assert gate.per_agent['ghost'].failure_reason == 'startup_result_missing'


# =============================================================================
# 全 ready
# =============================================================================


def test_all_ready_when_all_three_conditions_pass() -> None:
    """所有 agent 三条件全过 → all_ready=True。"""
    results = [_result('a'), _result('b')]
    evaluator = ReadyGateEvaluator(
        binding_check_fn=default_binding_check,
        provider_ready_fn=lambda _r: _ready_probe(),
        ping_fn=lambda _r: True,
    )
    gate = evaluator.evaluate(startup_results=results, target_order=['a', 'b'])
    assert gate.all_ready is True
    assert gate.total_ready_ms == 12.5  # max(12.5, 12.5)


def test_all_ready_false_on_any_not_ready() -> None:
    """任一 agent 未 ready → all_ready=False。"""
    # 构造一个 waiting：binding 缺失
    waiting = _result(
        'b',
        runtime_ref=None,
        session_ref=None,
        binding_source=None,
    )
    results = [_result('a'), waiting]
    evaluator = ReadyGateEvaluator(
        binding_check_fn=default_binding_check,
        provider_ready_fn=lambda _r: _ready_probe(),
        ping_fn=lambda _r: True,
    )
    gate = evaluator.evaluate(startup_results=results, target_order=['a', 'b'])
    assert gate.all_ready is False


# =============================================================================
# 度量
# =============================================================================


def test_to_record_flattens_states() -> None:
    """to_record 展开四类状态列表。"""
    ready = _result('a')
    waiting = _result(
        'b',
        runtime_ref=None,
        session_ref=None,
        binding_source=None,
    )
    failed = _result('c', action='failed', health='failed', failure_reason='x')
    evaluator = ReadyGateEvaluator(
        binding_check_fn=default_binding_check,
        provider_ready_fn=lambda _r: _ready_probe(),
        ping_fn=lambda _r: True,
    )
    gate = evaluator.evaluate(
        startup_results=[ready, waiting, failed],
        target_order=['a', 'b', 'c'],
    )
    record = gate.to_record()
    assert record['agent_ready'] == ['a']
    assert record['agent_waiting'] == ['b']
    assert record['agent_failed'] == ['c']


def test_empty_targets_not_all_ready() -> None:
    """空目标不视为 all_ready。"""
    evaluator = ReadyGateEvaluator()
    gate = evaluator.evaluate(startup_results=[], target_order=[])
    assert gate.all_ready is False


def test_probe_outcome_used_directly() -> None:
    """外部 probe_outcomes 直接被使用（provider_ready 条件）。"""
    result = _result('agent1')
    probe = HealthProbeOutcome(health_ok=True, ping_ok=True, health_label='healthy', probe_ms=2.0)
    evaluator = ReadyGateEvaluator(
        binding_check_fn=default_binding_check,
        # provider_ready_fn 不会被调用（用 probe）
        provider_ready_fn=lambda _r: HealthProbeOutcome(health_ok=False, ping_ok=False),
        ping_fn=lambda _r: False,
    )
    gate = evaluator.evaluate(
        startup_results=[result],
        target_order=['agent1'],
        probe_outcomes={'agent1': probe},
    )
    detail = gate.per_agent['agent1']
    assert detail.probe is probe
    assert detail.ping_succeeded is True
    assert detail.state is AgentReadyState.AGENT_READY