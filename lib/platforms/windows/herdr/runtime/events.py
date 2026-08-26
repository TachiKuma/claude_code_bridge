from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace

from terminal_runtime.mux_backend_contract import MuxCommandErrorV2

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

    def refresh(
        self,
        binding: HerdrRuntimeBinding,
        *,
        snapshot: Mapping[str, object] | None = None,
    ) -> tuple[str, ...]:
        previous = self._statuses
        self._binding = binding
        if snapshot is None:
            self._statuses = self._seed_statuses(binding)
        else:
            self._statuses = self._seed_statuses_from_snapshot(binding, snapshot)
        return self._changed_pane_ids(previous, self._statuses)

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

    @staticmethod
    def _seed_statuses_from_snapshot(
        binding: HerdrRuntimeBinding,
        snapshot: Mapping[str, object],
    ) -> dict[str, HerdrRuntimePaneStatus]:
        panes = snapshot.get("panes")
        if not isinstance(panes, list):
            return {}
        statuses: dict[str, HerdrRuntimePaneStatus] = {}
        for pane in binding.panes:
            snapshot_pane = _snapshot_pane_for_id(panes, pane.pane_id)
            if snapshot_pane is None:
                continue
            if not _snapshot_pane_matches_binding(binding, snapshot_pane):
                continue
            statuses[pane.pane_id] = _status_from_snapshot_pane(binding, pane, snapshot_pane)
        return statuses

    @staticmethod
    def _changed_pane_ids(
        previous: Mapping[str, HerdrRuntimePaneStatus],
        current: Mapping[str, HerdrRuntimePaneStatus],
    ) -> tuple[str, ...]:
        changed: list[str] = []
        for pane_id, status in current.items():
            if previous.get(pane_id) != status:
                changed.append(pane_id)
        for pane_id in previous:
            if pane_id not in current:
                changed.append(pane_id)
        return tuple(changed)


@dataclass(frozen=True)
class HerdrRuntimeEventSource:
    kind: str
    fallback_reason: str | None = None


class HerdrRuntimeEventSubscription:
    """最小事件订阅适配器：snapshot 先种子，再消费增量事件。

    上游能力缺失或订阅断开时显式回退到 snapshot polling，并把回退原因暴露给调用方。
    """

    def __init__(
        self,
        *,
        backend: object,
        binding: HerdrRuntimeBinding,
        projector: HerdrRuntimeEventProjector,
        events_supported: bool,
    ) -> None:
        self._backend = backend
        self._binding = binding
        self._projector = projector
        self._seeded = False
        self._source = HerdrRuntimeEventSource(
            kind="event" if events_supported else "snapshot_polling",
            fallback_reason=None if events_supported else "runtime_events_unsupported",
        )

    @property
    def source(self) -> HerdrRuntimeEventSource:
        return self._source

    def seed_snapshot(self) -> tuple[str, ...]:
        changed = poll_runtime_snapshot(self._projector, self._binding, self._backend)
        self._seeded = True
        return changed

    def poll(self) -> tuple[str, ...]:
        changed: list[str] = []
        if not self._seeded:
            changed.extend(self.seed_snapshot())
            if self._source.kind != "event":
                return tuple(dict.fromkeys(changed))
        if self._source.kind == "event":
            changed.extend(self._drain_events())
        else:
            changed.extend(poll_runtime_snapshot(self._projector, self._binding, self._backend))
        return tuple(dict.fromkeys(changed))

    def _drain_events(self) -> tuple[str, ...]:
        events_fn = getattr(self._backend, "runtime_events", None)
        if not callable(events_fn):
            return self._fallback_to_polling("subscription_unavailable")
        try:
            raw_events = events_fn()
        except MuxCommandErrorV2 as exc:
            return self._fallback_to_polling(
                f"subscription_failed:{exc.category or type(exc).__name__}"
            )
        except Exception as exc:
            return self._fallback_to_polling(f"subscription_failed:{type(exc).__name__}")
        if not isinstance(raw_events, (list, tuple)):
            return self._fallback_to_polling("subscription_failed:invalid_event_batch")
        changed: list[str] = []
        for raw in raw_events:
            event = parse_runtime_event(raw)
            if event is None:
                continue
            if self._projector.apply_event(event):
                changed.append(event.pane_id)
        return tuple(dict.fromkeys(changed))

    def _fallback_to_polling(self, reason: str) -> tuple[str, ...]:
        self._source = HerdrRuntimeEventSource(
            kind="snapshot_polling",
            fallback_reason=reason,
        )
        return poll_runtime_snapshot(self._projector, self._binding, self._backend)


def create_runtime_event_subscription(
    *,
    backend: object,
    binding: HerdrRuntimeBinding,
    projector: HerdrRuntimeEventProjector,
) -> HerdrRuntimeEventSubscription:
    events_supported = _events_supported_by_backend(backend)
    return HerdrRuntimeEventSubscription(
        backend=backend,
        binding=binding,
        projector=projector,
        events_supported=events_supported,
    )


def parse_runtime_event(payload: object) -> HerdrRuntimeEvent | None:
    """把上游事件记录解析为 HerdrRuntimeEvent，只复制白名单字段。"""
    if not isinstance(payload, Mapping):
        return None
    raw_state = str(payload.get("state") or "").strip().lower()
    if raw_state not in {"idle", "working", "blocked", "done", "unknown"}:
        return None
    seq = _non_negative_int(payload.get("seq"))
    generation = _positive_int(payload.get("runtime_generation"))
    pane_id = _text(payload.get("pane_id"))
    if seq is None or generation is None or not pane_id:
        return None
    server_id = _text(payload.get("server_id"))
    session_name = _text(payload.get("session_name"))
    workspace_id = _text(payload.get("workspace_id"))
    agent_id = _text(payload.get("agent_id"))
    provider_kind = _text(payload.get("provider_kind"))
    if not (server_id and session_name and workspace_id and agent_id and provider_kind):
        return None
    try:
        return HerdrRuntimeEvent(
            event_type=_text(payload.get("event_type")) or "agent_state_changed",
            event_id=_text(payload.get("event_id")) or f"{pane_id}:{seq}",
            server_id=server_id,
            session_name=session_name,
            workspace_id=workspace_id,
            pane_id=pane_id,
            agent_id=agent_id,
            provider_kind=provider_kind,
            runtime_generation=generation,
            seq=seq,
            state=raw_state,
            occurred_at=_text(payload.get("occurred_at"))
            or _text(payload.get("timestamp"))
            or "unknown",
        )
    except ValueError:
        return None


def poll_runtime_snapshot(
    projector: HerdrRuntimeEventProjector,
    binding: HerdrRuntimeBinding,
    backend: object,
) -> tuple[str, ...]:
    snapshot_fn = getattr(backend, "runtime_snapshot", None)
    if not callable(snapshot_fn):
        return ()
    snapshot = snapshot_fn()
    if not isinstance(snapshot, Mapping):
        return ()
    return projector.refresh(binding, snapshot=snapshot)


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


def _status_from_snapshot_pane(
    binding: HerdrRuntimeBinding,
    pane: HerdrRuntimeBoundPane,
    snapshot_pane: Mapping[str, object],
) -> HerdrRuntimePaneStatus:
    runtime_state = _herdr_state(snapshot_pane.get("runtime_state") or snapshot_pane.get("state"))
    seq = _snapshot_seq(snapshot_pane, fallback=pane.state_seq)
    return HerdrRuntimePaneStatus(
        slot=pane.slot,
        pane_id=pane.pane_id,
        agent_id=pane.agent_id,
        provider_kind=pane.provider_kind,
        runtime_generation=binding.runtime_generation,
        runtime_state=runtime_state,
        state=map_herdr_state_to_ccb(runtime_state),
        source=_text(snapshot_pane.get("source")) or "snapshot",
        seq=seq,
        unseen_done=runtime_state == "done",
    )


def _snapshot_pane_for_id(panes: list[object], pane_id: str) -> Mapping[str, object] | None:
    target = str(pane_id or "").strip()
    if not target:
        return None
    for pane in panes:
        if not isinstance(pane, Mapping):
            continue
        current = str(pane.get("pane_id") or "").strip()
        if current == target:
            return pane
    return None


def _snapshot_pane_matches_binding(
    binding: HerdrRuntimeBinding,
    snapshot_pane: Mapping[str, object],
) -> bool:
    for key, expected in (
        ("workspace_id", binding.workspace_id),
        ("session_name", binding.session_name),
    ):
        value = str(snapshot_pane.get(key) or "").strip()
        if value and value != expected:
            return False
    return True


def _snapshot_seq(snapshot_pane: Mapping[str, object], *, fallback: int) -> int:
    for key in ("state_seq", "seq"):
        value = snapshot_pane.get(key)
        try:
            if value is not None:
                seq = int(value)
                if seq >= 0:
                    return seq
        except (TypeError, ValueError):
            continue
    return fallback


def _events_supported_by_backend(backend: object) -> bool:
    capabilities_fn = getattr(backend, "runtime_capabilities", None)
    status = "unsupported"
    if callable(capabilities_fn):
        capabilities = capabilities_fn()
        if isinstance(capabilities, Mapping):
            status = str(capabilities.get("runtime_events") or "unsupported").strip()
    if status not in {"supported", "partial", "workaround"}:
        return False
    return callable(getattr(backend, "runtime_events", None)) and callable(
        getattr(backend, "runtime_snapshot", None)
    )


def _non_negative_int(value: object) -> int | None:
    try:
        result = int(value or -1)
    except (TypeError, ValueError):
        return None
    return result if result >= 0 else None


def _positive_int(value: object) -> int | None:
    try:
        result = int(value or 0)
    except (TypeError, ValueError):
        return None
    return result if result > 0 else None


def _text(value: object) -> str:
    return str(value or "").strip()


def _herdr_state(state: object) -> str:
    value = str(state or "").strip().lower()
    if value in {"idle", "working", "blocked", "done", "unknown"}:
        return value
    return "unknown"


__all__ = [
    "HerdrRuntimeEventProjector",
    "HerdrRuntimePaneStatus",
    "HerdrRuntimeEventSource",
    "HerdrRuntimeEventSubscription",
    "create_runtime_event_subscription",
    "map_herdr_state_to_ccb",
    "parse_runtime_event",
    "poll_runtime_snapshot",
    "runtime_status_from_binding",
]
