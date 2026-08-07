from __future__ import annotations

import os
import sys
from types import SimpleNamespace

import pytest

from cli.models import ParsedHerdrOpenCommand
from cli.parser import CliParser, CliUsageError
from cli.services.herdr_bootstrap import ensure_herdr_bootstrap_env
from cli.services.herdr_common import query_herdr_server_status, resolve_herdr_executable


@pytest.fixture()
def parser() -> CliParser:
    return CliParser()


# --- parse_herdr ---------------------------------------------------------


def test_parse_herdr_open_defaults(parser: CliParser) -> None:
    parsed = parser.parse(['herdr', 'open'])
    assert parsed == ParsedHerdrOpenCommand(project=None, kind='herdr-open')


def test_parse_herdr_open_with_flags(parser: CliParser) -> None:
    parsed = parser.parse(
        ['herdr', 'open', '--no-attach', '--herdr-session', 'sess-1', '--herdr-exe', '/x/herdr.exe']
    )
    assert parsed == ParsedHerdrOpenCommand(
        project=None,
        herdr_exe='/x/herdr.exe',
        herdr_session='sess-1',
        no_attach=True,
        kind='herdr-open',
    )


def test_parse_herdr_requires_subcommand(parser: CliParser) -> None:
    with pytest.raises(CliUsageError, match='herdr supports'):
        parser.parse(['herdr'])


def test_parse_herdr_rejects_unknown_subcommand(parser: CliParser) -> None:
    with pytest.raises(CliUsageError, match='herdr supports'):
        parser.parse(['herdr', 'attach'])


# --- ensure_herdr_bootstrap_env ------------------------------------------


def test_bootstrap_rejects_missing_executable(monkeypatch) -> None:
    monkeypatch.setattr(
        'cli.services.herdr_bootstrap.resolve_herdr_executable',
        lambda explicit=None: None,
    )
    result = ensure_herdr_bootstrap_env()
    assert result['ok'] is False
    assert 'Herdr executable not found' in str(result['reason'])


def test_bootstrap_rejects_unqueryable_server(monkeypatch) -> None:
    monkeypatch.setattr(
        'cli.services.herdr_bootstrap.resolve_herdr_executable',
        lambda explicit=None: '/x/herdr.exe',
    )
    monkeypatch.setattr(
        'cli.services.herdr_bootstrap.query_herdr_server_status',
        lambda exe: None,
    )
    result = ensure_herdr_bootstrap_env()
    assert result['ok'] is False
    assert 'Failed to query Herdr server status' in str(result['reason'])


def test_bootstrap_rejects_stopped_server(monkeypatch) -> None:
    monkeypatch.setattr(
        'cli.services.herdr_bootstrap.resolve_herdr_executable',
        lambda explicit=None: '/x/herdr.exe',
    )
    monkeypatch.setattr(
        'cli.services.herdr_bootstrap.query_herdr_server_status',
        lambda exe: {'status': 'stopped', 'running': False, 'compatible': True},
    )
    result = ensure_herdr_bootstrap_env()
    assert result['ok'] is False
    assert 'server is not running' in str(result['reason'])


def test_bootstrap_rejects_incompatible_protocol(monkeypatch) -> None:
    monkeypatch.setattr(
        'cli.services.herdr_bootstrap.resolve_herdr_executable',
        lambda explicit=None: '/x/herdr.exe',
    )
    monkeypatch.setattr(
        'cli.services.herdr_bootstrap.query_herdr_server_status',
        lambda exe: {'status': 'running', 'running': True, 'compatible': False, 'protocol': 3},
    )
    result = ensure_herdr_bootstrap_env()
    assert result['ok'] is False
    assert 'not compatible' in str(result['reason'])


def _bootstrap_success_mocks(monkeypatch, *, status=None):
    monkeypatch.delenv('CCB_HERDR_EXE', raising=False)
    monkeypatch.delenv('CCB_HERDR_SESSION', raising=False)
    monkeypatch.delenv('CCB_HERDR_CAPABILITY_REPORT', raising=False)
    monkeypatch.setattr(
        'cli.services.herdr_bootstrap.resolve_herdr_executable',
        lambda explicit=None: '/x/herdr.exe',
    )
    monkeypatch.setattr(
        'cli.services.herdr_bootstrap.query_herdr_server_status',
        lambda exe: status
        or {
            'status': 'running',
            'running': True,
            'compatible': True,
            'protocol': 19,
            'session': 'sess-live',
        },
    )
    monkeypatch.setattr(
        'cli.services.herdr_bootstrap._probe_herdr_read_capabilities',
        lambda exe: {
            'session_attach': True,
            'workspace_list': True,
            'pane_list': True,
        },
    )
    monkeypatch.setattr(
        'cli.services.herdr_bootstrap._write_capability_report',
        lambda report: 'C:/tmp/ccb-herdr-capability-test.json',
    )


def test_bootstrap_sets_env_and_succeeds(monkeypatch) -> None:
    _bootstrap_success_mocks(monkeypatch)
    result = ensure_herdr_bootstrap_env()
    assert result['ok'] is True
    assert result['herdr_exe'] == '/x/herdr.exe'
    assert result['herdr_session'] == 'sess-live'
    assert os.environ['CCB_HERDR_EXE'] == '/x/herdr.exe'
    assert os.environ['CCB_HERDR_SESSION'] == 'sess-live'
    assert os.environ['CCB_HERDR_CAPABILITY_REPORT'] == 'C:/tmp/ccb-herdr-capability-test.json'


def test_bootstrap_prefers_explicit_session(monkeypatch) -> None:
    _bootstrap_success_mocks(monkeypatch)
    result = ensure_herdr_bootstrap_env(herdr_session='sess-explicit')
    assert result['ok'] is True
    assert result['herdr_session'] == 'sess-explicit'
    assert os.environ['CCB_HERDR_SESSION'] == 'sess-explicit'


def test_bootstrap_rejects_failed_read_probes(monkeypatch) -> None:
    _bootstrap_success_mocks(monkeypatch)
    monkeypatch.setattr(
        'cli.services.herdr_bootstrap._probe_herdr_read_capabilities',
        lambda exe: {
            'session_attach': True,
            'workspace_list': False,
            'pane_list': True,
        },
    )
    result = ensure_herdr_bootstrap_env()
    assert result['ok'] is False
    assert 'workspace_list' in str(result['reason'])


def test_build_capability_report_covers_known_capabilities() -> None:
    from cli.services.herdr_bootstrap import _build_capability_report

    report = _build_capability_report(
        {'session_attach': True, 'workspace_list': True, 'pane_list': True}
    )
    assert report['verdict'] == 'pass'
    assert report['adapter_recommendation'] == 'continue'
    assert report['windows_beta_gaps'] == []
    assert report['blocking_gaps'] == []
    assert report['command_status']['session_attach'] == 'supported'
    assert report['command_status']['kill_pane'] == 'supported'


# --- handle_herdr_open daemon conflict ------------------------------------


def _stub_bootstrap_ok(monkeypatch) -> None:
    monkeypatch.setattr(
        'cli.services.herdr_bootstrap.ensure_herdr_bootstrap_env',
        lambda **kwargs: {'ok': True, 'warnings': []},
    )


def test_handle_herdr_open_rejects_conflicting_tmux_daemon(monkeypatch, capsys) -> None:
    from cli.phase2_runtime.handlers_start import handle_herdr_open

    _stub_bootstrap_ok(monkeypatch)
    monkeypatch.setattr(
        'cli.phase2_runtime.handlers_start._daemon_running_and_backend',
        lambda context: (True, 'tmux'),
    )
    rc = handle_herdr_open(None, ParsedHerdrOpenCommand(project=None), sys.stdout, None)
    assert rc == 1
    err = capsys.readouterr().err
    assert 'tmux' in err
    assert 'ccb kill' in err


def test_handle_herdr_open_rejects_daemon_with_unknown_backend(monkeypatch, capsys) -> None:
    from cli.phase2_runtime.handlers_start import handle_herdr_open

    _stub_bootstrap_ok(monkeypatch)
    monkeypatch.setattr(
        'cli.phase2_runtime.handlers_start._daemon_running_and_backend',
        lambda context: (True, None),
    )
    rc = handle_herdr_open(None, ParsedHerdrOpenCommand(project=None), sys.stdout, None)
    assert rc == 1
    assert 'ccb kill' in capsys.readouterr().err


def test_handle_herdr_open_proceeds_when_daemon_is_herdr(monkeypatch) -> None:
    from cli.phase2_runtime.handlers_start import handle_herdr_open

    _stub_bootstrap_ok(monkeypatch)
    monkeypatch.setattr(
        'cli.phase2_runtime.handlers_start._daemon_running_and_backend',
        lambda context: (True, 'herdr'),
    )
    started: dict[str, bool] = {}

    def _fake_handle_start(context, command, out, services) -> int:
        started['started'] = True
        return 0

    monkeypatch.setattr(
        'cli.phase2_runtime.handlers_start.handle_start',
        _fake_handle_start,
    )
    rc = handle_herdr_open(None, ParsedHerdrOpenCommand(project=None), sys.stdout, None)
    assert rc == 0
    assert started.get('started') is True


def test_daemon_running_and_backend_detects_herdr(monkeypatch) -> None:
    from cli.phase2_runtime.handlers_start import _daemon_running_and_backend

    class _FakeInspection:
        pid_alive = True
        socket_connectable = True

    class _FakeState:
        backend_impl = 'herdr'

    class _FakeStore:
        def load(self):
            return _FakeState()

    monkeypatch.setattr(
        'cli.services.daemon.inspect_daemon',
        lambda context: (None, None, _FakeInspection()),
    )
    monkeypatch.setattr(
        'ccbd.services.project_namespace_state_runtime.stores.ProjectNamespaceStateStore',
        lambda paths: _FakeStore(),
    )
    running, backend = _daemon_running_and_backend(SimpleNamespace(paths=SimpleNamespace()))
    assert running is True
    assert backend == 'herdr'


def test_daemon_running_and_backend_fails_closed_on_inspection_error(
    monkeypatch,
) -> None:
    """DEC-3: generic inspection errors → fail-closed (treat as potential conflict)."""
    from cli.phase2_runtime.handlers_start import _daemon_running_and_backend

    def _boom(context):
        raise RuntimeError('no lease')

    monkeypatch.setattr('cli.services.daemon.inspect_daemon', _boom)
    running, backend = _daemon_running_and_backend(SimpleNamespace(paths=SimpleNamespace()))
    assert running is True, 'DEC-3: inspection error should be fail-closed'
    assert backend is None


# --- resolve_herdr_executable --------------------------------------------


def test_resolve_herdr_explicit_existing(tmp_path) -> None:
    exe = tmp_path / 'herdr.exe'
    exe.write_text('')
    assert resolve_herdr_executable(explicit=str(exe)) == str(exe)


def test_resolve_herdr_via_env(monkeypatch, tmp_path) -> None:
    exe = tmp_path / 'herdr.exe'
    exe.write_text('')
    monkeypatch.setenv('CCB_HERDR_EXE', str(exe))
    assert resolve_herdr_executable() == str(exe)


def test_resolve_herdr_nonexistent_explicit_falls_back(monkeypatch) -> None:
    monkeypatch.delenv('CCB_HERDR_EXE', raising=False)
    monkeypatch.setattr('cli.services.herdr_common.shutil.which', lambda name: None)
    monkeypatch.setattr(
        'cli.services.herdr_common.os.path.isfile',
        lambda path: False,
    )
    assert resolve_herdr_executable(explicit='C:/nonexistent/herdr.exe') is None


# --- query_herdr_server_status --------------------------------------------


def test_query_herdr_server_status_running(monkeypatch) -> None:
    import subprocess

    class _FakeResult:
        returncode = 0
        stdout = '{"status":"running","running":true,"compatible":true,"protocol":19}'

    monkeypatch.setattr(subprocess, 'run', lambda *args, **kwargs: _FakeResult())
    payload = query_herdr_server_status('/x/herdr.exe')
    assert payload is not None
    assert payload['running'] is True
    assert payload['protocol'] == 19


def test_query_herdr_server_status_nonzero_exit(monkeypatch) -> None:
    import subprocess

    class _FakeResult:
        returncode = 1
        stdout = ''

    monkeypatch.setattr(subprocess, 'run', lambda *args, **kwargs: _FakeResult())
    assert query_herdr_server_status('/x/herdr.exe') is None


def test_query_herdr_server_status_malformed_json(monkeypatch) -> None:
    import subprocess

    class _FakeResult:
        returncode = 0
        stdout = 'not-json'

    monkeypatch.setattr(subprocess, 'run', lambda *args, **kwargs: _FakeResult())
    assert query_herdr_server_status('/x/herdr.exe') is None


# ---------------------------------------------------------------------------
# ITEM-2 fix 3: nested server shape unwrapping
# ---------------------------------------------------------------------------

def test_bootstrap_handles_nested_result_server_shape(monkeypatch) -> None:
    """Nested {"result":{"server":{"running":true,...}}} unwraps correctly."""
    monkeypatch.delenv('CCB_HERDR_EXE', raising=False)
    monkeypatch.delenv('CCB_HERDR_SESSION', raising=False)
    monkeypatch.delenv('CCB_HERDR_CAPABILITY_REPORT', raising=False)
    monkeypatch.setattr(
        'cli.services.herdr_bootstrap.resolve_herdr_executable',
        lambda explicit=None: '/x/herdr.exe',
    )
    monkeypatch.setattr(
        'cli.services.herdr_bootstrap.query_herdr_server_status',
        lambda exe: {
            'result': {
                'server': {
                    'running': True,
                    'compatible': True,
                    'protocol': 19,
                    'session': 'sess-nested',
                }
            }
        },
    )
    monkeypatch.setattr(
        'cli.services.herdr_bootstrap._probe_herdr_read_capabilities',
        lambda exe: {'session_attach': True, 'workspace_list': True, 'pane_list': True},
    )
    monkeypatch.setattr(
        'cli.services.herdr_bootstrap._write_capability_report',
        lambda report: '/tmp/cap.json',
    )
    result = ensure_herdr_bootstrap_env()
    assert result['ok'] is True, f'Nested shape should succeed, got: {result}'
    assert result['herdr_session'] == 'sess-nested'


def test_bootstrap_nested_shape_rejects_stopped(monkeypatch) -> None:
    """Nested shape with running=False is correctly rejected."""
    monkeypatch.delenv('CCB_HERDR_EXE', raising=False)
    monkeypatch.delenv('CCB_HERDR_SESSION', raising=False)
    monkeypatch.delenv('CCB_HERDR_CAPABILITY_REPORT', raising=False)
    monkeypatch.setattr(
        'cli.services.herdr_bootstrap.resolve_herdr_executable',
        lambda explicit=None: '/x/herdr.exe',
    )
    monkeypatch.setattr(
        'cli.services.herdr_bootstrap.query_herdr_server_status',
        lambda exe: {
            'result': {
                'server': {
                    'running': False,
                    'compatible': True,
                }
            }
        },
    )
    result = ensure_herdr_bootstrap_env()
    assert result['ok'] is False
    assert 'server is not running' in str(result['reason'])


def test_bootstrap_nested_shape_rejects_incompatible(monkeypatch) -> None:
    """Nested shape with compatible=False is correctly rejected."""
    monkeypatch.delenv('CCB_HERDR_EXE', raising=False)
    monkeypatch.delenv('CCB_HERDR_SESSION', raising=False)
    monkeypatch.delenv('CCB_HERDR_CAPABILITY_REPORT', raising=False)
    monkeypatch.setattr(
        'cli.services.herdr_bootstrap.resolve_herdr_executable',
        lambda explicit=None: '/x/herdr.exe',
    )
    monkeypatch.setattr(
        'cli.services.herdr_bootstrap.query_herdr_server_status',
        lambda exe: {
            'result': {
                'server': {
                    'running': True,
                    'compatible': False,
                    'protocol': 2,
                }
            }
        },
    )
    result = ensure_herdr_bootstrap_env()
    assert result['ok'] is False
    assert 'not compatible' in str(result['reason'])


# ---------------------------------------------------------------------------
# ITEM-2 fix 2: XDG platform gate
# ---------------------------------------------------------------------------

def test_herdr_command_env_clears_xdg_on_windows(monkeypatch) -> None:
    """XDG_* is cleared on Windows, HERDR_CONFIG_PATH is set."""
    import sys as _sys
    from lib.cli.services.herdr_common import herdr_command_env

    if _sys.platform != 'win32':
        import pytest
        pytest.skip('test only meaningful on Windows')

    monkeypatch.setenv('XDG_CONFIG_HOME', '/fake/xdg/config')
    monkeypatch.setenv('XDG_CACHE_HOME', '/fake/xdg/cache')
    monkeypatch.setenv('XDG_STATE_HOME', '/fake/xdg/state')
    monkeypatch.delenv('HERDR_CONFIG_PATH', raising=False)

    env = herdr_command_env()
    assert 'XDG_CONFIG_HOME' not in env
    assert 'XDG_CACHE_HOME' not in env
    assert 'XDG_STATE_HOME' not in env
    assert 'HERDR_CONFIG_PATH' in env


def test_herdr_command_env_preserves_xdg_on_non_windows(monkeypatch) -> None:
    """XDG_* is preserved on non-Windows platforms."""
    from lib.cli.services.herdr_common import herdr_command_env

    monkeypatch.setattr('sys.platform', 'linux')
    monkeypatch.setenv('XDG_CONFIG_HOME', '/fake/xdg/config')
    monkeypatch.setenv('XDG_CACHE_HOME', '/fake/xdg/cache')

    env = herdr_command_env()
    assert env.get('XDG_CONFIG_HOME') == '/fake/xdg/config'
    assert env.get('XDG_CACHE_HOME') == '/fake/xdg/cache'
    # HERDR_CONFIG_PATH should NOT be forced on non-Windows
    assert 'HERDR_CONFIG_PATH' not in env or env['HERDR_CONFIG_PATH'] == os.environ.get('HERDR_CONFIG_PATH', '')
