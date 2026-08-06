from __future__ import annotations

import pytest

from agents.config_loader_runtime.common import ConfigValidationError
from agents.config_loader_runtime.parsing_runtime.validation import validate_project_config
from agents.config_loader_runtime.parsing_runtime.workflow_v3 import _parse_runtime_mux_backend_v3


def _v2_doc(runtime_payload) -> dict:
    doc = {
        'version': 2,
        'entry_window': 'main',
        'windows': {'main': 'agent1:codex'},
    }
    if runtime_payload is not None:
        doc['runtime'] = runtime_payload
    return doc


def test_v2_runtime_mux_backend_herdr() -> None:
    cfg = validate_project_config(_v2_doc({'mux': {'backend': 'herdr'}}))
    assert cfg.runtime_mux_backend == 'herdr'


def test_v2_runtime_mux_backend_absent() -> None:
    cfg = validate_project_config(_v2_doc(None))
    assert cfg.runtime_mux_backend is None
    # 显式 null mux 视为 absent（raw_mux is None 分支）
    cfg2 = validate_project_config(_v2_doc({'mux': None}))
    assert cfg2.runtime_mux_backend is None


@pytest.mark.parametrize(
    'payload',
    [
        {'mux': {'backend': 'rmux'}},
        {'mux': {'backend': 'other'}},
        {'mux': {'backend': 'herdr', 'x': 1}},
        {'foo': 1},
        'not-a-mapping',
    ],
)
def test_v2_runtime_mux_backend_rejects_invalid(payload) -> None:
    with pytest.raises(ConfigValidationError):
        validate_project_config(_v2_doc(payload))


# --- VA-5: unknown runtime.* fields fail-closed ---

@pytest.mark.parametrize(
    'runtime_payload',
    [
        {'mux': {'backend': 'herdr'}, 'other_key': 1},
        {'unknown_section': {'x': 1}},
        {'mux': {'backend': 'herdr', 'unknown_field': 'value'}},
    ],
)
def test_v2_unknown_runtime_fields_rejected(runtime_payload) -> None:
    with pytest.raises(ConfigValidationError):
        validate_project_config(_v2_doc(runtime_payload))


# --- VA-6: 非 Windows 环境 + runtime.mux.backend fail-closed ---

def test_herdr_selection_blocked_by_non_windows_platform_gate() -> None:
    """非 Windows platform gate 应阻止 herdr 后端选择。"""
    from terminal_runtime.backend_resolver import resolve_mux_backend_v2

    non_windows_gate = {
        'supported': False,
        'os_platform': 'linux',
        'cpu_arch': 'x64',
        'python_bitness': '64bit',
        'is_wsl': False,
    }
    result = resolve_mux_backend_v2(
        requested_backend='herdr',
        source='user_config',
        platform_gate=non_windows_gate,
        capability_report=None,
        capability_report_ref=None,
    )
    assert result.get('blocked') is True
    assert result.get('failure_reason') in {
        'platform-gate-blocked',
        'herdr-capability-missing',
        'unsupported-capability',
    }
    assert result.get('effective_backend') is None
    assert result.get('fallback_used') is False


def test_herdr_config_accepted_on_windows_with_capability() -> None:
    """Windows + capability evidence → herdr 后端选择成功。

    注：完整能力矩阵需要所有 facade capabilities（workspace_create 等），
    此处仅验证 selection flow 可达到非 blocked 分支。
    """
    from terminal_runtime.backend_resolver import resolve_mux_backend_v2
    from terminal_runtime.herdr_backend_runtime.capabilities import (
        _CORE_REQUIRED_CAPABILITIES,
        _KNOWN_CAPABILITIES,
    )

    windows_gate = {
        'supported': True, 'os_platform': 'win32', 'cpu_arch': 'x64',
        'python_bitness': '64bit', 'is_wsl': False,
    }
    # 构造包含所有 facade capabilities + 元数据字段的最小 supported 报告
    all_supported = {name: 'supported' for name in _KNOWN_CAPABILITIES}
    capability = {
        'backend_impl': 'herdr',
        'command_status': dict(all_supported),
        'semantic_status': dict(all_supported),
        'windows_beta_gaps': [],
        'blocking_gaps': [],
        'source_ref': 'test/ref',
        'adapter_recommendation': 'continue',
        'verdict': 'pass',
        'failure_class': '',
    }
    result = resolve_mux_backend_v2(
        requested_backend='herdr',
        source='user_config',
        platform_gate=windows_gate,
        capability_report=capability,
        capability_report_ref='test/ref',
    )
    assert result.get('blocked') is not True
    assert result.get('effective_backend') == 'herdr'
    assert result.get('backend_family') == 'herdr-native'


# --- VA-3: herdr selection fails when herdr server unavailable ---

def test_herdr_selection_blocked_without_capability_evidence() -> None:
    """缺 capability evidence → herdr 后端选择 fail-closed，不 fallback tmux。"""
    from terminal_runtime.backend_resolver import resolve_mux_backend_v2

    windows_gate = {
        'supported': True,
        'os_platform': 'win32',
        'cpu_arch': 'x64',
        'python_bitness': '64bit',
        'is_wsl': False,
    }
    result = resolve_mux_backend_v2(
        requested_backend='herdr',
        source='user_config',
        platform_gate=windows_gate,
        capability_report=None,  # no evidence
        capability_report_ref=None,
    )
    assert result.get('blocked') is True
    assert result.get('failure_reason') == 'herdr-capability-missing'
    assert result.get('effective_backend') is None
    assert result.get('fallback_used') is False  # D5: 不静默回退


def test_herdr_selection_blocked_by_capability_gaps() -> None:
    """blocking_gaps 非空 → herdr 后端选择 fail-closed。"""
    from terminal_runtime.backend_resolver import resolve_mux_backend_v2

    windows_gate = {
        'supported': True,
        'os_platform': 'win32',
        'cpu_arch': 'x64',
        'python_bitness': '64bit',
        'is_wsl': False,
    }
    capability = {
        'backend_impl': 'herdr',
        'command_status': {'session_attach': 'supported', 'pane_spawn': 'supported'},
        'semantic_status': {'session_attach': 'supported', 'pane_spawn': 'supported'},
        'blocking_gaps': ['pane_split_unavailable'],
        'source_ref': 'test/ref',
    }
    result = resolve_mux_backend_v2(
        requested_backend='auto',
        source='platform_default',
        platform_gate=windows_gate,
        capability_report=capability,
        capability_report_ref='test/ref',
    )
    assert result.get('blocked') is True
    assert result.get('failure_reason') == 'unsupported-capability'


# v3 完整 config 校验依赖 rolepack 安装（测试基础设施），此处直接测 mux 解析 helper。
# helper 的 raw 是 workflow.runtime 内容（含 'mux' 键），不是 mux 内容本身。
def test_v3_runtime_mux_backend_herdr() -> None:
    assert (
        _parse_runtime_mux_backend_v3({'mux': {'backend': 'herdr'}}, path='workflow.runtime.mux')
        == 'herdr'
    )


def test_v3_runtime_mux_backend_absent() -> None:
    assert _parse_runtime_mux_backend_v3({}, path='workflow.runtime.mux') is None
    # 显式 null mux 视为 absent（mux_value is None 分支，与 v2 对齐）
    assert _parse_runtime_mux_backend_v3({'mux': None}, path='workflow.runtime.mux') is None


@pytest.mark.parametrize(
    'payload',
    [
        {'mux': {'backend': 'rmux'}},
        {'mux': {'backend': 'other'}},
        {'mux': {'backend': 'herdr', 'x': 1}},
    ],
)
def test_v3_runtime_mux_backend_rejects_invalid(payload) -> None:
    with pytest.raises(ConfigValidationError):
        _parse_runtime_mux_backend_v3(payload, path='workflow.runtime.mux')
