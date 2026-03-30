# GSD & CCB 国际化与多 AI 协作可行性研究

## What This Is

这是一个可行性研究项目，探索两个方向：
1. 为 GSD (Get Shit Done) 和 CCB (Claude Code Bridge) 进行 i18n 国际化改造
2. 让 GSD 在 CCB 环境中利用多 AI 协作能力提升工作效率

最终交付完整的技术方案文档和原型验证。

## Core Value

**通过国际化和多 AI 协作，让 GSD 和 CCB 能够服务更广泛的用户群体，并显著提升复杂任务的执行质量。**

## Requirements

### Validated

- ✓ CCB 已有 i18n.py 实现（支持中英文） — existing
- ✓ CCB 支持多 AI 提供商（Claude、Codex、Gemini、Droid） — existing
- ✓ GSD 使用 Agent 工具进行子任务分发 — existing

### Active

- [ ] 构建原型验证关键技术点
- [ ] 编写完整的技术方案文档

### Validated in Phase 1

- ✓ 分析 GSD 和 CCB 代码库，识别需要国际化的文本 — Phase 1: 代码库分析 (2026-03-28)
  - CCB: 6471 个字符串
  - GSD: 3402 个字符串
  - 分类: 520 个协议字符串, 9029 个人类文本

### Validated in Phase 2

- ✓ 设计统一的 i18n 架构框架 — Phase 2: 架构设计 (2026-03-28)
  - i18n_core 保持 `t(key, **kwargs)` 契约，并增加 `ccb.*` / `gsd.*` 命名空间和回退机制
- ✓ 设计 GSD 利用 CCB 多 AI 协作的集成方案 — Phase 2: 架构设计 (2026-03-28)
  - 明确 `CCBCLIBackend`、`TaskHandle` / `TaskResult` 和协议字符串保护机制

### Validated in Phase 3

- ✓ 评估国际化改造的工作量和技术风险 — Phase 3: 风险评估 (2026-03-30)
  - 协议白名单扩展到 300 项，采用 `CI 检查 + 运行时验证` 双层保护
  - i18n 完整实施估算 536 小时，建议按 643 小时缓冲口径排期
- ✓ 评估多 AI 集成的工作量和技术复杂度 — Phase 3: 风险评估 (2026-03-30)
  - 明确同 provider 单任务约束，推荐复用 `ProviderLock`，工作量估算 40-60 小时

### Out of Scope

- 完整实施国际化改造 — 本项目仅做可行性研究
- 生产级别的多 AI 协作实现 — 仅做概念验证
- 其他语言（日语、韩语等）的翻译工作 — 先聚焦中英文框架

## Context

**现有技术基础：**

CCB i18n 实现：
- 基于字典的消息存储（`MESSAGES = {"en": {...}, "zh": {...}}`）
- 环境变量语言检测（`CCB_LANG`）
- 简单的翻译函数 `t(key, **kwargs)`
- 支持参数化消息格式化

CCB 多 AI 架构：
- 守护进程驱动的多提供商系统
- 命令行接口（`ask codex/droid/gemini`）
- 异步消息传递和会话管理
- Worker pool 支持并行任务处理

GSD 架构：
- Agent 工具进行子任务分发
- 阶段化项目管理流程
- 支持并行研究代理（4 个研究维度）

**代码库状况：**
- CCB: 98 个 Python 文件，~6,366 行代码
- GSD: 需要进一步分析
- 测试覆盖率: CCB ~41%

**Droid 专家建议：**
- 最大挑战：文本分散与动态内容处理（1000+ 处硬编码文本）
- 集成方式：模块化 i18n 框架共享
- 关键风险：技术债务、日志分析破坏、性能影响、测试覆盖

**Codex 技术方案：**

i18n 架构：
- 不要直接复制 CCB 的 i18n.py，而是提取共享的 i18n_core
- 保持 `t(key, **kwargs)` API 契约
- 添加命名空间（`ccb.*`, `gsd.*`）和外部目录支持
- 区分人类可读文本和协议字符串（永不翻译协议标记）

GSD-CCB 集成：
- 添加 `MultiAIBackend` 抽象层
- 优先实现 `CCBCLIBackend`（包装 `ask/pend/ping`）
- 可选实现 `CCBMCPBackend`（使用 MCP 服务器）
- 返回结构化 `TaskHandle` 而非解析控制台文本

关键风险缓解：
- 永不翻译命令名、环境变量、JSON 键、完成标记
- 为翻译的提示添加快照测试
- 绑定所有 CCB 调用到明确的工作区/会话文件
- 添加 CI 检查缺失键和孤立键

工作量估算：
- MVP 可行性 PoC: 1-1.5 周
- 生产就绪版本: 3-4 周

## Constraints

- **时间**: 可行性研究阶段，不做完整实施
- **范围**: 聚焦中英文支持，其他语言仅考虑扩展性
- **技术**: 基于现有 Python 技术栈，不引入重型框架
- **兼容性**: 不破坏现有功能和 API

## Current State

- Phase 1-3 已完成：代码分析、架构设计、风险评估与工作量估算都已落盘并验证
- 下一阶段是 Phase 4：原型验证，目标是把 i18n_core、CCBCLIBackend、协议保护和文件锁方案落成最小可运行实现
- 当前最重要的工程约束：
  - 协议字符串永不翻译，白名单当前为 300 项
  - 同一 provider 必须串行化，避免结果覆盖
  - 会话文件访问应复用 `ProviderLock`

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 提取共享 i18n_core | 保持 API 契约，添加命名空间和目录支持 | Phase 2 已验证 |
| CCBCLIBackend 优先 | 比 MCP 更简单，已有生产级 CLI 接口 | Phase 2 已验证 |
| 区分人类文本和协议 | 永不翻译命令名、环境变量、完成标记 | Phase 1-3 已验证 |
| 渐进式迁移策略 | 降低风险，按模块逐步国际化 | Phase 3 工时估算支持该结论 |
| 结构化任务句柄 | 避免解析控制台文本，使用 TaskHandle/TaskResult | Phase 2 已验证 |
| 双层协议保护 | 外部翻译无法被 CI 覆盖，必须增加运行时验证 | Phase 3 已验证 |
| 单 provider 单任务约束 | 同 provider 并发会导致结果覆盖 | Phase 3 已验证 |
| 复用 ProviderLock | 现有 `process_lock.py` 已具备跨平台锁能力 | Phase 3 已验证 |

## Evolution

本文档在研究过程中持续更新。

**研究阶段更新触发：**
1. 代码分析完成 → 更新 Context 和 Requirements
2. 架构设计完成 → 更新 Key Decisions
3. 风险评估完成 → 更新 Constraints
4. 原型验证完成 → 移动 Requirements 到 Validated

---
*Last updated: 2026-03-30 after Phase 03 completion*
