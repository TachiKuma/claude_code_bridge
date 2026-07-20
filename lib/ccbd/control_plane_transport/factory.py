from __future__ import annotations

from pathlib import Path

from .endpoint import EndpointRef, endpoint_from_legacy_socket_path, endpoint_from_record
from .unix import UnixControlPlaneTransport


def transport_for_endpoint(endpoint: EndpointRef | dict | str | Path):
    resolved = endpoint_from_record(endpoint)
    if resolved['kind'] == 'unix_socket':
        return UnixControlPlaneTransport(resolved)
    raise RuntimeError(f'unsupported ccbd control-plane endpoint: {resolved["kind"]}')


def connect_endpoint(endpoint: EndpointRef | dict | str | Path, *, timeout_s: float):
    return transport_for_endpoint(endpoint).connect(timeout_s=timeout_s)


def endpoint_connectable(endpoint: EndpointRef | dict | str | Path, *, timeout_s: float = 0.2) -> bool:
    try:
        return bool(transport_for_endpoint(endpoint).is_connectable(timeout_s=timeout_s))
    except Exception:
        return False


def transport_for_legacy_socket_path(socket_path: str | Path):
    return transport_for_endpoint(endpoint_from_legacy_socket_path(socket_path))
