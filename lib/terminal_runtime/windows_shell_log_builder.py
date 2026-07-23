from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Protocol
import base64
import re
import shlex
import shutil


@dataclass(frozen=True)
class ShellResolution:
    shell: str
    flags: tuple[str, ...]
    source: str
    candidates: dict[str, bool]
    fallback_reason: str | None = None
    diagnostic: str = ""


class WindowsCommandBuilder(Protocol):
    def wrap_provider_command(self, cmd: str, *, cwd: str | None) -> str: ...

    def build_pipe_log_command(self, log_path: Path) -> str: ...

    def append_stderr_redirection(self, cmd: str, stderr_log_path: str | None) -> tuple[str, str | None]: ...


def resolve_shell(
    *,
    env_shell: str,
    tmux_default_shell: str,
    process_shell: str,
    fallback_shell: str,
    flags_raw: str = '',
    fallback_flags: str = '',
    which_fn: Callable[[str], str | None] = shutil.which,
) -> ShellResolution:
    shell, source = _select_shell(
        env_shell=env_shell,
        tmux_default_shell=tmux_default_shell,
        process_shell=process_shell,
        fallback_shell=fallback_shell,
    )
    flags = tuple(resolve_shell_flags(shell=shell, flags_raw=flags_raw, fallback_flags=fallback_flags))
    candidates = _candidate_availability(which_fn=which_fn, shell=shell)
    fallback_reason = None
    if source == 'platform-default':
        fallback_reason = 'default_shell_fn'
    elif source == 'fallback':
        fallback_reason = 'explicit_fallback'
    diagnostic = (
        f'source={source}; shell={shell}; flags={" ".join(flags) or "<none>"}; '
        f'candidates={_candidate_text(candidates)}'
    )
    if fallback_reason:
        diagnostic = f'{diagnostic}; fallback_reason={fallback_reason}'
    return ShellResolution(
        shell=shell,
        flags=flags,
        source=source,
        candidates=candidates,
        fallback_reason=fallback_reason,
        diagnostic=diagnostic,
    )


def resolve_shell_flags(*, shell: str, flags_raw: str, fallback_flags: str = '') -> list[str]:
    raw = (flags_raw or '').strip()
    if raw:
        return shlex.split(raw)
    fallback = (fallback_flags or '').strip()
    if fallback:
        return shlex.split(fallback)
    family = _shell_family(shell)
    if family == 'powershell':
        return ['-NoLogo', '-NoProfile', '-Command']
    if family == 'cmd':
        return ['/d', '/s', '/c']
    shell_name = _shell_name(shell)
    if shell_name in {'bash', 'zsh', 'ksh', 'fish'}:
        return ['-l', '-c']
    if shell_name in {'sh', 'dash'}:
        return ['-c']
    return ['-c']


def build_shell_command(*, shell: str, flags: list[str], cmd_body: str) -> str:
    family = _shell_family(shell)
    if family == 'posix':
        argv = [shell, *flags, cmd_body]
        return ' '.join(shlex.quote(arg) for arg in argv)
    if family == 'powershell':
        argv = [
            _quote_windows_token(shell),
            *_powershell_encoded_flags(flags),
            _powershell_encoded_command(cmd_body),
        ]
        return ' '.join(token for token in argv if token)
    if family == 'cmd':
        argv = [_quote_windows_token(shell), *flags, _quote_cmd_body(cmd_body)]
        return ' '.join(token for token in argv if token)
    argv = [shell, *flags, cmd_body]
    return ' '.join(shlex.quote(arg) for arg in argv)


def build_respawn_tmux_args(*, pane_id: str, start_dir: str, full_command: str) -> list[str]:
    args = ['respawn-pane', '-k', '-t', pane_id]
    if start_dir:
        args.extend(['-c', start_dir])
    args.append(full_command)
    return args


def append_stderr_redirection(cmd_body: str, stderr_log_path: str | None, *, shell: str = '') -> tuple[str, str | None]:
    if not stderr_log_path:
        return cmd_body, None
    resolved = str(Path(stderr_log_path).expanduser().resolve())
    Path(resolved).parent.mkdir(parents=True, exist_ok=True)
    family = _shell_family(shell)
    if family == 'powershell':
        target = _quote_path_for_shell(shell, resolved)
        return f'& {{ {cmd_body} }} 2>> {target}', resolved
    if family == 'cmd':
        target = _quote_path_for_shell(shell, resolved)
        return f'{cmd_body} 2>> {target}', resolved
    return f'{cmd_body} 2>> {_quote_path_for_shell(shell, resolved)}', resolved


def build_pipe_log_command(log_path: Path, *, shell: str = '') -> str:
    resolved = str(Path(log_path).expanduser().resolve())
    family = _shell_family(shell)
    if family == 'powershell':
        body = f'$content = [Console]::In.ReadToEnd(); Add-Content -LiteralPath {_quote_path_for_shell(shell, resolved)} -Value $content'
        flags = resolve_shell_flags(shell=shell, flags_raw='')
        return build_shell_command(shell=shell, flags=flags, cmd_body=body)
    elif family == 'cmd':
        body = f'more >> {_quote_path_for_shell(shell, resolved)}'
        flags = resolve_shell_flags(shell=shell, flags_raw='')
        return build_shell_command(shell=shell, flags=flags, cmd_body=body)
    else:
        return f'tee -a {_quote_path_for_shell(shell, resolved)}'


def clipboard_pipe_command() -> str:
    return (
        "sh -lc '"
        "tmp=$(mktemp \"${TMPDIR:-/tmp}/ccb-clipboard.XXXXXX\") || exit 0; "
        "cat >\"$tmp\"; "
        "if command -v wl-copy >/dev/null 2>&1 && [ -n \"${WAYLAND_DISPLAY:-}\" ]; then (wl-copy <\"$tmp\"; rm -f \"$tmp\") >/dev/null 2>&1 & "
        "elif command -v xclip >/dev/null 2>&1 && [ -n \"${DISPLAY:-}\" ]; then (xclip -selection clipboard <\"$tmp\"; rm -f \"$tmp\") >/dev/null 2>&1 & "
        "elif command -v xsel >/dev/null 2>&1 && [ -n \"${DISPLAY:-}\" ]; then (xsel --clipboard --input <\"$tmp\"; rm -f \"$tmp\") >/dev/null 2>&1 & "
        "elif command -v pbcopy >/dev/null 2>&1; then pbcopy <\"$tmp\"; rm -f \"$tmp\"; "
        "elif command -v powershell.exe >/dev/null 2>&1; then powershell.exe -NoProfile -Command \"[Console]::InputEncoding=[System.Text.UTF8Encoding]::new(); Set-Clipboard -Value ([Console]::In.ReadToEnd())\" <\"$tmp\"; rm -f \"$tmp\"; "
        "elif command -v pwsh >/dev/null 2>&1; then pwsh -NoLogo -NoProfile -Command \"[Console]::InputEncoding=[System.Text.UTF8Encoding]::new(); Set-Clipboard -Value ([Console]::In.ReadToEnd())\" <\"$tmp\"; rm -f \"$tmp\"; "
        "else rm -f \"$tmp\"; fi'"
    )


@dataclass(frozen=True)
class DefaultWindowsShellLogBuilder:
    env: Mapping[str, str]
    default_shell_fn: Callable[[], tuple[str, str]]
    which_fn: Callable[[str], str | None] = shutil.which

    def wrap_provider_command(self, cmd: str, *, cwd: str | None) -> str:
        del cwd
        body = (cmd or '').strip()
        if not body:
            raise ValueError('cmd is required')
        resolution = self.resolve_shell(
            env_shell=self.env.get('CCB_TMUX_SHELL', ''),
            tmux_default_shell='',
            process_shell=self._process_shell(),
            flags_raw=self.env.get('CCB_TMUX_SHELL_FLAGS', ''),
        )
        if _shell_family(resolution.shell) == 'powershell':
            body = _translate_posix_exports_for_powershell(body)
        flags = list(resolution.flags)
        if _shell_family(resolution.shell) == 'powershell' and not any(flag.lower() == '-noexit' for flag in flags):
            command_index = next((index for index, flag in enumerate(flags) if flag.lower() in {'-command', '-c'}), len(flags))
            flags.insert(command_index, '-NoExit')
        return build_shell_command(shell=resolution.shell, flags=flags, cmd_body=body)

    def build_pipe_log_command(self, log_path: Path) -> str:
        fallback_shell, _ = self.default_shell_fn()
        resolution = resolve_shell(
            env_shell=self.env.get('CCB_TMUX_SHELL', ''),
            tmux_default_shell='',
            process_shell=self._process_shell(),
            fallback_shell=fallback_shell,
            flags_raw=self.env.get('CCB_TMUX_SHELL_FLAGS', ''),
            which_fn=self.which_fn,
        )
        return build_pipe_log_command(log_path, shell=resolution.shell)

    def append_stderr_redirection(self, cmd: str, stderr_log_path: str | None) -> tuple[str, str | None]:
        if not stderr_log_path:
            return cmd, None
        fallback_shell, _ = self.default_shell_fn()
        resolution = resolve_shell(
            env_shell=self.env.get('CCB_TMUX_SHELL', ''),
            tmux_default_shell='',
            process_shell=self._process_shell(),
            fallback_shell=fallback_shell,
            flags_raw=self.env.get('CCB_TMUX_SHELL_FLAGS', ''),
            which_fn=self.which_fn,
        )
        cmd = (
            _translate_posix_exports_for_powershell(cmd)
            if _shell_family(resolution.shell) == 'powershell'
            else cmd
        )
        return append_stderr_redirection(cmd, stderr_log_path, shell=resolution.shell)

    def resolve_shell(
        self,
        *,
        env_shell: str = '',
        tmux_default_shell: str = '',
        process_shell: str = '',
        fallback_shell: str = '',
        flags_raw: str = '',
        fallback_flags: str = '',
    ) -> ShellResolution:
        fallback_shell_value = fallback_shell
        fallback_flags_value = fallback_flags
        if not fallback_shell_value:
            fallback_shell_value, _ = self.default_shell_fn()
        return resolve_shell(
            env_shell=env_shell,
            tmux_default_shell=tmux_default_shell,
            process_shell=process_shell,
            fallback_shell=fallback_shell_value,
            flags_raw=flags_raw,
            fallback_flags=fallback_flags_value,
            which_fn=self.which_fn,
        )

    def _process_shell(self) -> str:
        return (self.env.get('SHELL') or self.env.get('ComSpec') or '').strip()


def build_windows_shell_log_builder(
    *,
    env: Mapping[str, str] | None = None,
    default_shell_fn: Callable[[], tuple[str, str]],
    which_fn: Callable[[str], str | None] = shutil.which,
) -> DefaultWindowsShellLogBuilder:
    return DefaultWindowsShellLogBuilder(env=dict(env or {}), default_shell_fn=default_shell_fn, which_fn=which_fn)


def _select_shell(
    *,
    env_shell: str,
    tmux_default_shell: str,
    process_shell: str,
    fallback_shell: str,
) -> tuple[str, str]:
    shell = (env_shell or '').strip()
    if shell:
        return shell, 'env-override'
    shell = (tmux_default_shell or '').strip()
    if shell:
        return shell, 'tmux-default-shell'
    shell = (process_shell or '').strip()
    if shell:
        return shell, 'process-shell'
    shell = (fallback_shell or '').strip()
    if shell:
        return shell, 'platform-default'
    return 'bash', 'fallback'


def _candidate_availability(*, which_fn: Callable[[str], str | None], shell: str) -> dict[str, bool]:
    candidates = {
        'pwsh': bool(which_fn('pwsh')),
        'powershell.exe': bool(which_fn('powershell.exe')),
        'powershell': bool(which_fn('powershell')),
        'cmd': bool(which_fn('cmd')),
    }
    shell_name = _shell_name(shell)
    if shell_name and shell_name not in candidates:
        candidates[shell_name] = bool(which_fn(shell))
    return candidates


def _candidate_text(candidates: dict[str, bool]) -> str:
    return ','.join(f'{name}:{int(found)}' for name, found in sorted(candidates.items()))


def _shell_family(shell: str) -> str:
    shell_name = _shell_name(shell)
    if shell_name in {'pwsh', 'powershell'}:
        return 'powershell'
    if shell_name == 'cmd':
        return 'cmd'
    return 'posix'


def _shell_name(shell: str) -> str:
    return str(shell or '').strip().replace('\\', '/').rsplit('/', 1)[-1].lower().removesuffix('.exe')


def _quote_windows_token(value: str) -> str:
    token = str(value or '').strip()
    if not token:
        return "''"
    if any(ch.isspace() for ch in token) or '"' in token:
        return '"' + token.replace('"', '""') + '"'
    return token


def _quote_powershell_body(value: str) -> str:
    token = str(value or '')
    return "'" + token.replace("'", "''") + "'"


def _powershell_encoded_flags(flags: list[str]) -> list[str]:
    rendered: list[str] = []
    command_flag_replaced = False
    for flag in flags:
        if _is_powershell_command_flag(flag):
            if not command_flag_replaced:
                rendered.append('-EncodedCommand')
                command_flag_replaced = True
            continue
        rendered.append(flag)
    if not command_flag_replaced:
        rendered.append('-EncodedCommand')
    return rendered


def _powershell_encoded_command(value: str) -> str:
    return base64.b64encode(str(value or '').encode('utf-16le')).decode('ascii')


def _is_powershell_command_flag(value: str) -> bool:
    return str(value or '').strip().lower() in {
        '-command',
        '-c',
        '-encodedcommand',
        '-enc',
        '-e',
    }


def _quote_cmd_body(value: str) -> str:
    token = str(value or '')
    return '"' + token.replace('"', '""') + '"'


def _quote_path_for_shell(shell: str, path: str) -> str:
    family = _shell_family(shell)
    if family == 'powershell':
        return "'" + path.replace("'", "''") + "'"
    if family == 'cmd':
        return '"' + path.replace('"', '""') + '"'
    return shlex.quote(path)


def _translate_posix_exports_for_powershell(command: str) -> str:
    segments = [segment.strip() for segment in str(command or '').split(';')]
    translated: list[str] = []
    for segment in segments:
        translated.append(_translate_posix_env_segment_for_powershell(segment))
    return '; '.join(segment for segment in translated if segment)


def _translate_posix_env_segment_for_powershell(segment: str) -> str:
    if segment.startswith('export '):
        return _translate_posix_export_for_powershell(segment)
    if segment.startswith('unset '):
        return _translate_posix_unset_for_powershell(segment)
    return segment


def _translate_posix_export_for_powershell(segment: str) -> str:
    try:
        assignments = shlex.split(segment[len('export '):], posix=True)
    except ValueError:
        return segment
    rendered: list[str] = []
    for assignment in assignments:
        name, separator, value = assignment.partition('=')
        if not separator or not _is_posix_env_name(name):
            return segment
        rendered.append(f"$env:{name} = {_quote_powershell_string(value)}")
    return '; '.join(rendered) if rendered else segment


def _translate_posix_unset_for_powershell(segment: str) -> str:
    try:
        names = shlex.split(segment[len('unset '):], posix=True)
    except ValueError:
        return segment
    rendered: list[str] = []
    for name in names:
        if not _is_posix_env_name(name):
            return segment
        rendered.append(f"Remove-Item Env:\\{name} -ErrorAction SilentlyContinue")
    return '; '.join(rendered) if rendered else segment


def _is_posix_env_name(value: str) -> bool:
    return bool(re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', value))


def _quote_powershell_string(value: str) -> str:
    return "'" + str(value or '').replace("'", "''") + "'"
