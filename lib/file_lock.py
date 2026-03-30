"""
file_lock.py - 通用跨平台文件锁

提供操作系统级的文件互斥锁，支持 Windows 和 Unix/Linux/macOS。
复用 lib/process_lock.py 的跨平台锁模式，但作为独立通用类
供 CCBCLIBackend 和未来 GSD 使用。

用法:
    lock = FileLock("/tmp/my.lock", timeout=10.0)
    if lock.acquire():
        try:
            # critical section
        finally:
            lock.release()

    # 或使用 context manager:
    with FileLock("/tmp/my.lock") as lock:
        # critical section
"""
from __future__ import annotations

import os
import sys
import time
import hashlib
from pathlib import Path
from typing import Optional


def _is_pid_alive(pid: int) -> bool:
    """检查进程是否存活（复用 process_lock.py 逻辑）"""
    if os.name == "nt":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            SYNCHRONIZE = 0x00100000
            handle = kernel32.OpenProcess(SYNCHRONIZE, False, pid)
            if handle:
                kernel32.CloseHandle(handle)
                return True
            return False
        except Exception:
            return True
    else:
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False


class FileLock:
    """通用跨平台文件锁

    使用操作系统级文件锁实现互斥。锁文件路径由调用者指定。

    Attributes:
        lock_file: 锁文件路径
        timeout: 获取锁的最大等待时间（秒）
    """

    def __init__(self, lock_path: str, timeout: float = 30.0):
        """初始化文件锁

        Args:
            lock_path: 锁文件的完整路径
            timeout: 等待获取锁的最大秒数
        """
        self.lock_file = Path(lock_path)
        self.timeout = timeout
        self._fd: Optional[int] = None
        self._acquired = False

    def _try_acquire_once(self) -> bool:
        """尝试获取锁一次（非阻塞）"""
        try:
            if os.name == "nt":
                import msvcrt
                # Windows: 确保文件至少 1 字节以支持区域锁定
                try:
                    st = os.fstat(self._fd)
                    if getattr(st, "st_size", 0) < 1:
                        os.lseek(self._fd, 0, os.SEEK_SET)
                        os.write(self._fd, b"\0")
                except Exception:
                    pass
                msvcrt.locking(self._fd, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

            # 写入 PID 用于调试和死锁检测
            pid_bytes = f"{os.getpid()}\n".encode()
            os.lseek(self._fd, 0, os.SEEK_SET)
            os.write(self._fd, pid_bytes)
            if os.name == "nt":
                try:
                    os.ftruncate(self._fd, max(1, len(pid_bytes)))
                except Exception:
                    pass
            else:
                os.ftruncate(self._fd, len(pid_bytes))

            self._acquired = True
            return True
        except (OSError, IOError):
            return False

    def _check_stale_lock(self) -> bool:
        """检查锁是否过期（持有进程已死）"""
        try:
            with open(self.lock_file, "r") as f:
                content = f.read().strip()
                if content:
                    pid = int(content)
                    if not _is_pid_alive(pid):
                        try:
                            self.lock_file.unlink()
                        except OSError:
                            pass
                        return True
        except (OSError, ValueError):
            pass
        return False

    def try_acquire(self) -> bool:
        """尝试获取锁（非阻塞）

        Returns:
            True 如果获取成功，False 如果锁被其他进程持有
        """
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)
        self._fd = os.open(str(self.lock_file), os.O_CREAT | os.O_RDWR)

        if self._try_acquire_once():
            return True

        if self._check_stale_lock():
            os.close(self._fd)
            self._fd = os.open(str(self.lock_file), os.O_CREAT | os.O_RDWR)
            if self._try_acquire_once():
                return True

        os.close(self._fd)
        self._fd = None
        return False

    def acquire(self) -> bool:
        """获取锁，等待至多 timeout 秒

        Returns:
            True 如果获取成功，False 如果超时
        """
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)
        self._fd = os.open(str(self.lock_file), os.O_CREAT | os.O_RDWR)

        deadline = time.time() + self.timeout
        stale_checked = False

        while time.time() < deadline:
            if self._try_acquire_once():
                return True

            if not stale_checked:
                stale_checked = True
                if self._check_stale_lock():
                    os.close(self._fd)
                    self._fd = os.open(str(self.lock_file), os.O_CREAT | os.O_RDWR)
                    if self._try_acquire_once():
                        return True

            time.sleep(0.1)

        if self._fd is not None:
            os.close(self._fd)
            self._fd = None
        return False

    def release(self) -> None:
        """释放锁"""
        if self._fd is not None:
            try:
                if self._acquired:
                    if os.name == "nt":
                        import msvcrt
                        try:
                            msvcrt.locking(self._fd, msvcrt.LK_UNLCK, 1)
                        except OSError:
                            pass
                    else:
                        import fcntl
                        try:
                            fcntl.flock(self._fd, fcntl.LOCK_UN)
                        except OSError:
                            pass
            finally:
                try:
                    os.close(self._fd)
                except OSError:
                    pass
                self._fd = None
                self._acquired = False

    @property
    def is_acquired(self) -> bool:
        """锁是否已被当前实例持有"""
        return self._acquired

    def __enter__(self) -> "FileLock":
        if not self.acquire():
            raise TimeoutError(f"Failed to acquire lock at {self.lock_file} after {self.timeout}s")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.release()
