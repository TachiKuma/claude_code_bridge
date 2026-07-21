from __future__ import annotations

from contextlib import contextmanager
import errno
import os
import time
from pathlib import Path

from provider_core.platform_info import is_windows

# msvcrt.locking raises OSError with these errno values when the byte range is
# held by another handle/process; anything else (permission, disk, ...) must
# surface rather than be treated as contention.
_LOCK_CONTENTION_ERRNOS = {errno.EACCES}
for _name in ('EDEADLK', 'EDEADLOCK'):
    _code = getattr(errno, _name, None)
    if _code is not None:
        _LOCK_CONTENTION_ERRNOS.add(_code)


@contextmanager
def file_lock(path: Path):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('a+', encoding='utf-8') as handle:
        if _lock_handle(handle):
            try:
                yield
            finally:
                _unlock_handle(handle)
        else:
            yield


def _lock_handle(handle) -> bool:
    if is_windows():
        import msvcrt

        _ensure_lock_region_byte(handle)
        # Emulate fcntl.flock(LOCK_EX) blocking semantics: msvcrt LK_LOCK would
        # block ~10s then raise, so retry the non-blocking lock with backoff on
        # the fixed byte-0 region until it is acquired. Only contention errno
        # values are retried; other OSErrors surface.
        delay = 0.005
        while True:
            handle.seek(0)
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                return True
            except OSError as exc:
                if exc.errno not in _LOCK_CONTENTION_ERRNOS:
                    raise
                time.sleep(delay)
                delay = min(delay * 2, 0.25)

    try:
        import fcntl  # type: ignore
    except ModuleNotFoundError:
        return False

    fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
    return True


def _unlock_handle(handle) -> None:
    if is_windows():
        import msvcrt

        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        return

    import fcntl  # type: ignore

    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _ensure_lock_region_byte(handle) -> None:
    # msvcrt.locking requires the locked region to contain a byte. The lock file
    # is a pure sentinel (no consumer reads its content), so a placeholder byte
    # is harmless. Lock the fixed byte-0 region so both acquirers contend on the
    # same byte regardless of file size.
    if handle.seek(0, os.SEEK_END) == 0:
        handle.write('\0')
        handle.flush()
    handle.seek(0)
