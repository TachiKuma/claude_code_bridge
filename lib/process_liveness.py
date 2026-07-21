from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
from pathlib import Path

SYNCHRONIZE = 0x00100000
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
PROCESS_LIVENESS_ACCESS = SYNCHRONIZE | PROCESS_QUERY_LIMITED_INFORMATION

WAIT_OBJECT_0 = 0x00000000
WAIT_TIMEOUT = 0x00000102
WAIT_FAILED = 0xFFFFFFFF

ERROR_ACCESS_DENIED = 5
ERROR_INVALID_PARAMETER = 87
ERROR_NOT_FOUND = 1168


class _WindowsApi:
    def __init__(self) -> None:
        self._kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self._kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self._kernel32.OpenProcess.restype = wintypes.HANDLE
        self._kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        self._kernel32.WaitForSingleObject.restype = wintypes.DWORD
        self._kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        self._kernel32.CloseHandle.restype = wintypes.BOOL

    def open_process(self, access: int, inherit_handle: bool, pid: int):
        return self._kernel32.OpenProcess(access, bool(inherit_handle), int(pid))

    def wait_for_single_object(self, handle, milliseconds: int) -> int:
        return int(self._kernel32.WaitForSingleObject(handle, int(milliseconds)))

    def close_handle(self, handle) -> None:
        self._kernel32.CloseHandle(handle)

    def get_last_error(self) -> int:
        return int(ctypes.get_last_error())


def process_exists(pid: int | None) -> bool:
    if pid is None:
        return False
    try:
        resolved_pid = int(pid)
    except Exception:
        return False
    if resolved_pid <= 0:
        return False
    if os.name == "nt":
        return _windows_process_exists(resolved_pid)
    return _posix_process_exists(resolved_pid)


def _windows_process_exists(pid: int) -> bool:
    api = _winapi()
    handle = api.open_process(PROCESS_LIVENESS_ACCESS, False, pid)
    if not handle:
        return _windows_open_failure_process_exists(api.get_last_error())
    try:
        return api.wait_for_single_object(handle, 0) == WAIT_TIMEOUT
    finally:
        api.close_handle(handle)


def _windows_open_failure_process_exists(error_code: int) -> bool:
    if int(error_code) == ERROR_ACCESS_DENIED:
        return True
    return False


def _posix_process_exists(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    except Exception:
        return False
    if _proc_pid_state(pid) == "Z":
        return False
    return True


def _winapi():
    return _WindowsApi()


def _proc_pid_state(pid: int, *, proc_root: Path = Path("/proc")) -> str | None:
    if os.name == "nt" or pid <= 0:
        return None
    try:
        return _parse_proc_stat_state((proc_root / str(pid) / "stat").read_text(encoding="utf-8"))
    except Exception:
        return None


def _parse_proc_stat_state(text: str) -> str | None:
    try:
        after_comm = text.rsplit(") ", 1)[1]
    except Exception:
        return None
    fields = after_comm.split()
    if not fields:
        return None
    state = fields[0].strip()
    return state[:1] or None


__all__ = [
    "ERROR_ACCESS_DENIED",
    "ERROR_INVALID_PARAMETER",
    "ERROR_NOT_FOUND",
    "PROCESS_LIVENESS_ACCESS",
    "PROCESS_QUERY_LIMITED_INFORMATION",
    "SYNCHRONIZE",
    "WAIT_FAILED",
    "WAIT_OBJECT_0",
    "WAIT_TIMEOUT",
    "process_exists",
]
