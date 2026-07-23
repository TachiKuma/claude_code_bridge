from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "rmux_windows_validation_matrix.py"
SPEC = importlib.util.spec_from_file_location("rmux_windows_validation_matrix", SCRIPT_PATH)
matrix = importlib.util.module_from_spec(SPEC)
assert SPEC is not None and SPEC.loader is not None
sys.modules[SPEC.name] = matrix
SPEC.loader.exec_module(matrix)


def _command(name: str, returncode: int = 0) -> dict[str, object]:
    argv = ["python", "ccb.py"]
    if name == "ccb-ping-ccbd":
        argv += ["ping", "ccbd"]
    elif name == "ccb-doctor":
        argv += ["doctor"]
    elif name == "ccb-ask":
        argv += ["ask", "demo", "--", "hello"]
    elif name == "ccb-kill-force":
        argv += ["kill", "-f"]
    return {
        "name": name,
        "argv": argv,
        "cwd": "C:/tmp/project",
        "env_allowlist": {"CCB_MUX_BACKEND": "rmux"},
        "started_at": "2026-07-23T00:00:00Z",
        "duration_ms": 1,
        "returncode": returncode,
        "stdout_path": f"commands/{name}.stdout.txt",
        "stderr_path": f"commands/{name}.stderr.txt",
    }


def _transcript() -> dict[str, object]:
    return {
        "schema_version": 1,
        "host_kind": "native_windows",
        "control_plane": "ccbd",
        "backend_impl": "rmux",
        "probe_bypass": False,
        "backend_selection_source": "env",
        "ccbd_transport": "tcp_loopback",
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
        "evidence": {},
        "redaction_summary": {
            "redacted": True,
            "raw_retention_policy": "redacted_artifacts_only",
        },
        "cleanup": {
            "status": "cleaned",
            "ok": True,
            "evidence": {
                "endpoint_removed": True,
                "token_removed": True,
                "rmux_namespace_removed": True,
                "session_removed": True,
                "owned_process_residue": [],
            },
        },
        "scenario_results": {
            "start_ping": {"observed": True, "classification": "pass"},
            "ask": {"observed": True, "classification": "pass"},
            "kill": {"observed": True, "classification": "pass"},
            "diagnostics": {"observed": True, "classification": "pass"},
        },
    }


def _full_transcript() -> dict[str, object]:
    payload = _transcript()
    payload["scenario_results"] = {
        scenario: {"observed": True, "classification": "pass"}
        for scenario in matrix.CORE_SCENARIOS
    }
    return payload


def test_manifest_covers_core_scenarios_and_true_host_fields() -> None:
    result = matrix.validate_manifest(matrix.matrix_manifest())

    assert result.ok, result.errors
    scenarios = {case["scenario"] for case in matrix.matrix_manifest()}
    lanes = {case["lane"] for case in matrix.matrix_manifest()}
    assert matrix.CORE_SCENARIOS <= scenarios
    assert {"fake", "provider_blackbox", "windows_true_host", "manual_transcript"} <= lanes
    for case in matrix.matrix_manifest():
        if case["lane"] != "windows_true_host":
            continue
        assert case["host_kind"] == "native_windows"
        assert case["control_plane"] == "ccbd"
        assert case["probe_bypass"] is False
        assert case["backend_impl"] == "rmux"
        assert case["backend_selection_source"] != "unknown"


def test_fake_subset_report_passes_selected_but_not_full_matrix() -> None:
    report = matrix.build_report(lane="fake", scope="subset", include_fake_evidence=True)

    assert report["selected_cases_status"] == "pass"
    assert report["full_matrix_status"] == "incomplete"
    assert all(row["lane"] == "fake" for row in report["rows"])
    assert all(row["details"]["not_true_host"] is True for row in report["rows"])


def test_missing_evidence_fails_closed() -> None:
    report = matrix.build_report(lane="windows_true_host", scope="full")

    assert report["selected_cases_status"] == "incomplete"
    assert report["full_matrix_status"] == "incomplete"
    assert {row["classification"] for row in report["rows"]} == {"missing_evidence"}


def test_transcript_rejects_probe_bypass() -> None:
    payload = _transcript()
    payload["commands"] = [_command("ccb-start"), {"name": "ccb-ping-ccbd", "argv": ["rmux", "list-sessions"]}]

    result = matrix.evaluate_transcript(payload)

    assert result.ok is False
    assert result.verdict == "test_design_failure"
    assert any("direct rmux" in error for error in result.errors)


def test_transcript_allows_named_direct_rmux_diagnostics() -> None:
    payload = _transcript()
    commands = list(payload["commands"])
    commands.append({"name": "preflight-rmux-version", "argv": ["rmux", "-V"], "returncode": 0})
    commands.append({"name": "cleanup-rmux-list-sessions", "argv": ["rmux", "list-sessions"], "returncode": 0})
    payload["commands"] = commands

    result = matrix.evaluate_transcript(payload)

    assert result.ok, result.errors


def test_named_direct_rmux_diagnostics_cannot_run_other_rmux_commands() -> None:
    payload = _transcript()
    commands = list(payload["commands"])
    commands.append({"name": "preflight-rmux-version", "argv": ["rmux", "kill-session", "-t", "x"], "returncode": 0})
    payload["commands"] = commands

    result = matrix.evaluate_transcript(payload)

    assert result.ok is False
    assert any("direct rmux" in error for error in result.errors)


def test_named_direct_rmux_diagnostics_do_not_allow_lowercase_short_version() -> None:
    payload = _transcript()
    commands = list(payload["commands"])
    commands.append({"name": "preflight-rmux-version", "argv": ["rmux", "-v"], "returncode": 0})
    payload["commands"] = commands

    result = matrix.evaluate_transcript(payload)

    assert result.ok is False
    assert any("direct rmux" in error for error in result.errors)


def test_named_direct_rmux_diagnostics_do_not_allow_psmux() -> None:
    payload = _transcript()
    commands = list(payload["commands"])
    commands.append({"name": "cleanup-rmux-list-sessions", "argv": ["psmux", "list-sessions"], "returncode": 0})
    payload["commands"] = commands

    result = matrix.evaluate_transcript(payload)

    assert result.ok is False
    assert any("direct rmux" in error for error in result.errors)


def test_provider_failure_is_not_system_failure() -> None:
    payload = _transcript()
    commands = list(payload["commands"])
    commands[3] = _command("ccb-ask", returncode=2)
    payload["commands"] = commands

    result = matrix.evaluate_transcript(payload)

    assert result.verdict == "provider_failure"
    assert result.failure_class == "provider_failure"


def test_provider_failure_in_optional_ask_is_not_system_failure() -> None:
    payload = _transcript()
    commands = list(payload["commands"])
    commands.append(_command("ccb-ask-reviewer", returncode=2))
    payload["commands"] = commands

    result = matrix.evaluate_transcript(payload)

    assert result.verdict == "provider_failure"
    assert result.failure_class == "provider_failure"


def test_provider_failure_takes_priority_over_mixed_system_failure() -> None:
    payload = _transcript()
    commands = list(payload["commands"])
    commands.append(_command("ccb-ask-reviewer", returncode=2))
    commands.append(_command("ccb-doctor", returncode=1))
    payload["commands"] = commands

    result = matrix.evaluate_transcript(payload)

    assert result.verdict == "provider_failure"
    assert result.failure_class == "provider_failure"


def test_cleanup_list_sessions_failure_is_valid_after_successful_cleanup() -> None:
    payload = _transcript()
    commands = list(payload["commands"])
    commands.append({"name": "cleanup-rmux-list-sessions", "argv": ["rmux", "list-sessions"], "returncode": 1})
    payload["commands"] = commands

    result = matrix.evaluate_transcript(payload)

    assert result.ok, result.errors


def test_invalid_transcript_cannot_declare_passing_rows(tmp_path: Path) -> None:
    payload = _transcript()
    payload["host_kind"] = "wsl"
    transcript = tmp_path / "manual-transcript.json"
    transcript.write_text(json.dumps(payload), encoding="utf-8")

    report = matrix.build_report(scope="full", transcripts=[transcript])

    start_ping = next(row for row in report["rows"] if row["case_id"] == "windows-true-host-start-ping")
    assert start_ping["classification"] == "test_design_failure"
    assert report["full_matrix_status"] == "fail"


def test_missing_transcript_classification_fails_closed(tmp_path: Path) -> None:
    payload = _transcript()
    payload["scenario_results"] = {"start_ping": {"observed": True}}
    transcript = tmp_path / "manual-transcript.json"
    transcript.write_text(json.dumps(payload), encoding="utf-8")

    report = matrix.build_report(lane="windows_true_host", scope="full", transcripts=[transcript])

    start_ping = next(row for row in report["rows"] if row["case_id"] == "windows-true-host-start-ping")
    assert start_ping["classification"] == "test_design_failure"
    assert report["full_matrix_status"] == "fail"


def test_provider_failure_prevents_full_matrix_pass() -> None:
    rows = []
    for case in matrix.matrix_manifest():
        if case["lane"] == "windows_true_host":
            classification = "provider_failure" if case["scenario"] == "ask" else "pass"
            rows.append({"case_id": case["case_id"], "classification": classification, "observed": True})

    report = matrix.build_report(scope="full", evidence_rows=rows)

    assert report["selected_cases_status"] == "fail"
    assert report["full_matrix_status"] == "fail"


def test_valid_non_success_is_limited_to_bounded_scenarios() -> None:
    rows = []
    for case in matrix.matrix_manifest():
        if case["lane"] == "windows_true_host":
            rows.append({"case_id": case["case_id"], "classification": "valid_non_success", "observed": True})

    report = matrix.build_report(scope="full", evidence_rows=rows)

    assert report["full_matrix_status"] == "fail"


def test_transcript_rows_feed_full_report(tmp_path: Path) -> None:
    transcript = tmp_path / "manual-transcript.json"
    transcript.write_text(json.dumps(_transcript()), encoding="utf-8")

    report = matrix.build_report(scope="full", transcripts=[transcript])

    by_scenario = {
        row["scenario"]: row["classification"]
        for row in report["rows"]
        if row["observed"] and row["lane"] == "windows_true_host"
    }
    assert by_scenario["start_ping"] == "pass"
    assert by_scenario["ask"] == "pass"
    assert by_scenario["kill"] == "pass"
    assert report["full_matrix_status"] == "incomplete"


def test_transcript_runtime_failure_does_not_override_unrelated_rows(tmp_path: Path) -> None:
    payload = _transcript()
    commands = list(payload["commands"])
    commands[0] = _command("ccb-start", returncode=1)
    payload["commands"] = commands
    payload["scenario_results"] = {
        "start_ping": {"observed": True, "classification": "system_failure"},
        "ask": {"observed": True, "classification": "pass"},
        "kill": {"observed": True, "classification": "pass"},
        "diagnostics": {"observed": True, "classification": "pass"},
    }
    transcript = tmp_path / "manual-transcript.json"
    transcript.write_text(json.dumps(payload), encoding="utf-8")

    report = matrix.build_report(scope="full", transcripts=[transcript])

    by_scenario = {
        row["scenario"]: row["classification"]
        for row in report["rows"]
        if row["observed"] and row["lane"] == "windows_true_host"
    }
    assert by_scenario["start_ping"] == "system_failure"
    assert by_scenario["ask"] == "pass"
    assert by_scenario["kill"] == "pass"
    assert by_scenario["diagnostics"] == "pass"
    assert report["full_matrix_status"] == "fail"


def test_windows_true_host_lane_full_transcript_can_pass_selected_and_full(tmp_path: Path) -> None:
    transcript = tmp_path / "manual-transcript.json"
    transcript.write_text(json.dumps(_full_transcript()), encoding="utf-8")

    report = matrix.build_report(lane="windows_true_host", scope="full", transcripts=[transcript])

    assert report["selected_cases_status"] == "pass"
    assert report["full_matrix_status"] == "pass"


def test_manual_transcript_lane_records_sidecar_import(tmp_path: Path) -> None:
    transcript = tmp_path / "manual-transcript.json"
    transcript.write_text(json.dumps(_transcript()), encoding="utf-8")

    report = matrix.build_report(lane="manual_transcript", scope="subset", transcripts=[transcript])

    assert report["selected_cases_status"] == "pass"
    assert report["rows"][0]["case_id"] == "manual-transcript-import"
    assert report["rows"][0]["classification"] == "pass"


def test_dirty_transcript_redaction_fixture_fails() -> None:
    payload = _transcript()
    payload["secret"] = "token=sk-secret-value"

    result = matrix.evaluate_transcript(payload)

    assert result.ok is False
    assert any("redaction" in error for error in result.errors)


def test_write_report_creates_json_jsonl_and_markdown(tmp_path: Path) -> None:
    report = matrix.build_report(lane="fake", scope="subset", include_fake_evidence=True)

    paths = matrix.write_report(report, tmp_path)

    assert Path(paths["report_json"]).exists()
    assert Path(paths["rows_jsonl"]).exists()
    assert Path(paths["summary_markdown"]).exists()
    assert "selected_cases_status" in Path(paths["summary_markdown"]).read_text(encoding="utf-8")
