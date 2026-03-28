# CCBCLIBackend 接口设计 v3

**设计日期:** 2026-03-28 (第二次修订)
**需求:** ARCH-02
**用户决策:** D-08, D-10, D-11
**修订原因:** 修复 poll() 退出码映射错误

---

## 1. 接口概述

CCBCLIBackend 为 GSD 提供标准化的多 AI 协作接口，通过 subprocess 包装 CCB 的 ask/pend 命令实现。

**目标:**
- 异步任务提交和结果轮询
- 结构化数据传递（避免解析控制台文本）
- 统一的错误处理机制
- 支持多 AI 提供商（codex, droid, gemini, claude）

**实现方式:** subprocess 包装 CCB CLI 命令（per D-11）

**关键修复（v3）:**
- 正确映射 CCB 退出码：EXIT_OK(0)、EXIT_ERROR(1)、EXIT_NO_REPLY(2)
- 明确单任务约束：每个 provider 同时只能有一个活跃任务
- 使用 subprocess.run() 而非 Popen，保留 ask 输出以便调试

---

## 2. CCB 退出码定义

根据 `lib/cli_output.py`：

```python
EXIT_OK = 0         # 成功，有输出
EXIT_ERROR = 1      # 错误
EXIT_NO_REPLY = 2   # 无回复（仍在处理中）
```

---

## 3. 类设计

```python
from typing import List, Optional, Dict
from task_models import TaskHandle, TaskResult

class CCBCLIBackend:
    """CCB CLI 包装接口，提供结构化的多 AI 协作能力
    
    约束：每个 provider 同时只能有一个活跃任务
    """

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

## 4. submit() 方法设计

### 方法签名

```python
def submit(self, provider: str, prompt: str, context: Optional[Dict] = None) -> TaskHandle:
    """提交任务到 AI 提供商
    
    约束：同一 provider 同时只能有一个活跃任务
    """
```

### 实现逻辑

1. 验证 provider 在可用列表中
2. 构造命令: `["ask", provider, "--background", prompt]`
3. 使用 subprocess.run() 执行（保留输出以便调试）
4. 返回 TaskHandle(provider=provider, timestamp=time.time())

### 命令格式

```bash
ask {provider} --background "{prompt}"
```

### 实现示例

```python
import subprocess
import time

def submit(self, provider: str, prompt: str, context: Optional[Dict] = None) -> TaskHandle:
    cmd = ["ask", provider, "--background", prompt]
    
    # 使用 run() 而非 Popen，保留输出以便调试
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=10
    )
    
    # 记录提交结果（可选）
    if result.returncode != 0:
        # 提交失败会在 poll() 时体现
        pass
    
    return TaskHandle(
        provider=provider,
        timestamp=time.time()
    )
```

---

## 5. poll() 方法设计（关键修复）

### 方法签名

```python
def poll(self, handle: TaskHandle) -> TaskResult:
    """轮询任务结果"""
```

### 实现逻辑（修复后）

1. 构造命令: `["pend", handle.provider]`
2. 使用 subprocess.run(capture_output=True, text=True) 执行
3. **根据 CCB 退出码映射状态**:
   - `returncode == 0` (EXIT_OK) → `status="completed"`, output=stdout
   - `returncode == 2` (EXIT_NO_REPLY) → `status="pending"`
   - `returncode == 1` (EXIT_ERROR) → `status="error"`, error=stderr
   - 其他 → `status="error"`

### 退出码映射表

| 退出码 | CCB 常量 | TaskResult.status | 说明 |
|--------|----------|-------------------|------|
| 0 | EXIT_OK | completed | 有回复，任务完成 |
| 2 | EXIT_NO_REPLY | pending | 无回复，仍在处理 |
| 1 | EXIT_ERROR | error | 命令执行错误 |

### 实现示例

```python
# CCB 退出码常量
EXIT_OK = 0
EXIT_ERROR = 1
EXIT_NO_REPLY = 2

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

    # 正确的退出码映射
    if result.returncode == EXIT_OK:
        return TaskResult(
            provider=handle.provider,
            status="completed",
            output=result.stdout.strip()
        )
    elif result.returncode == EXIT_NO_REPLY:
        return TaskResult(
            provider=handle.provider,
            status="pending"
        )
    else:  # EXIT_ERROR 或其他
        return TaskResult(
            provider=handle.provider,
            status="error",
            error=result.stderr.strip() or f"Command failed with code {result.returncode}"
        )
```

---

## 6. ping() 和 list_providers() 方法

### ping() 实现

```python
def ping(self, provider: str) -> bool:
    cmd = ["ccb-ping", provider]
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=2)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False
```

### list_providers() 实现

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

## 7. 单任务约束

**设计约束:** 每个 provider 同时只能有一个活跃任务。

### 约束说明

- CCB 的 `pend` 命令返回该 provider 的最新回复
- 如果同时提交多个任务到同一 provider，只能获取最后一个任务的结果
- 这是 CCB 架构的固有限制，非设计缺陷

### 使用建议

```python
# 正确用法：等待第一个任务完成后再提交第二个
handle1 = backend.submit("codex", "Task 1")
while backend.poll(handle1).status == "pending":
    time.sleep(1)

handle2 = backend.submit("codex", "Task 2")  # 安全

# 错误用法：同时提交多个任务到同一 provider
handle1 = backend.submit("codex", "Task 1")
handle2 = backend.submit("codex", "Task 2")  # 会覆盖 Task 1
```

### 并发支持

不同 provider 可以并发：

```python
# 正确：并发提交到不同 provider
handles = {
    "codex": backend.submit("codex", "Review code"),
    "droid": backend.submit("droid", "Review code"),
    "gemini": backend.submit("gemini", "Review code")
}
```

---

## 8. 错误处理策略

| 方法 | 错误处理 |
|------|---------|
| submit() | 始终返回 TaskHandle，错误延迟到 poll() |
| poll() | 返回 TaskResult(status="error")，不抛出异常 |
| ping() | 返回 False，不抛出异常 |
| list_providers() | 返回空列表 []，不抛出异常 |

---

## 9. 与 CCB 命令的映射表

| 方法 | CCB 命令 | 退出码 | 映射 |
|------|----------|--------|------|
| submit() | ask {provider} --background | - | - |
| poll() | pend {provider} | 0 | completed |
| poll() | pend {provider} | 2 | pending |
| poll() | pend {provider} | 1 | error |
| ping() | ccb-ping {provider} | 0 | True |
| list_providers() | ccb-mounted | - | JSON.mounted |

---

## 10. 使用示例

```python
backend = CCBCLIBackend()

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
    elif result.status == "pending":
        print("Still waiting...")
        time.sleep(1)
```

---

## 11. Windows 兼容性设计

```python
import sys

def submit(self, provider: str, prompt: str, context: Optional[Dict] = None) -> TaskHandle:
    cmd = ["ask", provider, "--background", prompt]
    
    kwargs = {
        "capture_output": True,
        "text": True,
        "timeout": 10
    }
    
    # Windows 特殊处理
    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        kwargs["startupinfo"] = startupinfo
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    
    result = subprocess.run(cmd, **kwargs)
    
    return TaskHandle(provider=provider, timestamp=time.time())
```

---

## 12. 关键修复总结（v2 → v3）

| 问题 | v2 设计 | v3 修复 |
|------|---------|---------|
| poll() 退出码 | returncode != 0 → error | EXIT_NO_REPLY(2) → pending |
| 状态判断 | stdout 为空 → pending | 基于退出码映射 |
| submit() 实现 | Popen + DEVNULL | run() 保留输出 |
| 单任务约束 | 隐含 | 明确文档化 |

---

## 13. 未来扩展

- **任务队列:** 为每个 provider 维护队列，串行化请求
- **任务取消:** 支持取消正在处理的任务
- **流式输出:** 支持部分结果返回

---

**设计完成:** 2026-03-28 (v3)
**依赖:** task_models_design.md
**下一步:** 重新提交 Codex 审核
