"""Ready Gate 并发上限配置测试。"""

from __future__ import annotations

from ccbd.ready_gate.config import (
    DEFAULT_MAX_CONCURRENCY,
    ENV_MAX_CONCURRENCY,
    resolve_max_concurrency,
)


def test_default_max_concurrency_is_three() -> None:
    assert DEFAULT_MAX_CONCURRENCY == 3


def test_resolve_default_when_unset() -> None:
    assert resolve_max_concurrency({}) == 3


def test_resolve_from_env() -> None:
    assert resolve_max_concurrency({ENV_MAX_CONCURRENCY: '5'}) == 5


def test_resolve_falls_back_on_zero() -> None:
    assert resolve_max_concurrency({ENV_MAX_CONCURRENCY: '0'}) == 3


def test_resolve_falls_back_on_negative() -> None:
    assert resolve_max_concurrency({ENV_MAX_CONCURRENCY: '-1'}) == 3


def test_resolve_falls_back_on_non_numeric() -> None:
    assert resolve_max_concurrency({ENV_MAX_CONCURRENCY: 'abc'}) == 3


def test_resolve_falls_back_on_whitespace() -> None:
    assert resolve_max_concurrency({ENV_MAX_CONCURRENCY: '   '}) == 3


def test_resolve_max_is_at_least_one() -> None:
    # 有值但 <=0 一律回退默认（>=1）
    assert resolve_max_concurrency({ENV_MAX_CONCURRENCY: '-100'}) == 3