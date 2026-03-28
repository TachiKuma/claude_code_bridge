# CCBCLIBackend 接口设计 v2

**设计日期:** 2026-03-28 (修订)
**需求:** ARCH-02
**用户决策:** D-08, D-10, D-11
**修订原因:** 修复任务模型与 CCB 实际契约不匹配的问题

---

## 1. 接口概述

CCBCLIBackend 为 GSD 提供标准化的多 AI 协作接口，通过 subprocess 包装 CCB 的 ask/pend 命令实现。

**目标:**
- 异步任务提交和结果轮询
- 结构化数据传递（避免解析控制台文本）
- 统一的错误处理机制
- 支持多 AI 提供商（codex, droid, gemini, claude）

**实现方式:** subprocess 包装 CCB CLI 命令（per D-11）

**关键修复:**
- 使用 CCB 实际的 `--background` 标志而非 shell `&`
- 使用通用 `pend` 命令而非 provider[0] 推导
- 使用通用 `ccb-ping` 命令
- 正确解析 `ccb-mounted` 的 JSON 输出
- 简化任务模型，使用 provider 作为任务标识

---

## 2. 类设计

```python
from typing import List, Optional, Dict
from task_models import TaskHandle, TaskResult

class CCBCLIBackend:
    """CCB CLI 包装接口，提供结构化的多 AI 协作能力"""

    def submit(self, provider: str, prompt: str, context: Optional[Dict] = None) -> TaskHandle:
        """提交任务到 AI 提供商"""
        pass

    def poll(self, handle: TaskHandle) -> TaskResult:
        """轮询任务结果"""
        pass

    def ping(self, provider: str) -> bool:
        """检查提供商连接状态"""
        pass

    def list_providers(self) -> List[str]:
        """列出所有可用的 AI 提供商"""
        pass
```

---

## 3. submit() 方法设计

### 方法签名

```python
def submit(self, provider: str, prompt: str, context: Optional[Dict] = None) -> TaskHandle:
    """提交任务到 AI 提供商

    Args:
        provider: 提供商名称（codex, droid, gemini, claude）
        prompt: 提示词内容
        context: 可选的上下文信息（预留，当前未使用）

    Returns:
        TaskHandle: 任务句柄，用于后续轮询
    """
```

### 实现逻辑

1. 验证 provider 在可用列表中
2. 构造命令: `["ask", provider, "--background", prompt]`
3. 使用 subprocess.Popen() 执行（真正的后台模式）
4. 返回 TaskHandle(provider=provider, timestamp=time.time())

### 命令格式

```bash
ask {provider} --background "{prompt}"
```

使用 CCB 内置的 `--background` 标志，而非 shell 的 `&` 符号。

### 任务标识简化

**关键变更:** 不生成客户端 task_id，直接使用 provider 作为任务标识。

**原因:**
- CCB 每个 provider 同时只能有一个活跃任务
- pend 命令自动获取该 provider 的最新回复
- 无需维护复杂的任务 ID 映射

### 实现示例

```python
import subprocess
import time
from typing import Optional, Dict

def submit(self, provider: str, prompt: str, context: Optional[Dict] = None) -> TaskHandle:
    """提交任务到 AI 提供商"""
    cmd = ["ask", provider, "--background", prompt]

    # 使用 Popen 真正后台执行
    subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True  # 完全分离进程
    )

    return TaskHandle(
        provider=provider,
        timestamp=time.time()
    )
```

### 错误处理

- provider 无效时仍返回 TaskHandle
- 错误延迟到 poll() 时通过 TaskResult(status="error") 报告
- 保持接口一致性（per D-10）

---

## 4. poll() 方法设计

### 方法签名

```python
def poll(self, handle: TaskHandle) -> TaskResult:
    """轮询任务结果

    Args:
        handle: submit() 返回的任务句柄

    Returns:
        TaskResult: 任务结果（pending/completed/error）
    """
```

### 实现逻辑

1. 构造命令: `["pend", handle.provider]`（使用通用 pend 命令）
2. 使用 subprocess.run(capture_output=True, text=True) 执行
3. 检查返回码:
   - returncode != 0 → TaskResult(status="error", error=stderr)
   - stdout 非空 → TaskResult(status="completed", output=stdout.strip())
   - stdout 为空 → TaskResult(status="pending")

### 命令映射

**关键修复:** 使用通用 `pend` 命令，而非从 provider[0] 推导。

| Provider | 命令 |
|----------|------|
| codex    | pend codex |
| droid    | pend droid |
| gemini   | pend gemini |
| claude   | pend claude |

### 超时处理

使用 subprocess timeout 参数（默认 5 秒）

### 实现示例

```python
def poll(self, handle: TaskHandle) -> TaskResult:
    cmd = ["pend", handle.provider]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5
        )
    except subprocess.TimeoutExpired:
        return TaskResult(
            provider=handle.provider,
            status="error",
            error="Timeout waiting for reply"
        )

    if result.returncode != 0:
        return TaskResult(
            provider=handle.provider,
            status="error",
            error=result.stderr.strip() or "Command failed"
        )

    if result.stdout.strip():
        return TaskResult(
            provider=handle.provider,
            status="completed",
            output=result.stdout.strip()
        )

    return TaskResult(
        provider=handle.provider,
        status="pending"
    )
```

---

## 5. ping() 方法设计

### 方法签名

```python
def ping(self, provider: str) -> bool:
    """检查提供商连接状态

    Args:
        provider: 提供商名称

    Returns:
        bool: True 表示可用，False 表示不可用
    """
```

### 实现逻辑

**关键修复:** 使用通用 `ccb-ping` 命令，而非从 provider[0] 推导。

1. 构造命令: `["ccb-ping", provider]`
2. 使用 subprocess.run() 执行
3. 返回 returncode == 0

### 超时设置

2 秒（快速检测）

### 实现示例

```python
def ping(self, provider: str) -> bool:
    cmd = ["ccb-ping", provider]

    try:
        result = subprocess.run(cmd, capture_output=True, timeout=2)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False
```

---

## 6. list_providers() 方法设计

### 方法签名

```python
def list_providers(self) -> List[str]:
    """列出所有可用的 AI 提供商

    Returns:
        List[str]: 提供商名称列表
    """
```

### 实现逻辑

**关键修复:** 正确解析 `ccb-mounted` 的 JSON 输出。

1. 执行命令: `["ccb-mounted"]`
2. 解析 JSON 输出: `{"cwd": "...", "mounted": ["codex", "droid", ...]}`
3. 返回 `mounted` 字段的值

### 输出格式

ccb-mounted 命令输出 JSON 格式：

```json
{
  "cwd": "/path/to/project",
  "mounted": ["codex", "droid", "gemini", "claude"]
}
```

### 错误处理

- 命令失败时返回空列表 []
- JSON 解析失败时返回空列表 []

### 实现示例

```python
import json

def list_providers(self) -> List[str]:
    cmd = ["ccb-mounted"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data.get("mounted", [])
        return []
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        return []
```

---

## 7. 错误处理策略（D-10）

**设计原则:** 所有方法不抛出异常，通过返回值报告错误。

| 方法 | 错误处理 |
|------|---------|
| submit() | 始终返回 TaskHandle，错误延迟到 poll() |
| poll() | 返回 TaskResult(status="error")，不抛出异常 |
| ping() | 返回 False，不抛出异常 |
| list_providers() | 返回空列表 []，不抛出异常 |

**一致性保证:** 调用者无需 try-except，通过检查返回值判断成功或失败。

---

## 8. subprocess 包装模式（D-11）

### 提交任务（后台）

```python
subprocess.Popen(
    ["ask", provider, "--background", prompt],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    start_new_session=True  # 完全分离进程
)
```

### 轮询结果

```python
result = subprocess.run(
    ["pend", provider],
    capture_output=True,
    text=True,
    timeout=5
)
```

### 检查连接

```python
result = subprocess.run(
    ["ccb-ping", provider],
    capture_output=True,
    timeout=2
)
```

---

## 9. 与 CCB 命令的映射表

| 方法 | CCB 命令 | 说明 |
|------|----------|------|
| submit("codex", "...") | ask codex --background "..." | 后台提交 |
| poll(handle) | pend codex | 轮询 Codex 结果 |
| poll(handle) | pend droid | 轮询 Droid 结果 |
| poll(handle) | pend gemini | 轮询 Gemini 结果 |
| ping("codex") | ccb-ping codex | 检查 Codex 连接 |
| list_providers() | ccb-mounted | 列出已挂载提供商（JSON） |

---

## 10. 使用示例

### 基本使用

```python
backend = CCBCLIBackend()

# 检查可用提供商
providers = backend.list_providers()
# ["codex", "droid", "gemini", "claude"]

# 提交任务
handle = backend.submit("codex", "Review this code")

# 轮询结果
while True:
    result = backend.poll(handle)
    if result.status == "completed":
        print(result.output)
        break
    elif result.status == "error":
        print(f"Error: {result.error}")
        break
    time.sleep(1)
```

### 并行多 AI

```python
# 提交到多个 AI
handles = []
for provider in ["codex", "droid", "gemini"]:
    handle = backend.submit(provider, "Review this code")
    handles.append(handle)

# 轮询所有结果
results = []
for handle in handles:
    while True:
        result = backend.poll(handle)
        if result.status != "pending":
            results.append(result)
            break
        time.sleep(1)
```

---

## 11. 线程安全性

**当前设计:** 非线程安全（subprocess 调用无锁）

**并发场景:**
- 多个 submit() 可并行调用（不同提供商）
- 同一提供商的 poll() 应串行调用（避免竞态条件）

**限制:** 同一时刻每个提供商只能有一个活跃任务

---

## 12. 关键修复总结

| 问题 | 原设计 | 修复后 |
|------|--------|--------|
| 后台执行 | shell `&` 符号 | `--background` 标志 |
| 任务标识 | 客户端生成 task_id | 使用 provider 作为标识 |
| poll 命令 | `{provider[0]}pend` | `pend {provider}` |
| ping 命令 | `{provider[0]}ping` | `ccb-ping {provider}` |
| ccb-mounted | 按行解析文本 | 解析 JSON 输出 |

---

## 13. 未来扩展

预留扩展点：

- **context 参数:** 传递文件路径、项目信息等
- **超时配置:** 可添加 timeout 参数到 poll()
- **批量操作:** 可添加 submit_batch() 方法
- **流式输出:** 支持 poll() 返回部分结果

当前设计保持最小化，扩展时添加可选参数不破坏兼容性。

---

**设计完成:** 2026-03-28 (修订版)
**依赖:** task_models_design.md（TaskHandle/TaskResult 定义需同步更新）
**下一步:** 更新 task_models_design.md，移除 task_id 字段

## 14. Windows 兼容性设计（补充）

**修复原因:** Droid 审核指出 subprocess 包装模式在 Windows 环境下的兼容性未充分验证。

### Windows 后台任务实现

在 Windows 上，后台任务需要特殊处理以避免弹出控制台窗口：

```python
import subprocess
import sys

def submit(self, provider: str, prompt: str, context: Optional[Dict] = None) -> TaskHandle:
    cmd = ["ask", provider, "--background", prompt]

    # Windows 特殊处理
    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
    else:
        # Unix/Linux/macOS
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )

    return TaskHandle(
        provider=provider,
        timestamp=time.time()
    )
```

### 跨平台测试清单

| 平台 | 测试项 | 预期行为 |
|------|--------|---------|
| Windows | submit() 后台执行 | 无控制台窗口弹出 |
| Windows | poll() 命令执行 | 正常捕获 stdout/stderr |
| Linux | submit() 后台执行 | 进程完全分离 |
| macOS | submit() 后台执行 | 进程完全分离 |

### 路径处理

CCB 命令在 Windows 上使用 Git Bash 或 WSL，路径处理已由 CCB 内部处理，无需特殊转换。

---
