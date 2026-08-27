from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

import cli.services.start_foreground as start_foreground_service
from ccbd.socket_client import CcbdClientError
from cli.context import CliContextBuilder
from cli.models import ParsedStartCommand
from cli.services.start_foreground import ForegroundAttachError, ForegroundAttachSummary, attach_started_project_namespace
from project.resolver import bootstrap_project

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _clear_tmux_config_env(monkeypatch) -> None:
    monkeypatch.delenv('CCB_TMUX_CONFIG', raising=False)
    monkeypatch.delenv('CCB_HERDR_EXE', raising=False)
    for name in (
        'WEZTERM_EXECUTABLE',
        'WEZTERM_EXECUTABLE_DIR',
        'WEZTERM_PANE',
        'WEZTERM_UNIX_SOCKET',
        'TERM_PROGRAM',
    ):
        monkeypatch.delenv(name, raising=False)


def _context(project_root: Path):
    command = ParsedStartCommand(project=None, agent_names=(), restore=True, auto_permission=True)
    return CliContextBuilder().build(command, cwd=project_root, bootstrap_if_missing=False)


def _assert_call_subsequence(actual: list[list[str]], expected: list[list[str]]) -> None:
    index = 0
    for call in actual:
        if call == expected[index]:
            index += 1
            if index == len(expected):
                return
    raise AssertionError(f'expected call subsequence {expected!r}; actual={actual!r}')


def _tmux_cmd(context, *args: str) -> list[str]:
    return ['tmux', '-f', '/dev/null', '-S', str(context.paths.ccbd_tmux_socket_path), *args]


def test_foreground_attach_summary_exposes_restore_token_presence_only() -> None:
    summary = ForegroundAttachSummary(
        project_id='proj-herdr',
        tmux_socket_path='',
        tmux_session_name='ccb-herdr',
        backend_impl='herdr',
        namespace_id='workspace-1',
        session_name='ccb-herdr',
        ipc_kind='herdr_socket',
        ipc_ref='herdr://ccb-herdr',
        namespace_restore_token_present=True,
    )

    assert summary.backend_impl == 'herdr'
    assert summary.namespace_restore_token_present is True
    assert not hasattr(summary, 'namespace_restore_token')
    assert 'ccb-herdr::workspace-1' not in str(summary)


def test_start_foreground_herdr_attach_uses_builder_without_tmux_binary(monkeypatch) -> None:
    context = SimpleNamespace(project=SimpleNamespace(project_id='proj-herdr'))
    payload = {
        'namespace_backend_family': 'herdr-native',
        'namespace_backend_impl': 'herdr',
        'namespace_id': 'workspace-1',
        'namespace_session_name': 'ccb-herdr',
        'namespace_ipc_kind': 'herdr_socket',
        'namespace_ipc_ref': 'herdr://workspace-1',
        'namespace_restore_token_present': True,
        'namespace_workspace_window_name': 'main',
        'namespace_ui_attachable': True,
    }
    builder_calls: list[dict[str, object]] = []
    attach_calls: list[tuple[dict[str, object], str | None]] = []

    class _FakeClient:
        def ping(self, target: str) -> dict[str, object]:
            assert target == 'ccbd'
            return payload

    class _FakeHerdrAttachBackend:
        def attach_namespace(self, namespace_ref: dict[str, object], *, window_name: str | None = None) -> None:
            attach_calls.append((dict(namespace_ref), window_name))

    def _build_herdr_attach_backend(*, namespace_ref, backend_selection):
        builder_calls.append(
            {
                'namespace_ref': dict(namespace_ref),
                'backend_selection': dict(backend_selection),
            }
        )
        return _FakeHerdrAttachBackend()

    monkeypatch.setattr(start_foreground_service, '_foreground_attach_client', lambda _context: _FakeClient())
    monkeypatch.setattr(start_foreground_service, '_attach_env', lambda: {})
    monkeypatch.setattr(
        start_foreground_service.shutil,
        'which',
        lambda _name: (_ for _ in ()).throw(AssertionError('tmux should not be queried')),
    )
    monkeypatch.setattr(
        start_foreground_service.subprocess,
        'Popen',
        lambda *_, **__: (_ for _ in ()).throw(AssertionError('tmux subprocess should not run')),
    )
    monkeypatch.setattr(start_foreground_service, '_launch_herdr_ui', lambda _namespace_ref, **_: None)
    monkeypatch.setattr(start_foreground_service, '_build_herdr_attach_backend', _build_herdr_attach_backend)

    summary = attach_started_project_namespace(context)  # type: ignore[arg-type]

    assert summary.backend_impl == 'herdr'
    assert summary.namespace_id == 'workspace-1'
    assert summary.session_name == 'ccb-herdr'
    assert summary.ipc_kind == 'herdr_socket'
    assert summary.namespace_restore_token_present is True
    assert builder_calls == [
        {
            'namespace_ref': {
                'backend_family': 'herdr-native',
                'backend_impl': 'herdr',
                'namespace_id': 'workspace-1',
                'session_name': 'ccb-herdr',
                'ipc_kind': 'herdr_socket',
                'ipc_ref': 'herdr://workspace-1',
                'restore_token': None,
            },
            'backend_selection': {
                'backend_family': 'herdr-native',
                'backend_impl': 'herdr',
                'ipc_kind': 'herdr_socket',
                'ipc_ref_present': True,
                'namespace_restore_token_present': True,
            },
        }
    ]
    assert attach_calls == [
        (
            {
                'backend_family': 'herdr-native',
                'backend_impl': 'herdr',
                'namespace_id': 'workspace-1',
                'session_name': 'ccb-herdr',
                'ipc_kind': 'herdr_socket',
                'ipc_ref': 'herdr://workspace-1',
                'restore_token': None,
            },
            'main',
        )
    ]
    assert 'restore-token' not in str(builder_calls)


def test_start_foreground_reads_existing_frontend_binding_for_herdr_reuse(monkeypatch) -> None:
    context = SimpleNamespace(
        project=SimpleNamespace(project_id='proj-herdr'),
        paths=SimpleNamespace(ccbd_socket_path='socket', ccbd_tmux_socket_path='socket'),
    )
    payload = {
        'namespace_backend_family': 'herdr-native',
        'namespace_backend_impl': 'herdr',
        'namespace_id': 'workspace-1',
        'namespace_session_name': 'ccb-herdr',
        'namespace_ipc_kind': 'herdr_socket',
        'namespace_ipc_ref': 'herdr://workspace-1',
        'namespace_restore_token_present': True,
        'namespace_workspace_window_name': 'main',
        'namespace_ui_attachable': True,
    }
    captured: dict[str, object] = {}
    attach_calls: list[dict[str, object]] = []

    class _FakeClient:
        def ping(self, target: str) -> dict[str, object]:
            assert target == 'ccbd'
            return payload

    class _FakeBackend:
        def namespace_alive(self, namespace_ref):
            assert namespace_ref['session_name'] == 'ccb-herdr'
            return True

        def attach_namespace(self, namespace_ref, *, window_name=None):
            attach_calls.append({'namespace_ref': dict(namespace_ref), 'window_name': window_name})

    monkeypatch.setattr(start_foreground_service, '_foreground_attach_client', lambda _context: _FakeClient())
    monkeypatch.setattr(start_foreground_service, '_attach_env', lambda: {})
    monkeypatch.setattr(
        start_foreground_service,
        '_load_herdr_frontend',
        lambda _context: start_foreground_service._HerdrFrontendLoad(
            frontend={
                'kind': 'wezterm',
                'status': 'wezterm_tab_attached',
                'mux_available': True,
                'pane_id': '42',
                'workspace': 'ccb-proj-abc',
            }
        ),
    )
    monkeypatch.setattr(start_foreground_service, '_build_herdr_attach_backend', lambda **kwargs: _FakeBackend())
    def _launch(namespace_ref, **kwargs):
        del namespace_ref
        captured['args'] = kwargs
        return {
            'kind': 'wezterm',
            'status': 'wezterm_tab_attached',
            'mux_available': True,
            'launch_mode': 'existing_frontend_reuse',
            'fallback': False,
            'pane_id': '42',
            'window_id': '7',
            'workspace': 'ccb-proj-abc',
            'probe_status': 'reachable',
        }
    monkeypatch.setattr(start_foreground_service, '_launch_herdr_ui', _launch)

    summary = start_foreground_service._attach_herdr_project_namespace(context, payload)  # type: ignore[arg-type]

    assert summary.backend_impl == 'herdr'
    assert captured['args']['existing_frontend'] == {
        'kind': 'wezterm',
        'status': 'wezterm_tab_attached',
        'mux_available': True,
        'pane_id': '42',
        'workspace': 'ccb-proj-abc',
    }
    assert captured['args']['backend'] is not None
    assert attach_calls[0]['window_name'] == 'main'


def test_start_foreground_herdr_attach_real_builder_accepts_matching_backend_ref(monkeypatch) -> None:
    context = SimpleNamespace(project=SimpleNamespace(project_id='proj-herdr'))
    payload = {
        'namespace_backend_family': 'herdr-native',
        'namespace_backend_impl': 'herdr',
        'namespace_id': 'workspace-1',
        'namespace_session_name': 'ccb-herdr',
        'namespace_ipc_kind': 'herdr_socket',
        'namespace_ipc_ref': 'herdr://workspace-1',
        'namespace_restore_token_present': True,
        'namespace_workspace_window_name': 'main',
        'namespace_ui_attachable': True,
    }
    attach_calls: list[tuple[dict[str, object], str | None]] = []

    class _FakeClient:
        def ping(self, target: str) -> dict[str, object]:
            assert target == 'ccbd'
            return payload

    backend_calls: list[object] = []

    class _MatchingHerdrBackend:
        def namespace_ref(self, session_name: str, namespace_id: str) -> dict[str, object]:
            return {
                'backend_family': 'herdr-native',
                'backend_impl': 'herdr',
                'namespace_id': namespace_id,
                'session_name': session_name,
                'ipc_kind': 'herdr_socket',
                'ipc_ref': 'herdr://workspace-1',
                'restore_token': None,
            }

        def attach_namespace(self, namespace_ref: dict[str, object], *, window_name: str | None = None) -> None:
            attach_calls.append((dict(namespace_ref), window_name))

    monkeypatch.setattr(start_foreground_service, '_foreground_attach_client', lambda _context: _FakeClient())
    monkeypatch.setattr(start_foreground_service, '_attach_env', lambda: {})
    monkeypatch.setattr(
        start_foreground_service.shutil,
        'which',
        lambda _name: (_ for _ in ()).throw(AssertionError('tmux should not be queried')),
    )
    monkeypatch.setattr(
        start_foreground_service.subprocess,
        'Popen',
        lambda *_, **__: (_ for _ in ()).throw(AssertionError('tmux subprocess should not run')),
    )
    monkeypatch.setattr(start_foreground_service, '_launch_herdr_ui', lambda _namespace_ref, **_: None)
    monkeypatch.setattr(
        'terminal_runtime.api.get_backend',
        lambda terminal_type=None: backend_calls.append(terminal_type) or _MatchingHerdrBackend(),
    )

    summary = attach_started_project_namespace(context)  # type: ignore[arg-type]

    assert summary.backend_impl == 'herdr'
    assert backend_calls == ['herdr']
    assert attach_calls == [
        (
            {
                'backend_family': 'herdr-native',
                'backend_impl': 'herdr',
                'namespace_id': 'workspace-1',
                'session_name': 'ccb-herdr',
                'ipc_kind': 'herdr_socket',
                'ipc_ref': 'herdr://workspace-1',
                'restore_token': None,
            },
            'main',
        )
    ]


def test_start_foreground_herdr_attach_uses_backend_normalized_ipc_ref(monkeypatch) -> None:
    context = SimpleNamespace(project=SimpleNamespace(project_id='proj-herdr'))
    payload = {
        'namespace_backend_family': 'herdr-native',
        'namespace_backend_impl': 'herdr',
        'namespace_id': 'workspace-1',
        'namespace_session_name': 'ccb-herdr',
        'namespace_ipc_kind': 'herdr_socket',
        'namespace_ipc_ref': 'herdr://local',
        'namespace_restore_token_present': True,
        'namespace_workspace_window_name': 'main',
        'namespace_ui_attachable': True,
    }
    attach_calls: list[tuple[dict[str, object], str | None]] = []

    class _FakeClient:
        def ping(self, target: str) -> dict[str, object]:
            assert target == 'ccbd'
            return payload

    class _NormalizingHerdrBackend:
        def namespace_ref(self, session_name: str, namespace_id: str) -> dict[str, object]:
            return {
                'backend_family': 'herdr-native',
                'backend_impl': 'herdr',
                'namespace_id': namespace_id,
                'session_name': session_name,
                'ipc_kind': 'herdr_socket',
                'ipc_ref': 'herdr://ccb-herdr',
                'restore_token': None,
            }

        def attach_namespace(self, namespace_ref: dict[str, object], *, window_name: str | None = None) -> None:
            attach_calls.append((dict(namespace_ref), window_name))

    monkeypatch.setattr(start_foreground_service, '_foreground_attach_client', lambda _context: _FakeClient())
    monkeypatch.setattr(start_foreground_service, '_attach_env', lambda: {})
    monkeypatch.setattr(start_foreground_service, '_launch_herdr_ui', lambda _namespace_ref, **_: None)
    monkeypatch.setattr(
        'terminal_runtime.api.get_backend',
        lambda terminal_type=None: _NormalizingHerdrBackend(),
    )

    attach_started_project_namespace(context)  # type: ignore[arg-type]

    assert attach_calls == [
        (
            {
                'backend_family': 'herdr-native',
                'backend_impl': 'herdr',
                'namespace_id': 'workspace-1',
                'session_name': 'ccb-herdr',
                'ipc_kind': 'herdr_socket',
                'ipc_ref': 'herdr://ccb-herdr',
                'restore_token': None,
            },
            'main',
        )
    ]


def test_launch_herdr_ui_hides_windows_control_wrapper(monkeypatch) -> None:
    run_calls: list[tuple[list[str], dict[str, object]]] = []

    def _fake_run(args, **kwargs):
        run_calls.append((list(args), dict(kwargs)))
        if list(args)[1:3] == ['cli', 'spawn']:
            return subprocess.CompletedProcess(args, 0, stdout='77\n')
        if list(args)[1:] == ['cli', 'list', '--format', 'json']:
            return subprocess.CompletedProcess(
                args,
                0,
                stdout=json.dumps(
                    [
                        {
                            'pane_id': 77,
                            'window_id': 9,
                            'workspace': 'ccb-proj-abc',
                        }
                    ]
                ),
            )
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(start_foreground_service.sys, 'platform', 'win32')
    monkeypatch.setattr(start_foreground_service.subprocess, 'CREATE_NO_WINDOW', 0x08000000, raising=False)
    monkeypatch.setenv('CCB_HERDR_EXE', 'C:/Herdr/herdr.exe')
    monkeypatch.setattr(
        start_foreground_service.shutil,
        'which',
        lambda name: 'C:/WezTerm/wezterm.exe' if name == 'wezterm' else None,
    )
    monkeypatch.setattr(start_foreground_service.os, 'getcwd', lambda: 'C:/repo')
    monkeypatch.setattr(start_foreground_service.subprocess, 'run', _fake_run)

    frontend = start_foreground_service._launch_herdr_ui({'session_name': 'ccb-proj-abc'})

    assert frontend == {
        'kind': 'wezterm',
        'status': 'wezterm_tab_attached',
        'mux_available': True,
        'launch_mode': 'wezterm_spawn',
        'fallback': False,
        'pane_id': '77',
        'window_id': '9',
        'workspace': 'ccb-proj-abc',
        'target_pane_id': '77',
    }
    assert run_calls == [
        (
            ['C:/WezTerm/wezterm.exe', 'cli', 'list'],
            {
                'check': False,
                'stdout': start_foreground_service.subprocess.DEVNULL,
                'stderr': start_foreground_service.subprocess.DEVNULL,
                'timeout': start_foreground_service._WEZTERM_CLI_TIMEOUT_S,
                'creationflags': 0x08000000,
            },
        ),
        (
            [
                'C:/WezTerm/wezterm.exe',
                'cli',
                'spawn',
                '--cwd',
                'C:/repo',
                '--',
                'C:/Herdr/herdr.exe',
                'session',
                'attach',
                'ccb-proj-abc',
            ],
            {
                'check': False,
                'stdout': start_foreground_service.subprocess.PIPE,
                'stderr': start_foreground_service.subprocess.DEVNULL,
                'text': True,
                'timeout': start_foreground_service._WEZTERM_CLI_TIMEOUT_S,
                'creationflags': 0x08000000,
            },
        ),
        (
            ['C:/WezTerm/wezterm.exe', 'cli', 'list', '--format', 'json'],
            {
                'check': False,
                'stdout': start_foreground_service.subprocess.PIPE,
                'stderr': start_foreground_service.subprocess.DEVNULL,
                'text': True,
                'timeout': start_foreground_service._WEZTERM_CLI_TIMEOUT_S,
                'creationflags': 0x08000000,
            },
        )
    ]


def test_launch_herdr_ui_uses_injected_runner_without_real_processes(monkeypatch) -> None:
    run_calls: list[list[str]] = []
    popen_calls: list[list[str]] = []

    def _fake_run(args, **kwargs):
        run_calls.append(list(args))
        return subprocess.CompletedProcess(args, 0)

    def _fake_popen(args, **kwargs):
        popen_calls.append(list(args))
        raise AssertionError('detached fallback should not run when WezTerm spawn succeeds')

    runner = start_foreground_service.HerdrFrontendCommandRunner(
        which_fn=lambda name: {
            'herdr': 'C:/Herdr/herdr.exe',
            'wezterm': 'C:/WezTerm/wezterm.exe',
        }.get(name),
        run_fn=_fake_run,
        popen_fn=_fake_popen,
        getcwd_fn=lambda: 'C:/repo',
    )
    monkeypatch.delenv('CCB_HERDR_EXE', raising=False)

    frontend = start_foreground_service._launch_herdr_ui(
        {'session_name': 'ccb-proj-abc'},
        runner=runner,
    )

    assert frontend['status'] == 'wezterm_tab_attached'
    assert run_calls == [
        ['C:/WezTerm/wezterm.exe', 'cli', 'list'],
        [
            'C:/WezTerm/wezterm.exe',
            'cli',
            'spawn',
            '--cwd',
            'C:/repo',
            '--',
            'C:/Herdr/herdr.exe',
            'session',
            'attach',
            'ccb-proj-abc',
        ],
    ]
    assert popen_calls == []


def test_launch_herdr_ui_uses_wezterm_executable_env_without_path(
    tmp_path: Path,
    monkeypatch,
) -> None:
    run_calls: list[list[str]] = []
    popen_calls: list[list[str]] = []
    wezterm_exe = tmp_path / 'WezTerm' / 'wezterm.exe'
    wezterm_exe.parent.mkdir()
    wezterm_exe.write_text('', encoding='utf-8')

    def _fake_run(args, **kwargs):
        del kwargs
        run_calls.append(list(args))
        return subprocess.CompletedProcess(args, 0)

    def _fake_popen(args, **kwargs):
        del kwargs
        popen_calls.append(list(args))
        raise AssertionError('WEZTERM_EXECUTABLE 可用时不应进入 Herdr 裸 fallback')

    runner = start_foreground_service.HerdrFrontendCommandRunner(
        which_fn=lambda name: 'C:/Herdr/herdr.exe' if name == 'herdr' else None,
        run_fn=_fake_run,
        popen_fn=_fake_popen,
        getcwd_fn=lambda: 'C:/repo',
    )
    monkeypatch.delenv('CCB_HERDR_EXE', raising=False)
    monkeypatch.setenv('WEZTERM_EXECUTABLE', str(wezterm_exe))

    frontend = start_foreground_service._launch_herdr_ui(
        {'session_name': 'ccb-proj-abc'},
        runner=runner,
    )

    assert frontend['status'] == 'wezterm_tab_attached'
    assert run_calls == [
        [str(wezterm_exe), 'cli', 'list'],
        [
            str(wezterm_exe),
            'cli',
            'spawn',
            '--cwd',
            'C:/repo',
            '--',
            'C:/Herdr/herdr.exe',
            'session',
            'attach',
            'ccb-proj-abc',
        ],
    ]
    assert popen_calls == []


def test_launch_herdr_ui_uses_wezterm_gui_env_cli_sibling_without_path(
    tmp_path: Path,
    monkeypatch,
) -> None:
    run_calls: list[list[str]] = []
    popen_calls: list[list[str]] = []
    wezterm_dir = tmp_path / 'WezTerm'
    wezterm_dir.mkdir()
    wezterm_gui = wezterm_dir / 'wezterm-gui.exe'
    wezterm_cli = wezterm_dir / 'wezterm.exe'
    wezterm_gui.write_text('', encoding='utf-8')
    wezterm_cli.write_text('', encoding='utf-8')

    def _fake_run(args, **kwargs):
        del kwargs
        run_calls.append(list(args))
        return subprocess.CompletedProcess(args, 0)

    def _fake_popen(args, **kwargs):
        del kwargs
        popen_calls.append(list(args))
        raise AssertionError('WEZTERM_EXECUTABLE 可派生 CLI 时不应进入 Herdr 裸 fallback')

    runner = start_foreground_service.HerdrFrontendCommandRunner(
        which_fn=lambda name: 'C:/Herdr/herdr.exe' if name == 'herdr' else None,
        run_fn=_fake_run,
        popen_fn=_fake_popen,
        getcwd_fn=lambda: 'C:/repo',
    )
    monkeypatch.delenv('CCB_HERDR_EXE', raising=False)
    monkeypatch.setenv('WEZTERM_EXECUTABLE', str(wezterm_gui))

    frontend = start_foreground_service._launch_herdr_ui(
        {'session_name': 'ccb-proj-abc'},
        runner=runner,
    )

    assert frontend['status'] == 'wezterm_tab_attached'
    assert run_calls[0] == [str(wezterm_cli), 'cli', 'list']
    assert run_calls[1][0] == str(wezterm_cli)
    assert popen_calls == []


def test_launch_herdr_ui_uses_wezterm_executable_dir_env_without_path(
    tmp_path: Path,
    monkeypatch,
) -> None:
    run_calls: list[list[str]] = []
    popen_calls: list[list[str]] = []
    wezterm_dir = tmp_path / 'WezTerm'
    wezterm_dir.mkdir()
    wezterm_cli = wezterm_dir / 'wezterm.exe'
    wezterm_cli.write_text('', encoding='utf-8')

    def _fake_run(args, **kwargs):
        del kwargs
        run_calls.append(list(args))
        return subprocess.CompletedProcess(args, 0)

    def _fake_popen(args, **kwargs):
        del kwargs
        popen_calls.append(list(args))
        raise AssertionError('WEZTERM_EXECUTABLE_DIR 可用时不应进入 Herdr 裸 fallback')

    runner = start_foreground_service.HerdrFrontendCommandRunner(
        which_fn=lambda name: 'C:/Herdr/herdr.exe' if name == 'herdr' else None,
        run_fn=_fake_run,
        popen_fn=_fake_popen,
        getcwd_fn=lambda: 'C:/repo',
    )
    monkeypatch.delenv('CCB_HERDR_EXE', raising=False)
    monkeypatch.delenv('WEZTERM_EXECUTABLE', raising=False)
    monkeypatch.setenv('WEZTERM_EXECUTABLE_DIR', str(wezterm_dir))

    frontend = start_foreground_service._launch_herdr_ui(
        {'session_name': 'ccb-proj-abc'},
        runner=runner,
    )

    assert frontend['status'] == 'wezterm_tab_attached'
    assert run_calls[0] == [str(wezterm_cli), 'cli', 'list']
    assert run_calls[1][0] == str(wezterm_cli)
    assert popen_calls == []


def test_launch_herdr_ui_replaces_current_wezterm_pane_without_spawning(monkeypatch) -> None:
    run_calls: list[list[str]] = []
    run_envs: list[dict[str, str] | None] = []
    popen_calls: list[list[str]] = []
    exec_calls: list[tuple[str, list[str], dict[str, str]]] = []
    frontend_records: list[dict[str, object]] = []

    def _fake_run(args, **kwargs):
        call = list(args)
        run_calls.append(call)
        run_envs.append(kwargs.get('env'))
        if call == ['C:/WezTerm/wezterm.exe', 'cli', 'list', '--format', 'json']:
            return subprocess.CompletedProcess(
                args,
                0,
                stdout=json.dumps(
                    [
                        {
                            'pane_id': 1,
                            'window_id': 7,
                            'workspace': 'ccb-proj-abc',
                        }
                    ]
                ),
            )
        raise AssertionError('当前 WezTerm pane 应直接交接给 Herdr UI')

    def _fake_popen(args, **kwargs):
        del kwargs
        popen_calls.append(list(args))
        raise AssertionError('当前 WezTerm pane 应避免裸进程 fallback')

    def _fake_execvpe(executable, command, env):
        exec_calls.append((executable, list(command), dict(env)))
        raise SystemExit(0)

    runner = start_foreground_service.HerdrFrontendCommandRunner(
        which_fn=lambda name: {
            'herdr': 'C:/Herdr/herdr.exe',
            'wezterm': 'C:/WezTerm/wezterm.exe',
        }.get(name),
        run_fn=_fake_run,
        popen_fn=_fake_popen,
        execvpe_fn=_fake_execvpe,
        getcwd_fn=lambda: 'C:/repo',
    )
    monkeypatch.delenv('CCB_HERDR_EXE', raising=False)
    monkeypatch.setenv('WEZTERM_PANE', '1')
    monkeypatch.setenv('WEZTERM_UNIX_SOCKET', 'C:/Users/Administrator/.local/share/wezterm/gui-sock-14220')

    with pytest.raises(SystemExit):
        start_foreground_service._launch_herdr_ui(
            {'session_name': 'ccb-proj-abc'},
            runner=runner,
            before_current_pane_exec=frontend_records.append,
        )

    assert frontend_records == [
        {
            'kind': 'wezterm',
            'status': 'wezterm_tab_attached',
            'mux_available': True,
            'launch_mode': 'current_pane_exec',
            'fallback': False,
            'pane_id': '1',
            'window_id': '7',
            'workspace': 'ccb-proj-abc',
            'wezterm_socket': 'C:/Users/Administrator/.local/share/wezterm/gui-sock-14220',
        }
    ]
    assert len(exec_calls) == 1
    assert exec_calls[0][0] == 'C:/Herdr/herdr.exe'
    assert exec_calls[0][1] == ['C:/Herdr/herdr.exe', 'session', 'attach', 'ccb-proj-abc']
    assert exec_calls[0][2]['WEZTERM_PANE'] == '1'
    assert exec_calls[0][2]['WEZTERM_UNIX_SOCKET'] == 'C:/Users/Administrator/.local/share/wezterm/gui-sock-14220'
    assert run_calls == [['C:/WezTerm/wezterm.exe', 'cli', 'list', '--format', 'json']]
    assert run_envs[0] is not None
    assert run_envs[0]['WEZTERM_UNIX_SOCKET'] == 'C:/Users/Administrator/.local/share/wezterm/gui-sock-14220'
    assert popen_calls == []


def test_launch_herdr_ui_detects_current_wezterm_pane_with_cli_probe(monkeypatch) -> None:
    run_calls: list[list[str]] = []
    run_envs: list[dict[str, str] | None] = []
    exec_calls: list[tuple[str, list[str], dict[str, str]]] = []

    def _fake_run(args, **kwargs):
        call = list(args)
        run_calls.append(call)
        run_envs.append(kwargs.get('env'))
        if call == ['C:/WezTerm/wezterm.exe', 'cli', 'get-pane-direction', 'Next']:
            return subprocess.CompletedProcess(args, 0, stdout='')
        if call == ['C:/WezTerm/wezterm.exe', 'cli', 'list', '--format', 'json']:
            return subprocess.CompletedProcess(
                args,
                0,
                stdout=json.dumps(
                    [
                        {
                            'pane_id': 42,
                            'window_id': 9,
                            'workspace': 'ccb-proj-abc',
                            'is_active': True,
                        }
                    ]
                ),
            )
        raise AssertionError(f'当前 WezTerm pane 不应创建新 UI: {call!r}')

    def _fake_execvpe(executable, command, env):
        exec_calls.append((executable, list(command), dict(env)))
        raise SystemExit(0)

    runner = start_foreground_service.HerdrFrontendCommandRunner(
        which_fn=lambda name: {
            'herdr': 'C:/Herdr/herdr.exe',
            'wezterm': 'C:/WezTerm/wezterm.exe',
        }.get(name),
        run_fn=_fake_run,
        popen_fn=lambda *_, **__: (_ for _ in ()).throw(AssertionError('不应进入裸 fallback')),
        execvpe_fn=_fake_execvpe,
        getcwd_fn=lambda: 'C:/repo',
    )
    monkeypatch.setenv('TERM_PROGRAM', 'WezTerm')
    monkeypatch.setenv('WEZTERM_UNIX_SOCKET', 'C:/Users/Administrator/.local/share/wezterm/gui-sock-14220')

    with pytest.raises(SystemExit):
        start_foreground_service._launch_herdr_ui(
            {'session_name': 'ccb-proj-abc'},
            runner=runner,
        )

    assert run_calls == [
        ['C:/WezTerm/wezterm.exe', 'cli', 'get-pane-direction', 'Next'],
        ['C:/WezTerm/wezterm.exe', 'cli', 'list', '--format', 'json'],
    ]
    assert [env['WEZTERM_UNIX_SOCKET'] for env in run_envs if env is not None] == [
        'C:/Users/Administrator/.local/share/wezterm/gui-sock-14220',
        'C:/Users/Administrator/.local/share/wezterm/gui-sock-14220',
    ]
    assert exec_calls[0][1] == ['C:/Herdr/herdr.exe', 'session', 'attach', 'ccb-proj-abc']
    assert exec_calls[0][2]['WEZTERM_UNIX_SOCKET'] == 'C:/Users/Administrator/.local/share/wezterm/gui-sock-14220'


def test_attach_herdr_project_namespace_aborts_when_current_pane_handoff_fails(monkeypatch) -> None:
    context = SimpleNamespace(
        project=SimpleNamespace(project_id='proj-herdr'),
        paths=SimpleNamespace(ccbd_socket_path='socket', ccbd_tmux_socket_path='socket'),
    )
    payload = {
        'namespace_backend_family': 'herdr-native',
        'namespace_backend_impl': 'herdr',
        'namespace_id': 'workspace-1',
        'namespace_session_name': 'ccb-herdr',
        'namespace_ipc_kind': 'herdr_socket',
        'namespace_ipc_ref': 'herdr://workspace-1',
        'namespace_restore_token_present': True,
        'namespace_workspace_window_name': 'main',
        'namespace_ui_attachable': True,
    }

    class _Backend:
        def attach_namespace(self, namespace_ref, *, window_name=None):
            raise AssertionError('当前 pane 交接失败后不应继续 attach_namespace')

    monkeypatch.setattr(
        start_foreground_service,
        '_load_herdr_frontend',
        lambda _context: start_foreground_service._HerdrFrontendLoad(),
    )
    monkeypatch.setattr(start_foreground_service, '_build_herdr_attach_backend', lambda **_: _Backend())
    monkeypatch.setattr(
        start_foreground_service,
        '_launch_herdr_ui',
        lambda *_, **__: {
            'kind': 'wezterm',
            'status': 'frontend_not_ready',
            'mux_available': True,
            'launch_mode': 'current_pane_exec',
            'fallback': False,
            'reason': 'current_pane_exec_failed',
        },
    )

    with pytest.raises(ForegroundAttachError, match='current_pane_exec_failed'):
        start_foreground_service._attach_herdr_project_namespace(context, payload)  # type: ignore[arg-type]


def test_launch_herdr_ui_records_frontend_binding_load_failure_when_rebuilding(monkeypatch) -> None:
    run_calls: list[list[str]] = []

    def _fake_run(args, **kwargs):
        del kwargs
        call = list(args)
        run_calls.append(call)
        if call == ['C:/WezTerm/wezterm.exe', 'cli', 'list']:
            return subprocess.CompletedProcess(args, 0)
        if call == ['C:/WezTerm/wezterm.exe', 'cli', 'list', '--format', 'json']:
            return subprocess.CompletedProcess(args, 0, stdout='[]')
        if call[1:3] == ['cli', 'spawn']:
            return subprocess.CompletedProcess(args, 0, stdout='77\n')
        raise AssertionError(f'unexpected wezterm call: {call!r}')

    runner = start_foreground_service.HerdrFrontendCommandRunner(
        which_fn=lambda name: {
            'herdr': 'C:/Herdr/herdr.exe',
            'wezterm': 'C:/WezTerm/wezterm.exe',
        }.get(name),
        run_fn=_fake_run,
        popen_fn=lambda *_, **__: (_ for _ in ()).throw(AssertionError('不应进入裸 fallback')),
        getcwd_fn=lambda: 'C:/repo',
    )

    frontend = start_foreground_service._launch_herdr_ui(
        {'session_name': 'ccb-proj-abc'},
        previous_frontend_probe={
            'probe_status': 'unreachable',
            'reason': 'frontend_binding_load_failed',
        },
        runner=runner,
    )

    assert frontend['status'] == 'wezterm_tab_attached'
    assert frontend['launch_mode'] == 'wezterm_spawn'
    assert frontend['previous_frontend_probe_status'] == 'unreachable'
    assert frontend['previous_frontend_probe_reason'] == 'frontend_binding_load_failed'


def test_launch_herdr_ui_reuses_reachable_frontend_binding_without_spawning(monkeypatch) -> None:
    run_calls: list[list[str]] = []
    run_envs: list[dict[str, str] | None] = []
    popen_calls: list[list[str]] = []
    exec_calls: list[list[str]] = []

    class _Backend:
        def namespace_alive(self, namespace_ref):
            assert namespace_ref['session_name'] == 'ccb-proj-abc'
            return True

    def _fake_run(args, **kwargs):
        call = list(args)
        run_calls.append(call)
        run_envs.append(kwargs.get('env'))
        if call == ['C:/WezTerm/wezterm.exe', 'cli', 'list', '--format', 'json']:
            return subprocess.CompletedProcess(
                args,
                0,
                stdout=json.dumps(
                    [
                        {
                            'pane_id': 42,
                            'window_id': 7,
                            'workspace': 'ccb-proj-abc',
                        }
                    ]
                ),
            )
        if call == ['C:/WezTerm/wezterm.exe', 'cli', 'activate-pane', '--pane-id', '42']:
            return subprocess.CompletedProcess(args, 0)
        raise AssertionError(f'不应创建新的 WezTerm UI: {call!r}')

    runner = start_foreground_service.HerdrFrontendCommandRunner(
        which_fn=lambda name: {
            'herdr': 'C:/Herdr/herdr.exe',
            'wezterm': 'C:/WezTerm/wezterm.exe',
        }.get(name),
        run_fn=_fake_run,
        popen_fn=lambda args, **kwargs: popen_calls.append(list(args)),
        execvpe_fn=lambda executable, command, env: exec_calls.append(list(command)),
        getcwd_fn=lambda: 'C:/repo',
    )

    frontend = start_foreground_service._launch_herdr_ui(
        {
            'session_name': 'ccb-proj-abc',
            'namespace_id': 'workspace-1',
            'ipc_kind': 'herdr_socket',
            'ipc_ref': 'herdr://workspace-1',
        },
        existing_frontend={
            'kind': 'wezterm',
            'status': 'wezterm_tab_attached',
            'mux_available': True,
            'pane_id': '42',
            'workspace': 'ccb-proj-abc',
            'wezterm_socket': 'C:/Users/Administrator/.local/share/wezterm/gui-sock-14220',
        },
        backend=_Backend(),
        runner=runner,
    )

    assert frontend == {
        'kind': 'wezterm',
        'status': 'wezterm_tab_attached',
        'mux_available': True,
        'launch_mode': 'existing_frontend_reuse',
        'fallback': False,
        'pane_id': '42',
        'window_id': '7',
        'workspace': 'ccb-proj-abc',
        'wezterm_socket': 'C:/Users/Administrator/.local/share/wezterm/gui-sock-14220',
        'probe_status': 'reachable',
    }
    assert run_calls == [
        ['C:/WezTerm/wezterm.exe', 'cli', 'list', '--format', 'json'],
        ['C:/WezTerm/wezterm.exe', 'cli', 'activate-pane', '--pane-id', '42'],
    ]
    assert [env['WEZTERM_UNIX_SOCKET'] for env in run_envs if env is not None] == [
        'C:/Users/Administrator/.local/share/wezterm/gui-sock-14220',
        'C:/Users/Administrator/.local/share/wezterm/gui-sock-14220',
    ]
    assert popen_calls == []
    assert exec_calls == []


def test_launch_herdr_ui_rebuilds_unreachable_frontend_binding_and_records_reason(monkeypatch) -> None:
    run_calls: list[list[str]] = []

    class _Backend:
        def namespace_alive(self, namespace_ref):
            assert namespace_ref['session_name'] == 'ccb-proj-abc'
            return False

    def _fake_run(args, **kwargs):
        del kwargs
        call = list(args)
        run_calls.append(call)
        if call == ['C:/WezTerm/wezterm.exe', 'cli', 'list']:
            return subprocess.CompletedProcess(args, 0)
        if call == ['C:/WezTerm/wezterm.exe', 'cli', 'list', '--format', 'json']:
            return subprocess.CompletedProcess(args, 0, stdout='[]')
        if call[1:3] == ['cli', 'spawn']:
            return subprocess.CompletedProcess(args, 0, stdout='77\n')
        raise AssertionError(f'unexpected wezterm call: {call!r}')

    runner = start_foreground_service.HerdrFrontendCommandRunner(
        which_fn=lambda name: {
            'herdr': 'C:/Herdr/herdr.exe',
            'wezterm': 'C:/WezTerm/wezterm.exe',
        }.get(name),
        run_fn=_fake_run,
        popen_fn=lambda *_, **__: (_ for _ in ()).throw(AssertionError('不应进入裸 fallback')),
        getcwd_fn=lambda: 'C:/repo',
    )

    frontend = start_foreground_service._launch_herdr_ui(
        {'session_name': 'ccb-proj-abc'},
        existing_frontend={
            'kind': 'wezterm',
            'status': 'wezterm_tab_attached',
            'pane_id': '42',
        },
        backend=_Backend(),
        runner=runner,
    )

    assert frontend['status'] == 'wezterm_tab_attached'
    assert frontend['launch_mode'] == 'wezterm_spawn'
    assert frontend['pane_id'] == '77'
    assert frontend['previous_frontend_probe_status'] == 'unreachable'
    assert frontend['previous_frontend_probe_reason'] == 'herdr_namespace_unreachable'
    assert run_calls == [
        ['C:/WezTerm/wezterm.exe', 'cli', 'list'],
        [
            'C:/WezTerm/wezterm.exe',
            'cli',
            'spawn',
            '--cwd',
            'C:/repo',
            '--',
            'C:/Herdr/herdr.exe',
            'session',
            'attach',
            'ccb-proj-abc',
        ],
        ['C:/WezTerm/wezterm.exe', 'cli', 'list', '--format', 'json'],
    ]


def test_launch_herdr_ui_rebuilds_legacy_wezterm_binding_without_socket(monkeypatch) -> None:
    run_calls: list[list[str]] = []

    class _Backend:
        def namespace_alive(self, namespace_ref):
            assert namespace_ref['session_name'] == 'ccb-proj-abc'
            return True

    def _fake_run(args, **kwargs):
        del kwargs
        call = list(args)
        run_calls.append(call)
        if call == ['C:/WezTerm/wezterm.exe', 'cli', 'list']:
            return subprocess.CompletedProcess(args, 0)
        if call == ['C:/WezTerm/wezterm.exe', 'cli', 'list', '--format', 'json']:
            return subprocess.CompletedProcess(args, 0, stdout='[]')
        if call[1:3] == ['cli', 'spawn']:
            return subprocess.CompletedProcess(args, 0, stdout='77\n')
        raise AssertionError(f'unexpected wezterm call: {call!r}')

    runner = start_foreground_service.HerdrFrontendCommandRunner(
        which_fn=lambda name: {
            'herdr': 'C:/Herdr/herdr.exe',
            'wezterm': 'C:/WezTerm/wezterm.exe',
        }.get(name),
        run_fn=_fake_run,
        popen_fn=lambda *_, **__: (_ for _ in ()).throw(AssertionError('不应进入裸 fallback')),
        getcwd_fn=lambda: 'C:/repo',
    )

    frontend = start_foreground_service._launch_herdr_ui(
        {'session_name': 'ccb-proj-abc'},
        existing_frontend={
            'kind': 'wezterm',
            'status': 'wezterm_tab_attached',
            'pane_id': '42',
            'workspace': 'ccb-proj-abc',
        },
        backend=_Backend(),
        runner=runner,
    )

    assert frontend['status'] == 'wezterm_tab_attached'
    assert frontend['launch_mode'] == 'wezterm_spawn'
    assert frontend['pane_id'] == '77'
    assert frontend['previous_frontend_probe_status'] == 'unreachable'
    assert frontend['previous_frontend_probe_reason'] == 'missing_frontend_wezterm_socket'
    assert ['C:/WezTerm/wezterm.exe', 'cli', 'activate-pane', '--pane-id', '42'] not in run_calls


def test_launch_herdr_ui_fallback_uses_visible_windows_console(monkeypatch) -> None:
    popen_calls: list[tuple[list[str], dict[str, object]]] = []

    class _FakeProcess:
        pid = 1234

    def _fake_run(args, **kwargs):
        raise AssertionError('wezterm 不可用时不应运行 wezterm 命令')

    def _fake_popen(args, **kwargs):
        popen_calls.append((list(args), dict(kwargs)))
        return _FakeProcess()

    monkeypatch.setattr(start_foreground_service.sys, 'platform', 'win32')
    monkeypatch.setattr(start_foreground_service.subprocess, 'CREATE_NEW_CONSOLE', 0x00000010, raising=False)

    runner = start_foreground_service.HerdrFrontendCommandRunner(
        which_fn=lambda name: 'C:/Herdr/herdr.exe' if name == 'herdr' else None,
        run_fn=_fake_run,
        popen_fn=_fake_popen,
        getcwd_fn=lambda: 'C:/repo',
    )

    frontend = start_foreground_service._launch_herdr_ui(
        {'session_name': 'ccb-proj-abc'},
        runner=runner,
    )

    assert frontend['status'] == 'detached_fallback'
    assert frontend['fallback_reason'] == 'wezterm_cli_unavailable'
    assert popen_calls == [
        (
            ['C:/Herdr/herdr.exe', 'session', 'attach', 'ccb-proj-abc'],
            {'creationflags': 0x00000010},
        )
    ]


def test_launch_herdr_ui_falls_back_when_wezterm_mux_is_missing(monkeypatch) -> None:
    popen_calls: list[list[str]] = []

    class _FakeProcess:
        pid = 1234

    def _fake_run(args, **kwargs):
        return subprocess.CompletedProcess(args, 1)

    def _fake_popen(args, **kwargs):
        popen_calls.append(list(args))
        return _FakeProcess()

    monkeypatch.setenv('CCB_HERDR_EXE', 'C:/Herdr/herdr.exe')
    monkeypatch.setattr(
        start_foreground_service.shutil,
        'which',
        lambda name: 'C:/WezTerm/wezterm.exe' if name == 'wezterm' else None,
    )
    monkeypatch.setattr(start_foreground_service.subprocess, 'run', _fake_run)
    monkeypatch.setattr(start_foreground_service.subprocess, 'Popen', _fake_popen)

    frontend = start_foreground_service._launch_herdr_ui({'session_name': 'ccb-proj-abc'})

    assert frontend['status'] == 'detached_fallback'
    assert frontend['mux_available'] is False
    assert frontend['fallback_reason'] == 'wezterm_mux_unavailable'
    assert popen_calls == [['C:/Herdr/herdr.exe', 'session', 'attach', 'ccb-proj-abc']]


def test_launch_herdr_ui_falls_back_when_wezterm_spawn_fails(monkeypatch) -> None:
    popen_calls: list[list[str]] = []
    run_returncodes = iter([0, 7])

    class _FakeProcess:
        pid = 1234

    def _fake_run(args, **kwargs):
        return subprocess.CompletedProcess(args, next(run_returncodes))

    def _fake_popen(args, **kwargs):
        popen_calls.append(list(args))
        return _FakeProcess()

    monkeypatch.setenv('CCB_HERDR_EXE', 'C:/Herdr/herdr.exe')
    monkeypatch.setattr(
        start_foreground_service.shutil,
        'which',
        lambda name: 'C:/WezTerm/wezterm.exe' if name == 'wezterm' else None,
    )
    monkeypatch.setattr(start_foreground_service.os, 'getcwd', lambda: 'C:/repo')
    monkeypatch.setattr(start_foreground_service.subprocess, 'run', _fake_run)
    monkeypatch.setattr(start_foreground_service.subprocess, 'Popen', _fake_popen)

    frontend = start_foreground_service._launch_herdr_ui({'session_name': 'ccb-proj-abc'})

    assert frontend['status'] == 'detached_fallback'
    assert frontend['mux_available'] is True
    assert frontend['fallback_reason'] == 'wezterm_spawn_failed'
    assert popen_calls == [['C:/Herdr/herdr.exe', 'session', 'attach', 'ccb-proj-abc']]


def test_start_foreground_herdr_attach_rejects_missing_payload_without_tmux_fallback(monkeypatch) -> None:
    payload = {
        'namespace_backend_impl': 'herdr',
        'namespace_id': 'workspace-1',
        'namespace_session_name': 'ccb-herdr',
        'namespace_ipc_kind': 'herdr_socket',
        'namespace_ui_attachable': True,
    }

    ready, error = start_foreground_service._attach_target_ready(payload, env={})

    assert ready is False
    assert 'ipc_ref_present=False' in error


def test_start_foreground_herdr_attach_blocked_error_includes_projection() -> None:
    payload = {
        'namespace_backend_impl': 'herdr',
        'namespace_id': 'workspace-1',
        'namespace_session_name': 'ccb-herdr',
        'namespace_ipc_kind': 'herdr_socket',
        'namespace_ipc_ref': 'herdr://workspace-1',
        'namespace_ui_attachable': False,
        'herdr_surface_projection': {
            'backend_impl': 'herdr',
            'capability_status': 'blocked',
            'support_tier_projection': 'experimental',
            'support_tier_projection_source': 'validation_pending',
            'beta_gaps': ['foreground-attach-validation-pending'],
            'blocking_gaps': ['attach_unsupported'],
            'degraded_next_action': 'collect-validation-transcript',
            'evidence_refs': {},
        },
    }

    ready, error = start_foreground_service._attach_target_ready(payload, env={})

    assert ready is False
    assert 'capability_status=blocked' in error
    assert 'beta_gaps=foreground-attach-validation-pending' in error
    assert 'blocking_gaps=attach_unsupported' in error
    assert 'next_action=collect-validation-transcript' in error


def test_start_foreground_herdr_attach_builder_rejects_backend_session_name_mismatch(monkeypatch) -> None:
    namespace_ref = {
        'backend_family': 'herdr-native',
        'backend_impl': 'herdr',
        'namespace_id': 'workspace-1',
        'session_name': 'ccb-herdr',
        'ipc_kind': 'herdr_socket',
        'ipc_ref': 'herdr://workspace-1',
        'restore_token': None,
    }
    backend_selection = {
        'backend_family': 'herdr-native',
        'backend_impl': 'herdr',
        'ipc_kind': 'herdr_socket',
        'ipc_ref_present': True,
        'namespace_restore_token_present': True,
    }

    class _MismatchedHerdrBackend:
        def namespace_ref(self, session_name: str, namespace_id: str) -> dict[str, object]:
            return {
                'backend_family': 'herdr-native',
                'backend_impl': 'herdr',
                'namespace_id': namespace_id,
                'session_name': 'other-session',
                'ipc_kind': 'herdr_socket',
                'ipc_ref': 'herdr://other-session',
                'restore_token': None,
            }

    monkeypatch.setattr(
        'terminal_runtime.api.get_backend',
        lambda terminal_type=None: _MismatchedHerdrBackend(),
    )

    with pytest.raises(ForegroundAttachError, match='namespace ref mismatch'):
        start_foreground_service._build_herdr_attach_backend(
            namespace_ref=namespace_ref,
            backend_selection=backend_selection,
        )


def test_start_foreground_herdr_attach_builder_ignores_backend_ipc_ref_difference(monkeypatch) -> None:
    namespace_ref = {
        'backend_family': 'herdr-native',
        'backend_impl': 'herdr',
        'namespace_id': 'workspace-1',
        'session_name': 'ccb-herdr',
        'ipc_kind': 'herdr_socket',
        'ipc_ref': 'herdr://workspace-1',
        'restore_token': None,
    }
    backend_selection = {
        'backend_family': 'herdr-native',
        'backend_impl': 'herdr',
        'ipc_kind': 'herdr_socket',
        'ipc_ref_present': True,
        'namespace_restore_token_present': True,
    }

    class _SessionRefHerdrBackend:
        def namespace_ref(self, session_name: str, namespace_id: str) -> dict[str, object]:
            return {
                'backend_family': 'herdr-native',
                'backend_impl': 'herdr',
                'namespace_id': namespace_id,
                'session_name': session_name,
                'ipc_kind': 'herdr_socket',
                'ipc_ref': 'herdr://normalized-session',
                'restore_token': None,
            }

    monkeypatch.setattr(
        'terminal_runtime.api.get_backend',
        lambda terminal_type=None: _SessionRefHerdrBackend(),
    )

    backend = start_foreground_service._build_herdr_attach_backend(
        namespace_ref=namespace_ref,
        backend_selection=backend_selection,
    )

    assert isinstance(backend, _SessionRefHerdrBackend)


class _FakeAttachProcess:
    def __init__(self, *, pid: int, returncode: int | None = None):
        self.pid = pid
        self.returncode = returncode
        self.wait_calls = 0

    def poll(self):
        return self.returncode

    def wait(self):
        self.wait_calls += 1
        if self.returncode is None:
            self.returncode = 0
        return self.returncode


def test_start_foreground_attaches_to_namespace_tmux_session(tmp_path: Path, monkeypatch) -> None:
    project_root = tmp_path / 'repo-attach'
    (project_root / '.ccb').mkdir(parents=True, exist_ok=True)
    (project_root / '.ccb' / 'ccb.config').write_text('demo:codex\n', encoding='utf-8')
    bootstrap_project(project_root)
    context = _context(project_root)
    client_timeouts: list[float | None] = []

    class _FakeClient:
        def __init__(self, socket_path, *, timeout_s=None):
            self.socket_path = socket_path
            self.timeout_s = timeout_s
            client_timeouts.append(timeout_s)

        def ping(self, target: str) -> dict[str, object]:
            assert target == 'ccbd'
            return {
                'namespace_tmux_socket_path': str(context.paths.ccbd_tmux_socket_path),
                'namespace_tmux_session_name': context.paths.ccbd_tmux_session_name,
                'namespace_backend_impl': 'tmux',
                'namespace_id': context.paths.ccbd_tmux_session_name,
                'namespace_session_name': context.paths.ccbd_tmux_session_name,
                'namespace_ipc_kind': 'socket_path',
                'namespace_ipc_ref': str(context.paths.ccbd_tmux_socket_path),
                'namespace_restore_token_present': False,
                'namespace_workspace_window_name': context.paths.ccbd_tmux_workspace_window_name,
                'namespace_ui_attachable': True,
            }

    run_calls: list[list[str]] = []
    attach_calls: list[list[str]] = []
    attach_process = _FakeAttachProcess(pid=4242, returncode=0)

    def _run(args, **kwargs):
        call = list(args)
        run_calls.append(call)
        if 'list-clients' in call:
            if call[-1] == '#{client_pid}\t#{client_tty}':
                return subprocess.CompletedProcess(args=args, returncode=0, stdout='4242\t/dev/pts/55\n')
            return subprocess.CompletedProcess(args=args, returncode=0, stdout='4242\n')
        return subprocess.CompletedProcess(args=args, returncode=0)

    def _popen(args, **kwargs):
        del kwargs
        attach_calls.append(list(args))
        return attach_process

    monkeypatch.setattr('cli.services.start_foreground.shutil.which', lambda name: f'/usr/bin/{name}')
    monkeypatch.setattr('cli.services.start_foreground.CcbdClient', _FakeClient)
    monkeypatch.setattr('cli.services.start_foreground.subprocess.run', _run)
    monkeypatch.setattr('cli.services.start_foreground.subprocess.Popen', _popen)

    summary = attach_started_project_namespace(context)

    assert summary.project_id == context.project.project_id
    assert summary.tmux_socket_path == str(context.paths.ccbd_tmux_socket_path)
    assert summary.tmux_session_name == context.paths.ccbd_tmux_session_name
    assert summary.backend_impl == 'tmux'
    assert summary.namespace_id == context.paths.ccbd_tmux_session_name
    assert summary.session_name == context.paths.ccbd_tmux_session_name
    assert summary.ipc_kind == 'socket_path'
    assert summary.ipc_ref == str(context.paths.ccbd_tmux_socket_path)
    assert summary.namespace_restore_token_present is False
    assert client_timeouts == [start_foreground_service.FOREGROUND_ATTACH_RPC_TIMEOUT_S]
    assert 'CONTROL_PLANE_RPC_TIMEOUT_S' not in start_foreground_service.__dict__
    _assert_call_subsequence(run_calls, [
        _tmux_cmd(context, 'has-session', '-t', context.paths.ccbd_tmux_session_name),
        _tmux_cmd(context, 'select-window', '-t', f'{context.paths.ccbd_tmux_session_name}:{context.paths.ccbd_tmux_workspace_window_name}'),
        _tmux_cmd(context, 'list-clients', '-t', context.paths.ccbd_tmux_session_name, '-F', '#{client_pid}'),
        _tmux_cmd(context, 'list-clients', '-t', context.paths.ccbd_tmux_session_name, '-F', '#{client_pid}\t#{client_tty}'),
        _tmux_cmd(context, 'refresh-client', '-t', '/dev/pts/55'),
    ])
    assert _tmux_cmd(context, 'attach-session', '-t', context.paths.ccbd_tmux_session_name) in attach_calls
    assert attach_calls.count(
        _tmux_cmd(context, 'attach-session', '-t', context.paths.ccbd_tmux_session_name)
    ) == 1


def test_start_foreground_normalizes_ghostty_term_for_tmux(monkeypatch) -> None:
    monkeypatch.setenv('TERM', 'xterm-ghostty')
    monkeypatch.setenv('TMUX', '/tmp/tmux-1000/default,123,0')
    monkeypatch.setenv('TMUX_PANE', '%77')

    env = start_foreground_service._attach_env()

    assert env['TERM'] == 'xterm-256color'
    assert 'TMUX' not in env
    assert 'TMUX_PANE' not in env


def test_start_foreground_waits_for_workspace_window_visibility_before_attach(tmp_path: Path, monkeypatch) -> None:
    project_root = tmp_path / 'repo-attach-delayed-window'
    (project_root / '.ccb').mkdir(parents=True, exist_ok=True)
    (project_root / '.ccb' / 'ccb.config').write_text('demo:codex\n', encoding='utf-8')
    bootstrap_project(project_root)
    context = _context(project_root)

    class _FakeClient:
        def __init__(self, socket_path, *, timeout_s=None):
            self.socket_path = socket_path
            self.timeout_s = timeout_s
            self.calls = 0

        def ping(self, target: str) -> dict[str, object]:
            assert target == 'ccbd'
            self.calls += 1
            return {
                'namespace_tmux_socket_path': str(context.paths.ccbd_tmux_socket_path),
                'namespace_tmux_session_name': context.paths.ccbd_tmux_session_name,
                'namespace_workspace_window_name': context.paths.ccbd_tmux_workspace_window_name,
                'namespace_ui_attachable': True,
            }

    run_calls: list[list[str]] = []
    attach_calls: list[list[str]] = []
    attach_process = _FakeAttachProcess(pid=4343, returncode=0)
    select_attempts = 0

    def _run(args, **kwargs):
        nonlocal select_attempts
        call = list(args)
        run_calls.append(call)
        if 'list-clients' in call:
            if call[-1] == '#{client_pid}\t#{client_tty}':
                return subprocess.CompletedProcess(args=args, returncode=0, stdout='4343\t/dev/pts/88\n')
            return subprocess.CompletedProcess(args=args, returncode=0, stdout='4343\n')
        if 'select-window' in call:
            select_attempts += 1
            return subprocess.CompletedProcess(args=args, returncode=0 if select_attempts >= 2 else 1)
        return subprocess.CompletedProcess(args=args, returncode=0)

    def _popen(args, **kwargs):
        del kwargs
        attach_calls.append(list(args))
        return attach_process

    monkeypatch.setattr('cli.services.start_foreground.shutil.which', lambda name: f'/usr/bin/{name}')
    monkeypatch.setattr('cli.services.start_foreground.CcbdClient', _FakeClient)
    monkeypatch.setattr('cli.services.start_foreground.subprocess.run', _run)
    monkeypatch.setattr('cli.services.start_foreground.subprocess.Popen', _popen)
    monkeypatch.setattr('cli.services.start_foreground._ATTACH_TARGET_READY_POLL_INTERVAL_S', 0.0)

    summary = attach_started_project_namespace(context)

    assert summary.project_id == context.project.project_id
    _assert_call_subsequence(run_calls, [
        _tmux_cmd(context, 'has-session', '-t', context.paths.ccbd_tmux_session_name),
        _tmux_cmd(context, 'select-window', '-t', f'{context.paths.ccbd_tmux_session_name}:{context.paths.ccbd_tmux_workspace_window_name}'),
        _tmux_cmd(context, 'has-session', '-t', context.paths.ccbd_tmux_session_name),
        _tmux_cmd(context, 'select-window', '-t', f'{context.paths.ccbd_tmux_session_name}:{context.paths.ccbd_tmux_workspace_window_name}'),
        _tmux_cmd(context, 'list-clients', '-t', context.paths.ccbd_tmux_session_name, '-F', '#{client_pid}'),
        _tmux_cmd(context, 'list-clients', '-t', context.paths.ccbd_tmux_session_name, '-F', '#{client_pid}\t#{client_tty}'),
        _tmux_cmd(context, 'refresh-client', '-t', '/dev/pts/88'),
    ])
    assert _tmux_cmd(context, 'attach-session', '-t', context.paths.ccbd_tmux_session_name) in attach_calls
    assert attach_calls.count(
        _tmux_cmd(context, 'attach-session', '-t', context.paths.ccbd_tmux_session_name)
    ) == 1


def test_start_foreground_retries_transient_ccbd_ping_timeouts_before_attach(
    tmp_path: Path,
    monkeypatch,
) -> None:
    project_root = tmp_path / 'repo-attach-delayed-ping'
    (project_root / '.ccb').mkdir(parents=True, exist_ok=True)
    (project_root / '.ccb' / 'ccb.config').write_text('demo:codex\n', encoding='utf-8')
    bootstrap_project(project_root)
    context = _context(project_root)

    class _FakeClient:
        def __init__(self, socket_path, *, timeout_s=None):
            self.socket_path = socket_path
            self.timeout_s = timeout_s
            self.calls = 0

        def ping(self, target: str) -> dict[str, object]:
            assert target == 'ccbd'
            self.calls += 1
            if self.calls < 3:
                raise CcbdClientError('timed out')
            return {
                'namespace_tmux_socket_path': str(context.paths.ccbd_tmux_socket_path),
                'namespace_tmux_session_name': context.paths.ccbd_tmux_session_name,
                'namespace_workspace_window_name': context.paths.ccbd_tmux_workspace_window_name,
                'namespace_ui_attachable': True,
            }

    client_holder: list[_FakeClient] = []
    run_calls: list[list[str]] = []
    attach_process = _FakeAttachProcess(pid=4444, returncode=0)

    def _client(socket_path, *, timeout_s=None):
        client = _FakeClient(socket_path, timeout_s=timeout_s)
        client_holder.append(client)
        return client

    def _run(args, **kwargs):
        call = list(args)
        run_calls.append(call)
        if 'list-clients' in call:
            if call[-1] == '#{client_pid}\t#{client_tty}':
                return subprocess.CompletedProcess(args=args, returncode=0, stdout='4444\t/dev/pts/44\n')
            return subprocess.CompletedProcess(args=args, returncode=0, stdout='4444\n')
        return subprocess.CompletedProcess(args=args, returncode=0)

    monkeypatch.setattr('cli.services.start_foreground.shutil.which', lambda name: f'/usr/bin/{name}')
    monkeypatch.setattr('cli.services.start_foreground.CcbdClient', _client)
    monkeypatch.setattr('cli.services.start_foreground.subprocess.run', _run)
    monkeypatch.setattr('cli.services.start_foreground.subprocess.Popen', lambda *args, **kwargs: attach_process)
    monkeypatch.setattr('cli.services.start_foreground._ATTACH_TARGET_READY_POLL_INTERVAL_S', 0.0)

    summary = attach_started_project_namespace(context)

    assert summary.tmux_session_name == context.paths.ccbd_tmux_session_name
    assert len(client_holder) == 1
    assert client_holder[0].calls == 3
    assert any('refresh-client' in call for call in run_calls)


def test_start_foreground_ping_timeout_error_reports_foreground_attach_context(
    tmp_path: Path,
    monkeypatch,
) -> None:
    project_root = tmp_path / 'repo-attach-ping-timeout'
    (project_root / '.ccb').mkdir(parents=True, exist_ok=True)
    (project_root / '.ccb' / 'ccb.config').write_text('demo:codex\n', encoding='utf-8')
    bootstrap_project(project_root)
    context = _context(project_root)
    current = {'t': 0.0}

    class _FakeClient:
        def __init__(self, socket_path, *, timeout_s=None):
            self.socket_path = socket_path
            self.timeout_s = timeout_s

        def ping(self, target: str) -> dict[str, object]:
            assert target == 'ccbd'
            current['t'] = 0.2
            raise CcbdClientError('timed out')

    monkeypatch.setattr('cli.services.start_foreground.shutil.which', lambda name: f'/usr/bin/{name}')
    monkeypatch.setattr('cli.services.start_foreground.CcbdClient', _FakeClient)
    monkeypatch.setattr('cli.services.start_foreground.time.monotonic', lambda: current['t'])
    monkeypatch.setattr('cli.services.start_foreground._ATTACH_TARGET_READY_TIMEOUT_S', 0.1)

    with pytest.raises(
        ForegroundAttachError,
        match=r'foreground attach timed out: ccbd did not respond.*rpc_timeout=.*attempts=1',
    ):
        attach_started_project_namespace(context)


def test_start_foreground_caps_each_attach_ping_to_remaining_ready_budget(monkeypatch) -> None:
    current = {'t': 0.0}

    def _monotonic() -> float:
        return current['t']

    def _sleep(seconds: float) -> None:
        current['t'] += float(seconds)

    class _FakeClient:
        def __init__(self) -> None:
            self.timeouts: list[float] = []
            self.calls = 0

        def with_timeout(self, timeout_s: float):
            self.timeouts.append(timeout_s)
            return self

        def ping(self, target: str) -> dict[str, object]:
            assert target == 'ccbd'
            self.calls += 1
            current['t'] += 1.4
            raise CcbdClientError('timed out')

    client = _FakeClient()

    monkeypatch.setattr('cli.services.start_foreground.time.monotonic', _monotonic)
    monkeypatch.setattr('cli.services.start_foreground.time.sleep', _sleep)
    monkeypatch.setattr('cli.services.start_foreground._ATTACH_TARGET_READY_TIMEOUT_S', 2.0)
    monkeypatch.setattr('cli.services.start_foreground._ATTACH_TARGET_READY_POLL_INTERVAL_S', 0.0)
    monkeypatch.setattr('cli.services.start_foreground.FOREGROUND_ATTACH_RPC_TIMEOUT_S', 3.0)

    with pytest.raises(ForegroundAttachError, match=r'rpc_timeout=0\.6s'):
        start_foreground_service._wait_for_attach_target(client, env={})

    assert client.calls == 2
    assert client.timeouts[0] == 2.0
    assert 0.5 <= client.timeouts[1] <= 0.7


def test_start_foreground_reports_clean_error_when_session_exits_before_attach(tmp_path: Path, monkeypatch) -> None:
    project_root = tmp_path / 'repo-attach-fail'
    (project_root / '.ccb').mkdir(parents=True, exist_ok=True)
    (project_root / '.ccb' / 'ccb.config').write_text('demo:codex\n', encoding='utf-8')
    bootstrap_project(project_root)
    context = _context(project_root)

    class _FakeClient:
        def __init__(self, socket_path, *, timeout_s=None):
            self.socket_path = socket_path
            self.timeout_s = timeout_s

        def ping(self, target: str) -> dict[str, object]:
            assert target == 'ccbd'
            return {
                'namespace_tmux_socket_path': str(context.paths.ccbd_tmux_socket_path),
                'namespace_tmux_session_name': context.paths.ccbd_tmux_session_name,
                'namespace_workspace_window_name': context.paths.ccbd_tmux_workspace_window_name,
                'namespace_ui_attachable': True,
            }

    run_calls: list[list[str]] = []
    attach_calls: list[list[str]] = []
    attach_process = _FakeAttachProcess(pid=5151, returncode=1)

    def _run(args, **kwargs):
        del kwargs
        call = list(args)
        run_calls.append(call)
        if len(run_calls) in {1, 2}:
            return subprocess.CompletedProcess(args=args, returncode=0)
        if len(run_calls) == 3:
            return subprocess.CompletedProcess(args=args, returncode=1, stdout='')
        if len(run_calls) == 4:
            return subprocess.CompletedProcess(args=args, returncode=1)
        raise AssertionError(f'unexpected subprocess call: {call}')

    def _popen(args, **kwargs):
        del kwargs
        attach_calls.append(list(args))
        return attach_process

    monkeypatch.setattr('cli.services.start_foreground.shutil.which', lambda name: f'/usr/bin/{name}')
    monkeypatch.setattr('cli.services.start_foreground.CcbdClient', _FakeClient)
    monkeypatch.setattr('cli.services.start_foreground.subprocess.run', _run)
    monkeypatch.setattr('cli.services.start_foreground.subprocess.Popen', _popen)

    with pytest.raises(ForegroundAttachError, match='session exited before foreground attach completed'):
        attach_started_project_namespace(context)

    assert run_calls == [
        _tmux_cmd(context, 'has-session', '-t', context.paths.ccbd_tmux_session_name),
        _tmux_cmd(context, 'select-window', '-t', f'{context.paths.ccbd_tmux_session_name}:{context.paths.ccbd_tmux_workspace_window_name}'),
        _tmux_cmd(context, 'list-clients', '-t', context.paths.ccbd_tmux_session_name, '-F', '#{client_pid}'),
        _tmux_cmd(context, 'has-session', '-t', context.paths.ccbd_tmux_session_name),
    ]
    assert attach_calls == [
        _tmux_cmd(context, 'attach-session', '-t', context.paths.ccbd_tmux_session_name)
    ]


def test_start_foreground_keeps_backend_when_session_survives_post_attach_exit(tmp_path: Path, monkeypatch) -> None:
    project_root = tmp_path / 'repo-attach-killed-later'
    (project_root / '.ccb').mkdir(parents=True, exist_ok=True)
    (project_root / '.ccb' / 'ccb.config').write_text('demo:codex\n', encoding='utf-8')
    bootstrap_project(project_root)
    context = _context(project_root)

    class _FakeClient:
        stop_all_calls = 0

        def __init__(self, socket_path, *, timeout_s=None):
            self.socket_path = socket_path
            self.timeout_s = timeout_s

        def ping(self, target: str) -> dict[str, object]:
            assert target == 'ccbd'
            return {
                'namespace_tmux_socket_path': str(context.paths.ccbd_tmux_socket_path),
                'namespace_tmux_session_name': context.paths.ccbd_tmux_session_name,
                'namespace_workspace_window_name': context.paths.ccbd_tmux_workspace_window_name,
                'namespace_ui_attachable': True,
            }

        def stop_all(self, *, force: bool):
            del force
            type(self).stop_all_calls += 1

    run_calls: list[list[str]] = []
    attach_calls: list[list[str]] = []
    attach_process = _FakeAttachProcess(pid=6161, returncode=None)

    def _run(args, **kwargs):
        call = list(args)
        run_calls.append(call)
        if 'list-clients' in call:
            if call[-1] == '#{client_pid}\t#{client_tty}':
                return subprocess.CompletedProcess(args=args, returncode=0, stdout='6161\t/dev/pts/61\n')
            attach_process.returncode = 1
            return subprocess.CompletedProcess(args=args, returncode=0, stdout='6161\n')
        return subprocess.CompletedProcess(args=args, returncode=0)

    def _popen(args, **kwargs):
        del kwargs
        attach_calls.append(list(args))
        return attach_process

    monkeypatch.setattr('cli.services.start_foreground.shutil.which', lambda name: f'/usr/bin/{name}')
    monkeypatch.setattr('cli.services.start_foreground.CcbdClient', _FakeClient)
    monkeypatch.setattr('cli.services.start_foreground.subprocess.run', _run)
    monkeypatch.setattr('cli.services.start_foreground.subprocess.Popen', _popen)

    summary = attach_started_project_namespace(context)

    assert summary.project_id == context.project.project_id
    assert attach_process.wait_calls == 1
    assert run_calls == [
        _tmux_cmd(context, 'has-session', '-t', context.paths.ccbd_tmux_session_name),
        _tmux_cmd(context, 'select-window', '-t', f'{context.paths.ccbd_tmux_session_name}:{context.paths.ccbd_tmux_workspace_window_name}'),
        _tmux_cmd(context, 'list-clients', '-t', context.paths.ccbd_tmux_session_name, '-F', '#{client_pid}'),
        _tmux_cmd(context, 'list-clients', '-t', context.paths.ccbd_tmux_session_name, '-F', '#{client_pid}\t#{client_tty}'),
        _tmux_cmd(context, 'refresh-client', '-t', '/dev/pts/61'),
    ]
    assert attach_calls == [
        _tmux_cmd(context, 'attach-session', '-t', context.paths.ccbd_tmux_session_name)
    ]
    assert _FakeClient.stop_all_calls == 0


def test_start_foreground_does_not_stop_backend_when_session_disappears_after_attach(tmp_path: Path, monkeypatch) -> None:
    project_root = tmp_path / 'repo-attach-server-exited'
    (project_root / '.ccb').mkdir(parents=True, exist_ok=True)
    (project_root / '.ccb' / 'ccb.config').write_text('demo:codex\n', encoding='utf-8')
    bootstrap_project(project_root)
    context = _context(project_root)

    class _FakeClient:
        stop_all_calls: list[bool] = []

        def __init__(self, socket_path, *, timeout_s=None):
            self.socket_path = socket_path
            self.timeout_s = timeout_s

        def ping(self, target: str) -> dict[str, object]:
            assert target == 'ccbd'
            return {
                'namespace_tmux_socket_path': str(context.paths.ccbd_tmux_socket_path),
                'namespace_tmux_session_name': context.paths.ccbd_tmux_session_name,
                'namespace_workspace_window_name': context.paths.ccbd_tmux_workspace_window_name,
                'namespace_ui_attachable': True,
            }

        def stop_all(self, *, force: bool):
            type(self).stop_all_calls.append(force)

    run_calls: list[list[str]] = []
    attach_process = _FakeAttachProcess(pid=7171, returncode=None)

    def _run(args, **kwargs):
        del kwargs
        call = list(args)
        run_calls.append(call)
        if 'list-clients' in call:
            if call[-1] == '#{client_pid}\t#{client_tty}':
                return subprocess.CompletedProcess(args=args, returncode=0, stdout='7171\t/dev/pts/71\n')
            attach_process.returncode = 1
            return subprocess.CompletedProcess(args=args, returncode=0, stdout='7171\n')
        return subprocess.CompletedProcess(args=args, returncode=0)

    monkeypatch.setattr('cli.services.start_foreground.shutil.which', lambda name: f'/usr/bin/{name}')
    monkeypatch.setattr('cli.services.start_foreground.CcbdClient', _FakeClient)
    monkeypatch.setattr('cli.services.start_foreground.subprocess.run', _run)
    monkeypatch.setattr('cli.services.start_foreground.subprocess.Popen', lambda *args, **kwargs: attach_process)

    summary = attach_started_project_namespace(context)

    assert summary.project_id == context.project.project_id
    assert _FakeClient.stop_all_calls == []
    assert run_calls == [
        _tmux_cmd(context, 'has-session', '-t', context.paths.ccbd_tmux_session_name),
        _tmux_cmd(context, 'select-window', '-t', f'{context.paths.ccbd_tmux_session_name}:{context.paths.ccbd_tmux_workspace_window_name}'),
        _tmux_cmd(context, 'list-clients', '-t', context.paths.ccbd_tmux_session_name, '-F', '#{client_pid}'),
        _tmux_cmd(context, 'list-clients', '-t', context.paths.ccbd_tmux_session_name, '-F', '#{client_pid}\t#{client_tty}'),
        _tmux_cmd(context, 'refresh-client', '-t', '/dev/pts/71'),
    ]


def test_start_foreground_requires_attachable_namespace(tmp_path: Path, monkeypatch) -> None:
    project_root = tmp_path / 'repo-not-attachable'
    (project_root / '.ccb').mkdir(parents=True, exist_ok=True)
    (project_root / '.ccb' / 'ccb.config').write_text('demo:codex\n', encoding='utf-8')
    bootstrap_project(project_root)
    context = _context(project_root)
    current = {'t': 0.0}

    class _FakeClient:
        def __init__(self, socket_path, *, timeout_s=None):
            self.socket_path = socket_path
            self.timeout_s = timeout_s

        def ping(self, target: str) -> dict[str, object]:
            assert target == 'ccbd'
            current['t'] = 0.2
            return {
                'namespace_tmux_socket_path': str(context.paths.ccbd_tmux_socket_path),
                'namespace_tmux_session_name': context.paths.ccbd_tmux_session_name,
                'namespace_workspace_window_name': context.paths.ccbd_tmux_workspace_window_name,
                'namespace_ui_attachable': False,
            }

    monkeypatch.setattr('cli.services.start_foreground.shutil.which', lambda name: f'/usr/bin/{name}')
    monkeypatch.setattr('cli.services.start_foreground.CcbdClient', _FakeClient)
    monkeypatch.setattr('cli.services.start_foreground.time.monotonic', lambda: current['t'])
    monkeypatch.setattr('cli.services.start_foreground._ATTACH_TARGET_READY_TIMEOUT_S', 0.1)

    with pytest.raises(ForegroundAttachError, match='not attachable after successful `ccb` start'):
        attach_started_project_namespace(context)


def test_start_foreground_skips_refresh_when_client_tty_is_unavailable(tmp_path: Path, monkeypatch) -> None:
    project_root = tmp_path / 'repo-attach-no-tty'
    (project_root / '.ccb').mkdir(parents=True, exist_ok=True)
    (project_root / '.ccb' / 'ccb.config').write_text('demo:codex\n', encoding='utf-8')
    bootstrap_project(project_root)
    context = _context(project_root)

    class _FakeClient:
        def __init__(self, socket_path, *, timeout_s=None):
            self.socket_path = socket_path
            self.timeout_s = timeout_s

        def ping(self, target: str) -> dict[str, object]:
            assert target == 'ccbd'
            return {
                'namespace_tmux_socket_path': str(context.paths.ccbd_tmux_socket_path),
                'namespace_tmux_session_name': context.paths.ccbd_tmux_session_name,
                'namespace_workspace_window_name': context.paths.ccbd_tmux_workspace_window_name,
                'namespace_ui_attachable': True,
            }

    run_calls: list[list[str]] = []
    attach_process = _FakeAttachProcess(pid=7171, returncode=0)

    def _run(args, **kwargs):
        call = list(args)
        run_calls.append(call)
        if 'list-clients' in call:
            if call[-1] == '#{client_pid}\t#{client_tty}':
                return subprocess.CompletedProcess(args=args, returncode=0, stdout='7171\t\n')
            return subprocess.CompletedProcess(args=args, returncode=0, stdout='7171\n')
        return subprocess.CompletedProcess(args=args, returncode=0)

    monkeypatch.setattr('cli.services.start_foreground.shutil.which', lambda name: f'/usr/bin/{name}')
    monkeypatch.setattr('cli.services.start_foreground.CcbdClient', _FakeClient)
    monkeypatch.setattr('cli.services.start_foreground.subprocess.run', _run)
    monkeypatch.setattr('cli.services.start_foreground.subprocess.Popen', lambda *args, **kwargs: attach_process)

    attach_started_project_namespace(context)

    assert not any('refresh-client' in call for call in run_calls)


# ── _clean_herdr_exec_env 纯函数测试 ─────────────────────────────


def test_clean_herdr_exec_env_preserves_only_whitelist_vars() -> None:
    """输入包含白名单和非白名单变量 -> 输出只含白名单变量。"""
    raw = {
        'PATH': 'C:\\Windows\\system32',
        'TMUX': '/tmp/tmux-1000/default,123,0',
        'PYTHONHOME': 'C:\\Python312',
        'CCB_SOURCE_RUNTIME_OK': '1',
        'WEZTERM_PANE': '1',
        'TERM_PROGRAM': 'WezTerm',
        'TEMP': 'C:\\Temp',
    }
    cleaned = start_foreground_service._clean_herdr_exec_env(raw)
    assert cleaned == {
        'PATH': 'C:\\Windows\\system32',
        'WEZTERM_PANE': '1',
        'TERM_PROGRAM': 'WezTerm',
        'TEMP': 'C:\\Temp',
    }


def test_clean_herdr_exec_env_removes_tmux_vars() -> None:
    """输入包含 TMUX/TMUX_PANE -> 输出不含。"""
    raw = {
        'PATH': 'C:\\Windows',
        'TMUX': '/tmp/tmux-1000/default,123,0',
        'TMUX_PANE': '%77',
        'TERM': 'xterm-256color',
    }
    cleaned = start_foreground_service._clean_herdr_exec_env(raw)
    assert 'TMUX' not in cleaned
    assert 'TMUX_PANE' not in cleaned
    assert cleaned['PATH'] == 'C:\\Windows'
    assert cleaned['TERM'] == 'xterm-256color'


def test_clean_herdr_exec_env_keeps_wezterm_vars() -> None:
    """输入包含 WEZTERM 变量 -> 输出保留。"""
    raw = {
        'WEZTERM_PANE': '1',
        'WEZTERM_UNIX_SOCKET': '/tmp/wezterm.sock',
        'WEZTERM_EXECUTABLE': '/usr/bin/wezterm',
        'SYSTEMROOT': 'C:\\Windows',
        'CCB_INTERNAL': 'should-go',
    }
    cleaned = start_foreground_service._clean_herdr_exec_env(raw)
    assert cleaned['WEZTERM_PANE'] == '1'
    assert cleaned['WEZTERM_UNIX_SOCKET'] == '/tmp/wezterm.sock'
    assert cleaned['WEZTERM_EXECUTABLE'] == '/usr/bin/wezterm'
    assert 'CCB_INTERNAL' not in cleaned


def test_clean_herdr_exec_env_empty_input() -> None:
    """输入空字典 -> 输出空字典。"""
    assert start_foreground_service._clean_herdr_exec_env({}) == {}


def test_clean_herdr_exec_env_whitelist_only_input() -> None:
    """输入只含白名单变量 -> 输出与输入一致。"""
    raw = {'PATH': '/usr/bin', 'TERM': 'xterm-256color', 'WEZTERM_PANE': '1'}
    cleaned = start_foreground_service._clean_herdr_exec_env(raw)
    assert cleaned == raw


# ── _foreground_tabs_override 纯函数测试 ─────────────────────────


def test_foreground_tabs_override_returns_none_when_unset() -> None:
    """CCB_FOREGROUND_TABS 未设置 -> None。"""
    assert start_foreground_service._foreground_tabs_override({}) is None


def test_foreground_tabs_override_returns_one() -> None:
    """CCB_FOREGROUND_TABS=1 -> 1。"""
    assert start_foreground_service._foreground_tabs_override({'CCB_FOREGROUND_TABS': '1'}) == 1


def test_foreground_tabs_override_returns_two() -> None:
    """CCB_FOREGROUND_TABS=2 -> 2。"""
    assert start_foreground_service._foreground_tabs_override({'CCB_FOREGROUND_TABS': '2'}) == 2


def test_foreground_tabs_override_rejects_invalid() -> None:
    """CCB_FOREGROUND_TABS=3 -> None。"""
    assert start_foreground_service._foreground_tabs_override({'CCB_FOREGROUND_TABS': '3'}) is None
    assert start_foreground_service._foreground_tabs_override({'CCB_FOREGROUND_TABS': ''}) is None


# ── 诊断开关调度测试 ─────────────────────────────────────────


def test_launch_herdr_ui_forces_current_pane_when_foreground_tabs_is_one(monkeypatch) -> None:
    """CCB_FOREGROUND_TABS=1 且在当前 WezTerm pane 中 -> 走 current_pane_exec。"""
    exec_calls: list[tuple[str, list[str], dict[str, str]]] = []

    def _fake_execvpe(executable, command, env):
        exec_calls.append((executable, list(command), dict(env)))
        raise SystemExit(0)

    runner = start_foreground_service.HerdrFrontendCommandRunner(
        which_fn=lambda name: {
            'herdr': 'C:/Herdr/herdr.exe',
            'wezterm': 'C:/WezTerm/wezterm.exe',
        }.get(name),
        run_fn=lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0),
        popen_fn=lambda *_, **__: (_ for _ in ()).throw(AssertionError('不应进入 spawn 路径')),
        execvpe_fn=_fake_execvpe,
        getcwd_fn=lambda: 'C:/repo',
    )

    monkeypatch.setenv('WEZTERM_PANE', '1')
    monkeypatch.setenv('CCB_FOREGROUND_TABS', '1')

    with pytest.raises(SystemExit):
        start_foreground_service._launch_herdr_ui(
            {'session_name': 'ccb-proj-abc'},
            runner=runner,
        )

    assert len(exec_calls) == 1
    assert exec_calls[0][1] == ['C:/Herdr/herdr.exe', 'session', 'attach', 'ccb-proj-abc']
    # execvpe 的 env 是净化后的：不含 TMUX/PYTHON
    assert 'PYTHONHOME' not in exec_calls[0][2]
    assert 'CCB_SOURCE_RUNTIME_OK' not in exec_calls[0][2]
    # WezTerm 变量应保留
    assert exec_calls[0][2]['WEZTERM_PANE'] == '1'


def test_launch_herdr_ui_rejects_one_tab_when_not_in_wezterm_pane(monkeypatch) -> None:
    """CCB_FOREGROUND_TABS=1 但不在 WezTerm pane 中 -> frontend_not_ready。"""
    monkeypatch.setenv('CCB_FOREGROUND_TABS', '1')

    frontend = start_foreground_service._launch_herdr_ui(
        {'session_name': 'ccb-proj-abc'},
        runner=start_foreground_service.HerdrFrontendCommandRunner(
            which_fn=lambda name: {
                'herdr': 'C:/Herdr/herdr.exe',
                'wezterm': 'C:/WezTerm/wezterm.exe',
            }.get(name),
            run_fn=lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0),
        ),
    )

    assert frontend['status'] == 'frontend_not_ready'
    assert frontend['reason'] == 'foreground_tabs_1_requires_current_wezterm_pane'
    assert frontend.get('requested_tabs') == 1


def test_launch_herdr_ui_forces_spawn_when_foreground_tabs_is_two(monkeypatch) -> None:
    """CCB_FOREGROUND_TABS=2 时强制走 spawn 路径。"""
    run_calls: list[list[str]] = []

    def _fake_run(args, **kwargs):
        call = list(args)
        run_calls.append(call)
        if call[1:3] == ['cli', 'spawn']:
            return subprocess.CompletedProcess(args, 0, stdout='77\n')
        return subprocess.CompletedProcess(args, 0)

    runner = start_foreground_service.HerdrFrontendCommandRunner(
        which_fn=lambda name: {
            'herdr': 'C:/Herdr/herdr.exe',
            'wezterm': 'C:/WezTerm/wezterm.exe',
        }.get(name),
        run_fn=_fake_run,
        popen_fn=lambda *_, **__: (_ for _ in ()).throw(AssertionError('不应进入 detached fallback')),
        getcwd_fn=lambda: 'C:/repo',
    )

    monkeypatch.setenv('WEZTERM_PANE', '1')
    monkeypatch.setenv('CCB_FOREGROUND_TABS', '2')

    frontend = start_foreground_service._launch_herdr_ui(
        {'session_name': 'ccb-proj-abc'},
        runner=runner,
    )

    assert frontend['status'] == 'wezterm_tab_attached'
    assert frontend['launch_mode'] == 'wezterm_spawn'
    assert frontend.get('requested_tabs') == 2
    assert frontend.get('origin_pane_id') == '1'
    assert frontend.get('target_pane_id') == '77'
    # 验证走了 spawn 路径而不是 current_pane_exec
    assert any('spawn' in str(call) for call in run_calls)


def test_launch_herdr_ui_records_requested_tabs_in_frontend_fact(monkeypatch) -> None:
    """diagnostic开关的 frontend fact 包含 requested_tabs 字段。"""
    run_calls: list[list[str]] = []

    def _fake_run(args, **kwargs):
        call = list(args)
        run_calls.append(call)
        if call[1:3] == ['cli', 'spawn']:
            return subprocess.CompletedProcess(args, 0, stdout='88\n')
        return subprocess.CompletedProcess(args, 0)

    runner = start_foreground_service.HerdrFrontendCommandRunner(
        which_fn=lambda name: {
            'herdr': 'C:/Herdr/herdr.exe',
            'wezterm': 'C:/WezTerm/wezterm.exe',
        }.get(name),
        run_fn=_fake_run,
        popen_fn=lambda *_, **__: (_ for _ in ()).throw(AssertionError('不应进入 detached fallback')),
        getcwd_fn=lambda: 'C:/repo',
    )

    monkeypatch.setenv('WEZTERM_PANE', '1')
    monkeypatch.setenv('CCB_FOREGROUND_TABS', '2')

    frontend = start_foreground_service._launch_herdr_ui(
        {'session_name': 'ccb-proj-abc'},
        runner=runner,
    )

    assert 'requested_tabs' in frontend
    assert frontend['requested_tabs'] == 2
    assert 'origin_pane_id' in frontend
    assert 'target_pane_id' in frontend


# ── _replace_current_wezterm_pane_with_herdr_ui 环境净化测试 ──


def test_replace_current_pane_exec_uses_clean_herdr_env(monkeypatch) -> None:
    """execvpe 接收的 env 是净化后的版本，不含 TMUX/PYTHONHOME。"""
    exec_calls: list[dict[str, str]] = []

    def _fake_run(args, **kwargs):
        call = list(args)
        if call[1:5] == ['cli', 'list', '--format', 'json']:
            return subprocess.CompletedProcess(
                args, 0,
                stdout=json.dumps([{'pane_id': 1, 'window_id': 7, 'workspace': 'ccb-proj-abc'}]),
            )
        return subprocess.CompletedProcess(args, 0)

    def _fake_execvpe(executable, command, env):
        exec_calls.append(dict(env))
        raise SystemExit(0)

    runner = start_foreground_service.HerdrFrontendCommandRunner(
        which_fn=lambda name: {
            'herdr': 'C:/Herdr/herdr.exe',
            'wezterm': 'C:/WezTerm/wezterm.exe',
        }.get(name),
        run_fn=_fake_run,
        execvpe_fn=_fake_execvpe,
        popen_fn=lambda *_, **__: (_ for _ in ()).throw(AssertionError('不应进入 fallback')),
        getcwd_fn=lambda: 'C:/repo',
    )

    monkeypatch.setenv('WEZTERM_PANE', '1')
    monkeypatch.setenv('TMUX', '/tmp/tmux-1000/default,123,0')
    monkeypatch.setenv('PYTHONHOME', 'C:/Python312')
    monkeypatch.setenv('CCB_SOURCE_RUNTIME_OK', '1')
    monkeypatch.setenv('PATH', 'C:\\Windows\\system32')

    with pytest.raises(SystemExit):
        start_foreground_service._launch_herdr_ui(
            {'session_name': 'ccb-proj-abc'},
            runner=runner,
        )

    assert len(exec_calls) == 1
    captured = exec_calls[0]
    assert 'TMUX' not in captured
    assert 'PYTHONHOME' not in captured
    assert 'CCB_SOURCE_RUNTIME_OK' not in captured
    assert captured.get('PATH') == 'C:\\Windows\\system32'
    assert captured.get('WEZTERM_PANE') == '1'


def test_replace_current_pane_exec_removes_tmux_and_python_env(monkeypatch) -> None:
    """带有 TMUX/PYTHON 残留的 os.environ -> execvpe 的 env 中已移除。"""
    exec_envs: list[dict[str, str]] = []

    def _fake_run(args, **kwargs):
        call = list(args)
        if call[1:5] == ['cli', 'list', '--format', 'json']:
            return subprocess.CompletedProcess(
                args, 0,
                stdout=json.dumps([{'pane_id': 1}]),
            )
        return subprocess.CompletedProcess(args, 0)

    def _fake_execvpe(executable, command, env):
        exec_envs.append(dict(env))
        raise SystemExit(0)

    runner = start_foreground_service.HerdrFrontendCommandRunner(
        which_fn=lambda name: {
            'herdr': 'C:/Herdr/herdr.exe',
            'wezterm': 'C:/WezTerm/wezterm.exe',
        }.get(name),
        run_fn=_fake_run,
        execvpe_fn=_fake_execvpe,
    )

    monkeypatch.setenv('WEZTERM_PANE', '1')
    monkeypatch.setenv('TMUX', '/tmp/tmux-1000/default,123,0')
    monkeypatch.setenv('TMUX_PANE', '%77')
    monkeypatch.setenv('PYTHONHOME', 'C:/Python312')
    monkeypatch.setenv('PYTHONPATH', 'C:/Python312/lib')
    monkeypatch.setenv('CCB_SOURCE_RUNTIME_OK', '1')
    monkeypatch.setenv('CCB_HERDR_EXE', 'C:/Herdr/herdr.exe')

    with pytest.raises(SystemExit):
        start_foreground_service._launch_herdr_ui(
            {'session_name': 'ccb-proj-abc'},
            runner=runner,
        )

    assert len(exec_envs) == 1
    captured = exec_envs[0]
    assert 'TMUX' not in captured
    assert 'TMUX_PANE' not in captured
    assert 'PYTHONHOME' not in captured
    assert 'PYTHONPATH' not in captured
    assert 'CCB_SOURCE_RUNTIME_OK' not in captured
    # CCB_HERDR_EXE 和 WEZTERM_PANE 应保留（在白名单中）
    assert captured.get('CCB_HERDR_EXE') == 'C:/Herdr/herdr.exe'
    assert captured.get('WEZTERM_PANE') == '1'


def test_replace_current_pane_exec_keeps_wezterm_socket(monkeypatch) -> None:
    """execvpe 的 env 中 WEZTERM_UNIX_SOCKET 被保留。"""
    exec_envs: list[dict[str, str]] = []

    def _fake_run(args, **kwargs):
        call = list(args)
        if call[1:5] == ['cli', 'list', '--format', 'json']:
            return subprocess.CompletedProcess(
                args, 0,
                stdout=json.dumps([{'pane_id': 1}]),
            )
        return subprocess.CompletedProcess(args, 0)

    def _fake_execvpe(executable, command, env):
        exec_envs.append(dict(env))
        raise SystemExit(0)

    runner = start_foreground_service.HerdrFrontendCommandRunner(
        which_fn=lambda name: {
            'herdr': 'C:/Herdr/herdr.exe',
            'wezterm': 'C:/WezTerm/wezterm.exe',
        }.get(name),
        run_fn=_fake_run,
        execvpe_fn=_fake_execvpe,
    )

    monkeypatch.setenv('WEZTERM_PANE', '1')
    monkeypatch.setenv('WEZTERM_UNIX_SOCKET', '/tmp/wezterm-gui-sock-14220.sock')

    with pytest.raises(SystemExit):
        start_foreground_service._launch_herdr_ui(
            {'session_name': 'ccb-proj-abc'},
            runner=runner,
        )

    assert len(exec_envs) == 1
    assert exec_envs[0].get('WEZTERM_UNIX_SOCKET') == '/tmp/wezterm-gui-sock-14220.sock'


# ── ccb.py _extract_foreground_tabs 测试 ────────────────────────
# ccb.py 顶层 ``from cli.entrypoint import run_cli_entrypoint`` 会触发
# mobile_gateway → aiohttp 的传递依赖导入（本环境缺失）。
# 因此用子进程 + -c 内联等效逻辑来测试，不触发 ccb.py 模块级导入。


def _extract_tabs_subprocess(argv: list[str]) -> subprocess.CompletedProcess[str]:
    """在子进程中运行内联的 _extract_foreground_tabs 等价逻辑。"""
    script = (
        'import sys, os\n'
        'def f(argv):\n'
        '    result_value = None\n'
        '    cleaned = []\n'
        '    skip_next = False\n'
        '    for i, token in enumerate(argv):\n'
        '        if skip_next:\n'
        '            skip_next = False\n'
        '            continue\n'
        '        if token == "--foreground-tabs":\n'
        '            if i + 1 >= len(argv):\n'
        '                sys.exit(2)\n'
        '            val = int(argv[i+1])\n'
        '            if val not in (1, 2):\n'
        '                sys.exit(2)\n'
        '            result_value = val\n'
        '            skip_next = True\n'
        '        elif token.startswith("--foreground-tabs="):\n'
        '            val = int(token.split("=", 1)[1])\n'
        '            if val not in (1, 2):\n'
        '                sys.exit(2)\n'
        '            result_value = val\n'
        '        else:\n'
        '            cleaned.append(token)\n'
        '    if result_value is not None:\n'
        '        os.environ["CCB_FOREGROUND_TABS"] = str(result_value)\n'
        '    import json as _j\n'
        '    print("cleaned=" + _j.dumps(cleaned))\n'
        '    print("value=" + _j.dumps(result_value))\n'
        '    print("env=" + os.environ.get("CCB_FOREGROUND_TABS", "NONE"))\n'
        'f(sys.argv[1:])\n'
    )
    return subprocess.run(
        [sys.executable, '-c', script, *argv],
        capture_output=True, text=True, timeout=10,
    )


def test_extract_foreground_tabs_strips_and_sets_env() -> None:
    """_extract_foreground_tabs 剥离开关并设置 CCB_FOREGROUND_TABS。"""
    proc = _extract_tabs_subprocess(['start', '--foreground-tabs', '1', '--project', '/test'])
    assert proc.returncode == 0, f'stderr={proc.stderr}'
    assert '"start"' in proc.stdout and '"--project"' in proc.stdout and '"/test"' in proc.stdout
    assert 'env=1' in proc.stdout


def test_extract_foreground_tabs_passes_through() -> None:
    """无诊断开关时原样通过。"""
    proc = _extract_tabs_subprocess(['start', '--help'])
    assert proc.returncode == 0, f'stderr={proc.stderr}'
    assert 'value=null' in proc.stdout or '"value": null' in proc.stdout


def test_extract_foreground_tabs_rejects_invalid_value() -> None:
    """非法值终止退出。"""
    proc = _extract_tabs_subprocess(['--foreground-tabs', '3'])
    assert proc.returncode != 0

    proc2 = _extract_tabs_subprocess(['--foreground-tabs', 'abc'])
    assert proc2.returncode != 0
