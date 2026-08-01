from __future__ import annotations

import json
from pathlib import Path

import terminal_runtime.api as terminal_api
from terminal_runtime.backend_selection import TerminalBackendSelection


class _FakeTmuxBackend:
    pass


def test_mux_backend_contract_only_selects_existing_tmux_backend(monkeypatch) -> None:
    selection = TerminalBackendSelection(
        detect_terminal_fn=lambda: "tmux",
        tmux_backend_factory=lambda: _FakeTmuxBackend(),
    )

    assert isinstance(selection.get_backend(), _FakeTmuxBackend)
    monkeypatch.setattr(terminal_api, "_backend_cache", None)
    assert terminal_api.get_backend("herdr") is None


def test_mux_backend_contract_has_no_herdr_native_surface() -> None:
    root = Path(__file__).resolve().parents[1]
    runtime_root = root / "lib" / "terminal_runtime"
    matches = [
        path.relative_to(root)
        for path in runtime_root.rglob("*.py")
        if "herdr-native" in path.read_text(encoding="utf-8", errors="ignore")
    ]

    assert matches == []


def test_mux_backend_contract_has_no_production_runtime_diff() -> None:
    root = Path(__file__).resolve().parents[1]
    scope_gate = json.loads(
        (
            root
            / ".codestable"
            / "features"
            / "2026-07-31-herdr-backend-contract-spike"
            / "evidence"
            / "scope-gate.json"
        ).read_text(encoding="utf-8")
    )
    changed_files = scope_gate["evidence"][0]["changed_files"]

    assert [path for path in changed_files if path.startswith("lib/terminal_runtime/")] == []
