"""Launch Plan 预计算管线。

在运行时动作之前对目标 agent 做只读解析，产生每个 agent 的 LaunchPlan
对象。只读约束：不创建 provider home、不写 binding、不启动任何进程。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from time import monotonic_ns

from agents.config_identity import project_config_identity_payload
from agents.models_runtime.config import ProjectConfig
from workspace.planner import WorkspacePlanner

from .cache import LaunchPlanCache
from .fingerprint import compute_launch_plan_fingerprint
from .models import (
    AgentLaunchPlan,
    AgentLaunchState,
    LaunchPlan,
    PrecomputeResult,
)


@dataclass(frozen=True)
class PrecomputeContext:
    """预计算所需的外部依赖注入。"""

    planner: object = WorkspacePlanner()


def precompute_launch_plans(
    *,
    targets: tuple[str, ...],
    config: ProjectConfig,
    project_root: Path,
    project_id: str,
    session_anchor: str | None = None,
    context: PrecomputeContext | None = None,
) -> PrecomputeResult:
    """对所有目标 agent 执行只读预计算，输出 PrecomputeResult。

    只读约束：
    - 不创建 provider home
    - 不写 binding
    - 不启动任何进程
    - 只解析 Project Config 和 inherited provider assets

    支持目标 agent 子集：targets 参数只计算指定 agent。
    """
    if context is None:
        context = PrecomputeContext()

    started_ns = monotonic_ns()
    plans: dict[str, AgentLaunchPlan] = {}

    for agent_name in targets:
        try:
            spec = config.agents[agent_name]
        except KeyError:
            plans[agent_name] = AgentLaunchPlan(
                agent_name=agent_name,
                launch_plan=None,
                fingerprint='',
                status='failed',
                error=f'unknown agent: {agent_name}',
            )
            continue

        try:
            plan = context.planner.plan(spec, _project_ctx(project_root, project_id))
        except Exception as exc:
            plans[agent_name] = AgentLaunchPlan(
                agent_name=agent_name,
                launch_plan=None,
                fingerprint='',
                status='failed',
                error=f'workspace planning failed: {exc}',
            )
            continue

        try:
            fingerprint = compute_launch_plan_fingerprint(
                agent_name,
                spec,
                plan,
                session_anchor=session_anchor,
            )
        except Exception as exc:
            plans[agent_name] = AgentLaunchPlan(
                agent_name=agent_name,
                launch_plan=None,
                fingerprint='',
                status='failed',
                error=f'fingerprint computation failed: {exc}',
            )
            continue

        provider_name = str(spec.provider).strip().lower()
        try:
            from provider_core.runtime_shared import provider_start_parts

            provider_entry = ' '.join(provider_start_parts(provider_name))
        except Exception:
            provider_entry = provider_name

        env_items = tuple(
            sorted(
                (str(key), str(value))
                for key, value in dict(getattr(spec, 'env', {}) or {}).items()
            )
        )
        profile = getattr(spec, 'provider_profile', None)
        if profile is not None:
            profile_env = dict(getattr(profile, 'env', {}) or {})
            env_items = tuple(
                dict.fromkeys(
                    list(env_items)
                    + sorted(
                        (str(k), str(v)) for k, v in profile_env.items()
                    )
                )
            )

        launch_plan = LaunchPlan(
            agent_name=agent_name,
            provider=provider_name,
            provider_entry=provider_entry,
            model=spec.model,
            thinking=spec.thinking,
            startup_args=tuple(spec.startup_args),
            workdir=str(plan.workspace_path),
            env=env_items,
            session_anchor=session_anchor or '',
            fingerprint=fingerprint,
        )

        plans[agent_name] = AgentLaunchPlan(
            agent_name=agent_name,
            launch_plan=launch_plan,
            fingerprint=fingerprint,
            status='ready',
        )

    elapsed_ms = (monotonic_ns() - started_ns) / 1_000_000
    return PrecomputeResult(
        plans=plans,
        timings_ms={'precompute_total': elapsed_ms},
    )


def precompute_with_cache(
    *,
    targets: tuple[str, ...],
    config: ProjectConfig,
    project_root: Path,
    project_id: str,
    session_anchor: str | None = None,
    context: PrecomputeContext | None = None,
    cache: LaunchPlanCache | None = None,
    skip_agent_targets: tuple[str, ...] | None = None,
) -> PrecomputeResult:
    """预计算管线 + 缓存逻辑。

    流程：
    1. 对每个 target，先查缓存（指纹匹配 → cache_hit）
    2. 缓存命中 → 使用缓存的 LaunchPlan
    3. 缓存未命中 → 执行全量预计算 → 写入缓存

    ``cache`` 为 None 时降级为纯预计算（无缓存）。
    ``skip_agent_targets`` 指定直接跳过预计算的 agent（不用缓存也不计算）。
    """
    if cache is None:
        return precompute_launch_plans(
            targets=targets,
            config=config,
            project_root=project_root,
            project_id=project_id,
            session_anchor=session_anchor,
            context=context,
        )

    started_ns = monotonic_ns()
    cached_plans: dict[str, AgentLaunchPlan] = {}
    compute_targets: list[str] = []
    skip_set = frozenset(str(name) for name in (skip_agent_targets or ()))

    # 阶段 1：对每个 agent 先查指纹（只读），缓存命中就不进入计算路径
    for agent_name in targets:
        if agent_name in skip_set:
            cached_plans[agent_name] = AgentLaunchPlan(
                agent_name=agent_name,
                launch_plan=None,
                fingerprint='',
                status='skipped',
                error='explicitly skipped',
            )
            cache.metrics.invalidation_count += 1  # 不计为失效，标记跳过
            continue

        try:
            spec = config.agents[agent_name]
        except KeyError:
            cached_plans[agent_name] = AgentLaunchPlan(
                agent_name=agent_name,
                launch_plan=None,
                fingerprint='',
                status='failed',
                error=f'unknown agent: {agent_name}',
            )
            continue

        try:
            plan = context.planner.plan(spec, _project_ctx(project_root, project_id))
        except Exception as exc:
            cached_plans[agent_name] = AgentLaunchPlan(
                agent_name=agent_name,
                launch_plan=None,
                fingerprint='',
                status='failed',
                error=f'workspace planning failed: {exc}',
            )
            continue

        try:
            fingerprint = compute_launch_plan_fingerprint(
                agent_name,
                spec,
                plan,
                session_anchor=session_anchor,
            )
        except Exception as exc:
            cached_plans[agent_name] = AgentLaunchPlan(
                agent_name=agent_name,
                launch_plan=None,
                fingerprint='',
                status='failed',
                error=f'fingerprint computation failed: {exc}',
            )
            continue

        cached_entry = cache.lookup(agent_name, fingerprint)
        if cached_entry is not None and cached_entry.plan_json != 'null':
            # 缓存命中：从缓存的 JSON 重建 LaunchPlan
            try:
                plan_data = json.loads(cached_entry.plan_json)
                launch_plan = _launch_plan_from_dict(plan_data, fingerprint=fingerprint)
                cached_plans[agent_name] = AgentLaunchPlan(
                    agent_name=agent_name,
                    launch_plan=launch_plan,
                    fingerprint=fingerprint,
                    status='ready',
                )
                continue
            except (json.JSONDecodeError, ValueError, TypeError):
                pass

        # 缓存未命中（或无效）：加入计算列表
        compute_targets.append(agent_name)
        # 暂存 spec 和 plan，避免重算
        cached_plans[agent_name] = _Placeholder(agent_name=agent_name, spec=spec, plan=plan, fingerprint=fingerprint)

    elapsed_ms_phase1 = (monotonic_ns() - started_ns) / 1_000_000

    # 阶段 2：对未命中缓存的 agent 执行全量预计算
    phase2_started_ns = monotonic_ns()
    if compute_targets:
        compute_result = precompute_launch_plans(
            targets=tuple(compute_targets),
            config=config,
            project_root=project_root,
            project_id=project_id,
            session_anchor=session_anchor,
            context=context,
        )
        for agent_name, agent_plan in compute_result.plans.items():
            cached_plans[agent_name] = agent_plan
            if agent_plan.status == 'ready' and agent_plan.launch_plan is not None:
                cache.write(
                    agent_name=agent_name,
                    fingerprint=agent_plan.fingerprint,
                    launch_plan=agent_plan.launch_plan,
                )
    elapsed_ms_phase2 = (monotonic_ns() - phase2_started_ns) / 1_000_000

    elapsed_ms = (monotonic_ns() - started_ns) / 1_000_000
    return PrecomputeResult(
        plans=_finalize_plans(cached_plans),
        timings_ms={
            'precompute_total': elapsed_ms,
            'precompute_cache_phase1': elapsed_ms_phase1,
            'precompute_cache_phase2': elapsed_ms_phase2,
        },
    )


class _Placeholder:
    """内部占位符，用于缓存未命中时暂存已计算的 spec/plan/fingerprint。"""

    def __init__(self, *, agent_name: str, spec, plan, fingerprint: str) -> None:
        self.agent_name = agent_name
        self.spec = spec
        self.plan = plan
        self.fingerprint = fingerprint


def _finalize_plans(plans: dict[str, object]) -> dict[str, AgentLaunchPlan]:
    """将占位符替换为实际 AgentLaunchPlan（降级为 failed）。"""
    result: dict[str, AgentLaunchPlan] = {}
    for name, plan in plans.items():
        if isinstance(plan, _Placeholder):
            result[name] = AgentLaunchPlan(
                agent_name=name,
                launch_plan=None,
                fingerprint=plan.fingerprint,
                status='failed',
                error='compute target was not resolved',
            )
        else:
            result[name] = plan
    return result


def _launch_plan_from_dict(data: dict[str, object], *, fingerprint: str) -> LaunchPlan:
    """从 JSON dict 重建 LaunchPlan。"""
    env_raw = data.get('env', [])
    env = tuple(
        (str(item[0]), str(item[1]))
        for item in env_raw
        if isinstance(item, (list, tuple)) and len(item) >= 2
    )
    return LaunchPlan(
        agent_name=str(data.get('agent_name', '') or ''),
        provider=str(data.get('provider', '') or ''),
        provider_entry=str(data.get('provider_entry', '') or ''),
        model=data.get('model') or None,
        thinking=data.get('thinking') or None,
        startup_args=tuple(str(a) for a in (data.get('startup_args') or ())),
        workdir=str(data.get('workdir', '') or ''),
        env=env,
        session_anchor=str(data.get('session_anchor', '') or ''),
        runtime_binding_expected=data.get('runtime_binding_expected'),
        fingerprint=fingerprint,
    )


def _project_ctx(project_root: Path, project_id: str):
    """构建最小化的 ProjectContext 供 WorkspacePlanner.plan 使用。"""
    from types import SimpleNamespace

    return SimpleNamespace(
        project_root=project_root,
        project_id=project_id,
    )