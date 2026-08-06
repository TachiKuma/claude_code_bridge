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
