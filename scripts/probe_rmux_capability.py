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


TOKEN_RE = re.compile(r"(sk-[A-Za-z0-9_-]{6,}|sess-[A-Za-z0-9_-]{6,}|Bearer\s+[A-Za-z0-9._-]+)")
SECRET_RE = re.compile(r"(?i)\b(api[_-]?key|token|secret|password)\s*[:=]\s*\S+")

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
    "move-pane",
    "resize-pane",
    "select-layout",
    "swap-pane",
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


class SubprocessRunner:
    def run(self, args: list[str], *, timeout: float = 5.0) -> CommandResult:
        try:
            completed = subprocess.run(
                args,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            return CommandResult(args, 124, exc.stdout or "", exc.stderr or "timeout", timeout)
        except OSError as exc:
            return CommandResult(args, 127, "", str(exc), timeout)
        return CommandResult(args, completed.returncode, completed.stdout, completed.stderr, timeout)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def redact_text(text: str) -> str:
    value = TOKEN_RE.sub("[REDACTED]", text or "")
    return SECRET_RE.sub(lambda match: f"{match.group(1)}=[REDACTED]", value)


def command_name(args: list[str]) -> str:
    catalog = set(COMMAND_CATALOG)
    for item in args:
        if item in catalog:
            return item
    return Path(args[0]).name if args else "unknown"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


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
        return [*base, "attach-session", "-t", session, "-d"]
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
        return [*base, "move-pane", "-s", f"{session}:0.0", "-t", f"{session}:0.0"]
    if name == "resize-pane":
        return [*base, "resize-pane", *pane, "-Z"]
    if name == "select-layout":
        return [*base, "select-layout", *target, "even-horizontal"]
    if name == "swap-pane":
        return [*base, "swap-pane", "-s", f"{session}:0.0", "-t", f"{session}:0.0"]
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
        return [*base, "refresh-client", "-S"]
    return [*base, name]


def _status_for_result(result: CommandResult) -> str:
    return "supported" if result.returncode == 0 else "unsupported"


def _result_record(
    *,
    catalog: dict[str, str | bool],
    status: str,
    evidence: str,
    workaround: dict[str, Any] | None = None,
    returncode: int | None = None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "required": bool(catalog["required"]),
        "status": status,
        "evidence": evidence,
        "workaround": workaround,
        "degrade_impact": str(catalog["degrade_impact"]),
        "consequence": str(catalog["consequence"]),
        "notes": "",
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
            if status == "unsupported" or (status in {"partial", "workaround"} and not accepted):
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


def _capture_fidelity_evidence(path: Path) -> dict[str, Any]:
    cases = [
        {
            "dimension": "trailing_whitespace",
            "raw": "• Working (1s • esc to interrupt)   \n",
            "absorbed": True,
        },
        {
            "dimension": "csi",
            "raw": "\x1b[31m• Working (1s • esc to interrupt)\x1b[0m\n",
            "absorbed": True,
        },
        {
            "dimension": "osc",
            "raw": "\x1b]0;title\x07• Working (1s • esc to interrupt)\n",
            "absorbed": False,
        },
        {
            "dimension": "wrapping",
            "raw": "• Working (1s • esc to interrupt)\nwrapped-body-without-logical-line-rebuild\n",
            "absorbed": False,
        },
        {
            "dimension": "wide_char",
            "raw": "• Working (1s • esc to interrupt)\n宽字符列宽需要 Rmux/tmux 输出平价证明\n",
            "absorbed": False,
        },
        {
            "dimension": "last_n_tail",
            "raw": "old\n• Working (1s • esc to interrupt)\n",
            "absorbed": False,
        },
    ]
    for case in cases:
        raw = str(case["raw"])
        codex_status = parse_codex_pane_status(raw)
        claude_status = parse_claude_pane_status("✶ Thinking (1s, 1 token)\n" if case["dimension"] != "osc" else raw)
        case["consumer_strip"] = {
            "codex_normalized": normalize_codex_screen(raw),
            "claude_normalized": normalize_claude_screen(raw),
        }
        case["direct_stdout"] = {
            "codex_state": codex_status.state,
            "codex_reason": codex_status.reason,
            "claude_state": claude_status.state,
            "claude_reason": claude_status.reason,
        }

    payload = {
        "parser_paths": ["consumer_strip", "direct_stdout"],
        "providers": ["codex", "claude"],
        "normalization_responsibility": {
            "trailing_whitespace": "parser normalize_screen strips line tails",
            "csi": "current strip_ansi handles CSI sequences",
            "osc": "current strip_ansi does not remove OSC/non-CSI sequences",
            "wrapping": "current parser does not rebuild logical lines",
            "wide_char": "current parser does not correct display width",
            "last_n_tail": "must be proven by rmux/tmux capture tail equivalence",
        },
        "cases": cases,
    }
    _write_json(path, payload)
    return payload


def _derive_semantics(command_results: dict[str, Any], run_dir: Path, artifact_index: list[dict[str, Any]]) -> dict[str, Any]:
    semantics: dict[str, Any] = {}
    command_status = {name: value["status"] for name, value in command_results.items()}
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
            evidence = _capture_fidelity_evidence(path)
            status = "partial"
            workaround = {
                "id": "parser-normalization-boundary",
                "description": "fixture proves parser-facing paths, but OSC/wrapping/wide-char/last-N require true Rmux artifact equivalence",
                "evidence": path.relative_to(run_dir).as_posix(),
                "accepted": False,
            }
        else:
            deps = dependencies.get(name, [])
            missing = [dep for dep in deps if command_status.get(dep) != "supported"]
            status = "supported" if not missing else "unsupported"
            workaround = None
            evidence = {"dependencies": deps, "missing": missing, "status": status}
            _write_json(path, evidence)
        artifact_index.append(_artifact_entry(run_dir, path, kind="semantic", probe=name))
        semantics[name] = _result_record(
            catalog=catalog,
            status=status,
            evidence=path.relative_to(run_dir).as_posix(),
            workaround=workaround,
        )
    return semantics


def _probe_preflight(runner: Any, rmux_bin: str, run_dir: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    artifacts: list[dict[str, Any]] = []
    executable = shutil.which(rmux_bin) or rmux_bin
    version = runner.run([rmux_bin, "-V"], timeout=5.0)
    daemon_probe = runner.run([rmux_bin, "list-sessions"], timeout=5.0)
    payload = {
        "platform": platform.system().lower(),
        "windows_release": platform.release() if platform.system().lower() == "windows" else None,
        "rmux_executable": executable,
        "version": redact_text((version.stdout or version.stderr).strip()),
        "version_returncode": version.returncode,
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


def run_probe(work_root: Path, *, runner: Any | None = None, rmux_bin: str = "rmux") -> dict[str, Any]:
    runner = runner or SubprocessRunner()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = work_root.expanduser().resolve(strict=False) / f"run-{stamp}-{os.getpid()}"
    work_dir = run_dir / "work"
    work_dir.mkdir(parents=True, exist_ok=False)
    namespace = f"ccb-rmux-probe-{os.getpid()}-{stamp.lower()}"
    session = "ccb-rmux-probe"

    artifact_index: list[dict[str, Any]] = []
    preflight, preflight_artifacts = _probe_preflight(runner, rmux_bin, run_dir)
    artifact_index.extend(preflight_artifacts)

    commands: dict[str, Any] = {}
    for name in COMMAND_ORDER:
        catalog = COMMAND_CATALOG[name]
        args = _command_args(rmux_bin, namespace, session, name, work_dir)
        result = runner.run(args, timeout=8.0)
        artifact_path = run_dir / "artifacts" / "commands" / f"{name}.json"
        _write_json(
            artifact_path,
            {
                "args": result.args,
                "returncode": result.returncode,
                "stdout": redact_text(result.stdout),
                "stderr": redact_text(result.stderr),
                "timeout": result.timeout,
            },
        )
        artifact_index.append(_artifact_entry(run_dir, artifact_path, kind="command", probe=name))
        commands[name] = _result_record(
            catalog=catalog,
            status=_status_for_result(result),
            evidence=artifact_path.relative_to(run_dir).as_posix(),
            returncode=result.returncode,
        )

    semantics = _derive_semantics(commands, run_dir, artifact_index)
    cleanup = runner.run([rmux_bin, "-L", namespace, "kill-session", "-t", session], timeout=5.0)
    cleanup_path = run_dir / "artifacts" / "cleanup" / "kill-session.json"
    _write_json(
        cleanup_path,
        {
            "args": cleanup.args,
            "returncode": cleanup.returncode,
            "stdout": redact_text(cleanup.stdout),
            "stderr": redact_text(cleanup.stderr),
        },
    )
    artifact_index.append(_artifact_entry(run_dir, cleanup_path, kind="cleanup", probe="kill-session"))

    report = {
        "backend_impl": "rmux",
        "version": preflight.get("version") or "unknown",
        "platform": preflight["platform"],
        "generated_at": utc_now(),
        "probe_status": "completed",
        "run_dir": str(run_dir),
        "preflight": preflight,
        "commands": commands,
        "semantics": semantics,
        "artifact_index": artifact_index,
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
    args = parser.parse_args(argv)

    report = run_probe(args.work_root, rmux_bin=args.rmux_bin)
    report_path = Path(report["run_dir"]) / "capability-report.json"
    print(json.dumps({"ok": True, "report": str(report_path), "blocking_gaps": len(report["blocking_gaps"])}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
