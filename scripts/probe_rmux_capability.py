#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import time
from typing import Any


LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from provider_pane_status.claude_pane import (  # noqa: E402
    normalize_screen as normalize_claude_screen,
    parse_claude_pane_status,
)
from provider_pane_status.codex_pane import (  # noqa: E402
    normalize_screen as normalize_codex_screen,
    parse_codex_pane_status,
)
from terminal_runtime.rmux_runner import client_tail_nonempty_lines, rmux_command_name  # noqa: E402


TOKEN_RE = re.compile(r"(sk-[A-Za-z0-9_-]{6,}|sess-[A-Za-z0-9_-]{6,}|Bearer\s+[A-Za-z0-9._-]+)")
SECRET_RE = re.compile(
    r"(?i)([\"']?\b(api[_-]?key|token|secret|password)[\"']?\s*[:=]\s*)([\"']?)([^\"'\s,}]+)([\"']?)"
)

COMMAND_CATALOG: dict[str, dict[str, str | bool]] = {
    "start-server": {"required": True, "degrade_impact": "core-lifecycle", "consequence": "无法建立 mux server"},
    "new-session": {"required": True, "degrade_impact": "core-lifecycle", "consequence": "无法创建项目 namespace"},
    "attach-session": {"required": True, "degrade_impact": "core-lifecycle", "consequence": "无法重新附着 UI"},
    "has-session": {"required": True, "degrade_impact": "core-lifecycle", "consequence": "无法判断 namespace 是否存在"},
    "kill-session": {"required": True, "degrade_impact": "core-lifecycle", "consequence": "无法清理项目 namespace"},
    "kill-server": {"required": True, "degrade_impact": "diagnostic", "consequence": "无法验证 server 级清理"},
    "list-windows": {"required": True, "degrade_impact": "core-lifecycle", "consequence": "无法投影窗口布局"},
    "new-window": {"required": True, "degrade_impact": "core-lifecycle", "consequence": "无法创建 agent window"},
    "rename-window": {"required": True, "degrade_impact": "core-lifecycle", "consequence": "无法维护 window identity"},
    "select-window": {"required": True, "degrade_impact": "degradable-ui", "consequence": "无法选择目标 window"},
    "kill-window": {"required": True, "degrade_impact": "core-lifecycle", "consequence": "无法清理 window"},
    "move-pane": {"required": True, "degrade_impact": "core-lifecycle", "consequence": "无法移动 patch agent pane"},
    "resize-pane": {"required": True, "degrade_impact": "degradable-ui", "consequence": "无法重排 pane geometry"},
    "select-layout": {"required": True, "degrade_impact": "degradable-ui", "consequence": "无法应用 layout policy"},
    "swap-pane": {"required": True, "degrade_impact": "core-lifecycle", "consequence": "无法重排 agent pane"},
    "split-window": {"required": True, "degrade_impact": "core-lifecycle", "consequence": "无法创建 pane"},
    "list-panes": {"required": True, "degrade_impact": "core-lifecycle", "consequence": "无法发现 pane identity"},
    "display-message": {"required": True, "degrade_impact": "diagnostic", "consequence": "无法读取格式化诊断"},
    "set-option": {"required": True, "degrade_impact": "diagnostic", "consequence": "无法写 session option evidence"},
    "set-window-option": {"required": True, "degrade_impact": "diagnostic", "consequence": "无法写 window option evidence"},
    "set-hook": {"required": True, "degrade_impact": "diagnostic", "consequence": "无法安装 lifecycle hook"},
    "bind-key": {"required": False, "degrade_impact": "degradable-ui", "consequence": "UI key binding 可能不可用"},
    "send-keys": {"required": True, "degrade_impact": "core-io", "consequence": "无法向 provider pane 发送输入"},
    "load-buffer": {"required": True, "degrade_impact": "core-io", "consequence": "大文本 paste 无可靠输入路径"},
    "paste-buffer": {"required": True, "degrade_impact": "core-io", "consequence": "buffer paste 不可用"},
    "delete-buffer": {"required": True, "degrade_impact": "core-io", "consequence": "buffer cleanup 不可用"},
    "capture-pane": {"required": True, "degrade_impact": "parser-fidelity", "consequence": "pane 状态与 ask completion evidence 会漂移"},
    "pipe-pane": {"required": True, "degrade_impact": "core-io", "consequence": "pane 日志绑定不可用"},
    "respawn-pane": {"required": True, "degrade_impact": "core-lifecycle", "consequence": "pane recovery 不可用"},
    "list-clients": {"required": True, "degrade_impact": "diagnostic", "consequence": "无法诊断 attach client"},
    "refresh-client": {"required": True, "degrade_impact": "degradable-ui", "consequence": "UI refresh 能力不可用"},
}
COMMAND_ORDER = [
    "start-server",
    "new-session",
    "has-session",
    "list-windows",
    "new-window",
    "rename-window",
    "select-window",
    "split-window",
    "list-panes",
    "display-message",
    "set-option",
    "set-window-option",
    "set-hook",
    "bind-key",
    "send-keys",
    "load-buffer",
    "paste-buffer",
    "delete-buffer",
    "capture-pane",
    "pipe-pane",
    "respawn-pane",
    "resize-pane",
    "select-layout",
    "swap-pane",
    "move-pane",
    "attach-session",
    "refresh-client",
    "list-clients",
    "kill-window",
    "kill-session",
    "kill-server",
]

SEMANTIC_CATALOG: dict[str, dict[str, str | bool]] = {
    "session_survival": {"required": True, "degrade_impact": "core-lifecycle", "consequence": "关闭终端后 namespace 可能丢失"},
    "namespace_isolation": {"required": True, "degrade_impact": "core-lifecycle", "consequence": "多项目可能互相污染"},
    "attach_reattach": {"required": True, "degrade_impact": "core-lifecycle", "consequence": "用户无法恢复 UI"},
    "window_policy": {"required": True, "degrade_impact": "core-lifecycle", "consequence": "agent window policy 不可靠"},
    "layout_reflow": {"required": True, "degrade_impact": "degradable-ui", "consequence": "layout/reflow/reload 不可靠"},
    "pane_id_stability": {"required": True, "degrade_impact": "core-lifecycle", "consequence": "runtime authority 无法稳定定位 pane"},
    "user_options_title": {"required": True, "degrade_impact": "diagnostic", "consequence": "pane identity marker 不可靠"},
    "capture_last_n_lines": {"required": True, "degrade_impact": "parser-fidelity", "consequence": "recent tail 证据可能漂移"},
    "capture_format_fidelity_for_provider_completion": {"required": True, "degrade_impact": "parser-fidelity", "consequence": "provider pane status 可能静默误判"},
    "buffer_paste": {"required": True, "degrade_impact": "core-io", "consequence": "大文本输入不可用"},
    "ctrl_c_ctrl_d": {"required": True, "degrade_impact": "core-io", "consequence": "interrupt / EOF 语义不可控"},
    "pane_death": {"required": True, "degrade_impact": "core-lifecycle", "consequence": "pane death 无法诊断"},
    "kill_session_cleanup": {"required": True, "degrade_impact": "core-lifecycle", "consequence": "ccb kill 清理不完整"},
    "daemon_crash_cleanup_evidence": {"required": False, "degrade_impact": "diagnostic", "consequence": "daemon ownership 后续决策证据不足"},
    "provider_process_distinction_workaround_evidence": {"required": True, "degrade_impact": "core-lifecycle", "consequence": "pane alive 与 provider healthy 可能混淆"},
}


@dataclass(frozen=True)
class CommandResult:
    args: list[str]
    returncode: int
    stdout: str
    stderr: str
    timeout: float
    stdout_bytes: bytes = b""
    stderr_bytes: bytes = b""


class SubprocessRunner:
    def run(self, args: list[str], *, timeout: float = 5.0) -> CommandResult:
        stdio_mode = _rmux_probe_stdio_mode(args)
        if stdio_mode != "pipe":
            return self._run_without_pipe_capture(args, timeout=timeout, stdio_mode=stdio_mode)
        process: subprocess.Popen[bytes] | None = None
        try:
            process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout_bytes, stderr_bytes = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            self._terminate_process_tree(process)
            stdout_bytes = exc.stdout or b""
            stderr_bytes = exc.stderr or b"timeout"
            if isinstance(stdout_bytes, str):
                stdout_bytes = stdout_bytes.encode("utf-8", errors="replace")
            if isinstance(stderr_bytes, str):
                stderr_bytes = stderr_bytes.encode("utf-8", errors="replace")
            return CommandResult(
                args,
                124,
                stdout_bytes.decode("utf-8", errors="replace"),
                stderr_bytes.decode("utf-8", errors="replace"),
                timeout,
                stdout_bytes,
                stderr_bytes,
            )
        except OSError as exc:
            return CommandResult(args, 127, "", str(exc), timeout)
        return CommandResult(
            args,
            process.returncode if process is not None else 127,
            stdout_bytes.decode("utf-8", errors="replace"),
            stderr_bytes.decode("utf-8", errors="replace"),
            timeout,
            stdout_bytes,
            stderr_bytes,
        )

    def _run_without_pipe_capture(self, args: list[str], *, timeout: float, stdio_mode: str) -> CommandResult:
        kwargs: dict[str, object] = {"check": False, "timeout": timeout}
        if stdio_mode == "devnull":
            kwargs["stdout"] = subprocess.DEVNULL
            kwargs["stderr"] = subprocess.DEVNULL
        try:
            cp = subprocess.run(args, **kwargs)
        except subprocess.TimeoutExpired as exc:
            return CommandResult(
                args,
                124,
                "",
                f"timeout after {timeout}s",
                timeout,
            )
        except OSError as exc:
            return CommandResult(args, 127, "", str(exc), timeout)
        return CommandResult(args, int(getattr(cp, "returncode", 1) or 0), "", "", timeout)

    @staticmethod
    def _terminate_process_tree(process: subprocess.Popen[bytes] | None) -> None:
        if process is None or process.poll() is not None:
            return
        if platform.system().lower() == "windows":
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            return
        process.kill()


def _rmux_probe_stdio_mode(args: list[str]) -> str:
    command = rmux_command_name(args)
    if command in {"attach", "attach-session"}:
        return "inherit"
    if platform.system().lower() == "windows" and command in {"start-server", "new-session"}:
        return "devnull"
    return "pipe"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def redact_text(text: str) -> str:
    value = TOKEN_RE.sub("[REDACTED]", text or "")
    return SECRET_RE.sub(lambda match: f"{match.group(1)}{match.group(3)}[REDACTED]{match.group(5)}", value)


def command_name(args: list[str]) -> str:
    catalog = set(COMMAND_CATALOG)
    for item in args:
        if item in catalog:
            return item
    return Path(args[0]).name if args else "unknown"


def backend_impl_name(rmux_bin: str) -> str:
    name = Path(str(rmux_bin or "rmux")).stem.strip().lower()
    return name or "rmux"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def _write_command_artifact(
    run_dir: Path,
    result: CommandResult,
    *,
    kind: str,
    probe: str,
    status: str | None = None,
    notes: str = "",
) -> Path:
    artifact_path = run_dir / "artifacts" / kind / f"{probe}.json"
    payload: dict[str, Any] = {
        "args": result.args,
        "returncode": result.returncode,
        "stdout_raw_sha256": hashlib.sha256(result.stdout_bytes or result.stdout.encode("utf-8")).hexdigest(),
        "stdout_raw_size": len(result.stdout_bytes or result.stdout.encode("utf-8")),
        "stdout": redact_text(result.stdout),
        "stderr": redact_text(result.stderr),
        "timeout": result.timeout,
    }
    if status is not None:
        payload["classification"] = status
    if notes:
        payload["notes"] = notes
    _write_json(artifact_path, payload)
    return artifact_path


def _artifact_entry(run_dir: Path, path: Path, *, kind: str, probe: str, redacted: bool = True) -> dict[str, Any]:
    rel_path = path.relative_to(run_dir).as_posix()
    return {
        "path": rel_path,
        "kind": kind,
        "probe": probe,
        "name": probe,
        "redacted": redacted,
        "size_bytes": path.stat().st_size,
        "sha256": _sha256(path),
    }


def _command_args(rmux_bin: str, namespace: str, session: str, name: str, work_dir: Path) -> list[str]:
    base = [rmux_bin, "-L", namespace]
    target = ["-t", session]
    pane = ["-t", f"{session}:0.0"]
    if name == "start-server":
        return [*base, "start-server"]
    if name == "new-session":
        return [*base, "new-session", "-d", "-s", session]
    if name == "attach-session":
        return [*base, "attach-session", "-t", session, "-d", "-E"]
    if name == "has-session":
        return [*base, "has-session", *target]
    if name == "kill-session":
        return [*base, "kill-session", *target]
    if name == "kill-server":
        return [*base, "kill-server"]
    if name == "list-windows":
        return [*base, "list-windows", *target]
    if name == "new-window":
        return [*base, "new-window", "-d", *target, "-n", "probe-extra"]
    if name == "rename-window":
        return [*base, "rename-window", "-t", f"{session}:0", "probe-main"]
    if name == "select-window":
        return [*base, "select-window", "-t", f"{session}:0"]
    if name == "kill-window":
        return [*base, "kill-window", "-t", f"{session}:probe-extra"]
    if name == "move-pane":
        return [*base, "move-pane", "-s", f"{session}:0.0", "-t", f"{session}:probe-extra"]
    if name == "resize-pane":
        return [*base, "resize-pane", *pane, "-Z"]
    if name == "select-layout":
        return [*base, "select-layout", *target, "even-horizontal"]
    if name == "swap-pane":
        return [*base, "swap-pane", "-s", f"{session}:0.0", "-t", f"{session}:0.1"]
    if name == "split-window":
        return [*base, "split-window", "-d", *pane]
    if name == "list-panes":
        return [*base, "list-panes", *target, "-F", "#{pane_id}"]
    if name == "display-message":
        return [*base, "display-message", "-p", *target, "#{session_name}"]
    if name == "set-option":
        return [*base, "set-option", *target, "@ccb_probe", "1"]
    if name == "set-window-option":
        return [*base, "set-window-option", "-t", f"{session}:0", "@ccb_probe_window", "1"]
    if name == "set-hook":
        return [*base, "set-hook", *target, "pane-died", "display-message pane-died"]
    if name == "bind-key":
        return [*base, "bind-key", "C-b", "display-message", "probe"]
    if name == "send-keys":
        return [*base, "send-keys", *pane, "echo ccb-rmux-probe", "Enter"]
    if name == "load-buffer":
        buffer_file = work_dir / "buffer.txt"
        buffer_file.write_text("ccb-rmux-probe\n", encoding="utf-8")
        return [*base, "load-buffer", str(buffer_file)]
    if name == "paste-buffer":
        return [*base, "paste-buffer", *pane]
    if name == "delete-buffer":
        return [*base, "delete-buffer"]
    if name == "capture-pane":
        return [*base, "capture-pane", *pane, "-p", "-S", "-20"]
    if name == "pipe-pane":
        return [*base, "pipe-pane", *pane]
    if name == "respawn-pane":
        return [*base, "respawn-pane", "-k", *pane]
    if name == "list-clients":
        return [*base, "list-clients", *target]
    if name == "refresh-client":
        return [*base, "refresh-client", "-S", "-t", session]
    return [*base, name]


def _command_status_and_notes(name: str, result: CommandResult) -> tuple[str, str]:
    if result.returncode == 0:
        return "supported", ""
    scenario_sensitive = {"attach-session", "refresh-client", "move-pane", "swap-pane", "kill-server"}
    combined = f"{result.stdout}\n{result.stderr}".lower()
    attach_started_tui = name == "attach-session" and result.returncode == 124 and any(
        marker in result.stdout for marker in ("\x1b[?1049h", "\x1b[?2004h", "\x1b]0;", "probe-main", "probe-extra")
    )
    if name in scenario_sensitive and any(
        marker in combined
        for marker in (
            "no current client",
            "not a client",
            "can't find client",
            "ambiguous",
            "same pane",
            "no such file or directory",
            "timeout",
        )
    ):
        return "partial", "scenario-invalid: command requires live client/server or distinct pane/window context; not classified as command missing"
    if attach_started_tui:
        return "partial", "scenario-invalid: attach opened an interactive TUI and hit the non-interactive probe timeout"
    return "unsupported", ""


def _result_record(
    *,
    catalog: dict[str, str | bool],
    status: str,
    evidence: str,
    workaround: dict[str, Any] | None = None,
    returncode: int | None = None,
    notes: str = "",
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "required": bool(catalog["required"]),
        "status": status,
        "evidence": evidence,
        "workaround": workaround,
        "degrade_impact": str(catalog["degrade_impact"]),
        "consequence": str(catalog["consequence"]),
        "notes": notes,
    }
    if returncode is not None:
        record["returncode"] = returncode
    return record


def _blocking_gaps(commands: dict[str, Any], semantics: dict[str, Any]) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    for section_name, section in (("command", commands), ("semantic", semantics)):
        for name, result in section.items():
            if not result.get("required"):
                continue
            status = result.get("status")
            workaround = result.get("workaround")
            accepted = bool(workaround and workaround.get("accepted") is True)
            if status in {"unsupported", "partial", "workaround"} and not accepted:
                gaps.append(
                    {
                        "kind": section_name,
                        "name": name,
                        "reason": f"required {status} without accepted workaround",
                        "required": True,
                        "status": status,
                        "evidence": result.get("evidence"),
                        "degrade_impact": result.get("degrade_impact"),
                        "consequence": result.get("consequence"),
                    }
                )
    return gaps


def _read_optional_json(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _accepted_live_workaround(
    name: str,
    *,
    live_attach_evidence: dict[str, Any] | None,
    live_attach_evidence_path: Path | None,
    live_client_evidence: dict[str, Any] | None,
    live_client_evidence_path: Path | None,
) -> dict[str, Any] | None:
    if name in {"attach-session", "attach_reattach"} and live_attach_evidence and live_attach_evidence.get("verdict") == "pass":
        return {
            "id": "live-foreground-attach-evidence",
            "description": "non-interactive probe cannot own a TTY; a separate live foreground attach run observed an attached client and clean detach",
            "evidence": str(live_attach_evidence_path) if live_attach_evidence_path is not None else None,
            "accepted": True,
        }
    if name == "refresh-client" and live_client_evidence and live_client_evidence.get("refresh_client_returncode") == 0:
        return {
            "id": "live-client-refresh-evidence",
            "description": "refresh-client requires a live attached client; separate live-client evidence verified refresh-client against the observed client id",
            "evidence": str(live_client_evidence_path) if live_client_evidence_path is not None else None,
            "accepted": True,
        }
    if name == "kill-server" and live_client_evidence and live_client_evidence.get("kill_server_returncode") == 0:
        return {
            "id": "live-server-kill-evidence",
            "description": "the main non-interactive probe runs kill-server after kill-session cleanup; separate live-server evidence verified kill-server while the server existed",
            "evidence": str(live_client_evidence_path) if live_client_evidence_path is not None else None,
            "accepted": True,
        }
    return None


def _pane_ids(result: CommandResult | None) -> list[str]:
    if result is None or result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip().startswith("%")]


def _capture_fidelity_evidence(path: Path, raw_results: dict[str, CommandResult]) -> tuple[dict[str, Any], str, dict[str, Any] | None, str]:
    capture_result = raw_results.get("capture-pane")
    fixture_result = raw_results.get("verify.capture-fidelity")
    tail_result = raw_results.get("verify.capture-last-n")
    cases = [
        {
            "dimension": "trailing_whitespace",
            "codex_raw": "• Working (1s • esc to interrupt)   \n",
            "claude_raw": "✶ Thinking (1s, 1 token)   \n",
        },
        {
            "dimension": "csi",
            "codex_raw": "\x1b[31m• Working (1s • esc to interrupt)\x1b[0m\n",
            "claude_raw": "\x1b[31m✶ Thinking (1s, 1 token)\x1b[0m\n",
        },
        {
            "dimension": "osc",
            "codex_raw": "\x1b]0;title\x07• Working (1s • esc to interrupt)\n",
            "claude_raw": "\x1b]0;title\x07✶ Thinking (1s, 1 token)\n",
        },
        {
            "dimension": "wrapping",
            "codex_raw": "• Working (1s • esc to interrupt)\nwrapped-body-without-logical-line-rebuild\n",
            "claude_raw": "✶ Thinking (1s, 1 token)\nwrapped-body-without-logical-line-rebuild\n",
        },
        {
            "dimension": "wide_char",
            "codex_raw": "• Working (1s • esc to interrupt)\n宽字符列宽需要 Rmux/tmux 输出平价证明\n",
            "claude_raw": "✶ Thinking (1s, 1 token)\n宽字符列宽需要 Rmux/tmux 输出平价证明\n",
        },
        {
            "dimension": "last_n_tail",
            "codex_raw": "old\n• Working (1s • esc to interrupt)\n",
            "claude_raw": "old\n✶ Thinking (1s, 1 token)\n",
        },
    ]
    for case in cases:
        codex_raw = str(case["codex_raw"])
        claude_raw = str(case["claude_raw"])
        codex_status = parse_codex_pane_status(codex_raw)
        claude_status = parse_claude_pane_status(claude_raw)
        case["absorbed"] = codex_status.state in {"working", "tool_running", "completed"} and claude_status.state in {
            "working",
            "tool_running",
            "terminal_summary",
        }
        case["consumer_strip"] = {
            "codex_normalized": normalize_codex_screen(codex_raw),
            "claude_normalized": normalize_claude_screen(claude_raw),
        }
        case["direct_stdout"] = {
            "codex_state": codex_status.state,
            "codex_reason": codex_status.reason,
            "claude_state": claude_status.state,
            "claude_reason": claude_status.reason,
        }

    def capture_observation(result: CommandResult | None) -> dict[str, Any]:
        if result is None or result.returncode != 0:
            return {
                "available": False,
                "reason": "capture-pane did not produce successful real Rmux stdout in this run",
            }
        decoded = redact_text(result.stdout)
        return {
            "available": True,
            "returncode": result.returncode,
            "raw_bytes_sha256": hashlib.sha256(result.stdout_bytes or result.stdout.encode("utf-8")).hexdigest(),
            "raw_bytes_size": len(result.stdout_bytes or result.stdout.encode("utf-8")),
            "decoded_text": decoded,
            "consumer_strip": {
                "codex_normalized": normalize_codex_screen(decoded),
                "claude_normalized": normalize_claude_screen(decoded),
            },
            "direct_stdout": {
                "codex_state": parse_codex_pane_status(decoded).state,
                "codex_reason": parse_codex_pane_status(decoded).reason,
                "claude_state": parse_claude_pane_status(decoded).state,
                "claude_reason": parse_claude_pane_status(decoded).reason,
            },
            "observed_dimensions": {
                "contains_csi": "\x1b[" in result.stdout,
                "contains_osc": "\x1b]" in result.stdout,
                "line_count": len(result.stdout.splitlines()),
            },
        }

    fixture_text = fixture_result.stdout if fixture_result and fixture_result.returncode == 0 else ""
    tail_text = tail_result.stdout if tail_result and tail_result.returncode == 0 else ""
    client_tail_text = client_tail_nonempty_lines(tail_text, 2)
    fixture_lines = fixture_text.splitlines()
    absorbed_dimensions = {str(case["dimension"]): bool(case["absorbed"]) for case in cases}
    has_fixture_output_line = any(line.startswith("CCB_RMUX_TRAILING") for line in fixture_lines)
    has_trailing_output_line = any(line == "CCB_RMUX_TRAILING   " for line in fixture_lines)
    has_wrapped_marker = "CCB_RMUX_WRAP_" in fixture_text and any(
        line.startswith(("P_", "pqrstuvwxyz", "defghijklmnopqrstuvwxyz")) for line in fixture_lines
    )
    has_osc_payload_effect = "CCB_RMUX_OSC_AFTER" in fixture_text
    real_dimension_checks = {
        "trailing_whitespace": has_fixture_output_line and absorbed_dimensions.get("trailing_whitespace", False),
        "osc": (("\x1b]" in fixture_text) or has_osc_payload_effect) and absorbed_dimensions.get("osc", False),
        "wrapping": has_wrapped_marker and absorbed_dimensions.get("wrapping", False),
        "wide_char": "CCB_RMUX_WIDE_宽字符" in fixture_text,
        "last_n_tail": "CCB_RMUX_LASTN" in client_tail_text and "CCB_RMUX_TRAILING" not in client_tail_text,
    }

    if capture_result is None or capture_result.returncode != 0:
        status = "unsupported"
        notes = "real Rmux capture did not succeed"
        workaround = None
    elif all(real_dimension_checks.values()):
        status = "supported"
        notes = "real Rmux capture covered every parser fidelity dimension"
        workaround = None
    else:
        status = "partial"
        notes = "real Rmux capture succeeded but one or more parser fidelity dimensions lack real evidence"
        missing = [name for name, passed in real_dimension_checks.items() if not passed]
        workaround = {
            "id": "parser-normalization-boundary",
            "description": "real Rmux capture evidence is incomplete for parser fidelity dimensions",
            "evidence": path.relative_to(path.parents[2]).as_posix(),
            "accepted": False,
            "missing_real_dimensions": missing,
        }

    payload = {
        "parser_paths": ["consumer_strip", "direct_stdout"],
        "providers": ["codex", "claude"],
        "rmux_capture_observation": capture_observation(capture_result),
        "rmux_capture_fixture_observation": capture_observation(fixture_result),
        "rmux_last_n_observation": capture_observation(tail_result),
        "rmux_client_tail_observation": {
            "lines": 2,
            "decoded_text": client_tail_text,
            "strategy": "backend client-side tail of non-empty capture lines",
        },
        "real_dimension_checks": real_dimension_checks,
        "real_dimension_observations": {
            "trailing_whitespace_preserved": has_trailing_output_line,
            "trailing_whitespace_marker_visible": has_fixture_output_line,
            "osc_sequence_preserved": "\x1b]" in fixture_text,
            "osc_payload_visible_after_terminal_handling": has_osc_payload_effect,
            "wrapped_marker_observed_as_physical_rows": has_wrapped_marker,
        },
        "normalization_responsibility": {
            "trailing_whitespace": "parser normalize_screen strips line tails",
            "csi": "current strip_ansi handles CSI sequences",
            "osc": "shared terminal sequence stripping removes OSC/non-CSI title/control sequences before parsing",
            "wrapping": "rmux exposes physical wrapped rows; provider parser only treats explicit status-shaped rows as authority",
            "wide_char": "current parser does not correct display width",
            "last_n_tail": "must be proven by rmux/tmux capture tail equivalence",
        },
        "cases": cases,
    }
    _write_json(path, payload)
    return payload, status, workaround, notes


def _assert_semantic(name: str, command_results: dict[str, Any], raw_results: dict[str, CommandResult]) -> tuple[str, list[dict[str, Any]], str]:
    def supported(command: str) -> bool:
        return command_results.get(command, {}).get("status") == "supported"

    def output(command: str) -> str:
        return raw_results.get(command, CommandResult([], 1, "", "", 0)).stdout

    def passed_assertion(check_name: str, passed: bool, *, kind: str = "semantic") -> dict[str, Any]:
        return {"name": check_name, "passed": passed, "kind": kind}

    initial_panes = set(_pane_ids(raw_results.get("list-panes")))
    verify_panes = set(_pane_ids(raw_results.get("verify.list-panes-after-layout")))
    capture_text = output("capture-pane")
    fixture_capture_text = output("verify.capture-fidelity")
    buffer_capture_text = output("verify.buffer-paste-capture")
    control_capture_text = output("verify.ctrl-c-ctrl-d-capture")
    namespace_default = raw_results.get("verify.namespace-default-has-session")
    attach_result = raw_results.get("attach-session")
    attach_started_tui = bool(
        attach_result
        and attach_result.returncode == 124
        and any(marker in attach_result.stdout for marker in ("\x1b[?1049h", "\x1b[?2004h", "\x1b]0;", "probe-main", "probe-extra"))
    )

    checks_by_name: dict[str, list[dict[str, Any]]] = {
        "session_survival": [
            passed_assertion("new-session returned success", supported("new-session"), kind="prerequisite"),
            passed_assertion("has-session confirmed target session", supported("has-session"), kind="prerequisite"),
            passed_assertion("display-message read back the probe session name", output("display-message").strip() == "ccb-rmux-probe"),
        ],
        "namespace_isolation": [
            passed_assertion("probe namespace session exists inside the explicit rmux namespace", supported("has-session"), kind="prerequisite"),
            passed_assertion(
                "same session is not visible from rmux default namespace",
                namespace_default is not None and namespace_default.returncode != 0,
            ),
        ],
        "attach_reattach": [
            passed_assertion("attach-session opened an interactive TUI", attach_started_tui),
            passed_assertion("attach-session can complete in this non-interactive probe", supported("attach-session")),
        ],
        "window_policy": [
            passed_assertion("list-windows succeeded", supported("list-windows"), kind="prerequisite"),
            passed_assertion("new-window succeeded", supported("new-window"), kind="prerequisite"),
            passed_assertion("rename-window succeeded", supported("rename-window"), kind="prerequisite"),
            passed_assertion("select-window succeeded", supported("select-window"), kind="prerequisite"),
            passed_assertion("window listing observed renamed probe windows", "probe-main" in output("verify.list-windows-after-policy")),
        ],
        "layout_reflow": [
            passed_assertion("resize-pane succeeded", supported("resize-pane"), kind="prerequisite"),
            passed_assertion("select-layout succeeded", supported("select-layout"), kind="prerequisite"),
            passed_assertion("swap-pane succeeded with distinct pane targets", supported("swap-pane"), kind="prerequisite"),
            passed_assertion("move-pane succeeded with distinct window target", supported("move-pane"), kind="prerequisite"),
            passed_assertion("pane identity remained discoverable after layout operations", bool(initial_panes & verify_panes)),
        ],
        "pane_id_stability": [
            passed_assertion("list-panes succeeded", supported("list-panes"), kind="prerequisite"),
            passed_assertion("initial list-panes returned pane identity", bool(initial_panes)),
            passed_assertion("follow-up list-panes preserved at least one pane identity", bool(initial_panes & verify_panes)),
        ],
        "user_options_title": [
            passed_assertion("set-option succeeded", supported("set-option"), kind="prerequisite"),
            passed_assertion("set-window-option succeeded", supported("set-window-option"), kind="prerequisite"),
            passed_assertion("rename-window succeeded", supported("rename-window"), kind="prerequisite"),
            passed_assertion("window title evidence contains probe-main", "probe-main" in output("verify.list-windows-after-policy")),
        ],
        "capture_last_n_lines": [
            passed_assertion("capture-pane succeeded", supported("capture-pane"), kind="prerequisite"),
            passed_assertion("capture-pane produced stdout", bool(capture_text)),
            passed_assertion(
                "backend client-tail contains the tail marker without the earlier marker",
                "CCB_RMUX_LASTN" in client_tail_nonempty_lines(output("verify.capture-last-n"), 2)
                and "CCB_RMUX_TRAILING" not in client_tail_nonempty_lines(output("verify.capture-last-n"), 2),
            ),
        ],
        "buffer_paste": [
            passed_assertion("load-buffer succeeded", supported("load-buffer"), kind="prerequisite"),
            passed_assertion("paste-buffer succeeded", supported("paste-buffer"), kind="prerequisite"),
            passed_assertion("delete-buffer succeeded", supported("delete-buffer"), kind="prerequisite"),
            passed_assertion("capture contains the pasted probe marker", "CCB_RMUX_BUFFER_PASTE_OK" in buffer_capture_text),
        ],
        "ctrl_c_ctrl_d": [
            passed_assertion("send-keys accepted input path", supported("send-keys"), kind="prerequisite"),
            passed_assertion("probe captures text sent through send-keys", "CCB_RMUX_CONTROL_AFTER_INTERRUPT" in control_capture_text),
            passed_assertion("logical EOF uses C-z Enter and returns control", "CCB_RMUX_EOF_DONE" in control_capture_text),
            passed_assertion("Ctrl-C interrupt returns control to shell", "CCB_RMUX_CONTROL_AFTER_INTERRUPT" in control_capture_text),
        ],
        "pane_death": [
            passed_assertion("respawn-pane succeeded", supported("respawn-pane"), kind="prerequisite"),
            passed_assertion("kill-window cleanup command succeeded", supported("kill-window"), kind="prerequisite"),
            passed_assertion("pane identity remains observable after respawn/cleanup path", bool(verify_panes)),
        ],
        "kill_session_cleanup": [passed_assertion("kill-session cleanup succeeded", supported("kill-session"))],
        "daemon_crash_cleanup_evidence": [
            passed_assertion("start-server evidence recorded", supported("start-server"), kind="prerequisite"),
            passed_assertion("kill-server evidence recorded", supported("kill-server"), kind="prerequisite"),
        ],
        "provider_process_distinction_workaround_evidence": [
            passed_assertion("list-panes returned pane identity", bool(initial_panes)),
            passed_assertion("capture-pane produced pane text", bool(capture_text or fixture_capture_text)),
        ],
    }
    checks = checks_by_name.get(name, [])
    semantic_checks = [check for check in checks if check.get("kind") != "prerequisite"]
    if checks and semantic_checks and all(check["passed"] for check in checks):
        return "supported", checks, ""
    if any(check["passed"] for check in checks):
        return "partial", checks, "one or more scenario assertions failed despite at least one prerequisite passing"
    return "unsupported", checks, "scenario assertions failed"


def _derive_semantics(
    command_results: dict[str, Any],
    raw_results: dict[str, CommandResult],
    run_dir: Path,
    artifact_index: list[dict[str, Any]],
    *,
    live_attach_evidence: dict[str, Any] | None = None,
    live_attach_evidence_path: Path | None = None,
    live_client_evidence: dict[str, Any] | None = None,
    live_client_evidence_path: Path | None = None,
) -> dict[str, Any]:
    semantics: dict[str, Any] = {}
    dependencies = {
        "session_survival": ["new-session", "has-session"],
        "namespace_isolation": ["new-session", "has-session"],
        "attach_reattach": ["attach-session"],
        "window_policy": ["list-windows", "new-window", "rename-window", "select-window", "kill-window"],
        "layout_reflow": ["resize-pane", "select-layout", "swap-pane", "move-pane"],
        "pane_id_stability": ["list-panes"],
        "user_options_title": ["set-option", "set-window-option", "rename-window"],
        "capture_last_n_lines": ["capture-pane"],
        "buffer_paste": ["load-buffer", "paste-buffer", "delete-buffer"],
        "ctrl_c_ctrl_d": ["send-keys"],
        "pane_death": ["respawn-pane", "kill-window"],
        "kill_session_cleanup": ["kill-session"],
        "daemon_crash_cleanup_evidence": ["start-server", "kill-server"],
        "provider_process_distinction_workaround_evidence": ["list-panes", "capture-pane"],
    }
    for name, catalog in SEMANTIC_CATALOG.items():
        path = run_dir / "artifacts" / "semantics" / f"{name}.json"
        if name == "capture_format_fidelity_for_provider_completion":
            evidence, status, workaround, notes = _capture_fidelity_evidence(path, raw_results)
        else:
            deps = dependencies.get(name, [])
            status, assertions, notes = _assert_semantic(name, command_results, raw_results)
            workaround = None
            if status == "partial":
                workaround = {
                    "id": f"{name}-scenario-gap",
                    "description": "required command prerequisites did not prove the full CCB semantic scenario",
                    "evidence": path.relative_to(run_dir).as_posix(),
                    "accepted": False,
                }
            live_workaround = _accepted_live_workaround(
                name,
                live_attach_evidence=live_attach_evidence,
                live_attach_evidence_path=live_attach_evidence_path,
                live_client_evidence=live_client_evidence,
                live_client_evidence_path=live_client_evidence_path,
            )
            if live_workaround is not None:
                workaround = live_workaround
            evidence = {
                "dependencies": deps,
                "assertions": assertions,
                "status": status,
                "notes": notes,
                "workaround": workaround,
            }
            _write_json(path, evidence)
        artifact_index.append(_artifact_entry(run_dir, path, kind="semantic", probe=name))
        semantics[name] = _result_record(
            catalog=catalog,
            status=status,
            evidence=path.relative_to(run_dir).as_posix(),
            workaround=workaround,
            notes=notes,
        )
    return semantics


def _probe_preflight(
    runner: Any,
    rmux_bin: str,
    run_dir: Path,
    *,
    platform_name: str | None = None,
    require_executable: bool = True,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    artifacts: list[dict[str, Any]] = []
    system_name = (platform_name or platform.system()).lower()
    executable_path = shutil.which(rmux_bin)
    explicit_path = Path(rmux_bin).expanduser()
    executable_found = executable_path is not None or explicit_path.exists()
    executable = executable_path or str(explicit_path if explicit_path.exists() else rmux_bin)
    version = runner.run([rmux_bin, "-V"], timeout=5.0) if executable_found or not require_executable else CommandResult(
        [rmux_bin, "-V"], 127, "", "rmux executable not found", 5.0
    )
    daemon_probe = runner.run([rmux_bin, "list-sessions"], timeout=5.0) if version.returncode == 0 else CommandResult(
        [rmux_bin, "list-sessions"], 127, "", "preflight version check failed", 5.0
    )
    failure_reason = None
    probe_status = "completed"
    if system_name != "windows":
        probe_status = "skipped"
        failure_reason = f"native Windows required, got {system_name}"
    elif require_executable and not executable_found:
        probe_status = "failed"
        failure_reason = "rmux executable not found"
    elif version.returncode != 0:
        probe_status = "failed"
        failure_reason = "rmux version check failed"
    payload = {
        "platform": system_name,
        "windows_release": platform.release() if system_name == "windows" else None,
        "rmux_executable": executable,
        "rmux_executable_found": executable_found,
        "version": redact_text((version.stdout or version.stderr).strip()),
        "version_returncode": version.returncode,
        "probe_status": probe_status,
        "failure_reason": failure_reason,
        "shell": os.environ.get("ComSpec") or os.environ.get("SHELL"),
        "run_id": run_dir.name,
        "daemon_pre_state": {
            "detected": daemon_probe.returncode == 0,
            "returncode": daemon_probe.returncode,
            "evidence": "artifacts/preflight/daemon-pre-state.json",
        },
    }
    path = run_dir / "artifacts" / "preflight" / "daemon-pre-state.json"
    _write_json(
        path,
        {
            "args": daemon_probe.args,
            "returncode": daemon_probe.returncode,
            "stdout": redact_text(daemon_probe.stdout),
            "stderr": redact_text(daemon_probe.stderr),
        },
    )
    artifacts.append(_artifact_entry(run_dir, path, kind="preflight", probe="daemon-pre-state"))
    return payload, artifacts


def _cleanup_windows_probe_daemons(namespace: str, run_dir: Path) -> Path | None:
    if platform.system().lower() != "windows":
        return None
    env = dict(os.environ)
    env["CCB_RMUX_PROBE_NAMESPACE"] = namespace
    command = (
        "Get-CimInstance Win32_Process | "
        "Where-Object { "
        "($_.Name -eq 'rmux.exe' -or $_.Name -eq 'psmux.exe') -and "
        "$_.CommandLine -like \"*$env:CCB_RMUX_PROBE_NAMESPACE*\" "
        "} | ForEach-Object { "
        "$targetPid = $_.ProcessId; Stop-Process -Id $targetPid -Force; $targetPid "
        "}"
    )
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", command],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
        check=False,
        env=env,
    )
    path = run_dir / "artifacts" / "cleanup" / "orphan-daemons.json"
    _write_json(
        path,
        {
            "args": ["powershell", "-NoProfile", "-Command", "cleanup rmux/psmux daemon by probe namespace"],
            "namespace": namespace,
            "returncode": result.returncode,
            "stdout": redact_text(result.stdout),
            "stderr": redact_text(result.stderr),
        },
    )
    return path


def run_probe(
    work_root: Path,
    *,
    runner: Any | None = None,
    rmux_bin: str = "rmux",
    platform_name: str | None = None,
    live_attach_evidence_path: Path | None = None,
    live_client_evidence_path: Path | None = None,
) -> dict[str, Any]:
    require_executable = runner is None
    runner = runner or SubprocessRunner()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = work_root.expanduser().resolve(strict=False) / f"run-{stamp}-{os.getpid()}"
    work_dir = run_dir / "work"
    work_dir.mkdir(parents=True, exist_ok=False)
    namespace = f"ccb-rmux-probe-{os.getpid()}-{stamp.lower()}"
    session = "ccb-rmux-probe"
    live_attach_evidence = _read_optional_json(live_attach_evidence_path)
    live_client_evidence = _read_optional_json(live_client_evidence_path)

    artifact_index: list[dict[str, Any]] = []
    preflight, preflight_artifacts = _probe_preflight(
        runner,
        rmux_bin,
        run_dir,
        platform_name=platform_name,
        require_executable=require_executable,
    )
    artifact_index.extend(preflight_artifacts)

    if preflight["probe_status"] != "completed":
        report = {
            "backend_impl": backend_impl_name(rmux_bin),
            "version": preflight.get("version") or "unknown",
            "platform": preflight["platform"],
            "generated_at": utc_now(),
            "probe_status": preflight["probe_status"],
            "run_dir": str(run_dir),
            "preflight": preflight,
            "commands": {},
            "semantics": {},
            "artifact_index": artifact_index,
            "blocking_gaps": [],
        }
        report_path = run_dir / "capability-report.json"
        _write_json(report_path, report)
        return report

    commands: dict[str, Any] = {}
    raw_results: dict[str, CommandResult] = {}
    for name in COMMAND_ORDER:
        if name in {"kill-session", "kill-server"}:
            continue
        catalog = COMMAND_CATALOG[name]
        args = _command_args(rmux_bin, namespace, session, name, work_dir)
        result = runner.run(args, timeout=8.0)
        raw_results[name] = result
        status, notes = _command_status_and_notes(name, result)
        workaround = _accepted_live_workaround(
            name,
            live_attach_evidence=live_attach_evidence,
            live_attach_evidence_path=live_attach_evidence_path,
            live_client_evidence=live_client_evidence,
            live_client_evidence_path=live_client_evidence_path,
        )
        artifact_path = run_dir / "artifacts" / "commands" / f"{name}.json"
        _write_json(
            artifact_path,
            {
                "args": result.args,
                "returncode": result.returncode,
                "stdout_raw_sha256": hashlib.sha256(result.stdout_bytes or result.stdout.encode("utf-8")).hexdigest(),
                "stdout_raw_size": len(result.stdout_bytes or result.stdout.encode("utf-8")),
                "stdout": redact_text(result.stdout),
                "stderr": redact_text(result.stderr),
                "timeout": result.timeout,
                "classification": status,
                "notes": notes,
                "workaround": workaround,
            },
        )
        artifact_index.append(_artifact_entry(run_dir, artifact_path, kind="command", probe=name))
        commands[name] = _result_record(
            catalog=catalog,
            status=status,
            evidence=artifact_path.relative_to(run_dir).as_posix(),
            returncode=result.returncode,
            notes=notes,
            workaround=workaround,
        )
        if name in {"start-server", "new-session", "has-session"} and status == "unsupported":
            cleanup_path = _cleanup_windows_probe_daemons(namespace, run_dir) if isinstance(runner, SubprocessRunner) else None
            if cleanup_path is not None:
                artifact_index.append(_artifact_entry(run_dir, cleanup_path, kind="cleanup", probe="orphan-daemons"))
            report = {
                "backend_impl": backend_impl_name(rmux_bin),
                "version": preflight.get("version") or "unknown",
                "platform": preflight["platform"],
                "generated_at": utc_now(),
                "probe_status": preflight["probe_status"],
                "run_dir": str(run_dir),
                "preflight": preflight,
                "commands": commands,
                "semantics": {},
                "artifact_index": artifact_index,
                "blocking_gaps": _blocking_gaps(commands, {}),
                "early_stop": {
                    "command": name,
                    "reason": f"required core command {name} is unsupported; dependent checks skipped",
                    "evidence": artifact_path.relative_to(run_dir).as_posix(),
                    "cleanup_evidence": cleanup_path.relative_to(run_dir).as_posix() if cleanup_path is not None else None,
                },
            }
            report_path = run_dir / "capability-report.json"
            _write_json(report_path, report)
            return report

    verification_commands = {
        "namespace-default-has-session": [rmux_bin, "has-session", "-t", session],
        "list-panes-after-layout": [rmux_bin, "-L", namespace, "list-panes", "-t", session, "-F", "#{pane_id}"],
        "list-windows-after-policy": [rmux_bin, "-L", namespace, "list-windows", "-t", session],
    }
    for probe_name, args in verification_commands.items():
        result = runner.run(args, timeout=5.0)
        raw_results[f"verify.{probe_name}"] = result
        artifact_path = _write_command_artifact(run_dir, result, kind="verification", probe=probe_name)
        artifact_index.append(_artifact_entry(run_dir, artifact_path, kind="verification", probe=probe_name))

    fixture_script = work_dir / "capture_fidelity_fixture.py"
    fixture_script.write_text(
        "\n".join(
            [
                "from __future__ import annotations",
                "import sys",
                "sys.stdout.buffer.write(",
                "    \"CCB_RMUX_TRAILING   \\n\"",
                "    \"\\x1b]0;ccb-rmux-title\\x07CCB_RMUX_OSC_AFTER\\n\"",
                "    \"CCB_RMUX_WRAP_abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_\"",
                "    \"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789\\n\"",
                "    \"CCB_RMUX_WIDE_宽字符\\n\"",
                "    \"CCB_RMUX_LASTN\\n\"",
                "    .encode(\"utf-8\")",
                ")",
            ]
        ),
        encoding="utf-8",
    )
    fixture_command = subprocess.list2cmdline([sys.executable, str(fixture_script)])
    fixture_send = runner.run([rmux_bin, "-L", namespace, "send-keys", "-t", f"{session}:0.0", fixture_command, "Enter"], timeout=5.0)
    raw_results["verify.capture-fidelity-send"] = fixture_send
    fixture_send_path = _write_command_artifact(run_dir, fixture_send, kind="verification", probe="capture-fidelity-send")
    artifact_index.append(_artifact_entry(run_dir, fixture_send_path, kind="verification", probe="capture-fidelity-send"))
    if isinstance(runner, SubprocessRunner):
        time.sleep(0.5)
    fixture_capture = runner.run([rmux_bin, "-L", namespace, "capture-pane", "-t", f"{session}:0.0", "-p", "-S", "-12"], timeout=5.0)
    raw_results["verify.capture-fidelity"] = fixture_capture
    fixture_capture_path = _write_command_artifact(run_dir, fixture_capture, kind="verification", probe="capture-fidelity")
    artifact_index.append(_artifact_entry(run_dir, fixture_capture_path, kind="verification", probe="capture-fidelity"))
    tail_capture = runner.run([rmux_bin, "-L", namespace, "capture-pane", "-t", f"{session}:0.0", "-p", "-S", "-2"], timeout=5.0)
    raw_results["verify.capture-last-n"] = tail_capture
    tail_capture_path = _write_command_artifact(run_dir, tail_capture, kind="verification", probe="capture-last-n")
    artifact_index.append(_artifact_entry(run_dir, tail_capture_path, kind="verification", probe="capture-last-n"))

    buffer_name = "ccb-rmux-buffer-verify"
    buffer_file = work_dir / "buffer-verify.txt"
    buffer_file.write_text("echo CCB_RMUX_BUFFER_PASTE_OK", encoding="utf-8")
    buffer_load = runner.run([rmux_bin, "-L", namespace, "load-buffer", "-b", buffer_name, str(buffer_file)], timeout=5.0)
    raw_results["verify.buffer-paste-load"] = buffer_load
    buffer_load_path = _write_command_artifact(run_dir, buffer_load, kind="verification", probe="buffer-paste-load")
    artifact_index.append(_artifact_entry(run_dir, buffer_load_path, kind="verification", probe="buffer-paste-load"))
    buffer_paste = runner.run([rmux_bin, "-L", namespace, "paste-buffer", "-p", "-t", f"{session}:0.0", "-b", buffer_name], timeout=5.0)
    raw_results["verify.buffer-paste-paste"] = buffer_paste
    buffer_paste_path = _write_command_artifact(run_dir, buffer_paste, kind="verification", probe="buffer-paste-paste")
    artifact_index.append(_artifact_entry(run_dir, buffer_paste_path, kind="verification", probe="buffer-paste-paste"))
    buffer_enter = runner.run([rmux_bin, "-L", namespace, "send-keys", "-t", f"{session}:0.0", "Enter"], timeout=5.0)
    raw_results["verify.buffer-paste-enter"] = buffer_enter
    buffer_enter_path = _write_command_artifact(run_dir, buffer_enter, kind="verification", probe="buffer-paste-enter")
    artifact_index.append(_artifact_entry(run_dir, buffer_enter_path, kind="verification", probe="buffer-paste-enter"))
    buffer_delete = runner.run([rmux_bin, "-L", namespace, "delete-buffer", "-b", buffer_name], timeout=5.0)
    raw_results["verify.buffer-paste-delete"] = buffer_delete
    buffer_delete_path = _write_command_artifact(run_dir, buffer_delete, kind="verification", probe="buffer-paste-delete")
    artifact_index.append(_artifact_entry(run_dir, buffer_delete_path, kind="verification", probe="buffer-paste-delete"))
    if isinstance(runner, SubprocessRunner):
        time.sleep(0.5)
    buffer_capture = runner.run([rmux_bin, "-L", namespace, "capture-pane", "-t", f"{session}:0.0", "-p", "-S", "-20"], timeout=5.0)
    raw_results["verify.buffer-paste-capture"] = buffer_capture
    buffer_capture_path = _write_command_artifact(run_dir, buffer_capture, kind="verification", probe="buffer-paste-capture")
    artifact_index.append(_artifact_entry(run_dir, buffer_capture_path, kind="verification", probe="buffer-paste-capture"))

    eof_command = (
        "python -c \"import sys; print('CCB_RMUX_EOF_READY', flush=True); "
        "sys.stdin.read(); print('CCB_RMUX_EOF_DONE', flush=True)\""
    )
    eof_send = runner.run([rmux_bin, "-L", namespace, "send-keys", "-l", "-t", f"{session}:0.0", eof_command], timeout=5.0)
    raw_results["verify.ctrl-d-send"] = eof_send
    eof_send_path = _write_command_artifact(run_dir, eof_send, kind="verification", probe="ctrl-d-send")
    artifact_index.append(_artifact_entry(run_dir, eof_send_path, kind="verification", probe="ctrl-d-send"))
    eof_enter = runner.run([rmux_bin, "-L", namespace, "send-keys", "-t", f"{session}:0.0", "Enter"], timeout=5.0)
    raw_results["verify.ctrl-d-enter"] = eof_enter
    eof_enter_path = _write_command_artifact(run_dir, eof_enter, kind="verification", probe="ctrl-d-enter")
    artifact_index.append(_artifact_entry(run_dir, eof_enter_path, kind="verification", probe="ctrl-d-enter"))
    if isinstance(runner, SubprocessRunner):
        time.sleep(0.8)
    eof_key = runner.run([rmux_bin, "-L", namespace, "send-keys", "-t", f"{session}:0.0", "C-z", "Enter"], timeout=5.0)
    raw_results["verify.ctrl-d-key"] = eof_key
    eof_key_path = _write_command_artifact(run_dir, eof_key, kind="verification", probe="ctrl-d-key")
    artifact_index.append(_artifact_entry(run_dir, eof_key_path, kind="verification", probe="ctrl-d-key"))
    if isinstance(runner, SubprocessRunner):
        time.sleep(0.8)
    interrupt_command = "python -c \"import time; print('CCB_RMUX_INTERRUPT_READY', flush=True); time.sleep(30)\""
    interrupt_send = runner.run([rmux_bin, "-L", namespace, "send-keys", "-l", "-t", f"{session}:0.0", interrupt_command], timeout=5.0)
    raw_results["verify.ctrl-c-send"] = interrupt_send
    interrupt_send_path = _write_command_artifact(run_dir, interrupt_send, kind="verification", probe="ctrl-c-send")
    artifact_index.append(_artifact_entry(run_dir, interrupt_send_path, kind="verification", probe="ctrl-c-send"))
    interrupt_enter = runner.run([rmux_bin, "-L", namespace, "send-keys", "-t", f"{session}:0.0", "Enter"], timeout=5.0)
    raw_results["verify.ctrl-c-enter"] = interrupt_enter
    interrupt_enter_path = _write_command_artifact(run_dir, interrupt_enter, kind="verification", probe="ctrl-c-enter")
    artifact_index.append(_artifact_entry(run_dir, interrupt_enter_path, kind="verification", probe="ctrl-c-enter"))
    if isinstance(runner, SubprocessRunner):
        time.sleep(0.8)
    interrupt_key = runner.run([rmux_bin, "-L", namespace, "send-keys", "-t", f"{session}:0.0", "C-c"], timeout=5.0)
    raw_results["verify.ctrl-c-key"] = interrupt_key
    interrupt_key_path = _write_command_artifact(run_dir, interrupt_key, kind="verification", probe="ctrl-c-key")
    artifact_index.append(_artifact_entry(run_dir, interrupt_key_path, kind="verification", probe="ctrl-c-key"))
    interrupt_after = runner.run(
        [rmux_bin, "-L", namespace, "send-keys", "-l", "-t", f"{session}:0.0", "echo CCB_RMUX_CONTROL_AFTER_INTERRUPT"],
        timeout=5.0,
    )
    raw_results["verify.ctrl-c-after-send"] = interrupt_after
    interrupt_after_path = _write_command_artifact(run_dir, interrupt_after, kind="verification", probe="ctrl-c-after-send")
    artifact_index.append(_artifact_entry(run_dir, interrupt_after_path, kind="verification", probe="ctrl-c-after-send"))
    interrupt_after_enter = runner.run([rmux_bin, "-L", namespace, "send-keys", "-t", f"{session}:0.0", "Enter"], timeout=5.0)
    raw_results["verify.ctrl-c-after-enter"] = interrupt_after_enter
    interrupt_after_enter_path = _write_command_artifact(run_dir, interrupt_after_enter, kind="verification", probe="ctrl-c-after-enter")
    artifact_index.append(_artifact_entry(run_dir, interrupt_after_enter_path, kind="verification", probe="ctrl-c-after-enter"))
    if isinstance(runner, SubprocessRunner):
        time.sleep(0.8)
    control_capture = runner.run([rmux_bin, "-L", namespace, "capture-pane", "-t", f"{session}:0.0", "-p", "-S", "-80"], timeout=5.0)
    raw_results["verify.ctrl-c-ctrl-d-capture"] = control_capture
    control_capture_path = _write_command_artifact(run_dir, control_capture, kind="verification", probe="ctrl-c-ctrl-d-capture")
    artifact_index.append(_artifact_entry(run_dir, control_capture_path, kind="verification", probe="ctrl-c-ctrl-d-capture"))

    cleanup = runner.run([rmux_bin, "-L", namespace, "kill-session", "-t", session], timeout=5.0)
    raw_results["cleanup.kill-session"] = cleanup
    cleanup_path = run_dir / "artifacts" / "cleanup" / "kill-session.json"
    _write_json(
        cleanup_path,
        {
            "args": cleanup.args,
            "returncode": cleanup.returncode,
            "stdout_raw_sha256": hashlib.sha256(cleanup.stdout_bytes or cleanup.stdout.encode("utf-8")).hexdigest(),
            "stdout_raw_size": len(cleanup.stdout_bytes or cleanup.stdout.encode("utf-8")),
            "stdout": redact_text(cleanup.stdout),
            "stderr": redact_text(cleanup.stderr),
        },
    )
    artifact_index.append(_artifact_entry(run_dir, cleanup_path, kind="cleanup", probe="kill-session"))
    cleanup_catalog = COMMAND_CATALOG["kill-session"]
    cleanup_status = "supported" if cleanup.returncode == 0 else "unsupported"
    commands["kill-session"] = _result_record(
        catalog=cleanup_catalog,
        status=cleanup_status,
        evidence=cleanup_path.relative_to(run_dir).as_posix(),
        returncode=cleanup.returncode,
    )
    commands["kill-session"]["cleanup_evidence"] = cleanup_path.relative_to(run_dir).as_posix()
    if cleanup_status != "supported":
        commands["kill-session"]["status"] = cleanup_status
        commands["kill-session"]["notes"] = "final cleanup failed; command support cannot prove this run cleaned its namespace"

    kill_server = runner.run([rmux_bin, "-L", namespace, "kill-server"], timeout=5.0)
    raw_results["kill-server"] = kill_server
    kill_server_status, kill_server_notes = _command_status_and_notes("kill-server", kill_server)
    kill_server_workaround = _accepted_live_workaround(
        "kill-server",
        live_attach_evidence=live_attach_evidence,
        live_attach_evidence_path=live_attach_evidence_path,
        live_client_evidence=live_client_evidence,
        live_client_evidence_path=live_client_evidence_path,
    )
    kill_server_path = run_dir / "artifacts" / "commands" / "kill-server.json"
    _write_json(
        kill_server_path,
        {
            "args": kill_server.args,
            "returncode": kill_server.returncode,
            "stdout_raw_sha256": hashlib.sha256(kill_server.stdout_bytes or kill_server.stdout.encode("utf-8")).hexdigest(),
            "stdout_raw_size": len(kill_server.stdout_bytes or kill_server.stdout.encode("utf-8")),
            "stdout": redact_text(kill_server.stdout),
            "stderr": redact_text(kill_server.stderr),
            "timeout": kill_server.timeout,
            "classification": kill_server_status,
            "notes": kill_server_notes,
            "workaround": kill_server_workaround,
        },
    )
    artifact_index.append(_artifact_entry(run_dir, kill_server_path, kind="command", probe="kill-server"))
    commands["kill-server"] = _result_record(
        catalog=COMMAND_CATALOG["kill-server"],
        status=kill_server_status,
        evidence=kill_server_path.relative_to(run_dir).as_posix(),
        returncode=kill_server.returncode,
        notes=kill_server_notes,
        workaround=kill_server_workaround,
    )

    semantics = _derive_semantics(
        commands,
        raw_results,
        run_dir,
        artifact_index,
        live_attach_evidence=live_attach_evidence,
        live_attach_evidence_path=live_attach_evidence_path,
        live_client_evidence=live_client_evidence,
        live_client_evidence_path=live_client_evidence_path,
    )

    report = {
        "backend_impl": backend_impl_name(rmux_bin),
        "version": preflight.get("version") or "unknown",
        "platform": preflight["platform"],
        "generated_at": utc_now(),
        "probe_status": preflight["probe_status"],
        "run_dir": str(run_dir),
        "preflight": preflight,
        "commands": commands,
        "semantics": semantics,
        "artifact_index": artifact_index,
        "external_live_evidence": {
            "foreground_attach": str(live_attach_evidence_path) if live_attach_evidence_path is not None else None,
            "live_client_commands": str(live_client_evidence_path) if live_client_evidence_path is not None else None,
        },
        "blocking_gaps": [],
    }
    report["blocking_gaps"] = _blocking_gaps(commands, semantics)
    report_path = run_dir / "capability-report.json"
    _write_json(report_path, report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Probe Rmux capability for CCB's Windows mux backend roadmap.")
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--rmux-bin", default=os.environ.get("RMUX_BIN", "rmux"))
    parser.add_argument("--live-attach-evidence", type=Path, default=None)
    parser.add_argument("--live-client-evidence", type=Path, default=None)
    args = parser.parse_args(argv)

    report = run_probe(
        args.work_root,
        rmux_bin=args.rmux_bin,
        live_attach_evidence_path=args.live_attach_evidence,
        live_client_evidence_path=args.live_client_evidence,
    )
    report_path = Path(report["run_dir"]) / "capability-report.json"
    ok = report.get("probe_status") == "completed"
    print(
        json.dumps(
            {
                "ok": ok,
                "report": str(report_path),
                "probe_status": report.get("probe_status"),
                "reason": report.get("preflight", {}).get("failure_reason"),
                "blocking_gaps": len(report["blocking_gaps"]),
            },
            ensure_ascii=True,
        )
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
