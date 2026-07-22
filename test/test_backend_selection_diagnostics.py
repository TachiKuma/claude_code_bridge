from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from cli.services.backend_selection_diagnostics import backend_selection_summary
from cli.render_runtime.ops_views_doctor import render_doctor
from cli.services import start_foreground as start_foreground_service


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def test_render_doctor_includes_backend_selection_summary() -> None:
    ccbd = {
        'state': 'unmounted',
        'health': 'unmounted',
        'generation': 0,
        'last_heartbeat_at': None,
        'pid_alive': False,
        'socket_connectable': False,
        'heartbeat_fresh': False,
        'takeover_allowed': True,
        'reason': 'not mounted',
        'active_execution_count': 0,
        'recoverable_execution_count': 0,
        'nonrecoverable_execution_count': 0,
        'pending_items_count': 0,
        'terminal_pending_count': 0,
        'recoverable_execution_providers': [],
        'nonrecoverable_execution_providers': [],
    }
    lines = render_doctor(
        {
            'project': '/repo',
            'project_id': 'repo-id',
            'installation': {},
            'entrypoint': {},
            'runtime': {},
            'requirements': {},
            'config': {},
            'backend_selection': {
                'backend_impl': 'tmux',
                'requested_backend': 'auto',
                'effective_backend': 'tmux',
                'source': 'env',
                'fallback_used': True,
                'fallback_reason': 'rmux route approval is missing',
                'diagnostic': 'mux backend auto fallback to tmux',
            },
            'ccbd': ccbd,
            'agents': [],
        }
    )

    assert 'backend_selection_backend_impl: tmux' in lines
    assert 'backend_selection_requested: auto' in lines
    assert 'backend_selection_effective: tmux' in lines
    assert 'backend_selection_fallback_used: True' in lines
    assert 'ccbd_tmux_socket_path: None' in lines


def test_backend_selection_summary_returns_failure_for_invalid_config(tmp_path: Path) -> None:
    project_root = tmp_path / 'repo-invalid-config'
    _write(project_root / '.ccb' / 'ccb.config', 'version = 2\nunknown = true\n')
    context = SimpleNamespace(project=SimpleNamespace(project_root=project_root))

    summary = backend_selection_summary(context)

    assert summary['failure_reason'] == 'config-invalid'
    assert 'config load failed' in str(summary['diagnostic'])


def test_backend_selection_summary_does_not_treat_default_tmux_as_explicit(
    tmp_path: Path,
    monkeypatch,
) -> None:
    project_root = tmp_path / 'repo-default-mux'
    _write(project_root / '.ccb' / 'ccb.config', 'demo:codex\n')
    monkeypatch.setenv('CCB_MUX_BACKEND', 'auto')
    context = SimpleNamespace(project=SimpleNamespace(project_root=project_root))

    summary = backend_selection_summary(context)

    assert summary['requested_backend'] == 'auto'
    assert summary['source'] == 'env'


def test_backend_selection_summary_uses_explicit_runtime_mux_over_env(
    tmp_path: Path,
    monkeypatch,
) -> None:
    project_root = tmp_path / 'repo-explicit-mux'
    _write(
        project_root / '.ccb' / 'ccb.config',
        """version = 2
default_agents = ["demo"]
layout = "demo:codex"

[runtime.mux]
backend = "tmux"

[agents.demo]
provider = "codex"
target = "."
workspace_mode = "inplace"
restore = "auto"
permission = "manual"
""",
    )
    monkeypatch.setenv('CCB_MUX_BACKEND', 'auto')
    context = SimpleNamespace(project=SimpleNamespace(project_root=project_root))

    summary = backend_selection_summary(context)

    assert summary['requested_backend'] == 'tmux'
    assert summary['source'] == 'project_config'


def test_foreground_attach_error_includes_selection_summary_for_missing_tmux_payload() -> None:
    ready, error = start_foreground_service._attach_target_ready(
        {
            'namespace_backend_impl': 'tmux',
            'namespace_ui_attachable': True,
            'backend_selection': {
                'requested_backend': 'rmux',
                'effective_backend': None,
                'source': 'project_config',
                'fallback_used': False,
                'failure_reason': 'route-not-approved',
                'diagnostic': 'rmux backend requested but route approval is missing',
            },
        },
        env={},
    )

    assert ready is False
    assert 'backend_requested=rmux' in error
    assert 'backend_failure=route-not-approved' in error


def test_foreground_attach_error_omits_selection_summary_for_legacy_payload() -> None:
    ready, error = start_foreground_service._attach_target_ready(
        {
            'namespace_backend_impl': 'tmux',
            'namespace_ui_attachable': True,
        },
        env={},
    )

    assert ready is False
    assert 'selection:' not in error
