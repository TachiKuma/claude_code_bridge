# Phase 1: 代码库分析 - Context

**Gathered:** 2026-03-28
**Status:** Ready for planning

<domain>
## Phase Boundary

识别 CCB 和 GSD 代码库中所有需要国际化的文本，区分人类可读文本和协议字符串。这是可行性研究的第一步，为后续架构设计提供数据基础。

</domain>

<decisions>
## Implementation Decisions

### 扫描方法
- **D-01:** 使用 AST 静态分析（Python ast 模块）扫描代码库
- **D-02:** 分析语法树中的所有字符串节点，确保完整覆盖
- **D-03:** 扫描范围：CCB 的 98 个 Python 文件（~6,366 行）+ GSD 代码库

### 分类标准
- **D-04:** 基于命名模式区分协议字符串和人类文本
- **D-05:** 协议字符串特征：全大写、特定前缀（CCB_、GSD_）、特定后缀（_DONE）
- **D-06:** 人类文本：其他所有字符串（用户界面、错误消息、日志等）

### 输出格式
- **D-07:** 生成 Markdown 报告，按文件分组
- **D-08:** 每个条目包含：文件路径、行号、文本内容、分类（协议/人类）、上下文代码片段

### 评估深度
- **D-09:** CCB i18n.py 可复用性评估包含三个维度：
  - API 设计分析（t() 函数、命名空间支持）
  - 性能分析（查找开销、内存占用）
  - 扩展性分析（多语言支持、外部目录加载）

### Claude's Discretion
- 具体的 AST 遍历算法实现
- Markdown 报告的具体排版样式
- 性能测试的具体方法

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 现有实现
- `lib/i18n.py` — CCB 现有 i18n 实现，需要评估其可复用性

### 研究发现
- `.planning/research/STACK.md` — 推荐的 i18n 技术栈（gettext + Babel）
- `.planning/research/FEATURES.md` — i18n 系统的基本功能和差异化功能
- `.planning/research/PITFALLS.md` — 协议字符串误翻译等关键风险

### 项目文档
- `.planning/PROJECT.md` — 项目背景和专家建议（Droid 和 Codex 的技术方案）
- `.planning/REQUIREMENTS.md` — Phase 1 的 4 个需求（ANALYSIS-01 到 04）

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `lib/i18n.py` — CCB 现有 i18n 实现，包含 MESSAGES 字典、detect_language()、t() 函数
- `.planning/codebase/` — 已有完整的代码库映射文档（STACK.md、ARCHITECTURE.md、CONCERNS.md 等）

### Established Patterns
- CCB 使用基于字典的简单 i18n 实现
- 环境变量检测（CCB_LANG）用于语言选择
- 参数化消息格式化（t(key, **kwargs)）

### Integration Points
- 扫描工具需要遍历 CCB 的 `lib/` 目录和 GSD 的代码库
- 分析结果将用于 Phase 2 的架构设计

</code_context>

<specifics>
## Specific Ideas

- 参考 ZCF 项目（https://github.com/UfoMiao/zcf）的国际化实现
- Codex 建议：区分人类文本和协议字符串是关键，永不翻译命令名、环境变量、完成标记
- Droid 警告：CCB 有 1000+ 处硬编码文本，需要系统化扫描

</specifics>

<deferred>
## Deferred Ideas

- 自动语言检测和用户切换功能 — 属于 Phase 2（架构设计）范畴
- 实际的翻译工作 — 超出可行性研究范围，属于完整实施阶段

</deferred>

---

*Phase: 01-代码库分析*
*Context gathered: 2026-03-28*
