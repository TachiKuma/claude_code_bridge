from __future__ import annotations

from dataclasses import dataclass, replace

from .contracts import HerdrRuntimeBinding, HerdrRuntimeBoundPane, HerdrRuntimeEvent


@dataclass(frozen=True)
class HerdrRuntimePaneStatus:
    slot: str
    pane_id: str
    agent_id: str
    provider_kind: str
    runtime_generation: int
    runtime_state: str
    state: str
    source: str
    seq: int
    unseen_done: bool = False

    def to_record(self) -> dict[str, object]:
        return {
            "slot": self.slot,
            "pane_id": self.pane_id,
            "agent_id": self.agent_id,
            "provider_kind": self.provider_kind,
            "runtime_generation": self.runtime_generation,
            "runtime_state": self.runtime_state,
            "state": self.state,
            "source": self.source,
            "seq": self.seq,
            "unseen_done": self.unseen_done,
        }


class HerdrRuntimeEventProjector:
    def __init__(self, binding: HerdrRuntimeBinding) -> None:
        self._binding = binding
        self._statuses = self._seed_statuses(binding)

    def refresh(self, binding: HerdrRuntimeBinding) -> None:
        self._binding = binding
        self._statuses = self._seed_statuses(binding)

    def apply_event(self, event: HerdrRuntimeEvent) -> bool:
        current = self._statuses.get(event.pane_id)
        if current is None:
            return False
        if not self._event_matches_binding(event, current):
            return False
        if event.seq <= current.seq:
            return False
        self._statuses[event.pane_id] = replace(
            current,
            runtime_state=event.state,
            state=map_herdr_state_to_ccb(event.state),
            source="event",
            seq=event.seq,
            unseen_done=_herdr_state(event.state) == "done",
        )
        return True

    def status_for_pane(self, pane_id: str) -> HerdrRuntimePaneStatus | None:
        return self._statuses.get(str(pane_id or "").strip())

    def statuses(self) -> tuple[HerdrRuntimePaneStatus, ...]:
        return tuple(self._statuses.values())

    def _event_matches_binding(
        self,
        event: HerdrRuntimeEvent,
        current: HerdrRuntimePaneStatus,
    ) -> bool:
        return (
            event.server_id == self._binding.server_id
            and event.session_name == self._binding.session_name
            and event.workspace_id == self._binding.workspace_id
            and event.runtime_generation == self._binding.runtime_generation
            and event.agent_id == current.agent_id
            and event.provider_kind == current.provider_kind
        )

    @staticmethod
    def _seed_statuses(binding: HerdrRuntimeBinding) -> dict[str, HerdrRuntimePaneStatus]:
        return {
            pane.pane_id: _status_from_bound_pane(binding, pane, source="snapshot")
            for pane in binding.panes
        }


def runtime_status_from_binding(
    binding: HerdrRuntimeBinding,
    *,
    slot: str,
    pane_id: str,
) -> dict[str, object] | None:
    slot_value = str(slot or "").strip()
    pane_value = str(pane_id or "").strip()
    for pane in binding.panes:
        if pane.slot == slot_value and pane.pane_id == pane_value:
            return _status_from_bound_pane(binding, pane, source="snapshot").to_record()
    return None


def map_herdr_state_to_ccb(state: object) -> str:
    value = _herdr_state(state)
    if value == "working":
        return "working"
    if value == "blocked":
        return "waiting_for_user"
    if value == "done":
        return "idle"
    if value == "idle":
        return "idle"
    return "unknown"


def _status_from_bound_pane(
    binding: HerdrRuntimeBinding,
    pane: HerdrRuntimeBoundPane,
    *,
    source: str,
) -> HerdrRuntimePaneStatus:
    return HerdrRuntimePaneStatus(
        slot=pane.slot,
        pane_id=pane.pane_id,
        agent_id=pane.agent_id,
        provider_kind=pane.provider_kind,
        runtime_generation=binding.runtime_generation,
        runtime_state=_herdr_state(pane.state),
        state=map_herdr_state_to_ccb(pane.state),
        source=source,
        seq=pane.state_seq,
        unseen_done=_herdr_state(pane.state) == "done",
    )


def _herdr_state(state: object) -> str:
    value = str(state or "").strip().lower()
    if value in {"idle", "working", "blocked", "done", "unknown"}:
        return value
    return "unknown"


__all__ = [
    "HerdrRuntimeEventProjector",
    "HerdrRuntimePaneStatus",
    "map_herdr_state_to_ccb",
    "runtime_status_from_binding",
]
