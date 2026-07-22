from __future__ import annotations

import json
from types import SimpleNamespace
from pathlib import Path

from cli.services.runtime_launch_runtime.session_files import write_session_file
from provider_runtime.session_payload import build_mux_session_payload, merge_provider_payload, project_session_payload


def test_build_mux_session_payload_projects_canonical_and_compat_aliases() -> None:
    payload = build_mux_session_payload(
        backend_impl="rmux",
        pane_id="%9",
        session_name="ccb-demo",
        window_name="main",
        namespace_id="ns-1",
        namespace_ipc_kind="named_pipe",
        namespace_ipc_ref=r"\\.\pipe\ccb-demo",
    )

    assert payload["terminal"] == "mux"
    assert payload["backend_family"] == "tmux-family"
    assert payload["backend_impl"] == "rmux"
    assert payload["pane_ref"] == {
        "backend_impl": "rmux",
        "pane_id": "%9",
        "session_name": "ccb-demo",
        "window_name": "main",
    }
    assert payload["namespace_ref"]["ipc_kind"] == "named_pipe"
    assert payload["namespace_ref"]["ipc_ref"] == r"\\.\pipe\ccb-demo"
    assert payload["tmux_session"] == "%9"
    assert payload["compat"]["tmux_session"] == "%9"

    view = project_session_payload(payload)
    assert view.terminal == "mux"
    assert view.backend_impl == "rmux"
    assert view.pane_id == "%9"
    assert view.namespace_ipc_kind == "named_pipe"


def test_merge_provider_payload_keeps_canonical_shared_keys() -> None:
    shared = build_mux_session_payload(
        backend_impl="tmux",
        pane_id="%7",
        tmux_socket_path="/tmp/ccb-agent.sock",
    )

    payload = merge_provider_payload(
        shared,
        {
            "terminal": "tmux",
            "pane_id": "%wrong",
            "tmux_session": "%wrong",
            "provider_field": "ok",
        },
    )

    assert payload["terminal"] == "mux"
    assert payload["pane_id"] == "%7"
    assert payload["tmux_session"] == "%7"
    assert payload["provider_field"] == "ok"
    conflicts = payload["payload_diagnostics"]["protected_key_conflicts"]
    assert {item["key"] for item in conflicts} == {"terminal", "pane_id", "tmux_session"}


def test_write_session_file_persists_ccb_session_id_only(tmp_path: Path) -> None:
    ccb_dir = tmp_path / ".ccb"
    ccb_dir.mkdir(parents=True, exist_ok=True)

    context = SimpleNamespace(
        paths=SimpleNamespace(ccb_dir=ccb_dir),
        project=SimpleNamespace(project_id="proj-1", project_root=tmp_path),
    )
    spec = SimpleNamespace(name="agent1", provider="codex")
    plan = SimpleNamespace(workspace_path=tmp_path / "workspace")
    runtime_dir = ccb_dir / "runtime" / "agent1"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    run_cwd = tmp_path / "workspace"
    run_cwd.mkdir(parents=True, exist_ok=True)

    session_path = write_session_file(
        context=context,
        spec=spec,
        plan=plan,
        runtime_dir=runtime_dir,
        run_cwd=run_cwd,
        pane_id="%7",
        tmux_socket_name="ccb-demo",
        tmux_socket_path=str(ccb_dir / "ccbd" / "tmux.sock"),
        pane_title_marker="CCB-agent1",
        start_cmd="codex",
        launch_session_id="ccb-agent1-123",
        provider_payload={"codex_session_id": "provider-sid"},
    )

    data = json.loads(session_path.read_text(encoding="utf-8"))
    assert data["ccb_session_id"] == "ccb-agent1-123"
    assert data["terminal"] == "mux"
    assert data["backend_family"] == "tmux-family"
    assert data["backend_impl"] == "tmux"
    assert data["pane_ref"]["pane_id"] == "%7"
    assert data["namespace_ref"]["ipc_kind"] == "unix_socket"
    assert data["compat"]["tmux_session"] == "%7"
    assert "session_id" not in data
    assert data["codex_session_id"] == "provider-sid"


def test_write_session_file_records_provider_payload_conflicts_without_overwrite(tmp_path: Path) -> None:
    ccb_dir = tmp_path / ".ccb"
    ccb_dir.mkdir(parents=True, exist_ok=True)

    context = SimpleNamespace(
        paths=SimpleNamespace(ccb_dir=ccb_dir),
        project=SimpleNamespace(project_id="proj-1", project_root=tmp_path),
    )
    spec = SimpleNamespace(name="agent1", provider="codex")
    plan = SimpleNamespace(workspace_path=tmp_path / "workspace")
    runtime_dir = ccb_dir / "runtime" / "agent1"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    run_cwd = tmp_path / "workspace"
    run_cwd.mkdir(parents=True, exist_ok=True)

    session_path = write_session_file(
        context=context,
        spec=spec,
        plan=plan,
        runtime_dir=runtime_dir,
        run_cwd=run_cwd,
        pane_id="%7",
        tmux_socket_name=None,
        tmux_socket_path="/tmp/ccb-agent.sock",
        pane_title_marker="CCB-agent1",
        start_cmd="codex",
        launch_session_id="ccb-agent1-123",
        provider_payload={"terminal": "tmux", "pane_id": "%wrong"},
    )

    data = json.loads(session_path.read_text(encoding="utf-8"))
    assert data["terminal"] == "mux"
    assert data["pane_id"] == "%7"
    assert data["tmux_socket_path"] == "/tmp/ccb-agent.sock"
    conflicts = data["payload_diagnostics"]["protected_key_conflicts"]
    assert {item["key"] for item in conflicts} == {"terminal", "pane_id"}


def test_write_session_file_skips_stale_codex_resume_binding_without_bound_authority(tmp_path: Path) -> None:
    ccb_dir = tmp_path / ".ccb"
    ccb_dir.mkdir(parents=True, exist_ok=True)
    (ccb_dir / ".codex-agent1-session").write_text(
        json.dumps(
            {
                "codex_session_id": "legacy-sid",
                "codex_session_path": str(tmp_path / "legacy.jsonl"),
                "codex_provider_authority_fingerprint": "fp-1",
                "updated_at": "2026-04-26 00:00:00",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    context = SimpleNamespace(
        paths=SimpleNamespace(ccb_dir=ccb_dir),
        project=SimpleNamespace(project_id="proj-1", project_root=tmp_path),
    )
    spec = SimpleNamespace(name="agent1", provider="codex")
    plan = SimpleNamespace(workspace_path=tmp_path / "workspace")
    runtime_dir = ccb_dir / "runtime" / "agent1"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    run_cwd = tmp_path / "workspace"
    run_cwd.mkdir(parents=True, exist_ok=True)

    session_path = write_session_file(
        context=context,
        spec=spec,
        plan=plan,
        runtime_dir=runtime_dir,
        run_cwd=run_cwd,
        pane_id="%7",
        tmux_socket_name="ccb-demo",
        tmux_socket_path=str(ccb_dir / "ccbd" / "tmux.sock"),
        pane_title_marker="CCB-agent1",
        start_cmd="codex",
        launch_session_id="ccb-agent1-456",
        provider_payload={
            "codex_home": str(ccb_dir / "provider-profiles" / "agent1" / "codex"),
            "codex_session_root": str(ccb_dir / "provider-profiles" / "agent1" / "codex" / "sessions"),
            "codex_provider_authority_fingerprint": "fp-1",
        },
    )

    data = json.loads(session_path.read_text(encoding="utf-8"))
    assert data["codex_provider_authority_fingerprint"] == "fp-1"
    assert "codex_session_id" not in data
    assert "codex_session_path" not in data
    assert "updated_at" not in data


def test_write_session_file_preserves_codex_resume_binding_when_bound_authority_matches(tmp_path: Path) -> None:
    ccb_dir = tmp_path / ".ccb"
    ccb_dir.mkdir(parents=True, exist_ok=True)
    (ccb_dir / ".codex-agent1-session").write_text(
        json.dumps(
            {
                "codex_session_id": "bound-sid",
                "codex_session_path": str(tmp_path / "bound.jsonl"),
                "codex_provider_authority_fingerprint": "fp-1",
                "codex_session_authority_fingerprint": "fp-1",
                "updated_at": "2026-04-26 00:00:00",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    context = SimpleNamespace(
        paths=SimpleNamespace(ccb_dir=ccb_dir),
        project=SimpleNamespace(project_id="proj-1", project_root=tmp_path),
    )
    spec = SimpleNamespace(name="agent1", provider="codex")
    plan = SimpleNamespace(workspace_path=tmp_path / "workspace")
    runtime_dir = ccb_dir / "runtime" / "agent1"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    run_cwd = tmp_path / "workspace"
    run_cwd.mkdir(parents=True, exist_ok=True)

    session_path = write_session_file(
        context=context,
        spec=spec,
        plan=plan,
        runtime_dir=runtime_dir,
        run_cwd=run_cwd,
        pane_id="%7",
        tmux_socket_name="ccb-demo",
        tmux_socket_path=str(ccb_dir / "ccbd" / "tmux.sock"),
        pane_title_marker="CCB-agent1",
        start_cmd="codex",
        launch_session_id="ccb-agent1-789",
        provider_payload={
            "codex_home": str(ccb_dir / "provider-profiles" / "agent1" / "codex"),
            "codex_session_root": str(ccb_dir / "provider-profiles" / "agent1" / "codex" / "sessions"),
            "codex_provider_authority_fingerprint": "fp-1",
        },
    )

    data = json.loads(session_path.read_text(encoding="utf-8"))
    assert data["codex_session_id"] == "bound-sid"
    assert data["codex_session_path"] == str(tmp_path / "bound.jsonl")
    assert data["codex_session_authority_fingerprint"] == "fp-1"
    assert data["updated_at"] == "2026-04-26 00:00:00"
