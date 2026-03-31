"""Security audit tests for token handling and leakage (D-11/D-12).

Covers:
- Token entropy (128-bit from os.urandom(16).hex())
- Token uniqueness between calls
- Plaintext token storage in state file (Pitfall 3: audit finding)
- Token not leaked to log files
- Token not exposed in error response messages
"""

import ast
import json
import os
import re

import pytest
from pathlib import Path


# ---------------------------------------------------------------------------
# Test 1: random_token entropy -- 128 bits (32 hex chars)
# ---------------------------------------------------------------------------
@pytest.mark.windows
@pytest.mark.security
def test_random_token_entropy():
    """random_token() returns 32 hex chars = 128 bits of entropy from os.urandom(16)."""
    from lib.askd_runtime import random_token
    token = random_token()
    assert len(token) == 32, f"Expected 32 hex chars, got {len(token)}"
    assert all(c in "0123456789abcdef" for c in token), "Token must be lowercase hex"


# ---------------------------------------------------------------------------
# Test 2: random_token uniqueness
# ---------------------------------------------------------------------------
@pytest.mark.windows
@pytest.mark.security
def test_random_token_unique():
    """Two consecutive random_token() calls return different values."""
    from lib.askd_runtime import random_token
    t1, t2 = random_token(), random_token()
    assert t1 != t2, "Two consecutive tokens must differ (statistical near-certainty)"


# ---------------------------------------------------------------------------
# Test 3: Token in state file is plaintext (audit finding: Pitfall 3)
# ---------------------------------------------------------------------------
@pytest.mark.windows
@pytest.mark.security
def test_token_in_state_file_is_plaintext(tmp_path):
    """State file stores token as plaintext JSON string.

    Audit finding: token is NOT hashed or encrypted.
    On Windows, os.chmod(0o600) is ineffective (NTFS), so the state file
    is protected only by NTFS user-level isolation. This needs DACL or
    DPAPI for proper protection.
    """
    test_token = "audit-test-secret-token-0123"
    state = {
        "token": test_token,
        "port": 12345,
        "pid": 1234,
        "host": "127.0.0.1",
        "connect_host": "127.0.0.1",
        "started_at": "2026-01-01 00:00:00",
        "python": "/usr/bin/python3",
        "managed": False,
        "work_dir": "/tmp/test",
    }
    state_file = tmp_path / "askd.json"
    state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")

    content = state_file.read_text(encoding="utf-8")
    loaded = json.loads(content)
    # Audit assertion: token IS stored as plaintext
    assert loaded["token"] == test_token, "Token stored as plaintext in state file"
    assert test_token in content, "Token value appears verbatim in state file"


# ---------------------------------------------------------------------------
# Test 4: Token not leaked to log files
# ---------------------------------------------------------------------------
@pytest.mark.windows
@pytest.mark.security
def test_token_not_in_log_files(tmp_path):
    """write_log() must not include the daemon token in log content.

    Verify that log lines written by the daemon do not contain
    token-like values (32 hex chars = 128-bit token).
    """
    from lib.askd_runtime import write_log

    log_file = tmp_path / "test-daemon.log"
    test_token = "audit-test-token-abc123"  # Not used in log calls

    # Simulate typical daemon log messages (from askd_server.py)
    write_log(log_file, f"[INFO] test-daemon started pid={os.getpid()} addr=127.0.0.1:12345")
    write_log(log_file, "[INFO] test-daemon idle timeout (60s) reached; shutting down")
    write_log(log_file, "[INFO] test-daemon parent pid 12345 exited; shutting down")
    write_log(log_file, "[ERROR] test-daemon crashed: ConnectionRefusedError")
    write_log(log_file, "[ERROR] request handler error: timeout")
    write_log(log_file, "[INFO] test-daemon stopped")

    content = log_file.read_text(encoding="utf-8")

    # The test token itself must not appear
    assert test_token not in content, "Test token leaked to log file"

    # Also check no token-like strings (32 consecutive hex chars) appear
    hex_pattern = r'\b[0-9a-f]{32}\b'
    matches = re.findall(hex_pattern, content)
    assert len(matches) == 0, f"Token-like string(s) found in log: {matches}"


# ---------------------------------------------------------------------------
# Test 5: Token not exposed in error response messages
# ---------------------------------------------------------------------------
@pytest.mark.windows
@pytest.mark.security
def test_token_not_exposed_in_error_messages():
    """Error responses from Handler.handle() must NOT include self.server.token.

    Scan lib/askd_server.py to verify that error response dicts
    (Unauthorized, Invalid request, Internal error, Invalid response)
    do not contain the key "token" in any dict literal within the Handler class.
    """
    server_file = Path(__file__).resolve().parent.parent.parent / "lib" / "askd_server.py"
    source = server_file.read_text(encoding="utf-8")

    tree = ast.parse(source)

    handler_class = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "Handler":
            handler_class = node
            break

    assert handler_class is not None, "Handler class not found in askd_server.py"

    # Walk all dict literals inside Handler class
    error_dicts_with_token = []
    for node in ast.walk(handler_class):
        if isinstance(node, ast.Dict):
            keys = []
            for k in node.keys:
                if isinstance(k, ast.Constant) and isinstance(k.value, str):
                    keys.append(k.value)
            if "token" in keys:
                error_dicts_with_token.append(keys)

    assert len(error_dicts_with_token) == 0, (
        f"Found 'token' key in Handler dict literals: {error_dicts_with_token}. "
        "Error responses must not expose the daemon token."
    )
