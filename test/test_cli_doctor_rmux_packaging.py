from __future__ import annotations

from collections import defaultdict

from cli.render_runtime.ops_views_doctor import render_doctor


def test_render_doctor_includes_rmux_packaging_support_fields() -> None:
    payload = {
        'project': 'C:/repo',
        'project_id': 'demo',
        'installation': {},
        'entrypoint': {},
        'runtime': {},
        'requirements': {},
        'backend_selection': {},
        'rmux_packaging_support': {
            'support_tier': 'beta',
            'rmux_version': 'rmux 0.9.0',
            'rmux_capability_status': 'ok',
            'validation_ref': 'artifacts/rmux-windows-validation/rmux_windows_validation_report.json',
            'install_entry': 'install_ps1',
            'windows_npm_enabled': False,
            'install_ps1_rmux_check': 'warn',
            'fallback_guidance': 'Use install.ps1/source on native Windows for rmux beta opt-in.',
        },
        'ccbd': defaultdict(lambda: None),
        'agents': [],
    }

    lines = render_doctor(payload)

    assert 'rmux_support_tier: beta' in lines
    assert 'rmux_version: rmux 0.9.0' in lines
    assert 'rmux_capability_status: ok' in lines
    assert 'rmux_validation_ref: artifacts/rmux-windows-validation/rmux_windows_validation_report.json' in lines
    assert 'windows_install_entry: install_ps1' in lines
    assert 'windows_npm_enabled: False' in lines
    assert 'windows_install_ps1_rmux_check: warn' in lines
    assert any(line.startswith('rmux_fallback_guidance: Use install.ps1/source') for line in lines)
