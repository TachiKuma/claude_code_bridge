from __future__ import annotations

import json
from pathlib import Path

import terminal_runtime.rmux_packaging_support as support


REPO_ROOT = Path(__file__).resolve().parents[1]


def _write_route(root: Path, *, approved: bool = True, blocking_gaps_count: int = 0) -> None:
    unit = root / '.codestable' / 'features' / '2026-07-19-rmux-route-approval'
    unit.mkdir(parents=True, exist_ok=True)
    unit.joinpath('approval-report.md').write_text(
        f'approvals:\n  rmux-route: {"approved" if approved else "rejected"}\n',
        encoding='utf-8',
    )
    unit.joinpath('rmux-route-decision-summary.yaml').write_text(
        f"""decision_status: {"approved" if approved else "rejected"}
capability_report: .codestable/features/2026-07-19-rmux-route-approval/rmux-capability-report.json
report_facts:
  blocking_gaps_count: {blocking_gaps_count}
parent_handoff:
  route_approved: {"true" if approved else "false"}
""",
        encoding='utf-8',
    )


def _write_validation(root: Path, *, selection_scope: str, full_status: str, selected_status: str) -> None:
    path = root / 'artifacts' / 'rmux-windows-validation' / 'rmux_windows_validation_report.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                'selection_scope': selection_scope,
                'selected_cases_status': selected_status,
                'full_matrix_status': full_status,
                'rows': [
                    {
                        'lane': 'windows_true_host',
                        'classification': 'pass',
                        'host_kind': 'native_windows',
                        'control_plane': 'ccbd',
                        'backend_impl': 'rmux',
                        'probe_bypass': False,
                        'selection_scope': selection_scope,
                    }
                ],
            }
        ),
        encoding='utf-8',
    )


def _write_package(root: Path, *, os_values: list[str]) -> None:
    root.joinpath('package.json').write_text(json.dumps({'os': os_values}), encoding='utf-8')


def test_support_projection_fails_closed_to_beta_without_docs_or_npm_gate(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _write_route(tmp_path)
    _write_validation(tmp_path, selection_scope='full', full_status='pass', selected_status='pass')
    _write_package(tmp_path, os_values=['linux', 'darwin'])
    monkeypatch.setattr(support, '_rmux_prerequisite', lambda: ('ok', 'rmux 0.9.0'))

    projection = support.rmux_packaging_support_summary(tmp_path)

    assert projection['support_tier'] == 'beta'
    assert projection['install_entry'] == 'install_ps1'
    assert projection['windows_npm_enabled'] is False
    assert projection['install_ps1_rmux_check'] == 'warn'
    assert projection['full_matrix_status'] == 'pass'
    assert projection['true_host_core_rows_observed'] is True
    assert projection['validation_ref'] == 'artifacts/rmux-windows-validation/rmux_windows_validation_report.json'
    assert 'package.json.os does not include win32' in projection['npm_no_change_rationale']


def test_support_projection_blocks_on_capability_gap(tmp_path: Path, monkeypatch) -> None:
    _write_route(tmp_path, approved=True, blocking_gaps_count=2)
    _write_validation(tmp_path, selection_scope='full', full_status='pass', selected_status='pass')
    _write_package(tmp_path, os_values=['linux', 'darwin'])
    monkeypatch.setattr(support, '_rmux_prerequisite', lambda: ('missing', None))

    projection = support.rmux_packaging_support_summary(tmp_path)

    assert projection['support_tier'] == 'blocked'
    assert projection['install_entry'] == 'diagnostic_only'
    assert projection['rmux_capability_status'] == 'blocking_gap'
    assert projection['rmux_prerequisite_status'] == 'missing'


def test_support_projection_never_supported_for_subset_validation(tmp_path: Path, monkeypatch) -> None:
    _write_route(tmp_path)
    _write_validation(tmp_path, selection_scope='subset', full_status='incomplete', selected_status='pass')
    _write_package(tmp_path, os_values=['linux', 'darwin', 'win32'])
    monkeypatch.setattr(support, '_rmux_prerequisite', lambda: ('ok', 'rmux 0.9.0'))

    projection = support.rmux_packaging_support_summary(tmp_path)

    assert projection['support_tier'] == 'beta'
    assert projection['full_matrix_status'] == 'incomplete'
    assert projection['selection_scope'] == 'subset'
    assert projection['windows_npm_enabled'] is False


def test_support_projection_can_reach_supported_only_with_docs_consistency(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _write_route(tmp_path)
    _write_validation(tmp_path, selection_scope='full', full_status='pass', selected_status='pass')
    _write_package(tmp_path, os_values=['linux', 'darwin'])
    docs_report = tmp_path / 'artifacts' / 'rmux-packaging-docs-contracts' / 'docs-consistency.json'
    docs_report.parent.mkdir(parents=True, exist_ok=True)
    docs_report.write_text(json.dumps({'ok': True}), encoding='utf-8')
    local_install = tmp_path / 'artifacts' / 'rmux-packaging-docs-contracts' / 'local-install-smoke.json'
    local_install.write_text(json.dumps({'status': 'pass'}), encoding='utf-8')
    monkeypatch.setattr(support, '_rmux_prerequisite', lambda: ('ok', 'rmux 0.9.0'))

    projection = support.rmux_packaging_support_summary(tmp_path)

    assert projection['support_tier'] == 'supported'
    assert projection['windows_npm_enabled'] is False
    assert projection['docs_consistency_ref'] == 'artifacts/rmux-packaging-docs-contracts/docs-consistency.json'
    assert projection['local_install_ref'] == 'artifacts/rmux-packaging-docs-contracts/local-install-smoke.json'


def test_support_projection_stays_beta_without_local_install_smoke(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _write_route(tmp_path)
    _write_validation(tmp_path, selection_scope='full', full_status='pass', selected_status='pass')
    _write_package(tmp_path, os_values=['linux', 'darwin'])
    docs_report = tmp_path / 'artifacts' / 'rmux-packaging-docs-contracts' / 'docs-consistency.json'
    docs_report.parent.mkdir(parents=True, exist_ok=True)
    docs_report.write_text(json.dumps({'ok': True}), encoding='utf-8')
    monkeypatch.setattr(support, '_rmux_prerequisite', lambda: ('ok', 'rmux 0.9.0'))

    projection = support.rmux_packaging_support_summary(tmp_path)

    assert projection['support_tier'] == 'beta'
    assert projection['docs_consistency_ref'] == 'artifacts/rmux-packaging-docs-contracts/docs-consistency.json'
    assert projection['local_install_ref'] is None


def test_support_projection_uses_packaged_contract_without_project_evidence(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(support, '_rmux_prerequisite', lambda: ('ok', 'rmux 0.9.0'))

    projection = support.rmux_packaging_support_summary(tmp_path)

    assert projection['support_tier'] == 'beta'
    assert projection['install_entry'] == 'install_ps1'
    assert projection['windows_npm_enabled'] is False
    assert projection['rmux_prerequisite_status'] == 'ok'


def test_packaged_projection_matches_repo_evidence_for_stable_fields(monkeypatch) -> None:
    monkeypatch.setattr(support, '_rmux_prerequisite', lambda: ('ok', 'rmux 0.9.0'))
    packaged = json.loads(
        (REPO_ROOT / 'lib' / 'terminal_runtime' / 'rmux_packaging_support_projection.json').read_text(
            encoding='utf-8'
        )
    )
    live = support.rmux_packaging_support_summary(REPO_ROOT)
    stable_fields = [
        'support_tier',
        'install_entry',
        'windows_npm_enabled',
        'install_ps1_rmux_check',
        'selection_scope',
        'selected_cases_status',
        'full_matrix_status',
        'true_host_core_rows_observed',
        'validation_ref',
        'route_approval_ref',
        'capability_report_ref',
        'local_install_ref',
        'package_gate_ref',
        'docs_consistency_ref',
        'rmux_capability_status',
        'npm_no_change_rationale',
        'fallback_guidance',
    ]

    assert {field: packaged.get(field) for field in stable_fields} == {
        field: live[field] for field in stable_fields
    }
