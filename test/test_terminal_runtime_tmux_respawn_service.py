from __future__ import annotations

import subprocess

import pytest

from terminal_runtime.tmux_respawn_service import TmuxRespawnService


def _cp(
    *,
    stdout: str = '',
    stderr: str = '',
    returncode: int = 0,
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=['tmux'], returncode=returncode, stdout=stdout, stderr=stderr)


def test_tmux_respawn_service_builds_respawn_and_remain_calls() -> None:
    calls: list[list[str]] = []
    service = TmuxRespawnService(
        tmux_run_fn=lambda args, **kwargs: calls.append(args) or (
            _cp(stdout='/bin/bash\n') if args == ['show-option', '-gqv', 'default-shell'] else _cp()
        ),
        ensure_pane_log_fn=lambda pane_id: None,
        normalize_start_dir_fn=lambda cwd: cwd,
        append_stderr_redirection_fn=lambda cmd, path: (cmd + ' 2>>/tmp/err.log', path),
        resolve_shell_fn=lambda **kwargs: '/bin/bash',
        resolve_shell_flags_fn=lambda **kwargs: ['-lc'],
        build_shell_command_fn=lambda **kwargs: '/bin/bash -lc "echo hi"',
        build_respawn_tmux_args_fn=lambda **kwargs: ['respawn-pane', '-k', '-t', kwargs['pane_id'], '/bin/bash -lc "echo hi"'],
        default_shell_fn=lambda: ('bash', '-c'),
        env={'SHELL': '/bin/bash'},
    )

    service.respawn_pane('%9', cmd='echo hi', cwd='/tmp/demo', stderr_log_path='/tmp/err.log', remain_on_exit=True)

    assert calls[0] == ['show-option', '-gqv', 'default-shell']
    assert ['set-option', '-p', '-t', '%9', 'remain-on-exit', 'on'] in calls
    assert ['respawn-pane', '-k', '-t', '%9', '/bin/bash -lc "echo hi"'] in calls


def test_tmux_respawn_service_uses_injected_provider_wrapper_after_stderr() -> None:
    calls: list[list[str]] = []
    wrapped: list[tuple[str, str | None]] = []

    service = TmuxRespawnService(
        tmux_run_fn=lambda args, **kwargs: calls.append(args) or _cp(),
        ensure_pane_log_fn=lambda pane_id: None,
        normalize_start_dir_fn=lambda cwd: '/resolved/work',
        append_stderr_redirection_fn=lambda cmd, path: (cmd + ' STDERR_APPENDED', path),
        resolve_shell_fn=lambda **kwargs: pytest.fail('resolve_shell_fn should not be called when wrapper is injected'),
        resolve_shell_flags_fn=lambda **kwargs: pytest.fail('resolve_shell_flags_fn should not be called when wrapper is injected'),
        build_shell_command_fn=lambda **kwargs: pytest.fail('build_shell_command_fn should not be called when wrapper is injected'),
        build_respawn_tmux_args_fn=lambda **kwargs: [
            'respawn-pane',
            '-k',
            '-t',
            kwargs['pane_id'],
            '-c',
            kwargs['start_dir'],
            kwargs['full_command'],
        ],
        default_shell_fn=lambda: ('bash', '-c'),
        env={'SHELL': '/bin/bash'},
        wrap_provider_command_fn=lambda cmd, *, cwd: wrapped.append((cmd, cwd)) or f'WRAPPED[{cmd}]@{cwd}',
    )

    service.respawn_pane('%9', cmd='echo hi', cwd='/work', stderr_log_path='/tmp/err.log', remain_on_exit=False)

    assert wrapped == [('echo hi STDERR_APPENDED', '/resolved/work')]
    assert ['respawn-pane', '-k', '-t', '%9', '-c', '/resolved/work', 'WRAPPED[echo hi STDERR_APPENDED]@/resolved/work'] in calls


def test_tmux_respawn_service_requires_pane_and_cmd() -> None:
    service = TmuxRespawnService(
        tmux_run_fn=lambda args, **kwargs: _cp(),
        ensure_pane_log_fn=lambda pane_id: None,
        normalize_start_dir_fn=lambda cwd: cwd,
        append_stderr_redirection_fn=lambda cmd, path: (cmd, path),
        resolve_shell_fn=lambda **kwargs: '/bin/bash',
        resolve_shell_flags_fn=lambda **kwargs: ['-lc'],
        build_shell_command_fn=lambda **kwargs: 'x',
        build_respawn_tmux_args_fn=lambda **kwargs: ['respawn-pane'],
        default_shell_fn=lambda: ('bash', '-c'),
        env={},
    )

    try:
        service.respawn_pane('', cmd='echo hi')
        assert False
    except ValueError:
        pass


@pytest.mark.parametrize(
    ('failure_stderr',),
    [
        ('fork failed: Device not configured\n',),
        ('no server running on /tmp/ccb-runtime/test.sock\n',),
        ('server exited unexpectedly\n',),
    ],
)
def test_tmux_respawn_service_retries_transient_tmux_failures(
    monkeypatch: pytest.MonkeyPatch,
    failure_stderr: str,
) -> None:
    calls: list[list[str]] = []
    respawn_attempts = 0

    def _tmux_run(args, **kwargs):
        nonlocal respawn_attempts
        calls.append(args)
        if args == ['show-option', '-gqv', 'default-shell']:
            return _cp(stdout='/bin/bash\n')
        if args[:1] == ['respawn-pane']:
            respawn_attempts += 1
            if respawn_attempts == 1:
                return _cp(returncode=1, stderr=failure_stderr)
        return _cp()

    monkeypatch.setattr('terminal_runtime.tmux_respawn_service.time.sleep', lambda _: None)
    service = TmuxRespawnService(
        tmux_run_fn=_tmux_run,
        ensure_pane_log_fn=lambda pane_id: None,
        normalize_start_dir_fn=lambda cwd: cwd,
        append_stderr_redirection_fn=lambda cmd, path: (cmd, path),
        resolve_shell_fn=lambda **kwargs: '/bin/bash',
        resolve_shell_flags_fn=lambda **kwargs: ['-lc'],
        build_shell_command_fn=lambda **kwargs: '/bin/bash -lc "echo hi"',
        build_respawn_tmux_args_fn=lambda **kwargs: ['respawn-pane', '-k', '-t', kwargs['pane_id'], '/bin/bash -lc "echo hi"'],
        default_shell_fn=lambda: ('bash', '-c'),
        env={'SHELL': '/bin/bash'},
    )

    service.respawn_pane('%9', cmd='echo hi')

    assert respawn_attempts == 2
    assert ['respawn-pane', '-k', '-t', '%9', '/bin/bash -lc "echo hi"'] in calls


def test_tmux_respawn_service_uses_shared_ready_budget_for_transient_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    respawn_attempts = 0

    def _tmux_run(args, **kwargs):
        nonlocal respawn_attempts
        if args == ['show-option', '-gqv', 'default-shell']:
            return _cp(stdout='/bin/bash\n')
        if args[:1] == ['respawn-pane']:
            respawn_attempts += 1
            if respawn_attempts < 15:
                return _cp(returncode=1, stderr='no server running on /tmp/ccb-runtime/test.sock\n')
        return _cp()

    tick = {'value': 0.0}

    def _monotonic() -> float:
        current = tick['value']
        tick['value'] += 0.1
        return current

    monkeypatch.setenv('CCB_TMUX_OBJECT_READY_TIMEOUT_S', '1.5')
    monkeypatch.setattr('terminal_runtime.tmux_respawn_service.time.sleep', lambda _: None)
    monkeypatch.setattr('terminal_runtime.tmux_respawn_service.time.monotonic', _monotonic)
    service = TmuxRespawnService(
        tmux_run_fn=_tmux_run,
        ensure_pane_log_fn=lambda pane_id: None,
        normalize_start_dir_fn=lambda cwd: cwd,
        append_stderr_redirection_fn=lambda cmd, path: (cmd, path),
        resolve_shell_fn=lambda **kwargs: '/bin/bash',
        resolve_shell_flags_fn=lambda **kwargs: ['-lc'],
        build_shell_command_fn=lambda **kwargs: '/bin/bash -lc "echo hi"',
        build_respawn_tmux_args_fn=lambda **kwargs: ['respawn-pane', '-k', '-t', kwargs['pane_id'], '/bin/bash -lc "echo hi"'],
        default_shell_fn=lambda: ('bash', '-c'),
        env={'SHELL': '/bin/bash'},
    )

    service.respawn_pane('%9', cmd='echo hi')

    assert respawn_attempts == 15


def test_tmux_respawn_service_does_not_retry_non_transient_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []
    respawn_attempts = 0

    def _tmux_run(args, **kwargs):
        nonlocal respawn_attempts
        calls.append(args)
        if args == ['show-option', '-gqv', 'default-shell']:
            return _cp(stdout='/bin/bash\n')
        if args[:1] == ['respawn-pane']:
            respawn_attempts += 1
            return _cp(returncode=1, stderr='pane not found\n')
        return _cp()

    monkeypatch.setattr('terminal_runtime.tmux_respawn_service.time.sleep', lambda _: None)
    service = TmuxRespawnService(
        tmux_run_fn=_tmux_run,
        ensure_pane_log_fn=lambda pane_id: None,
        normalize_start_dir_fn=lambda cwd: cwd,
        append_stderr_redirection_fn=lambda cmd, path: (cmd, path),
        resolve_shell_fn=lambda **kwargs: '/bin/bash',
        resolve_shell_flags_fn=lambda **kwargs: ['-lc'],
        build_shell_command_fn=lambda **kwargs: '/bin/bash -lc "echo hi"',
        build_respawn_tmux_args_fn=lambda **kwargs: ['respawn-pane', '-k', '-t', kwargs['pane_id'], '/bin/bash -lc "echo hi"'],
        default_shell_fn=lambda: ('bash', '-c'),
        env={'SHELL': '/bin/bash'},
    )

    with pytest.raises(RuntimeError, match='respawn pane failed: pane not found'):
        service.respawn_pane('%9', cmd='echo hi')

    assert respawn_attempts == 1

    try:
        service.respawn_pane('%1', cmd='  ')
        assert False
    except ValueError:
        pass
