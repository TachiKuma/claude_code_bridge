from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from cli.context import CliContextBuilder
from cli.models import ParsedDoctorCommand
import cli.services.doctor as doctor_module
import terminal_runtime.windows_x64_platform_gate as gate_module
from cli.services.doctor import doctor_summary
from cli.render_runtime.ops_views_doctor import render_doctor


def test_doctor_summary_includes_windows_x64_platform_gate(tmp_path: Path, monkeypatch) -> None:
    project_root = tmp_path / 'project'
    install_root = tmp_path / 'install'
    (project_root / '.ccb').mkdir(parents=True)
    (project_root / '.ccb' / 'ccb.config').write_text('demo:codex\n', encoding='utf-8')
    install_root.mkdir()
    context = CliContextBuilder().build(
        ParsedDoctorCommand(project=None, bundle=False),
        cwd=project_root,
        bootstrap_if_missing=False,
    )
    seen: list[object] = []
    gate = {
        'supported': False,
        'failure_reason': 'unknown',
        'detail_reason': 'ccb-version-mismatch',
        'diagnostic': 'CCB is not strict v8.5.2.',
    }

    monkeypatch.setattr(doctor_module, 'installation_summary', lambda: {'path': str(install_root)})
    monkeypatch.setattr(doctor_module, 'doctor_stores', lambda _context: {})
    monkeypatch.setattr(doctor_module, 'ping_local_state', lambda _context: type('Local', (), {'mount_state': 'unmounted'})())
    monkeypatch.setattr(doctor_module, 'load_project_config', lambda _root: type('Loaded', (), {'config': type('Config', (), {'runtime_mux': type('RuntimeMux', (), {'backend': None, 'explicit_backend': False})()})(), 'source_kind': None})())
    monkeypatch.setattr(doctor_module, 'validate_config_context', lambda _context: type('Validation', (), {'to_record': lambda self: {}})())
    monkeypatch.setattr(doctor_module, 'build_default_provider_catalog', lambda: {})
    monkeypatch.setattr(doctor_module, 'build_default_execution_registry', lambda: {})
    monkeypatch.setattr(doctor_module, 'agent_summaries', lambda *args, **kwargs: [])
    monkeypatch.setattr(doctor_module, 'backend_selection_summary', lambda _context: {})
    monkeypatch.setattr(doctor_module, 'runtime_identity_summary', lambda *args, **kwargs: {})
    monkeypatch.setattr(doctor_module, 'requirements_summary', lambda: {})
    monkeypatch.setattr(doctor_module, 'entrypoint_summary', lambda **kwargs: {})
    monkeypatch.setattr(doctor_module, 'ccbd_summary', lambda **kwargs: {})
    monkeypatch.setattr(doctor_module, 'rmux_packaging_support_summary', lambda _root: {})

    def fake_gate(root, *, installation=None):
        seen.append((root, installation))
        return gate

    monkeypatch.setattr(doctor_module, 'windows_x64_platform_gate_summary', fake_gate)

    payload = doctor_summary(context)

    assert seen == [(str(install_root), {'path': str(install_root)})]
    assert payload['windows_x64_platform_gate'] == gate


def test_doctor_summary_uses_windows_x64_platform_gate_installation_evidence(tmp_path: Path, monkeypatch) -> None:
    project_root = tmp_path / 'project'
    install_root = tmp_path / 'install'
    (project_root / '.ccb').mkdir(parents=True)
    (project_root / '.ccb' / 'ccb.config').write_text('demo:codex\n', encoding='utf-8')
    install_root.mkdir()
    (install_root / 'package.json').write_text('{"version": "8.5.2"}', encoding='utf-8')
    (install_root / 'VERSION').write_text('8.5.2', encoding='utf-8')
    context = CliContextBuilder().build(
        ParsedDoctorCommand(project=None, bundle=False),
        cwd=project_root,
        bootstrap_if_missing=False,
    )

    monkeypatch.setattr(gate_module, '_node_platform_arch', lambda: ('win32', 'x64'))
    monkeypatch.setattr(gate_module.platform, 'machine', lambda: 'AMD64')
    monkeypatch.setattr(gate_module, '_runtime_python_bitness', lambda: '64bit')
    monkeypatch.setattr(
        doctor_module,
        'installation_summary',
        lambda: {
            'path': str(install_root),
            'version': '8.5.2',
            'ccb_source_ref': 'refs/tags/v8.5.2',
            'ccb_branch_ref': 'feature/windows-herdr',
            'herdr_arch': 'x64',
            'helper_arch': {'ccb-rs-helper': 'x64', 'ccb-agent-sidebar': 'x64'},
        },
    )
    monkeypatch.setattr(doctor_module, 'doctor_stores', lambda _context: {})
    monkeypatch.setattr(doctor_module, 'ping_local_state', lambda _context: type('Local', (), {'mount_state': 'unmounted'})())
    monkeypatch.setattr(doctor_module, 'load_project_config', lambda _root: type('Loaded', (), {'config': type('Config', (), {'runtime_mux': type('RuntimeMux', (), {'backend': None, 'explicit_backend': False})()})(), 'source_kind': None})())
    monkeypatch.setattr(doctor_module, 'validate_config_context', lambda _context: type('Validation', (), {'to_record': lambda self: {}})())
    monkeypatch.setattr(doctor_module, 'build_default_provider_catalog', lambda: {})
    monkeypatch.setattr(doctor_module, 'build_default_execution_registry', lambda: {})
    monkeypatch.setattr(doctor_module, 'agent_summaries', lambda *args, **kwargs: [])
    monkeypatch.setattr(doctor_module, 'backend_selection_summary', lambda _context: {})
    monkeypatch.setattr(doctor_module, 'runtime_identity_summary', lambda *args, **kwargs: {})
    monkeypatch.setattr(doctor_module, 'requirements_summary', lambda: {})
    monkeypatch.setattr(doctor_module, 'entrypoint_summary', lambda **kwargs: {})
    monkeypatch.setattr(doctor_module, 'ccbd_summary', lambda **kwargs: {})
    monkeypatch.setattr(doctor_module, 'rmux_packaging_support_summary', lambda _root: {})

    payload = doctor_summary(context)

    assert payload['windows_x64_platform_gate']['supported'] is True
    assert payload['windows_x64_platform_gate']['ccb_source_status'] == 'strict-v8.5.2'


def test_render_doctor_includes_windows_x64_platform_gate_fields() -> None:
    payload = {
        'project': 'C:/repo',
        'project_id': 'demo',
        'installation': {},
        'entrypoint': {},
        'runtime': {},
        'requirements': {},
        'backend_selection': {},
        'rmux_packaging_support': {},
        'windows_x64_platform_gate': {
            'supported': False,
            'failure_reason': 'unknown',
            'detail_reason': 'ccb-version-mismatch',
            'diagnostic': 'Expected CCB 8.5.2, detected 8.2.1.',
            'expected_ccb_version': '8.5.2',
            'detected_ccb_version': '8.2.1',
            'os_platform': 'win32',
            'cpu_arch': 'x64',
            'node_arch': 'x64',
            'python_bitness': '64bit',
        },
        'ccbd': defaultdict(lambda: None),
        'agents': [],
    }

    lines = render_doctor(payload)

    assert 'windows_x64_supported: False' in lines
    assert 'windows_x64_failure_reason: unknown' in lines
    assert 'windows_x64_detail_reason: ccb-version-mismatch' in lines
    assert 'windows_x64_diagnostic: Expected CCB 8.5.2, detected 8.2.1.' in lines
    assert 'ccb_expected_version: 8.5.2' in lines
    assert 'ccb_detected_version: 8.2.1' in lines
