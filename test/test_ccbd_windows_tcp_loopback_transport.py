from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import json
import socket
import time

import pytest

from ccbd.api_models import RpcRequest
from ccbd.control_plane_transport.endpoint import endpoint_from_record, endpoint_to_record
from ccbd.control_plane_transport.endpoint_store import endpoint_store_path, read_endpoint, unlink_endpoint, write_endpoint
from ccbd.control_plane_transport.factory import transport_for_legacy_socket_path
from ccbd.control_plane_transport.token_auth import RpcTransportAuthError, create_token_file, _current_windows_user
from ccbd.control_plane_transport.windows_tcp import WindowsTcpControlPlaneTransport
from ccbd.socket_client_runtime import decode_response, recv_response_line, send_request
from ccbd.socket_server import CcbdSocketServer
from ccbd.socket_server_runtime.loop import enqueue_connection, start_worker, stop_worker


def _ok_runner(command, **kwargs):
    del kwargs
    if command[:3] == ['powershell', '-NoProfile', '-Command']:
        owner = _current_windows_user() or 'DESKTOP\\User'
        owner_sid = 'S-1-5-21-1'
        if 'WindowsIdentity' in command[3]:
            return SimpleNamespace(returncode=0, stdout=owner_sid, stderr='')
        if 'Get-Acl' in command[3]:
            payload = {
                'owner': owner,
                'sddl': f'O:{owner_sid}G:{owner_sid}D:',
                'access': [
                    {
                        'identity': owner,
                        'rights': 'Read',
                        'access_type': 'Allow',
                        'inherited': False,
                    }
                ],
            }
            return SimpleNamespace(returncode=0, stdout=json.dumps(payload), stderr='')
    return SimpleNamespace(returncode=0, stdout='ok', stderr='')


def _failing_runner(command, **kwargs):
    del command, kwargs
    return SimpleNamespace(returncode=1, stdout='', stderr='access denied')


def _windows_acl_runner(*, owner: str, owner_sid: str, access: list[dict]):
    def runner(command, **kwargs):
        del kwargs
        if command[:3] == ['powershell', '-NoProfile', '-Command'] and 'WindowsIdentity' in command[3]:
            return SimpleNamespace(returncode=0, stdout=owner_sid, stderr='')
        if command[:3] == ['powershell', '-NoProfile', '-Command'] and 'Get-Acl' in command[3]:
            payload = {
                'owner': owner,
                'sddl': f'O:{owner_sid}G:{owner_sid}D:',
                'access': access,
            }
            return SimpleNamespace(returncode=0, stdout=json.dumps(payload), stderr='')
        return SimpleNamespace(returncode=0, stdout='ok', stderr='')

    return runner


def test_factory_selects_windows_tcp_for_legacy_socket_path(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr('ccbd.control_plane_transport.factory.os.name', 'nt')
    write_endpoint(
        endpoint_from_record(
            {
                'kind': 'tcp_loopback',
                'host': '127.0.0.1',
                'port': 32123,
                'token_ref': str(tmp_path / 'token.json'),
                'generation': 'gen-1',
                'acl_status': 'windows-icacls-user-read',
                'fingerprint': 'deadbeefcafebabe',
            }
        ),
        legacy_socket_path=tmp_path / 'ccbd.sock',
    )

    transport = transport_for_legacy_socket_path(tmp_path / 'ccbd.sock')

    assert isinstance(transport, WindowsTcpControlPlaneTransport)


def test_socket_server_prefers_windows_tcp_without_endpoint_descriptor(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr('ccbd.control_plane_transport.factory.os.name', 'nt')
    monkeypatch.setattr('ccbd.socket_server_runtime.server.os.name', 'nt')

    server = CcbdSocketServer(tmp_path / 'ccbd.sock')

    assert isinstance(server._control_plane_transport, WindowsTcpControlPlaneTransport)
    assert server._control_plane_transport.endpoint is None


def test_tcp_endpoint_record_roundtrips_without_legacy_socket_path() -> None:
    endpoint = endpoint_from_record(
        {
            'kind': 'tcp_loopback',
            'host': '127.0.0.1',
            'port': 32123,
            'token_ref': 'C:/runtime/token.json',
            'generation': 'gen-1',
            'acl_status': 'windows-icacls-user-read',
            'fingerprint': 'deadbeefcafebabe',
        }
    )

    record = endpoint_to_record(endpoint)

    assert record['kind'] == 'tcp_loopback'
    assert record['address'] == '127.0.0.1:32123'
    assert record['legacy_socket_path'] is None
    assert record['token_ref'] == 'C:/runtime/token.json'
    assert record['auth_ref'] == 'C:/runtime/token.json'
    assert record['fingerprint'] == 'deadbeefcafebabe'


def test_create_token_file_fails_fast_when_acl_cannot_be_proven(tmp_path: Path) -> None:
    token_path = tmp_path / 'token.json'
    with pytest.raises(RpcTransportAuthError) as error:
        create_token_file(
            token_path,
            command_runner=_failing_runner,
            os_name='nt',
        )

    assert error.value.category == 'token-unprotectable'
    assert not token_path.exists()


def test_create_token_file_proves_acl_convergence(tmp_path: Path, monkeypatch) -> None:
    token_path = tmp_path / 'token.json'
    runner = _windows_acl_runner(
        owner='DESKTOP\\User',
        owner_sid='S-1-5-21-1',
        access=[
            {
                'identity': 'DESKTOP\\User',
                'rights': 'Read',
                'access_type': 'Allow',
                'inherited': False,
            }
        ],
    )
    monkeypatch.setattr('ccbd.control_plane_transport.token_auth._current_windows_user', lambda: 'DESKTOP\\User')

    token_file = create_token_file(
        token_path,
        command_runner=runner,
        os_name='nt',
    )

    assert token_file.acl_status == 'windows-icacls-user-read'
    assert token_path.exists()


def test_create_token_file_fails_when_acl_proof_contains_unexpected_principal(tmp_path: Path, monkeypatch) -> None:
    token_path = tmp_path / 'token.json'
    runner = _windows_acl_runner(
        owner='DESKTOP\\User',
        owner_sid='S-1-5-21-1',
        access=[
            {
                'identity': 'DESKTOP\\User',
                'rights': 'Read',
                'access_type': 'Allow',
                'inherited': False,
            },
            {
                'identity': 'Everyone',
                'rights': 'Read',
                'access_type': 'Allow',
                'inherited': False,
            },
        ],
    )
    monkeypatch.setattr('ccbd.control_plane_transport.token_auth._current_windows_user', lambda: 'DESKTOP\\User')

    with pytest.raises(RpcTransportAuthError) as error:
        create_token_file(
            token_path,
            command_runner=runner,
            os_name='nt',
        )

    assert error.value.category == 'token-unprotectable'
    assert not token_path.exists()


def test_tcp_listener_publishes_endpoint_and_roundtrips_ping(tmp_path: Path) -> None:
    transport = WindowsTcpControlPlaneTransport(
        None,
        legacy_socket_path=tmp_path / 'ccbd.sock',
        command_runner=_ok_runner,
    )
    server = CcbdSocketServer(tmp_path / 'ccbd.sock', control_plane_transport=transport)
    server.register_handler('ping', lambda payload: {'echo': payload})
    server.listen()
    try:
        endpoint = read_endpoint(tmp_path / 'ccbd.sock')
        assert endpoint is not None
        assert endpoint['kind'] == 'tcp_loopback'
        assert endpoint['host'] == '127.0.0.1'
        assert int(endpoint['port']) > 0
        assert endpoint['legacy_socket_path'] is None
        assert endpoint['token_ref'] == endpoint['auth_ref']
        assert endpoint['fingerprint']
        assert server.control_plane_endpoint['fingerprint'] == endpoint['fingerprint']

        client = transport.connect(timeout_s=1.0)
        send_request(client, RpcRequest(op='ping', request={'target': 'ccbd'}))
        accepted, peer = server._server.accept()
        assert peer['kind'] == 'tcp_loopback_token'
        start_worker(server, interval=0.0, on_tick=None)
        enqueue_connection(server, accepted)

        response = _wait_for_response(client)

        assert response.ok is True
        assert response.payload['echo'] == {'target': 'ccbd'}
    finally:
        try:
            client.close()
        except Exception:
            pass
        stop_worker(server)
        server.shutdown()


def test_bad_tcp_token_is_not_accepted_by_listener(tmp_path: Path) -> None:
    transport = WindowsTcpControlPlaneTransport(
        None,
        legacy_socket_path=tmp_path / 'ccbd.sock',
        command_runner=_ok_runner,
    )
    listener = transport.listen()
    listener.settimeout(0.2)
    raw = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        raw.connect(('127.0.0.1', int(listener.endpoint['port'])))
        raw.sendall(
            json.dumps(
                {
                    'schema': 'ccbd-control-plane-token-v1',
                    'token': 'wrong-token',
                }
            ).encode('utf-8')
            + b'\n'
        )

        with pytest.raises(TimeoutError):
            listener.accept()
    finally:
        raw.close()
        listener.close()
        transport.unlink_bound_endpoint(bound_identity=listener.bound_socket_stat)


def test_tcp_bootstrap_probe_uses_authenticated_loopback_path(tmp_path: Path) -> None:
    transport = WindowsTcpControlPlaneTransport(
        None,
        legacy_socket_path=tmp_path / 'ccbd.sock',
        command_runner=_ok_runner,
    )
    server = CcbdSocketServer(tmp_path / 'ccbd.sock', control_plane_transport=transport)
    seen: list[str] = []

    def _handle_ping(payload):
        nonce = str(payload.get('bootstrap_probe_nonce') or '')
        seen.append(nonce)
        return {'bootstrap_probe_nonce': nonce, 'identity': 'tcp-loopback'}

    server.register_handler('ping', _handle_ping)
    server.listen()
    try:
        with server.bootstrap_readiness_probe(timeout_s=1.0) as payload:
            assert payload['identity'] == 'tcp-loopback'
            assert payload['bootstrap_probe_nonce'] == seen[0]
            assert server._bootstrap_probe_active is True

        assert server._bootstrap_probe_active is False
        assert server._stop_event.is_set() is False
    finally:
        server.shutdown()


def test_shutdown_removes_only_current_endpoint_generation(tmp_path: Path) -> None:
    legacy_socket_path = tmp_path / 'ccbd.sock'
    transport = WindowsTcpControlPlaneTransport(
        None,
        legacy_socket_path=legacy_socket_path,
        command_runner=_ok_runner,
    )
    listener = transport.listen()
    path = endpoint_store_path(legacy_socket_path)
    assert path.exists()
    assert legacy_socket_path.exists()

    stale_identity = ('other-generation', listener.bound_socket_stat[1])
    transport.unlink_bound_endpoint(bound_identity=stale_identity)
    assert path.exists()
    assert legacy_socket_path.exists()

    listener.close()
    transport.unlink_bound_endpoint(bound_identity=listener.bound_socket_stat)
    assert not path.exists()
    assert not legacy_socket_path.exists()


def test_listen_failure_after_endpoint_publish_keeps_preexisting_marker(monkeypatch, tmp_path: Path) -> None:
    legacy_socket_path = tmp_path / 'ccbd.sock'
    legacy_socket_path.parent.mkdir(parents=True, exist_ok=True)
    legacy_socket_path.write_text('preexisting-marker', encoding='utf-8')
    transport = WindowsTcpControlPlaneTransport(
        None,
        legacy_socket_path=legacy_socket_path,
        command_runner=_ok_runner,
    )

    def _fail_marker(path):
        del path
        raise RuntimeError('marker touch failed')

    monkeypatch.setattr('ccbd.control_plane_transport.windows_tcp.touch_legacy_socket_marker', _fail_marker)

    with pytest.raises(RuntimeError, match='marker touch failed'):
        transport.listen()

    assert legacy_socket_path.exists()
    assert legacy_socket_path.read_text(encoding='utf-8') == 'preexisting-marker'
    assert not endpoint_store_path(legacy_socket_path).exists()
    assert list(tmp_path.glob('control-plane-token-*.json')) == []


def test_unlink_bound_endpoint_skips_when_generation_is_missing(tmp_path: Path) -> None:
    legacy_socket_path = tmp_path / 'ccbd.sock'
    transport = WindowsTcpControlPlaneTransport(
        None,
        legacy_socket_path=legacy_socket_path,
        command_runner=_ok_runner,
    )
    listener = transport.listen()
    path = endpoint_store_path(legacy_socket_path)

    transport.unlink_bound_endpoint(bound_identity=None)

    assert path.exists()
    assert legacy_socket_path.exists()

    listener.close()
    transport.unlink_bound_endpoint(bound_identity=listener.bound_socket_stat)
    assert not path.exists()
    assert not legacy_socket_path.exists()


def test_unlink_bound_endpoint_cleans_owned_token_when_generation_mismatches(tmp_path: Path) -> None:
    legacy_socket_path = tmp_path / 'ccbd.sock'
    transport = WindowsTcpControlPlaneTransport(
        None,
        legacy_socket_path=legacy_socket_path,
        command_runner=_ok_runner,
    )
    listener = transport.listen()
    path = endpoint_store_path(legacy_socket_path)
    token_ref = Path(listener.bound_socket_stat[1])
    assert path.exists()
    assert token_ref.exists()
    assert legacy_socket_path.exists()

    transport.unlink_bound_endpoint(
        bound_identity=('other-generation', listener.bound_socket_stat[1], listener.bound_socket_stat[2])
    )

    assert path.exists()
    assert not token_ref.exists()
    assert legacy_socket_path.exists()

    listener.close()
    transport.unlink_bound_endpoint(bound_identity=listener.bound_socket_stat)
    assert not path.exists()
    assert not legacy_socket_path.exists()


def test_unlink_bound_endpoint_cleans_owned_token_when_endpoint_is_missing(tmp_path: Path) -> None:
    legacy_socket_path = tmp_path / 'ccbd.sock'
    transport = WindowsTcpControlPlaneTransport(
        None,
        legacy_socket_path=legacy_socket_path,
        command_runner=_ok_runner,
    )
    listener = transport.listen()
    path = endpoint_store_path(legacy_socket_path)
    token_ref = Path(listener.bound_socket_stat[1])
    assert path.exists()
    assert token_ref.exists()
    assert legacy_socket_path.exists()
    path.unlink()

    transport.unlink_bound_endpoint(bound_identity=listener.bound_socket_stat)

    assert not token_ref.exists()
    assert legacy_socket_path.exists()

    listener.close()
    legacy_socket_path.unlink()


def test_unlink_endpoint_skips_when_generation_is_missing(tmp_path: Path) -> None:
    legacy_socket_path = tmp_path / 'ccbd.sock'
    endpoint = endpoint_from_record(
        {
            'kind': 'tcp_loopback',
            'host': '127.0.0.1',
            'port': 32123,
            'token_ref': str(tmp_path / 'token.json'),
            'generation': 'gen-1',
            'acl_status': 'windows-icacls-user-read',
            'fingerprint': 'deadbeefcafebabe',
        }
    )
    write_endpoint(endpoint, legacy_socket_path=legacy_socket_path)

    endpoint_store_path_value = endpoint_store_path(legacy_socket_path)
    assert endpoint_store_path_value.exists()

    assert unlink_endpoint(legacy_socket_path=legacy_socket_path, expected_generation=None) is False
    assert endpoint_store_path_value.exists()

    assert unlink_endpoint(legacy_socket_path=legacy_socket_path, expected_generation='gen-mismatch') is False
    assert endpoint_store_path_value.exists()

    assert unlink_endpoint(legacy_socket_path=legacy_socket_path, expected_generation='gen-1') is True
    assert not endpoint_store_path_value.exists()


def _wait_for_response(client):
    deadline = time.monotonic() + 2.0
    raw = b''
    while b'\n' not in raw and time.monotonic() < deadline:
        raw = recv_response_line(client)
        if not raw:
            time.sleep(0.01)
    assert raw
    return decode_response(raw)
