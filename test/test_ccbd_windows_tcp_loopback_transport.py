from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import json
import socket
import threading
import time

import pytest

from ccbd.api_models import RpcRequest
from ccbd.control_plane_transport.endpoint import endpoint_from_record, endpoint_to_record
from ccbd.control_plane_transport.endpoint_store import endpoint_store_path, read_endpoint, unlink_endpoint, write_endpoint
from ccbd.control_plane_transport.factory import connect_endpoint, transport_for_legacy_socket_path
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
        if _is_acl_proof_command(command[3]):
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
        if command[:3] == ['powershell', '-NoProfile', '-Command'] and _is_acl_proof_command(command[3]):
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


def test_create_token_file_accepts_admin_owner_when_acl_is_current_user_only(tmp_path: Path, monkeypatch) -> None:
    token_path = tmp_path / 'token.json'
    runner = _windows_acl_runner(
        owner='BUILTIN\\Administrators',
        owner_sid='S-1-5-32-544',
        access=[
            {
                'identity': 'DESKTOP\\User',
                'rights': 'Read, Synchronize',
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

        accepted_result = {}
        accept_thread = threading.Thread(
            target=lambda: accepted_result.update(zip(('conn', 'peer'), server._server.accept())),
            daemon=True,
        )
        accept_thread.start()
        client = transport.connect(timeout_s=1.0)
        accept_thread.join(timeout=1.0)
        assert 'conn' in accepted_result
        send_request(client, RpcRequest(op='ping', request={'target': 'ccbd'}))
        accepted = accepted_result['conn']
        peer = accepted_result['peer']
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


def test_bad_tcp_token_fails_during_client_connect(tmp_path: Path) -> None:
    transport = WindowsTcpControlPlaneTransport(
        None,
        legacy_socket_path=tmp_path / 'ccbd.sock',
        command_runner=_ok_runner,
    )
    listener = transport.listen()
    listener.settimeout(0.2)
    token_path = Path(listener.bound_socket_stat[1])
    payload = json.loads(token_path.read_text(encoding='utf-8'))
    payload['token'] = 'wrong-token'
    token_path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True) + '\n', encoding='utf-8')
    accept_errors: list[BaseException] = []
    accept_thread = threading.Thread(
        target=lambda: accept_errors.append(_accept_until_timeout(listener)),
        daemon=True,
    )
    try:
        accept_thread.start()
        with pytest.raises(RpcTransportAuthError) as error:
            transport.connect(timeout_s=1.0)

        assert error.value.category == 'not-same-user'
        accept_thread.join(timeout=1.0)
        assert accept_errors and isinstance(accept_errors[0], TimeoutError)
    finally:
        listener.close()
        transport.unlink_bound_endpoint(bound_identity=listener.bound_socket_stat)


def test_windows_legacy_socket_path_rejects_non_tcp_endpoint_descriptor(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr('ccbd.control_plane_transport.factory.os.name', 'nt')
    endpoint_store_path(tmp_path / 'ccbd.sock').write_text(
        json.dumps(
            {
                'kind': 'unix_socket',
                'address': str(tmp_path / 'ccbd.sock'),
            },
            ensure_ascii=False,
        )
        + '\n',
        encoding='utf-8',
    )

    transport = transport_for_legacy_socket_path(tmp_path / 'ccbd.sock')

    with pytest.raises(RpcTransportAuthError) as error:
        transport.connect(timeout_s=0.1)

    assert error.value.category == 'endpoint-invalid'


@pytest.mark.parametrize(
    'descriptor',
    [
        {'kind': 'tcp_loopback', 'host': '127.0.0.1', 'port': 32123},
        {'kind': 'tcp_loopback', 'host': '127.0.0.1', 'port': 'bad', 'token_ref': 'token.json'},
        {'kind': 'tcp_loopback', 'host': '127.0.0.2', 'port': 32123, 'token_ref': 'token.json'},
        {'kind': 'tcp_loopback', 'address': '127.0.0.2:32123', 'token_ref': 'token.json'},
        {'kind': 'tcp_loopback', 'address': '127.0.0.1:70000', 'token_ref': 'token.json'},
    ],
)
def test_windows_legacy_socket_path_rejects_invalid_tcp_endpoint_descriptor(
    monkeypatch,
    tmp_path: Path,
    descriptor: dict,
) -> None:
    monkeypatch.setattr('ccbd.control_plane_transport.factory.os.name', 'nt')
    endpoint_store_path(tmp_path / 'ccbd.sock').write_text(
        json.dumps(descriptor, ensure_ascii=False) + '\n',
        encoding='utf-8',
    )

    transport = transport_for_legacy_socket_path(tmp_path / 'ccbd.sock')

    with pytest.raises(RpcTransportAuthError) as error:
        transport.connect(timeout_s=0.1)

    assert error.value.category == 'endpoint-invalid'


def test_windows_legacy_socket_path_rejects_malformed_endpoint_descriptor(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr('ccbd.control_plane_transport.factory.os.name', 'nt')
    endpoint_store_path(tmp_path / 'ccbd.sock').write_text(
        '{not-json',
        encoding='utf-8',
    )

    transport = transport_for_legacy_socket_path(tmp_path / 'ccbd.sock')

    with pytest.raises(RpcTransportAuthError) as error:
        transport.connect(timeout_s=0.1)

    assert error.value.category == 'endpoint-invalid'


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


def test_tcp_bootstrap_probe_ignores_slow_preauth_connection(tmp_path: Path) -> None:
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
    slow_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        slow_client.connect(('127.0.0.1', int(server.control_plane_endpoint['port'])))

        started = time.monotonic()
        with server.bootstrap_readiness_probe(timeout_s=1.0) as payload:
            assert payload['identity'] == 'tcp-loopback'
            assert payload['bootstrap_probe_nonce'] == seen[0]
        assert time.monotonic() - started < 0.8
    finally:
        slow_client.close()
        server.shutdown()


def test_tcp_bootstrap_probe_sends_request_before_enqueueing_worker_connection(
    monkeypatch,
    tmp_path: Path,
) -> None:
    import ccbd.socket_client_runtime as socket_client_runtime

    original_send_request = socket_client_runtime.send_request
    transport = WindowsTcpControlPlaneTransport(
        None,
        legacy_socket_path=tmp_path / 'ccbd.sock',
        command_runner=_ok_runner,
    )
    server = CcbdSocketServer(tmp_path / 'ccbd.sock', control_plane_transport=transport)

    def _handle_ping(payload):
        nonce = str(payload.get('bootstrap_probe_nonce') or '')
        return {'bootstrap_probe_nonce': nonce, 'identity': 'tcp-loopback'}

    def _delayed_send_request(sock, request):
        time.sleep(0.6)
        original_send_request(sock, request)

    monkeypatch.setattr(socket_client_runtime, 'send_request', _delayed_send_request)
    server.register_handler('ping', _handle_ping)
    server.listen()
    try:
        with server.bootstrap_readiness_probe(timeout_s=2.0) as payload:
            assert payload['identity'] == 'tcp-loopback'
    finally:
        server.shutdown()


def test_tcp_bootstrap_probe_recovers_after_bad_existing_endpoint_descriptor(tmp_path: Path) -> None:
    legacy_socket_path = tmp_path / 'ccbd.sock'
    endpoint_store_path(legacy_socket_path).write_text('{not-json', encoding='utf-8')
    transport = WindowsTcpControlPlaneTransport.from_legacy_socket_path(legacy_socket_path)
    transport._command_runner = _ok_runner
    server = CcbdSocketServer(legacy_socket_path, control_plane_transport=transport)

    def _handle_ping(payload):
        nonce = str(payload.get('bootstrap_probe_nonce') or '')
        return {'bootstrap_probe_nonce': nonce, 'identity': 'tcp-loopback'}

    server.register_handler('ping', _handle_ping)
    server.listen()
    try:
        with server.bootstrap_readiness_probe(timeout_s=1.0) as payload:
            assert payload['identity'] == 'tcp-loopback'
    finally:
        server.shutdown()


def test_tcp_bootstrap_probe_ignores_slow_drip_preauth_connection(tmp_path: Path) -> None:
    transport = WindowsTcpControlPlaneTransport(
        None,
        legacy_socket_path=tmp_path / 'ccbd.sock',
        command_runner=_ok_runner,
    )
    server = CcbdSocketServer(tmp_path / 'ccbd.sock', control_plane_transport=transport)

    def _handle_ping(payload):
        nonce = str(payload.get('bootstrap_probe_nonce') or '')
        return {'bootstrap_probe_nonce': nonce, 'identity': 'tcp-loopback'}

    server.register_handler('ping', _handle_ping)
    server.listen()
    slow_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    drip_errors: list[BaseException] = []

    def _drip_auth_bytes() -> None:
        try:
            for _ in range(8):
                slow_client.sendall(b'{')
                time.sleep(0.05)
        except BaseException as exc:
            drip_errors.append(exc)

    try:
        slow_client.connect(('127.0.0.1', int(server.control_plane_endpoint['port'])))
        drip_thread = threading.Thread(target=_drip_auth_bytes, daemon=True)
        drip_thread.start()

        started = time.monotonic()
        with server.bootstrap_readiness_probe(timeout_s=1.5) as payload:
            assert payload['identity'] == 'tcp-loopback'
        assert time.monotonic() - started < 1.2
        drip_thread.join(timeout=1.0)
    finally:
        slow_client.close()
        server.shutdown()


@pytest.mark.parametrize(
    'descriptor',
    [
        {'kind': 'tcp_loopback', 'host': '127.0.0.1', 'port': 'bad', 'token_ref': 'token.json'},
        {'kind': 'tcp_loopback', 'host': '127.0.0.1', 'port': 70000, 'token_ref': 'token.json'},
        {'kind': 'tcp_loopback', 'address': '127.0.0.1:70000', 'token_ref': 'token.json'},
    ],
)
def test_direct_tcp_endpoint_rejects_invalid_descriptor(monkeypatch, descriptor: dict) -> None:
    monkeypatch.setattr('ccbd.control_plane_transport.factory.os.name', 'nt')
    with pytest.raises(RpcTransportAuthError) as error:
        connect_endpoint(descriptor, timeout_s=0.1)

    assert error.value.category == 'endpoint-invalid'


@pytest.mark.parametrize(
    'descriptor',
    [
        {'kind': 'unix_socket', 'address': 'ccbd.sock'},
        {'kind': 'named_pipe', 'address': r'\\.\pipe\ccbd'},
    ],
)
def test_direct_windows_endpoint_rejects_non_tcp_descriptor(monkeypatch, descriptor: dict) -> None:
    monkeypatch.setattr('ccbd.control_plane_transport.factory.os.name', 'nt')

    with pytest.raises(RpcTransportAuthError) as error:
        connect_endpoint(descriptor, timeout_s=0.1)

    assert error.value.category == 'endpoint-invalid'


def test_direct_windows_endpoint_rejects_legacy_socket_path_descriptor(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr('ccbd.control_plane_transport.factory.os.name', 'nt')

    with pytest.raises(RpcTransportAuthError) as error:
        connect_endpoint({'socket_path': str(tmp_path / 'ccbd.sock')}, timeout_s=0.1)

    assert error.value.category == 'endpoint-invalid'


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


def _accept_until_timeout(listener) -> BaseException:
    try:
        listener.accept()
    except BaseException as exc:
        return exc
    raise AssertionError('listener unexpectedly accepted a bad token')


def _is_acl_proof_command(command: str) -> bool:
    return 'Get-Acl' in command or 'GetAccessControl' in command
