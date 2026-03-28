# TaskHandle 和 TaskResult 数据结构设计

**设计日期:** 2026-03-28
**需求:** ARCH-03
**用户决策:** D-09, D-10

## 概述

为 GSD 多 AI 协作提供结构化的任务传递机制，避免解析控制台文本，使用类型化对象传递任务状态。

## 1. TaskHandle 数据结构

TaskHandle 用于跟踪提交的异步任务，提供唯一标识和元数据。

### 定义

```python
from dataclasses import dataclass

@dataclass
class TaskHandle:
    """任务句柄，用于跟踪提交的任务"""
    task_id: str          # 唯一任务标识符
    provider: str         # AI 提供商名称
    timestamp: float      # 提交时间戳（Unix 时间，秒）
```

### 字段说明

**task_id: str**
- 唯一标识符，格式: `{provider}_{timestamp_ms}`
- 示例: `"codex_1711234567890"`
- 生成方式: `f"{provider}_{int(time.time() * 1000)}"`
- 用途: 关联 submit() 和 poll() 调用

**provider: str**
- AI 提供商名称
- 有效值: `["codex", "droid", "gemini", "claude"]`
- 用途: 确定使用哪个 pend 命令（cpend, dpend, gpend）

**timestamp: float**
- 提交时间，Unix 时间戳（秒）
- 生成方式: `time.time()`
- 用途: 超时检测、日志记录、调试

## 2. TaskResult 数据结构

TaskResult 包含任务执行状态和输出，支持三种状态：pending、completed、error。

### 定义

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class TaskResult:
    """任务结果，包含执行状态和输出"""
    task_id: str                    # 对应的任务 ID
    status: str                     # 状态：pending, completed, error
    output: Optional[str] = None    # 成功时的输出内容
    error: Optional[str] = None     # 失败时的错误信息
```

### 字段说明

**task_id: str**
- 与 TaskHandle.task_id 对应
- 用途: 关联任务句柄和结果

**status: str**
- 三种状态值:
  - `"pending"`: 任务仍在处理中，output 和 error 均为 None
  - `"completed"`: 任务成功完成，output 包含结果，error 为 None
  - `"error"`: 任务失败，error 包含错误信息，output 为 None

**output: Optional[str]**
- AI 的回复内容
- 仅当 status="completed" 时有值
- 来源: pend 命令的 stdout

**error: Optional[str]**
- 错误描述信息
- 仅当 status="error" 时有值
- 来源: pend 命令的 stderr 或返回码非 0

## 3. 状态转换图

```
[submit()] → TaskHandle(task_id, provider, timestamp)
                ↓
[poll()]      → TaskResult(status="pending", output=None, error=None)
                ↓
[poll()]      → TaskResult(status="completed", output="...", error=None)
                或
[poll()]      → TaskResult(status="error", output=None, error="...")
```

状态转换规则:
- pending → completed: pend 命令返回非空 stdout
- pending → error: pend 命令返回码非 0 或超时
- completed/error 为终态，不再转换

## 4. 错误处理策略（D-10）

**设计原则:** 不抛出异常，所有错误通过 TaskResult(status="error") 返回。

### 错误类型

| 错误场景 | error 字段内容 | 示例 |
|---------|---------------|------|
| 提供商不可用 | `"Provider {provider} not available"` | `"Provider codex not available"` |
| 超时 | `"Timeout waiting for {provider} reply"` | `"Timeout waiting for droid reply"` |
| 命令执行失败 | `"Command failed: {stderr}"` | `"Command failed: connection refused"` |

### 接口一致性

- `poll()` 始终返回 TaskResult，不抛出异常
- 调用者通过检查 `result.status` 判断成功或失败
- 简化错误处理逻辑，避免 try-except 嵌套

## 5. 类型注解

完整的类型定义：

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class TaskHandle:
    task_id: str
    provider: str
    timestamp: float

@dataclass
class TaskResult:
    task_id: str
    status: str
    output: Optional[str] = None
    error: Optional[str] = None
```

## 6. 使用示例

### 提交任务

```python
handle = backend.submit("codex", "Review this code")
# TaskHandle(
#     task_id="codex_1711234567890",
#     provider="codex",
#     timestamp=1711234567.89
# )
```

### 轮询结果（pending）

```python
result = backend.poll(handle)
# TaskResult(
#     task_id="codex_1711234567890",
#     status="pending",
#     output=None,
#     error=None
# )
```

### 轮询结果（completed）

```python
result = backend.poll(handle)
# TaskResult(
#     task_id="codex_1711234567890",
#     status="completed",
#     output="Code looks good. Consider adding error handling.",
#     error=None
# )
```

### 轮询结果（error）

```python
result = backend.poll(handle)
# TaskResult(
#     task_id="codex_1711234567890",
#     status="error",
#     output=None,
#     error="Provider timeout"
# )
```

### 错误处理模式

```python
result = backend.poll(handle)
if result.status == "completed":
    print(f"Success: {result.output}")
elif result.status == "error":
    print(f"Error: {result.error}")
else:
    print("Still pending...")
```

## 7. 与现有 CCB 命令的映射

| 数据结构字段 | CCB 命令 | 说明 |
|------------|---------|------|
| TaskHandle.provider | `ask {provider}` | 第一个参数 |
| TaskHandle.task_id | 生成 | 客户端生成，非 CCB 返回 |
| TaskResult.output | `{provider[0]}pend` stdout | 标准输出 |
| TaskResult.error | `{provider[0]}pend` stderr | 标准错误或返回码非 0 |
| TaskResult.status | 推断 | 根据 returncode 和 stdout 判断 |

## 8. 序列化支持

dataclass 自动支持序列化：

```python
from dataclasses import asdict
import json

# 转换为字典
handle_dict = asdict(handle)
# {'task_id': 'codex_1711234567890', 'provider': 'codex', 'timestamp': 1711234567.89}

# JSON 序列化
json_str = json.dumps(asdict(handle))
# '{"task_id": "codex_1711234567890", "provider": "codex", "timestamp": 1711234567.89}'

# 用途: 日志记录、调试、持久化
```

## 9. 设计权衡

| 决策 | 选择 | 备选方案 | 理由 |
|-----|------|---------|------|
| 数据结构类型 | dataclass | namedtuple, dict | 类型安全、IDE 支持、可扩展 |
| 错误处理 | 返回 error 字段 | 抛出异常 | 接口一致性（D-10） |
| task_id 格式 | `{provider}_{ms}` | UUID | 可读性、包含提供商信息 |
| status 值 | 字符串 | 枚举 | 简单、易于序列化 |

## 10. 未来扩展

预留扩展点：

- **TaskHandle.context**: 可选字典，传递文件路径、项目信息
- **TaskResult.metadata**: 可选字典，包含执行时间、token 使用量
- **TaskResult.partial_output**: 流式输出支持

当前设计保持最小化，扩展时添加可选字段不破坏兼容性。

---

**设计完成:** 2026-03-28
**下一步:** 设计 CCBCLIBackend 接口，使用这些数据结构
