from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

import terminal_runtime.tmux_compat as tmux_compat
from ccbd.services.project_namespace_runtime.backend import (
    apply_pane_identity,
    create_window,
    create_session,
    ensure_server_policy,
    ensure_window,
    find_window,
    list_windows,
    prepare_server,
    respawn_pane,
    set_pane_user_option,
    session_alive,
    split_pane,
    wait_for_root_pane,
)
from terminal_runtime.tmux_readiness import TmuxTransientServerUnavailable
from terminal_runtime.placeholders import pane_placeholder_argv
from terminal_runtime.mux_backend_contract import MuxCommandError
from terminal_runtime.windows_shell_log_builder import clipboard_pipe_command

_TMUX_UPDATE_ENVIRONMENT_FOR_TEST = (
    'TERM TERM_PROGRAM TERM_PROGRAM_VERSION DISPLAY WAYLAND_DISPLAY XDG_RUNTIME_DIR '
    'WSL_DISTRO_NAME WSL_INTEROP SSH_AUTH_SOCK SSH_CONNECTION KITTY_WINDOW_ID '
    'WEZTERM_EXECUTABLE WEZTERM_PANE WEZTERM_UNIX_SOCKET CCB_WORKBENCH_PROFILE '
    'CCB_WORKBENCH_FORCE_RICH CCB_WORKBENCH_ROOT CCB_WORKBENCH_TERMINAL_PROGRAM '
    'CCB_WORKBENCH_TERMINAL_PROGRAM_VERSION CCB_WORKBENCH_YAZI_SAFE_CONFIG '
    'CCB_WORKBENCH_YAZI_RICH_CONFIG AGENT_ROLES_STORE'
)


def _clipboard_pipe_command_for_test() -> str:
    return clipboard_pipe_command()


class _FlakyBackend:
    def __init__(self) -> None:
        self.calls: list[tuple[str, ...]] = []
        self._remaining_failures: dict[tuple[str, ...], int] = {}
        self.session_created = False
        self.require_session_for_server_policy = False
        self.missing_session_stderr: str | None = None

    def fail_once(self, *args: str) -> None:
        self._remaining_failures[tuple(args)] = 1

    def _tmux_run(self, args, *, check=False, capture=False, timeout=None):
        del check, capture, timeout
        key = tuple(str(item) for item in args)
        self.calls.append(key)
        if key[:1] == ('new-session',):
            self.session_created = True
        remaining = int(self._remaining_failures.get(key, 0))
        if remaining > 0:
            self._remaining_failures[key] = remaining - 1
            return subprocess.CompletedProcess(
                ['tmux', *key],
                1,
                stdout='',
                stderr='no server running on /tmp/ccb-runtime/test.sock\n',
            )
        if key[:2] == ('set-option', '-g') and self.require_session_for_server_policy and not self.session_created:
            return subprocess.CompletedProcess(
                ['tmux', *key],
                1,
                stdout='',
                stderr='no server running on /tmp/ccb-runtime/test.sock\n',
            )
        if key[:1] == ('list-windows',):
            return subprocess.CompletedProcess(
                ['tmux', *key],
                0,
                stdout='@1\tcmd\t1\n@2\tworkspace\t0\n',
                stderr='',
            )
        if key[:2] == ('has-session', '-t'):
            missing_stderr = self.missing_session_stderr or f"can't find session: {key[2]}\n"
            return subprocess.CompletedProcess(
                ['tmux', *key],
                0 if self.session_created else 1,
                stdout='',
                stderr='' if self.session_created else missing_stderr,
            )
        if key[:2] == ('list-panes', '-t'):
            return subprocess.CompletedProcess(
                ['tmux', *key],
                0,
                stdout='%7\n',
                stderr='',
            )
        return subprocess.CompletedProcess(['tmux', *key], 0, stdout='', stderr='')


class _UnavailableMuxBackend:
    backend_family = 'tmux-family'

    def namespace_ref(self, *, session_name):
        return {
            'backend_family': 'tmux-family',
            'backend_impl': 'rmux',
            'namespace_id': session_name,
            'session_name': session_name,
            'ipc_kind': 'named_pipe',
            'ipc_ref': session_name,
        }

    def session_alive(self, namespace, *, timeout_s=None):
        del namespace, timeout_s
        raise MuxCommandError(
            category='transient-unavailable',
            backend_impl='rmux',
            operation='session_alive',
            detail=r'error connecting to \\.\pipe\rmux-demo (No such file or directory)',
        )


class _RecordingMuxBackend:
    backend_family = 'tmux-family'
    backend_impl = 'rmux'
    namespace = 'project-namespace-id'

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict, dict]] = []

    def namespace_ref(self, *, session_name):
        return {
            'backend_family': 'tmux-family',
            'backend_impl': 'rmux',
            'namespace_id': session_name,
            'session_name': session_name,
            'ipc_kind': 'named_pipe',
            'ipc_ref': session_name,
        }

    def pane_ref(self, pane_id, *, session_name, window_name=None):
        return {
            'backend_impl': 'rmux',
            'pane_id': pane_id,
            'session_name': session_name,
            'window_name': window_name,
        }

    def split_pane(self, parent, **kwargs):
        self.calls.append(('split_pane', dict(parent), dict(kwargs)))
        return self.pane_ref('%1', session_name=parent['session_name'], window_name=parent.get('window_name'))

    def respawn_pane(self, pane, **kwargs):
        self.calls.append(('respawn_pane', dict(pane), dict(kwargs)))

    def set_pane_user_option(self, pane, name, value):
        self.calls.append(('set_pane_user_option', dict(pane), {'name': name, 'value': value}))

    def set_pane_identity(self, pane, **kwargs):
        self.calls.append(('set_pane_identity', dict(pane), dict(kwargs)))


class _CanonicalizingMuxBackend(_RecordingMuxBackend):
    def _run_checked(self, args, *, operation, timeout_s=None):
        self.calls.append(('_run_checked', {}, {'args': tuple(args), 'operation': operation, 'timeout_s': timeout_s}))
        if tuple(args[:3]) == ('list-panes', '-t', 'ccb-session:workspace'):
            return subprocess.CompletedProcess(['rmux', *args], 0, stdout='%1\t0\n%2\t1\n', stderr='')
        if tuple(args) == ('list-panes', '-a', '-F', '#{pane_id}\t#{pane_index}'):
            return subprocess.CompletedProcess(['rmux', *args], 0, stdout='%1\t0\n', stderr='')
        if tuple(args[:3]) == ('list-panes', '-a', '-F'):
            return subprocess.CompletedProcess(['rmux', *args], 0, stdout='other\t%9\t0\nccb-session\t%1\t0\n', stderr='')
        return subprocess.CompletedProcess(['rmux', *args], 1, stdout='', stderr="can't find pane: %0\n")


def test_prepare_server_then_create_session_and_clipboard_policy_retry_transient_tmux_failures(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv('CCB_TMUX_OBJECT_READY_POLL_INTERVAL_S', '0')
    monkeypatch.setenv('DISPLAY', ':99')
    monkeypatch.setenv('AGENT_ROLES_STORE', '/home/demo/.roles')
    backend = _FlakyBackend()
    backend.fail_once('start-server')
    backend.fail_once('set-option', '-g', 'destroy-unattached', 'off')
    backend.fail_once(
        'new-session',
        '-d',
        '-x',
        '160',
        '-y',
        '48',
        '-s',
        'ccb-proj',
        '-n',
        'cmd',
        '-c',
        str(tmp_path),
        *pane_placeholder_argv(),
    )

    prepare_server(backend)
    create_session(backend, session_name='ccb-proj', project_root=tmp_path, window_name='cmd')
    ensure_server_policy(backend)

    assert backend.calls.count(('start-server',)) == 2
    assert backend.calls.count(('set-option', '-g', 'destroy-unattached', 'off')) == 2
    assert backend.calls.count(('set-option', '-g', 'mouse', 'on')) == 1
    assert backend.calls.count(('set-option', '-g', 'history-limit', '50000')) == 1
    assert backend.calls.count(('set-option', '-g', 'set-clipboard', 'on')) == 1
    assert backend.calls.count(('set-option', '-g', 'focus-events', 'on')) == 1
    assert backend.calls.count(('set-option', '-g', 'escape-time', '10')) == 1
    assert backend.calls.count(('set-option', '-g', 'allow-passthrough', 'on')) == 1
    assert backend.calls.count(('set-window-option', '-g', 'mode-keys', 'vi')) == 1
    assert backend.calls.count(('bind-key', '-T', 'copy-mode-vi', 'v', 'send-keys', '-X', 'begin-selection')) == 1
    assert ('bind-key', '-T', 'copy-mode-vi', 'y', 'send-keys', '-X', 'copy-selection-and-cancel') not in backend.calls
    assert any(
        call[:7] == ('bind-key', '-T', 'copy-mode-vi', 'y', 'send-keys', '-X', 'copy-pipe-and-cancel')
        and 'xclip -selection clipboard <"$tmp"' in call[7]
        and 'exec xclip' not in call[7]
        for call in backend.calls
    )
    assert ('set-environment', '-g', 'DISPLAY', ':99') in backend.calls
    assert ('set-environment', '-g', 'AGENT_ROLES_STORE', '/home/demo/.roles') in backend.calls
    assert backend.calls.count(('bind-key', 'h', 'select-pane', '-L')) == 1
    assert backend.calls.count(('bind-key', '-r', 'L', 'resize-pane', '-R', '5')) == 1
    assert backend.calls.count(
        (
            'new-session',
            '-d',
            '-x',
            '160',
            '-y',
            '48',
            '-s',
            'ccb-proj',
            '-n',
            'cmd',
            '-c',
            str(tmp_path),
            *pane_placeholder_argv(),
        )
    ) == 2


def test_prepare_server_accepts_fast_probe_timeout(monkeypatch) -> None:
    monkeypatch.setenv('CCB_TMUX_OBJECT_READY_POLL_INTERVAL_S', '0')
    backend = _FlakyBackend()

    prepare_server(backend, timeout_s=0.0)

    assert backend.calls == [('start-server',)]


def test_fresh_namespace_creates_session_before_clipboard_policy(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv('CCB_TMUX_OBJECT_READY_POLL_INTERVAL_S', '0')
    monkeypatch.delenv('DISPLAY', raising=False)
    monkeypatch.delenv('WAYLAND_DISPLAY', raising=False)
    monkeypatch.delenv('XDG_RUNTIME_DIR', raising=False)
    monkeypatch.delenv('WSL_DISTRO_NAME', raising=False)
    monkeypatch.delenv('WSL_INTEROP', raising=False)
    monkeypatch.delenv('SSH_AUTH_SOCK', raising=False)
    monkeypatch.delenv('SSH_CONNECTION', raising=False)
    for key in (
        'TERM',
        'TERM_PROGRAM',
        'TERM_PROGRAM_VERSION',
        'KITTY_WINDOW_ID',
        'WEZTERM_EXECUTABLE',
        'WEZTERM_PANE',
        'WEZTERM_UNIX_SOCKET',
        'CCB_WORKBENCH_PROFILE',
        'CCB_WORKBENCH_FORCE_RICH',
        'CCB_WORKBENCH_ROOT',
        'CCB_WORKBENCH_TERMINAL_PROGRAM',
        'CCB_WORKBENCH_TERMINAL_PROGRAM_VERSION',
        'CCB_WORKBENCH_YAZI_SAFE_CONFIG',
        'CCB_WORKBENCH_YAZI_RICH_CONFIG',
    ):
        monkeypatch.delenv(key, raising=False)
    backend = _FlakyBackend()
    backend.require_session_for_server_policy = True

    create_session(backend, session_name='ccb-proj', project_root=tmp_path, window_name='cmd')
    ensure_server_policy(backend)

    assert backend.calls[0][:1] == ('new-session',)
    assert ('start-server',) not in backend.calls
    assert ('set-option', '-g', 'destroy-unattached', 'off') not in backend.calls[:1]
    assert ('set-option', '-g', 'mouse', 'on') not in backend.calls[:1]
    assert ('set-option', '-g', 'history-limit', '50000') not in backend.calls[:1]
    assert ('set-option', '-g', 'set-clipboard', 'on') not in backend.calls[:1]
    assert ('set-option', '-g', 'focus-events', 'on') not in backend.calls[:1]
    assert ('set-option', '-g', 'escape-time', '10') not in backend.calls[:1]
    expected_policy_calls = [
        ('set-option', '-g', 'destroy-unattached', 'off'),
        ('set-option', '-g', 'mouse', 'on'),
        ('set-option', '-g', 'history-limit', '50000'),
        ('set-option', '-g', 'set-clipboard', 'on'),
        ('set-option', '-g', 'focus-events', 'on'),
        ('set-option', '-g', 'escape-time', '10'),
        ('set-option', '-g', 'allow-passthrough', 'on'),
        ('set-option', '-g', 'update-environment', _TMUX_UPDATE_ENVIRONMENT_FOR_TEST),
        ('set-window-option', '-g', 'mode-keys', 'vi'),
        ('bind-key', '-T', 'copy-mode-vi', 'v', 'send-keys', '-X', 'begin-selection'),
        ('bind-key', '-T', 'copy-mode-vi', 'C-v', 'send-keys', '-X', 'rectangle-toggle'),
        (
            'bind-key',
            '-T',
            'copy-mode-vi',
            'y',
            'send-keys',
            '-X',
            'copy-pipe-and-cancel',
            _clipboard_pipe_command_for_test(),
        ),
        (
            'bind-key',
            '-T',
            'copy-mode-vi',
            'Enter',
            'send-keys',
            '-X',
            'copy-pipe-and-cancel',
            _clipboard_pipe_command_for_test(),
        ),
        (
            'bind-key',
            '-T',
            'copy-mode-vi',
            'MouseDragEnd1Pane',
            'send-keys',
            '-X',
            'copy-pipe-and-cancel',
            _clipboard_pipe_command_for_test(),
        ),
        ('bind-key', 'h', 'select-pane', '-L'),
        ('bind-key', 'j', 'select-pane', '-D'),
        ('bind-key', 'k', 'select-pane', '-U'),
        ('bind-key', 'l', 'select-pane', '-R'),
        ('bind-key', '-r', 'H', 'resize-pane', '-L', '5'),
        ('bind-key', '-r', 'J', 'resize-pane', '-D', '5'),
        ('bind-key', '-r', 'K', 'resize-pane', '-U', '5'),
        ('bind-key', '-r', 'L', 'resize-pane', '-R', '5'),
    ]
    assert backend.calls[-len(expected_policy_calls):] == expected_policy_calls


def test_list_windows_retries_transient_tmux_failures(monkeypatch) -> None:
    monkeypatch.setenv('CCB_TMUX_OBJECT_READY_POLL_INTERVAL_S', '0')
    backend = _FlakyBackend()
    backend.fail_once('list-windows', '-t', 'ccb-proj', '-F', '#{window_id}\t#{window_name}\t#{window_active}')

    windows = list_windows(backend, 'ccb-proj')

    assert [(window.window_id, window.window_name, window.active) for window in windows] == [
        ('@1', 'cmd', True),
        ('@2', 'workspace', False),
    ]
    assert backend.calls.count(('list-windows', '-t', 'ccb-proj', '-F', '#{window_id}\t#{window_name}\t#{window_active}')) == 2


def test_session_alive_retries_transient_tmux_failures(monkeypatch) -> None:
    monkeypatch.setenv('CCB_TMUX_OBJECT_READY_POLL_INTERVAL_S', '0')
    backend = _FlakyBackend()
    backend.session_created = True

    original_tmux_run = backend._tmux_run
    state = {'remaining': 1}

    def _tmux_run(args, *, check=False, capture=False, timeout=None):
        if tuple(str(item) for item in args) == ('has-session', '-t', 'ccb-proj') and state['remaining'] > 0:
            state['remaining'] -= 1
            backend.calls.append(tuple(str(item) for item in args))
            return subprocess.CompletedProcess(
                ['tmux', *args],
                1,
                stdout='',
                stderr='fork failed: resource temporarily unavailable\n',
            )
        return original_tmux_run(args, check=check, capture=capture, timeout=timeout)

    backend._tmux_run = _tmux_run  # type: ignore[method-assign]

    assert session_alive(backend, 'ccb-proj') is True
    assert backend.calls.count(('has-session', '-t', 'ccb-proj')) == 2


def test_session_alive_treats_absent_project_server_as_missing_namespace(monkeypatch) -> None:
    monkeypatch.setenv('CCB_TMUX_OBJECT_READY_POLL_INTERVAL_S', '0')
    backend = _FlakyBackend()
    backend.missing_session_stderr = 'no server running on /tmp/ccb-runtime/test.sock\n'

    assert session_alive(backend, 'ccb-proj') is False
    assert backend.calls.count(('has-session', '-t', 'ccb-proj')) == 1


def test_session_alive_treats_missing_project_socket_as_missing_namespace(monkeypatch) -> None:
    monkeypatch.setenv('CCB_TMUX_OBJECT_READY_POLL_INTERVAL_S', '0')
    backend = _FlakyBackend()
    backend.missing_session_stderr = (
        'error connecting to /tmp/ccb-runtime/test.sock (No such file or directory)\n'
    )

    assert session_alive(backend, 'ccb-proj') is False
    assert backend.calls.count(('has-session', '-t', 'ccb-proj')) == 1


def test_session_alive_treats_unavailable_mux_namespace_as_missing() -> None:
    assert session_alive(_UnavailableMuxBackend(), 'ccb-proj') is False


def test_mux_percent_pane_adapter_preserves_window_name(tmp_path: Path) -> None:
    backend = _RecordingMuxBackend()

    pane_id = split_pane(
        backend,
        target='%0',
        direction='right',
        percent=50,
        project_root=tmp_path,
        session_name='ccb-session',
        window_name='workspace',
    )
    respawn_pane(
        backend,
        '%0',
        cmd='python -c pass',
        cwd=str(tmp_path),
        session_name='ccb-session',
        window_name='workspace',
    )
    set_pane_user_option(
        backend,
        '%0',
        '@ccb_agent',
        'demo',
        session_name='ccb-session',
        window_name='workspace',
    )
    apply_pane_identity(
        backend,
        '%0',
        title='demo',
        agent_label='demo',
        project_id='project-1',
        role='agent',
        slot_key='demo',
        session_name='ccb-session',
        window_name='workspace',
    )

    assert pane_id == '%1'
    assert [call[1]['window_name'] for call in backend.calls] == [
        'workspace',
        'workspace',
        'workspace',
        'workspace',
    ]
    assert [call[1]['session_name'] for call in backend.calls] == [
        'ccb-session',
        'ccb-session',
        'ccb-session',
        'ccb-session',
    ]


def test_mux_percent_pane_adapter_canonicalizes_rmux_index_alias() -> None:
    backend = _CanonicalizingMuxBackend()

    set_pane_user_option(
        backend,
        '%0',
        '@ccb_agent',
        'demo',
        session_name='ccb-session',
        window_name='workspace',
    )
    apply_pane_identity(
        backend,
        '%0',
        title='demo',
        agent_label='demo',
        project_id='project-1',
        role='agent',
        slot_key='demo',
        session_name='ccb-session',
        window_name='workspace',
    )

    assert [call[1]['pane_id'] for call in backend.calls if call[0] in {'set_pane_user_option', 'set_pane_identity'}] == [
        '%1',
        '%1',
    ]
    assert any(call[0] == '_run_checked' and call[2]['args'][:3] == ('list-panes', '-t', 'ccb-session:workspace') for call in backend.calls)


def test_mux_percent_pane_adapter_canonicalizes_rmux_index_alias_without_window_name() -> None:
    backend = _CanonicalizingMuxBackend()

    apply_pane_identity(
        backend,
        '%0',
        title='demo',
        agent_label='demo',
        project_id='project-1',
        role='agent',
        slot_key='demo',
        session_name='ccb-session',
    )

    identity_call = next(call for call in backend.calls if call[0] == 'set_pane_identity')
    assert identity_call[1]['pane_id'] == '%1'
    assert any(call[0] == '_run_checked' and call[2]['args'][:3] == ('list-panes', '-a', '-F') for call in backend.calls)


def test_mux_percent_pane_adapter_canonicalizes_rmux_index_alias_without_session_name() -> None:
    backend = _CanonicalizingMuxBackend()

    apply_pane_identity(
        backend,
        '%0',
        title='demo',
        agent_label='demo',
        project_id='project-1',
        role='agent',
        slot_key='demo',
    )

    identity_call = next(call for call in backend.calls if call[0] == 'set_pane_identity')
    assert identity_call[1]['pane_id'] == '%1'
    assert any(call[0] == '_run_checked' and call[2]['args'] == ('list-panes', '-a', '-F', '#{pane_id}\t#{pane_index}') for call in backend.calls)


def test_mux_respawn_adapter_canonicalizes_replacement_index_alias() -> None:
    class Backend(_CanonicalizingMuxBackend):
        def respawn_pane(self, pane, **kwargs):
            self.calls.append(('respawn_pane', dict(pane), dict(kwargs)))
            return '%0'

    backend = Backend()

    replacement = respawn_pane(
        backend,
        '%0',
        cmd='codex',
        cwd='D:/repo',
        session_name='ccb-session',
        window_name='workspace',
    )

    assert replacement == '%1'
    assert any(call[0] == '_run_checked' and call[2]['args'][:3] == ('list-panes', '-t', 'ccb-session:workspace') for call in backend.calls)


def test_wait_for_root_pane_raises_transient_unavailable_for_fast_probe(monkeypatch) -> None:
    monkeypatch.setenv('CCB_TMUX_OBJECT_READY_POLL_INTERVAL_S', '0')
    backend = _FlakyBackend()
    backend.fail_once('list-panes', '-t', 'ccb-proj:workspace', '-F', '#{pane_id}')

    with pytest.raises(TmuxTransientServerUnavailable):
        wait_for_root_pane(backend, target_window='ccb-proj:workspace', timeout_s=0.0)


def test_find_window_uses_fast_probe_timeout_when_provided(monkeypatch) -> None:
    monkeypatch.setenv('CCB_TMUX_OBJECT_READY_POLL_INTERVAL_S', '0')
    backend = _FlakyBackend()
    backend.fail_once('list-windows', '-t', 'ccb-proj', '-F', '#{window_id}\t#{window_name}\t#{window_active}')

    with pytest.raises(TmuxTransientServerUnavailable):
        find_window(backend, session_name='ccb-proj', window_name='workspace', timeout_s=0.0)
    assert backend.calls.count(('list-windows', '-t', 'ccb-proj', '-F', '#{window_id}\t#{window_name}\t#{window_active}')) == 1


def test_create_window_uses_fast_probe_timeout_when_provided(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv('CCB_TMUX_OBJECT_READY_POLL_INTERVAL_S', '0')
    backend = _FlakyBackend()
    backend.fail_once('list-windows', '-t', 'ccb-proj', '-F', '#{window_id}\t#{window_name}\t#{window_active}')

    record = create_window(
        backend,
        session_name='ccb-proj',
        window_name='workspace',
        project_root=tmp_path,
        timeout_s=0.0,
    )
    assert record.window_name == 'workspace'
    assert backend.calls.count(('list-windows', '-t', 'ccb-proj', '-F', '#{window_id}\t#{window_name}\t#{window_active}')) == 2


def test_ensure_window_uses_fast_probe_timeout_when_provided(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv('CCB_TMUX_OBJECT_READY_POLL_INTERVAL_S', '0')
    backend = _FlakyBackend()
    backend.fail_once('list-windows', '-t', 'ccb-proj', '-F', '#{window_id}\t#{window_name}\t#{window_active}')

    with pytest.raises(TmuxTransientServerUnavailable):
        ensure_window(
            backend,
            session_name='ccb-proj',
            window_name='workspace',
            project_root=tmp_path,
            timeout_s=0.0,
        )
    assert backend.calls.count(('list-windows', '-t', 'ccb-proj', '-F', '#{window_id}\t#{window_name}\t#{window_active}')) == 1


def test_create_session_uses_terminal_size_hint_when_provided(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv('CCB_TMUX_OBJECT_READY_POLL_INTERVAL_S', '0')
    backend = _FlakyBackend()

    create_session(
        backend,
        session_name='ccb-proj',
        project_root=tmp_path,
        window_name='cmd',
        terminal_size=(233, 61),
    )

    assert backend.calls == [
        (
            'new-session',
            '-d',
            '-x',
            '233',
            '-y',
            '61',
            '-s',
            'ccb-proj',
            '-n',
            'cmd',
            '-c',
            str(tmp_path),
            *pane_placeholder_argv(),
        ),
        ('has-session', '-t', 'ccb-proj'),
    ]


def test_create_session_falls_back_to_default_size_when_terminal_size_too_small(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv('CCB_TMUX_OBJECT_READY_POLL_INTERVAL_S', '0')
    backend = _FlakyBackend()

    create_session(
        backend,
        session_name='ccb-proj',
        project_root=tmp_path,
        window_name='cmd',
        terminal_size=(10, 5),
    )

    assert backend.calls == [
        (
            'new-session',
            '-d',
            '-x',
            '160',
            '-y',
            '48',
            '-s',
            'ccb-proj',
            '-n',
            'cmd',
            '-c',
            str(tmp_path),
            *pane_placeholder_argv(),
        ),
        ('has-session', '-t', 'ccb-proj'),
    ]


def test_create_session_accepts_fast_probe_timeout(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv('CCB_TMUX_OBJECT_READY_POLL_INTERVAL_S', '0')
    backend = _FlakyBackend()

    create_session(
        backend,
        session_name='ccb-proj',
        project_root=tmp_path,
        window_name='cmd',
        timeout_s=0.0,
    )

    assert backend.calls[0][:2] == ('new-session', '-d')


def test_ensure_clipboard_server_policy_accepts_fast_probe_timeout(monkeypatch) -> None:
    monkeypatch.setenv('CCB_TMUX_OBJECT_READY_POLL_INTERVAL_S', '0')
    backend = _FlakyBackend()

    ensure_server_policy(backend, timeout_s=0.0)

    assert backend.calls[:7] == [
        ('set-option', '-g', 'destroy-unattached', 'off'),
        ('set-option', '-g', 'mouse', 'on'),
        ('set-option', '-g', 'history-limit', '50000'),
        ('set-option', '-g', 'set-clipboard', 'on'),
        ('set-option', '-g', 'focus-events', 'on'),
        ('set-option', '-g', 'escape-time', '10'),
        ('set-option', '-g', 'allow-passthrough', 'on'),
    ]
    assert ('set-option', '-g', 'update-environment', _TMUX_UPDATE_ENVIRONMENT_FOR_TEST) in backend.calls
    assert (
        'bind-key',
        '-T',
        'copy-mode-vi',
        'MouseDragEnd1Pane',
        'send-keys',
        '-X',
        'copy-pipe-and-cancel',
        _clipboard_pipe_command_for_test(),
    ) in backend.calls
    assert backend.calls[-14:] == [
        ('set-window-option', '-g', 'mode-keys', 'vi'),
        ('bind-key', '-T', 'copy-mode-vi', 'v', 'send-keys', '-X', 'begin-selection'),
        ('bind-key', '-T', 'copy-mode-vi', 'C-v', 'send-keys', '-X', 'rectangle-toggle'),
        ('bind-key', '-T', 'copy-mode-vi', 'y', 'send-keys', '-X', 'copy-pipe-and-cancel', _clipboard_pipe_command_for_test()),
        ('bind-key', '-T', 'copy-mode-vi', 'Enter', 'send-keys', '-X', 'copy-pipe-and-cancel', _clipboard_pipe_command_for_test()),
        ('bind-key', '-T', 'copy-mode-vi', 'MouseDragEnd1Pane', 'send-keys', '-X', 'copy-pipe-and-cancel', _clipboard_pipe_command_for_test()),
        ('bind-key', 'h', 'select-pane', '-L'),
        ('bind-key', 'j', 'select-pane', '-D'),
        ('bind-key', 'k', 'select-pane', '-U'),
        ('bind-key', 'l', 'select-pane', '-R'),
        ('bind-key', '-r', 'H', 'resize-pane', '-L', '5'),
        ('bind-key', '-r', 'J', 'resize-pane', '-D', '5'),
        ('bind-key', '-r', 'K', 'resize-pane', '-U', '5'),
        ('bind-key', '-r', 'L', 'resize-pane', '-R', '5'),
    ]


def test_ensure_server_policy_retries_transient_optional_window_policy(monkeypatch) -> None:
    monkeypatch.setenv('CCB_TMUX_OBJECT_READY_POLL_INTERVAL_S', '0')
    backend = _FlakyBackend()
    backend.fail_once('set-window-option', '-g', 'mode-keys', 'vi')

    ensure_server_policy(backend)

    assert backend.calls.count(('set-window-option', '-g', 'mode-keys', 'vi')) == 2
    assert ('bind-key', '-T', 'copy-mode-vi', 'v', 'send-keys', '-X', 'begin-selection') in backend.calls


def test_ensure_server_policy_skips_window_and_keybinding_policy_for_psmux_compat(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv('CCB_TMUX_OBJECT_READY_POLL_INTERVAL_S', '0')
    monkeypatch.setattr(tmux_compat.shutil, 'which', lambda name: str(tmp_path / 'psmux' / 'tmux.EXE') if name == 'tmux' else None)
    backend = _FlakyBackend()
    backend._tmux_base = lambda: ['tmux', '-S', '/tmp/ccb-runtime/test.sock']  # type: ignore[attr-defined]

    ensure_server_policy(backend, timeout_s=0.0)

    assert ('set-option', '-g', 'destroy-unattached', 'off') in backend.calls
    assert ('set-option', '-g', 'update-environment', _TMUX_UPDATE_ENVIRONMENT_FOR_TEST) not in backend.calls
    assert not any(call[:1] == ('set-environment',) for call in backend.calls)
    assert not any(call[:1] == ('set-window-option',) for call in backend.calls)
    assert not any(call[:1] == ('bind-key',) for call in backend.calls)


def test_tmux_compat_subset_ignores_socket_paths_containing_psmux(monkeypatch) -> None:
    monkeypatch.setattr(tmux_compat.shutil, 'which', lambda name: 'C:/bin/tmux.exe' if name == 'tmux' else None)

    class Backend:
        backend_impl = 'tmux'

        def _tmux_base(self):
            return ['tmux', '-S', 'D:/tmp/psmux/socket.sock']

    assert tmux_compat.is_tmux_compat_subset(Backend()) is False


def test_kill_window_accepts_fast_probe_timeout(monkeypatch) -> None:
    monkeypatch.setenv('CCB_TMUX_OBJECT_READY_POLL_INTERVAL_S', '0')
    backend = _FlakyBackend()

    from ccbd.services.project_namespace_runtime.backend import kill_window

    kill_window(backend, target='ccb-proj:@1', timeout_s=0.0)

    assert backend.calls == [('kill-window', '-t', 'ccb-proj:@1')]
