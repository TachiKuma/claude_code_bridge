from __future__ import annotations

import errno
import os
from pathlib import Path
import subprocess
import sys
import threading
from types import SimpleNamespace

import pytest

from maintenance_heartbeat import lock as heartbeat_lock
from storage import atomic
from storage import locks as storage_locks


class _FakeMsvcrt:
    LK_NBLCK = 1
    LK_UNLCK = 2

    def __init__(self, *, fail_errno: int | None = None) -> None:
        self.fail_errno = fail_errno
        self.locked = False
        self.positions: list[int] = []

    def locking(self, fd: int, mode: int, nbytes: int) -> None:
        assert nbytes == 1
        self.positions.append(os.lseek(fd, 0, os.SEEK_CUR))
        if mode == self.LK_UNLCK:
            self.locked = False
            return
        if self.fail_errno is not None:
            raise OSError(self.fail_errno, 'injected lock failure')
        if self.locked:
            raise OSError(errno.EACCES, 'locked')
        self.locked = True


def _install_fake_msvcrt(monkeypatch, fake: _FakeMsvcrt) -> None:
    monkeypatch.setitem(sys.modules, 'msvcrt', SimpleNamespace(
        LK_NBLCK=fake.LK_NBLCK,
        LK_UNLCK=fake.LK_UNLCK,
        locking=fake.locking,
    ))


def test_runtime_modules_import_without_unix_terminal_modules() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    code = """
import importlib.abc

class BlockUnixRuntimeImports(importlib.abc.MetaPathFinder):
    blocked = {'fcntl', 'pty', 'termios'}

    def find_spec(self, fullname, path=None, target=None):
        if fullname in self.blocked:
            raise ModuleNotFoundError(fullname)
        return None

import sys
sys.meta_path.insert(0, BlockUnixRuntimeImports())

import mobile_gateway.terminal
import maintenance_heartbeat.lock
import storage.atomic
import storage.locks
"""
    env = dict(os.environ)
    env['PYTHONPATH'] = str(repo_root / 'lib') + os.pathsep + env.get('PYTHONPATH', '')

    result = subprocess.run(
        [sys.executable, '-c', code],
        cwd=str(repo_root),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=10,
    )

    assert result.returncode == 0, result.stderr


def test_windows_atomic_write_fallback_creates_parent_and_skips_directory_fsync(monkeypatch, tmp_path: Path) -> None:
    target = tmp_path / 'missing' / 'state.txt'
    events: list[str] = []
    real_fdopen = os.fdopen
    real_fsync = os.fsync
    real_replace = os.replace

    class TrackingHandle:
        def __init__(self, handle):
            self.handle = handle

        def __enter__(self):
            self.handle.__enter__()
            return self

        def __exit__(self, *args):
            return self.handle.__exit__(*args)

        def write(self, text):
            events.append('write')
            return self.handle.write(text)

        def flush(self):
            events.append('flush')
            return self.handle.flush()

        def fileno(self):
            return self.handle.fileno()

    def tracking_fdopen(*args, **kwargs):
        return TrackingHandle(real_fdopen(*args, **kwargs))

    def tracking_fsync(fd: int) -> None:
        events.append('file-fsync')
        return real_fsync(fd)

    def tracking_replace(*args, **kwargs):
        events.append('replace')
        return real_replace(*args, **kwargs)

    monkeypatch.setattr(atomic, '_supports_directory_fsync', lambda: False)
    monkeypatch.setattr(os, 'fdopen', tracking_fdopen)
    monkeypatch.setattr(os, 'fsync', tracking_fsync)
    monkeypatch.setattr(os, 'replace', tracking_replace)

    atomic.atomic_write_text(target, 'new')

    assert target.read_text(encoding='utf-8') == 'new'
    assert events == ['write', 'flush', 'file-fsync', 'replace']


def test_windows_file_lock_waits_on_fixed_byte_zero(monkeypatch, tmp_path: Path) -> None:
    fake = _FakeMsvcrt()
    _install_fake_msvcrt(monkeypatch, fake)
    monkeypatch.setattr(storage_locks, 'is_windows', lambda: True)
    lock_path = tmp_path / 'state.lock'
    lock_path.write_text('existing-lock-sentinel-content', encoding='utf-8')
    second_entered = threading.Event()

    def acquire_second() -> None:
        with storage_locks.file_lock(lock_path):
            second_entered.set()

    with storage_locks.file_lock(lock_path):
        thread = threading.Thread(target=acquire_second)
        thread.start()
        assert not second_entered.wait(0.05)

    thread.join(timeout=2)

    assert second_entered.is_set()
    assert not thread.is_alive()
    assert fake.positions
    assert set(fake.positions) == {0}


def test_windows_heartbeat_lock_reports_contention_as_busy(monkeypatch, tmp_path: Path) -> None:
    fake = _FakeMsvcrt()
    _install_fake_msvcrt(monkeypatch, fake)
    monkeypatch.setattr(heartbeat_lock, 'is_windows', lambda: True)
    lock_path = tmp_path / 'heartbeat.json'

    with heartbeat_lock.MaintenanceHeartbeatLock(lock_path, payload={'pid': 1}):
        with pytest.raises(heartbeat_lock.MaintenanceHeartbeatLockBusy):
            with heartbeat_lock.MaintenanceHeartbeatLock(lock_path, payload={'pid': 2}):
                pass

    assert set(fake.positions) == {0}


def test_windows_heartbeat_lock_surfaces_non_contention_oserror(monkeypatch, tmp_path: Path) -> None:
    fake = _FakeMsvcrt(fail_errno=errno.EPERM)
    _install_fake_msvcrt(monkeypatch, fake)
    monkeypatch.setattr(heartbeat_lock, 'is_windows', lambda: True)

    with pytest.raises(OSError, match='injected lock failure'):
        with heartbeat_lock.MaintenanceHeartbeatLock(tmp_path / 'heartbeat.json', payload={'pid': 1}):
            pass


def test_heartbeat_lock_closes_handle_when_locking_surfaces_oserror(monkeypatch, tmp_path: Path) -> None:
    class FakeHandle:
        closed = False

        def close(self) -> None:
            self.closed = True

    handle = FakeHandle()

    monkeypatch.setattr(Path, 'open', lambda self, *args, **kwargs: handle)
    monkeypatch.setattr(
        heartbeat_lock,
        '_lock_handle',
        lambda _handle: (_ for _ in ()).throw(OSError('non-contention failure')),
    )

    with pytest.raises(OSError, match='non-contention failure'):
        with heartbeat_lock.MaintenanceHeartbeatLock(tmp_path / 'heartbeat.json', payload={'pid': 1}):
            pass

    assert handle.closed is True
