"""Launch Plan 预计算管线测试。"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from ccbd.launch_plan import (
    AgentLaunchPlan,
    LaunchPlan,
    PrecomputeResult,
    compute_launch_plan_fingerprint,
    fingerprints_equal,
    precompute_launch_plans,
)


def _make_spec(agent_name: str, **overrides) -> SimpleNamespace:
    """便捷构建最小 AgentSpec 存根。"""
    base = dict(
        name=agent_name,
        provider='codex',
        target='.',
        workspace_mode='inplace',
        workspace_root=None,
        workspace_path=None,
        workspace_group=None,
        runtime_mode='v2',
        restore_default='auto',
        permission_default='manual',
        queue_policy='fifo',
        model='deepseek-v4-pro',
        thinking=None,
        startup_args=(),
        env={},
        provider_command_template=None,
        branch_template=None,
        labels=(),
        description=None,
        role=None,
        watch_paths=(),
        dispatch_disabled=False,
        provider_profile=None,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _make_plan(
    agent_name: str,
    *,
    workspace_path: str | None = None,
    **overrides,
) -> SimpleNamespace:
    """便捷构建最小 WorkspacePlan 存根。"""
    base = dict(
        project_id='test-proj',
        project_root=Path('/tmp/test'),
        project_slug='test',
        agent_name=agent_name,
        workspace_mode='inplace',
        workspace_path=Path(workspace_path or '/tmp/test/workspace'),
        binding_path=None,
        source_root=Path('/tmp/test'),
        branch_name=None,
        branch_template=None,
        unsafe_shared_workspace=False,
        workspace_scope='agent',
    )
    base.update(overrides)
    return SimpleNamespace(**base)


# =============================================================================
# 数据模型测试
# =============================================================================


def test_launch_plan_is_frozen() -> None:
    """LaunchPlan 应冻结不可变。"""
    plan = LaunchPlan(
        agent_name='agent1',
        provider='codex',
        provider_entry='codex',
        model='deepseek-v4-pro',
        thinking=None,
        startup_args=(),
        workdir='/tmp/test',
        env=(),
        session_anchor='main',
        runtime_binding_expected=None,
        fingerprint='abc123',
    )
    assert plan.agent_name == 'agent1'
    assert plan.provider == 'codex'
    assert plan.fingerprint == 'abc123'
    assert plan.runtime_binding_expected is None


def test_agent_launch_plan_ready() -> None:
    """AgentLaunchPlan 正常就绪状态。"""
    plan = AgentLaunchPlan(
        agent_name='agent1',
        launch_plan=_dummy_launch_plan('agent1'),
        fingerprint='fp123',
        status='ready',
        error=None,
    )
    assert plan.status == 'ready'
    assert plan.error is None
    assert plan.launch_plan is not None


def test_agent_launch_plan_failed() -> None:
    """AgentLaunchPlan 失败状态。"""
    plan = AgentLaunchPlan(
        agent_name='unknown_agent',
        launch_plan=None,
        fingerprint='',
        status='failed',
        error='unknown agent',
    )
    assert plan.status == 'failed'
    assert plan.error == 'unknown agent'
    assert plan.launch_plan is None


def test_agent_launch_plan_skipped() -> None:
    """AgentLaunchPlan 跳过状态。"""
    plan = AgentLaunchPlan(
        agent_name='agent1',
        launch_plan=None,
        fingerprint='',
        status='skipped',
    )
    assert plan.status == 'skipped'


def test_precompute_result_aggregation() -> None:
    """PrecomputeResult 聚合多个 agent 计划。"""
    plans = {
        'agent1': AgentLaunchPlan(agent_name='agent1', launch_plan=_dummy_launch_plan('agent1'), fingerprint='fp1', status='ready'),
        'agent2': AgentLaunchPlan(agent_name='agent2', launch_plan=_dummy_launch_plan('agent2'), fingerprint='fp2', status='ready'),
    }
    result = PrecomputeResult(plans=plans, timings_ms={'precompute_total': 12.5})
    assert len(result.plans) == 2
    assert result.plans['agent1'].fingerprint == 'fp1'
    assert result.plans['agent2'].fingerprint == 'fp2'
    assert result.timings_ms['precompute_total'] == 12.5


# =============================================================================
# 指纹计算测试
# =============================================================================


def test_fingerprint_stable_for_same_config() -> None:
    """相同配置产生相同指纹。"""
    spec = _make_spec('agent1', startup_args=('--verbose',), env={'KEY': 'value'})
    plan = _make_plan('agent1', workspace_path='/tmp/test/work')

    fp1 = compute_launch_plan_fingerprint('agent1', spec, plan, session_anchor='main')
    fp2 = compute_launch_plan_fingerprint('agent1', spec, plan, session_anchor='main')

    assert fp1 == fp2
    assert len(fp1) == 64  # SHA-256 hex


def test_fingerprint_changes_when_config_changes() -> None:
    """配置变化产生不同指纹。"""
    spec_a = _make_spec('agent1', model='deepseek-v4-pro')
    spec_b = _make_spec('agent1', model='deepseek-v4-flash')
    plan = _make_plan('agent1')

    fp_a = compute_launch_plan_fingerprint('agent1', spec_a, plan, session_anchor='main')
    fp_b = compute_launch_plan_fingerprint('agent1', spec_b, plan, session_anchor='main')

    assert fp_a != fp_b


def test_fingerprint_ignores_timestamp() -> None:
    """相同配置不同 timestamp 产生相同指纹。"""
    spec = _make_spec('agent1')
    plan = _make_plan('agent1')

    fp1 = compute_launch_plan_fingerprint('agent1', spec, plan, session_anchor='main')
    fp2 = compute_launch_plan_fingerprint('agent1', spec, plan, session_anchor='main')

    assert fp1 == fp2


def test_fingerprint_changes_on_env_change() -> None:
    """env 变化产生不同指纹。"""
    spec_a = _make_spec('agent1', env={'KEY': 'value1'})
    spec_b = _make_spec('agent1', env={'KEY': 'value2'})
    plan = _make_plan('agent1')

    fp_a = compute_launch_plan_fingerprint('agent1', spec_a, plan, session_anchor='main')
    fp_b = compute_launch_plan_fingerprint('agent1', spec_b, plan, session_anchor='main')

    assert fp_a != fp_b


def test_fingerprint_changes_on_startup_args_change() -> None:
    """startup_args 变化产生不同指纹。"""
    spec_a = _make_spec('agent1', startup_args=('--mode=a',))
    spec_b = _make_spec('agent1', startup_args=('--mode=b',))
    plan = _make_plan('agent1')

    fp_a = compute_launch_plan_fingerprint('agent1', spec_a, plan, session_anchor='main')
    fp_b = compute_launch_plan_fingerprint('agent1', spec_b, plan, session_anchor='main')

    assert fp_a != fp_b


def test_fingerprint_changes_on_session_anchor() -> None:
    """session_anchor 变化产生不同指纹。"""
    spec = _make_spec('agent1')
    plan = _make_plan('agent1')

    fp_a = compute_launch_plan_fingerprint('agent1', spec, plan, session_anchor='main')
    fp_b = compute_launch_plan_fingerprint('agent1', spec, plan, session_anchor='review')

    assert fp_a != fp_b


def test_fingerprint_changes_on_workdir_change() -> None:
    """workdir 变化产生不同指纹。"""
    spec = _make_spec('agent1')
    plan_a = _make_plan('agent1', workspace_path='/tmp/work1')
    plan_b = _make_plan('agent1', workspace_path='/tmp/work2')

    fp_a = compute_launch_plan_fingerprint('agent1', spec, plan_a, session_anchor='main')
    fp_b = compute_launch_plan_fingerprint('agent1', spec, plan_b, session_anchor='main')

    assert fp_a != fp_b


def test_fingerprint_ignores_plan_unsafe_shared() -> None:
    """unsafe_shared_workspace 不影响指纹。"""
    spec = _make_spec('agent1')
    plan_a = _make_plan('agent1', unsafe_shared_workspace=True)
    plan_b = _make_plan('agent1', unsafe_shared_workspace=False)

    fp_a = compute_launch_plan_fingerprint('agent1', spec, plan_a, session_anchor='main')
    fp_b = compute_launch_plan_fingerprint('agent1', spec, plan_b, session_anchor='main')

    assert fp_a == fp_b


def test_fingerprints_equal_constant_time() -> None:
    """指纹恒定时间比较。"""
    assert fingerprints_equal('abc', 'abc') is True
    assert fingerprints_equal('abc', 'def') is False
    assert fingerprints_equal('', '') is True
    assert fingerprints_equal('abc', '') is False


def test_fingerprints_equal_non_string() -> None:
    """非字符串输入返回 False。"""
    assert fingerprints_equal(None, 'abc') is False  # type: ignore[arg-type]
    assert fingerprints_equal('abc', None) is False  # type: ignore[arg-type]
    assert fingerprints_equal(123, 'abc') is False  # type: ignore[arg-type]


# =============================================================================
# 预计算管线测试
# =============================================================================


def test_precompute_plans_for_single_agent() -> None:
    """预计算管线正常处理单个 agent。"""
    project_root = Path('/tmp/test-proj')
    config = SimpleNamespace(
        agents={
            'agent1': _make_spec('agent1', env={'API_KEY': 'sk-test'}),
        },
    )
    planner = _make_planner(Path('/tmp/test-proj/workspace'))

    result = precompute_launch_plans(
        targets=('agent1',),
        config=config,
        project_root=project_root,
        project_id='test-proj',
        session_anchor='main',
        context=SimpleNamespace(planner=planner),
    )

    assert 'agent1' in result.plans
    plan = result.plans['agent1']
    assert plan.status == 'ready'
    assert plan.launch_plan is not None
    assert plan.launch_plan.agent_name == 'agent1'
    assert plan.launch_plan.provider == 'codex'
    assert plan.launch_plan.fingerprint != ''
    assert plan.launch_plan.env == (('API_KEY', 'sk-test'),)
    assert plan.launch_plan.session_anchor == 'main'


def test_precompute_plans_for_subset_of_agents() -> None:
    """预计算管线支持只计算指定 subset。"""
    project_root = Path('/tmp/test-proj')
    config = SimpleNamespace(
        agents={
            'agent1': _make_spec('agent1'),
            'agent2': _make_spec('agent2', provider='claude', model='claude-sonnet-5'),
            'agent3': _make_spec('agent3', provider='gemini'),
        },
    )

    def planner_impl(spec, project_ctx):
        del project_ctx
        return _make_plan(spec.name, workspace_path=f'/tmp/wd/{spec.name}')

    planner = SimpleNamespace(plan=planner_impl)

    result = precompute_launch_plans(
        targets=('agent1', 'agent3'),
        config=config,
        project_root=project_root,
        project_id='test-proj',
        session_anchor='main',
        context=SimpleNamespace(planner=planner),
    )

    assert 'agent1' in result.plans
    assert 'agent3' in result.plans
    assert 'agent2' not in result.plans
    assert result.plans['agent1'].status == 'ready'
    assert result.plans['agent3'].status == 'ready'


def test_precompute_fails_for_unknown_agent() -> None:
    """未知 agent 返回 failed 状态。"""
    config = SimpleNamespace(agents={})

    result = precompute_launch_plans(
        targets=('unknown_agent',),
        config=config,
        project_root=Path('/tmp'),
        project_id='test',
    )

    assert 'unknown_agent' in result.plans
    assert result.plans['unknown_agent'].status == 'failed'
    assert result.plans['unknown_agent'].error is not None
    assert 'unknown agent' in result.plans['unknown_agent'].error


def test_precompute_fails_for_failing_planner() -> None:
    """planner 异常时返回 failed 状态，不影响其他 agent。"""
    project_root = Path('/tmp/test-proj')
    config = SimpleNamespace(
        agents={
            'agent_ok': _make_spec('agent_ok'),
            'agent_bad': _make_spec('agent_bad'),
        },
    )

    call_count: int = 0

    def planner_impl(spec, project_ctx):
        nonlocal call_count
        del project_ctx
        call_count += 1
        if spec.name == 'agent_bad':
            raise ValueError('bad workspace config')
        return _make_plan(spec.name, workspace_path=f'/tmp/wd/{spec.name}')

    planner = SimpleNamespace(plan=planner_impl)

    result = precompute_launch_plans(
        targets=('agent_bad', 'agent_ok'),
        config=config,
        project_root=project_root,
        project_id='test',
        context=SimpleNamespace(planner=planner),
    )

    assert result.plans['agent_bad'].status == 'failed'
    assert 'bad workspace config' in result.plans['agent_bad'].error
    assert result.plans['agent_ok'].status == 'ready'
    assert result.plans['agent_ok'].launch_plan is not None


def test_precompute_is_read_only_no_side_effects(tmp_path: Path) -> None:
    """预计算管线不写入任何文件、不创建目录。"""
    project_root = tmp_path / 'read-only-test'
    project_root.mkdir()
    config = SimpleNamespace(
        agents={
            'agent1': _make_spec('agent1'),
        },
    )

    def planner_impl(spec, project_ctx):
        del project_ctx
        return _make_plan(spec.name, workspace_path='/tmp/nonexistent')

    planner = SimpleNamespace(plan=planner_impl)

    original_files = {str(p) for p in project_root.rglob('*')}

    result = precompute_launch_plans(
        targets=('agent1',),
        config=config,
        project_root=project_root,
        project_id='test',
        context=SimpleNamespace(planner=planner),
    )

    after_files = {str(p) for p in project_root.rglob('*')}
    assert after_files == original_files
    assert result.plans['agent1'].status == 'ready'


def test_precompute_mixed_status_agents() -> None:
    """多个 agent 混合状态结果保留各自的 status。"""
    project_root = Path('/tmp/test-proj')
    call_count: int = 0

    def planner_impl(spec, project_ctx):
        nonlocal call_count
        del project_ctx
        call_count += 1
        if spec.name == 'bad':
            raise RuntimeError('planner error')
        return _make_plan(spec.name, workspace_path=f'/tmp/wd/{spec.name}')

    config = SimpleNamespace(
        agents={
            'good': _make_spec('good', provider='claude'),
            'bad': _make_spec('bad', provider='codex'),
            'skipped_target': _make_spec('skipped_target', provider='gemini'),
        },
    )

    result = precompute_launch_plans(
        targets=('good', 'bad'),
        config=config,
        project_root=project_root,
        project_id='test',
        session_anchor='main',
        context=SimpleNamespace(planner=SimpleNamespace(plan=planner_impl)),
    )

    assert result.plans['good'].status == 'ready'
    assert result.plans['bad'].status == 'failed'
    assert 'skipped_target' not in result.plans


def test_precompute_timings_included() -> None:
    """结果包含时间度量。"""
    config = SimpleNamespace(
        agents={'agent1': _make_spec('agent1')},
    )

    result = precompute_launch_plans(
        targets=('agent1',),
        config=config,
        project_root=Path('/tmp'),
        project_id='test',
        context=SimpleNamespace(planner=SimpleNamespace(plan=lambda spec, ctx: _make_plan(spec.name))),
    )

    assert 'precompute_total' in result.timings_ms
    assert result.timings_ms['precompute_total'] >= 0


def test_precompute_fingerprint_stable_across_calls() -> None:
    """相同输入的多次预计算产生相同指纹。"""
    project_root = Path('/tmp/test-proj')
    config = SimpleNamespace(
        agents={
            'agent1': _make_spec('agent1', env={'KEY': 'stable'}),
        },
    )

    def planner_impl(spec, project_ctx):
        del project_ctx
        return _make_plan(spec.name, workspace_path='/tmp/wd/agent1')

    planner = SimpleNamespace(plan=planner_impl)

    result1 = precompute_launch_plans(
        targets=('agent1',),
        config=config,
        project_root=project_root,
        project_id='test',
        session_anchor='main',
        context=SimpleNamespace(planner=planner),
    )
    result2 = precompute_launch_plans(
        targets=('agent1',),
        config=config,
        project_root=project_root,
        project_id='test',
        session_anchor='main',
        context=SimpleNamespace(planner=planner),
    )

    fp1 = result1.plans['agent1'].fingerprint
    fp2 = result2.plans['agent1'].fingerprint
    assert fp1 == fp2
    assert len(fp1) == 64


def test_precompute_with_provider_profile_env() -> None:
    """provider_profile.env 纳入 LaunchPlan env。"""
    project_root = Path('/tmp/test-proj')

    profile = SimpleNamespace(
        mode='inherit',
        home=None,
        env={'PROFILE_KEY': 'profile_val'},
        mcp_servers={},
        plugins={},
        inherit_api=True,
        inherit_auth=True,
        inherit_config=True,
        inherit_skills=True,
        inherit_commands=True,
        inherit_memory=True,
        inherited_skill_include=(),
        inherited_skill_exclude=(),
        skill_overlays={},
    )
    spec = _make_spec('agent1', env={'AGENT_KEY': 'agent_val'}, provider_profile=profile)

    config = SimpleNamespace(agents={'agent1': spec})

    result = precompute_launch_plans(
        targets=('agent1',),
        config=config,
        project_root=project_root,
        project_id='test',
        session_anchor='main',
        context=SimpleNamespace(
            planner=SimpleNamespace(
                plan=lambda spec, ctx: _make_plan(spec.name, workspace_path='/tmp/wd/a1'),
            ),
        ),
    )

    env_items = result.plans['agent1'].launch_plan.env
    env_dict = dict(env_items)
    assert 'AGENT_KEY' in env_dict
    assert 'PROFILE_KEY' in env_dict


# =============================================================================
# 帮助函数
# =============================================================================


def _dummy_launch_plan(agent_name: str) -> LaunchPlan:
    return LaunchPlan(
        agent_name=agent_name,
        provider='codex',
        provider_entry='codex',
        model='deepseek-v4-pro',
        thinking=None,
        startup_args=(),
        workdir='/tmp/test',
        env=(),
        session_anchor='main',
        fingerprint='dummy',
    )


def _make_planner(
    default_workspace_path: Path | str = '/tmp/test/workspace',
) -> SimpleNamespace:
    def planner_impl(spec, project_ctx):
        del project_ctx
        return _make_plan(spec.name, workspace_path=str(default_workspace_path))

    return SimpleNamespace(plan=planner_impl)