from __future__ import annotations

from pathlib import Path
import os
import shutil
import subprocess
import sys
import uuid
from types import SimpleNamespace

import pytest

import cli.services.tmux_ui as tmux_ui
import cli.services.tmux_ui_runtime.helpers as tmux_helpers
import cli.services.tmux_ui_runtime.service as tmux_ui_service
import terminal_runtime.tmux_compat as tmux_compat

_BASH = shutil.which('bash')


def test_keeper_import_does_not_cycle_through_tmux_ui() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env['PYTHONPATH'] = str(repo_root / 'lib')

    result = subprocess.run(
        [sys.executable, '-c', 'import ccbd.keeper_main'],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
    )

    assert result.returncode == 0, result.stderr


def test_set_tmux_ui_active_runs_expected_script_from_current_install_root(monkeypatch, tmp_path: Path) -> None:
    config_dir = tmp_path / 'config'
    config_dir.mkdir(parents=True)
    on_script = config_dir / 'ccb-tmux-on.sh'
    off_script = config_dir / 'ccb-tmux-off.sh'
    on_script.write_text('#!/bin/sh\n', encoding='utf-8')
    off_script.write_text('#!/bin/sh\n', encoding='utf-8')

    calls: list[list[str]] = []

    monkeypatch.setenv('TMUX', '/tmp/tmux-1/default,123,0')
    monkeypatch.setattr(tmux_helpers, 'current_install_root', lambda: tmp_path)
    monkeypatch.setattr(tmux_ui.subprocess, 'run', lambda args, **kwargs: calls.append(list(args)))

    tmux_ui.set_tmux_ui_active(True)
    tmux_ui.set_tmux_ui_active(False)

    assert calls == [[str(on_script)], [str(off_script)]]


def test_set_tmux_ui_active_skips_outside_tmux(monkeypatch, tmp_path: Path) -> None:
    calls: list[list[str]] = []

    monkeypatch.delenv('TMUX', raising=False)
    monkeypatch.delenv('TMUX_PANE', raising=False)
    monkeypatch.setattr(tmux_helpers, 'current_install_root', lambda: tmp_path)
    monkeypatch.setattr(tmux_ui.subprocess, 'run', lambda args, **kwargs: calls.append(list(args)))

    tmux_ui.set_tmux_ui_active(True)

    assert calls == []


def test_set_tmux_ui_active_falls_back_to_path_lookup(monkeypatch, tmp_path: Path) -> None:
    path_dir = tmp_path / 'path-bin'
    path_dir.mkdir(parents=True)
    on_script = path_dir / 'ccb-tmux-on.sh'
    on_script.write_text('#!/bin/sh\n', encoding='utf-8')

    calls: list[list[str]] = []

    monkeypatch.setenv('TMUX', '/tmp/tmux-1/default,123,0')
    monkeypatch.setattr(tmux_helpers, 'current_install_root', lambda: tmp_path / 'missing-root')
    monkeypatch.setattr(tmux_helpers.shutil, 'which', lambda name: str(on_script) if name == 'ccb-tmux-on.sh' else None)
    monkeypatch.setattr(tmux_ui.subprocess, 'run', lambda args, **kwargs: calls.append(list(args)))

    tmux_ui.set_tmux_ui_active(True)

    assert calls == [[str(on_script)]]


def test_apply_project_tmux_ui_sets_session_theme_and_hook_from_current_install_root(monkeypatch, tmp_path: Path) -> None:
    config_dir = tmp_path / 'config'
    config_dir.mkdir(parents=True)
    for script_name in ('ccb-status.sh', 'ccb-border.sh', 'ccb-git.sh'):
        (config_dir / script_name).write_text('#!/bin/sh\n', encoding='utf-8')
    (tmp_path / 'VERSION').write_text('9.9.9\n', encoding='utf-8')

    calls: list[list[str]] = []

    class FakeBackend:
        def _tmux_run(self, args, *, check=False, capture=False):
            del check
            calls.append(list(args))
            if capture and args[:4] == ['list-panes', '-t', 'ccb-demo', '-F']:
                return SimpleNamespace(returncode=0, stdout='\n%9\n', stderr='')
            if capture and args[:3] == ['list-panes', '-a', '-F']:
                return SimpleNamespace(
                    returncode=0,
                    stdout=(
                        'ccb-demo\tmain\t%8\t0\tsidebar\tfg=#6c7086\tfg=#6c7086\n'
                        'ccb-demo\tmain\t%9\t1\tagent\tfg=#f7768e\tfg=#f7768e,bold\n'
                    ),
                    stderr='',
                )
            if capture and args[:4] == ['display-message', '-p', '-t', '%9']:
                if args[4] == '#{@ccb_role}':
                    return SimpleNamespace(returncode=0, stdout='agent\n', stderr='')
                if args[4] == '#{@ccb_active_border_style}':
                    return SimpleNamespace(returncode=0, stdout='fg=#f7768e,bold\n', stderr='')
                return SimpleNamespace(returncode=0, stdout='', stderr='')
            if capture and args[:4] == ['list-windows', '-t', 'ccb-demo', '-F']:
                return SimpleNamespace(returncode=0, stdout='main\nreview\n', stderr='')
            return SimpleNamespace(returncode=0, stdout='', stderr='')

    monkeypatch.setattr(tmux_helpers, 'current_install_root', lambda: tmp_path)

    tmux_ui.apply_project_tmux_ui(
        tmux_socket_path='/tmp/ccb.sock',
        ccbd_socket_path='/tmp/ccbd.sock',
        tmux_session_name='ccb-demo',
        backend=FakeBackend(),
    )

    assert ['set-option', '-t', 'ccb-demo', 'status', 'on'] in calls
    assert ['set-option', '-t', 'ccb-demo', 'status-format', 'CCB_CLEAR'] in calls
    assert any(
        call[:4] == ['set-option', '-t', 'ccb-demo', 'status-format[0]']
        and 'status-left' in call[4]
        for call in calls
    )
    assert ['set-option', '-u', '-t', 'ccb-demo', 'status-format[1]'] not in calls
    assert ['set-option', '-t', 'ccb-demo', '@ccb_version', '9.9.9'] in calls
    assert ['set-window-option', '-t', 'ccb-demo:main', 'pane-border-status', 'top'] in calls
    assert ['set-window-option', '-t', 'ccb-demo:review', 'pane-border-status', 'top'] in calls
    assert ['set-window-option', '-t', 'ccb-demo:main', 'pane-border-lines', 'heavy'] in calls
    assert ['set-window-option', '-t', 'ccb-demo:review', 'pane-border-lines', 'heavy'] in calls
    assert ['set-window-option', '-t', 'ccb-demo:main', 'pane-border-style', 'fg=#f7768e'] in calls
    assert ['set-window-option', '-t', 'ccb-demo:main', 'pane-active-border-style', 'fg=#f7768e,bold'] in calls
    assert any(
        call[:4] == ['set-window-option', '-t', 'ccb-demo:main', 'pane-border-format']
        for call in calls
    )
    assert any(
        call[:4] == ['set-window-option', '-t', 'ccb-demo:review', 'pane-border-format']
        for call in calls
    )
    assert any(
        call[:4] == ['set-hook', '-t', 'ccb-demo', 'after-select-pane']
        and 'ccb-border.sh' in call[4]
        and '[ -x ' in call[4]
        and 'run-shell -b' in call[4]
        for call in calls
    )
    assert ['unbind-key', '-T', 'root', 'MouseDown1Pane'] in calls
    assert ['unbind-key', '-T', 'root', 'MouseDown1Border'] in calls
    assert ['unbind-key', '-T', 'root', 'MouseDown3Pane'] in calls
    assert ['unbind-key', '-T', 'root', 'M-MouseDown3Pane'] in calls
    assert ['unbind-key', '-T', 'root', 'WheelUpPane'] in calls
    assert ['unbind-key', '-T', 'root', 'WheelDownPane'] in calls
    sidebar_mouse_bindings = [
        call for call in calls if call[:4] == ['bind-key', '-T', 'root', 'MouseDown1Pane']
    ]
    assert len(sidebar_mouse_bindings) == 1
    sidebar_mouse_binding = sidebar_mouse_bindings[0]
    assert sidebar_mouse_binding[:5] == [
        'bind-key',
        '-T',
        'root',
        'MouseDown1Pane',
        'if-shell',
    ]
    assert sidebar_mouse_binding[5] == '-F'
    assert sidebar_mouse_binding[6:8] == ['-t', '#{mouse_pane}']
    assert '#{@ccb_role}' in sidebar_mouse_binding[8]
    assert '#{mouse_x}' in sidebar_mouse_binding[8]
    assert '#{mouse_y}' in sidebar_mouse_binding[8]
    assert sidebar_mouse_binding[9] == 'select-pane -t "#{mouse_pane}" ; send-keys -t "#{mouse_pane}" c'
    assert 'if-shell -F -t "#{mouse_pane}"' in sidebar_mouse_binding[10]
    assert sidebar_mouse_binding[10].count('if-shell -F -t "#{mouse_pane}"') == 1
    assert 'send-keys -t "#{mouse_pane}" Q' in sidebar_mouse_binding[10]
    assert 'select-pane -t "#{mouse_pane}" ; send-keys -t "#{mouse_pane}" -M' in sidebar_mouse_binding[10]
    sidebar_border_bindings = [
        call for call in calls if call[:4] == ['bind-key', '-T', 'root', 'MouseDown1Border']
    ]
    assert len(sidebar_border_bindings) == 1
    sidebar_border_binding = sidebar_border_bindings[0]
    assert sidebar_border_binding[:5] == [
        'bind-key',
        '-T',
        'root',
        'MouseDown1Border',
        'if-shell',
    ]
    assert sidebar_border_binding[5] == '-F'
    assert sidebar_border_binding[6:8] == ['-t', '#{mouse_pane}']
    assert '#{@ccb_role}' in sidebar_border_binding[8]
    assert '#{mouse_y}' in sidebar_border_binding[8]
    assert sidebar_border_binding[9] == 'select-pane -t "#{mouse_pane}" ; send-keys -t "#{mouse_pane}" c'
    assert 'if-shell -F -t "#{mouse_pane}"' in sidebar_border_binding[10]
    assert sidebar_border_binding[10].count('if-shell -F -t "#{mouse_pane}"') == 2
    assert 'send-keys -t "#{mouse_pane}" Q' in sidebar_border_binding[10]
    assert 'select-pane -t "#{mouse_pane}" ; send-keys -t "#{mouse_pane}" -M' in sidebar_border_binding[10]
    assert 'select-pane -M' in sidebar_border_binding[10]
    sidebar_wheel_up_bindings = [
        call for call in calls if call[:4] == ['bind-key', '-T', 'root', 'WheelUpPane']
    ]
    assert len(sidebar_wheel_up_bindings) == 1
    sidebar_wheel_up_binding = sidebar_wheel_up_bindings[0]
    assert sidebar_wheel_up_binding[:5] == [
        'bind-key',
        '-T',
        'root',
        'WheelUpPane',
        'if-shell',
    ]
    assert sidebar_wheel_up_binding[5] == '-F'
    assert sidebar_wheel_up_binding[6:8] == ['-t', '#{mouse_pane}']
    assert sidebar_wheel_up_binding[8] == '#{==:#{@ccb_role},sidebar}'
    assert sidebar_wheel_up_binding[9] == 'select-pane -t "#{mouse_pane}" ; send-keys -t "#{mouse_pane}" -M'
    assert sidebar_wheel_up_binding[10] == (
        'if-shell -F -t "#{mouse_pane}" "#{pane_in_mode}" '
        '{ send-keys -t "#{mouse_pane}" -M } '
        '{ copy-mode -e -t "#{mouse_pane}" ; send-keys -t "#{mouse_pane}" -X -N 2 scroll-up }'
    )
    sidebar_wheel_down_bindings = [
        call for call in calls if call[:4] == ['bind-key', '-T', 'root', 'WheelDownPane']
    ]
    assert len(sidebar_wheel_down_bindings) == 1
    sidebar_wheel_down_binding = sidebar_wheel_down_bindings[0]
    assert sidebar_wheel_down_binding[:5] == [
        'bind-key',
        '-T',
        'root',
        'WheelDownPane',
        'if-shell',
    ]
    assert sidebar_wheel_down_binding[5] == '-F'
    assert sidebar_wheel_down_binding[6:8] == ['-t', '#{mouse_pane}']
    assert sidebar_wheel_down_binding[8] == '#{==:#{@ccb_role},sidebar}'
    assert sidebar_wheel_down_binding[9] == 'select-pane -t "#{mouse_pane}" ; send-keys -t "#{mouse_pane}" -M'
    assert sidebar_wheel_down_binding[10] == (
        'if-shell -F -t "#{mouse_pane}" "#{pane_in_mode}" '
        '{ send-keys -t "#{mouse_pane}" -M } '
        '{ copy-mode -e -t "#{mouse_pane}" ; send-keys -t "#{mouse_pane}" -X -N 2 scroll-down }'
    )
    sidebar_right_click_bindings = [
        call for call in calls if call[:4] == ['bind-key', '-T', 'root', 'MouseDown3Pane']
    ]
    assert len(sidebar_right_click_bindings) == 1
    sidebar_right_click_binding = sidebar_right_click_bindings[0]
    assert sidebar_right_click_binding[:5] == [
        'bind-key',
        '-T',
        'root',
        'MouseDown3Pane',
        'if-shell',
    ]
    assert sidebar_right_click_binding[5] == '-F'
    assert sidebar_right_click_binding[6:8] == ['-t', '#{mouse_pane}']
    assert sidebar_right_click_binding[8] == '#{==:#{@ccb_role},sidebar}'
    assert sidebar_right_click_binding[9] == 'select-pane -t "#{mouse_pane}" ; send-keys -t "#{mouse_pane}" -M'
    assert sidebar_right_click_binding[10] == 'paste-buffer -p'
    assert '__sidebar-click' not in '\n'.join(' '.join(call) for call in calls)
    sidebar_resize_bindings = [
        call for call in calls if call[:4] == ['bind-key', '-T', 'root', 'MouseDrag1Border']
    ]
    assert len(sidebar_resize_bindings) == 1
    sidebar_resize_binding = sidebar_resize_bindings[0]
    assert sidebar_resize_binding == ['bind-key', '-T', 'root', 'MouseDrag1Border', 'resize-pane', '-M']
    sidebar_resize_hooks = [
        call for call in calls if call[:4] == ['set-hook', '-t', 'ccb-demo', 'after-resize-pane']
    ]
    assert len(sidebar_resize_hooks) == 1
    sidebar_resize_hook = sidebar_resize_hooks[0][4]
    assert '__sidebar-resize-sync' in sidebar_resize_hook
    assert '@ccb_sidebar_sync_guard' in sidebar_resize_hook
    assert '--tmux-socket /tmp/ccb.sock' in sidebar_resize_hook
    assert '--session ccb-demo' in sidebar_resize_hook
    assert '--source-pane "#{pane_id}"' in sidebar_resize_hook
    assert '--project-id "#{@ccb_project_id}"' in sidebar_resize_hook
    sidebar_window_resize_hooks = [
        call for call in calls if call[:3] == ['set-hook', '-g', 'window-resized']
    ]
    assert len(sidebar_window_resize_hooks) == 1
    sidebar_window_resize_hook = sidebar_window_resize_hooks[0][3]
    assert '__sidebar-resize-sync' in sidebar_window_resize_hook
    assert '@ccb_sidebar_sync_guard' in sidebar_window_resize_hook
    assert 'current_session="#{session_name}"' in sidebar_window_resize_hook
    assert '--source-window "#{window_id}"' in sidebar_window_resize_hook
    assert '--from-stored-width' in sidebar_window_resize_hook
    assert ['set-option', '-p', '-t', '%9', 'pane-active-border-style', 'fg=#f7768e,bold'] in calls


def test_apply_project_tmux_ui_skips_project_ui_for_psmux_compat_tmux_path(monkeypatch, tmp_path: Path) -> None:
    config_dir = tmp_path / 'config'
    config_dir.mkdir(parents=True)
    for script_name in ('ccb-status.sh', 'ccb-border.sh', 'ccb-git.sh'):
        (config_dir / script_name).write_text('#!/bin/sh\n', encoding='utf-8')
    (tmp_path / 'VERSION').write_text('9.9.9\n', encoding='utf-8')

    calls: list[list[str]] = []

    class FakeBackend:
        backend_impl = 'tmux'

        def _tmux_base(self):
            return ['tmux', '-S', '/tmp/ccb.sock']

        def _tmux_run(self, args, *, check=False, capture=False):
            del check, capture
            calls.append(list(args))
            raise AssertionError(f'project tmux UI command should be skipped: {args!r}')

    monkeypatch.setattr(tmux_helpers, 'current_install_root', lambda: tmp_path)
    monkeypatch.setattr(tmux_compat.shutil, 'which', lambda name: str(tmp_path / 'psmux' / 'tmux.EXE') if name == 'tmux' else None)

    tmux_ui.apply_project_tmux_ui(
        tmux_socket_path='/tmp/ccb.sock',
        tmux_session_name='ccb-demo',
        backend=FakeBackend(),
    )

    assert calls == []


def test_rmux_backend_keeps_project_ui_enabled() -> None:
    class FakeBackend:
        backend_impl = 'rmux'

    assert tmux_compat.is_tmux_compat_subset(FakeBackend()) is False


def test_windows_rmux_project_ui_avoids_shell_status_commands(monkeypatch, tmp_path: Path) -> None:
    config_dir = tmp_path / 'config'
    config_dir.mkdir(parents=True)
    for script_name in ('ccb-status.sh', 'ccb-border.sh', 'ccb-git.sh'):
        (config_dir / script_name).write_text('#!/bin/sh\n', encoding='utf-8')
    (tmp_path / 'VERSION').write_text('9.9.9\n', encoding='utf-8')

    calls: list[list[str]] = []

    class FakeBackend:
        backend_impl = 'rmux'

        def _tmux_run(self, args, *, check=False, capture=False):
            del check
            calls.append(list(args))
            if capture and args[:4] == ['list-panes', '-t', 'ccb-demo', '-F']:
                return SimpleNamespace(returncode=0, stdout='\n%9\n', stderr='')
            if capture and args[:4] == ['display-message', '-p', '-t', '%9']:
                return SimpleNamespace(returncode=0, stdout='', stderr='')
            return SimpleNamespace(returncode=0, stdout='', stderr='')

    monkeypatch.setattr(tmux_helpers, 'current_install_root', lambda: tmp_path)
    monkeypatch.setattr(tmux_ui_service, 'is_windows', lambda: True)

    tmux_ui.apply_project_tmux_ui(
        tmux_socket_path='/tmp/ccb.sock',
        tmux_session_name='ccb-demo',
        backend=FakeBackend(),
    )

    rendered_commands = '\n'.join(' '.join(call) for call in calls)
    assert ['set-option', '-t', 'ccb-demo', '@ccb_version', '9.9.9'] in calls
    assert 'ccb-git.sh' not in rendered_commands
    assert 'ccb-status.sh' not in rendered_commands
    assert 'ccb-border.sh' not in rendered_commands
    assert '#(' not in rendered_commands
    assert 'run-shell' not in rendered_commands
    assert '#{mouse_pane}' not in rendered_commands
    mouse_down_bindings = [call for call in calls if call[:4] == ['bind-key', '-T', 'root', 'MouseDown1Pane']]
    assert len(mouse_down_bindings) == 1
    mouse_down_binding = mouse_down_bindings[0]
    # MouseDown1Pane fallback 改用 rmux 支持的 -t = 定位；条件也必须在鼠标 pane 上求值
    assert mouse_down_binding[:8] == [
        'bind-key',
        '-T',
        'root',
        'MouseDown1Pane',
        'if-shell',
        '-F',
        '-t',
        '=',
    ]
    assert mouse_down_binding[8] == '#{==:#{@ccb_role},sidebar}'
    # sidebar 分支：聚焦并把原始鼠标事件透传给 Rust header_action_at（命中 ⚙/x/agent）
    assert mouse_down_binding[9] == 'select-pane -t = ; send-keys -t = -M'
    # 普通 pane：单击即 focus（rmux -t =），不裸透传 send-keys -M
    assert mouse_down_binding[10] == 'select-pane -t ='
    # 不再出现无 -t 的 select-pane -M 占位，也不再有 mux 层 settings/kill 分发（改由 Rust 命中）
    assert 'select-pane -M' not in '\n'.join(mouse_down_binding)
    assert 'send-keys c' not in '\n'.join(mouse_down_binding)
    assert 'send-keys Q' not in '\n'.join(mouse_down_binding)
    assert '#{mouse_x}' not in '\n'.join(mouse_down_binding)
    assert ['bind-key', '-T', 'root', 'MouseDown1Pane', 'send-keys', '-M'] not in calls
    wheel_up_bindings = [call for call in calls if call[:4] == ['bind-key', '-T', 'root', 'WheelUpPane']]
    assert len(wheel_up_bindings) == 1
    wheel_up_binding = wheel_up_bindings[0]
    assert wheel_up_binding[:8] == ['bind-key', '-T', 'root', 'WheelUpPane', 'if-shell', '-F', '-t', '=']
    assert wheel_up_binding[8] == '#{==:#{@ccb_role},sidebar}'
    assert wheel_up_binding[9] == 'select-pane -t = ; send-keys -t = -M'
    assert wheel_up_binding[10] == 'select-pane -t ='
    assert 'pane_in_mode' not in wheel_up_binding[10]
    assert 'copy-mode -e' not in wheel_up_binding[10]
    assert 'history_size' not in wheel_up_binding[10]
    assert 'alternate_on' not in wheel_up_binding[10]
    assert 'send-keys -X -N 2 scroll-up' not in wheel_up_binding[10]
    assert 'select-pane -M' not in '\n'.join(wheel_up_binding)
    wheel_down_bindings = [call for call in calls if call[:4] == ['bind-key', '-T', 'root', 'WheelDownPane']]
    assert len(wheel_down_bindings) == 1
    wheel_down_binding = wheel_down_bindings[0]
    assert wheel_down_binding[:8] == ['bind-key', '-T', 'root', 'WheelDownPane', 'if-shell', '-F', '-t', '=']
    assert wheel_down_binding[8] == '#{==:#{@ccb_role},sidebar}'
    assert wheel_down_binding[9] == 'select-pane -t = ; send-keys -t = -M'
    assert wheel_down_binding[10] == 'select-pane -t ='
    assert 'pane_in_mode' not in wheel_down_binding[10]
    assert 'copy-mode -e' not in wheel_down_binding[10]
    assert 'history_size' not in wheel_down_binding[10]
    assert 'alternate_on' not in wheel_down_binding[10]
    assert 'send-keys -X -N 2 scroll-down' not in wheel_down_binding[10]
    assert 'select-pane -M' not in '\n'.join(wheel_down_binding)
    assert not [call for call in calls if call[:4] == ['bind-key', '-T', 'root', 'MouseDown3Pane']]
    assert not [call for call in calls if call[:4] == ['bind-key', '-T', 'root', 'M-MouseDown3Pane']]
    assert 'paste-buffer -p' not in rendered_commands


@pytest.mark.skipif(shutil.which('rmux') is None, reason='rmux is required for live binding validation')
def test_rmux_accepts_mouse_context_project_ui_bindings(monkeypatch, tmp_path: Path) -> None:
    session = f'ccb-test-ui-{uuid.uuid4().hex[:12]}'
    repo_root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env['PYTHONPATH'] = str(repo_root / 'lib') + os.pathsep + env.get('PYTHONPATH', '')
    env['CCB_TMUX_UI_TEST_SESSION'] = session
    script = r'''
import os

from cli.services.tmux_ui_runtime.service import _apply_sidebar_mouse_controls
from terminal_runtime.rmux_backend import RmuxBackend
import cli.services.tmux_ui_runtime.service as tmux_ui_service

session = os.environ["CCB_TMUX_UI_TEST_SESSION"]
backend = RmuxBackend(namespace=session, project_root=os.getcwd())
backend._tmux_run(["start-server"], check=False, capture=True)
backend._tmux_run(["new-session", "-d", "-s", session, "-n", "main"], check=False, capture=True)
try:
    tmux_ui_service.is_windows = lambda: True
    _apply_sidebar_mouse_controls(
        backend,
        tmux_socket_path=session,
        session_name=session,
        shell_commands_supported=False,
    )
    result = backend._tmux_run(["list-keys", "-T", "root"], check=False, capture=True)
    text = str(getattr(result, "stdout", "") or "")
    assert result.returncode == 0
    scoped_lines = [
        line
        for line in text.splitlines()
        if any(line.startswith(f"bind-key -T root {key}") for key in (
            "MouseDown1Pane",
            "MouseDown1Border",
            "WheelUpPane",
            "WheelDownPane",
        ))
    ]
    scoped_text = "\n".join(scoped_lines)
    all_key_lines = [line for line in text.splitlines() if line.startswith("bind-key -T root ")]
    for key in ("MouseDown1Pane", "MouseDown1Border", "WheelUpPane", "WheelDownPane"):
        assert key in scoped_text
    assert not any(line.startswith("bind-key -T root MouseDown3Pane") for line in all_key_lines)
    assert not any(line.startswith("bind-key -T root M-MouseDown3Pane") for line in all_key_lines)
    assert "#{mouse_pane}" not in text
    assert "select-pane -t =" in scoped_text
    assert "send-keys -t = -M" in scoped_text
    assert "select-pane -M" not in scoped_text
    mouse_down_matching = [
        line for line in scoped_lines if line.startswith("bind-key -T root MouseDown1Pane")
    ]
    assert len(mouse_down_matching) == 1
    assert "if-shell -F -t =" in mouse_down_matching[0]
    assert "select-pane -t =" in mouse_down_matching[0]
    assert "send-keys -t = -M" in mouse_down_matching[0]
    assert "send-keys c" not in mouse_down_matching[0]
    assert "send-keys Q" not in mouse_down_matching[0]
    for key in ("WheelUpPane", "WheelDownPane"):
        matching = [line for line in scoped_lines if line.startswith(f"bind-key -T root {key}")]
        assert len(matching) == 1
        line = matching[0]
        assert "if-shell -F -t =" in line
        assert "select-pane -t = ; send-keys -t = -M" in line
        assert "pane_in_mode" not in line
        assert "history_size" not in line
        assert "alternate_on" not in line
        assert "copy-mode -e" not in line
        assert "scroll-up" not in line
        assert "scroll-down" not in line
    assert "paste-buffer -p" not in scoped_text
finally:
    backend._tmux_run(["kill-session", "-t", session], check=False, capture=True)
'''

    result = subprocess.run(
        [sys.executable, '-c', script],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
        timeout=30,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout


def test_apply_project_tmux_ui_applies_window_theme_for_contrast_profile(monkeypatch, tmp_path: Path) -> None:
    config_dir = tmp_path / 'config'
    config_dir.mkdir(parents=True)
    for script_name in ('ccb-status.sh', 'ccb-border.sh', 'ccb-git.sh'):
        (config_dir / script_name).write_text('#!/bin/sh\n', encoding='utf-8')
    (tmp_path / 'VERSION').write_text('9.9.9\n', encoding='utf-8')

    calls: list[list[str]] = []

    class FakeBackend:
        def _tmux_run(self, args, *, check=False, capture=False):
            del check
            calls.append(list(args))
            if capture and args[:4] == ['list-panes', '-t', 'ccb-demo', '-F']:
                return SimpleNamespace(returncode=0, stdout='\n%9\n', stderr='')
            if capture and args[:4] == ['display-message', '-p', '-t', '%9']:
                return SimpleNamespace(returncode=0, stdout='', stderr='')
            return SimpleNamespace(returncode=0, stdout='', stderr='')

    monkeypatch.setenv('CCB_TMUX_THEME_PROFILE', 'contrast')
    monkeypatch.setattr(tmux_helpers, 'current_install_root', lambda: tmp_path)

    tmux_ui.apply_project_tmux_ui(
        tmux_socket_path='/tmp/ccb.sock',
        tmux_session_name='ccb-demo',
        backend=FakeBackend(),
    )

    assert ['set-option', '-t', 'ccb-demo', '@ccb_theme_profile', 'contrast'] in calls
    assert ['set-window-option', '-t', 'ccb-demo', 'pane-border-style', 'fg=#565f89,bold'] in calls
    assert ['set-window-option', '-t', 'ccb-demo', 'window-style', 'bg=#181825'] in calls
    assert ['set-window-option', '-t', 'ccb-demo', 'window-active-style', 'bg=#1e1e2e'] in calls


def test_apply_project_tmux_ui_applies_light_profile(monkeypatch, tmp_path: Path) -> None:
    config_dir = tmp_path / 'config'
    config_dir.mkdir(parents=True)
    for script_name in ('ccb-status.sh', 'ccb-border.sh', 'ccb-git.sh'):
        (config_dir / script_name).write_text('#!/bin/sh\n', encoding='utf-8')
    (tmp_path / 'VERSION').write_text('9.9.9\n', encoding='utf-8')

    calls: list[list[str]] = []

    class FakeBackend:
        def _tmux_run(self, args, *, check=False, capture=False):
            del check
            calls.append(list(args))
            if capture and args[:4] == ['list-panes', '-t', 'ccb-demo', '-F']:
                return SimpleNamespace(returncode=0, stdout='\n%9\n', stderr='')
            if capture and args[:4] == ['display-message', '-p', '-t', '%9']:
                return SimpleNamespace(returncode=0, stdout='', stderr='')
            return SimpleNamespace(returncode=0, stdout='', stderr='')

    monkeypatch.setenv('CCB_TMUX_THEME_PROFILE', 'light')
    monkeypatch.setattr(tmux_helpers, 'current_install_root', lambda: tmp_path)

    tmux_ui.apply_project_tmux_ui(
        tmux_socket_path='/tmp/ccb.sock',
        tmux_session_name='ccb-demo',
        backend=FakeBackend(),
    )

    assert ['set-option', '-t', 'ccb-demo', '@ccb_theme_profile', 'light'] in calls
    assert ['set-option', '-t', 'ccb-demo', 'status-style', 'bg=#eff1f5 fg=#4c4f69'] in calls
    assert ['set-window-option', '-t', 'ccb-demo', 'pane-border-style', 'fg=#bcc0cc,bold'] in calls
    assert ['set-window-option', '-t', 'ccb-demo', 'pane-active-border-style', 'fg=#1e66f5,bold'] in calls
    assert ['set-option', '-p', '-t', '%9', 'pane-active-border-style', 'fg=#1e66f5,bold'] in calls
    assert ['set-window-option', '-t', 'ccb-demo', 'window-style', 'bg=#f8fafc'] not in calls
    assert ['set-window-option', '-u', '-t', 'ccb-demo', 'window-style'] in calls
    assert ['set-window-option', '-u', '-t', 'ccb-demo', 'window-active-style'] in calls


def test_apply_project_tmux_ui_uses_active_tool_pane_border_style(monkeypatch, tmp_path: Path) -> None:
    config_dir = tmp_path / 'config'
    config_dir.mkdir(parents=True)
    for script_name in ('ccb-status.sh', 'ccb-border.sh', 'ccb-git.sh'):
        (config_dir / script_name).write_text('#!/bin/sh\n', encoding='utf-8')
    (tmp_path / 'VERSION').write_text('9.9.9\n', encoding='utf-8')

    calls: list[list[str]] = []

    class FakeBackend:
        def _tmux_run(self, args, *, check=False, capture=False):
            del check
            calls.append(list(args))
            if capture and args[:4] == ['list-panes', '-t', 'ccb-demo', '-F']:
                return SimpleNamespace(returncode=0, stdout='\n%5\n', stderr='')
            if capture and args[:3] == ['list-panes', '-a', '-F']:
                return SimpleNamespace(
                    returncode=0,
                    stdout='ccb-demo\trich\t%5\t1\ttool\tfg=#54bda7\tfg=#73daca,bold\n',
                    stderr='',
                )
            if capture and args[:4] == ['display-message', '-p', '-t', '%5']:
                if args[4] == '#{@ccb_active_border_style}':
                    return SimpleNamespace(returncode=0, stdout='fg=#73daca,bold\n', stderr='')
                return SimpleNamespace(returncode=0, stdout='', stderr='')
            if capture and args[:4] == ['list-windows', '-t', 'ccb-demo', '-F']:
                return SimpleNamespace(returncode=0, stdout='rich\n', stderr='')
            return SimpleNamespace(returncode=0, stdout='', stderr='')

    monkeypatch.setattr(tmux_helpers, 'current_install_root', lambda: tmp_path)

    tmux_ui.apply_project_tmux_ui(
        tmux_socket_path='/tmp/ccb.sock',
        tmux_session_name='ccb-demo',
        backend=FakeBackend(),
    )

    assert ['set-window-option', '-t', 'ccb-demo:rich', 'pane-border-style', 'fg=#54bda7'] in calls
    assert ['set-window-option', '-t', 'ccb-demo:rich', 'pane-active-border-style', 'fg=#73daca,bold'] in calls
    assert ['set-window-option', '-t', 'ccb-demo:rich', 'pane-border-lines', 'heavy'] in calls
    assert ['set-option', '-p', '-t', '%5', 'pane-active-border-style', 'fg=#73daca,bold'] in calls


@pytest.mark.skipif(_BASH is None, reason='bash is required to execute tmux helper scripts')
def test_border_script_keeps_sidebar_active_border_gray(tmp_path: Path) -> None:
    assert _BASH is not None
    fake_bin = tmp_path / 'bin'
    fake_bin.mkdir()
    log_path = tmp_path / 'tmux.log'
    fake_tmux = fake_bin / 'tmux'
    fake_tmux.write_text(
        f"""#!/usr/bin/env bash
set -euo pipefail
printf '%s\\n' "$*" >> {log_path}
if [[ "$1 $2 $3 $4" == "display-message -p -t %0" ]]; then
  case "$5" in
    "#{{@ccb_active_border_style}}") printf '%s\\n' 'fg=#6c7086' ;;
    "#{{@ccb_border_style}}") printf '%s\\n' 'fg=#6c7086' ;;
    "#{{@ccb_role}}") printf '%s\\n' 'sidebar' ;;
    "#{{session_name}}:#{{window_name}}") printf '%s\\n' 'ccb-demo:main' ;;
    *) printf '\\n' ;;
  esac
fi
""",
        encoding='utf-8',
    )
    fake_tmux.chmod(0o755)

    proc = subprocess.run(
        [_BASH, str(Path('config/ccb-border.sh').resolve()), '%0'],
        env={**os.environ, 'PATH': f'{fake_bin}:{os.environ.get("PATH", "")}'},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    calls = log_path.read_text(encoding='utf-8')
    assert 'list-panes' not in calls
    assert 'set-option -p -t %0 pane-active-border-style fg=#6c7086' in calls


@pytest.mark.skipif(_BASH is None, reason='bash is required to execute tmux helper scripts')
def test_tmux_on_script_prefers_stable_install_config_for_border_hook(tmp_path: Path) -> None:
    assert _BASH is not None
    release_root = tmp_path / 'ccb-v7.3.4-release.fake'
    release_config = release_root / 'config'
    release_config.mkdir(parents=True)
    on_script = release_config / 'ccb-tmux-on.sh'
    on_script.write_text(Path('config/ccb-tmux-on.sh').read_text(encoding='utf-8'), encoding='utf-8')
    on_script.chmod(0o755)
    for script_name in ('ccb-status.sh', 'ccb-border.sh', 'ccb-git.sh'):
        script = release_config / script_name
        script.write_text('#!/usr/bin/env bash\nexit 0\n', encoding='utf-8')
        script.chmod(0o755)

    install_root = tmp_path / 'installed'
    install_config = install_root / 'config'
    install_config.mkdir(parents=True)
    installed_border = install_config / 'ccb-border.sh'
    for script_name in ('ccb-status.sh', 'ccb-border.sh', 'ccb-git.sh'):
        script = install_config / script_name
        script.write_text('#!/usr/bin/env bash\nexit 0\n', encoding='utf-8')
        script.chmod(0o755)
    installed_ccb = install_root / 'ccb'
    installed_ccb.write_text('#!/usr/bin/env bash\necho v9.9.9\n', encoding='utf-8')
    installed_ccb.chmod(0o755)

    fake_bin = tmp_path / 'bin'
    fake_bin.mkdir()
    log_path = tmp_path / 'tmux.log'
    fake_tmux = fake_bin / 'tmux'
    fake_tmux.write_text(
        f"""#!/usr/bin/env bash
set -euo pipefail
printf '%s\\n' "$*" >> {log_path}
if [[ "$1" == "display-message" && "$2" == "-p" ]]; then
  case "${{@: -1}}" in
    "#{{session_name}}") printf '%s\\n' 'ccb-demo' ;;
    "#{{pane_id}}") printf '%s\\n' '%1' ;;
    *) printf '\\n' ;;
  esac
fi
exit 0
""",
        encoding='utf-8',
    )
    fake_tmux.chmod(0o755)

    proc = subprocess.run(
        [_BASH, str(on_script)],
        env={
            **os.environ,
            'PATH': f'{fake_bin}:{os.environ.get("PATH", "")}',
            'TMUX': '/tmp/tmux-1/default,123,0',
            'CODEX_INSTALL_PREFIX': str(install_root),
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    calls = log_path.read_text(encoding='utf-8')
    assert str(installed_border) in calls
    assert str(release_config / 'ccb-border.sh') not in calls
    assert 'after-select-pane run-shell -b' in calls
    assert '[ -x ' in calls
    assert 'set-option -t ccb-demo status on' in calls
    assert 'set-option -t ccb-demo status-format CCB_CLEAR' in calls
    assert 'set-option -t ccb-demo status-format[0]' in calls
    assert 'set-option -u -t ccb-demo status-format[1]' not in calls
    assert 'set-window-option -u -t ccb-demo window-style' in calls
    assert 'set-window-option -u -t ccb-demo window-active-style' in calls
    assert 'Copy: MouseDrag' not in calls


def test_detect_ccb_version_prefers_current_install_over_path(monkeypatch, tmp_path: Path) -> None:
    current_root = tmp_path / 'current'
    current_root.mkdir()
    (current_root / 'VERSION').write_text('9.9.9\n', encoding='utf-8')

    path_root = tmp_path / 'path-root'
    path_root.mkdir()
    path_ccb = path_root / 'ccb'
    path_ccb.write_text('VERSION = "1.2.3"\n', encoding='utf-8')

    monkeypatch.delenv('CCB_VERSION', raising=False)
    monkeypatch.setattr(tmux_helpers, 'current_install_root', lambda: current_root)
    monkeypatch.setattr(tmux_helpers.shutil, 'which', lambda name: str(path_ccb) if name == 'ccb' else None)

    assert tmux_helpers.detect_ccb_version() == '9.9.9'
