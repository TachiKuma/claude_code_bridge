"""Shared fixtures for Windows native audit tests."""

import os
import socket
import types

import pytest


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
