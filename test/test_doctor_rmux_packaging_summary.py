from __future__ import annotations

from pathlib import Path

from cli.context import CliContextBuilder
from cli.models import ParsedDoctorCommand
import cli.services.doctor as doctor_module
from cli.services.doctor import doctor_summary


def test_doctor_summary_uses_install_root_for_rmux_packaging_projection(
    tmp_path: Path,
    monkeypatch,
) -> None:
    project_root = tmp_path / 'user-project'
    install_root = tmp_path / 'install-root'
    (project_root / '.ccb').mkdir(parents=True, exist_ok=True)
    (project_root / '.ccb' / 'ccb.config').write_text('demo:codex\n', encoding='utf-8')
    install_root.mkdir()
    context = CliContextBuilder().build(
        ParsedDoctorCommand(project=None, bundle=False),
        cwd=project_root,
        bootstrap_if_missing=False,
    )
    seen: list[object] = []

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

    def fake_projection(root):
        seen.append(root)
        return {'support_tier': 'beta'}

    monkeypatch.setattr(doctor_module, 'rmux_packaging_support_summary', fake_projection)

    payload = doctor_summary(context)

    assert seen == [str(install_root)]
    assert payload['rmux_packaging_support'] == {'support_tier': 'beta'}
