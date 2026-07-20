from __future__ import annotations

from pathlib import Path
from typing import Literal, TypedDict


class EndpointRef(TypedDict):
    kind: Literal['unix_socket', 'tcp_loopback']
    address: str
    display: str
    legacy_socket_path: str | None
    auth_ref: str | None


def endpoint_from_legacy_socket_path(socket_path: str | Path) -> EndpointRef:
    raw = str(socket_path).strip()
    if not raw:
        raise ValueError('legacy socket path is required')
    path = str(Path(raw))
    return {
        'kind': 'unix_socket',
        'address': path,
        'display': path,
        'legacy_socket_path': path,
        'auth_ref': None,
    }


def endpoint_from_record(record: dict | str | Path) -> EndpointRef:
    if isinstance(record, (str, Path)):
        return endpoint_from_legacy_socket_path(record)
    kind = str(record.get('kind') or '')
    if kind == 'unix_socket':
        endpoint = endpoint_from_legacy_socket_path(
            record.get('address') or record.get('legacy_socket_path') or ''
        )
        endpoint['display'] = str(record.get('display') or endpoint['address'])
        endpoint['auth_ref'] = record.get('auth_ref')
        return endpoint
    if kind == 'tcp_loopback':
        address = str(record.get('address') or '')
        if not address:
            raise ValueError('tcp_loopback endpoint requires address')
        return {
            'kind': 'tcp_loopback',
            'address': address,
            'display': str(record.get('display') or address),
            'legacy_socket_path': record.get('legacy_socket_path'),
            'auth_ref': record.get('auth_ref'),
        }
    if 'socket_path' in record:
        return endpoint_from_legacy_socket_path(str(record['socket_path']))
    raise ValueError(f'unsupported ccbd endpoint kind: {kind!r}')


def endpoint_to_record(endpoint: EndpointRef) -> dict[str, object]:
    return {
        'kind': endpoint['kind'],
        'address': endpoint['address'],
        'display': endpoint['display'],
        'legacy_socket_path': endpoint.get('legacy_socket_path'),
        'auth_ref': endpoint.get('auth_ref'),
    }


def legacy_socket_path(endpoint: EndpointRef) -> Path | None:
    raw = endpoint.get('legacy_socket_path')
    return Path(raw) if raw else None
