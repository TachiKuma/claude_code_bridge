from __future__ import annotations

from pathlib import Path
import json

from ccbd.api_models import RpcRequest, RpcResponse
from ccbd.control_plane_transport.endpoint import endpoint_from_legacy_socket_path
from ccbd.control_plane_transport.factory import connect_endpoint

from .errors import CcbdClientError  # re-exported compatibility surface


def connect_socket(socket_path: Path, *, timeout_s: float):
    endpoint = endpoint_from_legacy_socket_path(socket_path)
    try:
        return connect_endpoint(endpoint, timeout_s=timeout_s)
    except CcbdClientError:
        raise
    except Exception as exc:
        raise CcbdClientError(str(exc)) from exc


def send_request(sock, request: RpcRequest) -> None:
    payload = json.dumps(request.to_record(), ensure_ascii=False) + '\n'
    sock.sendall(payload.encode('utf-8'))


def recv_response_line(sock) -> bytes:
    raw = b''
    while b'\n' not in raw:
        chunk = sock.recv(65536)
        if not chunk:
            break
        raw += chunk
    return raw


def decode_response(raw: bytes) -> RpcResponse:
    line = raw.split(b'\n', 1)[0].decode('utf-8')
    return RpcResponse.from_record(json.loads(line))


__all__ = ['connect_socket', 'decode_response', 'recv_response_line', 'send_request']
