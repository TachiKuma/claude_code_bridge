from __future__ import annotations

from pathlib import Path

import pytest

import ccbd.system as ccbd_system
import cli.kill_runtime.processes as kill_processes
import process_liveness
import provider_core.runtime_lock as runtime_lock
from ccbd.keeper_runtime.records import KeeperState
from ccbd.keeper_runtime.state import keeper_state_is_running
from ccbd.services.health import HealthMonitor
from ccbd.services.ownership import OwnershipGuard


class _FakeWinApi:
    def __init__(self, *, handle=100, wait_result=None, last_error=0) -> None:
        self.handle = handle
        self.wait_result = wait_result if wait_result is not None else process_liveness.WAIT_TIMEOUT
        self.last_error = last_error
        self.open_calls: list[tuple[int, bool, int]] = []
        self.wait_calls: list[tuple[int, int]] = []
        self.closed: list[int] = []

    def open_process(self, access: int, inherit_handle: bool, pid: int):
        self.open_calls.append((access, inherit_handle, pid))
        return self.handle

    def wait_for_single_object(self, handle, milliseconds: int) -> int:
        self.wait_calls.append((handle, milliseconds))
        return self.wait_result

    def close_handle(self, handle) -> None:
        self.closed.append(handle)

    def get_last_error(self) -> int:
        return self.last_error


class _FakeWinFunction:
    def __init__(self, result=1) -> None:
        self.argtypes = None
        self.restype = None
        self.result = result

    def __call__(self, *_args):
        return self.result


@pytest.mark.parametrize("pid", [None, 0, -1])
def test_invalid_pid_is_dead_without_platform_probe(monkeypatch, pid) -> None:
    monkeypatch.setattr(process_liveness.os, "name", "nt", raising=False)
    fake = _FakeWinApi()
    monkeypatch.setattr(process_liveness, "_winapi", lambda: fake)

    assert process_liveness.process_exists(pid) is False
    assert fake.open_calls == []


def test_windows_alive_uses_handle_probe_without_os_kill(monkeypatch) -> None:
    monkeypatch.setattr(process_liveness.os, "name", "nt", raising=False)
    monkeypatch.setattr(process_liveness.os, "kill", lambda pid, sig: (_ for _ in ()).throw(AssertionError("os.kill used")))
    fake = _FakeWinApi(handle=222, wait_result=process_liveness.WAIT_TIMEOUT)
    monkeypatch.setattr(process_liveness, "_winapi", lambda: fake)

    assert process_liveness.process_exists(123) is True
    assert fake.open_calls == [(process_liveness.PROCESS_LIVENESS_ACCESS, False, 123)]
    assert fake.wait_calls == [(222, 0)]
    assert fake.closed == [222]


def test_windows_exited_and_wait_failed_are_dead(monkeypatch) -> None:
    monkeypatch.setattr(process_liveness.os, "name", "nt", raising=False)

    exited = _FakeWinApi(handle=333, wait_result=process_liveness.WAIT_OBJECT_0)
    monkeypatch.setattr(process_liveness, "_winapi", lambda: exited)
    assert process_liveness.process_exists(123) is False
    assert exited.closed == [333]

    failed = _FakeWinApi(handle=444, wait_result=process_liveness.WAIT_FAILED)
    monkeypatch.setattr(process_liveness, "_winapi", lambda: failed)
    assert process_liveness.process_exists(123) is False
    assert failed.closed == [444]


@pytest.mark.parametrize(
    ("error_code", "expected"),
    [
        (process_liveness.ERROR_ACCESS_DENIED, True),
        (process_liveness.ERROR_INVALID_PARAMETER, False),
        (process_liveness.ERROR_NOT_FOUND, False),
        (99999, False),
    ],
)
def test_windows_open_process_error_mapping(monkeypatch, error_code: int, expected: bool) -> None:
    monkeypatch.setattr(process_liveness.os, "name", "nt", raising=False)
    fake = _FakeWinApi(handle=0, last_error=error_code)
    monkeypatch.setattr(process_liveness, "_winapi", lambda: fake)

    assert process_liveness.process_exists(123) is expected
    assert fake.wait_calls == []
    assert fake.closed == []


def test_windows_api_declares_pointer_sized_handle_signatures(monkeypatch) -> None:
    fake_kernel32 = type(
        "Kernel32",
        (),
        {
            "OpenProcess": _FakeWinFunction(result=222),
            "WaitForSingleObject": _FakeWinFunction(result=process_liveness.WAIT_TIMEOUT),
            "CloseHandle": _FakeWinFunction(result=True),
        },
    )()
    monkeypatch.setattr(
        process_liveness.ctypes,
        "WinDLL",
        lambda name, use_last_error: fake_kernel32,
        raising=False,
    )

    api = process_liveness._WindowsApi()

    assert api.open_process(process_liveness.PROCESS_LIVENESS_ACCESS, False, 123) == 222
    assert fake_kernel32.OpenProcess.restype is process_liveness.wintypes.HANDLE
    assert fake_kernel32.WaitForSingleObject.argtypes == [
        process_liveness.wintypes.HANDLE,
        process_liveness.wintypes.DWORD,
    ]
    assert fake_kernel32.CloseHandle.restype is process_liveness.wintypes.BOOL


def test_posix_liveness_error_mapping(monkeypatch) -> None:
    monkeypatch.setattr(process_liveness.os, "name", "posix", raising=False)
    monkeypatch.setattr(process_liveness, "_proc_pid_state", lambda pid: None)

    monkeypatch.setattr(process_liveness.os, "kill", lambda pid, sig: (_ for _ in ()).throw(ProcessLookupError()))
    assert process_liveness.process_exists(123) is False

    monkeypatch.setattr(process_liveness.os, "kill", lambda pid, sig: (_ for _ in ()).throw(PermissionError()))
    assert process_liveness.process_exists(123) is True

    monkeypatch.setattr(process_liveness.os, "kill", lambda pid, sig: (_ for _ in ()).throw(OSError()))
    assert process_liveness.process_exists(123) is False


def test_posix_zombie_is_dead(monkeypatch) -> None:
    monkeypatch.setattr(process_liveness.os, "name", "posix", raising=False)
    monkeypatch.setattr(process_liveness.os, "kill", lambda pid, sig: None)
    monkeypatch.setattr(process_liveness, "_proc_pid_state", lambda pid: "Z")

    assert process_liveness.process_exists(123) is False


def test_proc_stat_parser_handles_process_names_with_spaces() -> None:
    assert process_liveness._parse_proc_stat_state("123 (python worker) Z 1 2") == "Z"
    assert process_liveness._parse_proc_stat_state("bad") is None


def test_ccbd_system_process_exists_delegates_to_shared_helper(monkeypatch) -> None:
    calls: list[int | None] = []
    monkeypatch.setattr(ccbd_system, "_shared_process_exists", lambda pid: calls.append(pid) or True)

    assert ccbd_system.process_exists(456) is True
    assert calls == [456]


def test_kill_runtime_is_pid_alive_delegates_to_shared_helper(monkeypatch) -> None:
    calls: list[int | None] = []
    monkeypatch.setattr(kill_processes, "_shared_process_exists", lambda pid: calls.append(pid) or True)
    monkeypatch.setattr(kill_processes, "_proc_pid_state", lambda pid: None)

    assert kill_processes.is_pid_alive(789) is True
    assert calls == [789]


def test_runtime_lock_pid_alive_delegates_to_shared_helper(monkeypatch) -> None:
    calls: list[int | None] = []
    monkeypatch.setattr(runtime_lock, "_shared_process_exists", lambda pid: calls.append(pid) or False)

    assert runtime_lock._is_pid_alive(321) is False
    assert calls == [321]


def test_ccbd_default_pid_consumers_use_system_process_exists(monkeypatch) -> None:
    calls: list[int | None] = []
    monkeypatch.setattr(ccbd_system, "_shared_process_exists", lambda pid: calls.append(pid) or True)

    state = KeeperState(
        project_id="proj-1",
        keeper_pid=987,
        started_at="2026-07-21T00:00:00Z",
        last_check_at="2026-07-21T00:00:00Z",
        state="running",
    )

    assert keeper_state_is_running(state) is True
    assert OwnershipGuard.__init__.__kwdefaults__["pid_exists"] is ccbd_system.process_exists
    assert HealthMonitor.__init__.__kwdefaults__["pid_exists"] is ccbd_system.process_exists
    assert calls == [987]


def test_proc_pid_state_reads_from_proc_root(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(process_liveness.os, "name", "posix", raising=False)
    stat_path = tmp_path / "321" / "stat"
    stat_path.parent.mkdir()
    stat_path.write_text("321 (python worker) D 1 2", encoding="utf-8")

    assert process_liveness._proc_pid_state(321, proc_root=tmp_path) == "D"
