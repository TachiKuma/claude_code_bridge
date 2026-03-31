"""Shared fixtures for Windows native audit tests."""

import os
import shutil
import socket
import subprocess
import sys
import time
import types
from pathlib import Path

import pytest


CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0


@pytest.fixture(scope="module")
def daemon_proc():
    """Start a daemon subprocess once per module, yield (proc, state_file, tmp_dir, env).

    Used by multiple test modules (perf, security, socket tests).
    Skips if daemon fails to start.
    """
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
        shutil.rmtree(tmp_dir, ignore_errors=True)
    except Exception:
        pass


@pytest.fixture
def isolated_env():
    """Save and restore os.environ around each test to prevent CCB_* env var leakage."""
    original = os.environ.copy()
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(original)


@pytest.fixture
def temp_run_dir(tmp_path, monkeypatch, isolated_env):
    """Create a temporary CCB_RUN_DIR and set the env var for isolation."""
    run_dir = tmp_path / "ccb_run"
    run_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("CCB_RUN_DIR", str(run_dir))
    yield run_dir


@pytest.fixture
def daemon_spec():
    """Return a test ProviderDaemonSpec-like object using SimpleNamespace."""
    return types.SimpleNamespace(
        protocol_prefix="askd.test",
        daemon_key="test-daemon",
        lock_name="test-daemon.lock",
        log_file_name="test-daemon.log",
        idle_timeout_env="CCB_TEST_IDLE_TIMEOUT",
    )


@pytest.fixture
def daemon_token():
    """Return a fixed test token string for deterministic tests."""
    return "test-token-0123456789abcdef"


@pytest.fixture
def free_port():
    """Find and yield an available TCP port on 127.0.0.1."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        _, port = sock.getsockname()
    yield port
