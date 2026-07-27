from __future__ import annotations

import json

from ccbd.services.project_namespace_pane import ProjectNamespacePaneRecord
from ccbd.services.project_namespace_runtime.sidebar_settings_evidence import (
    classify_sidebar_settings_pane_evidence,
    main,
)


def _pane(**overrides) -> ProjectNamespacePaneRecord:
    values = {
        'pane_id': '%1',
        'session_name': 'ccb-demo',
        'window_name': 'main',
        'role': 'sidebar',
        'sidebar_helper_id': 'sha256:current',
        'project_id': 'project-1',
        'managed_by': 'ccbd',
        'alive': True,
    }
    values.update(overrides)
    return ProjectNamespacePaneRecord(**values)


def test_sidebar_settings_pane_evidence_passes_when_identity_matches() -> None:
    result = classify_sidebar_settings_pane_evidence(
        _pane(),
        expected_helper_id='sha256:current',
        target_pane_id='%1',
    )

    assert result['status'] == 'pass'
    assert result['failure_detail'] is None
    assert result['pane']['role'] == 'sidebar'
    assert result['pane']['sidebar_helper_id'] == 'sha256:current'
    assert result['pane']['expected_helper_id'] == 'sha256:current'


def test_sidebar_settings_pane_evidence_reports_helper_mismatch() -> None:
    result = classify_sidebar_settings_pane_evidence(
        _pane(sidebar_helper_id='sha256:old'),
        expected_helper_id='sha256:current',
        target_pane_id='%1',
    )

    assert result['status'] == 'blocked'
    assert result['failure_kind'] == 'sidebar_helper_mismatch'
    assert 'sha256:old' in str(result['failure_detail'])
    assert 'sha256:current' in str(result['failure_detail'])


def test_sidebar_settings_pane_evidence_reports_missing_role_before_hit_test() -> None:
    result = classify_sidebar_settings_pane_evidence(
        _pane(role=None),
        expected_helper_id='sha256:current',
        target_pane_id='%1',
    )

    assert result['status'] == 'blocked'
    assert result['failure_kind'] == 'pane_role_missing'
    assert result['pane']['role'] is None


def test_sidebar_settings_pane_evidence_reports_non_sidebar_target() -> None:
    result = classify_sidebar_settings_pane_evidence(
        _pane(role='agent'),
        expected_helper_id='sha256:current',
        target_pane_id='%1',
    )

    assert result['status'] == 'blocked'
    assert result['failure_kind'] == 'pane_role_mismatch'
    assert 'agent' in str(result['failure_detail'])


def test_sidebar_settings_pane_evidence_reports_target_mismatch() -> None:
    result = classify_sidebar_settings_pane_evidence(
        _pane(pane_id='%2'),
        expected_helper_id='sha256:current',
        target_pane_id='%1',
    )

    assert result['status'] == 'blocked'
    assert result['failure_kind'] == 'pane_target_mismatch'
    assert '%1' in str(result['failure_detail'])
    assert '%2' in str(result['failure_detail'])


def test_sidebar_settings_pane_evidence_reports_dead_pane_before_hit_test() -> None:
    result = classify_sidebar_settings_pane_evidence(
        _pane(alive=False),
        expected_helper_id='sha256:current',
        target_pane_id='%1',
    )

    assert result['status'] == 'blocked'
    assert result['failure_kind'] == 'pane_not_alive'
    assert result['pane']['alive'] is False


def test_sidebar_settings_pane_evidence_cli_writes_classification(tmp_path) -> None:
    pane_path = tmp_path / 'pane.json'
    output_path = tmp_path / 'result.json'
    pane_path.write_text(
        json.dumps(
            {
                'pane_id': '%1',
                'role': 'sidebar',
                'sidebar_helper_id': 'sha256:old',
                'alive': True,
            }
        ),
        encoding='utf-8',
    )

    exit_code = main(
        [
            '--pane-json',
            str(pane_path),
            '--expected-helper-id',
            'sha256:current',
            '--target-pane-id',
            '%1',
            '--output',
            str(output_path),
        ]
    )

    result = json.loads(output_path.read_text(encoding='utf-8'))
    assert exit_code == 0
    assert result['status'] == 'blocked'
    assert result['failure_kind'] == 'sidebar_helper_mismatch'
