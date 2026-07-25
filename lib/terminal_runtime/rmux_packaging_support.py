from __future__ import annotations

import json
import subprocess
from pathlib import Path
from shutil import which
from typing import Any, Literal, Mapping, TypedDict

from .backend_resolver import default_rmux_capability_reader, default_route_approval_reader


SupportTier = Literal['blocked', 'experimental', 'beta', 'supported']
InstallEntry = Literal['npm', 'install_ps1', 'source', 'diagnostic_only']
InstallPs1RmuxCheck = Literal['detect_only', 'warn', 'fail_fast']
RmuxPrerequisiteStatus = Literal['missing', 'partial', 'ok', 'unknown']
ValidationStatus = Literal['pass', 'incomplete', 'failed', 'missing']


class RmuxPackagingSupport(TypedDict):
    support_tier: SupportTier
    install_entry: InstallEntry
    windows_npm_enabled: bool
    install_ps1_rmux_check: InstallPs1RmuxCheck
    rmux_prerequisite_status: RmuxPrerequisiteStatus
    selection_scope: Literal['subset', 'full', 'none']
    selected_cases_status: ValidationStatus
    full_matrix_status: ValidationStatus
    true_host_core_rows_observed: bool
    validation_ref: str | None
    route_approval_ref: str | None
    capability_report_ref: str | None
    local_install_ref: str | None
    package_gate_ref: str | None
    docs_consistency_ref: str | None
    rmux_version: str | None
    rmux_capability_status: Literal['ok', 'blocking_gap', 'unknown']
    npm_no_change_rationale: str | None
    fallback_guidance: str


def rmux_packaging_support_summary(project_root: str | Path) -> RmuxPackagingSupport:
    root = _repo_root(project_root)
    if not _has_repo_evidence(root):
        return _packaged_projection()
    route = default_route_approval_reader(root)
    capability = default_rmux_capability_reader(root)
    validation_ref = _default_validation_report(root)
    validation = _load_validation_report(root / validation_ref) if validation_ref is not None else {}
    prerequisite_status, rmux_version = _rmux_prerequisite()
    local_install_ref = _local_install_ref(root)
    package_gate_ref = _package_gate_ref(root)
    docs_consistency_ref = _docs_consistency_ref(root)
    selected_cases_status = _validation_status(validation.get('selected_cases_status'))
    full_matrix_status = _validation_status(validation.get('full_matrix_status'))
    selection_scope = _selection_scope(validation)
    true_host_observed = _true_host_core_rows_observed(validation)
    package_os = _package_os(root / 'package.json')
    support_tier = _support_tier(
        route_approved=route.approved,
        capability_ok=capability.satisfied,
        selection_scope=selection_scope,
        selected_cases_status=selected_cases_status,
        full_matrix_status=full_matrix_status,
        true_host_core_rows_observed=true_host_observed,
        local_install_ref=local_install_ref,
        docs_consistency_ref=docs_consistency_ref,
    )
    windows_npm_enabled = (
        support_tier in {'beta', 'supported'}
        and package_gate_ref is not None
        and 'win32' in package_os
    )
    install_entry: InstallEntry = 'install_ps1' if support_tier in {'beta', 'supported'} else 'diagnostic_only'
    return {
        'support_tier': support_tier,
        'install_entry': install_entry,
        'windows_npm_enabled': windows_npm_enabled,
        'install_ps1_rmux_check': 'warn' if install_entry == 'install_ps1' else 'detect_only',
        'rmux_prerequisite_status': prerequisite_status,
        'selection_scope': selection_scope,
        'selected_cases_status': selected_cases_status,
        'full_matrix_status': full_matrix_status,
        'true_host_core_rows_observed': true_host_observed,
        'validation_ref': validation_ref,
        'route_approval_ref': route.ref,
        'capability_report_ref': capability.ref,
        'local_install_ref': local_install_ref,
        'package_gate_ref': package_gate_ref,
        'docs_consistency_ref': docs_consistency_ref,
        'rmux_version': rmux_version,
        'rmux_capability_status': 'ok' if capability.satisfied else 'blocking_gap',
        'npm_no_change_rationale': None if windows_npm_enabled else _npm_no_change_rationale(package_gate_ref, package_os),
        'fallback_guidance': _fallback_guidance(support_tier, windows_npm_enabled),
    }


def _repo_root(project_root: str | Path) -> Path:
    current = Path(project_root).expanduser().resolve()
    for path in (current, *current.parents):
        if (path / '.codestable').exists() or (path / '.git').exists():
            return path
    return current


def _has_repo_evidence(root: Path) -> bool:
    return (
        root / '.codestable' / 'features' / '2026-07-19-rmux-route-approval'
    ).exists() and (
        root / 'artifacts' / 'rmux-windows-validation' / 'rmux_windows_validation_report.json'
    ).exists()


def _packaged_projection() -> RmuxPackagingSupport:
    path = Path(__file__).with_name('rmux_packaging_support_projection.json')
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        data = {}
    prerequisite_status, rmux_version = _rmux_prerequisite()
    return _projection_with_defaults(data, rmux_prerequisite_status=prerequisite_status, rmux_version=rmux_version)


def _projection_with_defaults(
    data: Mapping[str, Any],
    *,
    rmux_prerequisite_status: RmuxPrerequisiteStatus,
    rmux_version: str | None,
) -> RmuxPackagingSupport:
    support_tier = str(data.get('support_tier') or 'experimental').strip().lower()
    install_entry = str(data.get('install_entry') or 'diagnostic_only').strip().lower()
    install_ps1_rmux_check = str(data.get('install_ps1_rmux_check') or 'detect_only').strip().lower()
    selection_scope = str(data.get('selection_scope') or 'none').strip().lower()
    return {
        'support_tier': support_tier if support_tier in {'blocked', 'experimental', 'beta', 'supported'} else 'experimental',  # type: ignore[typeddict-item]
        'install_entry': install_entry if install_entry in {'npm', 'install_ps1', 'source', 'diagnostic_only'} else 'diagnostic_only',  # type: ignore[typeddict-item]
        'windows_npm_enabled': bool(data.get('windows_npm_enabled') is True),
        'install_ps1_rmux_check': install_ps1_rmux_check if install_ps1_rmux_check in {'detect_only', 'warn', 'fail_fast'} else 'detect_only',  # type: ignore[typeddict-item]
        'rmux_prerequisite_status': rmux_prerequisite_status,
        'selection_scope': selection_scope if selection_scope in {'subset', 'full'} else 'none',  # type: ignore[typeddict-item]
        'selected_cases_status': _validation_status(data.get('selected_cases_status')),
        'full_matrix_status': _validation_status(data.get('full_matrix_status')),
        'true_host_core_rows_observed': bool(data.get('true_host_core_rows_observed') is True),
        'validation_ref': _optional_text(data.get('validation_ref')),
        'route_approval_ref': _optional_text(data.get('route_approval_ref')),
        'capability_report_ref': _optional_text(data.get('capability_report_ref')),
        'local_install_ref': _optional_text(data.get('local_install_ref')),
        'package_gate_ref': _optional_text(data.get('package_gate_ref')),
        'docs_consistency_ref': _optional_text(data.get('docs_consistency_ref')),
        'rmux_version': rmux_version,
        'rmux_capability_status': 'ok' if str(data.get('rmux_capability_status') or '').strip().lower() == 'ok' else 'unknown',
        'npm_no_change_rationale': _optional_text(data.get('npm_no_change_rationale')),
        'fallback_guidance': _optional_text(data.get('fallback_guidance')) or _fallback_guidance('experimental', False),
    }


def _optional_text(value: object) -> str | None:
    text = str(value or '').strip()
    return text or None


def _default_validation_report(root: Path) -> str | None:
    path = root / 'artifacts' / 'rmux-windows-validation' / 'rmux_windows_validation_report.json'
    if path.exists():
        return 'artifacts/rmux-windows-validation/rmux_windows_validation_report.json'
    return None


def _load_validation_report(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _validation_status(value: object) -> ValidationStatus:
    text = str(value or '').strip().lower()
    return text if text in {'pass', 'incomplete', 'failed'} else 'missing'  # type: ignore[return-value]


def _selection_scope(report: Mapping[str, Any]) -> Literal['subset', 'full', 'none']:
    text = str(report.get('selection_scope') or '').strip().lower()
    if text in {'subset', 'full'}:
        return text  # type: ignore[return-value]
    for row in _rows(report):
        row_scope = str(row.get('selection_scope') or '').strip().lower()
        if row_scope == 'full':
            return 'full'
        if row_scope == 'subset':
            return 'subset'
    return 'none'


def _true_host_core_rows_observed(report: Mapping[str, Any]) -> bool:
    rows = [row for row in _rows(report) if str(row.get('lane') or '').strip().lower() == 'windows_true_host']
    if not rows:
        return False
    observed = [row for row in rows if str(row.get('classification') or '').strip().lower() in {'pass', 'valid_non_success'}]
    if not observed:
        return False
    return all(
        str(row.get('host_kind') or '').strip().lower() == 'native_windows'
        and str(row.get('control_plane') or '').strip().lower() == 'ccbd'
        and str(row.get('backend_impl') or '').strip().lower() == 'rmux'
        and row.get('probe_bypass') is False
        for row in observed
    )


def _rows(report: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw_rows = report.get('rows')
    if not isinstance(raw_rows, list):
        raw_rows = report.get('manifest')
    return [dict(item) for item in raw_rows or () if isinstance(item, dict)]


def _package_os(path: Path) -> set[str]:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return set()
    raw = data.get('os') if isinstance(data, dict) else None
    return {str(item).strip().lower() for item in raw or () if str(item).strip()}


def _package_gate_ref(root: Path) -> str | None:
    candidates = (
        root / '.codestable' / 'features' / '2026-07-20-rmux-packaging-docs-contracts' / 'npm-gate-results.json',
        root / 'artifacts' / 'rmux-packaging-docs-contracts' / 'npm-gate-results.json',
    )
    for path in candidates:
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict) and str(data.get('status') or '').strip().lower() == 'pass':
            return _relative_ref(root, path)
    return None


def _local_install_ref(root: Path) -> str | None:
    report = root / 'artifacts' / 'rmux-packaging-docs-contracts' / 'local-install-smoke.json'
    if not report.exists():
        return None
    try:
        data = json.loads(report.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return None
    if isinstance(data, dict) and str(data.get('status') or '').strip().lower() == 'pass':
        return _relative_ref(root, report)
    return None


def _docs_consistency_ref(root: Path) -> str | None:
    report = root / 'artifacts' / 'rmux-packaging-docs-contracts' / 'docs-consistency.json'
    if report.exists():
        try:
            data = json.loads(report.read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError):
            return None
        if isinstance(data, dict) and data.get('ok') is True:
            return _relative_ref(root, report)
    return None


def _support_tier(
    *,
    route_approved: bool,
    capability_ok: bool,
    selection_scope: str,
    selected_cases_status: str,
    full_matrix_status: str,
    true_host_core_rows_observed: bool,
    local_install_ref: str | None,
    docs_consistency_ref: str | None,
) -> SupportTier:
    if not route_approved:
        return 'experimental'
    if not capability_ok:
        return 'blocked'
    full_pass = (
        selection_scope == 'full'
        and full_matrix_status == 'pass'
        and true_host_core_rows_observed
    )
    if full_pass and docs_consistency_ref is not None and local_install_ref is not None:
        return 'supported'
    if full_pass or selected_cases_status == 'pass':
        return 'beta'
    return 'experimental'


def _rmux_prerequisite() -> tuple[RmuxPrerequisiteStatus, str | None]:
    command = which('rmux') or which('psmux')
    if command is None:
        return 'missing', None
    try:
        completed = subprocess.run(
            [command, '-V'],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return 'partial', None
    version = (completed.stdout or completed.stderr or '').strip().splitlines()
    if completed.returncode == 0:
        return 'ok', version[0] if version else None
    return 'partial', version[0] if version else None


def _npm_no_change_rationale(package_gate_ref: str | None, package_os: set[str]) -> str:
    if 'win32' not in package_os:
        return 'package.json.os does not include win32; native Windows Rmux uses install.ps1/source until npm gate passes.'
    if package_gate_ref is None:
        return 'Windows npm gate evidence is missing; win32 npm entry remains disabled.'
    return 'Windows npm entry is not enabled by current package projection.'


def _fallback_guidance(support_tier: SupportTier, windows_npm_enabled: bool) -> str:
    if support_tier in {'blocked', 'experimental'}:
        return 'Use the existing Linux/macOS/WSL tmux route and run ccb doctor for rmux diagnostics.'
    if not windows_npm_enabled:
        return 'Use install.ps1/source on native Windows for rmux beta opt-in; npm remains Linux/macOS only.'
    return 'Use the explicit Windows rmux opt-in path; keep tmux/WSL available as fallback.'


def _relative_ref(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


__all__ = ['RmuxPackagingSupport', 'rmux_packaging_support_summary']
