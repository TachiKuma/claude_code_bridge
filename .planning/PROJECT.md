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

- [ ] 分析 GSD 和 CCB 代码库，识别需要国际化的文本
- [ ] 设计统一的 i18n 架构框架
- [ ] 评估国际化改造的工作量和技术风险
- [ ] 设计 GSD 利用 CCB 多 AI 协作的集成方案
- [ ] 构建原型验证关键技术点
- [ ] 编写完整的技术方案文档

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

## Constraints

- **时间**: 可行性研究阶段，不做完整实施
- **范围**: 聚焦中英文支持，其他语言仅考虑扩展性
- **技术**: 基于现有 Python 技术栈，不引入重型框架
- **兼容性**: 不破坏现有功能和 API

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 基于 CCB 现有 i18n.py 扩展 | 已有工作基础，避免重复造轮子 | — Pending |
| 命令行集成方式 | GSD 通过 CCB 命令行调用多 AI | — Pending |
| 渐进式迁移策略 | 降低风险，按模块逐步国际化 | — Pending |

## Evolution

本文档在研究过程中持续更新。

**研究阶段更新触发：**
1. 代码分析完成 → 更新 Context 和 Requirements
2. 架构设计完成 → 更新 Key Decisions
3. 风险评估完成 → 更新 Constraints
4. 原型验证完成 → 移动 Requirements 到 Validated

---
*Last updated: 2026-03-28 after initialization*
