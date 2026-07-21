from __future__ import annotations

import subprocess

import pytest

from terminal_runtime.rmux_backend import RmuxBackend
from terminal_runtime.rmux_runner import RmuxRunner, logical_key_sequence_for_rmux, run_rmux_subprocess


def test_rmux_lifecycle_capture_uses_devnull_stdio_on_windows(monkeypatch) -> None:
    seen: dict[str, object] = {}

    def fake_run(args, **kwargs):
        seen['args'] = args
        seen['kwargs'] = kwargs
        return subprocess.CompletedProcess(args=args, returncode=0)

    monkeypatch.setattr('terminal_runtime.rmux_runner.platform.system', lambda: 'Windows')

    cp = run_rmux_subprocess(['rmux', '-L', 'ccb-demo', 'start-server'], run_fn=fake_run, capture=True)

    assert cp.returncode == 0
    assert seen['kwargs']['stdout'] is subprocess.DEVNULL
    assert seen['kwargs']['stderr'] is subprocess.DEVNULL
    assert 'capture_output' not in seen['kwargs']


def test_rmux_foreground_attach_inherits_stdio_even_when_capture_requested() -> None:
    seen: dict[str, object] = {}

    def fake_run(args, **kwargs):
        seen['args'] = args
        seen['kwargs'] = kwargs
        return subprocess.CompletedProcess(args=args, returncode=0)

    cp = run_rmux_subprocess(['rmux', '-L', 'ccb-demo', 'attach-session', '-t', 'ccb-demo'], run_fn=fake_run, capture=True)

    assert cp.returncode == 0
    assert 'capture_output' not in seen['kwargs']
    assert 'stdout' not in seen['kwargs']
    assert 'stderr' not in seen['kwargs']


def test_rmux_runner_preserves_command_output_for_regular_commands() -> None:
    seen: dict[str, object] = {}

    def fake_run(args, **kwargs):
        seen['args'] = args
        seen['kwargs'] = kwargs
        return subprocess.CompletedProcess(args=args, returncode=7, stdout='out', stderr='err')

    runner = RmuxRunner(rmux_bin='rmux.exe', run_fn=fake_run)

    result = runner.run(['has-session', '-t', 'demo'], timeout_s=2.5)

    assert result.command == ('rmux.exe', 'has-session', '-t', 'demo')
    assert result.returncode == 7
    assert result.stdout == 'out'
    assert result.stderr == 'err'
    assert seen['kwargs']['capture_output'] is True
    assert seen['kwargs']['timeout'] == 2.5


@pytest.mark.parametrize(
    ('key', 'expected'),
    [
        ('C-d', ('C-z', 'Enter')),
        ('Ctrl-D', ('C-z', 'Enter')),
        ('C-c', ('C-c',)),
        ('Enter', ('Enter',)),
    ],
)
def test_logical_key_sequence_for_rmux(key: str, expected: tuple[str, ...]) -> None:
    assert logical_key_sequence_for_rmux(key) == expected


def test_rmux_backend_maps_ctrl_d_to_windows_logical_eof(monkeypatch) -> None:
    calls: list[list[str]] = []
    backend = RmuxBackend(namespace='ccb-demo')

    def fake_tmux_run(args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args=args, returncode=0, stdout='', stderr='')

    monkeypatch.setattr(backend, '_tmux_run', fake_tmux_run)

    assert backend.send_key('%1', 'C-d') is True
    assert calls == [['send-keys', '-t', '%1', 'C-z', 'Enter']]


def test_rmux_backend_tails_nonempty_capture_lines(monkeypatch) -> None:
    backend = RmuxBackend(namespace='ccb-demo')

    def fake_tmux_run(args, **kwargs):
        assert args == ['capture-pane', '-t', '%1', '-p']
        assert kwargs['capture'] is True
        return subprocess.CompletedProcess(
            args=args,
            returncode=0,
            stdout='old\nCCB_RMUX_TRAILING\nCCB_RMUX_LASTN\n\n\n',
            stderr='',
        )

    monkeypatch.setattr(backend, '_tmux_run', fake_tmux_run)

    assert backend.get_pane_content('%1', lines=1) == 'CCB_RMUX_LASTN'
