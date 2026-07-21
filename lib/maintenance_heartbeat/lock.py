from __future__ import annotations

import errno
import json
import os
from pathlib import Path
from typing import Any

from provider_core.platform_info import is_windows

# msvcrt.locking raises OSError with these errno values when the byte range is
# already held; any other OSError (permission, disk, ...) must surface rather
# than be mistaken for lock contention.
_LOCK_CONTENTION_ERRNOS = {errno.EACCES}
for _name in ('EDEADLK', 'EDEADLOCK'):
    _code = getattr(errno, _name, None)
    if _code is not None:
        _LOCK_CONTENTION_ERRNOS.add(_code)


class MaintenanceHeartbeatLockBusy(RuntimeError):
    pass


class MaintenanceHeartbeatLock:
    def __init__(self, path: Path, *, payload: dict[str, Any]) -> None:
        self._path = Path(path)
        self._payload = dict(payload)
        self._handle = None

    def __enter__(self) -> 'MaintenanceHeartbeatLock':
        self._path.parent.mkdir(parents=True, exist_ok=True)
        handle = self._path.open('a+', encoding='utf-8')
        try:
            _lock_handle(handle)
        except BaseException:
            handle.close()
            raise
        self._handle = handle
        self._write_state({'held': True, **self._payload})
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        handle = self._handle
        if handle is None:
            return
        try:
            release_payload = dict(self._payload)
            released_at = release_payload.pop('released_at', None)
            self._write_state({'held': False, **release_payload, 'released_at': released_at})
            _unlock_handle(handle)
        finally:
            handle.close()
            self._handle = None

    def _write_state(self, payload: dict[str, Any]) -> None:
        handle = self._handle
        if handle is None:
            return
        handle.seek(0)
        handle.truncate(0)
        handle.write(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')
        handle.flush()
        os.fsync(handle.fileno())


def _lock_handle(handle) -> None:
    # Non-blocking exclusive lock. On contention raise MaintenanceHeartbeatLockBusy;
    # any other error surfaces. The try/except is scoped tightly around the lock
    # call so unrelated OSErrors (permission, disk) are never mistaken for "busy".
    if is_windows():
        import msvcrt

        # msvcrt.locking needs a byte in the locked region; the owning handle may
        # still write/truncate its own locked byte (mirrors provider_core ProviderLock).
        if handle.seek(0, os.SEEK_END) == 0:
            handle.write('\0')
            handle.flush()
        handle.seek(0)
        try:
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as exc:
            if exc.errno in _LOCK_CONTENTION_ERRNOS:
                raise MaintenanceHeartbeatLockBusy('maintenance heartbeat tick is already running') from exc
            raise
        return

    import fcntl

    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        raise MaintenanceHeartbeatLockBusy('maintenance heartbeat tick is already running') from exc


def _unlock_handle(handle) -> None:
    if is_windows():
        import msvcrt

        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        return

    import fcntl

    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


__all__ = ['MaintenanceHeartbeatLock', 'MaintenanceHeartbeatLockBusy']
