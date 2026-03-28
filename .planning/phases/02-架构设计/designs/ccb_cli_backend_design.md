# CCBCLIBackend 接口设计

**设计日期:** 2026-03-28
**需求:** ARCH-02
**用户决策:** D-08, D-10, D-11

## 1. 接口概述

CCBCLIBackend 为 GSD 提供标准化的多 AI 协作接口，通过 subprocess 包装 CCB 的 ask/pend 命令实现。

**目标:**
- 异步任务提交和结果轮询
- 结构化数据传递（避免解析控制台文本）
- 统一的错误处理机制
- 支持多 AI 提供商（codex, droid, gemini, claude）

**实现方式:** subprocess 包装 CCB CLI 命令（per D-11）

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
2. 构造命令: `["ask", provider, prompt]`
3. 使用 subprocess.run() 执行（后台模式，添加 & 符号）
4. 生成 task_id: `f"{provider}_{int(time.time() * 1000)}"`
5. 返回 TaskHandle(task_id, provider, time.time())

### 命令格式

```bash
ask {provider} "{prompt}" &
```

后台执行，不等待命令完成。

### 错误处理

- provider 无效时仍返回 TaskHandle
- 错误延迟到 poll() 时通过 TaskResult(status="error") 报告
- 保持接口一致性（per D-10）

### 实现示例

```python
import subprocess
import time

def submit(self, provider: str, prompt: str, context: Optional[Dict] = None) -> TaskHandle:
    cmd = ["ask", provider, prompt]
    subprocess.run(cmd, capture_output=False, text=True)

    task_id = f"{provider}_{int(time.time() * 1000)}"
    return TaskHandle(
        task_id=task_id,
        provider=provider,
        timestamp=time.time()
    )
```

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

1. 构造命令: `[f"{handle.provider[0]}pend"]`（如 cpend, dpend）
2. 使用 subprocess.run(capture_output=True, text=True) 执行
3. 检查返回码:
   - returncode != 0 → TaskResult(status="error", error=stderr)
   - stdout 非空 → TaskResult(status="completed", output=stdout.strip())
   - stdout 为空 → TaskResult(status="pending")

### 命令映射

| Provider | pend 命令 |
|----------|----------|
| codex    | cpend    |
| droid    | dpend    |
| gemini   | gpend    |
| claude   | (预留)   |

### 超时处理

使用 subprocess timeout 参数（默认 5 秒）

### 实现示例

```python
def poll(self, handle: TaskHandle) -> TaskResult:
    cmd = [f"{handle.provider[0]}pend"]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5
        )
    except subprocess.TimeoutExpired:
        return TaskResult(
            task_id=handle.task_id,
            status="error",
            error="Timeout waiting for reply"
        )

    if result.returncode != 0:
        return TaskResult(
            task_id=handle.task_id,
            status="error",
            error=result.stderr.strip() or "Command failed"
        )

    if result.stdout.strip():
        return TaskResult(
            task_id=handle.task_id,
            status="completed",
            output=result.stdout.strip()
        )

    return TaskResult(
        task_id=handle.task_id,
        status="pending"
    )
```

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

1. 构造命令: `[f"{provider[0]}ping"]`（如 cping, dping）
2. 使用 subprocess.run() 执行
3. 返回 returncode == 0

### 命令映射

| Provider | ping 命令 |
|----------|----------|
| codex    | cping    |
| droid    | dping    |
| gemini   | gping    |

### 超时设置

2 秒（快速检测）

### 实现示例

```python
def ping(self, provider: str) -> bool:
    cmd = [f"{provider[0]}ping"]

    try:
        result = subprocess.run(cmd, capture_output=False, timeout=2)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False
```

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

1. 执行命令: `["ccb-mounted"]`
2. 解析 stdout，按行分割
3. 返回提供商列表（如 ["codex", "droid", "gemini"]）

### 输出格式

ccb-mounted 命令输出每行一个提供商名称：

```
codex
droid
gemini
```

### 错误处理

命令失败时返回空列表 []

### 实现示例

```python
def list_providers(self) -> List[str]:
    cmd = ["ccb-mounted"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            return [p.strip() for p in result.stdout.strip().split("\n") if p.strip()]
        return []
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []
```

## 7. 错误处理策略（D-10）

**设计原则:** 所有方法不抛出异常，通过返回值报告错误。

| 方法 | 错误处理 |
|------|---------|
| submit() | 始终返回 TaskHandle，错误延迟到 poll() |
| poll() | 返回 TaskResult(status="error")，不抛出异常 |
| ping() | 返回 False，不抛出异常 |
| list_providers() | 返回空列表 []，不抛出异常 |

**一致性保证:** 调用者无需 try-except，通过检查返回值判断成功或失败。

## 8. subprocess 包装模式（D-11）

### 提交任务（后台）

```python
result = subprocess.run(
    ["ask", provider, prompt],
    capture_output=False,  # 不捕获输出（后台运行）
    text=True
)
```

### 轮询结果

```python
result = subprocess.run(
    [f"{provider[0]}pend"],
    capture_output=True,
    text=True,
    timeout=5
)
```

### 检查连接

```python
result = subprocess.run(
    [f"{provider[0]}ping"],
    capture_output=False,
    timeout=2
)
```

## 9. 与 CCB 命令的映射表

| 方法 | CCB 命令 | 说明 |
|------|----------|------|
| submit("codex", "...") | ask codex "..." & | 后台提交 |
| poll(handle) | cpend | 轮询 Codex 结果 |
| poll(handle) | dpend | 轮询 Droid 结果 |
| poll(handle) | gpend | 轮询 Gemini 结果 |
| ping("codex") | cping | 检查 Codex 连接 |
| list_providers() | ccb-mounted | 列出已挂载提供商 |

## 10. 使用示例

### 基本使用

```python
backend = CCBCLIBackend()

# 检查可用提供商
providers = backend.list_providers()
# ["codex", "droid", "gemini"]

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

## 11. 线程安全性

**当前设计:** 非线程安全（subprocess 调用无锁）

**并发场景:**
- 多个 submit() 可并行调用（不同提供商）
- 同一提供商的 poll() 应串行调用（避免竞态条件）

**限制:** 同一时刻每个提供商只能有一个活跃任务

## 12. 未来扩展

预留扩展点：

- **context 参数:** 传递文件路径、项目信息等
- **超时配置:** 可添加 timeout 参数到 poll()
- **批量操作:** 可添加 submit_batch() 方法
- **流式输出:** 支持 poll() 返回部分结果

当前设计保持最小化，扩展时添加可选参数不破坏兼容性。

---

**设计完成:** 2026-03-28
**依赖:** task_models_design.md（TaskHandle/TaskResult 定义）
**下一步:** Phase 4 原型实现
