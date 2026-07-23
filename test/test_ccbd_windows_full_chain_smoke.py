from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "ccbd_windows_full_chain_smoke.py"
SPEC = importlib.util.spec_from_file_location("ccbd_windows_full_chain_smoke", SCRIPT_PATH)
smoke = importlib.util.module_from_spec(SPEC)
assert SPEC is not None and SPEC.loader is not None
sys.modules[SPEC.name] = smoke
SPEC.loader.exec_module(smoke)


def _command(name: str, *, returncode: int = 0, argv: list[str] | None = None, env: dict | None = None) -> dict:
    default_argv = {
        "ccb-start": ["ccb", "--project", "E:/tmp/demo"],
        "ccb-ping-ccbd": ["ccb", "--project", "E:/tmp/demo", "ping", "ccbd"],
        "ccb-doctor": ["ccb", "--project", "E:/tmp/demo", "doctor"],
        "ccb-ask": ["ccb", "--project", "E:/tmp/demo", "ask", "--artifact-reply", "ccb_self", "--", "smoke"],
        "ccb-kill-force": ["ccb", "--project", "E:/tmp/demo", "kill", "-f"],
    }
    return {
        "name": name,
        "argv": argv or default_argv.get(name, ["ccb", "--project", "E:/tmp/demo", name]),
        "cwd": "E:/tmp/demo",
        "env_allowlist": env or {},
        "started_at": "2026-07-23T00:00:00Z",
        "duration_ms": 1.0,
        "returncode": returncode,
        "stdout_path": f"commands/{name}.stdout.txt",
        "stderr_path": f"commands/{name}.stderr.txt",
    }


def _pass_transcript() -> dict:
    return {
        "schema_version": 1,
        "host_kind": "native_windows",
        "runner_host": {
            "shell": "PowerShell",
            "edition": "Core",
            "version": "7.5.4",
            "executable": "C:/Program Files/PowerShell/7/pwsh.exe",
        },
        "control_plane": "ccbd",
        "backend_impl": "rmux",
        "probe_bypass": False,
        "backend_selection_source": "env",
        "ccbd_transport": "tcp_loopback",
        "dependency_status": {
            "ccbd-windows-tcp-loopback-transport": "ready",
            "ccbd-rmux-namespace-lifecycle": "ready",
            "accelerator-transport-windows-guard": "ready",
            "ccbd-windows-process-liveness": "ready",
        },
        "ask_case_kind": "local_provider",
        "ask_case": {"provider": "ccb_self", "task_id": "job_smoke123", "reply_path": "commands/ccb-ask.stdout.txt"},
        "verdict": "pass",
        "failure_class": "none",
        "commands": [
            _command("ccb-start"),
            _command("ccb-ping-ccbd"),
            _command("ccb-doctor"),
            _command("ccb-ask"),
            _command("ccb-kill-force"),
        ],
        "artifacts": {
            "ping": "commands/ccb-ping-ccbd.stdout.txt",
            "doctor": "commands/ccb-doctor.stdout.txt",
            "ask": "commands/ccb-ask.stdout.txt",
            "runtime_session": "commands/ccb-ps-after-ask.stdout.txt",
            "cleanup": "commands/ccb-kill-force.stdout.txt",
        },
        "evidence": {
            "control_plane": {"mounted": True, "ping_target": "ccbd"},
            "backend_selection": {
                "backend_impl": "rmux",
                "effective_backend": "rmux",
                "source": "env",
                "namespace_backend_impl": "rmux",
            },
            "transport": {"kind": "tcp_loopback"},
            "ask": {
                "provider": "ccb_self",
                "task_id": "job_smoke123",
                "reply_path": "commands/ccb-ask.stdout.txt",
                "terminal_state": "completed",
                "runtime_session": {
                    "backend_impl": "rmux",
                    "runtime_ref": "rmux-session-1",
                    "evidence_path": "commands/ccb-ps-after-ask.stdout.txt",
                },
            },
            "cleanup": {
                "endpoint_removed": True,
                "token_removed": True,
                "rmux_namespace_removed": True,
                "session_removed": True,
                "owned_process_residue": [],
            },
        },
        "redaction_summary": {"redacted": True, "raw_retention_policy": "redacted_artifacts_only"},
        "cleanup": {"status": "cleaned", "ok": True, "evidence": "commands/ccb-kill-force.stdout.txt"},
        "final_status": "pass",
    }


def _evaluate(payload: dict) -> smoke.SmokeEvaluation:
    return smoke.evaluate_transcript(payload, scan_artifacts=False)


def test_pass_transcript_is_accepted() -> None:
    result = _evaluate(_pass_transcript())

    assert result.ok is True
    assert result.verdict == "pass"
    assert result.failure_class == "none"


def test_missing_required_fields_fail_closed() -> None:
    payload = _pass_transcript()
    del payload["host_kind"]

    result = _evaluate(payload)

    assert result.ok is False
    assert result.verdict == "test_design_failure"
    assert any("missing required fields" in error for error in result.errors)


def test_non_native_host_cannot_pass() -> None:
    payload = _pass_transcript()
    payload["host_kind"] = "wsl"

    result = _evaluate(payload)

    assert result.verdict == "test_design_failure"
    assert any("host_kind" in error for error in result.errors)


def test_runner_host_is_required() -> None:
    payload = _pass_transcript()
    del payload["runner_host"]

    result = _evaluate(payload)

    assert result.verdict == "test_design_failure"
    assert any("missing required fields" in error for error in result.errors)


def test_probe_bypass_and_fake_backend_cannot_pass() -> None:
    payload = _pass_transcript()
    payload["probe_bypass"] = True
    payload["backend_impl"] = "fake"

    result = _evaluate(payload)

    assert result.verdict == "test_design_failure"
    assert any("probe_bypass" in error for error in result.errors)
    assert any("backend_impl" in error for error in result.errors)


def test_direct_rmux_core_command_cannot_pass() -> None:
    payload = _pass_transcript()
    payload["commands"][0] = _command("ccb-start", argv=["rmux", "new-session"])

    result = _evaluate(payload)

    assert result.verdict == "test_design_failure"
    assert any("direct rmux" in error for error in result.errors)


def test_probe_script_command_cannot_pass() -> None:
    payload = _pass_transcript()
    payload["commands"].append(_command("debug-probe", argv=["python", "scripts/probe_rmux_capability.py"]))

    result = _evaluate(payload)

    assert result.verdict == "test_design_failure"
    assert any("probe_rmux" in error for error in result.errors)


def test_python_core_command_must_invoke_ccb_script() -> None:
    payload = _pass_transcript()
    payload["commands"][3] = _command("ccb-ask", argv=["python", "-c", "print('fake')"])

    result = _evaluate(payload)

    assert result.verdict == "test_design_failure"
    assert any("must execute through ccb" in error for error in result.errors)


def test_core_command_must_match_expected_subcommand() -> None:
    payload = _pass_transcript()
    payload["commands"][3] = _command("ccb-ask", argv=["ccb", "--project", "E:/tmp/demo", "--version"])

    result = _evaluate(payload)

    assert result.verdict == "test_design_failure"
    assert any("expected ccb subcommand" in error for error in result.errors)


def test_ask_job_action_cannot_replace_provider_ask() -> None:
    payload = _pass_transcript()
    payload["commands"][3] = _command("ccb-ask", argv=["ccb", "--project", "E:/tmp/demo", "ask", "get", "job_1"])

    result = _evaluate(payload)

    assert result.verdict == "test_design_failure"
    assert any("expected ccb subcommand" in error for error in result.errors)

    payload["commands"][3] = _command("ccb-ask", argv=["ccb", "--project", "E:/tmp/demo", "ask", "cancel", "job_1"])
    result = _evaluate(payload)
    assert result.verdict == "test_design_failure"
    assert any("expected ccb subcommand" in error for error in result.errors)


def test_provider_failure_is_not_system_pass() -> None:
    payload = _pass_transcript()
    payload["commands"][3] = _command("ccb-ask", returncode=2)
    payload["verdict"] = "provider_failure"
    payload["failure_class"] = "provider_failure"
    payload["final_status"] = "failed"

    result = _evaluate(payload)

    assert result.ok is False
    assert result.verdict == "provider_failure"
    assert result.failure_class == "provider_failure"


def test_dependency_pending_is_blocked() -> None:
    payload = _pass_transcript()
    payload["dependency_status"]["ccbd-windows-tcp-loopback-transport"] = "pending"
    payload["verdict"] = "blocked"
    payload["failure_class"] = "dependency_pending"
    payload["final_status"] = "blocked"

    result = _evaluate(payload)

    assert result.verdict == "blocked"
    assert result.failure_class == "dependency_pending"
    assert result.final_status == "blocked"


def test_cleanup_failure_is_system_failure() -> None:
    payload = _pass_transcript()
    payload["cleanup"] = {"status": "failed", "ok": False}

    result = _evaluate(payload)

    assert result.verdict == "system_failure"
    assert result.failure_class == "system_failure"


def test_missing_structured_evidence_cannot_pass() -> None:
    payload = _pass_transcript()
    del payload["evidence"]["backend_selection"]

    result = _evaluate(payload)

    assert result.verdict == "test_design_failure"
    assert any("evidence missing fields" in error for error in result.errors)


def test_backend_selection_requires_rmux_namespace() -> None:
    payload = _pass_transcript()
    payload["evidence"]["backend_selection"]["namespace_backend_impl"] = "tmux"

    result = _evaluate(payload)

    assert result.verdict == "test_design_failure"
    assert any("namespace_backend_impl" in error for error in result.errors)


def test_backend_selection_source_must_match_top_level() -> None:
    payload = _pass_transcript()
    payload["backend_selection_source"] = "cli"

    result = _evaluate(payload)

    assert result.verdict == "test_design_failure"
    assert any("source must match backend_selection_source" in error for error in result.errors)


def test_ask_evidence_requires_task_and_runtime_session() -> None:
    payload = _pass_transcript()
    payload["evidence"]["ask"]["task_id"] = ""
    payload["evidence"]["ask"]["runtime_session"] = {}

    result = _evaluate(payload)

    assert result.verdict == "test_design_failure"
    assert any("evidence.ask.task_id" in error for error in result.errors)
    assert any("runtime_session.backend_impl" in error for error in result.errors)


def test_cleanup_evidence_requires_residue_checks() -> None:
    payload = _pass_transcript()
    payload["evidence"]["cleanup"]["token_removed"] = False

    result = _evaluate(payload)

    assert result.verdict == "test_design_failure"
    assert any("residue checks failed" in error for error in result.errors)


def test_fake_provider_requires_test_entrypoint() -> None:
    payload = _pass_transcript()
    payload["ask_case_kind"] = "fake_provider"

    result = _evaluate(payload)

    assert result.verdict == "test_design_failure"
    assert any("CCB_TEST_ENTRYPOINT" in error for error in result.errors)

    payload["commands"][3]["env_allowlist"] = {"CCB_TEST_ENTRYPOINT": "1"}
    result = _evaluate(payload)
    assert result.ok is True


def test_redaction_removes_tokens_passwords_and_home_paths(monkeypatch) -> None:
    monkeypatch.setenv("USERPROFILE", r"C:\Users\Alice")

    text = (
        r'C:\Users\Alice\.ccb {"password": "hunter2", "api_key": "plain", '
        r'"access_token": "access-secret", "refresh_token": "refresh-secret"} '
        r'Bearer abc.def sk-secret123'
    )
    redacted = smoke.redact_text(text)

    assert "hunter2" not in redacted
    assert "plain" not in redacted
    assert "access-secret" not in redacted
    assert "refresh-secret" not in redacted
    assert "Bearer abc.def" not in redacted
    assert "sk-secret123" not in redacted
    assert "[USER_HOME]" in redacted
    assert redacted.count("[REDACTED]") >= 6
    assert smoke.redact_text("stage=ask-evidence") == "stage=ask-evidence"


def test_artifact_secret_scan_fails_closed(tmp_path: Path) -> None:
    payload = _pass_transcript()
    transcript_path = tmp_path / "transcript.json"
    for rel_path in payload["artifacts"].values():
        artifact_path = tmp_path / rel_path
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(
            "ccbd tcp_loopback job_smoke123 SMOKE_OK\n"
            "backend_selection_effective: rmux\n"
            "ccbd_namespace_backend_impl: rmux\n"
            "binding: status=bound runtime=rmux:%1\n",
            encoding="utf-8",
        )
    (tmp_path / payload["artifacts"]["ask"]).write_text("token=sk-secret123\n", encoding="utf-8")
    transcript_path.write_text(json.dumps(payload), encoding="utf-8")

    result = smoke.evaluate_transcript(payload, transcript_path=transcript_path, scan_artifacts=True)

    assert result.verdict == "test_design_failure"
    assert any("artifact redaction failed" in error for error in result.errors)


def test_transcript_redaction_scan_catches_escaped_home_path(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("USERPROFILE", r"C:\Users\Alice")
    payload = _pass_transcript()
    payload["commands"][0]["cwd"] = r"C:\\Users\\Alice\\repo"

    result = smoke.evaluate_transcript(payload, transcript_path=tmp_path / "transcript.json", scan_artifacts=False)

    assert result.verdict == "test_design_failure"
    assert any("transcript redaction failed" in error for error in result.errors)


def test_artifact_scan_requires_backend_transport_and_nonempty_ask(tmp_path: Path) -> None:
    payload = _pass_transcript()
    transcript_path = tmp_path / "transcript.json"
    for rel_path in payload["artifacts"].values():
        artifact_path = tmp_path / rel_path
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text("ccbd\n", encoding="utf-8")
    (tmp_path / payload["artifacts"]["ask"]).write_text("", encoding="utf-8")
    transcript_path.write_text(json.dumps(payload), encoding="utf-8")

    result = smoke.evaluate_transcript(payload, transcript_path=transcript_path, scan_artifacts=True)

    assert result.verdict == "test_design_failure"
    assert any("backend_selection_effective: rmux" in error for error in result.errors)
    assert any("ping or doctor artifact" in error for error in result.errors)
    assert any("ask artifact must not be empty" in error for error in result.errors)


def test_runtime_identity_must_match_runtime_artifact(tmp_path: Path) -> None:
    payload = _pass_transcript()
    transcript_path = tmp_path / "transcript.json"
    for key, rel_path in payload["artifacts"].items():
        artifact_path = tmp_path / rel_path
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        text = (
            "ccbd tcp_loopback job_smoke123 SMOKE_OK\n"
            "backend_selection_effective: rmux\n"
            "ccbd_namespace_backend_impl: rmux\n"
            "runtime_ref: rmux-session-1\n"
        )
        if key == "runtime_session":
            text = "backend_impl: rmux\nruntime_ref: different-session\n"
        artifact_path.write_text(text, encoding="utf-8")
    transcript_path.write_text(json.dumps(payload), encoding="utf-8")

    result = smoke.evaluate_transcript(payload, transcript_path=transcript_path, scan_artifacts=True)

    assert result.verdict == "test_design_failure"
    assert any("identity must appear as a labeled field" in error for error in result.errors)


def test_runtime_identity_accepts_ccb_ps_binding_line(tmp_path: Path) -> None:
    payload = _pass_transcript()
    payload["evidence"]["ask"]["runtime_session"]["runtime_ref"] = "rmux:%1"
    transcript_path = tmp_path / "transcript.json"
    for key, rel_path in payload["artifacts"].items():
        artifact_path = tmp_path / rel_path
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        text = (
            "ccbd tcp_loopback job_smoke123 SMOKE_OK\n"
            "backend_selection_effective: rmux\n"
            "ccbd_namespace_backend_impl: rmux\n"
            "runtime_ref: rmux:%1\n"
        )
        if key == "runtime_session":
            text = (
                "agent: name=demo state=idle provider=fake queue=0\n"
                "binding: status=partial runtime=rmux:%1 session=None terminal=rmux pane=%1 active_pane=%1\n"
            )
        artifact_path.write_text(text, encoding="utf-8")
    transcript_path.write_text(json.dumps(payload), encoding="utf-8")

    result = smoke.evaluate_transcript(payload, transcript_path=transcript_path, scan_artifacts=True)

    assert result.ok is True


def test_runtime_identity_cannot_be_generic_marker(tmp_path: Path) -> None:
    payload = _pass_transcript()
    payload["evidence"]["ask"]["runtime_session"]["runtime_ref"] = "rmux"
    transcript_path = tmp_path / "transcript.json"
    for key, rel_path in payload["artifacts"].items():
        artifact_path = tmp_path / rel_path
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        text = (
            "ccbd tcp_loopback job_smoke123 SMOKE_OK\n"
            "backend_selection_effective: rmux\n"
            "ccbd_namespace_backend_impl: rmux\n"
        )
        if key == "runtime_session":
            text = "backend_impl: rmux\nruntime_ref: rmux\n"
        artifact_path.write_text(text, encoding="utf-8")
    transcript_path.write_text(json.dumps(payload), encoding="utf-8")

    result = smoke.evaluate_transcript(payload, transcript_path=transcript_path, scan_artifacts=True)

    assert result.verdict == "test_design_failure"
    assert any("generic backend/control marker" in error for error in result.errors)


def test_runtime_identity_requires_labeled_artifact_field(tmp_path: Path) -> None:
    payload = _pass_transcript()
    transcript_path = tmp_path / "transcript.json"
    for key, rel_path in payload["artifacts"].items():
        artifact_path = tmp_path / rel_path
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        text = (
            "ccbd tcp_loopback job_smoke123 SMOKE_OK\n"
            "backend_selection_effective: rmux\n"
            "ccbd_namespace_backend_impl: rmux\n"
            "runtime_ref: rmux-session-1\n"
        )
        if key == "runtime_session":
            text = "backend_impl: rmux\nrmux-session-1\n"
        artifact_path.write_text(text, encoding="utf-8")
    transcript_path.write_text(json.dumps(payload), encoding="utf-8")

    result = smoke.evaluate_transcript(payload, transcript_path=transcript_path, scan_artifacts=True)

    assert result.verdict == "test_design_failure"
    assert any("labeled field" in error for error in result.errors)


def test_runtime_evidence_path_must_match_artifacts_runtime_session() -> None:
    payload = _pass_transcript()
    payload["evidence"]["ask"]["runtime_session"]["evidence_path"] = "commands/other.txt"

    result = _evaluate(payload)

    assert result.verdict == "test_design_failure"
    assert any("artifacts.runtime_session" in error for error in result.errors)


def test_scope_guard_allows_validation_assets() -> None:
    paths = [
        "scripts/ccbd_windows_full_chain_smoke.py",
        "scripts/ccbd-windows-full-chain-smoke.ps1",
        "test/test_ccbd_windows_full_chain_smoke.py",
        "lib/ccbd/start_runtime/agent_runtime.py",
        "lib/terminal_runtime/rmux_backend_runtime/panes.py",
        "artifacts/ccbd-windows-full-chain-smoke/transcript.json",
        ".codestable/goals/2026-07-23-ccbd-windows-full-chain-smoke/iterations/001.md",
    ]

    result = smoke.evaluate_scope_paths(paths)

    assert result.ok is True
    assert ".codestable/goals/2026-07-23-ccbd-windows-full-chain-smoke/iterations/001.md" in result.evidence["changed_paths"]


def test_scope_guard_rejects_runtime_docs_provider_and_packaging() -> None:
    result = smoke.evaluate_scope_paths(
        [
            "lib/terminal_runtime/tmux_backend.py",
            "lib/provider_pane_status/codex_pane.py",
            "docs/manuals/user-guide/index.md",
            "package.json",
            "scripts/probe_rmux_capability.py",
        ]
    )

    assert result.verdict == "test_design_failure"
    forbidden = result.evidence["forbidden_paths"]
    assert "lib/terminal_runtime/tmux_backend.py" in forbidden
    assert "lib/provider_pane_status/codex_pane.py" in forbidden
    assert "docs/manuals/user-guide/index.md" in forbidden
    assert "package.json" in forbidden
    assert "scripts/probe_rmux_capability.py" in forbidden


def test_scope_guard_rejects_unknown_paths_fail_closed() -> None:
    result = smoke.evaluate_scope_paths(
        [
            ".codestable/issues/other/fix-note.md",
            "artifacts/other/transcript.json",
            "pyproject.toml",
            "setup.cfg",
        ]
    )

    assert result.verdict == "test_design_failure"
    forbidden = result.evidence["forbidden_paths"]
    assert ".codestable/issues/other/fix-note.md" in forbidden
    assert "artifacts/other/transcript.json" in forbidden
    assert "pyproject.toml" in forbidden
    assert "setup.cfg" in forbidden
