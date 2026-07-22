from __future__ import annotations

import shlex
from pathlib import Path

import pytest

from terminal_runtime.windows_shell_log_builder import (
    append_stderr_redirection,
    build_pipe_log_command,
    build_windows_shell_log_builder,
    clipboard_pipe_command,
    resolve_shell,
    resolve_shell_flags,
)


def _which(available: set[str]):
    def _lookup(name: str) -> str | None:
        return name if Path(name).name.lower() in available else None

    return _lookup


def test_resolve_shell_returns_diagnostic_candidate_matrix() -> None:
    resolution = resolve_shell(
        env_shell='',
        tmux_default_shell='',
        process_shell='',
        fallback_shell='pwsh',
        which_fn=_which({'pwsh', 'cmd'}),
    )

    assert resolution.shell == 'pwsh'
    assert resolution.flags == ('-NoLogo', '-NoProfile', '-Command')
    assert resolution.source == 'platform-default'
    assert resolution.fallback_reason == 'default_shell_fn'
    assert resolution.candidates['pwsh'] is True
    assert resolution.candidates['powershell.exe'] is False
    assert resolution.candidates['cmd'] is True
    assert 'source=platform-default' in resolution.diagnostic


def test_resolve_shell_preserves_user_override_and_flags() -> None:
    resolution = resolve_shell(
        env_shell=r'C:\Tools\pwsh.exe',
        tmux_default_shell='/bin/bash',
        process_shell='/bin/sh',
        fallback_shell='powershell',
        flags_raw='-NoProfile -Command',
        which_fn=_which({'pwsh.exe'}),
    )

    assert resolution.shell == r'C:\Tools\pwsh.exe'
    assert resolution.flags == ('-NoProfile', '-Command')
    assert resolution.source == 'env-override'


def test_resolve_shell_flags_uses_windows_command_modes() -> None:
    assert resolve_shell_flags(shell='pwsh', flags_raw='') == ['-NoLogo', '-NoProfile', '-Command']
    assert resolve_shell_flags(shell='powershell.exe', flags_raw='') == ['-NoLogo', '-NoProfile', '-Command']
    assert resolve_shell_flags(shell='cmd', flags_raw='') == ['/d', '/s', '/c']


def test_wrap_provider_command_does_not_embed_cwd_as_cd_prefix() -> None:
    builder = build_windows_shell_log_builder(
        env={'CCB_TMUX_SHELL': 'pwsh'},
        default_shell_fn=lambda: ('powershell', '-Command'),
        which_fn=_which({'pwsh'}),
    )

    command = builder.wrap_provider_command('python -m provider', cwd=r'C:\work dir')

    assert command.startswith('pwsh -NoLogo -NoProfile -Command ')
    assert 'python -m provider' in command
    assert 'cd ' not in command
    assert r'C:\work dir' not in command


def test_append_stderr_redirection_uses_shell_specific_path_quoting(tmp_path: Path) -> None:
    log_path = tmp_path / 'stderr logs' / 'provider.err'

    command, resolved = append_stderr_redirection('run-provider', str(log_path), shell='pwsh')

    assert resolved == str(log_path.resolve())
    assert log_path.parent.exists()
    assert command.startswith('& { run-provider } 2>> ')
    assert f"'{resolved}'" in command


def test_cmd_stderr_redirection_uses_cmd_path_quoting(tmp_path: Path) -> None:
    log_path = tmp_path / 'stderr logs' / 'provider.err'

    command, resolved = append_stderr_redirection('run-provider', str(log_path), shell='cmd')

    assert resolved == str(log_path.resolve())
    assert command == f'run-provider 2>> "{resolved}"'


def test_posix_stderr_redirection_keeps_compatible_append(tmp_path: Path) -> None:
    log_path = tmp_path / 'stderr logs' / 'provider.err'

    command, resolved = append_stderr_redirection('run-provider', str(log_path), shell='/bin/sh')

    assert resolved == str(log_path.resolve())
    assert command == f'run-provider 2>> {shlex.quote(resolved)}'


@pytest.mark.parametrize('shell', ['pwsh', 'powershell.exe', 'cmd'])
def test_windows_pipe_log_command_avoids_posix_tee(shell: str, tmp_path: Path) -> None:
    command = build_pipe_log_command(tmp_path / 'pane.log', shell=shell)

    assert 'tee -a' not in command
    assert 'cat ' not in command
    assert 'mktemp' not in command
    assert str((tmp_path / 'pane.log').resolve()) in command


def test_powershell_pipe_log_command_appends_stdin(tmp_path: Path) -> None:
    command = build_pipe_log_command(tmp_path / 'pane.log', shell='pwsh')

    assert command.startswith('pwsh -NoLogo -NoProfile -Command ')
    assert '[Console]::In.ReadToEnd()' in command
    assert 'Add-Content' in command


def test_clipboard_pipe_command_is_builder_owned() -> None:
    command = clipboard_pipe_command()

    assert command.startswith("sh -lc '")
    assert 'Set-Clipboard' in command
