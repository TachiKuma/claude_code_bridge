from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class LaunchPlan:
    """单个 agent 启动所需的可验证输入集合。

    属性均为稳定输入字段，不包含 timestamp、seq 等运行时状态。
    用于 ready gate、缓存 key 和并发控制消费。
    """

    agent_name: str
    provider: str
    provider_entry: str
    model: str | None
    thinking: str | None
    startup_args: tuple[str, ...]
    workdir: str
    env: tuple[tuple[str, str], ...]
    session_anchor: str
    runtime_binding_expected: dict[str, object] | None = None
    fingerprint: str = ''


AgentLaunchState = Literal['ready', 'failed', 'skipped']


@dataclass(frozen=True)
class AgentLaunchPlan:
    """单个 agent 的预计算结果。"""

    agent_name: str
    launch_plan: LaunchPlan | None
    fingerprint: str
    status: AgentLaunchState
    error: str | None = None


@dataclass(frozen=True)
class PrecomputeResult:
    """预计算管线输出。"""

    plans: dict[str, AgentLaunchPlan]
    timings_ms: dict[str, float] = field(default_factory=dict)