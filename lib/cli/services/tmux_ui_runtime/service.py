from __future__ import annotations

import shlex

from terminal_runtime.env import is_windows
from terminal_runtime.tmux_compat import is_tmux_compat_subset
from terminal_runtime.tmux_theme import render_tmux_session_theme

from .helpers import build_tmux_backend, detect_ccb_version, script_path
from .tmux import active_session_pane_id, pane_option_value, tmux_run


def apply_project_tmux_ui(
    *,
    tmux_socket_path: str,
    tmux_session_name: str,
    ccbd_socket_path: str | None = None,
    backend=None,
) -> None:
    socket_path = str(tmux_socket_path or '').strip()
    session_name = str(tmux_session_name or '').strip()
    if not socket_path or not session_name:
        return
    resolved_backend = backend or build_tmux_backend(socket_path)
    if resolved_backend is None:
        return
    if is_tmux_compat_subset(resolved_backend):
        return

    status_script = script_path('ccb-status.sh')
    border_script = script_path('ccb-border.sh')
    git_script = script_path('ccb-git.sh')
    shell_commands_supported = _shell_commands_supported(resolved_backend)
    if not shell_commands_supported:
        status_script = None
        border_script = None
        git_script = None
    ccb_version = detect_ccb_version()
    rendered_theme = render_tmux_session_theme(
        ccb_version=ccb_version,
        status_script=status_script,
        git_script=git_script,
    )

    _apply_session_theme(resolved_backend, session_name=session_name, rendered_theme=rendered_theme)
    _apply_sidebar_mouse_controls(
        resolved_backend,
        tmux_socket_path=socket_path,
        session_name=session_name,
        shell_commands_supported=shell_commands_supported,
    )
    _apply_pane_theme(
        resolved_backend,
        session_name=session_name,
        border_script=border_script,
        rendered_theme=rendered_theme,
    )
    _apply_active_pane_border(
        resolved_backend,
        session_name=session_name,
        rendered_theme=rendered_theme,
    )


def _shell_commands_supported(backend) -> bool:
    backend_impl = str(getattr(backend, 'backend_impl', '') or '').strip().lower()
    return not (is_windows() and backend_impl == 'rmux')


def _apply_session_theme(backend, *, session_name: str, rendered_theme) -> None:
    for option, value in rendered_theme.session_options.items():
        if option == 'status-format[0]':
            # `status-format` is an array option. Setting index 0 alone leaves
            # inherited/old hint rows at [1+]. Setting the array root clears it,
            # then setting [0] preserves the full tmux format string safely.
            tmux_run(backend, ['set-option', '-t', session_name, 'status-format', 'CCB_CLEAR'])
            tmux_run(backend, ['set-option', '-t', session_name, 'status-format[0]', value])
            continue
        tmux_run(backend, ['set-option', '-t', session_name, option, value])


def _apply_sidebar_mouse_controls(
    backend,
    *,
    tmux_socket_path: str,
    session_name: str,
    shell_commands_supported: bool = True,
) -> None:
    tmux_socket = str(tmux_socket_path or '').strip()
    if not tmux_socket:
        return
    default_action = 'select-pane -t = ; send-keys -M'
    settings_action = 'select-pane -t = ; send-keys -t = c'
    kill_action = 'select-pane -t = ; send-keys -t = Q'
    wheel_up_action = (
        'if-shell -F -t = "#{pane_in_mode}" '
        '{ send-keys -t = -M } { copy-mode -e -t = ; send-keys -t = -X -N 2 scroll-up }'
    )
    wheel_down_action = (
        'if-shell -F -t = "#{pane_in_mode}" '
        '{ send-keys -t = -M } { copy-mode -e -t = ; send-keys -t = -X -N 2 scroll-down }'
    )
    for key in (
        'MouseDown1Pane',
        'MouseDown1Border',
        'MouseDown3Pane',
        'M-MouseDown3Pane',
        'WheelUpPane',
        'WheelDownPane',
    ):
        tmux_run(backend, ['unbind-key', '-T', 'root', key])
    tmux_run(
        backend,
        [
            'bind-key',
            '-T',
            'root',
            'MouseDown1Pane',
            'if-shell',
            '-F',
            '-t',
            '=',
            _sidebar_settings_click_condition(),
            settings_action,
            (
                'if-shell -F -t = '
                + shlex.quote(_sidebar_kill_click_condition())
                + ' '
                + shlex.quote(kill_action)
                + ' '
                + shlex.quote(default_action)
            ),
        ],
    )
    tmux_run(
        backend,
        [
            'bind-key',
            '-T',
            'root',
            'MouseDown1Border',
            'if-shell',
            '-F',
            '-t',
            '=',
            _sidebar_settings_click_condition(),
            settings_action,
            (
                'if-shell -F -t = '
                + shlex.quote(_sidebar_kill_click_condition())
                + ' '
                + shlex.quote(kill_action)
                + ' '
                + shlex.quote(_sidebar_top_border_action(default_action))
            ),
        ],
    )
    tmux_run(
        backend,
        [
            'bind-key',
            '-T',
            'root',
            'WheelUpPane',
            'if-shell',
            '-F',
            '-t',
            '=',
            '#{==:#{@ccb_role},sidebar}',
            default_action,
            wheel_up_action,
        ],
    )
    tmux_run(
        backend,
        [
            'bind-key',
            '-T',
            'root',
            'WheelDownPane',
            'if-shell',
            '-F',
            '-t',
            '=',
            '#{==:#{@ccb_role},sidebar}',
            default_action,
            wheel_down_action,
        ],
    )
    tmux_run(
        backend,
        [
            'bind-key',
            '-T',
            'root',
            'MouseDown3Pane',
            'if-shell',
            '-F',
            '-t',
            '=',
            '#{==:#{@ccb_role},sidebar}',
            default_action,
            'paste-buffer -p',
        ],
    )
    if not shell_commands_supported:
        return
    tmux_run(
        backend,
        [
            'bind-key',
            '-T',
            'root',
            'MouseDrag1Border',
            'resize-pane',
            '-M',
        ],
    )
    tmux_run(
        backend,
        [
            'set-hook',
            '-t',
            session_name,
            'after-resize-pane',
            'run-shell -b '
            + shlex.quote(
                _sidebar_resize_sync_shell(
                    tmux_socket,
                    session_name=session_name,
                    ccb_program=script_path('ccb') or 'ccb',
                )
            ),
        ],
    )
    tmux_run(
        backend,
        [
            'set-hook',
            '-g',
            'window-resized',
            'run-shell -b '
            + shlex.quote(
                _sidebar_window_resize_sync_shell(
                    tmux_socket,
                    session_name=session_name,
                    ccb_program=script_path('ccb') or 'ccb',
                )
            ),
        ],
    )


def _sidebar_resize_sync_shell(
    tmux_socket_path: str,
    *,
    session_name: str,
    ccb_program: str = 'ccb',
) -> str:
    quoted_socket = shlex.quote(tmux_socket_path)
    quoted_session = shlex.quote(session_name)
    quoted_ccb = shlex.quote(str(ccb_program or 'ccb'))
    return (
        'current_session="#{session_name}"; '
        f'[ "$current_session" = {quoted_session} ] || exit 0; '
        f'guard=$(tmux -S {quoted_socket} show-option -qv -t {quoted_session} @ccb_sidebar_sync_guard 2>/dev/null || true); '
        '[ "$guard" = "1" ] && exit 0; '
        f'{quoted_ccb} __sidebar-resize-sync '
        f'--tmux-socket {quoted_socket} '
        f'--session {quoted_session} '
        '--source-pane "#{pane_id}" '
        '--project-id "#{@ccb_project_id}" '
        '>/dev/null 2>&1 || true'
    )


def _sidebar_settings_click_condition() -> str:
    header_row = _sidebar_header_row_condition()
    relative_settings_col = (
        '#{||:'
        '#{==:#{mouse_x},#{e|-:#{pane_width},4}},'
        '#{==:#{mouse_x},#{e|-:#{pane_width},3}}'
        '}'
    )
    absolute_settings_col = (
        '#{||:'
        '#{==:#{mouse_x},#{e|+:#{pane_left},#{e|-:#{pane_width},4}}},'
        '#{==:#{mouse_x},#{e|+:#{pane_left},#{e|-:#{pane_width},3}}}'
        '}'
    )
    settings_col = f'#{{||:{relative_settings_col},{absolute_settings_col}}}'
    return f'#{{&&:#{{==:#{{@ccb_role}},sidebar}},#{{&&:{header_row},{settings_col}}}}}'


def _sidebar_kill_click_condition() -> str:
    header_row = _sidebar_header_row_condition()
    relative_kill_col = '#{==:#{mouse_x},#{e|-:#{pane_width},2}}'
    absolute_kill_col = '#{==:#{mouse_x},#{e|+:#{pane_left},#{e|-:#{pane_width},2}}}'
    kill_col = f'#{{||:{relative_kill_col},{absolute_kill_col}}}'
    return f'#{{&&:#{{==:#{{@ccb_role}},sidebar}},#{{&&:{header_row},{kill_col}}}}}'


def _sidebar_top_border_action(default_action: str) -> str:
    return (
        'if-shell -F -t = '
        + shlex.quote(_sidebar_top_border_click_condition())
        + ' '
        + shlex.quote(default_action)
        + ' '
        + shlex.quote('select-pane -M')
    )


def _sidebar_top_border_click_condition() -> str:
    return f'#{{&&:#{{==:#{{@ccb_role}},sidebar}},{_sidebar_header_row_condition()}}}'


def _sidebar_header_row_condition() -> str:
    return '#{||:#{==:#{mouse_y},0},#{==:#{mouse_y},#{pane_top}}}'


def _sidebar_window_resize_sync_shell(
    tmux_socket_path: str,
    *,
    session_name: str,
    ccb_program: str = 'ccb',
) -> str:
    quoted_socket = shlex.quote(tmux_socket_path)
    quoted_session = shlex.quote(session_name)
    quoted_ccb = shlex.quote(str(ccb_program or 'ccb'))
    return (
        'current_session="#{session_name}"; '
        f'[ "$current_session" = {quoted_session} ] || exit 0; '
        f'guard=$(tmux -S {quoted_socket} show-option -qv -t {quoted_session} @ccb_sidebar_sync_guard 2>/dev/null || true); '
        '[ "$guard" = "1" ] && exit 0; '
        f'{quoted_ccb} __sidebar-resize-sync '
        f'--tmux-socket {quoted_socket} '
        f'--session {quoted_session} '
        '--source-window "#{window_id}" '
        '--project-id "#{@ccb_project_id}" '
        '--from-stored-width '
        '>/dev/null 2>&1 || true'
    )


def _apply_pane_theme(backend, *, session_name: str, border_script: str | None, rendered_theme) -> None:
    windows = _session_windows(backend, session_name=session_name)
    targets = windows or (session_name,)
    active_window_styles = _active_window_pane_styles(backend, session_name=session_name)
    for target in targets:
        window_name = _window_name_from_target(session_name=session_name, target=target)
        window_styles = active_window_styles.get(window_name, {})
        options = dict(rendered_theme.window_options)
        options.update(window_styles)
        for option, value in options.items():
            tmux_run(backend, ['set-window-option', '-t', target, option, value])
        for option in ('window-style', 'window-active-style'):
            if option not in options:
                tmux_run(backend, ['set-window-option', '-u', '-t', target, option])
    if border_script is not None:
        hook = _border_hook_command(border_script)
        tmux_run(backend, ['set-hook', '-t', session_name, 'after-select-pane', hook])


def _apply_active_pane_border(backend, *, session_name: str, rendered_theme) -> None:
    active_pane_id = active_session_pane_id(backend, session_name)
    if not active_pane_id:
        return
    style = (
        pane_option_value(backend, active_pane_id, '@ccb_active_border_style')
        or pane_option_value(backend, active_pane_id, '@ccb_border_style')
        or rendered_theme.window_options.get('pane-active-border-style')
        or 'fg=#7aa2f7,bold'
    )
    tmux_run(
        backend,
        ['set-option', '-p', '-t', active_pane_id, 'pane-active-border-style', style],
    )


def _border_hook_command(border_script: str) -> str:
    quoted_script = shlex.quote(str(border_script))
    shell = f'[ -x {quoted_script} ] || exit 0; {quoted_script} "#{{pane_id}}" >/dev/null 2>&1 || true'
    return 'run-shell -b ' + shlex.quote(shell)


def _session_windows(backend, *, session_name: str) -> tuple[str, ...]:
    try:
        cp = backend._tmux_run(  # type: ignore[attr-defined]
            ['list-windows', '-t', session_name, '-F', '#{window_name}'],
            check=False,
            capture=True,
        )
    except Exception:
        return ()
    if getattr(cp, 'returncode', 0) != 0:
        return ()
    names = []
    for line in str(getattr(cp, 'stdout', '') or '').splitlines():
        name = line.strip()
        if name:
            names.append(f'{session_name}:{name}')
    return tuple(names)


def _active_window_pane_styles(backend, *, session_name: str) -> dict[str, dict[str, str]]:
    try:
        cp = backend._tmux_run(  # type: ignore[attr-defined]
            [
                'list-panes',
                '-a',
                '-F',
                '#{session_name}\t#{window_name}\t#{pane_id}\t#{pane_active}\t#{@ccb_role}\t#{@ccb_border_style}\t#{@ccb_active_border_style}',
            ],
            check=False,
            capture=True,
        )
    except Exception:
        return {}
    if getattr(cp, 'returncode', 0) != 0:
        return {}
    styles: dict[str, dict[str, str]] = {}
    for line in str(getattr(cp, 'stdout', '') or '').splitlines():
        parts = line.split('\t')
        if len(parts) != 7:
            continue
        pane_session, window_name, _pane_id, pane_active, role, border_style, active_border_style = (
            item.strip() for item in parts
        )
        if pane_session != session_name or pane_active != '1' or role not in {'agent', 'tool', 'cmd'}:
            continue
        window_styles: dict[str, str] = {}
        if border_style:
            window_styles['pane-border-style'] = border_style
        if active_border_style:
            window_styles['pane-active-border-style'] = active_border_style
        if window_styles:
            styles[window_name] = window_styles
    return styles


def _window_name_from_target(*, session_name: str, target: str) -> str:
    prefix = f'{session_name}:'
    if target.startswith(prefix):
        return target[len(prefix) :]
    return ''


__all__ = ['apply_project_tmux_ui']
