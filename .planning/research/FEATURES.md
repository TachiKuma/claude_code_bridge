# Feature Research

**Domain:** i18n 国际化系统 + 多 AI 协作系统
**Researched:** 2026-03-28
**Confidence:** HIGH

## Feature Landscape

### Table Stakes (基本功能 - 用户期望具备)

i18n 国际化系统必备功能：

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| 字符串外部化 | 所有 i18n 系统的基础，硬编码文本无法翻译 | LOW | CCB 已有基础实现（`MESSAGES` 字典） |
| 语言环境检测 | 用户期望自动使用系统语言 | LOW | 通过 `LANG`/`LC_ALL` 环境变量检测 |
| 参数化消息格式化 | 避免字符串拼接，支持不同语言的语法顺序 | LOW | CCB 已支持 `t(key, **kwargs)` |
| UTF-8 全栈支持 | 支持中文、日文、阿拉伯文等多字节字符 | LOW | Python 3 默认支持 |
| 回退机制 | 缺失翻译时显示默认语言（通常是英文） | LOW | 防止显示原始键名 |
| 区域感知格式化 | 日期、时间、数字、货币按用户区域格式化 | MEDIUM | 需要 `locale` 或 `babel` 库 |

多 AI 协作系统必备功能：

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| 提供商抽象 | 统一接口访问不同 AI（Claude/Codex/Gemini） | LOW | CCB 已有 `providers.py` 实现 |
| 异步消息传递 | 避免阻塞，AI 响应时间不可预测 | MEDIUM | CCB 已有 `askd` 守护进程架构 |
| 会话管理 | 跟踪每个 AI 的对话上下文和状态 | MEDIUM | CCB 已有 `session_utils.py` |
| 任务分发 | 将复杂任务拆解并分配给合适的 AI | MEDIUM | GSD 已有 Agent 工具支持 |
| 结果聚合 | 收集多个 AI 的响应并整合 | MEDIUM | 需要等待机制（`pend` 命令） |
| 错误处理与重试 | AI 调用可能失败，需要优雅降级 | MEDIUM | 超时检测、重试逻辑 |

### Differentiators (差异化功能 - 竞争优势)

i18n 国际化系统差异化功能：

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| 命名空间支持 | 避免键冲突，支持 GSD/CCB 共享 i18n 核心 | LOW | `ccb.*` vs `gsd.*` 前缀 |
| 外部翻译目录 | 用户可自定义翻译，无需修改代码 | MEDIUM | 从 `~/.ccb/i18n/` 加载用户翻译 |
| 协议字符串保护 | 永不翻译命令名、环境变量、完成标记 | LOW | 区分人类文本和机器协议 |
| CI/CD 集成 | 自动检测缺失键和孤立键 | MEDIUM | 防止翻译漂移 |
| 伪本地化测试 | 自动生成测试翻译，发现 UI 溢出问题 | MEDIUM | 文本扩展 30% 测试 |
| 上下文感知翻译 | 为翻译键提供元数据和截图 | HIGH | 帮助 AI/人类理解使用场景 |
| 动态翻译加载 | 运行时从 API/CDN 获取翻译 | HIGH | 无需重新部署即可更新翻译 |

多 AI 协作系统差异化功能：

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| 角色专业化 | 不同 AI 扮演不同角色（设计师/评审/创意） | LOW | CCB_ROLES 映射表已定义 |
| 并行任务执行 | 同时向多个 AI 发送任务，提升效率 | MEDIUM | 后台模式 `ask codex "..." &` |
| 层级协调 | 主协调者分解任务，分配给专家 AI | HIGH | GSD orchestrator 模式 |
| 共享状态管理 | 多个 AI 访问共享上下文和中间结果 | HIGH | 任务图或内存层 |
| 质量评分系统 | 自动评估 AI 输出质量，选择最佳方案 | MEDIUM | Rubric A 评分标准 |
| 结构化任务句柄 | 返回 `TaskHandle` 对象而非解析文本 | MEDIUM | 避免脆弱的文本解析 |
| 事件驱动架构 | AI 响应触发后续任务，而非轮询 | HIGH | 提升响应速度和效率 |
| 可观测性平台 | 追踪 AI 推理过程、成本、性能 | HIGH | 企业级生产需求 |


### Anti-Features (反功能 - 故意不构建)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| 自动机器翻译所有文本 | 快速支持多语言 | 质量差，破坏品牌形象，技术术语误译 | 混合 AI/人工工作流，关键内容人工审核 |
| 实时翻译所有 AI 响应 | 让非英语用户看懂 AI 输出 | AI 输出包含代码/命令，翻译会破坏功能 | 仅翻译用户界面，保持 AI 输出原样 |
| 支持所有语言 | 覆盖全球市场 | 维护成本高，测试复杂度指数增长 | 先聚焦中英文，按需扩展 |
| 翻译日志和错误消息 | 方便本地用户调试 | 破坏在线搜索，技术支持困难 | 保持技术日志英文，翻译用户提示 |
| 完全自动化 AI 协作 | 无需人工干预 | 缺乏控制，成本失控，质量无保障 | Human-in-the-loop 监控和审批 |
| 所有任务都用多 AI | 最大化 AI 能力 | 简单任务浪费资源，增加延迟 | 仅复杂任务使用多 AI 协作 |
| 实时同步所有 AI 状态 | 保持一致性 | 性能开销大，复杂度高 | 事件驱动的最终一致性 |
| 自动选择最佳 AI | 智能路由 | 难以预测，调试困难 | 显式角色映射，用户可控 |


## Feature Dependencies

```
i18n 系统依赖关系：

[字符串外部化]
    └──requires──> [语言环境检测]
                       └──requires──> [回退机制]

[参数化消息格式化] ──requires──> [字符串外部化]

[命名空间支持] ──enhances──> [字符串外部化]

[协议字符串保护] ──requires──> [字符串外部化]

[外部翻译目录] ──requires──> [命名空间支持]

[CI/CD 集成] ──requires──> [字符串外部化]

[动态翻译加载] ──conflicts──> [静态编译翻译]


多 AI 协作系统依赖关系：

[提供商抽象]
    └──requires──> [异步消息传递]
                       └──requires──> [会话管理]

[任务分发] ──requires──> [提供商抽象]

[结果聚合] ──requires──> [任务分发]

[角色专业化] ──requires──> [提供商抽象]

[并行任务执行] ──requires──> [异步消息传递]

[层级协调] ──requires──> [任务分发] + [结果聚合]

[质量评分系统] ──requires──> [结果聚合]

[结构化任务句柄] ──enhances──> [任务分发] + [结果聚合]

[事件驱动架构] ──conflicts──> [轮询模式]

[可观测性平台] ──enhances──> [所有协作功能]


GSD-CCB 集成依赖：

[GSD 使用 CCB 多 AI] ──requires──> [CCB CLI Backend] 或 [CCB MCP Backend]

[CCB CLI Backend] ──requires──> [结构化任务句柄]

[共享 i18n 核心] ──requires──> [命名空间支持]
```

### Dependency Notes

- **字符串外部化 → 语言环境检测 → 回退机制**: 必须按顺序实现，回退机制依赖检测逻辑
- **命名空间支持增强字符串外部化**: 允许 GSD 和 CCB 共享 i18n 核心而不冲突
- **协议字符串保护依赖字符串外部化**: 需要区分哪些是人类文本，哪些是协议标记
- **动态翻译加载与静态编译冲突**: 必须选择一种策略，不能混用
- **提供商抽象 → 异步消息 → 会话管理**: 多 AI 协作的基础架构链
- **层级协调需要任务分发和结果聚合**: 协调者必须能分配任务并收集结果
- **事件驱动与轮询冲突**: 架构选择，事件驱动更高效但实现复杂
- **结构化任务句柄增强分发和聚合**: 避免脆弱的文本解析，提供类型安全


## MVP Definition

### Launch With (v1 - 可行性验证)

i18n 国际化 MVP：

- [ ] 提取共享 i18n_core 模块 — 保持 `t(key, **kwargs)` API 契约
- [ ] 命名空间支持 (`ccb.*`, `gsd.*`) — 避免键冲突
- [ ] 协议字符串保护机制 — 永不翻译命令名、环境变量、完成标记
- [ ] 基础中英文翻译覆盖 — 核心用户界面文本
- [ ] 环境变量语言检测 — 自动使用用户首选语言

多 AI 协作 MVP：

- [ ] CCBCLIBackend 实现 — 包装现有 `ask/pend/ping` 命令
- [ ] 结构化 TaskHandle/TaskResult — 避免解析控制台文本
- [ ] 基础角色映射 (designer/reviewer/inspiration) — 使用 CCB_ROLES 表
- [ ] 并行任务提交 — 后台模式支持
- [ ] 简单结果聚合 — 等待所有任务完成并收集响应

### Add After Validation (v1.x - 生产就绪)

i18n 增强功能：

- [ ] 外部翻译目录支持 — 用户可自定义翻译
- [ ] CI/CD 键检查 — 自动检测缺失键和孤立键
- [ ] 伪本地化测试 — 发现 UI 布局问题
- [ ] 区域感知格式化 — 日期、时间、数字本地化

多 AI 协作增强：

- [ ] 质量评分系统 — 使用 Rubric A 评估输出
- [ ] 层级协调模式 — 主协调者分解复杂任务
- [ ] 错误重试机制 — 优雅处理 AI 调用失败
- [ ] 会话绑定 — 明确的工作区/会话文件管理

### Future Consideration (v2+ - 高级功能)

- [ ] 动态翻译加载 — 运行时从 API 获取翻译
- [ ] 上下文感知翻译 — 为翻译键提供元数据
- [ ] CCB MCP Backend — 使用 MCP 服务器替代 CLI
- [ ] 事件驱动架构 — 替代轮询模式
- [ ] 可观测性平台 — 追踪 AI 推理和成本
- [ ] 共享状态管理 — 任务图或内存层
- [ ] 更多语言支持 — 日语、韩语、德语等


## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| 提取共享 i18n_core | HIGH | LOW | P1 |
| 命名空间支持 | HIGH | LOW | P1 |
| 协议字符串保护 | HIGH | LOW | P1 |
| CCBCLIBackend | HIGH | MEDIUM | P1 |
| 结构化 TaskHandle | HIGH | MEDIUM | P1 |
| 基础中英文翻译 | HIGH | MEDIUM | P1 |
| 角色映射 | MEDIUM | LOW | P1 |
| 并行任务提交 | MEDIUM | LOW | P1 |
| 环境变量检测 | MEDIUM | LOW | P1 |
| 结果聚合 | MEDIUM | MEDIUM | P1 |
| 外部翻译目录 | MEDIUM | MEDIUM | P2 |
| CI/CD 键检查 | MEDIUM | MEDIUM | P2 |
| 质量评分系统 | MEDIUM | MEDIUM | P2 |
| 错误重试机制 | MEDIUM | MEDIUM | P2 |
| 会话绑定 | MEDIUM | MEDIUM | P2 |
| 伪本地化测试 | LOW | MEDIUM | P2 |
| 区域感知格式化 | LOW | MEDIUM | P2 |
| 层级协调模式 | MEDIUM | HIGH | P2 |
| 动态翻译加载 | LOW | HIGH | P3 |
| 上下文感知翻译 | LOW | HIGH | P3 |
| CCB MCP Backend | LOW | HIGH | P3 |
| 事件驱动架构 | MEDIUM | HIGH | P3 |
| 可观测性平台 | LOW | HIGH | P3 |
| 共享状态管理 | MEDIUM | HIGH | P3 |

**Priority key:**
- P1: 必须具备才能启动（MVP 可行性验证）
- P2: 应该具备，生产就绪所需
- P3: 很好具备，未来考虑


## Competitor Feature Analysis

### i18n 系统对比

| Feature | GNU gettext | i18next | CCB 现有实现 | 我们的方案 |
|---------|-------------|---------|--------------|------------|
| 字符串外部化 | PO 文件 | JSON/YAML | Python 字典 | JSON + 命名空间 |
| 参数化 | C 格式化 | 插值语法 | Python f-string | 保持 `**kwargs` |
| 复数规则 | 内置 | 内置 | 不支持 | 未来添加 |
| 上下文 | msgctxt | 键前缀 | 无 | 元数据支持 |
| 工具链 | xgettext | i18next-parser | 手动 | CI/CD 自动化 |

### 多 AI 协作系统对比

| Feature | LangGraph | AutoGen | CrewAI | 我们的方案 |
|---------|-----------|---------|--------|------------|
| 任务编排 | 图状态机 | 对话流 | 角色分配 | 角色映射 + CLI |
| 并行执行 | 支持 | 支持 | 支持 | 后台模式 |
| 状态管理 | 图状态 | 内存 | 共享上下文 | 会话文件 |
| 可观测性 | LangSmith | 日志 | 内置 | 文件日志 |
| 集成复杂度 | 高（需重构） | 高（新框架） | 中（Python SDK） | 低（CLI 包装） |

**我们的优势：**
- 利用 CCB 现有基础设施（守护进程、会话管理）
- 渐进式集成，无需重写 GSD
- CLI 优先，适合开发者工具
- 轻量级，避免重型框架依赖


## Sources

### i18n 国际化系统研究来源

- [Phrase - i18n Best Practices](https://phrase.com)
- [Crowdin - CLI Internationalization](https://crowdin.com)
- [Localazy - i18n Features 2026](https://localazy.com)
- [SimpleLocalize - Modern i18n Systems](https://simplelocalize.io)
- [Locize - i18n Essential Features](https://locize.com)

### 多 AI 协作系统研究来源

- [Botpress - Multi-Agent Orchestration](https://botpress.com)
- [Moveworks - AI Agent Collaboration Patterns](https://moveworks.com)
- [IBM - AI Orchestration](https://ibm.com)
- [Domo - AI Agent Orchestration](https://domo.com)
- [RTInsights - Multi-AI Collaboration 2026](https://rtinsights.com)

### 关键洞察

**i18n 系统 (2026):**
- 从简单字符串替换演进到 AI 驱动的上下文感知翻译
- CI/CD 集成成为标配，并行本地化取代顺序流程
- 协议字符串保护是 CLI 工具的关键差异点
- 伪本地化测试可提前发现 30% 的 UI 问题

**多 AI 协作 (2026):**
- 从单一 AI 能力转向协调编排策略
- 角色专业化优于通用 AI，提升任务质量
- 事件驱动架构取代轮询，提升响应速度
- Human-in-the-loop 监控是企业级部署的必要条件
- 可观测性平台对生产环境至关重要

---
*Feature research for: GSD & CCB i18n + Multi-AI Collaboration*
*Researched: 2026-03-28*
