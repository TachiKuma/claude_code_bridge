# Architecture Research

**Domain:** i18n 国际化系统 + 多 AI 协作系统
**Researched:** 2026-03-28
**Confidence:** HIGH

## Standard Architecture

### System Overview - i18n 架构

```
┌─────────────────────────────────────────────────────────────┐
│                    应用层 (Application)                       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │  CLI    │  │  GSD    │  │  CCB    │  │ Daemon  │        │
│  │ Commands│  │ Agents  │  │ Comm    │  │ Server  │        │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘        │
│       │            │            │            │              │
├───────┴────────────┴────────────┴────────────┴──────────────┤
│                    i18n 抽象层 (i18n Core)                    │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Translation Engine (t() API)                        │   │
│  │  - Namespace routing (ccb.*, gsd.*)                  │   │
│  │  - Locale detection (env, config)                    │   │
│  │  - Fallback chain (zh → en → key)                    │   │
│  └──────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│                    存储层 (Storage)                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│  │ ccb/     │  │ gsd/     │  │ common/  │                   │
│  │ zh.json  │  │ zh.json  │  │ zh.json  │                   │
│  │ en.json  │  │ en.json  │  │ en.json  │                   │
│  └──────────┘  └──────────┘  └──────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

### System Overview - 多 AI 协作架构

```
┌─────────────────────────────────────────────────────────────┐
│                 编排层 (Orchestration)                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐    │
│  │  GSD Orchestrator (Supervisor Pattern)              │    │
│  │  - Task decomposition                               │    │
│  │  - Agent role mapping (designer/reviewer/inspiration)│   │
│  │  - Result aggregation                               │    │
│  └────────────────┬────────────────────────────────────┘    │
│                   │                                          │
├───────────────────┴──────────────────────────────────────────┤
│                 通信层 (Communication)                        │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ CCB CLI  │  │ Async    │  │ Message  │  │ Session  │    │
│  │ Backend  │  │ RPC      │  │ Queue    │  │ Manager  │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘    │
│       │             │             │             │           │
├───────┴─────────────┴─────────────┴─────────────┴───────────┤
│                 提供商层 (Providers)                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ Claude   │  │ Codex    │  │ Gemini   │  │ Droid    │    │
│  │ (designer)│ │(reviewer)│  │(inspiration)│(inspiration)│  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| **i18n Core** | 统一翻译引擎，管理命名空间和语言回退 | Python 模块，字典加载器，t() 函数 |
| **Translation Storage** | 按命名空间组织的翻译文件 | JSON 文件 (ccb/zh.json, gsd/en.json) |
| **Locale Detector** | 检测用户语言偏好 | 环境变量 (CCB_LANG) + 配置文件 |
| **GSD Orchestrator** | 任务分解和 AI 角色分配 | Python 脚本，使用 Supervisor 模式 |
| **CCB CLI Backend** | 包装 ask/pend 命令为结构化 API | Python 类，返回 TaskHandle 对象 |
| **Async RPC** | 守护进程通信协议 | Socket-based JSON RPC |
| **Provider Comm** | 特定 AI 提供商的会话管理 | claude_comm.py, codex_comm.py 等 |
| **Message Queue** | 异步任务队列和状态跟踪 | 文件系统 + 守护进程状态 |

## Recommended Project Structure

### i18n 结构

```
lib/
├── i18n/
│   ├── __init__.py          # 导出 t(), set_locale()
│   ├── core.py              # 翻译引擎核心逻辑
│   ├── loader.py            # JSON 文件加载器
│   └── detector.py          # 语言检测逻辑
├── locales/
│   ├── ccb/
│   │   ├── zh.json          # CCB 中文翻译
│   │   └── en.json          # CCB 英文翻译
│   ├── gsd/
│   │   ├── zh.json          # GSD 中文翻译
│   │   └── en.json          # GSD 英文翻译
│   └── common/
│       ├── zh.json          # 共享翻译（错误消息等）
│       └── en.json
```

### 多 AI 协作结构

```
lib/
├── multi_ai/
│   ├── __init__.py          # 导出 MultiAIBackend
│   ├── backend.py           # 抽象基类
│   ├── ccb_cli_backend.py   # CCB CLI 实现
│   ├── task_handle.py       # TaskHandle/TaskResult 数据类
│   └── role_mapper.py       # 角色到提供商的映射
├── orchestration/
│   ├── supervisor.py        # Supervisor 模式实现
│   └── aggregator.py        # 结果聚合逻辑
```

### Structure Rationale

- **lib/i18n/:** 独立的 i18n 模块，可被 CCB 和 GSD 共享，避免代码重复
- **locales/:** 按命名空间组织翻译文件，支持按需加载，减少内存占用
- **lib/multi_ai/:** 抽象多 AI 后端，支持未来扩展（如 MCP Backend）
- **orchestration/:** 编排逻辑与通信层分离，便于测试和维护

## Architectural Patterns

### Pattern 1: Namespace-Based i18n

**What:** 使用命名空间前缀区分不同模块的翻译键，避免键冲突

**When to use:** 多个子系统共享同一个 i18n 引擎时

**Trade-offs:**
- 优点：清晰的边界，支持按需加载，易于维护
- 缺点：键名稍长，需要约定命名规范

**Example:**
```python
# CCB 模块
t("ccb.daemon.started", port=8080)  # → "守护进程已启动，端口: 8080"

# GSD 模块
t("gsd.research.complete", domain="i18n")  # → "研究完成: i18n"

# 共享消息
t("common.error.file_not_found", path="/tmp/x")  # → "文件未找到: /tmp/x"
```

### Pattern 2: Protocol String Exemption

**What:** 永不翻译协议字符串、命令名、环境变量、JSON 键、完成标记

**When to use:** 任何涉及机器解析的文本

**Trade-offs:**
- 优点：避免破坏日志解析、命令行接口、API 契约
- 缺点：需要明确区分人类可读文本和协议文本

**Example:**
```python
# ✓ 正确：协议标记不翻译
completion_marker = "CCB_DONE"  # 永远是英文

# ✓ 正确：人类消息翻译
user_message = t("ccb.task.completed")  # → "任务已完成"

# ✗ 错误：翻译命令名
command = t("ccb.command.ask")  # 不要这样做！应该硬编码 "ask"
```

### Pattern 3: Hierarchical Supervisor (Orchestrator-Worker)

**What:** 中央编排器分解任务并委派给专门的 Worker AI

**When to use:** 复杂的多步骤工作流，需要集中控制和审计

**Trade-offs:**
- 优点：清晰的任务所有权，易于调试，支持结果聚合
- 缺点：中央编排器可能成为瓶颈，增加延迟

**Example:**
```python
# GSD Orchestrator
orchestrator = GSDSupervisor()

# 分解任务
tasks = [
    Task(role="designer", prompt="设计 i18n 架构"),
    Task(role="inspiration", prompt="提供创意建议"),
    Task(role="reviewer", prompt="评审方案质量"),
]

# 并行执行
results = await orchestrator.execute_parallel(tasks)

# 聚合结果
final_plan = orchestrator.aggregate(results)
```

### Pattern 4: Async Message Passing with TaskHandle

**What:** 使用结构化的 TaskHandle 对象而非解析控制台文本

**When to use:** 需要跟踪异步任务状态和结果时

**Trade-offs:**
- 优点：类型安全，易于测试，避免文本解析错误
- 缺点：需要额外的数据结构定义

**Example:**
```python
@dataclass
class TaskHandle:
    task_id: str
    provider: str
    status: str  # "submitted", "running", "completed", "failed"
    result_path: Path

@dataclass
class TaskResult:
    task_id: str
    success: bool
    output: str
    error: Optional[str] = None

# 使用
backend = CCBCLIBackend()
handle = backend.submit("claude", "研究 i18n 架构")
result = backend.wait(handle)  # 返回 TaskResult
```

## Data Flow

### i18n Request Flow

```
[用户代码调用 t("ccb.daemon.started")]
    ↓
[i18n Core 解析命名空间 "ccb"]
    ↓
[Loader 加载 locales/ccb/{locale}.json]
    ↓
[查找键 "daemon.started"]
    ↓
[应用参数格式化]
    ↓
[返回翻译文本或回退到英文/键名]
```

### 多 AI 协作 Request Flow

```
[GSD 发起研究任务]
    ↓
[Orchestrator 分解为 4 个子任务]
    ↓
[Role Mapper 映射角色到提供商]
    designer → claude
    inspiration → droid, gemini
    reviewer → codex
    ↓
[CCB CLI Backend 调用 ask 命令]
    ↓
[Async RPC 提交到守护进程]
    ↓
[守护进程返回 TaskHandle]
    ↓
[Orchestrator 轮询或等待完成]
    ↓
[收集所有 TaskResult]
    ↓
[Aggregator 合并结果]
    ↓
[返回最终输出]
```

### State Management

**i18n 状态:**
- 当前语言环境存储在全局变量或线程本地存储
- 翻译字典缓存在内存中，按命名空间懒加载
- 配置文件 (~/.ccb/i18n.conf) 持久化用户语言偏好

**多 AI 协作状态:**
- 任务状态存储在 `~/.cache/ccb/tasks/<task_id>.json`
- 守护进程状态存储在 `~/.cache/ccb/askd/state.json`
- 会话文件存储在提供商特定位置 (如 `~/.claude/projects/`)

## Key Data Flows

1. **语言回退链:** zh (用户语言) → en (默认语言) → key (键名本身)
2. **任务委派流:** Orchestrator → Role Mapper → CCB Backend → Daemon → Provider
3. **结果聚合流:** Provider → Daemon → Backend → Orchestrator → Aggregator

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 0-100 用户 | 单进程，内存缓存翻译，同步 AI 调用 |
| 100-10k 用户 | 多进程守护进程，文件系统缓存，异步 AI 调用 |
| 10k+ 用户 | 分布式翻译服务 (API)，消息队列 (Redis/Kafka)，AI 请求池化 |

### Scaling Priorities

1. **第一瓶颈:** 翻译文件加载 → 解决方案：内存缓存 + 懒加载
2. **第二瓶颈:** AI 提供商并发限制 → 解决方案：请求队列 + 速率限制
3. **第三瓶颈:** 守护进程单点故障 → 解决方案：多守护进程 + 负载均衡

## Anti-Patterns

### Anti-Pattern 1: 翻译协议字符串

**What people do:** 将命令名、环境变量、完成标记放入翻译文件

**Why it's wrong:** 破坏日志解析、命令行接口、API 契约，导致系统故障

**Do this instead:**
- 明确区分 `HUMAN_TEXT` 和 `PROTOCOL_TEXT`
- 协议字符串硬编码为常量
- 添加 CI 检查防止误翻译

### Anti-Pattern 2: 单体翻译文件

**What people do:** 将所有翻译放在一个巨大的 `messages.json` 文件中

**Why it's wrong:**
- 加载缓慢，内存占用高
- 合并冲突频繁
- 难以按模块维护

**Do this instead:**
- 按命名空间拆分文件 (ccb/, gsd/, common/)
- 支持按需加载
- 使用目录结构组织

### Anti-Pattern 3: 解析控制台文本

**What people do:** 使用正则表达式解析 AI 输出的控制台文本

**Why it's wrong:**
- 脆弱，格式变化导致解析失败
- 难以测试
- 不支持结构化数据

**Do this instead:**
- 使用结构化的 TaskHandle/TaskResult
- 返回 JSON 或数据类
- 避免依赖文本格式

### Anti-Pattern 4: 紧耦合的 AI 调用

**What people do:** 直接在业务逻辑中调用 `subprocess.run(["ask", "claude", ...])`

**Why it's wrong:**
- 难以测试（需要真实 AI 提供商）
- 无法切换后端实现
- 错误处理困难

**Do this instead:**
- 使用 MultiAIBackend 抽象层
- 支持 Mock Backend 用于测试
- 统一错误处理和重试逻辑

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Claude API | CCB Daemon + Session Files | 通过 ~/.claude/projects/ 管理会话 |
| Codex API | CCB Daemon + Session Files | 通过 ~/.codex/sessions/ 管理会话 |
| Gemini API | CCB Daemon + Session Files | 通过 ~/.gemini/sessions/ 管理会话 |
| Translation Services | 未来扩展：API 调用 | 可集成 DeepL/Google Translate 用于自动翻译 |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| i18n Core ↔ Application | 函数调用 (t()) | 同步，低延迟 |
| Orchestrator ↔ Backend | 方法调用 (submit/wait) | 异步，返回 TaskHandle |
| Backend ↔ Daemon | Socket RPC (JSON) | 异步，支持并发 |
| Daemon ↔ Provider | Terminal 注入 + 日志解析 | 异步，基于文件系统 |

## Sources

**i18n 架构:**
- [Crowdin: Python i18n gettext vs custom dictionary](https://crowdin.com)
- [SimpleLocalize: i18n best practices 2026](https://simplelocalize.io)
- [Locize: i18n architecture patterns](https://locize.com)

**多 AI 协作架构:**
- [AI Agents Directory: Multi-agent orchestration patterns](https://aiagentsdirectory.com)
- [Promethium AI: Agent orchestration architecture](https://promethium.ai)
- [Microsoft: AutoGen multi-agent framework](https://microsoft.com)
- [Devm.io: AI agent communication protocols](https://devm.io)
- [Smythos: Message passing architecture](https://smythos.com)

---
*Architecture research for: i18n 国际化系统 + 多 AI 协作系统*
*Researched: 2026-03-28*
