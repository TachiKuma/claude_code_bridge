from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
README = REPO_ROOT / 'README.md'
SUPPORT_CONTRACT = (
    REPO_ROOT
    / 'docs'
    / 'plantree'
    / 'plans'
    / 'windows-rmux-native-backend'
    / 'topics'
    / 'rmux-packaging-support-contract.md'
)
INSTALL_RUNBOOK = SUPPORT_CONTRACT.with_name('rmux-user-install-runbook.md')
DIAGNOSTICS_CONTRACT = REPO_ROOT / 'docs' / 'ccbd-diagnostics-contract.md'


def test_docs_use_consistent_rmux_beta_install_entry_and_no_native_windows_npm() -> None:
    readme = README.read_text(encoding='utf-8')
    support = SUPPORT_CONTRACT.read_text(encoding='utf-8')
    runbook = INSTALL_RUNBOOK.read_text(encoding='utf-8')
    package = json.loads((REPO_ROOT / 'package.json').read_text(encoding='utf-8'))

    assert 'Native Windows Rmux is a beta opt-in route' in readme
    assert '`support_tier`: `beta`' in support
    assert '`install_entry`: `install_ps1`' in support
    assert '`windows_npm_enabled`: `false`' in support
    assert 'Native Windows Rmux is not installed through npm yet' in runbook
    assert 'win32' not in package.get('os', [])


def test_docs_and_diagnostics_contract_list_required_projection_fields() -> None:
    combined = '\n'.join(
        path.read_text(encoding='utf-8')
        for path in (README, SUPPORT_CONTRACT, INSTALL_RUNBOOK, DIAGNOSTICS_CONTRACT)
    )
    for field in (
        'rmux_support_tier',
        'rmux_version',
        'rmux_capability_status',
        'rmux_validation_ref',
        'windows_install_entry',
        'windows_npm_enabled',
        'windows_install_ps1_rmux_check',
        'rmux_fallback_guidance',
    ):
        assert field in combined


def test_docs_include_required_troubleshooting_categories() -> None:
    runbook = INSTALL_RUNBOOK.read_text(encoding='utf-8')

    for phrase in (
        'Route approval missing or rejected',
        'Capability partial or blocking',
        'Rmux missing',
        'Provider auth failure',
        'Validation incomplete',
        'Fallback',
    ):
        assert phrase in runbook
