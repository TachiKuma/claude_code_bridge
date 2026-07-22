from __future__ import annotations

from completion.detectors.anchored_session_stability import AnchoredSessionStabilityDetector
from completion.detectors.protocol_turn import ProtocolTurnDetector
from completion.detectors.terminal_text_quiet import TerminalTextQuietDetector
from completion.models import (
    CompletionConfidence,
    CompletionCursor,
    CompletionItem,
    CompletionItemKind,
    CompletionRequestContext,
    CompletionSourceKind,
    CompletionStatus,
)
from provider_backends.agy.execution_runtime.poll import _extract_agy_pane_reply
from provider_pane_status.claude_pane import parse_claude_pane_status
from provider_pane_status.codex_pane import parse_codex_pane_status


def _ctx(provider: str = "codex") -> CompletionRequestContext:
    return CompletionRequestContext(
        req_id="req-rmux",
        agent_name="agent1",
        provider=provider,
        timeout_s=10,
    )


def _cursor(seq: int, source_kind=CompletionSourceKind.PROTOCOL_EVENT_STREAM) -> CompletionCursor:
    return CompletionCursor(source_kind=source_kind, event_seq=seq)


def _item(kind: CompletionItemKind, seq: int, payload: dict | None = None) -> CompletionItem:
    return CompletionItem(
        kind=kind,
        timestamp=f"2026-07-23T00:00:{seq:02d}Z",
        cursor=_cursor(seq),
        provider="codex",
        agent_name="agent1",
        req_id="req-rmux",
        payload=payload or {},
    )


def _rmux_capture_text(text: str) -> str:
    result = {
        "text": text,
        "raw_bytes": text.encode("utf-8", errors="replace"),
        "start_line": -200,
        "end_line": None,
        "ansi_mode": "ansi",
        "trim_policy": "preserve",
        "diagnostics": {"source": "rmux_fixture"},
    }
    return result["text"]


def test_codex_pane_status_fixture_survives_ansi_and_trailing_spaces() -> None:
    capture = _rmux_capture_text(
        "\x1b[2muser prompt\x1b[0m  \n"
        "• Working (1s, esc to interrupt)\n"
        "final answer with trailing spaces   \n"
        "✔ Worked for 3s\n"
    )

    status = parse_codex_pane_status(capture)

    assert status.state == "completed"
    assert status.completion_evidence is not None
    assert status.completion_evidence.reason == "codex_worked_for_terminal_summary"


def test_claude_pane_status_fixture_keeps_terminal_summary_observational() -> None:
    capture = _rmux_capture_text(
        "\x1b[36mAssistant\x1b[0m\n"
        "Final answer.\n"
        "✻ Thought for 7s\n"
    )

    status = parse_claude_pane_status(capture)

    assert status.state == "terminal_summary"
    assert "not_completion_authority" in status.notes


def test_protocol_turn_detector_consumes_rmux_capture_derived_event_stream() -> None:
    capture = _rmux_capture_text("partial reply\nwith wide char: 界  \n")
    expected = capture.strip()
    detector = ProtocolTurnDetector()
    detector.bind(_ctx(), _cursor(0))
    detector.ingest(_item(CompletionItemKind.ANCHOR_SEEN, 1))
    detector.ingest(_item(CompletionItemKind.ASSISTANT_CHUNK, 2, {"text": capture}))
    detector.ingest(_item(CompletionItemKind.TURN_BOUNDARY, 3, {"reason": "task_complete", "last_agent_message": capture}))

    decision = detector.decision()

    assert decision.terminal is True
    assert decision.status is CompletionStatus.COMPLETED
    assert decision.confidence is CompletionConfidence.EXACT
    assert decision.reply == expected


def test_terminal_text_quiet_detector_preserves_final_newline_policy() -> None:
    capture = _rmux_capture_text("answer line one\nanswer line two\n")
    detector = TerminalTextQuietDetector()
    detector.bind(_ctx(), _cursor(0))
    detector.ingest(_item(CompletionItemKind.ASSISTANT_FINAL, 1, {"text": capture, "done_marker": True}))

    decision = detector.decision()

    assert decision.terminal is True
    assert decision.reason == "terminal_done_marker"
    assert decision.reply == capture.strip()


def test_agy_pane_snapshot_fixture_extracts_reply_from_rmux_capture() -> None:
    capture = _rmux_capture_text(
        "> CCB_REQ_ID=req-rmux\n"
        "▸ Thought for 1s\n"
        "AGY Answer\n"
        "line with shell chars & | < >\n"
        "Done\n"
        "ready > \n"
    )

    reply = _extract_agy_pane_reply(capture, "req-rmux")

    assert "AGY Answer" in reply
    assert "line with shell chars & | < >" in reply


def test_session_snapshot_detector_accepts_rmux_log_snapshot_shape() -> None:
    capture = _rmux_capture_text("DeepSeek reply from session snapshot\n")
    detector = AnchoredSessionStabilityDetector(settle_window_s=1.0)
    detector.bind(_ctx("deepseek"), _cursor(0, CompletionSourceKind.SESSION_SNAPSHOT))
    detector.ingest(_item(CompletionItemKind.ANCHOR_SEEN, 1))
    detector.ingest(
        _item(
            CompletionItemKind.SESSION_SNAPSHOT,
            2,
            {
                "message_id": "m-rmux",
                "reply": capture,
                "message_count": 2,
                "last_updated": "2026-07-23T00:00:02Z",
            },
        )
    )
    detector.tick("2026-07-23T00:00:04Z", _cursor(2, CompletionSourceKind.SESSION_SNAPSHOT))

    decision = detector.decision()

    assert decision.terminal is True
    assert decision.status is CompletionStatus.COMPLETED
    assert decision.reply == ""
    assert detector.state().reply_started is True
    assert detector.state().reply_stable is True
