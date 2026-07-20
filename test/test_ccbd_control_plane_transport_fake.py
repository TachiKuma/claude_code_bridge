from __future__ import annotations

import json
import time

from ccbd.api_models import RpcRequest
from ccbd.control_plane_transport.fake import FakeConnection, FakeControlPlaneTransport
from ccbd.socket_server import CcbdSocketServer
from ccbd.socket_server_runtime.loop import enqueue_connection, start_worker, stop_worker
from ccbd.socket_client_runtime import decode_response, recv_response_line, send_request


def test_fake_transport_listen_request_and_shutdown_roundtrip() -> None:
    transport = FakeControlPlaneTransport()
    server = CcbdSocketServer('fake://ccbd.sock', control_plane_transport=transport)
    calls: list[dict] = []
    server.register_handler('ping', lambda payload: calls.append(payload) or {'ok': True, 'echo': payload})

    server.listen()
    try:
        connection = FakeConnection()
        request = RpcRequest(op='ping', request={'target': 'ccbd'})
        connection.push_recv((json.dumps(request.to_record()) + '\n').encode('utf-8'))
        transport.listener.enqueue(connection)
        accepted, peer = server._server.accept()
        assert peer['kind'] == 'fake'
        start_worker(server, interval=0.0, on_tick=None)
        enqueue_connection(server, accepted)
        deadline = time.monotonic() + 2.0
        while (
            (not calls or not connection.closed or b'"ok": true' not in bytes(connection.sent))
            and time.monotonic() < deadline
        ):
            time.sleep(0.01)

        assert calls == [{'target': 'ccbd'}]
        assert connection.closed is True
        assert b'"ok": true' in bytes(connection.sent)
    finally:
        stop_worker(server)
        server.shutdown()


def test_fake_bootstrap_probe_roundtrip() -> None:
    from ccbd.handlers.ping_runtime.handler import _bootstrap_probe_nonce

    transport = FakeControlPlaneTransport()
    server = CcbdSocketServer('fake://ccbd.sock', control_plane_transport=transport)
    seen: list[str] = []

    def _handle_ping(payload):
        nonce = _bootstrap_probe_nonce(payload)
        seen.append(str(payload.get('bootstrap_probe_nonce') or ''))
        return {'bootstrap_probe_nonce': nonce}

    server.register_handler('ping', _handle_ping)
    server.listen()
    try:
        with server.bootstrap_readiness_probe(timeout_s=0.5) as payload:
            assert payload['bootstrap_probe_nonce'] == seen[0]
            assert len(seen[0]) == 32
    finally:
        server.shutdown()


def test_fake_transport_connect_pairs_client_with_listener() -> None:
    transport = FakeControlPlaneTransport()
    server = CcbdSocketServer('fake://ccbd.sock', control_plane_transport=transport)
    server.register_handler('ping', lambda payload: {'echo': payload})
    server.listen()
    try:
        client = transport.connect(timeout_s=1.0)
        send_request(client, RpcRequest(op='ping', request={'target': 'ccbd'}))
        accepted, _ = server._server.accept()
        start_worker(server, interval=0.0, on_tick=None)
        enqueue_connection(server, accepted)

        deadline = time.monotonic() + 2.0
        raw = b''
        while b'\n' not in raw and time.monotonic() < deadline:
            raw = recv_response_line(client)
            if not raw:
                time.sleep(0.01)

        response = decode_response(raw)

        assert response.ok is True
        assert response.payload['echo'] == {'target': 'ccbd'}
    finally:
        stop_worker(server)
        server.shutdown()


def test_fake_listener_timeout_semantics() -> None:
    transport = FakeControlPlaneTransport()
    listener = transport.listener
    listener.settimeout(0)

    try:
        listener.accept()
    except TimeoutError:
        pass
    else:
        raise AssertionError('non-blocking fake listener should time out without a pending connection')

    listener.enqueue(FakeConnection())
    conn, peer = listener.accept()

    assert isinstance(conn, FakeConnection)
    assert peer['kind'] == 'fake'


def test_fake_transport_rejects_connect_after_listener_close() -> None:
    transport = FakeControlPlaneTransport()
    transport.listener.close()

    assert transport.is_connectable() is False
    try:
        transport.listener.accept()
    except OSError:
        pass
    else:
        raise AssertionError('closed fake listener should reject accept')

    try:
        transport.connect(timeout_s=0.1)
    except OSError:
        pass
    else:
        raise AssertionError('closed fake transport should reject new connections')


def test_fake_connection_recv_returns_eof_after_peer_close() -> None:
    transport = FakeControlPlaneTransport()
    client = transport.connect(timeout_s=0.1)
    server_conn, _ = transport.listener.accept()

    server_conn.close()

    assert client.recv(65536) == b''
