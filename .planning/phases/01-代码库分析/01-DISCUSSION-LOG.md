# Phase 1: 代码库分析 - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-28
**Phase:** 01-代码库分析
**Areas discussed:** 扫描方法, 分类标准, 输出格式, 评估深度

---

## 扫描方法

| Option | Description | Selected |
|--------|-------------|----------|
| 正则表达式搜索 | 使用 grep/ripgrep 搜索字符串字面量模式（快速，但可能遗漏动态构建的字符串） | |
| AST 静态分析（推荐） | 使用 AST 解析器（如 Python ast 模块）分析语法树（准确，能识别所有字符串节点） | ✓ |
| 混合方法 | 结合 grep 快速定位 + AST 精确分析（平衡速度和准确性） | |

**User's choice:** AST 静态分析（推荐）
**Notes:** 选择准确性优先，确保完整覆盖所有硬编码文本

---

## 分类标准

| Option | Description | Selected |
|--------|-------------|----------|
| 基于文件/位置 | 基于位置：lib/i18n.py、命令行参数、环境变量名 = 协议；其他 = 人类文本 | |
| 基于命名模式 | 基于模式：全大写、特定前缀（CCB_、GSD_）、特定后缀（_DONE）= 协议；其他 = 人类文本（推荐） | ✓ |
| 基于使用上下文 | 基于上下文：分析字符串使用场景（日志、UI、配置键）来分类 | |

**User's choice:** 基于命名模式
**Notes:** 使用命名模式可以清晰识别协议字符串，符合 Codex 的建议

---

## 输出格式

| Option | Description | Selected |
|--------|-------------|----------|
| JSON（推荐） | 结构化 JSON 文件，包含 file/line/text/category/context 字段（适合程序处理） | |
| Markdown 报告 | Markdown 表格，按文件分组，人类可读性好 | ✓ |
| CSV 表格 | CSV 文件，方便 Excel 分析和筛选 | |

**User's choice:** Markdown 报告
**Notes:** 选择人类可读性，便于评审和讨论

---

## 评估深度

| Option | Description | Selected |
|--------|-------------|----------|
| API 分析 | 基础评估：分析 API 设计（t() 函数、命名空间支持）和基本可扩展性 | |
| API + 性能 + 扩展性 | 中等评估：包括 API + 性能分析（查找开销）+ 扩展性（多语言支持）（推荐） | ✓ |
| 全面评估 | 深度评估：包括上述 + 迁移成本估算 + 与 GSD 集成的技术可行性 | |

**User's choice:** API + 性能 + 扩展性
**Notes:** 平衡深度和可行性研究的时间限制

---

## Claude's Discretion

- AST 遍历算法的具体实现
- Markdown 报告的排版样式
- 性能测试的具体方法

## Deferred Ideas

- 自动语言检测和用户切换功能 — Phase 2（架构设计）
- 参考 ZCF 项目的具体实现细节 — Phase 2
