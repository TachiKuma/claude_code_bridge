from __future__ import annotations

import argparse
import json
import platform
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FEATURE = "2026-07-31-herdr-backend-contract-spike"
CORE_OPERATIONS = [
    "schema",
    "server_status",
    "session_attach",
    "pane_spawn",
    "send_input",
    "read_output",
    "kill_pane",
    "detach_reattach",
    "server_restart_restore",
]
SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*[^;\s]+"),
    re.compile(r"(?i)(bearer)\s+[a-z0-9._~+/-]+"),
]


class EvidenceError(ValueError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _platform_name() -> str:
    if sys.platform.startswith("win"):
        return "win32"
    if sys.platform == "darwin":
        return "darwin"
    if sys.platform.startswith("linux"):
        return "linux"
    return "unknown"


def _cpu_arch() -> str:
    machine = platform.machine().lower()
    if machine in {"amd64", "x86_64"}:
        return "x64"
    if machine in {"aarch64", "arm64"}:
        return "arm64"
    if machine in {"x86", "i386", "i686"}:
        return "ia32"
    return "unknown"


def _python_bitness() -> str:
    bits = platform.architecture()[0]
    if bits == "64bit":
        return "64bit"
    if bits == "32bit":
        return "32bit"
    return "unknown"


def _is_wsl() -> bool:
    if not sys.platform.startswith("linux"):
        return False
    try:
        text = Path("/proc/version").read_text(encoding="utf-8", errors="ignore").lower()
    except OSError:
        return False
    return "microsoft" in text or "wsl" in text


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise EvidenceError(f"missing JSON file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise EvidenceError(f"invalid JSON file: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise EvidenceError(f"JSON root must be object: {path}")
    return payload


def _load_platform_gate(path: Path | None) -> tuple[dict[str, Any] | None, str | None, str | None]:
    if path is None:
        return None, "manual-host-missing", "missing --platform-gate-ref"
    try:
        payload = _read_json(path)
    except EvidenceError as exc:
        return None, "manual-host-missing", str(exc)
    gate = payload.get("gate")
    if not isinstance(gate, dict):
        return payload, "platform-gate-blocked", "platform gate artifact lacks gate object"
    if gate.get("supported") is not True:
        reason = str(gate.get("detail_reason") or gate.get("failure_reason") or "platform gate not supported")
        return payload, "platform-gate-blocked", reason
    return payload, None, None


def _redact_text(text: str) -> str:
    redacted = text
    home = str(Path.home())
    if home:
        redacted = redacted.replace(home, "<home>")
        redacted = redacted.replace(home.replace("\\", "/"), "<home>")
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub(lambda match: f"{match.group(1)}=<redacted>", redacted)
    return redacted


def _redact_command(command: list[str]) -> list[str]:
    redacted: list[str] = []
    redact_next = False
    secret_option = re.compile(r"(?i)^--?(api[_-]?key|token|secret|password)$")
    for part in command:
        if redact_next:
            redacted.append("<redacted>")
            redact_next = False
            continue
        redacted_part = _redact_text(part)
        redacted.append(redacted_part)
        if secret_option.match(part):
            redact_next = True
    return redacted


def _command_ref(log_dir: Path, name: str, command: list[str], result: subprocess.CompletedProcess[str]) -> str:
    log_dir.mkdir(parents=True, exist_ok=True)
    ref = log_dir / f"{name}.json"
    payload = {
        "command": _redact_command(command),
        "returncode": result.returncode,
        "stdout_excerpt": _redact_text((result.stdout or "")[-4000:]),
        "stderr_excerpt": _redact_text((result.stderr or "")[-4000:]),
    }
    ref.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return ref.as_posix()


def _process_ref(log_dir: Path, name: str, command: list[str], process: subprocess.Popen[str]) -> str:
    log_dir.mkdir(parents=True, exist_ok=True)
    ref = log_dir / f"{name}.json"
    payload = {
        "command": _redact_command(command),
        "pid": process.pid,
        "returncode": process.poll(),
        "stdout_excerpt": "",
        "stderr_excerpt": "",
    }
    ref.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return ref.as_posix()


def _run(command: list[str], *, timeout: int = 20) -> tuple[subprocess.CompletedProcess[str], int]:
    start = time.perf_counter()
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        result = subprocess.CompletedProcess(
            command,
            124,
            stdout=stdout,
            stderr=(stderr + f"\ntimed out after {timeout}s").strip(),
        )
    except OSError as exc:
        result = subprocess.CompletedProcess(command, 127, stdout="", stderr=str(exc))
    elapsed_ms = int((time.perf_counter() - start) * 1000)
    return result, elapsed_ms


def _json_object_output_passed(result: subprocess.CompletedProcess[str]) -> bool:
    if result.returncode != 0:
        return False
    try:
        payload = json.loads(result.stdout or "")
    except json.JSONDecodeError:
        return False
    return isinstance(payload, dict)


def _json_object_output(result: subprocess.CompletedProcess[str]) -> dict[str, Any] | None:
    if result.returncode != 0:
        return None
    try:
        payload = json.loads(result.stdout or "")
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _json_path(payload: dict[str, Any] | None, path: list[str]) -> Any:
    current: Any = payload
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _first_pane_id(payload: dict[str, Any] | None) -> str | None:
    pane_id = _json_path(payload, ["result", "pane", "pane_id"])
    if isinstance(pane_id, str) and pane_id:
        return pane_id
    root_pane_id = _json_path(payload, ["result", "root_pane", "pane_id"])
    if isinstance(root_pane_id, str) and root_pane_id:
        return root_pane_id
    return None


def _first_workspace_id(payload: dict[str, Any] | None) -> str | None:
    workspace_id = _json_path(payload, ["result", "workspace", "workspace_id"])
    if isinstance(workspace_id, str) and workspace_id:
        return workspace_id
    pane_workspace_id = _json_path(payload, ["result", "pane", "workspace_id"])
    if isinstance(pane_workspace_id, str) and pane_workspace_id:
        return pane_workspace_id
    root_workspace_id = _json_path(payload, ["result", "root_pane", "workspace_id"])
    if isinstance(root_workspace_id, str) and root_workspace_id:
        return root_workspace_id
    return None


def _operation(
    operation: str,
    status: str,
    *,
    command_ref: str,
    elapsed_ms: int | None = None,
    evidence_ref: str | None = None,
    failure_class: str | None = None,
    diagnostic: str,
) -> dict[str, Any]:
    return {
        "operation": operation,
        "status": status,
        "command_ref": command_ref,
        "elapsed_ms": elapsed_ms,
        "evidence_ref": evidence_ref,
        "failure_class": failure_class,
        "diagnostic": diagnostic,
    }


def _blocked_operations(failure_class: str, diagnostic: str) -> list[dict[str, Any]]:
    return [
        _operation(
            operation,
            "blocked",
            command_ref="not-run",
            failure_class=failure_class,
            diagnostic=diagnostic,
        )
        for operation in CORE_OPERATIONS
    ]


def _host_evidence(platform_gate_ref: Path | None, platform_payload: dict[str, Any] | None) -> dict[str, Any]:
    gate = platform_payload.get("gate", {}) if isinstance(platform_payload, dict) else {}
    return {
        "os_platform": _platform_name(),
        "cpu_arch": _cpu_arch(),
        "python_bitness": _python_bitness(),
        "is_wsl": _is_wsl(),
        "dedicated_host_label": platform.node() or None,
        "platform_gate_host_label": platform_payload.get("host_label") if isinstance(platform_payload, dict) else None,
        "platform_gate_os_platform": gate.get("os_platform"),
        "platform_gate_cpu_arch": gate.get("cpu_arch"),
        "platform_gate_python_bitness": gate.get("python_bitness"),
        "platform_gate_ref": platform_gate_ref.as_posix() if platform_gate_ref is not None else None,
        "platform_gate_supported": gate.get("supported") is True,
        "platform_gate_failure_reason": gate.get("failure_reason"),
        "platform_gate_detail_reason": gate.get("detail_reason"),
    }


def _host_gate_mismatch_reason(host: dict[str, Any]) -> str | None:
    comparisons = [
        ("host_label", host.get("dedicated_host_label"), host.get("platform_gate_host_label")),
        ("os_platform", host.get("os_platform"), host.get("platform_gate_os_platform")),
        ("cpu_arch", host.get("cpu_arch"), host.get("platform_gate_cpu_arch")),
        ("python_bitness", host.get("python_bitness"), host.get("platform_gate_python_bitness")),
    ]
    mismatches = [
        f"{name}: current={current} gate={gate}"
        for name, current, gate in comparisons
        if gate is not None and current != gate
    ]
    if mismatches:
        return "platform gate artifact does not match current host: " + "; ".join(mismatches)
    return None


def _base_evidence(
    *,
    platform_gate_ref: Path | None,
    platform_payload: dict[str, Any] | None,
    herdr_executable: str | None,
    operations: list[dict[str, Any]],
    provider_cli_dry_run: dict[str, Any],
    fallback_terminal_smoke: dict[str, Any] | None,
    restore: dict[str, Any],
    verdict: str,
    failure_class: str,
    adapter_recommendation: str,
    residual_risks: list[str],
    artifact_refs: dict[str, str],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "feature": FEATURE,
        "generated_at": _now(),
        "host": _host_evidence(platform_gate_ref, platform_payload),
        "herdr": {
            "executable": herdr_executable,
            "version": None,
            "api_schema_ref": artifact_refs.get("schema"),
            "socket_ref": artifact_refs.get("socket"),
            "server_identity": None,
            "status": "missing" if herdr_executable is None else "unknown",
        },
        "operations": operations,
        "provider_cli_dry_run": provider_cli_dry_run,
        "fallback_terminal_smoke": fallback_terminal_smoke,
        "restore": restore,
        "capability_projection": {
            "command_status": {
                op["operation"]: "supported" if op["status"] == "pass" else "unsupported"
                for op in operations
            },
            "semantic_status": {
                op["operation"]: "supported" if op["status"] == "pass" else "unsupported"
                for op in operations
            },
            "windows_beta_gaps": [],
            "blocking_gaps": [op["operation"] for op in operations if op["status"] != "pass"],
        },
        "verdict": verdict,
        "failure_class": failure_class,
        "adapter_recommendation": adapter_recommendation,
        "residual_risks": residual_risks,
        "artifact_refs": artifact_refs,
    }


def build_blocked_evidence(
    *,
    platform_gate_ref: Path | None,
    platform_payload: dict[str, Any] | None,
    failure_class: str,
    diagnostic: str,
) -> dict[str, Any]:
    provider = {
        "provider_slug": None,
        "dry_run_kind": "provider_cli",
        "command": [],
        "pane_ref": None,
        "output_match": False,
        "exit_observed": False,
        "killed_by_spike": False,
        "treated_as_completion_authority": False,
        "public_provider_parity_claimed": False,
        "failure_class": failure_class,
    }
    restore = {
        "detach_reattach_checked": False,
        "detach_process_continues": None,
        "server_restart_checked": False,
        "restart_isolation": {
            "server_ref_kind": "unknown",
            "session_name": "",
            "socket_ref": None,
            "config_ref": None,
            "server_identity_before": None,
            "server_identity_after": None,
            "preexisting_sessions_before": [],
            "created_by_spike": False,
            "stop_command_ref": None,
            "cleanup_targets": [],
        },
        "restart_scope": "blocked-not-isolated",
        "server_identity": None,
        "preexisting_sessions_checked": False,
        "restart_authorized": False,
        "layout_restored": None,
        "output_history_restored": None,
        "agent_session_restored": None,
        "old_process_expected_to_survive": False,
        "diagnostic": diagnostic,
    }
    return _base_evidence(
        platform_gate_ref=platform_gate_ref,
        platform_payload=platform_payload,
        herdr_executable=None,
        operations=_blocked_operations(failure_class, diagnostic),
        provider_cli_dry_run=provider,
        fallback_terminal_smoke=None,
        restore=restore,
        verdict="blocked",
        failure_class=failure_class,
        adapter_recommendation="stop",
        residual_risks=[diagnostic],
        artifact_refs={"platform_gate": platform_gate_ref.as_posix() if platform_gate_ref is not None else ""},
    )


def run_spike(args: argparse.Namespace) -> dict[str, Any]:
    platform_gate_ref = Path(args.platform_gate_ref) if args.platform_gate_ref else None
    platform_payload, platform_failure, platform_diagnostic = _load_platform_gate(platform_gate_ref)
    if platform_failure is not None:
        return build_blocked_evidence(
            platform_gate_ref=platform_gate_ref,
            platform_payload=platform_payload,
            failure_class=platform_failure,
            diagnostic=platform_diagnostic or platform_failure,
        )

    host = _host_evidence(platform_gate_ref, platform_payload)
    mismatch_reason = _host_gate_mismatch_reason(host)
    if mismatch_reason is not None:
        return build_blocked_evidence(
            platform_gate_ref=platform_gate_ref,
            platform_payload=platform_payload,
            failure_class="manual-host-missing",
            diagnostic=mismatch_reason,
        )
    if (
        host["os_platform"] != "win32"
        or host["cpu_arch"] != "x64"
        or host["python_bitness"] != "64bit"
        or host["is_wsl"]
        or not host["dedicated_host_label"]
    ):
        return build_blocked_evidence(
            platform_gate_ref=platform_gate_ref,
            platform_payload=platform_payload,
            failure_class="manual-host-missing",
            diagnostic="current host is not admitted as dedicated Native Windows x64",
        )

    herdr = shutil.which("herdr")
    if herdr is None:
        return build_blocked_evidence(
            platform_gate_ref=platform_gate_ref,
            platform_payload=platform_payload,
            failure_class="herdr-missing",
            diagnostic="herdr executable not found on PATH",
        )

    if not args.isolated_server:
        return build_blocked_evidence(
            platform_gate_ref=platform_gate_ref,
            platform_payload=platform_payload,
            failure_class="unsupported-capability",
            diagnostic="server restart restore requires --isolated-server",
        )

    scope_args = _isolated_scope_args(args)
    if scope_args is None:
        return build_blocked_evidence(
            platform_gate_ref=platform_gate_ref,
            platform_payload=platform_payload,
            failure_class="unsupported-capability",
            diagnostic="Herdr probe requires explicit isolated socket/config proof created by this spike",
        )

    log_dir = Path(args.out).parent / "raw-command-refs"
    operations: list[dict[str, Any]] = []
    artifact_refs: dict[str, str] = {"platform_gate": platform_gate_ref.as_posix()}
    cleanup_targets: list[str] = [args.session]
    cleanup_refs: dict[str, str] = {}

    version_command = [herdr, *scope_args, "--version"]
    version_result, _ = _run(version_command)
    version_ref = _command_ref(log_dir, "herdr-version", version_command, version_result)
    artifact_refs["version"] = version_ref

    schema_command = [herdr, *scope_args, "api", "schema", "--json"]
    schema_result, schema_elapsed = _run(schema_command)
    schema_ref = _command_ref(log_dir, "herdr-api-schema", schema_command, schema_result)
    artifact_refs["schema"] = schema_ref
    schema_pass = _json_object_output_passed(schema_result)
    operations.append(
        _operation(
            "schema",
            "pass" if schema_pass else "blocked",
            command_ref=schema_ref,
            elapsed_ms=schema_elapsed,
            evidence_ref=schema_ref,
            failure_class=None if schema_pass else "schema-mismatch",
            diagnostic="schema command returned valid JSON" if schema_pass else "schema command did not return JSON object output",
        )
    )

    status_command = [herdr, *scope_args, "status", "--json"]
    status_result, status_elapsed = _run(status_command)
    status_ref = _command_ref(log_dir, "herdr-status", status_command, status_result)
    artifact_refs["status"] = status_ref
    status_pass = _json_object_output_passed(status_result)
    operations.append(
        _operation(
            "server_status",
            "pass" if status_pass else "blocked",
            command_ref=status_ref,
            elapsed_ms=status_elapsed,
            evidence_ref=status_ref,
            failure_class=None if status_pass else "unsupported-capability",
            diagnostic="status command returned valid JSON" if status_pass else "status command did not return JSON object output",
        )
    )
    status_payload = _json_object_output(status_result)
    server_started_by_spike = False
    server_running = _json_path(status_payload, ["server", "running"]) is True
    server_identity_before = _json_path(status_payload, ["server", "socket"])
    if status_pass and not server_running:
        start_command = [herdr, *scope_args, "server"]
        start_kwargs: dict[str, Any] = {
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.DEVNULL,
            "text": True,
        }
        if sys.platform.startswith("win"):
            start_kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        server_process = subprocess.Popen(start_command, **start_kwargs)
        cleanup_refs["server_start"] = _process_ref(log_dir, "herdr-server-start", start_command, server_process)
        time.sleep(2)
        status_after_start_command = [herdr, *scope_args, "status", "--json"]
        status_after_start_result, _ = _run(status_after_start_command)
        status_after_start_ref = _command_ref(
            log_dir,
            "herdr-status-after-start",
            status_after_start_command,
            status_after_start_result,
        )
        artifact_refs["status_after_start"] = status_after_start_ref
        status_after_start_payload = _json_object_output(status_after_start_result)
        server_running = _json_path(status_after_start_payload, ["server", "running"]) is True
        server_identity_before = _json_path(status_after_start_payload, ["server", "socket"]) or server_identity_before
        server_started_by_spike = server_running

    workspace_command = [
        herdr,
        *scope_args,
        "workspace",
        "create",
        "--cwd",
        str(Path.cwd()),
        "--label",
        args.session,
        "--focus",
    ]
    workspace_result, workspace_elapsed = _run(workspace_command)
    workspace_ref = _command_ref(log_dir, "herdr-workspace-create", workspace_command, workspace_result)
    artifact_refs["workspace_create"] = workspace_ref
    workspace_payload = _json_object_output(workspace_result)
    root_pane_id = _first_pane_id(workspace_payload)
    workspace_id = _first_workspace_id(workspace_payload)
    if workspace_id:
        cleanup_targets.append(workspace_id)
    session_attach_pass = root_pane_id is not None and workspace_id is not None
    operations.append(
        _operation(
            "session_attach",
            "pass" if session_attach_pass else "blocked",
            command_ref=workspace_ref,
            elapsed_ms=workspace_elapsed,
            evidence_ref=workspace_ref,
            failure_class=None if session_attach_pass else "unsupported-capability",
            diagnostic=(
                "workspace create returned workspace and root pane ids"
                if session_attach_pass
                else "workspace create did not return workspace/root pane ids"
            ),
        )
    )

    spawned_pane_id: str | None = None
    if root_pane_id is not None:
        pane_spawn_command = [
            herdr,
            *scope_args,
            "pane",
            "split",
            root_pane_id,
            "--direction",
            "right",
            "--ratio",
            "0.5",
            "--cwd",
            str(Path.cwd()),
            "--focus",
        ]
        pane_spawn_result, pane_spawn_elapsed = _run(pane_spawn_command)
        pane_spawn_ref = _command_ref(log_dir, "herdr-pane-spawn", pane_spawn_command, pane_spawn_result)
        artifact_refs["pane_spawn"] = pane_spawn_ref
        pane_spawn_payload = _json_object_output(pane_spawn_result)
        spawned_pane_id = _first_pane_id(pane_spawn_payload)
        pane_spawn_pass = spawned_pane_id is not None
    else:
        pane_spawn_result = subprocess.CompletedProcess([], 1, stdout="", stderr="missing root pane id")
        pane_spawn_elapsed = None
        pane_spawn_ref = "not-run"
        pane_spawn_pass = False
    operations.append(
        _operation(
            "pane_spawn",
            "pass" if pane_spawn_pass else "blocked",
            command_ref=pane_spawn_ref,
            elapsed_ms=pane_spawn_elapsed,
            evidence_ref=pane_spawn_ref if pane_spawn_ref != "not-run" else None,
            failure_class=None if pane_spawn_pass else "unsupported-capability",
            diagnostic="pane split returned pane id" if pane_spawn_pass else "pane split did not return pane id",
        )
    )

    marker = "CCB_HERDR_SPIKE_OK"
    send_pass = False
    read_pass = False
    kill_pass = False
    if spawned_pane_id is not None:
        time.sleep(1)
        send_text_command = [herdr, *scope_args, "pane", "send-text", spawned_pane_id, f"cmd /c echo {marker}"]
        send_text_result, send_text_elapsed = _run(send_text_command)
        send_text_ref = _command_ref(log_dir, "herdr-pane-send-text", send_text_command, send_text_result)
        artifact_refs["send_text"] = send_text_ref
        send_keys_command = [herdr, *scope_args, "pane", "send-keys", spawned_pane_id, "Enter"]
        send_keys_result, send_keys_elapsed = _run(send_keys_command)
        send_keys_ref = _command_ref(log_dir, "herdr-pane-send-keys", send_keys_command, send_keys_result)
        artifact_refs["send_keys"] = send_keys_ref
        send_pass = send_text_result.returncode == 0 and send_keys_result.returncode == 0
        send_elapsed = send_text_elapsed + send_keys_elapsed
        send_ref = send_keys_ref
    else:
        send_elapsed = None
        send_ref = "not-run"
    operations.append(
        _operation(
            "send_input",
            "pass" if send_pass else "blocked",
            command_ref=send_ref,
            elapsed_ms=send_elapsed,
            evidence_ref=send_ref if send_ref != "not-run" else None,
            failure_class=None if send_pass else "unsupported-capability",
            diagnostic="send-text plus Enter completed" if send_pass else "send-text or Enter failed",
        )
    )

    if spawned_pane_id is not None and send_pass:
        time.sleep(2)
        read_command = [herdr, *scope_args, "pane", "read", spawned_pane_id, "--lines", "20", "--format", "text"]
        read_result, read_elapsed = _run(read_command)
        read_ref = _command_ref(log_dir, "herdr-pane-read", read_command, read_result)
        artifact_refs["read_output"] = read_ref
        read_pass = read_result.returncode == 0 and marker in (read_result.stdout or "")
    else:
        read_elapsed = None
        read_ref = "not-run"
    operations.append(
        _operation(
            "read_output",
            "pass" if read_pass else "blocked",
            command_ref=read_ref,
            elapsed_ms=read_elapsed,
            evidence_ref=read_ref if read_ref != "not-run" else None,
            failure_class=None if read_pass else "unsupported-capability",
            diagnostic="pane read observed marker output" if read_pass else "pane read did not observe marker output",
        )
    )

    if spawned_pane_id is not None:
        kill_command = [herdr, *scope_args, "pane", "close", spawned_pane_id]
        kill_result, kill_elapsed = _run(kill_command)
        kill_ref = _command_ref(log_dir, "herdr-pane-close", kill_command, kill_result)
        artifact_refs["kill_pane"] = kill_ref
        kill_payload = _json_object_output(kill_result)
        kill_pass = kill_result.returncode == 0 and _json_path(kill_payload, ["result", "type"]) == "ok"
    else:
        kill_elapsed = None
        kill_ref = "not-run"
    operations.append(
        _operation(
            "kill_pane",
            "pass" if kill_pass else "blocked",
            command_ref=kill_ref,
            elapsed_ms=kill_elapsed,
            evidence_ref=kill_ref if kill_ref != "not-run" else None,
            failure_class=None if kill_pass else "unsupported-capability",
            diagnostic="pane close returned ok" if kill_pass else "pane close failed",
        )
    )

    if workspace_id is not None:
        workspace_close_command = [herdr, *scope_args, "workspace", "close", workspace_id]
        workspace_close_result, _ = _run(workspace_close_command)
        cleanup_refs["workspace_close"] = _command_ref(
            log_dir,
            "herdr-workspace-close",
            workspace_close_command,
            workspace_close_result,
        )
    if server_started_by_spike:
        server_stop_command = [herdr, *scope_args, "server", "stop"]
        server_stop_result, _ = _run(server_stop_command)
        cleanup_refs["server_stop"] = _command_ref(log_dir, "herdr-server-stop", server_stop_command, server_stop_result)

    restore_diagnostic = "server restart restore remains fail-closed until restart identity and preexisting-session isolation can be proven"
    operations.extend(
        _operation(
            operation,
            "blocked",
            command_ref="not-run",
            failure_class="unsupported-capability",
            diagnostic=restore_diagnostic,
        )
        for operation in ("detach_reattach", "server_restart_restore")
    )
    provider = {
        "provider_slug": None,
        "dry_run_kind": "provider_cli",
        "command": [],
        "pane_ref": None,
        "output_match": False,
        "exit_observed": False,
        "killed_by_spike": False,
        "treated_as_completion_authority": False,
        "public_provider_parity_claimed": False,
        "failure_class": "provider-dry-run-unavailable",
    }
    restore = {
        "detach_reattach_checked": False,
        "detach_process_continues": None,
        "server_restart_checked": False,
        "restart_isolation": {
            "server_ref_kind": "dedicated-disposable-server",
            "session_name": args.session,
            "socket_ref": args.isolated_socket_ref,
            "config_ref": args.isolated_config_ref,
            "server_identity_before": server_identity_before,
            "server_identity_after": None,
            "preexisting_sessions_before": [],
            "created_by_spike": True,
            "stop_command_ref": cleanup_refs.get("server_stop"),
            "cleanup_targets": cleanup_targets,
        },
        "restart_scope": "isolated-socket" if args.isolated_socket_ref else "dedicated-disposable-server",
        "server_identity": None,
        "preexisting_sessions_checked": False,
        "restart_authorized": False,
        "layout_restored": None,
        "output_history_restored": None,
        "agent_session_restored": None,
        "old_process_expected_to_survive": False,
        "diagnostic": restore_diagnostic,
    }
    evidence = _base_evidence(
        platform_gate_ref=platform_gate_ref,
        platform_payload=platform_payload,
        herdr_executable=herdr,
        operations=operations,
        provider_cli_dry_run=provider,
        fallback_terminal_smoke=None,
        restore=restore,
        verdict="blocked",
        failure_class="unsupported-capability",
        adapter_recommendation="needs-upstream-issue",
        residual_risks=[restore_diagnostic],
        artifact_refs=artifact_refs,
    )
    evidence["herdr"]["version"] = (version_result.stdout or version_result.stderr or "").strip() or None
    evidence["herdr"]["status"] = "available"
    validate_evidence(evidence)
    return evidence


def _isolated_scope_args(args: argparse.Namespace) -> list[str] | None:
    if not getattr(args, "isolation_created_by_spike", False):
        return None
    scope_args: list[str] = []
    if args.isolated_socket_ref:
        scope_args.extend([args.herdr_socket_arg, args.isolated_socket_ref])
    if args.isolated_config_ref:
        scope_args.extend([args.herdr_config_arg, args.isolated_config_ref])
    return scope_args or None


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise EvidenceError(message)


def validate_evidence(evidence: dict[str, Any]) -> None:
    _require(evidence.get("schema_version") == 1, "schema_version must be 1")
    _require(evidence.get("feature") == FEATURE, "feature mismatch")
    verdict = evidence.get("verdict")
    failure_class = evidence.get("failure_class")
    recommendation = evidence.get("adapter_recommendation")
    _require(verdict in {"pass", "partial", "blocked", "failed"}, "invalid verdict")
    _require(
        failure_class
        in {
            "none",
            "manual-host-missing",
            "platform-gate-blocked",
            "herdr-missing",
            "schema-mismatch",
            "unsupported-capability",
            "windows-beta-gap",
            "provider-dry-run-unavailable",
            "test-design-failure",
            "unknown",
        },
        "invalid failure_class",
    )
    _require(
        recommendation in {"continue", "continue-with-gaps", "stop", "needs-upstream-issue"},
        "invalid adapter_recommendation",
    )

    host = evidence.get("host")
    _require(isinstance(host, dict), "host must be object")
    if verdict != "blocked":
        _require(host.get("os_platform") == "win32", "non-blocked evidence requires win32 host")
        _require(host.get("cpu_arch") == "x64", "non-blocked evidence requires x64 host")
        _require(host.get("python_bitness") == "64bit", "non-blocked evidence requires 64-bit Python")
        _require(host.get("is_wsl") is False, "non-blocked evidence cannot be WSL")
        _require(bool(host.get("platform_gate_ref")), "non-blocked evidence requires platform_gate_ref")
        _require(host.get("platform_gate_supported") is True, "non-blocked evidence requires supported platform gate")
        _require(bool(host.get("platform_gate_host_label")), "non-blocked evidence requires platform gate host label")
        _require(_host_gate_mismatch_reason(host) is None, "non-blocked evidence requires current host to match platform gate")
    if verdict == "blocked":
        _require(failure_class != "none", "blocked evidence requires failure_class")
        _require(recommendation != "continue", "blocked evidence cannot recommend continue")

    operations = evidence.get("operations")
    _require(isinstance(operations, list), "operations must be list")
    core_operation_names = [
        op.get("operation") for op in operations if isinstance(op, dict) and op.get("operation") in CORE_OPERATIONS
    ]
    duplicate_operations = sorted({name for name in core_operation_names if core_operation_names.count(name) > 1})
    _require(
        not duplicate_operations,
        f"duplicate core operations: {', '.join(str(name) for name in duplicate_operations)}",
    )
    operation_by_name = {
        op.get("operation"): op for op in operations if isinstance(op, dict) and op.get("operation") in CORE_OPERATIONS
    }
    missing = [operation for operation in CORE_OPERATIONS if operation not in operation_by_name]
    _require(not missing, f"missing core operations: {', '.join(missing)}")
    non_pass_operations: list[str] = []
    for op in operation_by_name.values():
        _require(op.get("status") in {"pass", "partial", "blocked", "failed"}, "invalid operation status")
        if op.get("status") == "pass":
            _require(_trace_ref_exists(op.get("command_ref")), f"{op.get('operation')} pass requires command_ref")
            _require(_trace_ref_exists(op.get("evidence_ref")), f"{op.get('operation')} pass requires evidence_ref")
        if op.get("status") != "pass":
            _require(bool(op.get("failure_class")), f"{op.get('operation')} requires failure_class")
            non_pass_operations.append(str(op.get("operation")))

    provider = evidence.get("provider_cli_dry_run")
    _require(isinstance(provider, dict), "provider_cli_dry_run must be object")
    _require(provider.get("dry_run_kind") == "provider_cli", "provider dry run must use provider_cli kind")
    _require(provider.get("treated_as_completion_authority") is False, "provider dry run cannot be completion authority")
    _require(provider.get("public_provider_parity_claimed") is False, "provider dry run cannot claim public parity")

    fallback = evidence.get("fallback_terminal_smoke")
    if fallback is not None:
        _require(isinstance(fallback, dict), "fallback_terminal_smoke must be object")
        _require(fallback.get("dry_run_kind") == "fallback_terminal_smoke", "fallback kind mismatch")
        _require(fallback.get("public_provider_parity_claimed") is False, "fallback cannot claim provider parity")
        if not (provider.get("output_match") and (provider.get("exit_observed") or provider.get("killed_by_spike"))):
            _require(verdict != "pass", "fallback smoke alone cannot produce pass verdict")

    restore = evidence.get("restore")
    _require(isinstance(restore, dict), "restore must be object")
    isolation = restore.get("restart_isolation")
    _require(isinstance(isolation, dict), "restart_isolation must be object")
    if restore.get("restart_authorized") is True:
        _require(isolation.get("created_by_spike") is True, "authorized restart requires spike-created isolation")
        _require(
            restore.get("restart_scope") in {"dedicated-disposable-server", "isolated-socket"},
            "authorized restart requires dedicated or isolated scope",
        )
        _require(bool(isolation.get("session_name")), "authorized restart requires session_name")
        _require(
            bool(isolation.get("socket_ref")) or bool(isolation.get("config_ref")),
            "authorized restart requires isolated socket or config ref",
        )
        _require(bool(isolation.get("server_identity_before")), "authorized restart requires server_identity_before")
        _require(bool(isolation.get("server_identity_after")), "authorized restart requires server_identity_after")
        _require(restore.get("preexisting_sessions_checked") is True, "authorized restart requires preexisting session check")
        _require(_trace_ref_exists(isolation.get("stop_command_ref")), "authorized restart requires stop_command_ref")
    if restore.get("restart_scope") == "blocked-not-isolated":
        _require(restore.get("restart_authorized") is False, "blocked-not-isolated restart cannot be authorized")

    projection = evidence.get("capability_projection")
    _require(isinstance(projection, dict), "capability_projection must be object")
    blocking_gaps = projection.get("blocking_gaps")
    _require(isinstance(blocking_gaps, list), "blocking_gaps must be list")
    _require(
        sorted(str(gap) for gap in blocking_gaps) == sorted(non_pass_operations),
        "blocking_gaps must match non-pass operations",
    )

    provider_passed = provider.get("output_match") is True and (
        provider.get("exit_observed") is True or provider.get("killed_by_spike") is True
    )
    core_operations_passed = all(op.get("status") == "pass" for op in operation_by_name.values())
    restart_ready = (
        isolation.get("created_by_spike") is True
        and restore.get("restart_scope") != "blocked-not-isolated"
        and restore.get("restart_authorized") is True
        and restore.get("server_restart_checked") is True
        and bool(isolation.get("socket_ref") or isolation.get("config_ref"))
        and bool(isolation.get("server_identity_before"))
        and bool(isolation.get("server_identity_after"))
        and restore.get("preexisting_sessions_checked") is True
        and _trace_ref_exists(isolation.get("stop_command_ref"))
    )
    host_ready = (
        host.get("os_platform") == "win32"
        and host.get("cpu_arch") == "x64"
        and host.get("python_bitness") == "64bit"
        and host.get("is_wsl") is False
        and bool(host.get("platform_gate_ref"))
        and host.get("platform_gate_supported") is True
    )
    may_continue = (
        verdict == "pass"
        and failure_class == "none"
        and host_ready
        and core_operations_passed
        and restart_ready
        and provider_passed
        and not blocking_gaps
    )
    if verdict == "pass":
        _require(_required_artifact_refs_present(evidence), "pass verdict requires traceable artifact refs")
        _require(recommendation == "continue", "pass verdict requires continue recommendation")
        _require(may_continue, "pass verdict requires full passing truth table")
    if failure_class == "none":
        _require(verdict == "pass", "failure_class none requires pass verdict")
        _require(core_operations_passed, "failure_class none requires all core operations pass")
        _require(not blocking_gaps, "failure_class none requires no blocking gaps")
    if recommendation == "continue":
        _require(may_continue, "recommendation continue requires full passing truth table")


def _trace_ref_exists(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    ref = value.strip()
    if not ref or ref == "not-run":
        return False
    if "://" in ref:
        return ref.startswith(("https://", "http://"))
    return Path(ref).exists()


def _required_artifact_refs_present(evidence: dict[str, Any]) -> bool:
    refs = evidence.get("artifact_refs")
    if not isinstance(refs, dict):
        return False
    required = ("platform_gate", "version", "schema", "status")
    for name in required:
        if not _trace_ref_exists(refs.get(name)):
            return False
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Herdr backend contract spike.")
    parser.add_argument("--platform-gate-ref", required=True)
    parser.add_argument("--session", required=True)
    parser.add_argument("--isolated-server", action="store_true")
    parser.add_argument("--isolated-socket-ref", default="")
    parser.add_argument("--isolated-config-ref", default="")
    parser.add_argument("--isolation-created-by-spike", action="store_true")
    parser.add_argument("--herdr-socket-arg", default="--socket")
    parser.add_argument("--herdr-config-arg", default="--config")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    evidence = run_spike(args)
    validate_evidence(evidence)
    out.write_text(json.dumps(evidence, indent=2, sort_keys=True), encoding="utf-8")
    print(f"wrote {out.as_posix()} verdict={evidence['verdict']} failure_class={evidence['failure_class']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
