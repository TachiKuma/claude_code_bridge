from __future__ import annotations

from contextlib import contextmanager
import errno
from pathlib import Path
import select
import socket
import time
import uuid

from ccbd.api_models import RpcRequest

from .endpoint import EndpointRef, tcp_endpoint
from .endpoint_store import (
    read_endpoint,
    token_store_path,
    touch_legacy_socket_marker,
    unlink_endpoint,
    unlink_legacy_socket_marker,
    unlink_token,
    write_endpoint,
)
from .token_auth import (
    RpcTransportAuthError,
    client_authenticate,
    create_token_file,
    load_token_file,
    server_authenticate,
)

_LISTEN_BACKLOG = 128
_CONNECT_RETRY_INTERVAL_S = 0.05
_CONNECT_MAX_RETRIES = 2
_CONNECT_RETRY_ERRNOS = frozenset({
    errno.EAGAIN,
    errno.ECONNREFUSED,
    errno.ENOENT,
})
_MAX_RESPONSE_BYTES = 1024 * 1024
_MAX_DEFERRED_CONNECTIONS = 128


class WindowsTcpControlPlaneTransport:
    def __init__(
        self,
        endpoint: EndpointRef | None,
        *,
        legacy_socket_path: str | Path,
        command_runner=None,
    ) -> None:
        self.endpoint = endpoint
        self.legacy_socket_path = Path(legacy_socket_path)
        self._command_runner = command_runner

    @classmethod
    def from_legacy_socket_path(cls, socket_path: str | Path) -> 'WindowsTcpControlPlaneTransport':
        return cls(read_endpoint(socket_path), legacy_socket_path=socket_path)

    def connect(self, *, timeout_s: float):
        endpoint = self.endpoint or read_endpoint(self.legacy_socket_path)
        if endpoint is None:
            raise RpcTransportAuthError('endpoint-missing', 'ccbd TCP endpoint descriptor is missing')
        host, port = _endpoint_host_port(endpoint)
        token_ref = endpoint.get('token_ref') or endpoint.get('auth_ref')
        token_file = load_token_file(str(token_ref or ''))
        deadline = time.monotonic() + max(0.0, float(timeout_s))
        last_error: OSError | None = None
        for attempt in range(_CONNECT_MAX_RETRIES + 1):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(remaining)
            try:
                sock.connect((host, port))
                client_authenticate(sock, token_file.token)
                return sock
            except OSError as exc:
                sock.close()
                last_error = exc
                if isinstance(exc, RpcTransportAuthError) or not _is_transient_connect_error(exc):
                    break
                if attempt >= _CONNECT_MAX_RETRIES:
                    break
                sleep_for = min(_CONNECT_RETRY_INTERVAL_S, max(0.0, deadline - time.monotonic()))
                if sleep_for <= 0:
                    break
                time.sleep(sleep_for)
        if last_error is not None:
            raise last_error
        raise TimeoutError('timed out')

    def is_connectable(self, *, timeout_s: float = 0.2) -> bool:
        try:
            sock = self.connect(timeout_s=timeout_s)
        except Exception:
            return False
        try:
            sock.close()
        except OSError:
            pass
        return True

    def listen(self) -> 'WindowsTcpControlPlaneListener':
        generation = uuid.uuid4().hex[:16]
        token_file = create_token_file(
            token_store_path(self.legacy_socket_path, generation),
            command_runner=self._command_runner,
        )
        runtime_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        bound_endpoint = None
        marker_created = False
        try:
            runtime_socket.bind(('127.0.0.1', 0))
            runtime_socket.listen(_LISTEN_BACKLOG)
            runtime_socket.settimeout(0.2)
            host, port = runtime_socket.getsockname()[:2]
            bound_endpoint = tcp_endpoint(
                host=str(host),
                port=int(port),
                token_ref=token_file.token_ref,
                generation=token_file.generation,
                acl_status=token_file.acl_status,
                fingerprint=token_file.fingerprint,
            )
            write_endpoint(bound_endpoint, legacy_socket_path=self.legacy_socket_path)
            marker_created = touch_legacy_socket_marker(self.legacy_socket_path)
        except BaseException:
            try:
                runtime_socket.close()
            finally:
                unlink_token(token_file.token_ref)
                if bound_endpoint is not None:
                    endpoint_deleted = unlink_endpoint(
                        legacy_socket_path=self.legacy_socket_path,
                        expected_generation=str(bound_endpoint.get('generation') or ''),
                    )
                    if endpoint_deleted and marker_created:
                        unlink_legacy_socket_marker(self.legacy_socket_path)
            raise
        self.endpoint = bound_endpoint
        return WindowsTcpControlPlaneListener(
            endpoint=bound_endpoint,
            socket=runtime_socket,
            token=token_file.token,
            legacy_socket_path=self.legacy_socket_path,
            generation=token_file.generation,
            token_ref=token_file.token_ref,
            marker_created=marker_created,
        )

    def unlink_bound_endpoint(self, *, bound_identity) -> None:
        generation, token_ref, marker_created = _bound_identity_parts(bound_identity)
        endpoint_deleted = unlink_endpoint(
            legacy_socket_path=self.legacy_socket_path,
            expected_generation=generation,
        )
        if endpoint_deleted and marker_created:
            unlink_legacy_socket_marker(self.legacy_socket_path)
        if token_ref:
            unlink_token(token_ref)

    def bootstrap_readiness_probe(self, server, *, timeout_s: float):
        return tcp_bootstrap_readiness_probe(server, timeout_s=timeout_s)


class WindowsTcpControlPlaneListener:
    def __init__(
        self,
        *,
        endpoint: EndpointRef,
        socket,
        token: str,
        legacy_socket_path: Path,
        generation: str,
        token_ref: str,
        marker_created: bool,
    ) -> None:
        self.endpoint = endpoint
        self._socket = socket
        self._token = token
        self.legacy_socket_path = legacy_socket_path
        self.bound_socket_stat = (generation, token_ref, marker_created)

    def settimeout(self, value: float | None) -> None:
        self._socket.settimeout(value)

    def accept(self):
        deadline = None
        timeout = self._socket.gettimeout()
        if timeout is not None:
            deadline = time.monotonic() + max(0.0, float(timeout))
        while True:
            if deadline is not None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError('timed out waiting for authenticated ccbd TCP client')
                self._socket.settimeout(remaining)
            conn, peer = self._socket.accept()
            try:
                conn.settimeout(remaining if deadline is not None else timeout)
                remainder = server_authenticate(conn, self._token)
                return _BufferedConnection(conn, remainder), {
                    'kind': 'tcp_loopback_token',
                    'same_user': True,
                    'detail': f'{peer[0]}:{peer[1]}',
                }
            except RpcTransportAuthError:
                try:
                    conn.close()
                except OSError:
                    pass
                continue

    def close(self) -> None:
        self._socket.close()

    def fileno(self) -> int:
        return self._socket.fileno()


class _BufferedConnection:
    def __init__(self, sock, initial: bytes) -> None:
        self._sock = sock
        self._buffer = bytearray(initial or b'')

    def settimeout(self, value: float | None) -> None:
        self._sock.settimeout(value)

    def sendall(self, payload: bytes) -> None:
        self._sock.sendall(payload)

    def recv(self, size: int) -> bytes:
        if self._buffer:
            chunk = bytes(self._buffer[:size])
            del self._buffer[:size]
            return chunk
        return self._sock.recv(size)

    def close(self) -> None:
        self._sock.close()

    def __enter__(self) -> '_BufferedConnection':
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


def _is_transient_connect_error(exc: OSError) -> bool:
    return int(getattr(exc, 'errno', 0) or 0) in _CONNECT_RETRY_ERRNOS


def _endpoint_host_port(endpoint: EndpointRef) -> tuple[str, int]:
    host = str(endpoint.get('host') or '127.0.0.1')
    port = endpoint.get('port')
    if port is None:
        _, _, raw_port = str(endpoint.get('address') or '').rpartition(':')
        port = raw_port
    clean_port = int(port)
    if host != '127.0.0.1':
        raise ValueError('ccbd TCP endpoint must use 127.0.0.1')
    return host, clean_port


def _bound_identity_parts(bound_identity) -> tuple[str | None, str | None, bool]:
    if isinstance(bound_identity, tuple) and len(bound_identity) >= 2:
        marker_created = bool(bound_identity[2]) if len(bound_identity) >= 3 else True
        return str(bound_identity[0]), str(bound_identity[1]), marker_created
    return None, None, False


@contextmanager
def tcp_bootstrap_readiness_probe(server, *, timeout_s: float):
    from ccbd.socket_client_runtime import decode_response, send_request
    from ccbd.socket_server_runtime.loop import close_connection, enqueue_connection, start_worker

    runtime_socket = server._server
    if runtime_socket is None:
        raise RuntimeError('ccbd bootstrap probe requires a listening socket')
    if server._bootstrap_probe_active:
        raise RuntimeError('ccbd bootstrap probe is already active')
    deadline = time.monotonic() + max(0.1, float(timeout_s))
    nonce = uuid.uuid4().hex
    client = None
    server._bootstrap_probe_active = True
    completed = False
    try:
        start_worker(server, interval=0.0, on_tick=None)
        client = server._control_plane_transport.connect(timeout_s=max(0.1, deadline - time.monotonic()))
        send_request(
            client,
            RpcRequest(
                op='ping',
                request={
                    'target': 'ccbd',
                    'bootstrap_probe_nonce': nonce,
                },
            ),
        )
        payload = _pump_until_probe_response(
            server,
            runtime_socket=runtime_socket,
            client=client,
            deadline=deadline,
            nonce=nonce,
            decode_response=decode_response,
            close_connection=close_connection,
            enqueue_connection=enqueue_connection,
        )
        yield payload
        completed = True
    except BaseException:
        server._stop_event.set()
        raise
    finally:
        if completed:
            server._bootstrap_probe_active = False
        if client is not None:
            try:
                client.close()
            except OSError:
                pass


def _pump_until_probe_response(
    server,
    *,
    runtime_socket,
    client,
    deadline: float,
    nonce: str,
    decode_response,
    close_connection,
    enqueue_connection,
) -> dict:
    raw = b''
    deferred_connections = []
    try:
        while b'\n' not in raw:
            worker_error = server._peek_worker_error()
            if worker_error is not None:
                raise RuntimeError(f'ccbd bootstrap request worker failed: {worker_error}')
            if server._stop_event.is_set():
                raise RuntimeError('ccbd bootstrap request worker stopped')
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError('timed out waiting for ccbd bootstrap self-ping')
            readable, _, _ = select.select(
                [runtime_socket, client],
                [],
                [],
                remaining,
            )
            if runtime_socket in readable:
                try:
                    conn, _ = runtime_socket.accept()
                except (BlockingIOError, socket.timeout, TimeoutError):
                    conn = None
                if conn is not None:
                    if len(deferred_connections) >= _MAX_DEFERRED_CONNECTIONS:
                        close_connection(conn)
                    else:
                        deferred_connections.append(conn)
                        enqueue_connection(server, conn)
            if client in readable:
                chunk = client.recv(65536)
                if not chunk:
                    break
                raw += chunk
                if len(raw) > _MAX_RESPONSE_BYTES:
                    raise RuntimeError('ccbd bootstrap self-ping response is too large')
        if not raw:
            raise RuntimeError('ccbd bootstrap self-ping returned an empty response')
        response = decode_response(raw)
        if not response.ok:
            raise RuntimeError(response.error or 'ccbd bootstrap self-ping failed')
        payload = dict(response.payload)
        if str(payload.get('bootstrap_probe_nonce') or '') != nonce:
            raise RuntimeError('ccbd bootstrap self-ping nonce mismatch')
        return payload
    except BaseException:
        for connection in deferred_connections:
            close_connection(connection)
        raise
