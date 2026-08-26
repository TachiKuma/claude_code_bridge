"""Launch Plan 预计算管线。

在运行时动作之前对目标 agent 做只读解析，产生每个 agent 的 LaunchPlan
对象。只读约束：不创建 provider home、不写 binding、不启动任何进程。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import monotonic_ns

from agents.config_identity import project_config_identity_payload
from agents.models_runtime.config import ProjectConfig
from workspace.planner import WorkspacePlanner

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


def _project_ctx(project_root: Path, project_id: str):
    """构建最小化的 ProjectContext 供 WorkspacePlanner.plan 使用。"""
    from types import SimpleNamespace

    return SimpleNamespace(
        project_root=project_root,
        project_id=project_id,
    )