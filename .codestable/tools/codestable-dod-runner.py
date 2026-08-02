#!/usr/bin/env python3
"""Run checklist dod.commands and report real exit codes."""

from __future__ import annotations

import os
import json
import sys
from pathlib import Path
from typing import Any

if os.environ.get("PYTHONDONTWRITEBYTECODE") != "1":
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    os.execvpe(sys.executable, [sys.executable, *sys.argv], os.environ)
sys.dont_write_bytecode = True

from codestable_gate_common import gate_result, load_yaml, main_exit, parse_args, repo_root, run_command


def collect_commands(checklist: dict[str, Any]) -> list[dict[str, Any]]:
    # Authoritative schema: top-level `dod.commands` (cs-feat-design reference §"DoD
    # Contract" — `dod` is a top-level checklist key alongside `steps`/`checks`).
    # If present, it is the single source — do NOT also pull step-level commands,
    # or a checklist carrying both would execute each command twice.
    top_commands = (checklist.get("dod") or {}).get("commands") or []
    if top_commands:
        return list(top_commands)
    # Backward-compat: no top-level dod → fall back to step-level `dod.commands`.
    commands: list[dict[str, Any]] = []
    for step in checklist.get("steps", []) or []:
        dod = step.get("dod") or {}
        for command in dod.get("commands", []) or []:
            commands.append(command)
    return commands


def is_manual_command(command: dict[str, Any]) -> bool:
    raw_command = str(command.get("command", "")).lstrip().casefold()
    test_status = str(command.get("test_status") or "").strip().casefold()
    return test_status.startswith("manual") or raw_command.startswith(("manual ", "manual-action "))


def manual_run(
    command: dict[str, Any],
    root: Path | None = None,
    feature: str = "",
) -> dict[str, Any]:
    result = {
        "command": str(command.get("command", "")),
        "exit_code": None,
        "stdout": "",
        "stderr": "",
        "manual": True,
        "status": "manual-pending",
    }
    evidence_ref = str(command.get("evidence_ref") or "").strip()
    if not evidence_ref or root is None:
        return result

    evidence_path = Path(evidence_ref)
    if not evidence_path.is_absolute():
        evidence_path = root / evidence_path
    try:
        evidence_path = evidence_path.resolve()
        root_path = root.resolve()
        evidence_path.relative_to(root_path)
    except ValueError:
        result["evidence_error"] = f"manual evidence must stay under repository root: {evidence_ref}"
        return result
    if not evidence_path.is_file():
        result["evidence_error"] = f"manual evidence not found: {evidence_ref}"
        return result
    if evidence_path.suffix.casefold() != ".json":
        result["evidence_error"] = f"manual evidence must be a JSON manifest: {evidence_ref}"
        return result
    try:
        manifest = json.loads(evidence_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        result["evidence_error"] = f"manual evidence manifest unreadable: {evidence_ref} ({exc})"
        return result
    if not isinstance(manifest, dict):
        result["evidence_error"] = f"manual evidence manifest must be a JSON object: {evidence_ref}"
        return result
    expected_command_id = str(command.get("evidence_command_id") or command.get("id") or "")
    if manifest.get("feature") != feature:
        result["evidence_error"] = f"manual evidence feature mismatch: {evidence_ref}"
        return result
    if manifest.get("command_id") != expected_command_id:
        result["evidence_error"] = f"manual evidence command mismatch: {evidence_ref}"
        return result
    manifest_status = str(manifest.get("status") or "").casefold()
    if manifest_status != "passed":
        result["evidence_status"] = manifest_status or "missing"
        result["status"] = f"manual-evidence-{manifest_status or 'invalid'}"
        result["evidence_error"] = f"manual evidence status is not passed: {evidence_ref}"
        return result
    expected_scope = str(command.get("evidence_scope") or "").strip()
    if expected_scope and manifest.get("scope") != expected_scope:
        result["evidence_error"] = f"manual evidence scope mismatch: {evidence_ref}"
        return result
    expected_observations = command.get("evidence_observations") or {}
    manifest_observations = manifest.get("observations") or {}
    if not isinstance(expected_observations, dict) or not isinstance(manifest_observations, dict):
        result["evidence_error"] = f"manual evidence observations must be JSON objects: {evidence_ref}"
        return result
    for key, expected in expected_observations.items():
        if manifest_observations.get(key) != expected:
            result["evidence_error"] = f"manual evidence observation mismatch for {key}: {evidence_ref}"
            return result
    source_ref = str(manifest.get("source_ref") or "").strip()
    if not source_ref:
        result["evidence_error"] = f"manual evidence source_ref missing: {evidence_ref}"
        return result
    source_path = Path(source_ref)
    if not source_path.is_absolute():
        source_path = root / source_path
    try:
        source_path = source_path.resolve()
        source_path.relative_to(root_path)
    except ValueError:
        result["evidence_error"] = f"manual evidence source_ref must stay under repository root: {source_ref}"
        return result
    if not source_path.is_file():
        result["evidence_error"] = f"manual evidence source_ref not found: {source_ref}"
        return result
    result["evidence_ref"] = evidence_ref
    result["source_ref"] = source_ref
    result["evidence_status"] = manifest_status
    result["evidence_scope"] = manifest.get("scope")
    result["evidence_observations"] = manifest_observations
    result["evidence_verdict"] = manifest.get("verdict")
    result["manual_evidence"] = True
    result["status"] = "manual-evidence-present"
    return result


def main() -> None:
    parser = parse_args("Run explicit checklist dod.commands using real subprocess exit codes.")
    parser.add_argument("--checklist", required=True, help="Path to checklist YAML")
    parser.add_argument("--only", action="append", default=[], help="Run only this command id; repeatable")
    parser.add_argument("--stage", default="implementation.before_review")
    args = parser.parse_args()

    checklist_path = Path(args.checklist)
    if not checklist_path.exists():
        result = gate_result("dod-runner", args.stage, "blocked", [f"checklist not found: {checklist_path}"])
        main_exit(result, args.json_out)

    checklist = load_yaml(checklist_path)
    commands = collect_commands(checklist)
    if args.only:
        requested = set(args.only)
        commands = [command for command in commands if command.get("id") in requested]
    if not commands:
        result = gate_result("dod-runner", args.stage, "skipped", warnings=["no matching dod.commands found"])
        main_exit(result, args.json_out)

    root = repo_root()
    feature = str(checklist.get("feature") or "").strip()
    evidence = []
    blocking = []
    warnings = []
    manual_blocked = False
    for command in commands:
        raw_command = str(command.get("command", ""))
        if is_manual_command(command):
            run = manual_run(command, root, feature)
            if not run.get("manual_evidence"):
                message = run.get(
                    "evidence_error",
                    "manual command requires external transcript evidence",
                )
                if command.get("core"):
                    manual_blocked = True
                    blocking.append(f"{command.get('id')}: {message}")
                else:
                    warnings.append(f"{command.get('id')}: {message}")
        else:
            run = run_command(raw_command, root)
        run["id"] = command.get("id")
        run["core"] = bool(command.get("core"))
        run["failure_handling"] = command.get("failure_handling")
        run["test_status"] = command.get("test_status")
        evidence.append(run)
        if run.get("manual"):
            continue
        if run["exit_code"] != 0 and command.get("failure_handling") == "document-baseline":
            warnings.append(f"{command.get('id')}: documented baseline failed with exit {run['exit_code']}")
        elif run["exit_code"] != 0 and run["core"]:
            blocking.append(f"{command.get('id')}: command failed with exit {run['exit_code']}")
        elif run["exit_code"] != 0:
            warnings.append(f"{command.get('id')}: non-core command failed with exit {run['exit_code']}")

    status = "blocked" if manual_blocked else "failed" if blocking else "passed"
    result = gate_result("dod-runner", args.stage, status, blocking, warnings, evidence)
    main_exit(result, args.json_out)


if __name__ == "__main__":
    main()
