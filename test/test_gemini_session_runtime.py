from __future__ import annotations

import json
from pathlib import Path

from provider_backends.gemini.comm_runtime.session_runtime import load_gemini_session_info


def test_load_gemini_session_info_merges_env_and_session_file(monkeypatch, tmp_path: Path) -> None:
    session_file = tmp_path / ".gemini-session"
    session_file.write_text(
        json.dumps(
            {
                "gemini_session_path": str(tmp_path / "session.json"),
                "pane_id": "%3",
                "tmux_session": "%3",
                "pane_title_marker": "agent1",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("CCB_SESSION_ID", "ccb-1")
    monkeypatch.setenv("GEMINI_RUNTIME_DIR", str(tmp_path / "runtime"))
    monkeypatch.setenv("GEMINI_TMUX_SESSION", "%legacy")
    monkeypatch.setenv("CCB_MUX_BACKEND_FAMILY", "tmux-family")
    monkeypatch.setenv("CCB_MUX_BACKEND_IMPL", "rmux")
    monkeypatch.setenv("CCB_MUX_PANE_ID", "%mux")
    monkeypatch.setattr(
        "provider_backends.gemini.comm_runtime.session_runtime.read_gemini_session_id",
        lambda path: "gemini-sid" if path == Path(str(tmp_path / "session.json")) else None,
    )

    info = load_gemini_session_info(session_finder=lambda: session_file)

    assert info is not None
    assert info["ccb_session_id"] == "ccb-1"
    assert info["gemini_session_path"] == str(tmp_path / "session.json")
    assert info["gemini_session_id"] == "gemini-sid"
    assert info["pane_id"] == "%mux"
    assert info["tmux_session"] == "%legacy"
    assert info["terminal"] == "mux"
    assert info["backend_impl"] == "rmux"
    assert info["pane_title_marker"] == "agent1"


def test_load_gemini_session_info_merges_canonical_mux_session_file_without_env_mux(
    monkeypatch, tmp_path: Path
) -> None:
    session_file = tmp_path / ".gemini-session"
    session_file.write_text(
        json.dumps(
            {
                "terminal": "mux",
                "backend_family": "tmux-family",
                "backend_impl": "rmux",
                "pane_ref": {"pane_id": "%rmux", "backend_impl": "rmux"},
                "namespace_ref": {
                    "backend_family": "tmux-family",
                    "backend_impl": "rmux",
                    "ipc_kind": "named_pipe",
                    "ipc_ref": r"\\.\pipe\ccb-rmux",
                },
                "tmux_session": "%legacy",
                "gemini_session_path": str(tmp_path / "session.json"),
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("CCB_SESSION_ID", "ccb-1")
    monkeypatch.setenv("GEMINI_RUNTIME_DIR", str(tmp_path / "runtime"))
    monkeypatch.delenv("CCB_MUX_BACKEND_FAMILY", raising=False)
    monkeypatch.delenv("CCB_MUX_BACKEND_IMPL", raising=False)
    monkeypatch.delenv("CCB_MUX_PANE_ID", raising=False)
    monkeypatch.delenv("GEMINI_TMUX_SESSION", raising=False)

    info = load_gemini_session_info(session_finder=lambda: session_file)

    assert info is not None
    assert info["terminal"] == "mux"
    assert info["backend_family"] == "tmux-family"
    assert info["backend_impl"] == "rmux"
    assert info["pane_id"] == "%rmux"
    assert info["tmux_session"] == "%legacy"
    assert info["pane_ref"] == {"pane_id": "%rmux", "backend_impl": "rmux"}
    assert info["namespace_ref"]["ipc_kind"] == "named_pipe"


def test_load_gemini_session_info_returns_none_for_inactive_project_session(
    tmp_path: Path,
) -> None:
    session_file = tmp_path / ".gemini-session"
    session_file.write_text(json.dumps({"active": False}), encoding="utf-8")

    info = load_gemini_session_info(session_finder=lambda: session_file)

    assert info is None
