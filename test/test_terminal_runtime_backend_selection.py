from __future__ import annotations

from pathlib import Path

import terminal_runtime.backend_selection as backend_selection_module
import pytest

from terminal_runtime.backend_resolver import (
    MuxBackendSelectionError,
    RmuxAvailability,
    RmuxCapabilityStatus,
    RmuxRouteApproval,
    default_rmux_capability_reader,
    default_route_approval_reader,
    resolve_mux_backend,
)
from terminal_runtime.api import get_backend_selection_diagnostics
from terminal_runtime.backend_selection import TerminalBackendSelection, TerminalLayoutService
from ccbd.services.project_namespace_runtime.controller import default_project_namespace_backend


class _FakeBackend:
    def __init__(self, name: str) -> None:
        self.name = name


def test_backend_selection_caches_detected_backend() -> None:
    calls: list[str] = []
    selection = TerminalBackendSelection(
        detect_terminal_fn=lambda: 'tmux',
        tmux_backend_factory=lambda: calls.append('tmux') or _FakeBackend('tmux'),
    )

    first = selection.get_backend()
    second = selection.get_backend()

    assert first is second
    assert isinstance(first, _FakeBackend)
    assert first.name == 'tmux'
    assert calls == ['tmux']


def test_backend_selection_re_resolves_explicit_backend_after_tmux_cache() -> None:
    selection = TerminalBackendSelection(
        detect_terminal_fn=lambda: None,
        tmux_backend_factory=lambda: _FakeBackend('tmux'),
        rmux_backend_factory=lambda: _FakeBackend('rmux'),
        route_approval_reader=lambda: RmuxRouteApproval(False, None),
        rmux_availability_reader=lambda: RmuxAvailability(True),
        capability_reader=lambda: RmuxCapabilityStatus(True, None),
    )

    assert selection.get_backend().name == 'tmux'
    with pytest.raises(MuxBackendSelectionError) as exc_info:
        selection.get_backend('rmux')

    assert exc_info.value.to_diagnostics()['failure_reason'] == 'route-not-approved'


def test_backend_selection_uses_session_terminal_field() -> None:
    captured: dict[str, object] = {}

    def _tmux_backend_factory(socket_name=None, socket_path=None):
        captured['socket_name'] = socket_name
        captured['socket_path'] = socket_path
        return _FakeBackend('tmux')

    selection = TerminalBackendSelection(
        detect_terminal_fn=lambda: None,
        tmux_backend_factory=_tmux_backend_factory,
    )

    tmux_backend = selection.get_backend_for_session({'terminal': 'tmux', 'tmux_socket_name': 'sock-demo'})
    assert isinstance(tmux_backend, _FakeBackend)
    assert tmux_backend.name == 'tmux'
    assert captured['socket_name'] == 'sock-demo'
    assert captured['socket_path'] is None
    selection.get_backend_for_session({'terminal': 'tmux', 'tmux_socket_path': '/tmp/ccb.sock'})
    assert captured['socket_path'] == '/tmp/ccb.sock'
    assert selection.get_pane_id_from_session({'pane_id': '%1', 'tmux_session': '%old'}) == '%1'
    assert selection.get_pane_id_from_session({'tmux_session': '%old'}) == '%old'


def test_backend_selection_uses_psmux_session_backend() -> None:
    captured: dict[str, object] = {}

    def _psmux_backend_factory(namespace=None, socket_path=None):
        captured['namespace'] = namespace
        captured['socket_path'] = socket_path
        return _FakeBackend('psmux')

    selection = TerminalBackendSelection(
        detect_terminal_fn=lambda: None,
        tmux_backend_factory=lambda **kwargs: _FakeBackend('tmux'),
        psmux_backend_factory=_psmux_backend_factory,
    )

    backend = selection.get_backend_for_session(
        {
            'terminal_backend': 'rmux',
            'rmux_namespace': 'ccb-demo',
            'tmux_socket_path': r'\\.\pipe\ccb-demo',
        }
    )

    assert isinstance(backend, _FakeBackend)
    assert backend.name == 'psmux'
    assert captured == {'namespace': 'ccb-demo', 'socket_path': r'\\.\pipe\ccb-demo'}


def test_backend_selection_uses_rmux_factory_for_rmux_backend() -> None:
    captured: dict[str, object] = {}

    def _rmux_backend_factory(namespace=None, socket_path=None):
        captured['namespace'] = namespace
        captured['socket_path'] = socket_path
        return _FakeBackend('rmux')

    selection = TerminalBackendSelection(
        detect_terminal_fn=lambda: None,
        tmux_backend_factory=lambda **kwargs: _FakeBackend('tmux'),
        psmux_backend_factory=lambda **kwargs: _FakeBackend('psmux'),
        rmux_backend_factory=_rmux_backend_factory,
    )

    backend = selection.get_backend_for_session(
        {
            'terminal_backend': 'rmux',
            'rmux_namespace': 'ccb-demo',
            'tmux_socket_path': r'\\.\pipe\ccb-demo',
        }
    )

    assert backend.name == 'rmux'
    assert captured == {'namespace': 'ccb-demo', 'socket_path': r'\\.\pipe\ccb-demo'}


def test_backend_selection_uses_backend_impl_and_mux_backend_fields() -> None:
    selected: list[dict[str, object]] = []

    def _psmux_backend_factory(namespace=None, socket_path=None):
        selected.append({'namespace': namespace, 'socket_path': socket_path})
        return _FakeBackend('psmux')

    selection = TerminalBackendSelection(
        detect_terminal_fn=lambda: None,
        tmux_backend_factory=lambda **kwargs: _FakeBackend('tmux'),
        psmux_backend_factory=_psmux_backend_factory,
    )

    assert selection.get_backend_for_session({'backend_impl': 'psmux', 'psmux_namespace': 'impl-ns'}).name == 'psmux'
    assert selected[-1] == {'namespace': 'impl-ns', 'socket_path': None}
    assert selection.get_backend_for_session({'mux_backend': 'rmux', 'tmux_socket_name': 'fallback-ns'}).name == 'psmux'
    assert selected[-1] == {'namespace': 'fallback-ns', 'socket_path': None}


def test_backend_selection_can_cache_explicit_psmux_backend() -> None:
    calls: list[str] = []
    selection = TerminalBackendSelection(
        detect_terminal_fn=lambda: 'tmux',
        tmux_backend_factory=lambda: _FakeBackend('tmux'),
        psmux_backend_factory=lambda: calls.append('psmux') or _FakeBackend('psmux'),
        route_approval_reader=lambda: RmuxRouteApproval(True, 'approval-report.md#rmux-route'),
        rmux_availability_reader=lambda: RmuxAvailability(True),
        capability_reader=lambda: RmuxCapabilityStatus(True, None),
    )

    first = selection.get_backend('psmux')
    second = selection.get_backend('rmux')

    assert first is second
    assert isinstance(first, _FakeBackend)
    assert first.name == 'psmux'
    assert calls == ['psmux']


def test_backend_selection_normalizes_explicit_psmux_to_rmux_when_rmux_exists() -> None:
    calls: list[str] = []
    selection = TerminalBackendSelection(
        detect_terminal_fn=lambda: 'tmux',
        tmux_backend_factory=lambda: calls.append('tmux') or _FakeBackend('tmux'),
        psmux_backend_factory=lambda: calls.append('psmux') or _FakeBackend('psmux'),
        rmux_backend_factory=lambda: calls.append('rmux') or _FakeBackend('rmux'),
        route_approval_reader=lambda: RmuxRouteApproval(True, 'approval-report.md#rmux-route'),
        rmux_availability_reader=lambda: RmuxAvailability(True),
        capability_reader=lambda: RmuxCapabilityStatus(True, None),
    )

    backend = selection.get_backend('psmux')

    assert backend.name == 'rmux'
    assert calls == ['rmux']


def test_backend_selection_can_cache_explicit_rmux_backend() -> None:
    calls: list[str] = []
    selection = TerminalBackendSelection(
        detect_terminal_fn=lambda: 'tmux',
        tmux_backend_factory=lambda: _FakeBackend('tmux'),
        psmux_backend_factory=lambda: _FakeBackend('psmux'),
        rmux_backend_factory=lambda: calls.append('rmux') or _FakeBackend('rmux'),
        route_approval_reader=lambda: RmuxRouteApproval(True, 'approval-report.md#rmux-route'),
        rmux_availability_reader=lambda: RmuxAvailability(True),
        capability_reader=lambda: RmuxCapabilityStatus(True, 'capability.yaml'),
    )

    first = selection.get_backend('rmux')
    second = selection.get_backend('psmux')

    assert first is second
    assert isinstance(first, _FakeBackend)
    assert first.name == 'rmux'
    assert calls == ['rmux']


def test_mux_backend_default_selects_tmux_without_fallback() -> None:
    selection = TerminalBackendSelection(
        detect_terminal_fn=lambda: None,
        tmux_backend_factory=lambda: _FakeBackend('tmux'),
        env={},
    )

    result = selection.select_backend()

    assert result['backend_impl'] == 'tmux'
    assert result['requested_backend'] == 'tmux'
    assert result['effective_backend'] == 'tmux'
    assert result['source'] == 'platform_default'
    assert result['fallback_used'] is False


def test_mux_backend_select_backend_returns_cached_copy() -> None:
    selection = TerminalBackendSelection(
        detect_terminal_fn=lambda: None,
        tmux_backend_factory=lambda: _FakeBackend('tmux'),
        env={},
    )

    first = selection.select_backend()
    first['effective_backend'] = 'rmux'
    second = selection.select_backend()

    assert second['effective_backend'] == 'tmux'


def test_mux_backend_project_config_beats_user_config_and_env() -> None:
    selection = TerminalBackendSelection(
        detect_terminal_fn=lambda: None,
        tmux_backend_factory=lambda: _FakeBackend('tmux'),
        project_config_backend='tmux',
        user_config_backend='rmux',
        env={'CCB_MUX_BACKEND': 'auto'},
    )

    result = selection.select_backend()

    assert result['requested_backend'] == 'tmux'
    assert result['source'] == 'project_config'


def test_mux_backend_env_beats_detected_tmux_terminal() -> None:
    selection = TerminalBackendSelection(
        detect_terminal_fn=lambda: 'tmux',
        tmux_backend_factory=lambda: _FakeBackend('tmux'),
        env={'CCB_MUX_BACKEND': 'auto'},
        platform='win32',
        route_approval_reader=lambda: RmuxRouteApproval(False, None),
        rmux_availability_reader=lambda: RmuxAvailability(True),
        capability_reader=lambda: RmuxCapabilityStatus(True, None),
    )

    result = selection.select_backend()

    assert result['requested_backend'] == 'auto'
    assert result['source'] == 'env'
    assert result['effective_backend'] == 'tmux'
    assert result['fallback_used'] is True


def test_mux_backend_empty_env_does_not_read_ambient_env(monkeypatch) -> None:
    monkeypatch.setenv('CCB_MUX_BACKEND', 'auto')
    selection = TerminalBackendSelection(
        detect_terminal_fn=lambda: None,
        tmux_backend_factory=lambda: _FakeBackend('tmux'),
        env={},
    )

    result = selection.select_backend()

    assert result['requested_backend'] == 'tmux'
    assert result['source'] == 'platform_default'


def test_mux_backend_invalid_env_reports_env_source() -> None:
    selection = TerminalBackendSelection(
        detect_terminal_fn=lambda: None,
        tmux_backend_factory=lambda: _FakeBackend('tmux'),
        env={'CCB_MUX_BACKEND': 'bad'},
    )

    with pytest.raises(MuxBackendSelectionError) as exc_info:
        selection.select_backend()

    assert exc_info.value.to_diagnostics()['source'] == 'env'


def test_mux_backend_availability_uses_injected_env(monkeypatch) -> None:
    monkeypatch.setenv('CCB_RMUX_BIN', 'definitely-not-rmux-from-ambient')

    with pytest.raises(MuxBackendSelectionError) as exc_info:
        resolve_mux_backend(
            cli_backend='rmux',
            env={'CCB_RMUX_BIN': 'also-not-present'},
            route_approval_reader=lambda: RmuxRouteApproval(True, 'approval-report.md#rmux-route'),
        )

    assert exc_info.value.to_diagnostics()['failure_reason'] == 'rmux-unavailable'


def test_default_route_approval_reader_finds_repo_root_from_subdirectory(tmp_path, monkeypatch) -> None:
    report = (
        tmp_path
        / '.codestable'
        / 'features'
        / '2026-07-19-rmux-route-approval'
        / 'approval-report.md'
    )
    report.parent.mkdir(parents=True)
    report.write_text('rmux-route: approved\n', encoding='utf-8')
    subdir = tmp_path / 'nested' / 'work'
    subdir.mkdir(parents=True)
    monkeypatch.chdir(subdir)

    approval = default_route_approval_reader()

    assert approval.approved is True
    assert approval.ref == '.codestable/features/2026-07-19-rmux-route-approval/approval-report.md#rmux-route'


def test_default_route_approval_reader_uses_explicit_project_root_over_cwd(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target_report = (
        tmp_path
        / 'target'
        / '.codestable'
        / 'features'
        / '2026-07-19-rmux-route-approval'
        / 'approval-report.md'
    )
    cwd_report = (
        tmp_path
        / 'cwd'
        / '.codestable'
        / 'features'
        / '2026-07-19-rmux-route-approval'
        / 'approval-report.md'
    )
    target_report.parent.mkdir(parents=True)
    cwd_report.parent.mkdir(parents=True)
    target_report.write_text('rmux-route: approved\n', encoding='utf-8')
    cwd_report.write_text('rmux-route: rejected\n', encoding='utf-8')
    monkeypatch.chdir(cwd_report.parents[3])

    approval = default_route_approval_reader(project_root=target_report.parents[3])

    assert approval.approved is True
    assert approval.ref == '.codestable/features/2026-07-19-rmux-route-approval/approval-report.md#rmux-route'


def test_mux_backend_default_capability_reader_consumes_route_summary(
    tmp_path: Path,
    monkeypatch,
) -> None:
    approval = (
        tmp_path
        / '.codestable'
        / 'features'
        / '2026-07-19-rmux-route-approval'
        / 'approval-report.md'
    )
    approval.parent.mkdir(parents=True)
    approval.write_text('approvals:\n  rmux-route: approved\n', encoding='utf-8')
    summary = approval.parent / 'rmux-route-decision-summary.yaml'
    summary.write_text(
        """decision_id: rmux-route
status: approved
capability_report: .codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/capability-report.json
report_facts:
  blocking_gaps_count: 0
parent_handoff:
  route_approved: true
""",
        encoding='utf-8',
    )
    nested = tmp_path / 'nested' / 'work'
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)
    selection = TerminalBackendSelection(
        detect_terminal_fn=lambda: None,
        tmux_backend_factory=lambda: _FakeBackend('tmux'),
        rmux_backend_factory=lambda: _FakeBackend('rmux'),
        rmux_availability_reader=lambda: RmuxAvailability(True),
    )

    backend = selection.get_backend('rmux')
    result = selection.select_backend('rmux')

    assert backend.name == 'rmux'
    assert result['capability_report_ref'] == (
        '.codestable/roadmap/windows-rmux-native-backend/drafts/'
        'rmux-capability-gate/capability-report.json'
    )


def test_mux_backend_default_capability_reader_uses_explicit_project_root_over_cwd(
    tmp_path: Path,
    monkeypatch,
) -> None:
    target_summary = (
        tmp_path
        / 'target'
        / '.codestable'
        / 'features'
        / '2026-07-19-rmux-route-approval'
        / 'rmux-route-decision-summary.yaml'
    )
    cwd_summary = (
        tmp_path
        / 'cwd'
        / '.codestable'
        / 'features'
        / '2026-07-19-rmux-route-approval'
        / 'rmux-route-decision-summary.yaml'
    )
    target_summary.parent.mkdir(parents=True)
    cwd_summary.parent.mkdir(parents=True)
    target_summary.write_text(
        """status: approved
report_facts:
  blocking_gaps_count: 0
parent_handoff:
  route_approved: true
capability_report: target-capability.json
""",
        encoding='utf-8',
    )
    cwd_summary.write_text(
        """report_facts:
  blocking_gaps_count: 4
parent_handoff:
  route_approved: false
""",
        encoding='utf-8',
    )
    monkeypatch.chdir(cwd_summary.parents[3])

    result = resolve_mux_backend(
        cli_backend='rmux',
        project_root=target_summary.parents[3],
        route_approval_reader=lambda: RmuxRouteApproval(True, 'approval-report.md#rmux-route'),
        rmux_availability_reader=lambda: RmuxAvailability(True),
    )

    assert result['backend_impl'] == 'rmux'
    assert result['capability_report_ref'] == 'target-capability.json'


def test_default_capability_reader_ignores_superseded_zero_gap_reports(
    tmp_path: Path,
) -> None:
    summary = (
        tmp_path
        / '.codestable'
        / 'features'
        / '2026-07-19-rmux-route-approval'
        / 'rmux-route-decision-summary.yaml'
    )
    summary.parent.mkdir(parents=True)
    summary.write_text(
        """decision_id: rmux-route
status: approved
decision_status: approved
capability_report: current-capability.json
report_facts:
  blocking_gaps_count: 7
parent_handoff:
  route_approved: true
superseded_reports:
  - capability_report: old-capability.json
    blocking_gaps_count: 0
""",
        encoding='utf-8',
    )

    status = default_rmux_capability_reader(project_root=tmp_path)

    assert status.satisfied is False
    assert status.ref is None


def test_backend_selection_diagnostics_returns_failure_instead_of_raising(monkeypatch) -> None:
    monkeypatch.delenv('CCB_TERMINAL_BACKEND', raising=False)
    monkeypatch.setenv('CCB_MUX_BACKEND', 'bad')

    diagnostics = get_backend_selection_diagnostics()

    assert diagnostics['failure_reason'] == 'invalid-request'
    assert diagnostics['source'] == 'env'


def test_mux_backend_explicit_rmux_fails_fast_without_route_approval() -> None:
    selection = TerminalBackendSelection(
        detect_terminal_fn=lambda: None,
        tmux_backend_factory=lambda: _FakeBackend('tmux'),
        rmux_backend_factory=lambda: _FakeBackend('rmux'),
        route_approval_reader=lambda: RmuxRouteApproval(False, None),
        rmux_availability_reader=lambda: RmuxAvailability(True),
        capability_reader=lambda: RmuxCapabilityStatus(True, None),
    )

    with pytest.raises(MuxBackendSelectionError) as exc_info:
        selection.get_backend('rmux')

    diagnostics = exc_info.value.to_diagnostics()
    assert diagnostics['failure_reason'] == 'route-not-approved'
    assert diagnostics['requested_backend'] == 'rmux'


def test_default_project_namespace_backend_env_rmux_uses_resolver_fail_fast(monkeypatch) -> None:
    monkeypatch.setenv('CCB_MUX_BACKEND', 'rmux')
    monkeypatch.delenv('CCB_TERMINAL_BACKEND', raising=False)

    with pytest.raises(MuxBackendSelectionError) as exc_info:
        default_project_namespace_backend(
            namespace='ccb-demo',
            socket_path=r'\\.\pipe\ccb-demo',
            route_approval_reader=lambda: RmuxRouteApproval(False, None),
            rmux_availability_reader=lambda: RmuxAvailability(True),
            capability_reader=lambda: RmuxCapabilityStatus(True, None),
        )

    assert exc_info.value.to_diagnostics()['failure_reason'] == 'route-not-approved'


def test_default_project_namespace_backend_project_config_rmux_uses_resolver_fail_fast(
    monkeypatch,
) -> None:
    monkeypatch.delenv('CCB_MUX_BACKEND', raising=False)
    monkeypatch.delenv('CCB_TERMINAL_BACKEND', raising=False)

    with pytest.raises(MuxBackendSelectionError) as exc_info:
        default_project_namespace_backend(
            namespace='ccb-demo',
            socket_path=r'\\.\pipe\ccb-demo',
            project_config_backend='rmux',
            route_approval_reader=lambda: RmuxRouteApproval(False, None),
            rmux_availability_reader=lambda: RmuxAvailability(True),
            capability_reader=lambda: RmuxCapabilityStatus(True, None),
        )

    assert exc_info.value.to_diagnostics()['source'] == 'project_config'
    assert exc_info.value.to_diagnostics()['failure_reason'] == 'route-not-approved'


def test_mux_backend_auto_fallback_records_reason() -> None:
    selection = TerminalBackendSelection(
        detect_terminal_fn=lambda: None,
        tmux_backend_factory=lambda: _FakeBackend('tmux'),
        env={'CCB_MUX_BACKEND': 'auto'},
        platform='win32',
        route_approval_reader=lambda: RmuxRouteApproval(False, None),
        rmux_availability_reader=lambda: RmuxAvailability(True),
        capability_reader=lambda: RmuxCapabilityStatus(True, None),
    )

    backend = selection.get_backend()
    result = selection.select_backend()

    assert backend.name == 'tmux'
    assert result['requested_backend'] == 'auto'
    assert result['effective_backend'] == 'tmux'
    assert result['source'] == 'env'
    assert result['fallback_used'] is True
    assert 'approval' in str(result['fallback_reason'])


def test_mux_backend_approved_rmux_uses_rmux_factory_only() -> None:
    calls: list[str] = []
    selection = TerminalBackendSelection(
        detect_terminal_fn=lambda: None,
        tmux_backend_factory=lambda: calls.append('tmux') or _FakeBackend('tmux'),
        rmux_backend_factory=lambda: calls.append('rmux') or _FakeBackend('rmux'),
        route_approval_reader=lambda: RmuxRouteApproval(True, 'approval-report.md#rmux-route'),
        rmux_availability_reader=lambda: RmuxAvailability(True),
        capability_reader=lambda: RmuxCapabilityStatus(True, 'capability.yaml'),
    )

    backend = selection.get_backend('rmux')
    result = selection.select_backend('rmux')

    assert backend.name == 'rmux'
    assert result['backend_impl'] == 'rmux'
    assert result['route_approval_ref'] == 'approval-report.md#rmux-route'
    assert calls == ['rmux']


def test_terminal_layout_service_delegates_to_runtime_layout() -> None:
    backend = _FakeBackend('tmux')
    captured: dict[str, object] = {}

    def fake_create_tmux_auto_layout(providers, **kwargs):
        captured['providers'] = providers
        captured.update(kwargs)

        class _Result:
            panes = {'a1': '%root'}

        return _Result()

    original = backend_selection_module.create_tmux_auto_layout
    backend_selection_module.create_tmux_auto_layout = fake_create_tmux_auto_layout
    service = TerminalLayoutService(
        tmux_backend_factory=lambda: backend,
        detached_session_name_fn=lambda **kwargs: 'ccb-demo-1',
        os_getpid_fn=lambda: 123,
        time_fn=lambda: 5.0,
        env={'TMUX': '/tmp/tmux'},
    )
    try:
        result = service.create_auto_layout(['a1'], cwd='/tmp/demo')
    finally:
        backend_selection_module.create_tmux_auto_layout = original

    assert result.panes == {'a1': '%root'}
    assert captured['providers'] == ['a1']
    assert captured['backend'] is backend
    assert captured['detached_session_name'] == 'ccb-demo-1'
    assert captured['inside_tmux'] is True
