from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_legacy_herdr_hosting_spec_points_to_adr_0002_instead_of_waiting_upstream() -> None:
    text = _read(".scratch/wezterm-ccb-herdr-hosting/spec.md")

    assert "ADR 0002" in text
    assert "真正上游事件源仍待 Herdr 提供" not in text
    assert "需等待或接入 Herdr 上游原生 `runtime.ensure/event/agent_id` 能力" not in text
    assert "上游 Herdr 原生 `runtime.ensure` 成熟后再切换" not in text


def test_wontfix_herdr_downstream_tickets_are_not_open_blockers() -> None:
    for relative in (
        ".scratch/wezterm-ccb-herdr-hosting/issues/12C-herdr-restart-backoff-cleanup-handoff.md",
        ".scratch/wezterm-ccb-herdr-hosting/issues/13A-agent-id-authority-contract.md",
        ".scratch/wezterm-ccb-herdr-hosting/issues/13B-delete-ccb-pane-agent-report-patch.md",
    ):
        text = _read(relative)
        status_line = next(line for line in text.splitlines() if line.startswith("**Status:**"))
        assert "wontfix" in status_line
        assert "blocked-upstream" not in text
        assert "保持 blocked" not in text
        assert "保持 blocked-by" not in text

