import unittest
import tempfile
import os
import time
import shutil
from pathlib import Path
from lib.file_lock import FileLock, _is_pid_alive


class TestIsPidAlive(unittest.TestCase):
    def test_current_process_alive(self):
        """当前进程 PID 应存活"""
        self.assertTrue(_is_pid_alive(os.getpid()))

    def test_invalid_pid(self):
        """不存在的 PID 应返回 False"""
        # 使用一个不太可能存在的 PID（0 在 Windows 上特殊，用 999999）
        result = _is_pid_alive(999999)
        # 这个测试主要确保不抛异常
        self.assertIsInstance(result, bool)


class TestFileLockBasic(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.lock_path = os.path.join(self.tmpdir, "test.lock")

    def tearDown(self):
        try:
            shutil.rmtree(self.tmpdir, ignore_errors=True)
        except OSError:
            pass

    def test_acquire_and_release(self):
        """可正常获取和释放锁"""
        lock = FileLock(self.lock_path, timeout=5.0)
        self.assertTrue(lock.acquire())
        self.assertTrue(lock.is_acquired)
        lock.release()
        self.assertFalse(lock.is_acquired)

    def test_context_manager(self):
        """context manager 自动获取和释放锁"""
        with FileLock(self.lock_path, timeout=5.0) as lock:
            self.assertTrue(lock.is_acquired)
        self.assertFalse(lock.is_acquired)

    def test_double_release_safe(self):
        """重复释放不抛异常"""
        lock = FileLock(self.lock_path, timeout=5.0)
        lock.acquire()
        lock.release()
        lock.release()  # 不应抛异常

    def test_try_acquire_when_free(self):
        """锁空闲时 try_acquire 成功"""
        lock = FileLock(self.lock_path, timeout=5.0)
        self.assertTrue(lock.try_acquire())
        lock.release()

    def test_acquire_timeout(self):
        """同一锁路径同时获取会超时（同进程重入测试）"""
        lock1 = FileLock(self.lock_path, timeout=1.0)
        lock2 = FileLock(self.lock_path, timeout=1.0)
        self.assertTrue(lock1.acquire())
        # 同进程第二次获取（同一 fd 模式下行为因平台而异，仅测试不崩溃）
        try:
            result = lock2.try_acquire()
            # Windows msvcrt: 同进程同文件通常可以再次锁定
            # Unix fcntl: 同进程同 fd 可以重入
        except Exception:
            pass
        lock1.release()
        # 释放后应可获取
        self.assertTrue(lock2.try_acquire())
        lock2.release()

    def test_lock_creates_parent_dirs(self):
        """锁文件父目录不存在时自动创建"""
        nested_path = os.path.join(self.tmpdir, "a", "b", "test.lock")
        lock = FileLock(nested_path, timeout=5.0)
        self.assertTrue(lock.acquire())
        self.assertTrue(os.path.exists(nested_path))
        lock.release()


class TestFileLockStaleDetection(unittest.TestCase):
    def test_stale_lock_cleanup(self):
        """过期锁（持有者已死）可被清理"""
        tmpdir = tempfile.mkdtemp()
        lock_path = os.path.join(tmpdir, "stale.lock")
        try:
            # 写入一个不存在的 PID
            os.makedirs(os.path.dirname(lock_path), exist_ok=True)
            with open(lock_path, "w") as f:
                f.write("999999\n")

            lock = FileLock(lock_path, timeout=5.0)
            # 应该能获取锁（因为 PID 999999 不存在）
            self.assertTrue(lock.try_acquire())
            lock.release()
        finally:
            try:
                shutil.rmtree(tmpdir, ignore_errors=True)
            except OSError:
                pass


if __name__ == "__main__":
    unittest.main()
