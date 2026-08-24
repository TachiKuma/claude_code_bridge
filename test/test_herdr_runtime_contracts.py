from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import platforms.windows.herdr.runtime.manifest as herdr_manifest
from platforms.windows.herdr.runtime.contracts import (
    HerdrRuntimeBinding,
    HerdrRuntimeBoundPane,
    HerdrRuntimeEnvRef,
    HerdrRuntimeEvent,
    HerdrRuntimeManifest,
    HerdrRuntimeManifestPane,
    HerdrRuntimeManifestService,
    HerdrRuntimeManifestWorkspace,
    RUNTIME_BINDING_SCHEMA,
    RUNTIME_MANIFEST_SCHEMA,
)
from platforms.windows.herdr.runtime.ensure import ensure_runtime
from platforms.windows.herdr.runtime.events import (
    HerdrRuntimeEventProjector,
    map_herdr_state_to_ccb,
    poll_runtime_snapshot,
)


def test_herdr_runtime_manifest_round_trips_without_raw_secret_values() -> None:
    manifest = HerdrRuntimeManifest(
        project_id="proj-1",
        project_root="E:/repo",
        session_name="ccb-project-1",
        generation=12,
        services=(
            HerdrRuntimeManifestService(
                id="ccbd",
                command=("python", "-m", "ccbd"),
                cwd="E:/repo",
                ready={"kind": "ccb-lifecycle", "phase": "mounted"},
            ),
        ),
        workspaces=(
            HerdrRuntimeManifestWorkspace(
                name="project",
                cwd="E:/repo",
                panes=(
                    HerdrRuntimeManifestPane(
                        slot="codex",
                        agent_name="codex",
                        provider_kind="codex",
                        command=("codex",),
                        cwd="E:/repo",
                        env_refs=(
                            HerdrRuntimeEnvRef(
                                name="OPENAI_API_KEY",
                                source="ccb-provider-home",
                            ),
                        ),
                        restart={"policy": "manual-or-ccb-approved"},
                    ),
                ),
            ),
        ),
    )

    record = manifest.to_record()
    restored = HerdrRuntimeManifest.from_record(record)

    assert record["schema"] == RUNTIME_MANIFEST_SCHEMA
    pane = record["workspaces"][0]["panes"][0]  # type: ignore[index]
    assert "env" not in pane
    assert pane["env_refs"] == [{"name": "OPENAI_API_KEY", "source": "ccb-provider-home"}]
    assert pane["restart"] == {"policy": "manual-or-ccb-approved"}
    assert record["services"] == [
        {
            "id": "ccbd",
            "command": ["python", "-m", "ccbd"],
            "cwd": "E:/repo",
            "ready": {"kind": "ccb-lifecycle", "phase": "mounted"},
        }
    ]
    assert restored == manifest


def test_herdr_runtime_manifest_rejects_raw_environment_values() -> None:
    with pytest.raises(ValueError, match="env_refs"):
        HerdrRuntimeManifestPane.from_record(
            {
                "slot": "codex",
                "agent_name": "codex",
                "provider_kind": "codex",
                "command": ["codex"],
                "cwd": "E:/repo",
                "env": {"OPENAI_API_KEY": "sk-raw"},
            }
        )


def test_herdr_runtime_binding_round_trips_frontend_fact_with_redaction() -> None:
    binding = HerdrRuntimeBinding(
        project_id="proj-1",
        server_id="server-1",
        server_version="0.8.2",
        api_schema="Herdr API",
        session_name="ccb-project-1",
        workspace_id="w1",
        runtime_generation=12,
        ready=True,
        capabilities={"agent_state": True},
        panes=(
            HerdrRuntimeBoundPane(
                slot="codex",
                pane_id="w1:p1",
                agent_id="codex",
                provider_kind="codex",
                state="idle",
                state_seq=1,
            ),
        ),
        frontend={
            "kind": "wezterm",
            "status": "detached_fallback",
            "mux_available": False,
            "fallback_reason": "wezterm_mux_unavailable",
            "command": "wezterm cli spawn -- secret",
        },
    )

    record = binding.to_record()
    restored = HerdrRuntimeBinding.from_record(record)

    assert record["schema"] == RUNTIME_BINDING_SCHEMA
    assert record["frontend"] == {
        "kind": "wezterm",
        "status": "detached_fallback",
        "mux_available": False,
        "fallback_reason": "wezterm_mux_unavailable",
    }
    assert restored.frontend == record["frontend"]


def test_herdr_runtime_binding_rejects_stale_runtime_identity() -> None:
    binding = HerdrRuntimeBinding(
        project_id="proj-1",
        server_id="server-1",
        server_version="0.8.2",
        api_schema="Herdr API",
        session_name="ccb-project-1",
        workspace_id="w1",
        runtime_generation=12,
        ready=True,
        capabilities={},
        panes=(
            HerdrRuntimeBoundPane(
                slot="codex",
                pane_id="w1:p1",
                agent_id="codex",
                provider_kind="codex",
                state="idle",
                state_seq=1,
            ),
        ),
    )

    assert binding.matches_runtime_identity(
        project_id="proj-1",
        session_name="ccb-project-1",
        workspace_id="w1",
        pane_id="w1:p1",
        slot="codex",
        provider_kind="codex",
        runtime_generation=12,
    )
    assert not binding.matches_runtime_identity(
        project_id="proj-1",
        session_name="ccb-project-1",
        workspace_id="w1",
        pane_id="w1:p1",
        slot="codex",
        provider_kind="codex",
        runtime_generation=11,
    )


def test_build_herdr_runtime_manifest_for_start_uses_refs_without_raw_env(monkeypatch, tmp_path: Path) -> None:
    project_root = tmp_path / "repo"
    project_root.mkdir()
    config = SimpleNamespace(
        agents={
            "codex": SimpleNamespace(
                provider="codex",
                startup_args=("--model", "gpt-5"),
                env={"OPENAI_API_KEY": "sk-raw"},
                provider_profile=SimpleNamespace(env={"OPENAI_ORG_ID": "org-raw"}),
            )
        }
    )
    context = SimpleNamespace(
        project=SimpleNamespace(project_id="proj-1", project_root=project_root),
        paths=SimpleNamespace(ccbd_tmux_session_name="ccb-proj-1"),
    )
    command = SimpleNamespace(agent_names=("codex",))
    monkeypatch.setattr(herdr_manifest, "load_project_config", lambda _root: SimpleNamespace(config=config))

    manifest = herdr_manifest.build_herdr_runtime_manifest_for_start(
        context,
        command,
        session_name="ccb-proj-1",
    )
    record = manifest.to_record()

    pane = record["workspaces"][0]["panes"][0]  # type: ignore[index]
    assert record["project_id"] == "proj-1"
    assert record["services"][0]["id"] == "ccbd"  # type: ignore[index]
    assert pane["provider_kind"] == "codex"
    assert pane["env_refs"] == [
        {"name": "OPENAI_API_KEY", "source": "ccb-provider-home"},
        {"name": "OPENAI_ORG_ID", "source": "ccb-provider-home"},
    ]
    assert "sk-raw" not in str(record)
    assert "org-raw" not in str(record)


def test_herdr_runtime_event_preserves_generation_and_sequence_identity() -> None:
    event = HerdrRuntimeEvent(
        event_type="agent_state_changed",
        event_id="evt-1",
        server_id="server-1",
        session_name="ccb-project-1",
        workspace_id="w1",
        pane_id="w1:p1",
        agent_id="codex",
        provider_kind="codex",
        runtime_generation=12,
        seq=44,
        state="working",
        occurred_at="2026-08-20T12:00:00Z",
    )

    assert HerdrRuntimeEvent.from_record(event.to_record()) == event


def test_herdr_runtime_event_projector_drops_duplicate_stale_and_foreign_events() -> None:
    binding = HerdrRuntimeBinding(
        project_id="proj-1",
        server_id="server-1",
        server_version="0.8.2",
        api_schema="Herdr API",
        session_name="ccb-project-1",
        workspace_id="w1",
        runtime_generation=12,
        ready=True,
        capabilities={},
        panes=(
            HerdrRuntimeBoundPane(
                slot="codex",
                pane_id="w1:p1",
                agent_id="codex",
                provider_kind="codex",
                state="idle",
                state_seq=1,
            ),
        ),
    )
    projector = HerdrRuntimeEventProjector(binding)

    def event(**overrides):
        values = {
            "event_type": "agent_state_changed",
            "event_id": "evt",
            "server_id": "server-1",
            "session_name": "ccb-project-1",
            "workspace_id": "w1",
            "pane_id": "w1:p1",
            "agent_id": "codex",
            "provider_kind": "codex",
            "runtime_generation": 12,
            "seq": 2,
            "state": "working",
            "occurred_at": "2026-08-20T12:00:00Z",
        }
        values.update(overrides)
        return HerdrRuntimeEvent(**values)

    assert projector.apply_event(event()) is True
    assert projector.status_for_pane("w1:p1").to_record()["state"] == "working"  # type: ignore[union-attr]
    assert projector.apply_event(event(event_id="dup")) is False
    assert projector.apply_event(event(event_id="old", seq=1, state="blocked")) is False
    assert projector.apply_event(event(event_id="stale", runtime_generation=11, seq=3, state="blocked")) is False
    assert projector.apply_event(event(event_id="moved", pane_id="w1:p2", seq=3, state="blocked")) is False
    assert projector.status_for_pane("w1:p1").to_record()["runtime_state"] == "working"  # type: ignore[union-attr]


def test_herdr_runtime_event_projector_refreshes_snapshot_without_leaking_old_state() -> None:
    binding = HerdrRuntimeBinding(
        project_id="proj-1",
        server_id="server-1",
        server_version="0.8.2",
        api_schema="Herdr API",
        session_name="ccb-project-1",
        workspace_id="w1",
        runtime_generation=12,
        ready=True,
        capabilities={},
        panes=(
            HerdrRuntimeBoundPane(
                slot="codex",
                pane_id="w1:p1",
                agent_id="codex",
                provider_kind="codex",
                state="idle",
                state_seq=1,
            ),
        ),
    )
    projector = HerdrRuntimeEventProjector(binding)

    def event(**overrides):
        values = {
            "event_type": "agent_state_changed",
            "event_id": "evt",
            "server_id": "server-1",
            "session_name": "ccb-project-1",
            "workspace_id": "w1",
            "pane_id": "w1:p1",
            "agent_id": "codex",
            "provider_kind": "codex",
            "runtime_generation": 12,
            "seq": 2,
            "state": "working",
            "occurred_at": "2026-08-20T12:00:00Z",
        }
        values.update(overrides)
        return HerdrRuntimeEvent(**values)

    assert projector.apply_event(event()) is True
    assert projector.status_for_pane("w1:p1").to_record()["runtime_state"] == "working"  # type: ignore[union-attr]

    refreshed_binding = HerdrRuntimeBinding(
        project_id="proj-1",
        server_id="server-1",
        server_version="0.8.2",
        api_schema="Herdr API",
        session_name="ccb-project-1",
        workspace_id="w1",
        runtime_generation=12,
        ready=True,
        capabilities={},
        panes=(
            HerdrRuntimeBoundPane(
                slot="codex",
                pane_id="w1:p1",
                agent_id="codex",
                provider_kind="codex",
                state="idle",
                state_seq=10,
            ),
            HerdrRuntimeBoundPane(
                slot="claude",
                pane_id="w1:p2",
                agent_id="claude",
                provider_kind="claude",
                state="blocked",
                state_seq=3,
            ),
        ),
    )
    projector.refresh(refreshed_binding)

    assert projector.status_for_pane("w1:p1").to_record()["runtime_state"] == "idle"  # type: ignore[union-attr]
    assert projector.status_for_pane("w1:p1").to_record()["seq"] == 10  # type: ignore[union-attr]
    assert projector.status_for_pane("w1:p2").to_record()["runtime_state"] == "blocked"  # type: ignore[union-attr]
    assert projector.apply_event(event(seq=9, state="blocked")) is False
    assert projector.apply_event(event(event_id="fresh", seq=11, state="working")) is True
    assert projector.status_for_pane("w1:p1").to_record()["runtime_state"] == "working"  # type: ignore[union-attr]


def test_herdr_runtime_event_projector_refreshes_from_snapshot_and_drops_missing_panes() -> None:
    binding = HerdrRuntimeBinding(
        project_id="proj-1",
        server_id="server-1",
        server_version="0.8.2",
        api_schema="Herdr API",
        session_name="ccb-project-1",
        workspace_id="w1",
        runtime_generation=13,
        ready=True,
        capabilities={},
        panes=(
            HerdrRuntimeBoundPane(
                slot="codex",
                pane_id="w1:p1",
                agent_id="codex",
                provider_kind="codex",
                state="idle",
                state_seq=1,
            ),
            HerdrRuntimeBoundPane(
                slot="claude",
                pane_id="w1:p2",
                agent_id="claude",
                provider_kind="claude",
                state="blocked",
                state_seq=2,
            ),
        ),
    )
    projector = HerdrRuntimeEventProjector(binding)

    snapshot = {
        "panes": [
            {"pane_id": "w1:p1", "workspace_id": "w1", "state": "working", "state_seq": 7},
        ]
    }
    changed_pane_ids = projector.refresh(binding, snapshot=snapshot)

    assert changed_pane_ids == ("w1:p1", "w1:p2")
    assert projector.status_for_pane("w1:p1").to_record()["runtime_state"] == "working"  # type: ignore[union-attr]
    assert projector.status_for_pane("w1:p1").to_record()["seq"] == 7  # type: ignore[union-attr]
    assert projector.status_for_pane("w1:p2") is None


def test_herdr_runtime_event_projector_refreshes_generation_without_reusing_old_events() -> None:
    binding = HerdrRuntimeBinding(
        project_id="proj-1",
        server_id="server-1",
        server_version="0.8.2",
        api_schema="Herdr API",
        session_name="ccb-project-1",
        workspace_id="w1",
        runtime_generation=12,
        ready=True,
        capabilities={},
        panes=(
            HerdrRuntimeBoundPane(
                slot="codex",
                pane_id="w1:p1",
                agent_id="codex",
                provider_kind="codex",
                state="working",
                state_seq=5,
            ),
        ),
    )
    projector = HerdrRuntimeEventProjector(binding)

    projector.refresh(
        HerdrRuntimeBinding(
            project_id="proj-1",
            server_id="server-1",
            server_version="0.8.2",
            api_schema="Herdr API",
            session_name="ccb-project-1",
            workspace_id="w1",
            runtime_generation=13,
            ready=True,
            capabilities={},
            panes=(
                HerdrRuntimeBoundPane(
                    slot="codex",
                    pane_id="w1:p1",
                    agent_id="codex",
                    provider_kind="codex",
                    state="idle",
                    state_seq=1,
                ),
            ),
        ),
        snapshot={
            "panes": [
                {"pane_id": "w1:p1", "workspace_id": "w1", "state": "idle", "state_seq": 1},
            ]
        },
    )

    old_event = HerdrRuntimeEvent(
        event_type="agent_state_changed",
        event_id="evt-old",
        server_id="server-1",
        session_name="ccb-project-1",
        workspace_id="w1",
        pane_id="w1:p1",
        agent_id="codex",
        provider_kind="codex",
        runtime_generation=12,
        seq=6,
        state="blocked",
        occurred_at="2026-08-20T12:00:00Z",
    )

    assert projector.apply_event(old_event) is False
    assert projector.status_for_pane("w1:p1").to_record()["runtime_state"] == "idle"  # type: ignore[union-attr]
    assert projector.status_for_pane("w1:p1").to_record()["seq"] == 1  # type: ignore[union-attr]


def test_poll_runtime_snapshot_refreshes_projector_from_backend_snapshot() -> None:
    binding = HerdrRuntimeBinding(
        project_id="proj-1",
        server_id="server-1",
        server_version="0.8.2",
        api_schema="Herdr API",
        session_name="ccb-project-1",
        workspace_id="w1",
        runtime_generation=13,
        ready=True,
        capabilities={},
        panes=(
            HerdrRuntimeBoundPane(
                slot="codex",
                pane_id="w1:p1",
                agent_id="codex",
                provider_kind="codex",
                state="idle",
                state_seq=1,
            ),
        ),
    )
    projector = HerdrRuntimeEventProjector(binding)

    class _Backend:
        def runtime_snapshot(self) -> dict[str, object]:
            return {
                "panes": [
                    {"pane_id": "w1:p1", "workspace_id": "w1", "state": "blocked", "seq": 9},
                ]
            }

    changed_pane_ids = poll_runtime_snapshot(projector, binding, _Backend())

    assert changed_pane_ids == ("w1:p1",)
    status = projector.status_for_pane("w1:p1")
    assert status is not None
    assert status.runtime_state == "blocked"
    assert status.state == "waiting_for_user"
    assert status.seq == 9


def test_poll_runtime_snapshot_ignores_foreign_workspace_snapshot() -> None:
    binding = HerdrRuntimeBinding(
        project_id="proj-1",
        server_id="server-1",
        server_version="0.8.2",
        api_schema="Herdr API",
        session_name="ccb-project-1",
        workspace_id="w1",
        runtime_generation=13,
        ready=True,
        capabilities={},
        panes=(
            HerdrRuntimeBoundPane(
                slot="codex",
                pane_id="shared:pane",
                agent_id="codex",
                provider_kind="codex",
                state="idle",
                state_seq=1,
            ),
        ),
    )
    projector = HerdrRuntimeEventProjector(binding)

    class _Backend:
        def runtime_snapshot(self) -> dict[str, object]:
            return {
                "panes": [
                    {
                        "pane_id": "shared:pane",
                        "workspace_id": "other-workspace",
                        "state": "blocked",
                        "seq": 9,
                    },
                ]
            }

    changed_pane_ids = poll_runtime_snapshot(projector, binding, _Backend())

    assert changed_pane_ids == ("shared:pane",)
    assert projector.status_for_pane("shared:pane") is None


def test_herdr_state_mapping_preserves_done_and_unknown_semantics() -> None:
    assert map_herdr_state_to_ccb("working") == "working"
    assert map_herdr_state_to_ccb("blocked") == "waiting_for_user"
    assert map_herdr_state_to_ccb("idle") == "idle"
    assert map_herdr_state_to_ccb("done") == "idle"
    assert map_herdr_state_to_ccb("unknown") == "unknown"


def test_ensure_runtime_submits_manifest_to_bootstrap_without_capability_file() -> None:
    manifest = HerdrRuntimeManifest(
        project_id="proj-1",
        project_root="E:/repo",
        session_name="ccb-proj-1",
        generation=1,
        workspaces=(),
    )
    calls: list[dict[str, object]] = []

    def bootstrap(**kwargs):
        calls.append(kwargs)
        return {
            "ok": True,
            "herdr_session": "ccb-proj-1",
            "socket_ref": "herdr://ccb-proj-1",
            "warnings": ["using existing session"],
        }

    result = ensure_runtime(
        manifest,
        restore_token="secret-restore-token",
        herdr_exe="C:/Herdr/herdr.exe",
        bootstrap_fn=bootstrap,
    )

    assert result.ok is True
    assert result.socket_ref == "herdr://ccb-proj-1"
    assert result.to_record() == {
        "ok": True,
        "project_id": "proj-1",
        "session_name": "ccb-proj-1",
        "generation": 1,
        "socket_ref": "herdr://ccb-proj-1",
        "reason": None,
        "warnings": ["using existing session"],
    }
    assert "secret-restore-token" not in str(result.to_record())
    assert calls == [
        {
            "herdr_exe": "C:/Herdr/herdr.exe",
            "herdr_session": None,
            "auto_start_server": True,
            "start_session": "ccb-proj-1",
        }
    ]


def test_ensure_runtime_returns_structured_failure() -> None:
    manifest = HerdrRuntimeManifest(
        project_id="proj-1",
        project_root="E:/repo",
        session_name="ccb-proj-1",
        generation=1,
        workspaces=(),
    )

    result = ensure_runtime(
        manifest,
        bootstrap_fn=lambda **_kwargs: {"ok": False, "reason": "Herdr missing"},
    )

    assert result.ok is False
    assert result.reason == "Herdr missing"
    assert result.to_record()["session_name"] == "ccb-proj-1"
