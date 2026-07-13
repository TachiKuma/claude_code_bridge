from __future__ import annotations

from dataclasses import dataclass
from queue import Empty, Queue
import threading
from typing import Callable, Mapping

from .notifications import MobileNotificationEvent, NOTIFICATION_KIND_TASK_COMPLETED
from .pairing import MobileGatewayPairingStore

_COMPLETION_FIELDS = ('id', 'kind', 'project_id', 'project_short_name', 'agent', 'completed_at', 'dedupe_key')


@dataclass(frozen=True)
class PushSendResult:
    invalid_token: bool = False


PushSender = Callable[[str, dict[str, object], float], PushSendResult]


class MobilePushDispatcher:
    """Pushes canonical completion metadata through an externally injected sender."""

    def __init__(self, *, pairing_store: MobileGatewayPairingStore, sender: PushSender | None, timeout_seconds: float = 2.0) -> None:
        self._pairing_store = pairing_store
        self._sender = sender
        self._timeout_seconds = max(0.1, float(timeout_seconds))
        self._in_flight: set[str] = set()
        self._lock = threading.Lock()

    def deliver(self, event: MobileNotificationEvent) -> None:
        if self._sender is None or event.kind != NOTIFICATION_KIND_TASK_COMPLETED:
            return
        payload = completion_payload(event)
        for device_id, token in self._pairing_store.push_tokens_for_delivery():
            if self._is_visible_target(device_id, payload) or not self._claim(device_id):
                continue
            result = self._send_bounded(device_id, token, payload)
            if result is not None and result.invalid_token:
                self._pairing_store.delete_push_token(device_id=device_id, reason='invalid_sender_token')

    def _is_visible_target(self, device_id: str, payload: Mapping[str, object]) -> bool:
        presence = self._pairing_store.presence_for_device(device_id)
        return bool(presence and presence.get('visible') and presence.get('focused_project_id') == payload['project_id'] and presence.get('focused_agent') == payload['agent'])

    def _claim(self, device_id: str) -> bool:
        with self._lock:
            if device_id in self._in_flight:
                return False
            self._in_flight.add(device_id)
            return True

    def _send_bounded(self, device_id: str, token: str, payload: dict[str, object]) -> PushSendResult | None:
        outcome: Queue[PushSendResult | Exception] = Queue(maxsize=1)

        def run() -> None:
            try:
                outcome.put(self._sender(token, payload, self._timeout_seconds))  # type: ignore[misc]
            except Exception as exc:
                outcome.put(exc)
            finally:
                with self._lock:
                    self._in_flight.discard(device_id)

        threading.Thread(target=run, name='ccb-mobile-push', daemon=True).start()
        try:
            result = outcome.get(timeout=self._timeout_seconds)
        except Empty:
            return None
        return result if isinstance(result, PushSendResult) else None


def completion_payload(event: MobileNotificationEvent) -> dict[str, object]:
    payload = event.to_payload()
    return {key: payload[key] for key in _COMPLETION_FIELDS}
