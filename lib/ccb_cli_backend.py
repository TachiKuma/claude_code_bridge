"""
ccb_cli_backend.py - CCB CLI 包装接口

通过 subprocess 包装 CCB 的 ask/pend 命令，
为 GSD 提供结构化的多 AI 协作能力。

约束：每个 provider 同时只能有一个活跃任务。

设计文档: .planning/phases/02-架构设计/designs/ccb_cli_backend_design_v3.md
需求: ARCH-02
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from typing import Dict, List, Optional

from lib.process_lock import ProviderLock
from lib.task_models import TaskHandle, TaskResult

# CCB 退出码常量（per lib/cli_output.py）
EXIT_OK = 0
EXIT_ERROR = 1
EXIT_NO_REPLY = 2

# 支持的提供商列表
SUPPORTED_PROVIDERS = ["codex", "droid", "gemini", "claude"]


class CCBCLIBackend:
    """CCB CLI 包装接口，提供结构化的多 AI 协作能力

    约束：每个 provider 同时只能有一个活跃任务
    """

    def __init__(self, lock_timeout: float = 60.0):
        """初始化后端

        Args:
            lock_timeout: 文件锁超时时间（秒）
        """
        self.lock_timeout = lock_timeout

    def _build_kwargs(self) -> Dict:
        """构建 subprocess.run() 的平台相关参数"""
        kwargs: Dict = {
            "capture_output": True,
            "text": True,
        }
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            kwargs["startupinfo"] = startupinfo
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        return kwargs

    def submit(
        self,
        provider: str,
        prompt: str,
        context: Optional[Dict] = None,
    ) -> TaskHandle:
        """提交任务到 AI 提供商

        Args:
            provider: AI 提供商名称
            prompt: 提示文本
            context: 可选上下文信息（保留扩展用）

        Returns:
            TaskHandle(provider, timestamp)
        """
        cmd = ["ask", provider, "--background", prompt]
        kwargs = self._build_kwargs()
        kwargs["timeout"] = 10

        try:
            with ProviderLock(provider, timeout=self.lock_timeout):
                subprocess.run(cmd, **kwargs)
        except (TimeoutError, subprocess.TimeoutExpired):
            pass  # 提交失败延迟到 poll() 体现

        return TaskHandle(provider=provider, timestamp=time.time())

    def poll(self, handle: TaskHandle) -> TaskResult:
        """轮询任务结果

        Args:
            handle: 任务句柄

        Returns:
            TaskResult:
              - returncode 0 (EXIT_OK) -> status="completed", output=stdout
              - returncode 2 (EXIT_NO_REPLY) -> status="pending"
              - returncode 1 (EXIT_ERROR) -> status="error", error=stderr
              - 其他 -> status="error"
        """
        cmd = ["pend", handle.provider]
        kwargs = self._build_kwargs()
        kwargs["timeout"] = 5

        try:
            with ProviderLock(handle.provider, timeout=self.lock_timeout):
                result = subprocess.run(cmd, **kwargs)
        except (TimeoutError, subprocess.TimeoutExpired):
            return TaskResult(
                provider=handle.provider,
                status="error",
                error="Timeout waiting for reply",
            )
        except FileNotFoundError:
            return TaskResult(
                provider=handle.provider,
                status="error",
                error=f"Command not found: {' '.join(cmd)}",
            )

        if result.returncode == EXIT_OK:
            return TaskResult(
                provider=handle.provider,
                status="completed",
                output=result.stdout.strip() if result.stdout else "",
            )
        elif result.returncode == EXIT_NO_REPLY:
            return TaskResult(
                provider=handle.provider,
                status="pending",
            )
        else:
            return TaskResult(
                provider=handle.provider,
                status="error",
                error=result.stderr.strip()
                or f"Command failed with code {result.returncode}",
            )

    def ping(self, provider: str) -> bool:
        """检查提供商连接状态

        Args:
            provider: AI 提供商名称

        Returns:
            True 如果提供商可用，False 否则
        """
        cmd = ["ccb-ping", provider]
        kwargs = self._build_kwargs()
        kwargs["timeout"] = 2

        try:
            result = subprocess.run(cmd, **kwargs)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def list_providers(self) -> List[str]:
        """列出所有可用的 AI 提供商

        Returns:
            提供商名称列表，失败时返回空列表
        """
        cmd = ["ccb-mounted"]
        kwargs = self._build_kwargs()
        kwargs["timeout"] = 2

        try:
            result = subprocess.run(cmd, **kwargs)
            if result.returncode == 0 and result.stdout:
                data = json.loads(result.stdout)
                return data.get("mounted", [])
            return []
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            return []
