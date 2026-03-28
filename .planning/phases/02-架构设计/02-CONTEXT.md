# Phase 2: 架构设计 - Context

**Gathered:** 2026-03-28
**Status:** Ready for planning

<domain>
## Phase Boundary

设计共享 i18n_core 模块和 CCBCLIBackend 接口，建立协议字符串保护机制。

**重要范围调整:** 优先完成 CCB 的国际化多语言支持，GSD 多语言功能冻结在当前状态。本阶段聚焦 CCB i18n 架构设计和多 AI 协作接口。

</domain>

<decisions>
## Implementation Decisions

### i18n_core 模块设计
- **D-01:** 使用命名空间前缀（ccb.*）组织翻译键，避免键冲突
- **D-02:** 翻译键缺失时返回键名本身（如 'ccb.error.unknown'），便于调试
- **D-03:** 保持 t(key, **kwargs) 简洁 API，兼容现有 CCB 代码
- **D-04:** 支持外部翻译目录，用户可在 ~/.ccb/i18n/ 自定义翻译覆盖内置翻译
- **D-05:** 启动时一次性加载所有翻译到内存，优化查找性能
- **D-06:** 语言检测综合环境变量（CCB_LANG）和系统 locale，优先环境变量
- **D-07:** 使用 JSON 格式存储翻译文件，简单易读便于手动编辑

### CCBCLIBackend 接口
- **D-08:** 提供 4 个核心方法：submit() 提交任务返回 TaskHandle，poll() 轮询结果，ping() 检查连接，list_providers() 列出可用 AI
- **D-09:** TaskHandle 和 TaskResult 使用结构化对象（包含 task_id、provider、timestamp、status、output、error）
- **D-10:** 错误处理返回 TaskResult(status='error', error=...)，保持接口一致性，不抛出异常
- **D-11:** 通过 subprocess 包装 ask/pend 命令实现，解析命令输出

### 协议字符串保护机制
- **D-12:** CI 自动检查翻译文件，确保 520 个协议字符串未被翻译
- **D-13:** 维护白名单文件列出所有协议字符串，CI 检查对照
- **D-14:** CI 检查失败时阻止合并，强制修复后才能继续

### 翻译文件组织结构
- **D-15:** 使用三目录结构：ccb/ 存放 CCB 翻译，common/ 存放共享翻译（GSD 冻结，暂不创建 gsd/ 目录）
- **D-16:** 按语言分文件：en.json, zh.json，每个语言一个完整文件
- **D-17:** 支持外部翻译目录 ~/.ccb/i18n/，用户自定义翻译覆盖内置翻译

### 范围调整
- **D-18:** GSD 多语言功能冻结，Phase 2-5 仅关注 CCB 国际化
- **D-19:** 多 AI 协作接口（CCBCLIBackend）仍然设计，为未来 GSD 集成预留
- **D-20:** 翻译文件组织保留 common/ 目录概念，但当前仅实现 ccb/ 部分

### Claude's Discretion
- i18n_core 内部缓存实现细节
- TaskHandle 的具体字段命名
- CI 检查脚本的具体实现语言（Python/Bash）
- 白名单文件的具体格式（JSON/TXT）

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### 现有实现
- `lib/i18n.py` — CCB 现有 i18n 实现（评分 6.7/10），需要重新设计共享核心

### Phase 1 分析结果
- `.planning/phases/01-代码库分析/01-ANALYSIS-REPORT.md` — 完整的字符串分析报告（9873 个字符串，520 协议，9029 人类文本）
- `.planning/phases/01-代码库分析/results/classified.json` — 分类结果数据

### 研究文档
- `.planning/research/STACK.md` — 推荐的 i18n 技术栈
- `.planning/research/PITFALLS.md` — 协议字符串误翻译等关键风险

### 项目文档
- `.planning/PROJECT.md` — Codex 技术方案（i18n_core 架构、CCBCLIBackend 设计）
- `.planning/REQUIREMENTS.md` — Phase 2 的 5 个需求（ARCH-01 到 05）

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `lib/i18n.py` — 现有 t() 函数 API 可保持兼容
- CCB 守护进程架构 — ask/pend 命令已稳定，可直接包装

### Established Patterns
- CCB 使用环境变量 CCB_LANG 进行语言检测
- CCB 使用 subprocess 调用外部命令的模式成熟
- 参数化消息格式化 t(key, **kwargs) 已被广泛使用

### Integration Points
- i18n_core 需要替换现有 lib/i18n.py
- CCBCLIBackend 需要包装 bin/ask 和 bin/pend 命令
- CI 检查需要集成到现有 GitHub Actions 或 pre-commit hooks

</code_context>

<specifics>
## Specific Ideas

- Codex 建议：不要直接复制 CCB 的 i18n.py，而是提取共享的 i18n_core
- 协议字符串永不翻译：命令名、环境变量、JSON 键、完成标记（如 CCB_DONE、ask.response）
- TaskHandle 应该是结构化对象，避免解析控制台文本
- 外部翻译目录优先级：~/.ccb/i18n/ > 内置翻译

</specifics>

<deferred>
## Deferred Ideas

- GSD 多语言支持 — 需求变更，冻结在当前状态
- MCP Backend 实现 — CLI Backend 优先，MCP 为可选方案
- 动态翻译加载 — v2+ 功能，当前启动时全部加载即可
- 伪本地化测试（UI 溢出检测）— 属于完整实施阶段

</deferred>

---

*Phase: 02-架构设计*
*Context gathered: 2026-03-28*
