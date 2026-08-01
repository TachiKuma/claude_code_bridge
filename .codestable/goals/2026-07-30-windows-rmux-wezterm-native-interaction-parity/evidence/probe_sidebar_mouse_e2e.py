#!/usr/bin/env python3
"""Iteration 001 诊断 e2e：证明 rmux send-keys 把 SGR mouse 事件送达真实
ccb-agent-sidebar pane 的 crossterm（读 SidebarMouseProbe JSON）。

只读诊断，不改任何生产文件。产出 JSON 证据到 stdout。
Windows 上 new-session/start-server 必须 DEVNULL stdio，否则挂起
（见 scripts/probe_rmux_capability.py 的 _rmux_probe_stdio_mode）。
"""
from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
RMUX = shutil.which("rmux") or "rmux"
SIDEBAR = REPO / "bin" / "ccb-agent-sidebar.exe"
if not SIDEBAR.exists():
    SIDEBAR = REPO / "tools" / "ccb-agent-sidebar" / "target" / "release" / "ccb-agent-sidebar.exe"

WIDTH, HEIGHT = 80, 24


def run(args, *, devnull=False, timeout=8.0, env=None):
    kwargs = {"check": False, "timeout": timeout}
    if devnull:
        kwargs["stdout"] = subprocess.DEVNULL
        kwargs["stderr"] = subprocess.DEVNULL
    else:
        kwargs["stdout"] = subprocess.PIPE
        kwargs["stderr"] = subprocess.PIPE
    if env is not None:
        kwargs["env"] = env
    try:
        cp = subprocess.run(args, **kwargs)
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"
    out = (cp.stdout or b"").decode("utf-8", "replace") if not devnull else ""
    err = (cp.stderr or b"").decode("utf-8", "replace") if not devnull else ""
    return cp.returncode, out, err


def sgr_hex(col, row, press=True):
    seq = f"\x1b[<0;{col};{row}{'M' if press else 'm'}".encode("ascii")
    return " ".join(f"{b:02x}" for b in seq)


def main():
    ns = f"ccbe2e{uuid.uuid4().hex[:10]}"
    session = "s1"
    proj = Path(tempfile.mkdtemp(prefix="ccb-e2e-proj-"))
    probe = Path(tempfile.mkdtemp(prefix="ccb-e2e-probe-")) / "probe.json"
    # 无害 ccb stub，避免真实 kill / config ui
    stub = proj / "ccb-stub.cmd"
    stub.write_text("@echo ccb-stub-invoked %*\r\n", encoding="ascii")
    bogus_socket = r"\\.\pipe\ccb-e2e-bogus-" + ns

    env = dict(os.environ)
    env["CCB_AGENT_SIDEBAR_MOUSE_PROBE"] = str(probe)
    env["CCB_SIDEBAR_CCB_BIN"] = str(stub)

    evidence = {
        "rmux": RMUX,
        "sidebar": str(SIDEBAR),
        "sidebar_exists": SIDEBAR.exists(),
        "namespace": ns,
        "pane_size": f"{WIDTH}x{HEIGHT}",
        "probe_path": str(probe),
        "steps": [],
    }

    def record(step, rc, out, err):
        evidence["steps"].append(
            {"step": step, "rc": rc, "stdout": out[-400:], "stderr": err[-400:]}
        )

    base = [RMUX, "-L", ns]
    sidebar_cmd = (
        f'"{SIDEBAR}" --ccbd-socket "{bogus_socket}" '
        f'--project-root "{proj}" --pane-window main'
    )
    try:
        rc, out, err = run(
            [*base, "new-session", "-d", "-s", session, "-x", str(WIDTH), "-y", str(HEIGHT), sidebar_cmd],
            devnull=True, env=env,
        )
        record("new-session", rc, out, err)

        # 等 sidebar 初始化并创建 probe 文件
        probe_ready = False
        for _ in range(40):
            time.sleep(0.25)
            if probe.exists():
                probe_ready = True
                break
        evidence["probe_created"] = probe_ready
        if probe_ready:
            evidence["probe_initial"] = json.loads(io.open(probe, encoding="utf-8").read())

        # 探测 send-keys -H 是否被接受（发一个 mid-screen 左键按下）
        mid_col, mid_row = 40, 5
        rc, out, err = run([*base, "send-keys", "-t", session, "-H", *sgr_hex(mid_col, mid_row).split()])
        record("send-keys -H press mid", rc, out, err)
        rc, out, err = run([*base, "send-keys", "-t", session, "-H", *sgr_hex(mid_col, mid_row, press=False).split()])
        record("send-keys -H release mid", rc, out, err)
        time.sleep(0.6)
        if probe.exists():
            evidence["probe_after_mid"] = json.loads(io.open(probe, encoding="utf-8").read())

        # settings 列：tree area 假设近似全宽，settings crossterm col = WIDTH-4 (0-based) → SGR col = WIDTH-3
        set_col = WIDTH - 3
        rc, out, err = run([*base, "send-keys", "-t", session, "-H", *sgr_hex(set_col, 1).split()])
        record("send-keys -H press settings", rc, out, err)
        rc, out, err = run([*base, "send-keys", "-t", session, "-H", *sgr_hex(set_col, 1, press=False).split()])
        record("send-keys -H release settings", rc, out, err)
        time.sleep(0.8)
        if probe.exists():
            evidence["probe_after_settings"] = json.loads(io.open(probe, encoding="utf-8").read())

        # capture pane 快照（人读辅助）
        rc, out, err = run([*base, "capture-pane", "-t", session, "-p"])
        evidence["pane_capture_tail"] = out[-600:]
    finally:
        run([*base, "kill-server"], devnull=True)

    print(json.dumps(evidence, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
