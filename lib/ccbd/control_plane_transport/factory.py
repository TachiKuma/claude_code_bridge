from __future__ import annotations

import os
from pathlib import Path

from .endpoint import EndpointRef, endpoint_from_legacy_socket_path, endpoint_from_record
from .unix import UnixControlPlaneTransport
from .windows_tcp import WindowsTcpControlPlaneTransport


def transport_for_endpoint(endpoint: EndpointRef | dict | str | Path):
    resolved = endpoint_from_record(endpoint)
    if resolved['kind'] == 'unix_socket':
        return UnixControlPlaneTransport(resolved)
    if resolved['kind'] == 'tcp_loopback':
        token_ref = str(resolved.get('token_ref') or resolved.get('auth_ref') or '').strip()
        legacy_socket_path = resolved.get('legacy_socket_path') or token_ref or '.'
        return WindowsTcpControlPlaneTransport(resolved, legacy_socket_path=legacy_socket_path)
    raise RuntimeError(f'unsupported ccbd control-plane endpoint: {resolved["kind"]}')


def connect_endpoint(endpoint: EndpointRef | dict | str | Path, *, timeout_s: float):
    return transport_for_endpoint(endpoint).connect(timeout_s=timeout_s)


def endpoint_connectable(endpoint: EndpointRef | dict | str | Path, *, timeout_s: float = 0.2) -> bool:
    try:
        return bool(transport_for_endpoint(endpoint).is_connectable(timeout_s=timeout_s))
    except Exception:
        return False


def transport_for_legacy_socket_path(socket_path: str | Path, *, prefer_windows: bool = False):
    if os.name == 'nt':
        transport = WindowsTcpControlPlaneTransport.from_legacy_socket_path(socket_path)
        if prefer_windows:
            endpoint = getattr(transport, 'endpoint', None)
            if endpoint is None or endpoint.get('kind') == 'tcp_loopback':
                return transport
            return WindowsTcpControlPlaneTransport(None, legacy_socket_path=socket_path)
        if transport.endpoint is not None:
            return transport
    return transport_for_endpoint(endpoint_from_legacy_socket_path(socket_path))
