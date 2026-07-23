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
from typing import Any


REQUIRED_DEPENDENCIES = {
    "ccbd-windows-tcp-loopback-transport",
    "ccbd-rmux-namespace-lifecycle",
    "accelerator-transport-windows-guard",
    "ccbd-windows-process-liveness",
}
REQUIRED_FIELDS = {
    "schema_version",
    "host_kind",
    "runner_host",
    "control_plane",
    "backend_impl",
    "probe_bypass",
    "backend_selection_source",
    "ccbd_transport",
    "dependency_status",
    "ask_case_kind",
    "verdict",
    "failure_class",
    "commands",
    "artifacts",
    "evidence",
    "redaction_summary",
    "cleanup",
    "final_status",
}
ALLOWED_BACKEND_SOURCES = {"cli", "project_config", "user_config", "env"}
ALLOWED_DEPENDENCY_STATUS = {"ready", "pending", "blocked"}
ALLOWED_ASK_CASES = {"fake_provider", "local_provider", "real_provider"}
ALLOWED_VERDICTS = {"pass", "provider_failure", "system_failure", "test_design_failure", "blocked"}
ALLOWED_FAILURE_CLASSES = {
    "none",
    "provider_failure",
    "system_failure",
    "test_design_failure",
    "dependency_pending",
    "environment_blocked",
}
ALLOWED_FINAL_STATUS = {"pass", "failed", "blocked"}
CORE_COMMANDS = {"ccb-start", "ccb-ping-ccbd", "ccb-doctor", "ccb-ask", "ccb-kill-force"}
COMMAND_REQUIRED_FIELDS = {
    "name",
    "argv",
    "cwd",
    "env_allowlist",
    "started_at",
    "duration_ms",
    "returncode",
    "stdout_path",
    "stderr_path",
}
REQUIRED_ARTIFACTS_FOR_PASS = {"ping", "doctor", "ask", "runtime_session", "cleanup"}
SUCCESS_EVIDENCE_FIELDS = {"control_plane", "backend_selection", "transport", "ask", "cleanup"}
EXPECTED_CORE_SUBCOMMANDS = {
    "ccb-start": (),
    "ccb-ping-ccbd": ("ping", "ccbd"),
    "ccb-doctor": ("doctor",),
    "ccb-ask": ("ask",),
    "ccb-kill-force": ("kill",),
}

TOKEN_RE = re.compile(r"((?<![A-Za-z0-9_])sk-[A-Za-z0-9_-]{6,}|(?<![A-Za-z0-9_])sess-[A-Za-z0-9_-]{6,}|Bearer\s+[A-Za-z0-9._-]+)")
SECRET_RE = re.compile(
    r"(?i)([\"']?\b(api[_-]?key|(?:[A-Za-z0-9]+[_-])*token|secret|password)[\"']?\s*[:=]\s*)([\"']?)([^\"'\s,}]+)([\"']?)"
)
WEAK_RUNTIME_IDENTITIES = {"", "rmux", "ccbd", "tcp_loopback", "tcp-loopback", "true", "false", "none", "unknown"}

FORBIDDEN_PATH_PREFIXES = (
    "lib/",
    "bin/",
    "docs/",
    "README/",
    "mobile/",
    "mcp/",
    "rust/",
)
FORBIDDEN_EXACT_PATHS = {
    "README.md",
    "package.json",
    "install.cmd",
    "install.ps1",
    "install.sh",
    "ccb",
    "ccb.py",
    "ccb_test",
}
ALLOWED_EXACT_PATHS = {
    "scripts/ccbd_windows_full_chain_smoke.py",
    "scripts/ccbd-windows-full-chain-smoke.ps1",
    "test/test_ccbd_windows_full_chain_smoke.py",
    "lib/ccbd/reload_runtime_mount_start.py",
    "lib/ccbd/services/project_namespace_runtime/additive_patch_agents.py",
    "lib/ccbd/services/project_namespace_runtime/additive_patch_windows.py",
    "lib/ccbd/services/project_namespace_runtime/backend.py",
    "lib/ccbd/services/project_namespace_runtime/ensure_identity.py",
    "lib/ccbd/services/project_namespace_runtime/materialize_topology.py",
    "lib/ccbd/services/project_namespace_runtime/move_patch_agents.py",
    "lib/ccbd/services/project_namespace_runtime/sidebar_helper.py",
    "lib/ccbd/start_flow.py",
    "lib/ccbd/start_flow_runtime/service.py",
    "lib/ccbd/start_runtime/agent_runtime.py",
    "lib/ccbd/start_runtime/agent_runtime_binding.py",
    "lib/ccbd/start_runtime/binding_runtime/common.py",
    "lib/ccbd/start_runtime/binding_runtime/validation_context.py",
    "lib/ccbd/start_preparation.py",
    "lib/ccbd/supervisor_runtime/lifecycle.py",
    "lib/provider_runtime/helper_cleanup.py",
    "lib/terminal_runtime/rmux_backend.py",
    "lib/terminal_runtime/rmux_backend_runtime/panes.py",
    "test/test_ccbd_namespace_additive_patch.py",
    "test/test_ccbd_sidebar_helper.py",
    "test/test_ccbd_start_agent_runtime.py",
    "test/test_ccbd_start_binding.py",
    "test/test_ccbd_start_preparation.py",
    "test/test_provider_helper_cleanup.py",
    "test/test_rmux_backend_core.py",
    "test/test_v2_project_namespace_state.py",
    ".codestable/features/2026-07-20-ccbd-windows-full-chain-smoke/ccbd-windows-full-chain-smoke-checklist.yaml",
    ".codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml",
}
ALLOWED_PREFIXES = (
    "artifacts/ccbd-windows-full-chain-smoke/",
    "artifacts/ccbd-windows-full-chain-smoke-",
    ".codestable/goals/2026-07-23-ccbd-windows-full-chain-smoke/",
    ".codestable/issues/2026-07-23-windows-rmux-smoke-runtime-fixes/",
)


@dataclass(frozen=True)
class SmokeEvaluation:
    verdict: str
    failure_class: str
    final_status: str
    errors: list[str]
    warnings: list[str]
    evidence: dict[str, Any]

    @property
    def ok(self) -> bool:
        return self.verdict == "pass" and self.failure_class == "none" and self.final_status == "pass" and not self.errors

    def to_json(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "verdict": self.verdict,
            "failure_class": self.failure_class,
            "final_status": self.final_status,
            "errors": self.errors,
            "warnings": self.warnings,
            "evidence": self.evidence,
        }


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def redact_text(text: str, *, home: str | None = None) -> str:
    value = str(text or "")
    home_value = str(home or os.environ.get("USERPROFILE") or os.environ.get("HOME") or "").strip()
    if home_value:
        for variant in {
            home_value,
            home_value.replace("\\", "/"),
            home_value.replace("\\", "\\\\"),
            home_value.replace("\\", "\\\\\\\\"),
            home_value.replace("\\", "/").replace("/", "\\/"),
        }:
            value = value.replace(variant, "[USER_HOME]")
    value = TOKEN_RE.sub("[REDACTED]", value)
    return SECRET_RE.sub(lambda match: f"{match.group(1)}{match.group(3)}[REDACTED]{match.group(5)}", value)


def contains_secret(text: str) -> bool:
    redacted = redact_text(text)
    return redacted != str(text or "")


def load_transcript(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid transcript JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("transcript root must be an object")
    return payload


def evaluate_transcript(
    payload: dict[str, Any],
    *,
    transcript_path: Path | None = None,
    scan_artifacts: bool = True,
) -> SmokeEvaluation:
    errors: list[str] = []
    warnings: list[str] = []
    evidence: dict[str, Any] = {"checked_at": utc_now()}
    artifact_texts: dict[str, str] = {}

    missing = sorted(REQUIRED_FIELDS - set(payload))
    if missing:
        errors.append(f"missing required fields: {', '.join(missing)}")
        return _result("test_design_failure", "test_design_failure", "failed", errors, warnings, evidence)

    _validate_fixed_fields(payload, errors)
    _validate_runner_host(payload.get("runner_host"), errors)
    _validate_enum("backend_selection_source", payload.get("backend_selection_source"), ALLOWED_BACKEND_SOURCES, errors)
    _validate_enum("ask_case_kind", payload.get("ask_case_kind"), ALLOWED_ASK_CASES, errors)
    _validate_enum("verdict", payload.get("verdict"), ALLOWED_VERDICTS, errors)
    _validate_enum("failure_class", payload.get("failure_class"), ALLOWED_FAILURE_CLASSES, errors)
    _validate_enum("final_status", payload.get("final_status"), ALLOWED_FINAL_STATUS, errors)

    dependencies_pending = _validate_dependencies(payload.get("dependency_status"), errors, evidence)
    commands = _validate_commands(payload.get("commands"), errors, evidence)
    artifact_texts = _validate_artifacts(
        payload.get("artifacts"),
        errors,
        warnings,
        evidence,
        transcript_path=transcript_path,
        scan_artifacts=scan_artifacts,
    )
    cleanup_ok = _validate_cleanup(payload.get("cleanup"), errors, evidence)
    _validate_redaction_summary(payload.get("redaction_summary"), errors, warnings)
    _validate_transcript_redaction(payload, errors)
    _validate_fake_provider(payload, commands, errors)
    _validate_no_bypass_commands(commands, errors)

    if errors:
        return _result("test_design_failure", "test_design_failure", "failed", errors, warnings, evidence)

    if dependencies_pending:
        return _result("blocked", "dependency_pending", "blocked", errors, warnings, evidence)

    command_failure = _command_failure_class(commands)
    if command_failure == "provider_failure":
        return _result("provider_failure", "provider_failure", "failed", errors, warnings, evidence)
    if command_failure == "system_failure" or not cleanup_ok:
        return _result("system_failure", "system_failure", "failed", errors, warnings, evidence)

    _validate_success_evidence(
        payload.get("evidence"),
        payload.get("artifacts"),
        artifact_texts,
        errors,
        evidence,
        backend_selection_source=payload.get("backend_selection_source"),
    )
    if errors:
        return _result("test_design_failure", "test_design_failure", "failed", errors, warnings, evidence)

    declared_verdict = str(payload.get("verdict") or "")
    declared_failure = str(payload.get("failure_class") or "")
    declared_final = str(payload.get("final_status") or "")
    if (declared_verdict, declared_failure, declared_final) != ("pass", "none", "pass"):
        errors.append(
            "transcript declares non-pass terminal state without command/dependency evidence requiring it"
        )
        return _result("test_design_failure", "test_design_failure", "failed", errors, warnings, evidence)

    return _result("pass", "none", "pass", errors, warnings, evidence)


def _result(
    verdict: str,
    failure_class: str,
    final_status: str,
    errors: list[str],
    warnings: list[str],
    evidence: dict[str, Any],
) -> SmokeEvaluation:
    return SmokeEvaluation(
        verdict=verdict,
        failure_class=failure_class,
        final_status=final_status,
        errors=list(errors),
        warnings=list(warnings),
        evidence=dict(evidence),
    )


def _validate_fixed_fields(payload: dict[str, Any], errors: list[str]) -> None:
    expected = {
        "schema_version": 1,
        "host_kind": "native_windows",
        "control_plane": "ccbd",
        "backend_impl": "rmux",
        "probe_bypass": False,
        "ccbd_transport": "tcp_loopback",
    }
    for field, value in expected.items():
        if payload.get(field) != value:
            errors.append(f"{field} must be {value!r}")


def _validate_runner_host(value: Any, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append("runner_host must be an object")
        return
    shell = str(value.get("shell") or "").strip().lower()
    edition = str(value.get("edition") or "").strip()
    version = str(value.get("version") or "").strip()
    executable = str(value.get("executable") or "").strip()
    if shell != "powershell":
        errors.append("runner_host.shell must be PowerShell")
    if edition not in {"Desktop", "Core"}:
        errors.append("runner_host.edition must be Desktop or Core")
    if not version:
        errors.append("runner_host.version must be non-empty")
    if not executable:
        errors.append("runner_host.executable must be non-empty")


def _validate_enum(field: str, value: Any, allowed: set[str], errors: list[str]) -> None:
    if value not in allowed:
        errors.append(f"{field} must be one of: {', '.join(sorted(allowed))}")


def _validate_dependencies(value: Any, errors: list[str], evidence: dict[str, Any]) -> bool:
    if not isinstance(value, dict):
        errors.append("dependency_status must be an object")
        return False
    missing = sorted(REQUIRED_DEPENDENCIES - set(value))
    if missing:
        errors.append(f"dependency_status missing dependencies: {', '.join(missing)}")
    invalid = sorted(name for name, status in value.items() if status not in ALLOWED_DEPENDENCY_STATUS)
    if invalid:
        errors.append(f"dependency_status has invalid statuses for: {', '.join(invalid)}")
    pending = sorted(name for name in REQUIRED_DEPENDENCIES if value.get(name) != "ready")
    evidence["dependency_pending"] = pending
    return bool(pending)


def _validate_commands(value: Any, errors: list[str], evidence: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        errors.append("commands must be a non-empty list")
        return []
    commands: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            errors.append(f"commands[{index}] must be an object")
            continue
        missing = sorted(COMMAND_REQUIRED_FIELDS - set(item))
        if missing:
            errors.append(f"commands[{index}] missing fields: {', '.join(missing)}")
        if not isinstance(item.get("argv"), list) or not all(isinstance(part, str) for part in item.get("argv", [])):
            errors.append(f"commands[{index}].argv must be a list of strings")
        if not isinstance(item.get("env_allowlist"), dict):
            errors.append(f"commands[{index}].env_allowlist must be an object")
        if not isinstance(item.get("returncode"), int):
            errors.append(f"commands[{index}].returncode must be an integer")
        if not isinstance(item.get("duration_ms"), (int, float)) or float(item.get("duration_ms", -1)) < 0:
            errors.append(f"commands[{index}].duration_ms must be a non-negative number")
        commands.append(item)
    names = {str(command.get("name") or "") for command in commands}
    missing_core = sorted(CORE_COMMANDS - names)
    if missing_core:
        errors.append(f"missing core commands: {', '.join(missing_core)}")
    evidence["commands_checked"] = sorted(names)
    return commands


def _validate_artifacts(
    value: Any,
    errors: list[str],
    warnings: list[str],
    evidence: dict[str, Any],
    *,
    transcript_path: Path | None,
    scan_artifacts: bool,
) -> dict[str, str]:
    artifact_texts: dict[str, str] = {}
    if not isinstance(value, dict):
        errors.append("artifacts must be an object")
        return artifact_texts
    empty_keys = sorted(str(key) for key, item in value.items() if not isinstance(item, str) or not item.strip())
    if empty_keys:
        errors.append(f"artifact paths must be non-empty strings: {', '.join(empty_keys)}")
    missing_for_pass = sorted(REQUIRED_ARTIFACTS_FOR_PASS - set(value))
    if missing_for_pass:
        errors.append(f"missing required artifacts: {', '.join(missing_for_pass)}")
    evidence["artifacts_checked"] = sorted(str(key) for key in value)

    if not scan_artifacts or transcript_path is None:
        return artifact_texts
    base_dir = transcript_path.resolve().parent
    secret_artifacts: list[str] = []
    missing_artifacts: list[str] = []
    for key, rel_path in value.items():
        if not isinstance(rel_path, str) or not rel_path.strip():
            continue
        path = (base_dir / rel_path).resolve()
        try:
            path.relative_to(base_dir)
        except ValueError:
            errors.append(f"artifact path escapes transcript directory: {key}")
            continue
        if not path.exists():
            missing_artifacts.append(str(key))
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            warnings.append(f"artifact could not be read for redaction scan: {key}")
            continue
        if contains_secret(text):
            secret_artifacts.append(str(key))
        artifact_texts[str(key)] = text
        _validate_artifact_content_marker(str(key), text, errors)
    _validate_transport_artifact_marker(artifact_texts, errors)
    if missing_artifacts:
        errors.append(f"artifact paths do not exist: {', '.join(sorted(missing_artifacts))}")
    if secret_artifacts:
        errors.append(f"artifact redaction failed: {', '.join(sorted(secret_artifacts))}")
    return artifact_texts


def _validate_cleanup(value: Any, errors: list[str], evidence: dict[str, Any]) -> bool:
    if not isinstance(value, dict):
        errors.append("cleanup must be an object")
        return False
    status = str(value.get("status") or "").strip().lower()
    ok = value.get("ok")
    retained_reason = str(value.get("bounded_retained_reason") or "").strip()
    cleanup_ok = ok is True or status in {"pass", "clean", "cleaned"}
    if not cleanup_ok and not retained_reason:
        evidence["cleanup_status"] = status or "missing"
        return False
    evidence["cleanup_status"] = status or ("bounded_retained" if retained_reason else "pass")
    return True


def _validate_artifact_content_marker(key: str, text: str, errors: list[str]) -> None:
    lowered = str(text or "").lower()
    if key == "ping" and "ccbd" not in lowered:
        errors.append("ping artifact must include ccbd control-plane evidence")
    if key == "doctor":
        if not _line_value_equals(text, "backend_selection_effective", "rmux"):
            errors.append("doctor artifact must include backend_selection_effective: rmux")
        if not _line_value_equals(text, "ccbd_namespace_backend_impl", "rmux"):
            errors.append("doctor artifact must include ccbd_namespace_backend_impl: rmux")
    if key == "ask" and not lowered.strip():
        errors.append("ask artifact must not be empty")
    if key == "runtime_session" and not _runtime_artifact_uses_rmux(text):
        errors.append("runtime_session artifact must include rmux runtime binding evidence")


def _validate_transport_artifact_marker(artifact_texts: dict[str, str], errors: list[str]) -> None:
    combined = "\n".join(
        artifact_texts.get(key, "")
        for key in ("ping", "doctor")
    ).lower()
    if "tcp_loopback" not in combined and "tcp loopback" not in combined:
        errors.append("ping or doctor artifact must include tcp_loopback transport evidence")


def _validate_success_evidence(
    value: Any,
    artifacts: Any,
    artifact_texts: dict[str, str],
    errors: list[str],
    evidence: dict[str, Any],
    *,
    backend_selection_source: Any,
) -> None:
    if not isinstance(value, dict):
        errors.append("evidence must be an object")
        return
    missing = sorted(SUCCESS_EVIDENCE_FIELDS - set(value))
    if missing:
        errors.append(f"evidence missing fields: {', '.join(missing)}")
        return
    _validate_control_plane_evidence(value.get("control_plane"), errors)
    _validate_backend_evidence(value.get("backend_selection"), backend_selection_source, errors)
    _validate_transport_evidence(value.get("transport"), errors)
    _validate_ask_evidence(value.get("ask"), artifacts, artifact_texts, errors)
    _validate_cleanup_evidence(value.get("cleanup"), errors, evidence)


def _validate_control_plane_evidence(value: Any, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append("evidence.control_plane must be an object")
        return
    if value.get("mounted") is not True:
        errors.append("evidence.control_plane.mounted must be true")
    if str(value.get("ping_target") or "").strip().lower() != "ccbd":
        errors.append("evidence.control_plane.ping_target must be ccbd")


def _validate_backend_evidence(value: Any, declared_source: Any, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append("evidence.backend_selection must be an object")
        return
    backend_impl = str(value.get("backend_impl") or value.get("effective_backend") or "").strip().lower()
    if backend_impl != "rmux":
        errors.append("evidence.backend_selection backend must be rmux")
    namespace_backend_impl = str(value.get("namespace_backend_impl") or "").strip().lower()
    if namespace_backend_impl != "rmux":
        errors.append("evidence.backend_selection.namespace_backend_impl must be rmux")
    source = str(value.get("source") or "").strip()
    if source not in ALLOWED_BACKEND_SOURCES:
        errors.append("evidence.backend_selection.source must match backend_selection_source")
    if source != str(declared_source or "").strip():
        errors.append("evidence.backend_selection.source must match backend_selection_source")


def _validate_transport_evidence(value: Any, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append("evidence.transport must be an object")
        return
    if str(value.get("kind") or "").strip().lower() != "tcp_loopback":
        errors.append("evidence.transport.kind must be tcp_loopback")


def _validate_ask_evidence(
    value: Any,
    artifacts: Any,
    artifact_texts: dict[str, str],
    errors: list[str],
) -> None:
    if not isinstance(value, dict):
        errors.append("evidence.ask must be an object")
        return
    required_text_fields = ("provider", "task_id")
    for field in required_text_fields:
        if not str(value.get(field) or "").strip():
            errors.append(f"evidence.ask.{field} must be non-empty")
    has_terminal_evidence = any(
        str(value.get(field) or "").strip()
        for field in ("reply_path", "terminal_state", "accepted_terminal_evidence")
    )
    runtime_session = value.get("runtime_session")
    if not has_terminal_evidence:
        errors.append("evidence.ask requires reply_path, terminal_state, or accepted_terminal_evidence")
    if not isinstance(runtime_session, dict):
        errors.append("evidence.ask.runtime_session must be an object")
        return
    if str(runtime_session.get("backend_impl") or "").strip().lower() != "rmux":
        errors.append("evidence.ask.runtime_session.backend_impl must be rmux")
    evidence_path = str(runtime_session.get("evidence_path") or "").strip()
    expected_path = str((artifacts or {}).get("runtime_session") or "").strip() if isinstance(artifacts, dict) else ""
    if not evidence_path:
        errors.append("evidence.ask.runtime_session.evidence_path must be non-empty")
    elif expected_path and evidence_path != expected_path:
        errors.append("evidence.ask.runtime_session.evidence_path must match artifacts.runtime_session")
    identity_items = [
        (field, str(runtime_session.get(field) or "").strip())
        for field in ("session_id", "session_ref", "pane_id", "runtime_ref")
        if str(runtime_session.get(field) or "").strip()
    ]
    weak_values = [value for _field, value in identity_items if value.lower() in WEAK_RUNTIME_IDENTITIES or len(value) < 4]
    if weak_values:
        errors.append("evidence.ask.runtime_session identity must not be a generic backend/control marker")
    has_session_identity = bool(identity_items)
    if not has_session_identity:
        errors.append("evidence.ask.runtime_session requires session_id, session_ref, pane_id, or runtime_ref")
    if artifact_texts and evidence_path:
        runtime_text = artifact_texts.get("runtime_session")
        if runtime_text is None:
            errors.append("artifacts.runtime_session must be readable when artifact scanning is enabled")
        elif identity_items and not any(_runtime_identity_labeled_in_artifact(field, value, runtime_text) for field, value in identity_items):
            errors.append("evidence.ask.runtime_session identity must appear as a labeled field in runtime_session artifact")


def _runtime_identity_labeled_in_artifact(field: str, value: str, text: str) -> bool:
    if not value or value.lower() in WEAK_RUNTIME_IDENTITIES or len(value) < 4:
        return False
    field_variants = {field, field.replace("_", "-"), field.replace("_", " ")}
    if field in {"runtime_ref", "session_ref", "session_id"}:
        field_variants.add(field.rsplit("_", 1)[0])
    if field == "pane_id":
        field_variants.add("pane")
    escaped_value = re.escape(value)
    for variant in field_variants:
        pattern = rf"(?im)\b{re.escape(variant)}\b\s*[:=]\s*['\"]?{escaped_value}['\"]?\b"
        if re.search(pattern, text):
            return True
    return False


def _line_value_equals(text: str, key: str, expected: str) -> bool:
    pattern = rf"(?im)^\s*{re.escape(key)}\s*:\s*{re.escape(expected)}\s*$"
    return re.search(pattern, str(text or "")) is not None


def _runtime_artifact_uses_rmux(text: str) -> bool:
    value = str(text or "")
    return (
        _line_value_equals(value, "backend_impl", "rmux")
        or re.search(r"(?im)^binding:\s+.*\bruntime=rmux:", value) is not None
    )


def _validate_cleanup_evidence(value: Any, errors: list[str], evidence: dict[str, Any]) -> None:
    if not isinstance(value, dict):
        errors.append("evidence.cleanup must be an object")
        return
    required_bools = ("endpoint_removed", "token_removed", "rmux_namespace_removed", "session_removed")
    failed = [field for field in required_bools if value.get(field) is not True]
    residue = value.get("owned_process_residue")
    if failed:
        errors.append(f"evidence.cleanup residue checks failed: {', '.join(failed)}")
    if not isinstance(residue, list):
        errors.append("evidence.cleanup.owned_process_residue must be a list")
    elif residue and not str(value.get("bounded_retained_reason") or "").strip():
        errors.append("evidence.cleanup owned_process_residue requires bounded_retained_reason")
    evidence["cleanup_residue"] = {field: value.get(field) for field in required_bools}


def _validate_redaction_summary(value: Any, errors: list[str], warnings: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append("redaction_summary must be an object")
        return
    if value.get("redacted") is not True:
        errors.append("redaction_summary.redacted must be true")
    policy = str(value.get("raw_retention_policy") or "").strip().lower()
    if policy not in {"none", "hash_only", "redacted_artifacts_only"}:
        warnings.append("redaction_summary.raw_retention_policy should be none, hash_only, or redacted_artifacts_only")


def _validate_transcript_redaction(payload: dict[str, Any], errors: list[str]) -> None:
    text = json.dumps(payload, ensure_ascii=True, sort_keys=True)
    if contains_secret(text):
        errors.append("transcript redaction failed")


def _validate_fake_provider(payload: dict[str, Any], commands: list[dict[str, Any]], errors: list[str]) -> None:
    if payload.get("ask_case_kind") != "fake_provider":
        return
    ask_case = payload.get("ask_case")
    env_allowed = any(
        str(command.get("name") or "") == "ccb-ask"
        and str((command.get("env_allowlist") or {}).get("CCB_TEST_ENTRYPOINT") or "") == "1"
        for command in commands
    )
    sidecar_allowed = isinstance(ask_case, dict) and ask_case.get("test_entrypoint") == "CCB_TEST_ENTRYPOINT=1"
    if not env_allowed and not sidecar_allowed:
        errors.append("fake_provider requires CCB_TEST_ENTRYPOINT=1 evidence")


def _validate_no_bypass_commands(commands: list[dict[str, Any]], errors: list[str]) -> None:
    for command in commands:
        name = str(command.get("name") or "")
        argv = [str(item) for item in command.get("argv") or []]
        joined = " ".join(argv).replace("\\", "/").lower()
        if "probe_rmux" in joined:
            errors.append(f"{name} uses probe_rmux bypass")
        if name in CORE_COMMANDS and argv:
            executable = Path(argv[0]).stem.lower()
            if executable in {"rmux", "psmux"}:
                errors.append(f"{name} bypasses ccb/ccbd with direct {executable}")
        if name in CORE_COMMANDS and not _is_ccb_command(argv):
            errors.append(f"{name} must execute through ccb")
        if name in CORE_COMMANDS and not _matches_expected_ccb_subcommand(name, argv):
            errors.append(f"{name} argv does not match expected ccb subcommand")


def _is_ccb_command(argv: list[str]) -> bool:
    if not argv:
        return False
    executable = Path(str(argv[0] or "")).stem.lower()
    if executable in {"ccb", "ccb.py"} or str(argv[0]).lower().replace("\\", "/").endswith("/ccb"):
        return True
    if executable.startswith("python") and len(argv) >= 2:
        script = Path(str(argv[1] or "")).name.lower()
        return script in {"ccb", "ccb.py"}
    return False


def _ccb_command_tokens(argv: list[str]) -> list[str]:
    if not _is_ccb_command(argv):
        return []
    executable = Path(str(argv[0] or "")).stem.lower()
    index = 2 if executable.startswith("python") else 1
    tokens = list(argv[index:])
    result: list[str] = []
    skip_next = False
    for token in tokens:
        if skip_next:
            skip_next = False
            continue
        if token == "--project":
            skip_next = True
            continue
        result.append(token)
    return result


def _matches_expected_ccb_subcommand(name: str, argv: list[str]) -> bool:
    expected = EXPECTED_CORE_SUBCOMMANDS[name]
    tokens = _ccb_command_tokens(argv)
    if not expected:
        return not tokens
    if tuple(tokens[: len(expected)]) != expected:
        return False
    if name == "ccb-ask" and len(tokens) > 1 and tokens[1] in {"get", "cancel"}:
        return False
    if name == "ccb-kill-force":
        return "-f" in tokens[len(expected):] or "--force" in tokens[len(expected):]
    return True


def _command_failure_class(commands: list[dict[str, Any]]) -> str | None:
    by_name = {str(command.get("name") or ""): command for command in commands}
    ask_command = by_name.get("ccb-ask")
    if ask_command and int(ask_command.get("returncode") or 0) != 0:
        return "provider_failure"
    for name in CORE_COMMANDS - {"ccb-ask"}:
        command = by_name.get(name)
        if command and int(command.get("returncode") or 0) != 0:
            return "system_failure"
    return None


def evaluate_scope_paths(paths: list[str]) -> SmokeEvaluation:
    normalized = sorted({_normalize_path(path) for path in paths if str(path).strip()})
    forbidden = [path for path in normalized if _is_forbidden_scope_path(path)]
    evidence = {"checked_at": utc_now(), "changed_paths": normalized, "forbidden_paths": forbidden}
    if forbidden:
        return _result(
            "test_design_failure",
            "test_design_failure",
            "failed",
            [f"scope guard rejected paths: {', '.join(forbidden)}"],
            [],
            evidence,
        )
    return _result("pass", "none", "pass", [], [], evidence)


def changed_paths(diff_base: str) -> list[str]:
    tracked = _git_lines(["git", "diff", "--name-only", "--diff-filter=ACMRTUXB", diff_base, "--"])
    untracked = _git_lines(["git", "ls-files", "--others", "--exclude-standard"])
    return sorted(set(tracked + untracked))


def _git_lines(args: list[str]) -> list[str]:
    completed = subprocess.run(args, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr or completed.stdout or "git command failed").strip())
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def _normalize_path(path: str) -> str:
    value = str(path).replace("\\", "/")
    while value.startswith("./"):
        value = value[2:]
    return value


def _is_forbidden_scope_path(path: str) -> bool:
    if path in ALLOWED_EXACT_PATHS:
        return False
    if any(path.startswith(prefix) for prefix in ALLOWED_PREFIXES):
        return False
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate CCB Windows ccbd -> rmux full-chain smoke transcripts.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--transcript", type=Path)
    mode.add_argument("--scope-guard", action="store_true")
    parser.add_argument("--diff-base", default="HEAD")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-artifact-scan", action="store_true")
    args = parser.parse_args(argv)

    try:
        if args.scope_guard:
            result = evaluate_scope_paths(changed_paths(args.diff_base))
        else:
            transcript_path = args.transcript
            payload = load_transcript(transcript_path)
            result = evaluate_transcript(
                payload,
                transcript_path=transcript_path,
                scan_artifacts=not args.no_artifact_scan,
            )
    except Exception as exc:
        result = _result(
            "test_design_failure",
            "test_design_failure",
            "failed",
            [str(exc)],
            [],
            {"checked_at": utc_now()},
        )

    output = result.to_json()
    if args.json:
        print(json.dumps(output, ensure_ascii=True, sort_keys=True))
    else:
        print(f"{output['verdict']} ({output['failure_class']}): {output['final_status']}")
        for error in output["errors"]:
            print(f"error: {error}", file=sys.stderr)
        for warning in output["warnings"]:
            print(f"warning: {warning}", file=sys.stderr)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
