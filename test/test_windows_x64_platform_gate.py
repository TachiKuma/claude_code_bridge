from __future__ import annotations

from pathlib import Path

import terminal_runtime.windows_x64_platform_gate as gate_module
from terminal_runtime.windows_x64_platform_gate import build_windows_x64_platform_gate
from terminal_runtime.windows_x64_platform_gate import windows_x64_platform_gate_summary


def test_windows_x64_gate_supports_full_strict_v852_chain() -> None:
    gate = build_windows_x64_platform_gate(
        os_platform='win32',
        cpu_arch='x64',
        node_arch='x64',
        python_bitness='64bit',
        version_sources={'installation': '8.5.2', 'package_json': '8.5.2', 'version_file': '8.5.2'},
        ccb_source_ref='refs/tags/v8.5.2',
        ccb_branch_ref='feature/windows-herdr',
        herdr_arch='x64',
        helper_arch={'ccb-rs-helper': 'x64', 'ccb-agent-sidebar': 'x64'},
    )

    assert gate['platform_ready'] is True
    assert gate['native_helpers_ready'] is True
    assert gate['herdr_executable_ready'] is True
    assert gate['supported'] is True
    assert gate['failure_reason'] is None
    assert gate['detail_reason'] == 'none'
    assert gate['ccb_source_status'] == 'strict-v8.5.2'


def test_windows_x64_summary_uses_installation_admission_and_arch_evidence(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(gate_module, '_node_platform_arch', lambda: ('win32', 'x64'))
    monkeypatch.setattr(gate_module.platform, 'machine', lambda: 'AMD64')
    monkeypatch.setattr(gate_module, '_runtime_python_bitness', lambda: '64bit')
    (tmp_path / 'package.json').write_text('{"version": "8.5.2"}', encoding='utf-8')
    (tmp_path / 'VERSION').write_text('8.5.2', encoding='utf-8')

    gate = windows_x64_platform_gate_summary(
        tmp_path,
        installation={
            'version': '8.5.2',
            'ccb_source_ref': 'refs/tags/v8.5.2',
            'ccb_branch_ref': 'feature/windows-herdr',
            'herdr_arch': 'x64',
            'helper_arch': {'ccb-rs-helper': 'x64', 'ccb-agent-sidebar': 'x64'},
        },
    )

    assert gate['platform_ready'] is True
    assert gate['native_helpers_ready'] is True
    assert gate['herdr_executable_ready'] is True
    assert gate['supported'] is True
    assert gate['failure_reason'] is None


def test_windows_x64_gate_keeps_win32_distinct_from_node_ia32() -> None:
    gate = build_windows_x64_platform_gate(
        os_platform='win32',
        cpu_arch='x64',
        node_arch='ia32',
        python_bitness='64bit',
        version_sources={'package_json': '8.5.2'},
        ccb_source_ref='refs/tags/v8.5.2',
        ccb_branch_ref='feature/windows-herdr',
        herdr_arch='x64',
        helper_arch={'ccb-rs-helper': 'x64', 'ccb-agent-sidebar': 'x64'},
    )

    assert gate['supported'] is False
    assert gate['failure_reason'] == 'not-x64'
    assert gate['detail_reason'] == 'node-not-x64'
    assert 'win32 is the Windows OS name' in gate['diagnostic']


def test_windows_x64_gate_blocks_non_windows_hosts() -> None:
    gate = build_windows_x64_platform_gate(
        os_platform='linux',
        cpu_arch='x64',
        node_arch='x64',
        python_bitness='64bit',
        version_sources={'package_json': '8.5.2'},
        ccb_source_ref='refs/tags/v8.5.2',
        ccb_branch_ref='feature/windows-herdr',
        herdr_arch='x64',
        helper_arch={'ccb-rs-helper': 'x64', 'ccb-agent-sidebar': 'x64'},
    )

    assert gate['supported'] is False
    assert gate['platform_ready'] is False
    assert gate['failure_reason'] == 'not-windows'


def test_windows_x64_gate_blocks_cpu_ia32() -> None:
    gate = build_windows_x64_platform_gate(
        os_platform='win32',
        cpu_arch='ia32',
        node_arch='x64',
        python_bitness='64bit',
        version_sources={'package_json': '8.5.2'},
        ccb_source_ref='refs/tags/v8.5.2',
        ccb_branch_ref='feature/windows-herdr',
        herdr_arch='x64',
        helper_arch={'ccb-rs-helper': 'x64', 'ccb-agent-sidebar': 'x64'},
    )

    assert gate['supported'] is False
    assert gate['platform_ready'] is False
    assert gate['failure_reason'] == 'not-x64'
    assert gate['detail_reason'] == 'none'


def test_windows_x64_gate_blocks_python_not_x64() -> None:
    gate = build_windows_x64_platform_gate(
        os_platform='win32',
        cpu_arch='x64',
        node_arch='x64',
        python_bitness='32bit',
        version_sources={'package_json': '8.5.2'},
        ccb_source_ref='refs/tags/v8.5.2',
        ccb_branch_ref='feature/windows-herdr',
        herdr_arch='x64',
        helper_arch={'ccb-rs-helper': 'x64', 'ccb-agent-sidebar': 'x64'},
    )

    assert gate['supported'] is False
    assert gate['platform_ready'] is False
    assert gate['failure_reason'] == 'python-not-x64'


def test_windows_x64_gate_blocks_unknown_python_bitness() -> None:
    gate = build_windows_x64_platform_gate(
        os_platform='win32',
        cpu_arch='x64',
        node_arch='x64',
        python_bitness='unknown',
        version_sources={'package_json': '8.5.2'},
        ccb_source_ref='refs/tags/v8.5.2',
        ccb_branch_ref='feature/windows-herdr',
        herdr_arch='x64',
        helper_arch={'ccb-rs-helper': 'x64', 'ccb-agent-sidebar': 'x64'},
    )

    assert gate['supported'] is False
    assert gate['platform_ready'] is False
    assert gate['failure_reason'] == 'unknown'
    assert gate['detail_reason'] == 'python-bitness-unknown'


def test_windows_x64_gate_blocks_version_mismatch() -> None:
    gate = build_windows_x64_platform_gate(
        os_platform='win32',
        cpu_arch='x64',
        node_arch='x64',
        python_bitness='64bit',
        version_sources={'package_json': '8.2.1', 'version_file': '8.2.1'},
        ccb_source_ref='refs/tags/v8.5.2',
        ccb_branch_ref='feature/windows-herdr',
        herdr_arch='x64',
        helper_arch={'ccb-rs-helper': 'x64', 'ccb-agent-sidebar': 'x64'},
    )

    assert gate['supported'] is False
    assert gate['ccb_source_status'] == 'not-v8.5.2'
    assert gate['detected_ccb_version'] == '8.2.1'
    assert gate['failure_reason'] == 'unknown'
    assert gate['detail_reason'] == 'ccb-version-mismatch'


def test_windows_x64_gate_blocks_version_source_mismatch_even_when_installation_is_v852() -> None:
    gate = build_windows_x64_platform_gate(
        os_platform='win32',
        cpu_arch='x64',
        node_arch='x64',
        python_bitness='64bit',
        version_sources={'installation': '8.5.2', 'package_json': '8.2.1', 'version_file': '8.2.1'},
        ccb_source_ref='refs/tags/v8.5.2',
        ccb_branch_ref='feature/windows-herdr',
        herdr_arch='x64',
        helper_arch={'ccb-rs-helper': 'x64', 'ccb-agent-sidebar': 'x64'},
    )

    assert gate['platform_ready'] is False
    assert gate['supported'] is False
    assert gate['failure_reason'] == 'unknown'
    assert gate['detail_reason'] == 'ccb-version-source-mismatch'


def test_windows_x64_gate_blocks_missing_source_branch_admission() -> None:
    gate = build_windows_x64_platform_gate(
        os_platform='win32',
        cpu_arch='x64',
        node_arch='x64',
        python_bitness='64bit',
        version_sources={'package_json': '8.5.2'},
        ccb_source_ref=None,
        ccb_branch_ref=None,
        herdr_arch='x64',
        helper_arch={'ccb-rs-helper': 'x64', 'ccb-agent-sidebar': 'x64'},
    )

    assert gate['supported'] is False
    assert gate['platform_ready'] is False
    assert gate['ccb_source_status'] == 'unknown'
    assert gate['failure_reason'] == 'unknown'
    assert gate['detail_reason'] == 'source-branch-blocked'


def test_windows_x64_gate_blocks_non_v852_source_ref() -> None:
    gate = build_windows_x64_platform_gate(
        os_platform='win32',
        cpu_arch='x64',
        node_arch='x64',
        python_bitness='64bit',
        version_sources={'package_json': '8.5.2'},
        ccb_source_ref='refs/tags/v8.5.1',
        ccb_branch_ref='feature/windows-herdr',
        herdr_arch='x64',
        helper_arch={'ccb-rs-helper': 'x64', 'ccb-agent-sidebar': 'x64'},
    )

    assert gate['supported'] is False
    assert gate['platform_ready'] is False
    assert gate['ccb_source_status'] == 'unknown'
    assert gate['detail_reason'] == 'source-branch-blocked'


def test_windows_x64_gate_blocks_release_source_ref() -> None:
    gate = build_windows_x64_platform_gate(
        os_platform='win32',
        cpu_arch='x64',
        node_arch='x64',
        python_bitness='64bit',
        version_sources={'package_json': '8.5.2'},
        ccb_source_ref='refs/heads/release/v8.5.2',
        ccb_branch_ref='feature/windows-herdr',
        herdr_arch='x64',
        helper_arch={'ccb-rs-helper': 'x64', 'ccb-agent-sidebar': 'x64'},
    )

    assert gate['supported'] is False
    assert gate['platform_ready'] is False
    assert gate['ccb_source_status'] == 'unknown'
    assert gate['detail_reason'] == 'source-branch-blocked'


def test_windows_x64_gate_blocks_mainline_branch_ref() -> None:
    gate = build_windows_x64_platform_gate(
        os_platform='win32',
        cpu_arch='x64',
        node_arch='x64',
        python_bitness='64bit',
        version_sources={'package_json': '8.5.2'},
        ccb_source_ref='refs/tags/v8.5.2',
        ccb_branch_ref='codestable/main',
        herdr_arch='x64',
        helper_arch={'ccb-rs-helper': 'x64', 'ccb-agent-sidebar': 'x64'},
    )

    assert gate['supported'] is False
    assert gate['platform_ready'] is False
    assert gate['ccb_source_status'] == 'unknown'
    assert gate['detail_reason'] == 'source-branch-blocked'


def test_windows_x64_gate_blocks_release_branch_ref() -> None:
    gate = build_windows_x64_platform_gate(
        os_platform='win32',
        cpu_arch='x64',
        node_arch='x64',
        python_bitness='64bit',
        version_sources={'package_json': '8.5.2'},
        ccb_source_ref='refs/tags/v8.5.2',
        ccb_branch_ref='refs/heads/release/v8.5.2',
        herdr_arch='x64',
        helper_arch={'ccb-rs-helper': 'x64', 'ccb-agent-sidebar': 'x64'},
    )

    assert gate['supported'] is False
    assert gate['platform_ready'] is False
    assert gate['ccb_source_status'] == 'unknown'
    assert gate['detail_reason'] == 'source-branch-blocked'


def test_windows_x64_gate_blocks_herdr_missing() -> None:
    gate = build_windows_x64_platform_gate(
        os_platform='win32',
        cpu_arch='x64',
        node_arch='x64',
        python_bitness='64bit',
        version_sources={'package_json': '8.5.2'},
        ccb_source_ref='refs/tags/v8.5.2',
        ccb_branch_ref='feature/windows-herdr',
        herdr_arch='missing',
        helper_arch={'ccb-rs-helper': 'x64', 'ccb-agent-sidebar': 'x64'},
    )

    assert gate['supported'] is False
    assert gate['herdr_executable_ready'] is False
    assert gate['failure_reason'] == 'herdr-not-x64'
    assert gate['detail_reason'] == 'herdr-missing'


def test_windows_x64_gate_blocks_helper_missing() -> None:
    gate = build_windows_x64_platform_gate(
        os_platform='win32',
        cpu_arch='x64',
        node_arch='x64',
        python_bitness='64bit',
        version_sources={'package_json': '8.5.2'},
        ccb_source_ref='refs/tags/v8.5.2',
        ccb_branch_ref='feature/windows-herdr',
        herdr_arch='x64',
        helper_arch={'ccb-rs-helper': 'missing', 'ccb-agent-sidebar': 'x64'},
    )

    assert gate['supported'] is False
    assert gate['native_helpers_ready'] is False
    assert gate['failure_reason'] == 'helper-not-x64'
    assert gate['detail_reason'] == 'helper-missing'


def test_windows_x64_gate_fails_closed_on_helper_trusted_source_conflict() -> None:
    gate = build_windows_x64_platform_gate(
        os_platform='win32',
        cpu_arch='x64',
        node_arch='x64',
        python_bitness='64bit',
        version_sources={'package_json': '8.5.2'},
        ccb_source_ref='refs/tags/v8.5.2',
        ccb_branch_ref='feature/windows-herdr',
        herdr_arch='x64',
        helper_arch={
            'ccb-rs-helper': {'metadata': 'x64', 'pe_header': 'arm64'},
            'ccb-agent-sidebar': 'x64',
        },
    )

    assert gate['supported'] is False
    assert gate['native_helpers_ready'] is False
    assert gate['helper_arch']['ccb-rs-helper'] == 'unknown'
    assert gate['failure_reason'] == 'helper-not-x64'
    assert gate['detail_reason'] == 'helper-unknown'
