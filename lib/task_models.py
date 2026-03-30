"""
task_models.py - 结构化任务传递数据结构

为 GSD 多 AI 协作提供类型化的任务句柄和结果，
避免解析控制台文本。

设计文档: .planning/phases/02-架构设计/designs/task_models_design.md
需求: ARCH-03
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional


@dataclass
class TaskHandle:
    """任务句柄，用于跟踪提交的任务

    Attributes:
        provider: AI 提供商名称（也作为任务标识）
        timestamp: 提交时间戳（Unix 时间，秒）
    """

    provider: str
    timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    def to_json(self) -> str:
        """序列化为 JSON 字符串"""
        return json.dumps(self.to_dict())


@dataclass
class TaskResult:
    """任务结果，包含执行状态和输出

    Attributes:
        provider: 对应的提供商名称
        status: 状态 - "pending", "completed", "error"
        output: 成功时的输出内容
        error: 失败时的错误信息
    """

    provider: str
    status: str
    output: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    def to_json(self) -> str:
        """序列化为 JSON 字符串"""
        return json.dumps(self.to_dict())

    @property
    def is_done(self) -> bool:
        """任务是否已结束（completed 或 error）"""
        return self.status in ("completed", "error")

    @property
    def is_success(self) -> bool:
        """任务是否成功完成"""
        return self.status == "completed"
