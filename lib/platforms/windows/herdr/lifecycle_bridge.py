from __future__ import annotations

from collections.abc import Callable, Mapping

from agents.models import AgentState


class HerdrAgentLifecycleBridge:
    """保留调度层兼容入口，但不向 Herdr 同步 CCB 工作状态。"""

    def __init__(
        self,
        *,
        backend_factory: Callable[[], object],
        namespace_ref_fn: Callable[[], Mapping[str, object] | None],
        seq_start: int = 0,
    ) -> None:
        self._backend_factory = backend_factory
        self._namespace_ref_fn = namespace_ref_fn
        self._seq = max(int(seq_start), 0)

    @property
    def seq(self) -> int:
        return self._seq

    def sync(
        self,
        *,
        provider: str | None,
        state: AgentState | str,
        pane_id: str | None,
        session_id: str | None = None,
        session_path: str | None = None,
    ) -> bool:
        del provider, state, pane_id, session_id, session_path
        return False


__all__ = ["HerdrAgentLifecycleBridge"]
