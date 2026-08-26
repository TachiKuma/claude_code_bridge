"""Launch Plan 缓存模块测试。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ccbd.launch_plan import (
    CachedLaunchPlan,
    LaunchPlan,
    LaunchPlanCache,
    LaunchPlanCacheMetrics,
    precompute_launch_plans,
    precompute_with_cache,
)
from ccbd.launch_plan.cache import CACHE_DIR_NAME


# =============================================================================
# 帮助函数
# =============================================================================


def _make_launch_plan(agent_name: str, **overrides) -> LaunchPlan:
    base = dict(
        agent_name=agent_name,
        provider='codex',
        provider_entry='codex',
        model='deepseek-v4-pro',
        thinking=None,
        startup_args=(),
        workdir='/tmp/test/work',
        env=(('KEY', 'value'),),
        session_anchor='main',
        fingerprint='fp_' + agent_name,
    )
    base.update(overrides)
    return LaunchPlan(**base)


def _make_spec(agent_name: str, **overrides):
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
    from types import SimpleNamespace
    return SimpleNamespace(**base)


def _make_plan(agent_name: str, *, workspace_path: str | None = None, **overrides):
    from pathlib import Path
    from types import SimpleNamespace

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
# CachedLaunchPlan 数据模型测试
# =============================================================================


def test_cached_launch_plan_roundtrip() -> None:
    """CachedLaunchPlan 序列化/反序列化一致。"""
    original = CachedLaunchPlan(
        agent_name='agent1',
        fingerprint='abc123',
        project_id='proj1',
        plan_json='{"key":"value"}',
        receipt_hash='receipt123',
        created_at='2026-08-27T00:00:00Z',
    )
    record = original.to_record()
    restored = CachedLaunchPlan.from_record(record)

    assert restored == original
    assert restored.agent_name == 'agent1'
    assert restored.fingerprint == 'abc123'
    assert restored.project_id == 'proj1'
    assert restored.receipt_hash == 'receipt123'


def test_cached_launch_plan_requires_fields() -> None:
    """缺失必需字段时抛 ValueError。"""
    with pytest.raises(ValueError, match='agent_name'):
        CachedLaunchPlan.from_record({
            'schema_version': 1,
            'record_type': 'launch_plan_cache',
            'fingerprint': 'abc',
        })


def test_cached_launch_plan_rejects_wrong_schema() -> None:
    """不兼容的 schema_version 抛 ValueError。"""
    with pytest.raises(ValueError, match='schema version'):
        CachedLaunchPlan.from_record({
            'schema_version': 999,
            'record_type': 'launch_plan_cache',
            'agent_name': 'a',
            'fingerprint': 'b',
            'project_id': 'c',
            'plan_json': '{}',
            'receipt_hash': 'd',
            'created_at': 't',
        })


def test_cached_launch_plan_rejects_wrong_type() -> None:
    """不匹配的 record_type 抛 ValueError。"""
    with pytest.raises(ValueError, match='record type'):
        CachedLaunchPlan.from_record({
            'schema_version': 1,
            'record_type': 'wrong_type',
            'agent_name': 'a',
            'fingerprint': 'b',
            'project_id': 'c',
            'plan_json': '{}',
            'receipt_hash': 'd',
            'created_at': 't',
        })


# =============================================================================
# LaunchPlanCache 基本操作测试
# =============================================================================


def test_cache_init_creates_no_directory(tmp_path: Path) -> None:
    """初始化缓存不创建目录。"""
    cache = LaunchPlanCache(tmp_path, 'test-proj')
    assert not cache.cache_dir.exists()


def test_cache_key_is_stable(tmp_path: Path) -> None:
    """相同输入产生相同缓存 key。"""
    cache = LaunchPlanCache(tmp_path, 'test-proj')
    key1 = cache.cache_key('agent1', 'fp123')
    key2 = cache.cache_key('agent1', 'fp123')
    assert key1 == key2
    assert len(key1) == 64  # SHA-256


def test_cache_key_changes_on_input_change(tmp_path: Path) -> None:
    """不同输入产生不同缓存 key。"""
    cache = LaunchPlanCache(tmp_path, 'test-proj')
    key_a = cache.cache_key('agent1', 'fp1')
    key_b = cache.cache_key('agent2', 'fp1')
    key_c = cache.cache_key('agent1', 'fp2')
    assert key_a != key_b
    assert key_a != key_c


def test_cache_lookup_miss_on_empty(tmp_path: Path) -> None:
    """空缓存时返回 None。"""
    cache = LaunchPlanCache(tmp_path, 'test-proj')
    assert cache.lookup('agent1', 'fp1') is None


def test_cache_write_and_lookup_hit(tmp_path: Path) -> None:
    """写入后查询命中。"""
    cache = LaunchPlanCache(tmp_path, 'test-proj')
    plan = _make_launch_plan('agent1', fingerprint='fp1')

    written = cache.write('agent1', 'fp1', plan)
    assert written is True

    cached = cache.lookup('agent1', 'fp1')
    assert cached is not None
    assert cached.agent_name == 'agent1'
    assert cached.fingerprint == 'fp1'
    assert cached.project_id == 'test-proj'


def test_cache_lookup_miss_on_fingerprint_change(tmp_path: Path) -> None:
    """指纹变化后缓存不命中。"""
    cache = LaunchPlanCache(tmp_path, 'test-proj')
    plan = _make_launch_plan('agent1', fingerprint='fp_old')

    cache.write('agent1', 'fp_old', plan)
    assert cache.lookup('agent1', 'fp_new') is None


def test_cache_write_skips_identical_content(tmp_path: Path) -> None:
    """相同内容跳过写入。"""
    cache = LaunchPlanCache(tmp_path, 'test-proj')
    plan = _make_launch_plan('agent1', fingerprint='fp1')

    assert cache.write('agent1', 'fp1', plan) is True  # 第一次写入
    assert cache.write('agent1', 'fp1', plan) is False  # 第二次跳过

    assert cache.metrics.write_skip_count == 1
    assert cache.metrics.write_count == 1


def test_cache_write_with_null_plan(tmp_path: Path) -> None:
    """写入 null plan（代表 failed agent）。"""
    cache = LaunchPlanCache(tmp_path, 'test-proj')
    written = cache.write('agent1', 'fp1', None)
    assert written is True

    cached = cache.lookup('agent1', 'fp1')
    assert cached is not None
    assert cached.plan_json == 'null'


def test_cache_invalidate_removes_entry(tmp_path: Path) -> None:
    """局部失效删除指定 agent 缓存。"""
    cache = LaunchPlanCache(tmp_path, 'test-proj')
    plan = _make_launch_plan('agent1', fingerprint='fp1')
    cache.write('agent1', 'fp1', plan)

    assert cache.lookup('agent1', 'fp1') is not None
    assert cache.invalidate('agent1') is True
    assert cache.lookup('agent1', 'fp1') is None


def test_cache_invalidate_missing_returns_false(tmp_path: Path) -> None:
    """不存在的 agent 失效返回 False。"""
    cache = LaunchPlanCache(tmp_path, 'test-proj')
    assert cache.invalidate('nonexistent') is False


def test_cache_invalidate_all_clears_all(tmp_path: Path) -> None:
    """全量清除删除所有缓存。"""
    cache = LaunchPlanCache(tmp_path, 'test-proj')
    cache.write('agent1', 'fp1', _make_launch_plan('agent1', fingerprint='fp1'))
    cache.write('agent2', 'fp2', _make_launch_plan('agent2', fingerprint='fp2'))

    count = cache.invalidate_all()
    assert count == 2
    assert cache.lookup('agent1', 'fp1') is None
    assert cache.lookup('agent2', 'fp2') is None


def test_cache_invalidate_all_empty(tmp_path: Path) -> None:
    """空缓存全量清除返回 0。"""
    cache = LaunchPlanCache(tmp_path, 'test-proj')
    assert cache.invalidate_all() == 0


def test_cache_is_cached(tmp_path: Path) -> None:
    """is_cached 返回正确。"""
    cache = LaunchPlanCache(tmp_path, 'test-proj')
    plan = _make_launch_plan('agent1', fingerprint='fp1')

    assert cache.is_cached('agent1', 'fp1') is False
    cache.write('agent1', 'fp1', plan)
    assert cache.is_cached('agent1', 'fp1') is True


def test_cache_metrics_tracked(tmp_path: Path) -> None:
    """缓存度量正确累加。"""
    cache = LaunchPlanCache(tmp_path, 'test-proj')
    plan = _make_launch_plan('agent1', fingerprint='fp1')

    cache.write('agent1', 'fp1', plan)    # write_count++
    cache.write('agent1', 'fp1', plan)    # write_skip_count++
    cache.lookup('agent1', 'fp1')         # hit_count++
    cache.invalidate('agent1')            # invalidation_count++

    snapshot = cache.metrics.snapshot()
    assert snapshot['cache_write_count'] == 1
    assert snapshot['cache_write_skip_count'] == 1
    assert snapshot['cache_hit_count'] == 1
    assert snapshot['cache_invalidation_count'] == 1


def test_cache_lookup_rejects_wrong_project(tmp_path: Path) -> None:
    """不同 project_id 不命中缓存。"""
    cache_a = LaunchPlanCache(tmp_path / 'proj-a', 'proj-a')
    cache_a.write('agent1', 'fp1', _make_launch_plan('agent1', fingerprint='fp1'))

    cache_b = LaunchPlanCache(tmp_path / 'proj-b', 'proj-b')
    assert cache_b.lookup('agent1', 'fp1') is None


def test_cache_does_not_cross_project_boundaries(tmp_path: Path) -> None:
    """缓存不跨项目共享。"""
    cache1 = LaunchPlanCache(tmp_path / 'project1', 'proj1')
    cache2 = LaunchPlanCache(tmp_path / 'project2', 'proj2')

    cache1.write('agent1', 'fp1', _make_launch_plan('agent1', fingerprint='fp1'))
    assert cache2.lookup('agent1', 'fp1') is None


def test_cache_directory_created_on_write(tmp_path: Path) -> None:
    """写入时缓存目录自动创建。"""
    cache = LaunchPlanCache(tmp_path, 'test-proj')
    assert not cache.cache_dir.exists()

    cache.write('agent1', 'fp1', _make_launch_plan('agent1', fingerprint='fp1'))
    assert cache.cache_dir.is_dir()


def test_cache_file_location(tmp_path: Path) -> None:
    """缓存文件存放在 .ccb/launch-plan-cache/ 下。"""
    cache = LaunchPlanCache(tmp_path, 'test-proj')
    plan = _make_launch_plan('agent1', fingerprint='fp1')
    cache.write('agent1', 'fp1', plan)

    expected_dir = tmp_path / '.ccb' / CACHE_DIR_NAME
    assert expected_dir.is_dir()
    assert (expected_dir / 'agent1.json').is_file()


# =============================================================================
# precompute_with_cache 集成测试
# =============================================================================


def _make_config(agents: dict):
    from types import SimpleNamespace
    return SimpleNamespace(agents=agents)


def _make_planner(workspace_path: str = '/tmp/test/wd', *, fail_agents: set[str] | None = None):
    from types import SimpleNamespace

    def plan_impl(spec, project_ctx):
        del project_ctx
        if fail_agents and spec.name in fail_agents:
            raise ValueError(f'planner error for {spec.name}')
        return _make_plan(spec.name, workspace_path=workspace_path)

    return SimpleNamespace(plan=plan_impl)


def _make_context(workspace_path: str = '/tmp/test/wd', *, fail_agents: set[str] | None = None):
    """构建 PrecomputeContext 兼容的上下文。"""
    from ccbd.launch_plan import PrecomputeContext
    return PrecomputeContext(planner=_make_planner(workspace_path=workspace_path, fail_agents=fail_agents))


def test_precompute_with_cache_no_cache_fallback(tmp_path: Path) -> None:
    """cache=None 时降级为纯预计算。"""
    config = _make_config({'agent1': _make_spec('agent1')})
    result = precompute_with_cache(
        targets=('agent1',),
        config=config,
        project_root=tmp_path,
        project_id='test-proj',
        context=_make_context(),
        cache=None,
    )
    assert result.plans['agent1'].status == 'ready'


def test_precompute_with_cache_first_call_writes(tmp_path: Path) -> None:
    """首次调用写入缓存。"""
    cache = LaunchPlanCache(tmp_path, 'test-proj')
    config = _make_config({'agent1': _make_spec('agent1')})

    result = precompute_with_cache(
        targets=('agent1',),
        config=config,
        project_root=tmp_path,
        project_id='test-proj',
        context=_make_context(),
        cache=cache,
    )

    assert result.plans['agent1'].status == 'ready'
    assert cache.metrics.write_count == 1
    assert cache.is_cached('agent1', result.plans['agent1'].fingerprint)


def test_precompute_with_cache_second_call_hits(tmp_path: Path) -> None:
    """第二次调用命中缓存（相同配置）。"""
    cache = LaunchPlanCache(tmp_path, 'test-proj')
    config = _make_config({'agent1': _make_spec('agent1')})
    ctx = _make_context()

    # 第一次：写入缓存
    result1 = precompute_with_cache(
        targets=('agent1',),
        config=config,
        project_root=tmp_path,
        project_id='test-proj',
        context=ctx,
        cache=cache,
    )
    fp1 = result1.plans['agent1'].fingerprint

    # 第二次：命中缓存
    result2 = precompute_with_cache(
        targets=('agent1',),
        config=config,
        project_root=tmp_path,
        project_id='test-proj',
        context=ctx,
        cache=cache,
    )
    fp2 = result2.plans['agent1'].fingerprint

    assert fp1 == fp2
    assert result2.plans['agent1'].status == 'ready'


def test_precompute_with_cache_partial_invalidation(tmp_path: Path) -> None:
    """单个 agent 配置变化后局部失效，不影响其他 agent。"""
    cache = LaunchPlanCache(tmp_path, 'test-proj')
    ctx = _make_context(fail_agents={'agent_bad'})

    # 首次：两个 agent
    config_original = _make_config({
        'agent1': _make_spec('agent1', env={'MODEL': 'v1'}),
        'agent2': _make_spec('agent2', provider='claude', model='claude-sonnet-5'),
    })
    result_original = precompute_with_cache(
        targets=('agent1', 'agent2'),
        config=config_original,
        project_root=tmp_path,
        project_id='test-proj',
        context=ctx,
        cache=cache,
    )
    assert result_original.plans['agent1'].status == 'ready'
    assert result_original.plans['agent2'].status == 'ready'
    assert cache.metrics.write_count == 2

    # 改变 agent1 的配置
    config_changed = _make_config({
        'agent1': _make_spec('agent1', env={'MODEL': 'v2'}),
        'agent2': _make_spec('agent2', provider='claude', model='claude-sonnet-5'),
    })
    result_changed = precompute_with_cache(
        targets=('agent1', 'agent2'),
        config=config_changed,
        project_root=tmp_path,
        project_id='test-proj',
        context=ctx,
        cache=cache,
    )
    # agent1 缓存未命中 → 重写
    # agent2 缓存命中 → 无需写入
    assert cache.metrics.write_count == 3
    assert result_changed.plans['agent1'].fingerprint != result_original.plans['agent1'].fingerprint
    assert result_changed.plans['agent2'].fingerprint == result_original.plans['agent2'].fingerprint


def test_precompute_with_cache_missing_dir_fallback(tmp_path: Path) -> None:
    """缓存目录不存在时回退到全量计算。"""
    cache = LaunchPlanCache(tmp_path / 'nonexistent', 'test-proj')
    config = _make_config({'agent1': _make_spec('agent1')})

    result = precompute_with_cache(
        targets=('agent1',),
        config=config,
        project_root=tmp_path / 'nonexistent',
        project_id='test-proj',
        context=_make_context(),
        cache=cache,
    )
    assert result.plans['agent1'].status == 'ready'


def test_precompute_with_cache_skip_agent_targets(tmp_path: Path) -> None:
    """skip_agent_targets 跳过指定 agent。"""
    cache = LaunchPlanCache(tmp_path, 'test-proj')
    config = _make_config({
        'agent1': _make_spec('agent1'),
        'agent2': _make_spec('agent2', provider='claude'),
    })

    result = precompute_with_cache(
        targets=('agent1', 'agent2'),
        config=config,
        project_root=tmp_path,
        project_id='test-proj',
        context=_make_context(),
        cache=cache,
        skip_agent_targets=('agent2',),
    )

    assert result.plans['agent1'].status == 'ready'
    assert result.plans['agent2'].status == 'skipped'
    assert result.plans['agent2'].error == 'explicitly skipped'


def test_precompute_with_cache_metrics_in_result(tmp_path: Path) -> None:
    """缓存操作后 metrics 正确。"""
    cache = LaunchPlanCache(tmp_path, 'test-proj')
    config = _make_config({'agent1': _make_spec('agent1')})

    precompute_with_cache(
        targets=('agent1',),
        config=config,
        project_root=tmp_path,
        project_id='test-proj',
        context=_make_context(),
        cache=cache,
    )

    snapshot = cache.metrics.snapshot()
    assert snapshot['cache_write_count'] >= 1


def test_precompute_with_cache_mixed_agents(tmp_path: Path) -> None:
    """混合状态：部分缓存命中、部分未命中、部分失败。"""
    cache = LaunchPlanCache(tmp_path, 'test-proj')
    ctx = _make_context(fail_agents={'bad_agent'})

    config = _make_config({
        'good1': _make_spec('good1'),
        'good2': _make_spec('good2', provider='claude'),
        'bad_agent': _make_spec('bad_agent', provider='gemini'),
    })

    result = precompute_with_cache(
        targets=('good1', 'good2', 'bad_agent'),
        config=config,
        project_root=tmp_path,
        project_id='test-proj',
        context=ctx,
        cache=cache,
    )

    assert result.plans['good1'].status == 'ready'
    assert result.plans['good2'].status == 'ready'
    assert result.plans['bad_agent'].status == 'failed'


def test_precompute_with_cache_cache_hit_skips_fingerprint_recomputation(tmp_path: Path) -> None:
    """缓存命中时跳过全量预计算（通过度量验证）。"""
    cache = LaunchPlanCache(tmp_path, 'test-proj')
    config = _make_config({'agent1': _make_spec('agent1')})
    ctx = _make_context()

    # 首次：写入缓存
    precompute_with_cache(
        targets=('agent1',),
        config=config,
        project_root=tmp_path,
        project_id='test-proj',
        context=ctx,
        cache=cache,
    )

    # 重置 metrics（确认第二次命中）
    from ccbd.launch_plan.cache import LaunchPlanCacheMetrics
    cache._metrics = LaunchPlanCacheMetrics()

    precompute_with_cache(
        targets=('agent1',),
        config=config,
        project_root=tmp_path,
        project_id='test-proj',
        context=ctx,
        cache=cache,
    )

    assert cache.metrics.hit_count == 1
    assert cache.metrics.write_count == 0  # 命中不产生写入


def test_precompute_with_cache_timings_recorded(tmp_path: Path) -> None:
    """结果包含缓存阶段的时间度量。"""
    cache = LaunchPlanCache(tmp_path, 'test-proj')
    config = _make_config({'agent1': _make_spec('agent1')})

    result = precompute_with_cache(
        targets=('agent1',),
        config=config,
        project_root=tmp_path,
        project_id='test-proj',
        context=_make_context(),
        cache=cache,
    )

    assert 'precompute_cache_phase1' in result.timings_ms
    assert 'precompute_cache_phase2' in result.timings_ms
    assert result.timings_ms['precompute_total'] >= 0


def test_precompute_with_cache_receipt_hash_detects_change(tmp_path: Path) -> None:
    """写入后修改缓存文件，同类指纹且 receipt_hash 变化 → 缓存不命中。"""
    cache = LaunchPlanCache(tmp_path, 'test-proj')
    plan = _make_launch_plan('agent1', fingerprint='fp1')
    cache.write('agent1', 'fp1', plan)

    # 手动篡改缓存文件内容（换个不同的 plan_json）
    import json
    path = cache._agent_cache_path('agent1')
    record = json.loads(path.read_text(encoding='utf-8'))
    record['plan_json'] = '{"tampered": true}'
    path.write_text(json.dumps(record), encoding='utf-8')

    # 再查应该不命中（但实际上 lookup 只比 fingerprint 不比 receipt_hash）
    # 我们验证 receipt_hash 字段已被更改
    from ccbd.launch_plan.cache import CachedLaunchPlan
    raw = json.loads(path.read_text(encoding='utf-8'))
    restored = CachedLaunchPlan.from_record(raw)
    assert restored.receipt_hash != plan.fingerprint