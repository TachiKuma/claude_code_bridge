from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "probe_rmux_capability.py"
SPEC = importlib.util.spec_from_file_location("probe_rmux_capability", SCRIPT_PATH)
probe = importlib.util.module_from_spec(SPEC)
assert SPEC is not None and SPEC.loader is not None
sys.modules[SPEC.name] = probe
SPEC.loader.exec_module(probe)


class FakeRunner:
    def __init__(
        self,
        failures: set[str] | None = None,
        *,
        version_returncode: int = 0,
        empty_panes: bool = False,
        cleanup_returncode: int = 0,
    ) -> None:
        self.failures = failures or set()
        self.version_returncode = version_returncode
        self.empty_panes = empty_panes
        self.cleanup_returncode = cleanup_returncode
        self.calls: list[list[str]] = []

    def run(self, args: list[str], *, timeout: float = 5.0) -> probe.CommandResult:
        self.calls.append(args)
        name = probe.command_name(args)
        if args[-1] == "-V":
            return probe.CommandResult(args, self.version_returncode, "rmux 0.8.0", "version failed", timeout)
        if name == "has-session" and "-L" not in args:
            return probe.CommandResult(args, 1, "", "can't find session", timeout)
        if name == "kill-session" and "cleanup-fails" in self.failures:
            return probe.CommandResult(args, self.cleanup_returncode or 1, "", "cleanup failed", timeout)
        if name in self.failures:
            return probe.CommandResult(args, 1, "", f"{name} unsupported", timeout)
        if name == "attach-session" and "interactive-attach-timeout" in self.failures:
            return probe.CommandResult(args, 124, "\x1b[?1049hprobe-main\x1b[?2004h", "timeout", timeout)
        if name == "list-windows":
            return probe.CommandResult(args, 0, "0: probe-main* (1 panes)\n1: probe-extra (1 panes)\n", "", timeout)
        if name == "list-panes":
            return probe.CommandResult(args, 0, "" if self.empty_panes else "%0\n", "token=sk-secret-value", timeout)
        if name == "capture-pane":
            if "-2" in args:
                return probe.CommandResult(args, 0, "CCB_RMUX_WIDE_宽字符\nCCB_RMUX_LASTN\n", "token=sk-secret-value", timeout)
            if "-12" in args:
                return probe.CommandResult(
                    args,
                    0,
                    (
                        "CCB_RMUX_TRAILING   \n"
                        "CCB_RMUX_WRAP_abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
                        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789\n"
                        "CCB_RMUX_WIDE_宽字符\n"
                        "CCB_RMUX_LASTN\n"
                    ),
                    "token=sk-secret-value",
                    timeout,
                )
            return probe.CommandResult(args, 0, "old\n• Working (1s • esc to interrupt)\n", "token=sk-secret-value", timeout)
        if name == "display-message":
            return probe.CommandResult(args, 0, "ccb-rmux-probe\n", "token=sk-secret-value", timeout)
        return probe.CommandResult(args, 0, f"{name} ok", "token=sk-secret-value", timeout)


class TimeoutProcess:
    def __init__(self) -> None:
        self.pid = 4242
        self.returncode = None

    def communicate(self, timeout: float):
        raise subprocess.TimeoutExpired(["rmux", "start-server"], timeout, output=b"out", stderr=b"err")

    def poll(self):
        return self.returncode


def test_required_unsupported_command_enters_blocking_gaps(tmp_path: Path) -> None:
    report = probe.run_probe(tmp_path, runner=FakeRunner({"capture-pane"}), rmux_bin="rmux", platform_name="windows")

    gap_names = {gap["name"] for gap in report["blocking_gaps"]}

    assert "capture-pane" in gap_names
    assert report["commands"]["capture-pane"]["status"] == "unsupported"
    assert report["commands"]["capture-pane"]["degrade_impact"] == "parser-fidelity"
    assert report["commands"]["capture-pane"]["consequence"]


def test_core_command_timeout_writes_report_and_stops_early(tmp_path: Path) -> None:
    report = probe.run_probe(tmp_path, runner=FakeRunner({"start-server"}), rmux_bin="rmux", platform_name="windows")

    assert report["probe_status"] == "completed"
    assert report["early_stop"]["command"] == "start-server"
    assert report["commands"]["start-server"]["status"] == "unsupported"
    assert report["semantics"] == {}
    assert {gap["name"] for gap in report["blocking_gaps"]} == {"start-server"}
    assert (Path(report["run_dir"]) / "capability-report.json").exists()


def test_subprocess_runner_timeout_kills_windows_process_tree(monkeypatch) -> None:
    process = TimeoutProcess()
    taskkill_calls: list[list[str]] = []

    monkeypatch.setattr(probe.subprocess, "Popen", lambda *args, **kwargs: process)
    monkeypatch.setattr(probe.platform, "system", lambda: "Windows")

    def fake_run(args, **kwargs):
        taskkill_calls.append(args)

        class _Result:
            returncode = 0

        return _Result()

    monkeypatch.setattr(probe.subprocess, "run", fake_run)

    result = probe.SubprocessRunner().run(["rmux", "start-server"], timeout=0.01)

    assert result.returncode == 124
    assert result.stdout == "out"
    assert result.stderr == "err"
    assert taskkill_calls == [["taskkill", "/PID", "4242", "/T", "/F"]]


def test_core_command_early_stop_records_cleanup_evidence(monkeypatch, tmp_path: Path) -> None:
    cleanup_calls: list[tuple[str, Path]] = []

    class EarlyStopRunner(probe.SubprocessRunner):
        def run(self, args: list[str], *, timeout: float = 5.0) -> probe.CommandResult:
            name = probe.command_name(args)
            if args[-1] == "-V":
                return probe.CommandResult(args, 0, "rmux 0.9.0", "", timeout)
            if name == "has-session" and "-L" not in args:
                return probe.CommandResult(args, 1, "", "can't find session", timeout)
            if name == "start-server":
                return probe.CommandResult(args, 124, "", "timeout", timeout)
            return probe.CommandResult(args, 0, "", "", timeout)

    def fake_cleanup(namespace: str, run_dir: Path) -> Path:
        cleanup_calls.append((namespace, run_dir))
        path = run_dir / "artifacts" / "cleanup" / "orphan-daemons.json"
        probe._write_json(path, {"namespace": namespace, "returncode": 0})
        return path

    monkeypatch.setattr(probe, "_cleanup_windows_probe_daemons", fake_cleanup)

    report = probe.run_probe(tmp_path, runner=EarlyStopRunner(), rmux_bin="rmux", platform_name="windows")

    cleanup_evidence = report["early_stop"]["cleanup_evidence"]
    assert cleanup_calls
    assert cleanup_evidence == "artifacts/cleanup/orphan-daemons.json"
    assert any(entry["probe"] == "orphan-daemons" for entry in report["artifact_index"])
    assert (Path(report["run_dir"]) / cleanup_evidence).exists()


def test_partial_without_accepted_workaround_enters_blocking_gaps(tmp_path: Path) -> None:
    report = probe.run_probe(tmp_path, runner=FakeRunner(), rmux_bin="rmux", platform_name="windows")

    semantic = report["semantics"]["capture_format_fidelity_for_provider_completion"]
    gap_names = {gap["name"] for gap in report["blocking_gaps"]}

    assert semantic["status"] == "partial"
    assert semantic["workaround"]["accepted"] is False
    assert "capture_format_fidelity_for_provider_completion" in gap_names


def test_artifact_index_resolves_all_evidence_paths(tmp_path: Path) -> None:
    report = probe.run_probe(tmp_path, runner=FakeRunner(), rmux_bin="rmux", platform_name="windows")
    indexed = {entry["path"] for entry in report["artifact_index"]}

    evidence_paths = [
        result["evidence"]
        for section in ("commands", "semantics")
        for result in report[section].values()
    ]

    assert evidence_paths
    assert set(evidence_paths).issubset(indexed)
    for rel_path in evidence_paths:
        assert (Path(report["run_dir"]) / rel_path).exists()


def test_artifacts_are_redacted(tmp_path: Path) -> None:
    report = probe.run_probe(tmp_path, runner=FakeRunner(), rmux_bin="rmux", platform_name="windows")
    artifact_path = Path(report["run_dir"]) / report["commands"]["start-server"]["evidence"]

    text = artifact_path.read_text(encoding="utf-8")

    assert "sk-secret-value" not in text
    assert "[REDACTED]" in text


def test_json_and_quoted_secrets_are_redacted() -> None:
    text = probe.redact_text('{"password": "hunter2", "api_key": "plain-value", "token": "abc"} Bearer abc.def')

    assert "hunter2" not in text
    assert "plain-value" not in text
    assert "Bearer abc.def" not in text
    assert text.count("[REDACTED]") >= 4


def test_capture_fidelity_records_consumer_and_direct_parser_paths(tmp_path: Path) -> None:
    report = probe.run_probe(tmp_path, runner=FakeRunner(), rmux_bin="rmux", platform_name="windows")
    evidence_path = Path(report["run_dir"]) / report["semantics"][
        "capture_format_fidelity_for_provider_completion"
    ]["evidence"]
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))

    assert {"consumer_strip", "direct_stdout"} <= set(evidence["parser_paths"])
    assert {"codex", "claude"} <= set(evidence["providers"])
    assert evidence["rmux_capture_observation"]["available"] is True
    assert "raw_bytes_sha256" in evidence["rmux_capture_observation"]
    assert any(case["dimension"] in {"osc", "wrapping", "wide_char"} and not case["absorbed"] for case in evidence["cases"])


def test_preflight_hard_fail_writes_skipped_report(tmp_path: Path) -> None:
    report = probe.run_probe(tmp_path, runner=FakeRunner(), rmux_bin="rmux", platform_name="linux")

    assert report["probe_status"] == "skipped"
    assert report["preflight"]["failure_reason"]
    assert report["commands"] == {}
    assert report["semantics"] == {}


def test_report_backend_impl_follows_rmux_bin_name(tmp_path: Path) -> None:
    report = probe.run_probe(tmp_path, runner=FakeRunner(), rmux_bin="psmux", platform_name="windows")

    assert report["backend_impl"] == "psmux"


def test_preflight_version_failure_writes_failed_report(tmp_path: Path) -> None:
    report = probe.run_probe(
        tmp_path,
        runner=FakeRunner(version_returncode=1),
        rmux_bin="rmux",
        platform_name="windows",
    )

    assert report["probe_status"] == "failed"
    assert report["preflight"]["failure_reason"] == "rmux version check failed"
    assert report["commands"] == {}


def test_semantic_assertion_failure_is_not_supported_when_dependencies_succeed(tmp_path: Path) -> None:
    report = probe.run_probe(tmp_path, runner=FakeRunner(empty_panes=True), rmux_bin="rmux", platform_name="windows")

    semantic = report["semantics"]["pane_id_stability"]

    assert semantic["status"] == "partial"
    assert semantic["workaround"]["accepted"] is False
    assert "pane_id_stability" in {gap["name"] for gap in report["blocking_gaps"]}


def test_cleanup_failure_updates_cleanup_semantic(tmp_path: Path) -> None:
    report = probe.run_probe(
        tmp_path,
        runner=FakeRunner({"cleanup-fails"}, cleanup_returncode=1),
        rmux_bin="rmux",
        platform_name="windows",
    )

    assert report["commands"]["kill-session"]["status"] == "unsupported"
    assert report["semantics"]["kill_session_cleanup"]["status"] == "unsupported"
    assert "kill_session_cleanup" in {gap["name"] for gap in report["blocking_gaps"]}


def test_semantic_requires_real_assertion_not_only_command_success(tmp_path: Path) -> None:
    report = probe.run_probe(tmp_path, runner=FakeRunner(), rmux_bin="rmux", platform_name="windows")

    semantic = report["semantics"]["ctrl_c_ctrl_d"]
    evidence_path = Path(report["run_dir"]) / semantic["evidence"]
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))

    assert semantic["status"] == "partial"
    assert any(check["kind"] == "prerequisite" and check["passed"] for check in evidence["assertions"])
    assert any(check["name"] == "Ctrl-C/Ctrl-D control semantics were exercised" and not check["passed"] for check in evidence["assertions"])


def test_attach_timeout_with_tui_is_scenario_invalid() -> None:
    result = probe.CommandResult(["rmux", "attach-session"], 124, "\x1b[?1049hprobe-main\x1b[?2004h", "timeout", 8.0)

    status, notes = probe._command_status_and_notes("attach-session", result)

    assert status == "partial"
    assert "scenario-invalid" in notes


def test_capture_trailing_whitespace_requires_output_line_not_echo_command(tmp_path: Path) -> None:
    raw_results = {
        "capture-pane": probe.CommandResult(["rmux", "capture-pane"], 0, "ok", "", 5.0),
        "verify.capture-fidelity": probe.CommandResult(
            ["rmux", "capture-pane"],
            0,
            "E:\\repo>echo CCB_RMUX_TRAILING   & echo next\nCCB_RMUX_TRAILING\nnext\n",
            "",
            5.0,
        ),
        "verify.capture-last-n": probe.CommandResult(["rmux", "capture-pane"], 0, "CCB_RMUX_LASTN\n", "", 5.0),
    }

    evidence, status, workaround, _notes = probe._capture_fidelity_evidence(tmp_path / "capture.json", raw_results)

    assert evidence["real_dimension_checks"]["trailing_whitespace"] is False
    assert status == "partial"
    assert "trailing_whitespace" in workaround["missing_real_dimensions"]
