# Technology Stack Research

**Domain:** Python i18n 国际化与多 AI 协作
**Researched:** 2026-03-28
**Confidence:** HIGH

## Recommended Stack

### Core i18n Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| gettext (stdlib) | Python 3.10+ | 运行时翻译查找 | 行业标准，零依赖，GNU .po/.mo 格式通用，性能优异 |
| Babel | 2.14+ | i18n 工具链与本地化格式化 | 强大的消息提取、CLDR 支持、日期/数字/货币格式化 |

**理由：** gettext 处理运行时字符串翻译，Babel 管理翻译生命周期。这是 2026 年 Python 项目的事实标准组合，两者互补而非互斥。

### Multi-AI Orchestration

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| LangGraph | 0.2+ | 生产级多 AI 编排 | 图状态机架构，持久化执行，人机协作支持，可观测性最佳 |
| CrewAI | 0.51+ | 快速原型与角色协作 | 直观的团队抽象，快速上手，适合业务流程自动化 |

**理由：** LangGraph 用于生产级确定性工作流（GSD 核心流程），CrewAI 用于快速原型验证（研究阶段）。现代架构常混合使用两者。

### Async & HTTP Client

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| asyncio (stdlib) | Python 3.10+ | 异步运行时 | 标准库，CCB 已使用，支持并发 AI 调用 |
| httpx | 0.27+ | 现代 HTTP 客户端 | 同步/异步统一 API，HTTP/2 支持，比 aiohttp 更简洁 |

**理由：** httpx 是 2026 年推荐的 HTTP 客户端，API 设计优于 aiohttp，同时支持同步和异步模式。

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| polib | 1.2+ | .po/.pot 文件解析 | 需要程序化操作翻译文件时（CI/CD 集成） |
| langchain-core | 0.2+ | LLM 抽象层 | 与 LangGraph 配合使用，提供统一的 LLM 接口 |
| pydantic | 2.7+ | 数据验证 | AI 响应结构化验证，配置管理 |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| pybabel | 翻译目录管理 | Babel CLI 工具，用于 extract/init/update/compile |
| pytest | 单元测试 | CCB 已使用，添加 i18n 快照测试 |
| ruff | 代码检查与格式化 | 2026 年标准，替代 flake8/black |

## Installation

```bash
# Core i18n
pip install babel>=2.14

# Multi-AI orchestration (按需选择)
pip install langgraph>=0.2.0 langchain-core>=0.2.0
pip install crewai>=0.51.0

# HTTP client
pip install httpx>=0.27.0

# Supporting
pip install polib>=1.2.0 pydantic>=2.7.0

# Dev dependencies
pip install pytest>=8.0.0 ruff>=0.4.0
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| gettext + Babel | fluent-python | 需要 Mozilla Fluent 格式（更现代的语法），但生态系统较小 |
| LangGraph | AutoGen | 研究型项目，需要对话式多轮协作，不要求确定性执行 |
| httpx | aiohttp | 已有 aiohttp 代码库，迁移成本高于收益 |
| Babel | Django i18n | 项目是 Django 应用（使用内置 i18n 系统） |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| 硬编码字典翻译 | 无法扩展，缺少工具链支持，无复数/性别处理 | gettext + Babel |
| requests | 同步阻塞，2026 年已过时 | httpx（同步/异步统一） |
| 自定义 AI 编排框架 | 重复造轮子，缺少社区支持和最佳实践 | LangGraph 或 CrewAI |
| OpenAI SDK 直接调用 | 供应商锁定，难以切换模型 | langchain-core 抽象层 |

## Stack Patterns by Variant

**如果构建 CLI 工具的 i18n：**
- 使用 gettext + Babel
- 环境变量检测语言（`LANG`, `LC_ALL`）
- 编译 .mo 文件打包到分发包中
- 因为：CLI 需要零依赖运行时，gettext 是标准库

**如果构建多 AI 协作系统：**
- 生产环境使用 LangGraph（确定性、可观测）
- 原型阶段使用 CrewAI（快速验证）
- 使用 langchain-core 抽象 LLM 调用
- 因为：混合策略平衡开发速度和生产可靠性

**如果需要实时 AI 流式响应：**
- 使用 httpx 的 async streaming
- 配合 asyncio.gather 并发多个 AI 调用
- 因为：httpx 原生支持流式响应，API 简洁

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| Babel 2.14+ | Python 3.10+ | 需要 Python 3.8+ 但推荐 3.10+ |
| LangGraph 0.2+ | langchain-core 0.2+ | 强依赖，版本需匹配 |
| httpx 0.27+ | asyncio (stdlib) | 无冲突，推荐 Python 3.10+ |
| gettext (stdlib) | Babel 2.14+ | Babel 生成 gettext 兼容的 .mo 文件 |

## CCB-Specific Integration Notes

**现有技术栈兼容性：**
- CCB 已使用 Python 3.10+，asyncio，subprocess — 完全兼容
- 现有 `lib/i18n.py` 使用字典方案 — 需迁移到 gettext
- 守护进程架构（askd）— 适合集成 LangGraph 持久化执行
- 多提供商支持 — 可用 langchain-core 统一抽象

**推荐迁移路径：**
1. 提取 `i18n_core` 模块（gettext + Babel）
2. 保持 `t(key, **kwargs)` API 契约
3. 添加命名空间支持（`ccb.*`, `gsd.*`）
4. 区分人类文本和协议字符串（永不翻译协议标记）

## Sources

**HIGH Confidence (官方文档与 Context7):**
- [Python gettext documentation](https://python.org) — 标准库官方文档
- [Babel documentation](https://readthedocs.io) — 官方 Babel 文档
- [Phrase i18n guide](https://phrase.com) — Python i18n 最佳实践

**MEDIUM Confidence (行业分析与比较):**
- [Towards AI: Multi-AI Orchestration](https://towardsai.net) — LangGraph/CrewAI/AutoGen 对比
- [iSwift: Agent Framework Comparison](https://iswift.dev) — 生产环境框架选择
- [Crowdin: Python i18n Best Practices](https://crowdin.com) — 2026 年 i18n 工作流

**技术细节验证：**
- [Matt Layman: Python i18n](https://mattlayman.com) — CLI i18n 实现指南
- [Dev.to: httpx vs aiohttp](https://dev.to) — 异步 HTTP 客户端对比

---
*Stack research for: Python i18n 国际化与多 AI 协作*
*Researched: 2026-03-28*
