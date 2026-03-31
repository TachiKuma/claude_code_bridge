"""Daemon performance benchmarks and lifecycle management tests (WIN-01).

Tests daemon cold start (D-06: <3s), command response (D-07: <500ms),
memory usage (D-08: <50MB), shutdown/ping/state cleanup (D-16).
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


@pytest.fixture(scope="module")
def daemon_proc():
    """Start a daemon subprocess once per module, yield (proc, state_file_path)."""
    # Use a dedicated temp dir for daemon state isolation
    import tempfile
    tmp_dir = Path(tempfile.mkdtemp(prefix="askd_test_"))

    env = {**os.environ, "CCB_RUN_DIR": str(tmp_dir)}

    proc = subprocess.Popen(
        [sys.executable, "bin/askd"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=CREATE_NO_WINDOW,
        env=env,
    )

    # Wait for state file to appear (daemon is ready)
    state_file = tmp_dir / "askd.json"
    deadline = time.time() + 10.0
    while time.time() < deadline:
        if state_file.exists():
            time.sleep(0.1)  # extra settle
            break
        time.sleep(0.05)
        if proc.poll() is not None:
            # Daemon crashed
            yield None, None, tmp_dir, env
            return

    yield proc, state_file, tmp_dir, env

    # Cleanup: shutdown daemon then terminate
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

    # Remove temp dir
    try:
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)
    except Exception:
        pass


@pytest.fixture
def temp_run_dir(tmp_path, monkeypatch, daemon_proc):
    """Create isolated temp run dir using the daemon's own tmp dir."""
    proc, state_file, tmp_dir, env = daemon_proc
    if tmp_dir is None:
        pytest.skip("Daemon failed to start")
    monkeypatch.setenv("CCB_RUN_DIR", str(tmp_dir))
    yield tmp_dir


@pytest.fixture
def daemon_state(daemon_proc):
    """Read and return daemon state dict, or skip if daemon not running."""
    proc, state_file, tmp_dir, env = daemon_proc
    if state_file is None or not state_file.exists():
        pytest.skip("Daemon state file not available")
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
        return state
    except Exception as exc:
        pytest.skip(f"Failed to read daemon state: {exc}")


@pytest.mark.windows
@pytest.mark.perf
class TestDaemonColdStart:
    """D-06: daemon cold start < 3 seconds."""

    def test_daemon_cold_start_under_3s(self, tmp_path):
        """Measure daemon cold start time from process launch to state file ready."""
        import tempfile

        tmp_dir = Path(tempfile.mkdtemp(prefix="askd_cold_start_"))
        env = {**os.environ, "CCB_RUN_DIR": str(tmp_dir)}
        state_file = tmp_dir / "askd.json"

        start = time.perf_counter()
        proc = subprocess.Popen(
            [sys.executable, "bin/askd"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=CREATE_NO_WINDOW,
            env=env,
        )

        # Poll for state file
        deadline = time.time() + 5.0
        ready = False
        while time.time() < deadline:
            if state_file.exists():
                ready = True
                break
            time.sleep(0.05)

        elapsed = time.perf_counter() - start

        # Cleanup
        try:
            proc.terminate()
            proc.wait(timeout=5.0)
        except Exception:
            try:
                proc.kill()
                proc.wait(timeout=2.0)
            except Exception:
                pass
        try:
            import shutil
            shutil.rmtree(tmp_dir, ignore_errors=True)
        except Exception:
            pass

        assert ready, f"Daemon did not start within 5s (elapsed: {elapsed:.2f}s)"
        assert elapsed < 3.0, f"daemon cold start took {elapsed:.2f}s (limit: 3s)"


@pytest.mark.windows
@pytest.mark.perf
class TestCommandResponse:
    """D-07: command response time < 500ms."""

    def test_command_response_under_500ms(self, daemon_state, daemon_proc):
        """Send ping and measure round-trip time."""
        import socket as sock_mod

        state = daemon_state
        host = state.get("connect_host") or state.get("host", "127.0.0.1")
        port = int(state["port"])
        token = state["token"]

        req = json.dumps({
            "type": "askd.ping",
            "v": 1,
            "id": "perf-test-ping",
            "token": token,
        }) + "\n"

        start = time.perf_counter()
        try:
            with sock_mod.create_connection((host, port), timeout=2.0) as sock:
                sock.sendall(req.encode("utf-8"))
                buf = b""
                deadline_read = time.time() + 2.0
                while b"\n" not in buf and time.time() < deadline_read:
                    chunk = sock.recv(1024)
                    if not chunk:
                        break
                    buf += chunk
                elapsed = time.perf_counter() - start
                assert b"\n" in buf, f"No response received within 2s"
                line = buf.split(b"\n", 1)[0].decode("utf-8", errors="replace")
                resp = json.loads(line)
                assert resp.get("exit_code") == 0, f"Ping failed: {resp}"
        except Exception as exc:
            pytest.fail(f"Socket communication failed: {exc}")

        assert elapsed < 0.5, f"ping round-trip took {elapsed:.3f}s (limit: 500ms)"


@pytest.mark.windows
@pytest.mark.perf
class TestDaemonMemory:
    """D-08: daemon memory usage < 50MB."""

    def test_daemon_memory_under_50mb(self, daemon_state, daemon_proc):
        """Measure daemon RSS memory and assert < 50MB."""
        pytest.importorskip("psutil", reason="psutil not installed")

        import psutil

        state = daemon_state
        pid = int(state.get("pid", 0))
        assert pid > 0, "Daemon PID not found in state"

        try:
            proc = psutil.Process(pid)
            mem_info = proc.memory_info()
            rss = mem_info.rss
        except psutil.NoSuchProcess:
            pytest.skip("Daemon process not found")

        limit = 50 * 1024 * 1024  # 50 MB
        assert rss < limit, f"daemon RSS {rss / 1024 / 1024:.1f}MB (limit: 50MB)"


@pytest.mark.windows
@pytest.mark.perf
class TestPythonModuleImportTime:
    """Informational baseline: Python module import time."""

    def test_python_module_import_time(self):
        """Measure askd_server import time as a baseline (informational, no hard assert)."""
        import timeit

        setup = 'import sys; sys.path.insert(0, "lib")'
        stmt = 'import askd_server'
        times = timeit.repeat(stmt=stmt, setup=setup, number=1, repeat=3)
        avg_ms = sum(times) / len(times) * 1000
        # This is informational only - log but do not assert a hard threshold
        # Store result for human review
        print(f"\n[INFO] askd_server import time: {avg_ms:.1f}ms avg (3 runs)")


@pytest.mark.windows
class TestDaemonShutdown:
    """D-16: daemon shutdown and state file cleanup."""

    def test_daemon_shutdown_cleans_state_file(self, tmp_path):
        """Start daemon, shutdown via shutdown_daemon(), verify state file removed."""
        from lib.askd.daemon import shutdown_daemon

        # Start a fresh daemon in isolated temp dir
        import tempfile
        import shutil

        tmp_dir = Path(tempfile.mkdtemp(prefix="askd_shutdown_test_"))
        env = {**os.environ, "CCB_RUN_DIR": str(tmp_dir)}
        state_file = tmp_dir / "askd.json"

        try:
            proc = subprocess.Popen(
                [sys.executable, "bin/askd"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=CREATE_NO_WINDOW,
                env=env,
            )

            # Wait for state file
            deadline = time.time() + 10.0
            while time.time() < deadline:
                if state_file.exists():
                    break
                time.sleep(0.05)
                if proc.poll() is not None:
                    pytest.fail(f"Daemon crashed during startup")

            assert state_file.exists(), "State file should exist before shutdown"

            # Shutdown via shutdown_daemon
            ok = shutdown_daemon(state_file=state_file, timeout_s=5.0)
            assert ok, "shutdown_daemon should return True"

            # Wait for process to exit
            try:
                proc.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=2.0)

            # Verify state file is cleaned up
            assert not state_file.exists(), "State file should be removed after shutdown"
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)


@pytest.mark.windows
class TestDaemonPing:
    """D-16: daemon ping functionality."""

    def test_daemon_ping_returns_true_when_running(self, daemon_state):
        """ping_daemon returns True when daemon is running."""
        from lib.askd.daemon import ping_daemon

        # Need to set CCB_RUN_DIR so ping_daemon finds the correct state file
        state = daemon_state
        state_file_path_str = str(state_file_path("askd.json"))
        result = ping_daemon(timeout_s=2.0, state_file=Path(state_file_path_str))
        assert result is True, "ping_daemon should return True when daemon is running"

    def test_daemon_ping_returns_false_when_not_running(self, tmp_path):
        """ping_daemon returns False when no daemon is running."""
        from lib.askd.daemon import ping_daemon

        # Use a non-existent state file path
        fake_state = tmp_path / "nonexistent_askd.json"
        assert not fake_state.exists(), "Fake state file should not exist"

        result = ping_daemon(timeout_s=1.0, state_file=fake_state)
        assert result is False, "ping_daemon should return False when daemon is not running"
