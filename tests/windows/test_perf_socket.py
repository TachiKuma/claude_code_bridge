"""Socket communication efficiency tests (WIN-01).

Tests socket connect latency, request-response round-trip, unauthorized
rejection speed, and concurrent request handling.
"""

import concurrent.futures
import json
import os
import socket
import time

import pytest


@pytest.fixture
def daemon_state(daemon_proc):
    """Read daemon state for socket tests; skip if unavailable."""
    proc, state_file, tmp_dir, env = daemon_proc
    if state_file is None or not state_file.exists():
        pytest.skip("Daemon state file not available")
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
        return state
    except Exception as exc:
        pytest.skip(f"Failed to read daemon state: {exc}")


def _make_ping_request(token: str) -> str:
    """Build a JSON ping request string."""
    return json.dumps({
        "type": "ask.ping",
        "v": 1,
        "id": "socket-perf-test",
        "token": token,
    }) + "\n"


def _send_and_receive(host: str, port: int, message: str, timeout: float = 2.0) -> tuple[bytes, float]:
    """Send a message over socket and return (response_bytes, elapsed_time)."""
    start = time.perf_counter()
    with socket.create_connection((host, port), timeout=timeout) as sock:
        sock.sendall(message.encode("utf-8"))
        buf = b""
        deadline = time.time() + timeout
        while b"\n" not in buf and time.time() < deadline:
            chunk = sock.recv(1024)
            if not chunk:
                break
            buf += chunk
    elapsed = time.perf_counter() - start
    return buf, elapsed


@pytest.mark.windows
@pytest.mark.perf
class TestSocketConnectLatency:
    """Test 1: socket connect latency."""

    def test_socket_connect_latency(self, daemon_state):
        """Socket connect to daemon should complete within 100ms on localhost."""
        state = daemon_state
        host = state.get("connect_host") or state.get("host", "127.0.0.1")
        port = int(state["port"])

        start = time.perf_counter()
        sock = socket.create_connection((host, port), timeout=2.0)
        elapsed = time.perf_counter() - start
        sock.close()

        assert elapsed < 0.1, f"socket connect took {elapsed:.3f}s (limit: 100ms)"


@pytest.mark.windows
@pytest.mark.perf
class TestSocketRequestResponseLatency:
    """Test 2: socket request-response round-trip."""

    def test_socket_request_response_latency(self, daemon_state):
        """Ping round-trip should complete within 500ms."""
        state = daemon_state
        host = state.get("connect_host") or state.get("host", "127.0.0.1")
        port = int(state["port"])
        token = state["token"]

        req = _make_ping_request(token)
        buf, elapsed = _send_and_receive(host, port, req, timeout=2.0)

        assert b"\n" in buf, f"No response received within 2s"
        line = buf.split(b"\n", 1)[0].decode("utf-8", errors="replace")
        resp = json.loads(line)
        assert resp.get("exit_code") == 0, f"Ping failed: {resp}"

        assert elapsed < 0.5, f"ping round-trip took {elapsed:.3f}s (limit: 500ms)"


@pytest.mark.windows
@pytest.mark.perf
class TestSocketUnauthorizedRejection:
    """Test 3: unauthorized requests are rejected fast."""

    def test_socket_unauthorized_rejected_fast(self, daemon_state):
        """Request with wrong token should be rejected within 100ms."""
        state = daemon_state
        host = state.get("connect_host") or state.get("host", "127.0.0.1")
        port = int(state["port"])

        # Send with wrong token
        req = json.dumps({
            "type": "ask.ping",
            "v": 1,
            "id": "unauth-test",
            "token": "wrong-token-00000000000000",
        }) + "\n"

        buf, elapsed = _send_and_receive(host, port, req, timeout=2.0)

        assert b"\n" in buf, "No response received for unauthorized request"
        line = buf.split(b"\n", 1)[0].decode("utf-8", errors="replace")
        resp = json.loads(line)
        assert resp.get("reply") == "Unauthorized", f"Expected 'Unauthorized', got: {resp.get('reply')}"

        assert elapsed < 0.1, f"unauthorized rejection took {elapsed:.3f}s (limit: 100ms)"


@pytest.mark.windows
@pytest.mark.perf
class TestConcurrentRequests:
    """Test 4: concurrent request handling."""

    def test_concurrent_requests_handling(self, daemon_state):
        """5 concurrent ping requests should all get responses."""
        state = daemon_state
        host = state.get("connect_host") or state.get("host", "127.0.0.1")
        port = int(state["port"])
        token = state["token"]

        results = []

        def send_ping(idx: int) -> dict:
            req = json.dumps({
                "type": "ask.ping",
                "v": 1,
                "id": f"concurrent-{idx}",
                "token": token,
            }) + "\n"
            buf, elapsed = _send_and_receive(host, port, req, timeout=3.0)
            has_response = b"\n" in buf
            line = buf.split(b"\n", 1)[0].decode("utf-8", errors="replace") if has_response else ""
            try:
                resp = json.loads(line) if has_response else {}
            except Exception:
                resp = {}
            return {"idx": idx, "elapsed": elapsed, "ok": has_response, "exit_code": resp.get("exit_code")}

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(send_ping, i) for i in range(5)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All 5 should receive responses
        assert len(results) == 5, f"Expected 5 results, got {len(results)}"
        assert all(r["ok"] for r in results), "Not all concurrent requests received responses"
        assert all(r["exit_code"] == 0 for r in results), "Not all pings returned exit_code 0"

        # No individual request should take > 1s
        max_latency = max(r["elapsed"] for r in results)
        assert max_latency < 1.0, f"max concurrent latency {max_latency:.3f}s (limit: 1s)"
