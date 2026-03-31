"""Tests for FileLock and ProviderLock on Windows (D-16).

Covers msvcrt.locking acquire/release, mutual exclusion, Chinese paths,
timeout, stale lock detection, and ProviderLock per-directory scoping.
"""

import os
import time

import pytest
from pathlib import Path

from lib.file_lock import FileLock
from lib.process_lock import ProviderLock


pytestmark = [pytest.mark.windows, pytest.mark.compat]


# ---------------------------------------------------------------------------
# Test 8: FileLock acquire/release
# ---------------------------------------------------------------------------
class TestFileLockAcquireRelease:
    def test_file_lock_acquire_release(self, tmp_path):
        """FileLock acquires and releases, is_acquired property reflects state."""
        lock = FileLock(str(tmp_path / "test1.lock"))
        assert lock.try_acquire() is True
        assert lock.is_acquired is True
        lock.release()
        assert lock.is_acquired is False


# ---------------------------------------------------------------------------
# Test 9: FileLock context manager
# ---------------------------------------------------------------------------
class TestFileLockContextManager:
    def test_file_lock_context_manager(self, tmp_path):
        """FileLock works as context manager, lock released on exit."""
        lock_path = str(tmp_path / "test2.lock")
        with FileLock(lock_path) as lock:
            assert lock.is_acquired is True
        assert lock.is_acquired is False


# ---------------------------------------------------------------------------
# Test 10: FileLock mutual exclusion
# ---------------------------------------------------------------------------
class TestFileLockMutualExclusion:
    def test_file_lock_mutual_exclusion(self, tmp_path):
        """Second FileLock on same path fails try_acquire while first holds the lock."""
        lock1 = FileLock(str(tmp_path / "test3.lock"))
        lock2 = FileLock(str(tmp_path / "test3.lock"))
        assert lock1.try_acquire() is True
        assert lock2.try_acquire() is False  # blocked by lock1
        lock1.release()
        assert lock2.try_acquire() is True  # now can acquire
        lock2.release()


# ---------------------------------------------------------------------------
# Test 11: FileLock acquire after release
# ---------------------------------------------------------------------------
class TestFileLockAcquireAfterRelease:
    def test_file_lock_acquire_after_release(self, tmp_path):
        """After release, a new FileLock can acquire the same path."""
        lock1 = FileLock(str(tmp_path / "test4.lock"))
        lock1.acquire()
        lock1.release()
        lock2 = FileLock(str(tmp_path / "test4.lock"))
        assert lock2.try_acquire() is True
        lock2.release()


# ---------------------------------------------------------------------------
# Test 12: FileLock with Chinese path
# ---------------------------------------------------------------------------
class TestFileLockChinesePath:
    def test_file_lock_chinese_path(self, tmp_path):
        """FileLock works with Chinese characters in lock file path."""
        chinese_dir = tmp_path / "中文目录"
        chinese_dir.mkdir()
        lock = FileLock(str(chinese_dir / "锁文件.lock"))
        assert lock.try_acquire() is True
        lock.release()


# ---------------------------------------------------------------------------
# Test 13: FileLock timeout
# ---------------------------------------------------------------------------
class TestFileLockTimeout:
    def test_file_lock_timeout(self, tmp_path):
        """acquire with very short timeout returns False when lock is held."""
        lock1 = FileLock(str(tmp_path / "test5.lock"))
        lock1.acquire()
        lock2 = FileLock(str(tmp_path / "test5.lock"), timeout=0.1)
        assert lock2.acquire() is False  # timeout, lock held by lock1
        lock1.release()


# ---------------------------------------------------------------------------
# Test 14: ProviderLock basic
# ---------------------------------------------------------------------------
class TestProviderLockBasic:
    def test_provider_lock_basic(self, tmp_path):
        """ProviderLock acquires and releases for a given provider and cwd."""
        lock = ProviderLock("test-provider", cwd=str(tmp_path))
        assert lock.try_acquire() is True
        assert lock.is_acquired is True
        lock.release()


# ---------------------------------------------------------------------------
# Test 15: ProviderLock different dirs
# ---------------------------------------------------------------------------
class TestProviderLockDifferentDirs:
    def test_provider_lock_different_dirs(self, tmp_path):
        """ProviderLock for same provider but different dirs acquire independently."""
        lock_a = ProviderLock("test-provider", cwd=str(tmp_path / "dir_a"))
        lock_b = ProviderLock("test-provider", cwd=str(tmp_path / "dir_b"))
        assert lock_a.try_acquire() is True
        assert lock_b.try_acquire() is True  # different dir hash = different lock file
        lock_a.release()
        lock_b.release()


# ---------------------------------------------------------------------------
# Test 16: Stale lock detection
# ---------------------------------------------------------------------------
class TestStaleLockDetection:
    def test_stale_lock_detection(self, tmp_path):
        """Lock file with PID of dead process is detected as stale and can be acquired."""
        stale_lock_path = tmp_path / "stale.lock"
        stale_lock_path.write_text("9999999\n")
        # PID 9999999 does not exist, so _is_pid_alive returns False
        lock = FileLock(str(stale_lock_path))
        assert lock.try_acquire() is True  # stale lock detected and taken over
        lock.release()
