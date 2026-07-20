from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "probe_rmux_capability.py"
SPEC = importlib.util.spec_from_file_location("probe_rmux_capability", SCRIPT_PATH)
probe = importlib.util.module_from_spec(SPEC)
assert SPEC is not None and SPEC.loader is not None
sys.modules[SPEC.name] = probe
SPEC.loader.exec_module(probe)


class FakeRunner:
    def __init__(self, failures: set[str] | None = None) -> None:
        self.failures = failures or set()
        self.calls: list[list[str]] = []

    def run(self, args: list[str], *, timeout: float = 5.0) -> probe.CommandResult:
        self.calls.append(args)
        name = probe.command_name(args)
        if name in self.failures:
            return probe.CommandResult(args, 1, "", f"{name} unsupported", timeout)
        if args[-1] == "-V":
            return probe.CommandResult(args, 0, "rmux 0.8.0", "", timeout)
        return probe.CommandResult(args, 0, f"{name} ok", "token=sk-secret-value", timeout)


def test_required_unsupported_command_enters_blocking_gaps(tmp_path: Path) -> None:
    report = probe.run_probe(tmp_path, runner=FakeRunner({"capture-pane"}), rmux_bin="rmux")

    gap_names = {gap["name"] for gap in report["blocking_gaps"]}

    assert "capture-pane" in gap_names
    assert report["commands"]["capture-pane"]["status"] == "unsupported"
    assert report["commands"]["capture-pane"]["degrade_impact"] == "parser-fidelity"
    assert report["commands"]["capture-pane"]["consequence"]


def test_partial_without_accepted_workaround_enters_blocking_gaps(tmp_path: Path) -> None:
    report = probe.run_probe(tmp_path, runner=FakeRunner(), rmux_bin="rmux")

    semantic = report["semantics"]["capture_format_fidelity_for_provider_completion"]
    gap_names = {gap["name"] for gap in report["blocking_gaps"]}

    assert semantic["status"] == "partial"
    assert semantic["workaround"]["accepted"] is False
    assert "capture_format_fidelity_for_provider_completion" in gap_names


def test_artifact_index_resolves_all_evidence_paths(tmp_path: Path) -> None:
    report = probe.run_probe(tmp_path, runner=FakeRunner(), rmux_bin="rmux")
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
    report = probe.run_probe(tmp_path, runner=FakeRunner(), rmux_bin="rmux")
    artifact_path = Path(report["run_dir"]) / report["commands"]["start-server"]["evidence"]

    text = artifact_path.read_text(encoding="utf-8")

    assert "sk-secret-value" not in text
    assert "[REDACTED]" in text


def test_capture_fidelity_records_consumer_and_direct_parser_paths(tmp_path: Path) -> None:
    report = probe.run_probe(tmp_path, runner=FakeRunner(), rmux_bin="rmux")
    evidence_path = Path(report["run_dir"]) / report["semantics"][
        "capture_format_fidelity_for_provider_completion"
    ]["evidence"]
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))

    assert {"consumer_strip", "direct_stdout"} <= set(evidence["parser_paths"])
    assert {"codex", "claude"} <= set(evidence["providers"])
    assert any(case["dimension"] in {"osc", "wrapping", "wide_char"} and not case["absorbed"] for case in evidence["cases"])
