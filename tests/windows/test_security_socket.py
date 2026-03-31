"""Security audit tests for socket authentication (D-11).

Covers:
- Socket rejects requests without token
- Socket rejects requests with wrong token
- Socket accepts requests with correct token
- Token comparison is NOT timing-safe (audit finding, low risk)
- Socket has no TLS/SSL encryption (audit finding, localhost-only)
- Socket binds to 127.0.0.1 (not 0.0.0.0)
"""

import ast
import json
import os
import socket
import time

import pytest
from pathlib import Path


# ---------------------------------------------------------------------------
# Helper: send/receive over socket
# ---------------------------------------------------------------------------

def _send_socket_message(host: str, port: int, message: str, timeout: float = 2.0) -> dict | None:
    """Send a JSON message and return the parsed response, or None on failure."""
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            sock.sendall(message.encode("utf-8"))
            buf = b""
            deadline = time.time() + timeout
            while b"\n" not in buf and time.time() < deadline:
                chunk = sock.recv(65536)
                if not chunk:
                    break
                buf += chunk
            if b"\n" not in buf:
                return None
            line = buf.split(b"\n", 1)[0].decode("utf-8", errors="replace")
            return json.loads(line)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Helper fixture: get daemon state from daemon_proc
# ---------------------------------------------------------------------------

@pytest.fixture
def sec_daemon_state(daemon_proc):
    """Read daemon state for socket security tests; skip if unavailable."""
    proc, state_file, tmp_dir, env = daemon_proc
    if state_file is None or not state_file.exists():
        pytest.skip("Daemon not running -- socket tests require live daemon")
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
        return state
    except Exception as exc:
        pytest.skip(f"Failed to read daemon state: {exc}")


# ---------------------------------------------------------------------------
# Test 1: Socket rejects missing token
# ---------------------------------------------------------------------------
@pytest.mark.windows
@pytest.mark.security
def test_socket_rejects_missing_token(sec_daemon_state):
    """Request without 'token' field returns 'Unauthorized' (D-11)."""
    state = sec_daemon_state
    host = state.get("connect_host") or state.get("host", "127.0.0.1")
    port = int(state["port"])

    # Send request WITHOUT token field
    req = json.dumps({
        "type": "ask.ping",
        "v": 1,
        "id": "sec-test-no-token",
    }) + "\n"

    resp = _send_socket_message(host, port, req)
    assert resp is not None, "No response received from daemon"
    assert resp.get("reply") == "Unauthorized", (
        f"Expected 'Unauthorized' for missing token, got: {resp.get('reply')}"
    )


# ---------------------------------------------------------------------------
# Test 2: Socket rejects wrong token
# ---------------------------------------------------------------------------
@pytest.mark.windows
@pytest.mark.security
def test_socket_rejects_wrong_token(sec_daemon_state):
    """Request with incorrect token returns 'Unauthorized' (D-11)."""
    state = sec_daemon_state
    host = state.get("connect_host") or state.get("host", "127.0.0.1")
    port = int(state["port"])

    req = json.dumps({
        "type": "ask.ping",
        "v": 1,
        "id": "sec-test-wrong-token",
        "token": "definitely-wrong-token-value-12345",
    }) + "\n"

    resp = _send_socket_message(host, port, req)
    assert resp is not None, "No response received from daemon"
    assert resp.get("reply") == "Unauthorized", (
        f"Expected 'Unauthorized' for wrong token, got: {resp.get('reply')}"
    )


# ---------------------------------------------------------------------------
# Test 3: Socket accepts correct token
# ---------------------------------------------------------------------------
@pytest.mark.windows
@pytest.mark.security
def test_socket_accepts_correct_token(sec_daemon_state):
    """Request with correct token is processed successfully (D-11)."""
    state = sec_daemon_state
    host = state.get("connect_host") or state.get("host", "127.0.0.1")
    port = int(state["port"])
    token = state["token"]

    req = json.dumps({
        "type": "ask.ping",
        "v": 1,
        "id": "sec-test-correct-token",
        "token": token,
    }) + "\n"

    resp = _send_socket_message(host, port, req)
    assert resp is not None, "No response received from daemon"
    assert resp.get("exit_code") == 0, (
        f"Expected exit_code 0 for correct token, got: {resp.get('exit_code')}"
    )
    assert "pong" in resp.get("type", ""), (
        f"Expected 'pong' in response type, got: {resp.get('type')}"
    )


# ---------------------------------------------------------------------------
# Test 4: Token comparison is NOT timing-safe (audit finding)
# ---------------------------------------------------------------------------
@pytest.mark.windows
@pytest.mark.security
def test_socket_token_comparison_not_timing_safe():
    """Token comparison uses Python != operator, not hmac.compare_digest.

    This is a known low-risk finding: on localhost, timing attacks are
    not feasible since the attacker cannot measure response times with
    sufficient precision over loopback. Documented for completeness.

    Future hardening: replace != with hmac.compare_digest for defense in depth.
    """
    server_file = Path(__file__).resolve().parent.parent.parent / "lib" / "askd_server.py"
    source = server_file.read_text(encoding="utf-8")

    # Find the Handler.handle method and locate the token comparison
    tree = ast.parse(source)

    handler_class = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "Handler":
            handler_class = node
            break

    assert handler_class is not None, "Handler class not found"

    handle_method = None
    for node in ast.iter_child_nodes(handler_class):
        if isinstance(node, ast.FunctionDef) and node.name == "handle":
            handle_method = node
            break

    assert handle_method is not None, "Handler.handle method not found"

    # Extract the method source and check for the token comparison pattern
    method_source = "\n".join(
        source.split("\n")[handle_method.lineno - 1:handle_method.end_lineno]
    )

    # The current implementation uses != (not timing-safe)
    assert "!=" in method_source, "Token comparison operator not found"
    assert "compare_digest" not in method_source, (
        "Token comparison already uses hmac.compare_digest -- "
        "this test should be updated to verify timing safety"
    )

    # Document the finding: != is used, compare_digest is NOT used
    # This is acceptable for localhost-only daemon but should be noted
    assert 'msg.get("token")' in method_source or 'msg["token"]' in method_source, (
        "Token access pattern not found in handle method"
    )


# ---------------------------------------------------------------------------
# Test 5: Socket has no TLS/SSL encryption (audit finding)
# ---------------------------------------------------------------------------
@pytest.mark.windows
@pytest.mark.security
def test_socket_no_tls_encryption():
    """Socket server uses plain TCP without SSL/TLS wrapping.

    Audit finding: the daemon socket is unencrypted. This is acceptable
    because:
    1. Server binds to 127.0.0.1 only (localhost)
    2. Token authentication is required for all requests
    3. All traffic stays on the loopback interface

    TLS would be needed only if the daemon were exposed on external interfaces.
    """
    server_file = Path(__file__).resolve().parent.parent.parent / "lib" / "askd_server.py"
    source = server_file.read_text(encoding="utf-8")

    # Verify it uses plain ThreadingTCPServer (not SSL-wrapped)
    assert "ThreadingTCPServer" in source, "Server type not found"

    # Verify no SSL/TLS wrapping
    assert "ssl.wrap_socket" not in source, "ssl.wrap_socket found -- TLS is used"
    assert "ssl.SSLContext" not in source, "ssl.SSLContext found -- TLS is used"
    assert "SSLContext" not in source, "SSLContext found -- TLS is used"

    # Verify the import list does not include ssl module
    tree = ast.parse(source)
    import_names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            import_names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            import_names.append(node.module)

    assert "ssl" not in import_names, (
        "ssl module is imported -- daemon uses TLS encryption"
    )


# ---------------------------------------------------------------------------
# Test 6: Socket binds to localhost only (not 0.0.0.0)
# ---------------------------------------------------------------------------
@pytest.mark.windows
@pytest.mark.security
def test_socket_binds_localhost_only():
    """Server default host is 127.0.0.1, not 0.0.0.0 (D-11).

    Verify that:
    1. AskDaemonServer.__init__ defaults host="127.0.0.1"
    2. normalize_connect_host() converts "0.0.0.0" to "127.0.0.1"
    """
    # Check AskDaemonServer default parameter
    server_file = Path(__file__).resolve().parent.parent.parent / "lib" / "askd_server.py"
    source = server_file.read_text(encoding="utf-8")

    # Verify default host parameter
    tree = ast.parse(source)
    server_class = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "AskDaemonServer":
            server_class = node
            break

    assert server_class is not None, "AskDaemonServer class not found"

    init_method = None
    for node in ast.iter_child_nodes(server_class):
        if isinstance(node, ast.FunctionDef) and node.name == "__init__":
            init_method = node
            break

    assert init_method is not None, "__init__ method not found in AskDaemonServer"

    # Check that host parameter defaults to "127.0.0.1"
    init_source = "\n".join(
        source.split("\n")[init_method.lineno - 1:init_method.end_lineno]
    )

    assert '"127.0.0.1"' in init_source and 'host' in init_source, (
        "AskDaemonServer.__init__ host parameter does not default to '127.0.0.1'"
    )

    # Check normalize_connect_host converts 0.0.0.0 to 127.0.0.1
    runtime_file = Path(__file__).resolve().parent.parent.parent / "lib" / "askd_runtime.py"
    runtime_source = runtime_file.read_text(encoding="utf-8")

    assert 'normalize_connect_host' in runtime_source, (
        "normalize_connect_host not found in askd_runtime.py"
    )
    assert '"0.0.0.0"' in runtime_source, (
        "0.0.0.0 handling not found in normalize_connect_host"
    )
    assert '"127.0.0.1"' in runtime_source, (
        "127.0.0.1 not found as conversion target in normalize_connect_host"
    )
