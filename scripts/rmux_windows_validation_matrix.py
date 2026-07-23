#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Literal, TypedDict


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "artifacts" / "rmux-windows-validation"
REPORT_JSON = "rmux_windows_validation_report.json"
ROWS_JSONL = "rmux_windows_validation_rows.jsonl"
SUMMARY_MD = "rmux_windows_validation_summary.md"
TRANSCRIPT_SCHEMA_VERSION = 1

LANES = {"fake", "provider_blackbox", "windows_true_host", "manual_transcript"}
SCOPES = {"subset", "full"}
PROVIDERS = {"fake", "codex", "claude", "gemini", "opencode", "mixed", "none"}
HOST_KINDS = {"native_windows", "wsl", "linux", "macos", "unknown", "unsupported_host"}
CONTROL_PLANES = {"ccbd", "probe", "none"}
BACKEND_SELECTION_SOURCES = {"cli", "project_config", "user_config", "env", "manual_transcript", "unknown"}
UPSTREAM_GATE_STATUSES = {"ready", "pending", "blocked"}
ALLOWED_DIRECT_RMUX_DIAGNOSTIC_COMMANDS = {"preflight-rmux-version", "cleanup-rmux-list-sessions"}
SCENARIOS = {
    "start_ping",
    "ask",
    "kill",
    "restart_replay",
    "multi_agent",
    "multi_project",
    "supervision_recovery",
    "diagnostics",
}
ROW_CLASSIFICATIONS = {
    "pass",
    "missing_evidence",
    "provider_failure",
    "system_failure",
    "test_design_failure",
    "valid_non_success",
}
SUMMARY_STATUSES = {"pass", "fail", "incomplete"}
REQUIRED_TRUE_HOST_FIELDS = {
    "host_kind": "native_windows",
    "control_plane": "ccbd",
    "backend_impl": "rmux",
    "probe_bypass": False,
}
CORE_SCENARIOS = {
    "start_ping",
    "ask",
    "kill",
    "restart_replay",
    "multi_agent",
    "multi_project",
    "supervision_recovery",
    "diagnostics",
}
VALID_NON_SUCCESS_SCENARIOS = {"kill", "restart_replay", "supervision_recovery"}
TOKEN_RE = re.compile(
    r"((?<![A-Za-z0-9_])sk-[A-Za-z0-9_-]{6,}|(?<![A-Za-z0-9_])sess-[A-Za-z0-9_-]{6,}|Bearer\s+[A-Za-z0-9._-]+)"
)
SECRET_RE = re.compile(
    r"(?i)([\"']?\b(api[_-]?key|(?:[A-Za-z0-9]+[_-])*token|secret|password)[\"']?\s*[:=]\s*)([\"']?)([^\"'\s,}]+)([\"']?)"
)

FORBIDDEN_EXACT_PATHS = {
    "README.md",
    "install.cmd",
    "install.ps1",
    "install.sh",
    "bin/ccb-npm-install.js",
    "package-lock.json",
}
FORBIDDEN_PREFIXES = (
    "README/",
    "docs/manuals/",
    "lib/terminal_runtime/rmux",
    "lib/provider_backends/",
)
ALLOWED_EXACT_PATHS = {
    "scripts/rmux_windows_validation_matrix.py",
    "scripts/rmux-windows-validation-runbook.ps1",
    "test/test_rmux_windows_validation_matrix.py",
    "test/test_rmux_windows_validation_scope_guard.py",
    ".github/workflows/ccbd-rmux-windows-validation.yml",
    "docs/plantree/plans/windows-rmux-native-backend/topics/rmux-windows-validation-runbook.md",
    ".codestable/features/2026-07-20-rmux-windows-validation-matrix/rmux-windows-validation-matrix-checklist.yaml",
    ".codestable/features/2026-07-20-rmux-windows-validation-matrix/rmux-windows-validation-matrix-review.md",
    ".codestable/features/2026-07-20-rmux-windows-validation-matrix/rmux-windows-validation-matrix-qa.md",
    ".codestable/features/2026-07-20-rmux-windows-validation-matrix/rmux-windows-validation-matrix-acceptance.md",
    ".codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml",
}
ALLOWED_PREFIXES = (
    "artifacts/rmux-windows-validation/",
    ".codestable/goals/2026-07-23-rmux-windows-validation-matrix/",
)
PACKAGE_JSON_ALLOWED_KEYS = {"os"}


class ValidationCase(TypedDict):
    case_id: str
    lane: Literal["fake", "provider_blackbox", "windows_true_host", "manual_transcript"]
    selection_scope: Literal["subset", "full"]
    provider: Literal["fake", "codex", "claude", "gemini", "opencode", "mixed", "none"]
    backend_impl: Literal["rmux"]
    host_kind: Literal["native_windows", "wsl", "linux", "macos", "unknown"]
    control_plane: Literal["ccbd", "probe", "none"]
    probe_bypass: bool
    backend_selection_source: Literal["cli", "project_config", "user_config", "env", "manual_transcript", "unknown"]
    upstream_gate: Literal["ready", "pending", "blocked"]
    scenario: Literal[
        "start_ping",
        "ask",
        "kill",
        "restart_replay",
        "multi_agent",
        "multi_project",
        "supervision_recovery",
        "diagnostics",
    ]
    command: list[str]
    required_artifacts: list[str]
    pass_checks: list[str]
    failure_classes: list[str]


@dataclass(frozen=True)
class MatrixEvaluation:
    ok: bool
    verdict: str
    failure_class: str
    errors: list[str]
    warnings: list[str]
    evidence: dict[str, Any]

    def to_json(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "verdict": self.verdict,
            "failure_class": self.failure_class,
            "errors": self.errors,
            "warnings": self.warnings,
            "evidence": self.evidence,
        }


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def matrix_manifest() -> list[ValidationCase]:
    return [
        {
            "case_id": "fake-start-ping",
            "lane": "fake",
            "selection_scope": "subset",
            "provider": "fake",
            "backend_impl": "rmux",
            "host_kind": "unknown",
            "control_plane": "ccbd",
            "probe_bypass": False,
            "backend_selection_source": "env",
            "upstream_gate": "ready",
            "scenario": "start_ping",
            "command": ["python", "scripts/rmux_windows_validation_matrix.py", "--lane", "fake", "--scope", "subset", "--json"],
            "required_artifacts": ["fake_report"],
            "pass_checks": ["case_schema_valid", "not_true_host", "selected_subset_reported"],
            "failure_classes": ["missing_evidence", "test_design_failure", "system_failure"],
        },
        {
            "case_id": "fake-multi-agent",
            "lane": "fake",
            "selection_scope": "subset",
            "provider": "fake",
            "backend_impl": "rmux",
            "host_kind": "unknown",
            "control_plane": "ccbd",
            "probe_bypass": False,
            "backend_selection_source": "env",
            "upstream_gate": "ready",
            "scenario": "multi_agent",
            "command": ["python", "scripts/single_lane_multi_workgroup_smoke.py", "--count", "2", "--shape", "parallel"],
            "required_artifacts": ["fake_report"],
            "pass_checks": ["fake_lane_is_not_true_host", "multi_agent_projection_present"],
            "failure_classes": ["missing_evidence", "test_design_failure", "system_failure"],
        },
        {
            "case_id": "fake-multi-project",
            "lane": "fake",
            "selection_scope": "subset",
            "provider": "fake",
            "backend_impl": "rmux",
            "host_kind": "unknown",
            "control_plane": "ccbd",
            "probe_bypass": False,
            "backend_selection_source": "env",
            "upstream_gate": "ready",
            "scenario": "multi_project",
            "command": ["python", "scripts/rmux_windows_validation_matrix.py", "--lane", "fake", "--scope", "subset", "--json"],
            "required_artifacts": ["fake_report"],
            "pass_checks": ["namespace_isolation_projection_present"],
            "failure_classes": ["missing_evidence", "test_design_failure", "system_failure"],
        },
        {
            "case_id": "provider-blackbox-ask",
            "lane": "provider_blackbox",
            "selection_scope": "subset",
            "provider": "mixed",
            "backend_impl": "rmux",
            "host_kind": "unknown",
            "control_plane": "ccbd",
            "probe_bypass": False,
            "backend_selection_source": "env",
            "upstream_gate": "ready",
            "scenario": "ask",
            "command": ["python", "-m", "pytest", "-q", "-m", "provider_blackbox", "test/test_v2_phase2_entrypoint.py"],
            "required_artifacts": ["provider_blackbox_report"],
            "pass_checks": ["provider_failure_separated_from_system_failure"],
            "failure_classes": ["provider_failure", "system_failure", "missing_evidence", "test_design_failure"],
        },
        {
            "case_id": "windows-true-host-start-ping",
            "lane": "windows_true_host",
            "selection_scope": "full",
            "provider": "fake",
            "backend_impl": "rmux",
            "host_kind": "native_windows",
            "control_plane": "ccbd",
            "probe_bypass": False,
            "backend_selection_source": "env",
            "upstream_gate": "ready",
            "scenario": "start_ping",
            "command": ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ".\\scripts\\rmux-windows-validation-runbook.ps1"],
            "required_artifacts": ["transcript", "ping", "doctor"],
            "pass_checks": ["native_windows", "ccbd_control_plane", "rmux_backend", "not_probe"],
            "failure_classes": ["missing_evidence", "provider_failure", "system_failure", "test_design_failure"],
        },
        {
            "case_id": "windows-true-host-ask",
            "lane": "windows_true_host",
            "selection_scope": "full",
            "provider": "fake",
            "backend_impl": "rmux",
            "host_kind": "native_windows",
            "control_plane": "ccbd",
            "probe_bypass": False,
            "backend_selection_source": "env",
            "upstream_gate": "ready",
            "scenario": "ask",
            "command": ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ".\\scripts\\rmux-windows-validation-runbook.ps1"],
            "required_artifacts": ["transcript", "ask", "runtime_session"],
            "pass_checks": ["ask_terminal_evidence", "provider_failure_separated"],
            "failure_classes": ["missing_evidence", "provider_failure", "system_failure", "test_design_failure"],
        },
        {
            "case_id": "windows-true-host-kill",
            "lane": "windows_true_host",
            "selection_scope": "full",
            "provider": "fake",
            "backend_impl": "rmux",
            "host_kind": "native_windows",
            "control_plane": "ccbd",
            "probe_bypass": False,
            "backend_selection_source": "env",
            "upstream_gate": "ready",
            "scenario": "kill",
            "command": ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ".\\scripts\\rmux-windows-validation-runbook.ps1"],
            "required_artifacts": ["transcript", "cleanup", "residue"],
            "pass_checks": ["endpoint_removed", "token_removed", "rmux_namespace_removed", "owned_process_clean_or_bounded"],
            "failure_classes": ["missing_evidence", "system_failure", "test_design_failure", "valid_non_success"],
        },
        {
            "case_id": "windows-true-host-restart",
            "lane": "windows_true_host",
            "selection_scope": "full",
            "provider": "fake",
            "backend_impl": "rmux",
            "host_kind": "native_windows",
            "control_plane": "ccbd",
            "probe_bypass": False,
            "backend_selection_source": "env",
            "upstream_gate": "ready",
            "scenario": "restart_replay",
            "command": ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ".\\scripts\\rmux-windows-validation-runbook.ps1", "-IncludeRestartReplay"],
            "required_artifacts": ["transcript", "restart_replay"],
            "pass_checks": ["restart_replay_observed_or_degraded_with_reason"],
            "failure_classes": ["missing_evidence", "system_failure", "test_design_failure", "valid_non_success"],
        },
        {
            "case_id": "windows-true-host-multi-agent",
            "lane": "windows_true_host",
            "selection_scope": "full",
            "provider": "mixed",
            "backend_impl": "rmux",
            "host_kind": "native_windows",
            "control_plane": "ccbd",
            "probe_bypass": False,
            "backend_selection_source": "env",
            "upstream_gate": "ready",
            "scenario": "multi_agent",
            "command": ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ".\\scripts\\rmux-windows-validation-runbook.ps1", "-IncludeMultiAgent"],
            "required_artifacts": ["transcript", "multi_agent"],
            "pass_checks": ["same_project_agents_do_not_cross_provider_env"],
            "failure_classes": ["missing_evidence", "provider_failure", "system_failure", "test_design_failure"],
        },
        {
            "case_id": "windows-true-host-multi-project",
            "lane": "windows_true_host",
            "selection_scope": "full",
            "provider": "fake",
            "backend_impl": "rmux",
            "host_kind": "native_windows",
            "control_plane": "ccbd",
            "probe_bypass": False,
            "backend_selection_source": "env",
            "upstream_gate": "ready",
            "scenario": "multi_project",
            "command": ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ".\\scripts\\rmux-windows-validation-runbook.ps1", "-IncludeMultiProject"],
            "required_artifacts": ["transcript", "multi_project"],
            "pass_checks": ["two_projects_do_not_share_namespace_or_endpoint"],
            "failure_classes": ["missing_evidence", "system_failure", "test_design_failure"],
        },
        {
            "case_id": "windows-true-host-supervision-recovery",
            "lane": "windows_true_host",
            "selection_scope": "full",
            "provider": "fake",
            "backend_impl": "rmux",
            "host_kind": "native_windows",
            "control_plane": "ccbd",
            "probe_bypass": False,
            "backend_selection_source": "env",
            "upstream_gate": "ready",
            "scenario": "supervision_recovery",
            "command": ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ".\\scripts\\rmux-windows-validation-runbook.ps1", "-IncludeRecovery"],
            "required_artifacts": ["transcript", "supervision_recovery"],
            "pass_checks": ["pane_process_namespace_daemon_evidence_present"],
            "failure_classes": ["missing_evidence", "system_failure", "test_design_failure", "valid_non_success"],
        },
        {
            "case_id": "windows-true-host-diagnostics",
            "lane": "windows_true_host",
            "selection_scope": "full",
            "provider": "fake",
            "backend_impl": "rmux",
            "host_kind": "native_windows",
            "control_plane": "ccbd",
            "probe_bypass": False,
            "backend_selection_source": "env",
            "upstream_gate": "ready",
            "scenario": "diagnostics",
            "command": ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ".\\scripts\\rmux-windows-validation-runbook.ps1"],
            "required_artifacts": ["transcript", "doctor", "diagnostics_bundle"],
            "pass_checks": ["doctor_projects_backend_and_transport_evidence"],
            "failure_classes": ["missing_evidence", "system_failure", "test_design_failure"],
        },
        {
            "case_id": "manual-transcript-import",
            "lane": "manual_transcript",
            "selection_scope": "subset",
            "provider": "mixed",
            "backend_impl": "rmux",
            "host_kind": "native_windows",
            "control_plane": "ccbd",
            "probe_bypass": False,
            "backend_selection_source": "manual_transcript",
            "upstream_gate": "ready",
            "scenario": "diagnostics",
            "command": ["python", "scripts/rmux_windows_validation_matrix.py", "--transcript", "artifacts/rmux-windows-validation/manual-transcript.json", "--json"],
            "required_artifacts": ["manual_transcript_sidecar", "redaction_summary", "transcript_rows"],
            "pass_checks": ["manual_transcript_schema_valid", "manual_rows_backfill_true_host", "missing_fields_fail_closed"],
            "failure_classes": ["missing_evidence", "provider_failure", "system_failure", "test_design_failure", "valid_non_success"],
        },
    ]


def validate_manifest(cases: list[dict[str, Any]]) -> MatrixEvaluation:
    errors: list[str] = []
    warnings: list[str] = []
    seen: set[str] = set()
    scenarios: set[str] = set()
    for index, case in enumerate(cases):
        case_id = _text(case.get("case_id"))
        if not case_id:
            errors.append(f"cases[{index}].case_id is required")
            continue
        if case_id in seen:
            errors.append(f"duplicate case_id: {case_id}")
        seen.add(case_id)
        _validate_enum(case, "lane", LANES, errors)
        _validate_enum(case, "selection_scope", SCOPES, errors)
        _validate_enum(case, "provider", PROVIDERS, errors)
        _validate_literal(case, "backend_impl", "rmux", errors)
        _validate_enum(case, "host_kind", HOST_KINDS, errors)
        _validate_enum(case, "control_plane", CONTROL_PLANES, errors)
        _validate_enum(case, "backend_selection_source", BACKEND_SELECTION_SOURCES, errors)
        _validate_enum(case, "upstream_gate", UPSTREAM_GATE_STATUSES, errors)
        _validate_enum(case, "scenario", SCENARIOS, errors)
        _validate_str_list(case, "command", errors)
        _validate_str_list(case, "required_artifacts", errors)
        _validate_str_list(case, "pass_checks", errors)
        _validate_failure_classes(case, errors)
        scenarios.add(_text(case.get("scenario")))
        if case.get("lane") == "windows_true_host":
            _validate_true_host_case(case, errors)
        if case.get("selection_scope") == "full" and case.get("lane") not in {"windows_true_host", "manual_transcript"}:
            errors.append(f"{case_id}: full scope requires windows_true_host or manual_transcript lane")
    missing_scenarios = sorted(CORE_SCENARIOS - scenarios)
    if missing_scenarios:
        errors.append(f"manifest missing core scenarios: {', '.join(missing_scenarios)}")
    return _evaluation(not errors, "pass" if not errors else "test_design_failure", "test_design_failure" if errors else "none", errors, warnings, {"case_count": len(cases)})


def build_report(
    *,
    lane: str | None = None,
    scope: str = "subset",
    transcripts: list[Path] | None = None,
    evidence_rows: list[dict[str, Any]] | None = None,
    include_fake_evidence: bool = False,
) -> dict[str, Any]:
    cases = _select_cases(lane=lane, scope=scope)
    observed: dict[str, dict[str, Any]] = {}
    if include_fake_evidence:
        observed.update(_fake_rows(cases))
    for row in evidence_rows or []:
        case_id = _text(row.get("case_id"))
        if case_id:
            observed[case_id] = _normalize_external_row(row)
    for transcript in transcripts or []:
        for row in rows_from_transcript(transcript):
            observed[row["case_id"]] = row
        for row in manual_rows_from_transcript(transcript, cases):
            observed[row["case_id"]] = row
    rows = [observed.get(case["case_id"]) or _missing_row(case, "case evidence not observed") for case in cases]
    summary = _summary(rows, cases, requested_scope=scope)
    return {
        "schema": "ccb.rmux_windows_validation_report.v1",
        "generated_at": utc_now(),
        "selection": {
            "lane": lane or "all",
            "scope": scope,
            "case_ids": [case["case_id"] for case in cases],
        },
        "selection_scope": scope,
        "selected_cases_status": summary["selected_cases_status"],
        "full_matrix_status": summary["full_matrix_status"],
        "summary": summary,
        "manifest": cases,
        "rows": rows,
    }


def rows_from_transcript(path: Path) -> list[dict[str, Any]]:
    payload = load_json_object(path)
    transcript_result = evaluate_transcript(payload, transcript_path=path)
    scenario_results = payload.get("scenario_results") if isinstance(payload.get("scenario_results"), dict) else {}
    rows: list[dict[str, Any]] = []
    for case in matrix_manifest():
        if case["lane"] != "windows_true_host":
            continue
        scenario = case["scenario"]
        if scenario not in scenario_results and scenario != "start_ping":
            continue
        scenario_payload = scenario_results.get(scenario) if isinstance(scenario_results.get(scenario), dict) else {}
        if scenario == "start_ping":
            scenario_payload = scenario_payload or {"observed": transcript_result.ok, "classification": transcript_result.verdict}
        classification = _classification_from_transcript_result(transcript_result, scenario_payload)
        row = _row_from_case(case, classification=classification, evidence_source=str(path))
        row["observed"] = classification != "missing_evidence"
        row["transcript"] = {
            "path": str(path),
            "ok": transcript_result.ok,
            "verdict": transcript_result.verdict,
            "failure_class": transcript_result.failure_class,
            "errors": transcript_result.errors,
            "warnings": transcript_result.warnings,
        }
        row["details"] = scenario_payload
        rows.append(row)
    return rows


def manual_rows_from_transcript(path: Path, cases: list[ValidationCase]) -> list[dict[str, Any]]:
    manual_cases = [case for case in cases if case["lane"] == "manual_transcript"]
    if not manual_cases:
        return []
    payload = load_json_object(path)
    transcript_result = evaluate_transcript(payload, transcript_path=path)
    classification = transcript_result.verdict if transcript_result.verdict in ROW_CLASSIFICATIONS else "pass"
    if not transcript_result.ok and classification == "pass":
        classification = "test_design_failure"
    rows: list[dict[str, Any]] = []
    for case in manual_cases:
        row = _row_from_case(case, classification=classification, evidence_source=str(path))
        row["observed"] = classification not in {"missing_evidence", "test_design_failure"}
        row["transcript"] = {
            "path": str(path),
            "ok": transcript_result.ok,
            "verdict": transcript_result.verdict,
            "failure_class": transcript_result.failure_class,
            "errors": transcript_result.errors,
            "warnings": transcript_result.warnings,
        }
        rows.append(row)
    return rows


def evaluate_transcript(payload: dict[str, Any], *, transcript_path: Path | None = None) -> MatrixEvaluation:
    errors: list[str] = []
    warnings: list[str] = []
    evidence: dict[str, Any] = {"checked_at": utc_now()}
    required = {
        "schema_version",
        "host_kind",
        "control_plane",
        "backend_impl",
        "probe_bypass",
        "backend_selection_source",
        "ccbd_transport",
        "commands",
        "artifacts",
        "evidence",
        "redaction_summary",
        "cleanup",
        "scenario_results",
    }
    missing = sorted(required - set(payload))
    if missing:
        errors.append(f"missing transcript fields: {', '.join(missing)}")
        return _evaluation(False, "test_design_failure", "test_design_failure", errors, warnings, evidence)
    for field, expected in REQUIRED_TRUE_HOST_FIELDS.items():
        if payload.get(field) != expected:
            errors.append(f"{field} must be {expected!r}")
    if payload.get("backend_selection_source") not in BACKEND_SELECTION_SOURCES - {"unknown"}:
        errors.append("backend_selection_source must be traceable and not unknown")
    if _text(payload.get("ccbd_transport")) != "tcp_loopback":
        errors.append("ccbd_transport must be tcp_loopback")
    if not isinstance(payload.get("commands"), list) or not payload.get("commands"):
        errors.append("commands must be a non-empty list")
    if not isinstance(payload.get("artifacts"), dict):
        errors.append("artifacts must be an object")
    if not isinstance(payload.get("evidence"), dict):
        errors.append("evidence must be an object")
    if not isinstance(payload.get("scenario_results"), dict):
        errors.append("scenario_results must be an object")
    _validate_no_probe_bypass(payload.get("commands"), errors)
    _validate_redaction(payload, errors, warnings, transcript_path=transcript_path)
    _validate_cleanup(payload.get("cleanup"), errors, evidence)
    if errors:
        return _evaluation(False, "test_design_failure", "test_design_failure", errors, warnings, evidence)
    system_failure = _has_system_failure(payload)
    provider_failure = _has_provider_failure(payload)
    if provider_failure:
        return _evaluation(False, "provider_failure", "provider_failure", errors, warnings, evidence)
    if system_failure:
        return _evaluation(False, "system_failure", "system_failure", errors, warnings, evidence)
    return _evaluation(True, "pass", "none", errors, warnings, evidence)


def redact_text(text: str, *, home: str | None = None) -> str:
    value = str(text or "")
    home_value = str(home or os.environ.get("USERPROFILE") or os.environ.get("HOME") or "").strip()
    if home_value:
        for variant in {home_value, home_value.replace("\\", "/"), home_value.replace("\\", "\\\\")}:
            value = value.replace(variant, "[USER_HOME]")
    value = TOKEN_RE.sub("[REDACTED]", value)
    return SECRET_RE.sub(lambda match: f"{match.group(1)}{match.group(3)}[REDACTED]{match.group(5)}", value)


def contains_secret(text: str) -> bool:
    return redact_text(text) != str(text or "")


def write_report(report: dict[str, Any], output_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / REPORT_JSON
    rows_path = output_dir / ROWS_JSONL
    summary_path = output_dir / SUMMARY_MD
    report["report_paths"] = {
        "report_json": str(report_path),
        "rows_jsonl": str(rows_path),
        "summary_markdown": str(summary_path),
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    rows_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in report["rows"]),
        encoding="utf-8",
    )
    summary_path.write_text(markdown_summary(report), encoding="utf-8")
    return dict(report["report_paths"])


def markdown_summary(report: dict[str, Any]) -> str:
    rows = report.get("rows") if isinstance(report.get("rows"), list) else []
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    lines = [
        "# Rmux Windows Validation Matrix Summary",
        "",
        f"Generated: {report.get('generated_at')}",
        "",
        "## Status",
        "",
        f"- selection_scope: `{report.get('selection_scope')}`",
        f"- selected_cases_status: `{report.get('selected_cases_status')}`",
        f"- full_matrix_status: `{report.get('full_matrix_status')}`",
        f"- observed_case_count: `{summary.get('observed_case_count')}`",
        f"- missing_case_ids: `{', '.join(str(item) for item in summary.get('missing_case_ids') or [])}`",
        "",
        "## Rows",
        "",
        "| Case | Lane | Scenario | Classification | Evidence |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        if not isinstance(row, dict):
            continue
        lines.append(
            "| {case_id} | {lane} | {scenario} | {classification} | {evidence_source} |".format(
                case_id=_md(row.get("case_id")),
                lane=_md(row.get("lane")),
                scenario=_md(row.get("scenario")),
                classification=_md(row.get("classification")),
                evidence_source=_md(row.get("evidence_source")),
            )
        )
    lines.extend(
        [
            "",
            "## Delivery Record",
            "",
            "- `selected_cases_status=pass` only means the selected subset passed.",
            "- `full_matrix_status=pass` requires full true-host/manual core rows to be observed and passing.",
            "",
        ]
    )
    return "\n".join(lines)


def evaluate_scope_paths(paths: list[str], *, package_json_text: str | None = None) -> MatrixEvaluation:
    normalized = sorted({_normalize_path(path) for path in paths if str(path).strip()})
    forbidden = [path for path in normalized if _is_forbidden_scope_path(path)]
    errors = [f"scope guard rejected paths: {', '.join(forbidden)}"] if forbidden else []
    if package_json_text is not None:
        errors.extend(_package_json_scope_errors(package_json_text))
    evidence = {"checked_at": utc_now(), "changed_paths": normalized, "forbidden_paths": forbidden}
    return _evaluation(not errors, "pass" if not errors else "test_design_failure", "none" if not errors else "test_design_failure", errors, [], evidence)


def changed_paths(diff_base: str) -> list[str]:
    tracked = _git_lines(["git", "diff", "--name-only", "--diff-filter=ACDMRTUXB", diff_base, "--"])
    untracked = _git_lines(["git", "ls-files", "--others", "--exclude-standard"])
    return sorted(set(tracked + untracked))


def load_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid JSON object {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return payload


def _select_cases(*, lane: str | None, scope: str) -> list[ValidationCase]:
    if scope not in SCOPES:
        raise ValueError(f"unsupported scope: {scope}")
    if lane is not None and lane not in LANES:
        raise ValueError(f"unsupported lane: {lane}")
    cases = matrix_manifest()
    if lane:
        cases = [case for case in cases if case["lane"] == lane]
    if scope == "subset":
        cases = [case for case in cases if case["selection_scope"] == "subset"]
    return cases


def _fake_rows(cases: list[ValidationCase]) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for case in cases:
        if case["lane"] != "fake":
            continue
        row = _row_from_case(case, classification="pass", evidence_source="script-owned fake lane projection")
        row["observed"] = True
        row["details"] = {
            "not_true_host": True,
            "native_windows_evidence": False,
            "control_plane_projection": "ccbd",
            "backend_impl_projection": "rmux",
        }
        rows[case["case_id"]] = row
    return rows


def _normalize_external_row(row: dict[str, Any]) -> dict[str, Any]:
    case_id = _text(row.get("case_id"))
    cases = {case["case_id"]: case for case in matrix_manifest()}
    if case_id not in cases:
        raise ValueError(f"unknown row case_id: {case_id}")
    classification = _text(row.get("classification")) or "missing_evidence"
    if classification not in ROW_CLASSIFICATIONS:
        classification = "test_design_failure"
    normalized = _row_from_case(cases[case_id], classification=classification, evidence_source=_text(row.get("evidence_source")) or "external")
    normalized["observed"] = row.get("observed") is True or classification not in {"missing_evidence", "test_design_failure"}
    normalized["details"] = row.get("details") if isinstance(row.get("details"), dict) else {}
    return normalized


def _summary(rows: list[dict[str, Any]], cases: list[ValidationCase], *, requested_scope: str) -> dict[str, Any]:
    missing = [row["case_id"] for row in rows if row["classification"] == "missing_evidence"]
    failing = [row["case_id"] for row in rows if row["classification"] in {"provider_failure", "system_failure", "test_design_failure"}]
    provider_failures = [row["case_id"] for row in rows if row["classification"] == "provider_failure"]
    selected_status = "pass" if not missing and not failing else "incomplete" if missing and not failing else "fail"
    full_core_rows = [row for row in rows if row.get("selection_scope") == "full" and row.get("lane") == "windows_true_host"]
    all_cases = matrix_manifest()
    full_core_case_ids = {case["case_id"] for case in all_cases if case["selection_scope"] == "full" and case["lane"] == "windows_true_host"}
    observed_full_case_ids = {
        row["case_id"]
        for row in full_core_rows
        if _full_row_satisfies_core(row)
    }
    if requested_scope != "full":
        full_status = "incomplete"
    elif any(_full_row_fails_core(row) for row in full_core_rows):
        full_status = "fail"
    elif full_core_case_ids - observed_full_case_ids:
        full_status = "incomplete"
    else:
        full_status = "pass"
    return {
        "selected_cases_status": selected_status,
        "full_matrix_status": full_status,
        "selected_case_count": len(cases),
        "observed_case_count": sum(1 for row in rows if row.get("observed")),
        "missing_case_ids": missing,
        "failing_case_ids": failing,
        "provider_failure_case_ids": provider_failures,
        "classification_counts": {
            name: sum(1 for row in rows if row["classification"] == name)
            for name in sorted(ROW_CLASSIFICATIONS)
        },
    }


def _classification_from_transcript_result(result: MatrixEvaluation, scenario_payload: dict[str, Any]) -> str:
    if scenario_payload.get("observed") is False:
        return "missing_evidence"
    if not result.ok and result.failure_class == "test_design_failure":
        return "test_design_failure"
    declared = _text(scenario_payload.get("classification"))
    if declared in ROW_CLASSIFICATIONS:
        return declared
    if not result.ok and result.verdict in {"provider_failure", "system_failure"}:
        return result.verdict
    return "test_design_failure"


def _full_row_satisfies_core(row: dict[str, Any]) -> bool:
    classification = row.get("classification")
    if classification == "pass":
        return True
    return classification == "valid_non_success" and row.get("scenario") in VALID_NON_SUCCESS_SCENARIOS


def _full_row_fails_core(row: dict[str, Any]) -> bool:
    classification = row.get("classification")
    if classification in {"provider_failure", "system_failure", "test_design_failure"}:
        return True
    return classification == "valid_non_success" and row.get("scenario") not in VALID_NON_SUCCESS_SCENARIOS


def _missing_row(case: ValidationCase, reason: str) -> dict[str, Any]:
    row = _row_from_case(case, classification="missing_evidence", evidence_source="")
    row["observed"] = False
    row["details"] = {"reason": reason}
    return row


def _row_from_case(case: ValidationCase, *, classification: str, evidence_source: str) -> dict[str, Any]:
    return {
        "case_id": case["case_id"],
        "lane": case["lane"],
        "selection_scope": case["selection_scope"],
        "scenario": case["scenario"],
        "provider": case["provider"],
        "backend_impl": case["backend_impl"],
        "host_kind": case["host_kind"],
        "control_plane": case["control_plane"],
        "probe_bypass": case["probe_bypass"],
        "backend_selection_source": case["backend_selection_source"],
        "classification": classification,
        "required_artifacts": list(case["required_artifacts"]),
        "pass_checks": list(case["pass_checks"]),
        "evidence_source": evidence_source,
        "observed": classification not in {"missing_evidence", "test_design_failure"},
    }


def _validate_true_host_case(case: dict[str, Any], errors: list[str]) -> None:
    case_id = _text(case.get("case_id"))
    for field, expected in REQUIRED_TRUE_HOST_FIELDS.items():
        if case.get(field) != expected:
            errors.append(f"{case_id}: windows_true_host requires {field}={expected!r}")
    if case.get("backend_selection_source") == "unknown":
        errors.append(f"{case_id}: windows_true_host requires traceable backend_selection_source")
    if case.get("selection_scope") != "full":
        errors.append(f"{case_id}: windows_true_host must be full scope")


def _validate_no_probe_bypass(commands: Any, errors: list[str]) -> None:
    if not isinstance(commands, list):
        return
    for index, command in enumerate(commands):
        if not isinstance(command, dict):
            errors.append(f"commands[{index}] must be an object")
            continue
        argv = [str(item) for item in command.get("argv") or []]
        joined = " ".join(argv).replace("\\", "/").lower()
        name = _text(command.get("name")) or f"commands[{index}]"
        if "probe_rmux" in joined:
            errors.append(f"{name} uses probe_rmux bypass")
        if argv and Path(argv[0]).stem.lower() in {"rmux", "psmux"}:
            if not _is_allowed_direct_rmux_diagnostic(name, argv):
                errors.append(f"{name} bypasses ccb/ccbd with direct rmux command")
        if name.startswith("ccb-") and not _is_ccb_argv(argv):
            errors.append(f"{name} must execute through ccb")


def _validate_redaction(payload: dict[str, Any], errors: list[str], warnings: list[str], *, transcript_path: Path | None) -> None:
    redaction = payload.get("redaction_summary")
    if not isinstance(redaction, dict):
        errors.append("redaction_summary must be an object")
        return
    if redaction.get("redacted") is not True:
        errors.append("redaction_summary.redacted must be true")
    policy = _text(redaction.get("raw_retention_policy"))
    if policy not in {"none", "hash_only", "redacted_artifacts_only"}:
        warnings.append("redaction_summary.raw_retention_policy should be none, hash_only, or redacted_artifacts_only")
    if contains_secret(json.dumps(payload, ensure_ascii=True, sort_keys=True)):
        errors.append("transcript redaction failed")
    if transcript_path is None:
        return
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, dict):
        return
    base = transcript_path.resolve().parent
    for key, value in artifacts.items():
        rel = _text(value)
        if not rel:
            continue
        path = (base / rel).resolve()
        try:
            path.relative_to(base)
        except ValueError:
            errors.append(f"artifact path escapes transcript directory: {key}")
            continue
        if not path.exists():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if contains_secret(text):
            errors.append(f"artifact redaction failed: {key}")


def _validate_cleanup(value: Any, errors: list[str], evidence: dict[str, Any]) -> None:
    if not isinstance(value, dict):
        errors.append("cleanup must be an object")
        return
    cleanup_evidence = value.get("evidence") if isinstance(value.get("evidence"), dict) else value
    required = ("endpoint_removed", "token_removed", "rmux_namespace_removed", "session_removed")
    failed = [field for field in required if cleanup_evidence.get(field) is not True]
    residue = cleanup_evidence.get("owned_process_residue")
    if failed:
        errors.append(f"cleanup evidence failed: {', '.join(failed)}")
    if not isinstance(residue, list):
        errors.append("cleanup.owned_process_residue must be a list")
    elif residue and not _text(cleanup_evidence.get("bounded_retained_reason")):
        errors.append("owned process residue requires bounded_retained_reason")
    evidence["cleanup"] = {field: cleanup_evidence.get(field) for field in required}


def _has_system_failure(payload: dict[str, Any]) -> bool:
    for command in payload.get("commands") or []:
        if not isinstance(command, dict):
            continue
        name = _text(command.get("name"))
        if name.startswith("ccb-ask"):
            continue
        if name == "cleanup-rmux-list-sessions" and _cleanup_declares_success(payload):
            continue
        if int(command.get("returncode") or 0) != 0:
            return True
    return False


def _cleanup_declares_success(payload: dict[str, Any]) -> bool:
    cleanup = payload.get("cleanup")
    if not isinstance(cleanup, dict) or cleanup.get("ok") is not True:
        return False
    evidence = cleanup.get("evidence") if isinstance(cleanup.get("evidence"), dict) else cleanup
    return all(evidence.get(field) is True for field in ("endpoint_removed", "token_removed", "rmux_namespace_removed", "session_removed"))


def _has_provider_failure(payload: dict[str, Any]) -> bool:
    for command in payload.get("commands") or []:
        if not isinstance(command, dict) or not _text(command.get("name")).startswith("ccb-ask"):
            continue
        if int(command.get("returncode") or 0) != 0:
            return True
    return False


def _is_ccb_argv(argv: list[str]) -> bool:
    if not argv:
        return False
    executable = Path(argv[0]).stem.lower()
    if executable in {"ccb", "ccb.py"}:
        return True
    return executable.startswith("python") and len(argv) >= 2 and Path(argv[1]).name.lower() in {"ccb", "ccb.py"}


def _is_allowed_direct_rmux_diagnostic(name: str, argv: list[str]) -> bool:
    if name not in ALLOWED_DIRECT_RMUX_DIAGNOSTIC_COMMANDS:
        return False
    executable = Path(argv[0]).stem.lower() if argv else ""
    if executable != "rmux":
        return False
    tail = [str(item) for item in argv[1:]]
    if name == "preflight-rmux-version":
        return tail in (["-V"], ["-version"], ["--version"])
    if name == "cleanup-rmux-list-sessions":
        return tail == ["list-sessions"]
    return False


def _is_forbidden_scope_path(path: str) -> bool:
    if path in ALLOWED_EXACT_PATHS:
        return False
    if any(path.startswith(prefix) for prefix in ALLOWED_PREFIXES):
        return False
    if path == "package.json":
        return True
    if path in FORBIDDEN_EXACT_PATHS:
        return True
    if any(path.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
        allowed_doc = "docs/plantree/plans/windows-rmux-native-backend/topics/rmux-windows-validation-runbook.md"
        return path != allowed_doc
    return False


def _package_json_scope_errors(text: str) -> list[str]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        return [f"package.json is not valid JSON: {exc}"]
    os_value = payload.get("os")
    if os_value != ["linux", "darwin"]:
        return ["package.json os must remain ['linux', 'darwin'] in this feature"]
    return []


def _git_lines(args: list[str]) -> list[str]:
    completed = subprocess.run(args, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr or completed.stdout or "git command failed").strip())
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def _validate_enum(case: dict[str, Any], field: str, allowed: set[str], errors: list[str]) -> None:
    if case.get(field) not in allowed:
        errors.append(f"{_text(case.get('case_id')) or '<unknown>'}: {field} must be one of {sorted(allowed)}")


def _validate_literal(case: dict[str, Any], field: str, expected: Any, errors: list[str]) -> None:
    if case.get(field) != expected:
        errors.append(f"{_text(case.get('case_id')) or '<unknown>'}: {field} must be {expected!r}")


def _validate_str_list(case: dict[str, Any], field: str, errors: list[str]) -> None:
    value = case.get(field)
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item.strip() for item in value):
        errors.append(f"{_text(case.get('case_id')) or '<unknown>'}: {field} must be a non-empty string list")


def _validate_failure_classes(case: dict[str, Any], errors: list[str]) -> None:
    value = case.get("failure_classes")
    if not isinstance(value, list) or not value:
        errors.append(f"{_text(case.get('case_id')) or '<unknown>'}: failure_classes must be non-empty")
        return
    invalid = sorted(str(item) for item in value if item not in ROW_CLASSIFICATIONS)
    if invalid:
        errors.append(f"{_text(case.get('case_id'))}: invalid failure_classes: {', '.join(invalid)}")


def _normalize_path(path: str) -> str:
    value = str(path).replace("\\", "/")
    while value.startswith("./"):
        value = value[2:]
    return value


def _evaluation(
    ok: bool,
    verdict: str,
    failure_class: str,
    errors: list[str],
    warnings: list[str],
    evidence: dict[str, Any],
) -> MatrixEvaluation:
    return MatrixEvaluation(ok=ok, verdict=verdict, failure_class=failure_class, errors=list(errors), warnings=list(warnings), evidence=dict(evidence))


def _text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _md(value: Any) -> str:
    return _text(value).replace("|", "\\|")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build and validate the Windows Rmux validation matrix.")
    parser.add_argument("--lane", choices=sorted(LANES))
    parser.add_argument("--scope", choices=sorted(SCOPES), default="subset")
    parser.add_argument("--transcript", action="append", type=Path, default=[])
    parser.add_argument("--evidence-row", action="append", type=Path, default=[])
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--manifest", action="store_true")
    parser.add_argument("--validate-manifest", action="store_true")
    parser.add_argument("--scope-guard", action="store_true")
    parser.add_argument("--diff-base", default="HEAD")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(list(argv or sys.argv[1:]))
    try:
        if args.manifest:
            payload: dict[str, Any] = {"manifest": matrix_manifest()}
            ok = True
        elif args.validate_manifest:
            result = validate_manifest(matrix_manifest())
            payload = result.to_json()
            ok = result.ok
        elif args.scope_guard:
            package_text = Path("package.json").read_text(encoding="utf-8") if Path("package.json").exists() else None
            result = evaluate_scope_paths(changed_paths(args.diff_base), package_json_text=package_text)
            payload = result.to_json()
            ok = result.ok
        else:
            evidence_rows = [load_json_object(path) for path in args.evidence_row]
            include_fake = args.lane == "fake" and not args.transcript and not evidence_rows
            payload = build_report(
                lane=args.lane,
                scope=args.scope,
                transcripts=list(args.transcript),
                evidence_rows=evidence_rows,
                include_fake_evidence=include_fake,
            )
            write_report(payload, args.output_dir)
            ok = payload["selected_cases_status"] == "pass"
    except Exception as exc:
        payload = {"ok": False, "verdict": "test_design_failure", "failure_class": "test_design_failure", "errors": [str(exc)]}
        ok = False
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        if "selected_cases_status" in payload:
            print(f"selected_cases_status: {payload['selected_cases_status']}")
            print(f"full_matrix_status: {payload['full_matrix_status']}")
        else:
            print(f"verdict: {payload.get('verdict')}")
        for error in payload.get("errors", []):
            print(f"error: {error}", file=sys.stderr)
        for warning in payload.get("warnings", []):
            print(f"warning: {warning}", file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
