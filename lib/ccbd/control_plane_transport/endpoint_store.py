from __future__ import annotations

from pathlib import Path
import json
import os

from .endpoint import EndpointRef, endpoint_from_record, endpoint_to_record

_ENDPOINT_FILE = 'control-plane-endpoint.json'
_TOKEN_FILE_PREFIX = 'control-plane-token-'


def endpoint_store_path(legacy_socket_path: str | Path) -> Path:
    return Path(legacy_socket_path).parent / _ENDPOINT_FILE


def token_store_path(legacy_socket_path: str | Path, generation: str) -> Path:
    return Path(legacy_socket_path).parent / f'{_TOKEN_FILE_PREFIX}{generation}.json'


def write_endpoint(endpoint: EndpointRef, *, legacy_socket_path: str | Path) -> None:
    path = endpoint_store_path(legacy_socket_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = endpoint_to_record(endpoint)
    tmp = path.with_name(f'.{path.name}.{os.getpid()}.tmp')
    tmp.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True) + '\n', encoding='utf-8')
    os.replace(tmp, path)


def read_endpoint(legacy_socket_path: str | Path) -> EndpointRef | None:
    path = endpoint_store_path(legacy_socket_path)
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(payload, dict):
        raise ValueError('ccbd endpoint descriptor must be an object')
    return endpoint_from_record(payload)


def unlink_endpoint(
    *,
    legacy_socket_path: str | Path,
    expected_generation: str | None,
) -> bool:
    path = endpoint_store_path(legacy_socket_path)
    if not path.exists():
        return False
    if not str(expected_generation or '').strip():
        return False
    current = read_endpoint(legacy_socket_path)
    if str((current or {}).get('generation') or '') != str(expected_generation):
        return False
    try:
        path.unlink()
        return True
    except FileNotFoundError:
        return False


def touch_legacy_socket_marker(legacy_socket_path: str | Path) -> bool:
    path = Path(legacy_socket_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open('xb'):
            pass
        return True
    except FileExistsError:
        return False


def unlink_legacy_socket_marker(legacy_socket_path: str | Path) -> None:
    try:
        Path(legacy_socket_path).unlink()
    except FileNotFoundError:
        return


def unlink_token(token_ref: str | Path) -> None:
    try:
        Path(token_ref).unlink()
    except FileNotFoundError:
        return
