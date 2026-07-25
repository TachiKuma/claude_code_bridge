from __future__ import annotations

import json
from pathlib import Path
import tarfile

from cli.context import CliContextBuilder
from cli.models import ParsedDoctorCommand
import cli.services.diagnostics_runtime.bundle as bundle_runtime
from cli.services.diagnostics import export_diagnostic_bundle


def _read_tar_json(bundle_path: Path, member_name: str) -> dict:
    with tarfile.open(bundle_path, 'r:gz') as archive:
        with archive.extractfile(member_name) as handle:
            assert handle is not None
            return json.loads(handle.read().decode('utf-8'))


def test_diagnostic_bundle_includes_rmux_packaging_projection(
    tmp_path: Path,
    monkeypatch,
) -> None:
    project_root = tmp_path / 'repo-bundle-rmux-packaging'
    (project_root / '.ccb').mkdir(parents=True, exist_ok=True)
    (project_root / '.ccb' / 'ccb.config').write_text('demo:codex\n', encoding='utf-8')
    context = CliContextBuilder().build(
        ParsedDoctorCommand(project=None, bundle=True),
        cwd=project_root,
        bootstrap_if_missing=False,
    )

    monkeypatch.setattr(
        bundle_runtime,
        'doctor_summary',
        lambda _context: {
            'project': str(project_root),
            'project_id': _context.project.project_id,
            'rmux_packaging_support': {
                'support_tier': 'beta',
                'install_entry': 'install_ps1',
                'windows_npm_enabled': False,
                'rmux_validation_ref': 'artifacts/rmux-windows-validation/rmux_windows_validation_report.json',
            },
        },
    )

    summary = export_diagnostic_bundle(context, ParsedDoctorCommand(project=None, bundle=True))
    doctor = _read_tar_json(Path(summary.bundle_path), f'{summary.bundle_id}/generated/doctor.json')

    assert doctor['rmux_packaging_support']['support_tier'] == 'beta'
    assert doctor['rmux_packaging_support']['install_entry'] == 'install_ps1'
    assert doctor['rmux_packaging_support']['windows_npm_enabled'] is False
