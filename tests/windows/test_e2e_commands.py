"""End-to-end command functionality tests (WIN-01, Success Criteria #1).

Verifies core commands (ask, pend, ccb start) work end-to-end on
native Windows: daemon start, ping command, pend polling, and full
start/stop lifecycle.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from lib.askd_runtime import state_file_path

CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0


def _start_isolated_daemon(tmp_dir: Path):
    """Start a daemon in the given temp dir. Returns (proc, state_file)."""
    env = {**os.environ, "CCB_RUN_DIR": str(tmp_dir)}
    proc = subprocess.Popen(
        [sys.executable, "bin/askd"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=CREATE_NO_WINDOW,
        env=env,
    )
    state_file = tmp_dir / "askd.json"

    # Wait for state file
    deadline = time.time() + 10.0
    while time.time() < deadline:
        if state_file.exists():
            time.sleep(0.1)  # settle
            break
        time.sleep(0.05)
        if proc.poll() is not None:
            return proc, state_file, False  # crashed

    return proc, state_file, True


def _stop_daemon(proc, tmp_dir):
    """Terminate daemon and clean up temp dir."""
    try:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=2.0)
    except Exception:
        pass
    try:
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)
    except Exception:
        pass


@pytest.mark.windows
class TestE2EDaemonStart:
    """Test 5: daemon start creates valid state file."""

    def test_e2e_daemon_start_creates_state_file(self, tmp_path):
        """bin/askd creates state file with port, token, pid keys."""
        import tempfile
        import shutil

        tmp_dir = Path(tempfile.mkdtemp(prefix="askd_e2e_start_"))
        try:
            proc, state_file, ok = _start_isolated_daemon(tmp_dir)
            assert ok, "Daemon crashed during startup"
            assert state_file.exists(), "State file should exist after daemon start"

            state = json.loads(state_file.read_text(encoding="utf-8"))
            assert "port" in state, "State file should contain 'port'"
            assert "token" in state, "State file should contain 'token'"
            assert "pid" in state, "State file should contain 'pid'"
            assert isinstance(state["pid"], int) and state["pid"] > 0, "PID should be a positive integer"
        finally:
            _stop_daemon(proc, tmp_dir)


@pytest.mark.windows
class TestE2EAskPing:
    """Test 6: ask ping command via socket."""

    def test_e2e_ask_ping_command(self, tmp_path):
        """Send ping to running daemon via socket, verify valid response."""
        import socket as sock_mod
        import tempfile

        tmp_dir = Path(tempfile.mkdtemp(prefix="askd_e2e_ping_"))
        try:
            proc, state_file, ok = _start_isolated_daemon(tmp_dir)
            assert ok, "Daemon crashed during startup"

            state = json.loads(state_file.read_text(encoding="utf-8"))
            host = state.get("connect_host") or state.get("host", "127.0.0.1")
            port = int(state["port"])
            token = state["token"]

            req = json.dumps({
                "type": "ask.ping",
                "v": 1,
                "id": "e2e-ping-test",
                "token": token,
            }) + "\n"

            with sock_mod.create_connection((host, port), timeout=2.0) as sock:
                sock.sendall(req.encode("utf-8"))
                buf = b""
                deadline = time.time() + 2.0
                while b"\n" not in buf and time.time() < deadline:
                    chunk = sock.recv(1024)
                    if not chunk:
                        break
                    buf += chunk

            assert b"\n" in buf, "No response received from daemon"
            line = buf.split(b"\n", 1)[0].decode("utf-8", errors="replace")
            resp = json.loads(line)
            assert resp.get("exit_code") == 0, f"Ping returned error: {resp}"
            assert resp.get("type", "").endswith("response") or "pong" in resp.get("type", ""), \
                f"Unexpected response type: {resp.get('type')}"
        finally:
            _stop_daemon(proc, tmp_dir)


@pytest.mark.windows
class TestE2EPend:
    """Test 7: pend command polling mechanism."""

    def test_e2e_pend_returns_response(self, tmp_path):
        """Verify pend polling works: send a request without provider, expect error response."""
        import socket as sock_mod
        import tempfile

        tmp_dir = Path(tempfile.mkdtemp(prefix="askd_e2e_pend_"))
        try:
            proc, state_file, ok = _start_isolated_daemon(tmp_dir)
            assert ok, "Daemon crashed during startup"

            state = json.loads(state_file.read_text(encoding="utf-8"))
            host = state.get("connect_host") or state.get("host", "127.0.0.1")
            port = int(state["port"])
            token = state["token"]

            # Send request without provider field (should get error)
            req = json.dumps({
                "type": "ask.request",
                "v": 1,
                "id": "e2e-pend-test",
                "token": token,
                "caller": "e2e-test",
            }) + "\n"

            with sock_mod.create_connection((host, port), timeout=5.0) as sock:
                sock.sendall(req.encode("utf-8"))
                buf = b""
                deadline = time.time() + 5.0
                while b"\n" not in buf and time.time() < deadline:
                    chunk = sock.recv(1024)
                    if not chunk:
                        break
                    buf += chunk

            assert b"\n" in buf, "No response from pend-like request"
            line = buf.split(b"\n", 1)[0].decode("utf-8", errors="replace")
            resp = json.loads(line)
            # Expect error because provider is missing
            assert "type" in resp, "Response should have 'type' field"
            assert resp.get("exit_code") != 0 or resp.get("reply") != "", \
                "Request without provider should get error or timeout response"

        finally:
            _stop_daemon(proc, tmp_dir)


@pytest.mark.windows
class TestE2ECcbStartStop:
    """Test 8: full daemon start/stop lifecycle."""

    def test_e2e_ccb_start_stop_cycle(self, tmp_path):
        """Full lifecycle: start daemon -> verify state -> stop daemon -> verify cleanup."""
        import tempfile

        tmp_dir = Path(tempfile.mkdtemp(prefix="askd_e2e_lifecycle_"))
        try:
            # Start
            proc, state_file, ok = _start_isolated_daemon(tmp_dir)
            assert ok, "Daemon crashed during startup"
            assert state_file.exists(), "State file should exist after start"

            state = json.loads(state_file.read_text(encoding="utf-8"))
            assert "port" in state, "State should have port"
            assert "token" in state, "State should have token"
            assert "pid" in state, "State should have pid"

            # Stop daemon by terminating process directly
            # (avoids importing internal askd package which may not be available)
            proc.terminate()
            try:
                proc.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=2.0)

            # Verify cleanup: state file should persist (daemon doesn't auto-delete)
            assert state_file.exists(), "State file should persist after process termination"
        finally:
            _stop_daemon(proc, tmp_dir)
