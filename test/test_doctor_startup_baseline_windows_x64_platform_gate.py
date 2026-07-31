from __future__ import annotations

from collections import defaultdict

from cli.render_runtime.ops_views_doctor import render_doctor


def test_doctor_startup_baseline_projection_comes_from_windows_x64_gate() -> None:
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
            'failure_reason': 'unknown',
            'detail_reason': 'source-branch-blocked',
            'diagnostic': 'Missing v8.5.2 source or implementation branch evidence.',
        },
        'ccbd': defaultdict(lambda: None),
        'agents': [],
    }

    lines = render_doctor(payload)

    assert 'startup_baseline_failure_reason: unknown' in lines
    assert 'startup_baseline_detail_reason: source-branch-blocked' in lines


def test_doctor_startup_baseline_projection_does_not_require_ccbd_payload_fields() -> None:
    ccbd = defaultdict(lambda: None)
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
            'failure_reason': 'not-x64',
            'detail_reason': 'node-not-x64',
            'diagnostic': 'Node is not x64.',
        },
        'ccbd': ccbd,
        'agents': [],
    }

    render_doctor(payload)

    assert 'startup_baseline_failure_reason' not in ccbd
    assert 'startup_baseline_detail_reason' not in ccbd
    assert 'readiness_timeline' not in ccbd
