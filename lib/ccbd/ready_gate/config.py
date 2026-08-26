"""Ready Gate 并发上限配置。

沿用仓库现有 ``CCB_*`` 环境变量直读模式（参考
``CCB_GEMINI_READY_TIMEOUT_S``）。"""

from __future__ import annotations

import os
from collections.abc import Mapping


DEFAULT_MAX_CONCURRENCY = 3
ENV_MAX_CONCURRENCY = 'CCB_START_MAX_CONCURRENCY'


def resolve_max_concurrency(env: Mapping[str, str] | None = None) -> int:
    """读取并发上限。

    读取 ``CCB_START_MAX_CONCURRENCY``，默认 3。非法值或非正整数回退默认，
    并保证 >= 1。``env`` 可选注入便于测试。
    """
    source = os.environ if env is None else env
    raw = str(source.get(ENV_MAX_CONCURRENCY) or '').strip()
    if not raw:
        return DEFAULT_MAX_CONCURRENCY
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return DEFAULT_MAX_CONCURRENCY
    return value if value >= 1 else DEFAULT_MAX_CONCURRENCY


__all__ = ['DEFAULT_MAX_CONCURRENCY', 'ENV_MAX_CONCURRENCY', 'resolve_max_concurrency']