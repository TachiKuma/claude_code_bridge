"""LaunchPlan 输入指纹计算。

指纹覆盖项目配置中影响启动结果的所有稳定输入字段，
忽略运行时状态（timestamp、seq 等）。"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from pathlib import Path

from agents.models_runtime.config_runtime.spec import AgentSpec
from provider_core.runtime_shared import provider_start_parts
from workspace.models import WorkspacePlan


def compute_launch_plan_fingerprint(
    agent_name: str,
    spec: AgentSpec,
    plan: WorkspacePlan,
    *,
    session_anchor: str | None = None,
    runtime_dir: Path | None = None,
) -> str:
    """根据稳定输入字段计算 LaunchPlan 指纹。

    指纹覆盖：provider 入口、model、startup_args、env、workdir、session 锚点。
    忽略：timestamp、seq_id、运行时状态。
    """
    # provider 入口：按规范化的 provider 启动命令片段计算
    provider_name = str(spec.provider).strip().lower()
    try:
        provider_parts = provider_start_parts(provider_name)
    except Exception:
        provider_parts = [provider_name]

    # 环境：规范化排序
    env_items = sorted(
        (str(key), str(value))
        for key, value in dict(getattr(spec, 'env', {}) or {}).items()
    )
    # provider profile env 也纳入
    profile = getattr(spec, 'provider_profile', None)
    if profile is not None:
        profile_env = dict(getattr(profile, 'env', {}) or {})
        env_items.extend(
            sorted(
                (str(key), str(value))
                for key, value in profile_env.items()
            )
        )

    payload: dict[str, object] = {
        'agent_name': agent_name,
        'provider': provider_name,
        'provider_entry': tuple(provider_parts),
        'model': spec.model,
        'thinking': spec.thinking,
        'startup_args': tuple(spec.startup_args),
        'workdir': str(plan.workspace_path),
        'env': tuple(dict.fromkeys(env_items)),  # 去重保留首条
        'session_anchor': session_anchor or '',
        'workspace_mode': getattr(spec, 'workspace_mode', None),
        'runtime_mode': getattr(spec, 'runtime_mode', None),
    }

    raw = json.dumps(payload, sort_keys=True, ensure_ascii=True, default=str)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def fingerprints_equal(a: str, b: str) -> bool:
    """恒定时间比较两个指纹。"""
    if not isinstance(a, str) or not isinstance(b, str):
        return False
    return hashlib.sha256(a.encode('utf-8')).hexdigest() == hashlib.sha256(
        b.encode('utf-8')
    ).hexdigest()