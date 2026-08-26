"""Ready Gate 结果模型。

定义 Agent Ready 判定所需的枚举、探针结果、单 agent 详情与聚合结果。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class AgentReadyState(Enum):
    """单个 agent 的 ready gate 最终状态。"""

    AGENT_READY = 'agent_ready'
    AGENT_WAITING = 'agent_waiting'
    AGENT_FAILED = 'agent_failed'
    AGENT_SKIPPED = 'agent_skipped'


@dataclass(frozen=True)
class HealthProbeOutcome:
    """provider 入口就绪与 ping 探测结果。"""

    health_ok: bool
    ping_ok: bool
    health_label: str | None = None
    probe_ms: float = 0.0

    def to_record(self) -> dict[str, object]:
        return {
            'health_ok': self.health_ok,
            'ping_ok': self.ping_ok,
            'health_label': self.health_label,
            'probe_ms': self.probe_ms,
        }


@dataclass(frozen=True)
class AgentReadyDetail:
    """单个 agent 的 ready gate 详情。"""

    agent_name: str
    state: AgentReadyState
    binding_verified: bool
    provider_ready: bool
    ping_succeeded: bool
    failure_reason: str | None
    binding_evidence: tuple[str, ...]
    ready_ms: float | None = None
    concurrency_wait_ms: float = 0.0
    probe: HealthProbeOutcome | None = None

    def to_record(self) -> dict[str, object]:
        return {
            'agent_name': self.agent_name,
            'state': self.state.value,
            'binding_verified': self.binding_verified,
            'provider_ready': self.provider_ready,
            'ping_succeeded': self.ping_succeeded,
            'failure_reason': self.failure_reason,
            'binding_evidence': list(self.binding_evidence),
            'ready_ms': self.ready_ms,
            'concurrency_wait_ms': self.concurrency_wait_ms,
            'probe': self.probe.to_record() if self.probe is not None else None,
        }


@dataclass(frozen=True)
class ConcurrencyObservation:
    """受限并发观测。"""

    max_workers: int
    total_agents: int
    measured_peak_in_flight: int
    concurrency_wait_ms: float = 0.0

    def to_record(self) -> dict[str, object]:
        return {
            'max_workers': self.max_workers,
            'total_agents': self.total_agents,
            'measured_peak_in_flight': self.measured_peak_in_flight,
            'concurrency_wait_ms': self.concurrency_wait_ms,
        }


@dataclass(frozen=True)
class AllReadyResult:
    """Ready Gate 聚合结果。"""

    all_ready: bool
    per_agent: dict[str, AgentReadyDetail]
    total_ready_ms: float | None = None
    per_agent_ms: dict[str, float] = field(default_factory=dict)
    stage_timings_ms: dict[str, float] = field(default_factory=dict)
    concurrency: ConcurrencyObservation | None = None
    failures: dict[str, str] = field(default_factory=dict)

    def to_record(self) -> dict[str, object]:
        return {
            'all_ready': self.all_ready,
            'per_agent': {
                name: detail.to_record() for name, detail in self.per_agent.items()
            },
            'total_ready_ms': self.total_ready_ms,
            'per_agent_ms': dict(self.per_agent_ms),
            'stage_timings_ms': dict(self.stage_timings_ms),
            'concurrency': (
                self.concurrency.to_record() if self.concurrency is not None else None
            ),
            'agent_failed': sorted(
                name for name, detail in self.per_agent.items()
                if detail.state is AgentReadyState.AGENT_FAILED
            ),
            'agent_waiting': sorted(
                name for name, detail in self.per_agent.items()
                if detail.state is AgentReadyState.AGENT_WAITING
            ),
            'agent_ready': sorted(
                name for name, detail in self.per_agent.items()
                if detail.state is AgentReadyState.AGENT_READY
            ),
            'agent_skipped': sorted(
                name for name, detail in self.per_agent.items()
                if detail.state is AgentReadyState.AGENT_SKIPPED
            ),
        }


__all__ = [
    'AgentReadyDetail',
    'AgentReadyState',
    'AllReadyResult',
    'ConcurrencyObservation',
    'HealthProbeOutcome',
]