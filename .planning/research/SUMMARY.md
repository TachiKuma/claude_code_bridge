# Project Research Summary

**Project:** CCB i18n 国际化 + 多 AI 协作系统
**Domain:** CLI 工具国际化与多 AI 编排
**Researched:** 2026-03-28
**Confidence:** HIGH

## Executive Summary

本项目旨在为 CCB（Claude Code Bridge）和 GSD（Get Shit Done）构建共享的 i18n 国际化系统，并优化多 AI 协作架构。研究表明，成功的 CLI 工具国际化需要使用 gettext + Babel 标准工具链，配合命名空间隔离和协议字符串保护机制。多 AI 协作系统应采用 LangGraph 进行生产级编排，使用结构化 TaskHandle 替代脆弱的文本解析，并通过角色专业化提升输出质量。

推荐的实施路径是：先建立共享 i18n_core 模块（保持现有 `t()` API 契约），添加命名空间支持避免 CCB/GSD 键冲突，然后实现 CCBCLIBackend 包装现有 ask/pend 命令为结构化接口。关键风险包括协议字符串被误翻译（会破坏跨进程通信）、多 AI 协作中的上下文崩溃（信息在传递中丢失）、以及会话文件竞态条件（并发写入导致损坏）。

缓解策略包括：在架构设计阶段就明确区分人类文本和协议常量，使用 CI 检查防止误翻译；实现结构化 TaskHandle 对象显式传递任务状态；采用原子写入和文件锁机制保护会话文件。研究置信度高，基于官方文档、行业最佳实践和项目代码库分析。

## Key Findings

### Recommended Stack

Python i18n 的事实标准是 gettext（标准库）+ Babel（工具链），这一组合提供零依赖运行时、强大的消息提取、CLDR 本地化支持。多 AI 编排推荐 LangGraph（生产级确定性工作流）和 CrewAI（快速原型验证）混合使用。HTTP 客户端应使用 httpx 替代过时的 requests，支持同步/异步统一 API。

**Core technologies:**
- **gettext (stdlib)**: 运行时翻译查找 — 行业标准，零依赖，GNU .po/.mo 格式通用
- **Babel 2.14+**: i18n 工具链与本地化格式化 — 强大的消息提取、日期/数字/货币格式化
- **LangGraph 0.2+**: 生产级多 AI 编排 — 图状态机架构，持久化执行，可观测性最佳
- **httpx 0.27+**: 现代 HTTP 客户端 — 同步/异步统一 API，HTTP/2 支持
- **pydantic 2.7+**: 数据验证 — AI 响应结构化验证，配置管理

### Expected Features

**Must have (table stakes):**
- 字符串外部化与参数化格式化 — 所有 i18n 系统的基础
- 语言环境自动检测（环境变量） — 用户期望自动使用系统语言
- 回退机制（zh → en → key） — 防止显示原始键名
- 提供商抽象与异步消息传递 — 统一接口访问不同 AI
- 会话管理与任务分发 — 跟踪对话上下文，拆解复杂任务
- 结果聚合与错误重试 — 收集多 AI 响应，优雅处理失败

**Should have (competitive):**
- 命名空间支持（ccb.*, gsd.*） — 避免键冲突，支持共享 i18n 核心
- 协议字符串保护机制 — 永不翻译命令名、环境变量、完成标记
- 外部翻译目录支持 — 用户可自定义翻译，无需修改代码
- 角色专业化（designer/reviewer/inspiration） — 不同 AI 扮演不同角色
- 并行任务执行 — 同时向多个 AI 发送任务，提升效率
- 质量评分系统 — 使用 Rubric A 评估输出，选择最佳方案

**Defer (v2+):**
- 动态翻译加载（运行时从 API 获取） — 无需重新部署即可更新翻译
- 上下文感知翻译（元数据和截图） — 帮助 AI/人类理解使用场景
- CCB MCP Backend — 使用 MCP 服务器替代 CLI
- 事件驱动架构 — 替代轮询模式，提升响应速度
- 可观测性平台 — 追踪 AI 推理过程、成本、性能

### Architecture Approach

系统采用分层架构：i18n Core 提供统一翻译引擎（命名空间路由、语言检测、回退链），Translation Storage 按命名空间组织 JSON 文件（ccb/zh.json, gsd/en.json），GSD Orchestrator 使用 Supervisor 模式分解任务并分配给专家 AI，CCB CLI Backend 包装 ask/pend 命令为结构化 API（返回 TaskHandle 对象），Async RPC 通过守护进程实现跨进程通信。

**Major components:**
1. **i18n Core** — 统一翻译引擎，管理命名空间和语言回退，提供 t() API
2. **CCB CLI Backend** — 包装 ask/pend 命令为结构化 API，返回 TaskHandle 对象
3. **GSD Orchestrator** — 任务分解和 AI 角色分配，使用 Supervisor 模式
4. **Translation Storage** — 按命名空间组织的翻译文件（ccb/, gsd/, common/）
5. **Async RPC** — 守护进程通信协议，支持并发 AI 调用

### Critical Pitfalls

1. **协议字符串被误翻译** — 在架构设计阶段明确区分人类文本和协议常量，添加 CI 检查防止 `t()` 包装协议标记
2. **多 AI 协作中的上下文崩溃** — 实现结构化 TaskHandle 对象，显式传递原始目标、当前状态、已完成子任务
3. **硬编码字符串散落导致翻译不完整** — 使用自动化工具扫描代码库，建立翻译覆盖率指标，纳入 CI 检查
4. **多 AI 协作的"协调税"爆炸** — 为每个 AI 定义明确专长领域，实现模型路由，限制并行 AI 数量，添加 token 消耗监控
5. **会话文件竞态条件** — 实现原子性会话写入（临时文件 → 原子重命名），使用进程级文件锁，为每个提供商使用独立会话目录

## Implications for Roadmap

基于研究，建议分 4 个阶段实施：

### Phase 1: i18n 核心架构
**Rationale:** 必须先建立共享 i18n 基础设施，避免后续重复工作和架构返工
**Delivers:** 共享 i18n_core 模块，命名空间支持，协议字符串保护机制
**Addresses:** 字符串外部化、语言检测、回退机制、命名空间支持
**Avoids:** 协议字符串被误翻译、硬编码字符串散落

### Phase 2: 多 AI 协作集成
**Rationale:** 在 i18n 基础上构建多 AI 后端，利用现有守护进程架构
**Delivers:** CCBCLIBackend 实现，结构化 TaskHandle/TaskResult，角色映射
**Uses:** asyncio、httpx、pydantic（数据验证）
**Implements:** CCB CLI Backend、Role Mapper 组件
**Avoids:** 上下文崩溃、会话竞态条件

### Phase 3: 翻译实施与测试
**Rationale:** 在架构稳定后进行大规模翻译迁移，避免重复工作
**Delivers:** CCB/GSD 核心模块中英文翻译，伪本地化测试，CI/CD 集成
**Addresses:** 基础中英文翻译覆盖、外部翻译目录支持、CI/CD 键检查
**Avoids:** 文本扩展破坏 UI、字符串拼接破坏翻译

### Phase 4: 生产优化
**Rationale:** 基于实际使用数据优化性能和质量
**Delivers:** 质量评分系统，错误重试机制，性能监控
**Addresses:** 质量评分系统、层级协调模式、错误重试机制
**Avoids:** 协调税爆炸

### Phase Ordering Rationale

- **Phase 1 优先**：i18n 是基础设施，必须先建立，否则后续所有用户界面代码都需要返工
- **Phase 2 依赖 Phase 1**：多 AI 协作的用户提示和错误消息需要 i18n 支持
- **Phase 3 依赖 Phase 1+2**：只有架构稳定后才能大规模翻译，避免翻译文件频繁变更
- **Phase 4 最后**：需要真实使用数据才能有效优化，过早优化浪费资源

### Research Flags

需要深入研究的阶段：
- **Phase 2**：会话文件锁定机制需要跨平台测试（Windows/Linux/macOS），可能需要研究特定平台 API
- **Phase 4**：质量评分系统的 Rubric 设计需要实际案例验证，可能需要迭代调整

标准模式阶段（跳过研究）：
- **Phase 1**：gettext + Babel 是成熟工具链，文档完善，实现路径清晰
- **Phase 3**：翻译工作流是标准流程，无需额外研究

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | 基于官方文档（Python gettext、Babel）和行业标准（LangGraph、httpx） |
| Features | HIGH | 基于多个 i18n 平台（Phrase、Crowdin）和 AI 编排框架（LangGraph、CrewAI）的最佳实践 |
| Architecture | HIGH | 基于 CCB 现有代码库分析和标准分层架构模式 |
| Pitfalls | HIGH | 基于项目 CONCERNS.md 已知问题和多源验证的常见错误 |

**Overall confidence:** HIGH

### Gaps to Address

- **复数形式处理**：研究未深入探讨复数规则（ngettext），需要在 Phase 3 实施时补充
- **跨平台文件锁**：Windows/Linux/macOS 的文件锁定 API 差异需要在 Phase 2 实施时验证
- **LangGraph 学习曲线**：团队可能需要时间熟悉图状态机概念，建议先用 CrewAI 快速原型验证
- **翻译质量保证**：需要在 Phase 3 确定翻译审核流程（人工审核 vs AI 辅助）

## Sources

### Primary (HIGH confidence)
- Python gettext documentation (python.org) — 标准库官方文档
- Babel documentation (readthedocs.io) — 官方 Babel 文档
- LangGraph documentation — 多 AI 编排架构
- CCB 项目代码库 (.planning/codebase/CONCERNS.md, lib/i18n.py) — 现有实现和已知问题

### Secondary (MEDIUM confidence)
- Phrase i18n guide (phrase.com) — Python i18n 最佳实践
- Crowdin CLI Internationalization (crowdin.com) — CLI 工具 i18n 模式
- Towards AI: Multi-AI Orchestration (towardsai.net) — LangGraph/CrewAI/AutoGen 对比
- SimpleLocalize i18n Pitfalls (simplelocalize.io) — 常见错误和反模式

### Tertiary (MEDIUM confidence)
- AI Agents Directory (aiagentsdirectory.com) — 多 AI 协作模式
- Localazy i18n Features (localazy.com) — 现代 i18n 系统特性
- RTInsights Multi-AI Collaboration (rtinsights.com) — 2026 年协作趋势

---
*Research completed: 2026-03-28*
*Ready for roadmap: yes*
