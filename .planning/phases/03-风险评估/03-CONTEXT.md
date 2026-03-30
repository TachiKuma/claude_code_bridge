# Phase 3: 风险评估 - Context

**Gathered:** 2026-03-28  
**Status:** Ready for planning

<domain>
## Phase Boundary

评估协议误翻译、上下文崩溃、竞态条件等风险，估算实施工作量。基于 Phase 1 的代码分析和 Phase 2 的架构设计，识别关键技术风险并制定缓解策略。

</domain>

<decisions>
## Implementation Decisions

### 协议字符串误翻译风险
- **D-01:** 误翻译影响评估为"完全破坏" — CCB 守护进程无法识别命令，系统崩溃
- **D-02:** 最高风险漏洞是外部翻译 — 用户自定义翻译（~/.ccb/i18n/）可绕过 CI 检查
- **D-03:** 缓解策略：运行时验证 — i18n_core 加载外部翻译时检查白名单，拒绝协议字符串覆盖
- **D-04:** 验证失败时拒绝加载该翻译文件，记录错误日志，使用内置翻译

### 多 AI 并发风险
- **D-05:** 文件锁方案：操作系统级文件锁 — 使用 fcntl (Unix) / msvcrt (Windows)
- **D-06:** 跨平台兼容：封装为 FileLock 类，自动检测平台
- **D-07:** 超时策略：等待重试 — 默认重试 3 次，每次等待 0.5 秒
- **D-08:** 获取锁失败后返回错误，由调用者决定是否继续重试


### 实施工作量估算
- **D-09:** 翻译文件创建最耗时 — 9029 条消息需要人工翻译和审校
- **D-10:** 完整实施估算：约 536 小时（13.4 周）
  - 翻译文件创建：300 小时
  - 代码修改：196 小时（98 个文件）
  - 测试覆盖：40 小时
- **D-11:** 原型阶段估算：约 26 小时（3-4 天）
  - 原型翻译：2 小时（50 条关键消息）
  - 核心代码：16 小时（i18n_core 实现）
  - 基础测试：8 小时（单元测试）
- **D-12:** 多 AI 集成工作量：基于 CCBCLIBackend 设计，估算 40-60 小时（包含测试和文档）

### 技术债务风险
- **D-13:** 主要担忧：字符串提取不完整和键命名不一致
- **D-14:** 缓解策略 1：自动化扫描工具 — 使用 AST 分析确保覆盖所有字符串
- **D-15:** 缓解策略 2：命名规范文档 — 定义清晰的键命名约定（ccb.module.action.detail）
- **D-16:** 开发模式下运行时检测未翻译的键，记录警告日志

### Claude's Discretion
- FileLock 类的具体实现细节
- 运行时验证的错误消息格式
- 自动化扫描工具的具体实现语言
- 命名规范文档的详细格式

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 2 架构设计
- `.planning/phases/02-架构设计/designs/i18n_core_design.md` — i18n_core 模块设计，包含日志系统
- `.planning/phases/02-架构设计/designs/ccb_cli_backend_design_v3.md` — CCBCLIBackend 接口设计（正确的退出码映射）
- `.planning/phases/02-架构设计/designs/protocol_protection_design.md` — 协议字符串保护机制（双层保护）
- `.planning/phases/02-架构设计/02-CONTEXT.md` — Phase 2 的所有实现决策

### Phase 1 分析结果
- `.planning/phases/01-代码库分析/01-ANALYSIS-REPORT.md` — 9029 个人类文本，520 个协议字符串
- `.planning/phases/01-代码库分析/results/classified.json` — 分类结果数据

### 项目文档
- `.planning/PROJECT.md` — 项目背景和专家建议
- `.planning/REQUIREMENTS.md` — Phase 3 的 5 个需求（RISK-01 到 05）

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Phase 2 设计的 i18n_core 模块 — 可直接用于运行时验证
- Phase 2 设计的协议字符串白名单 — 520 个协议字符串已识别
- Phase 1 的 AST 扫描工具 — 可复用于字符串提取完整性检查

### Established Patterns
- CCB 使用 subprocess 调用外部命令 — FileLock 需要兼容这种模式
- CCB 守护进程架构 — 多 AI 并发是常见场景
- 环境变量配置模式 — 可用于开发模式开关

### Integration Points
- i18n_core 加载外部翻译时需要集成运行时验证
- CCB 会话文件读写需要集成 FileLock
- CI 流程需要集成字符串提取完整性检查

</code_context>

<specifics>
## Specific Ideas

- 运行时验证应该在 i18n_core.load_translations() 中实现，加载外部翻译后立即检查
- FileLock 超时参数应该可配置，通过环境变量 CCB_LOCK_TIMEOUT 覆盖默认值
- 命名规范：ccb.{module}.{action}.{detail}，例如 ccb.daemon.startup.success
- 自动化扫描工具应该在 CI 中作为独立步骤运行，失败时阻止合并

</specifics>

<deferred>
## Deferred Ideas

- 性能回归风险评估 — Phase 1 已测试 i18n 查找性能（0.85 μs），当前不是主要风险
- 测试覆盖下降风险 — 属于 Phase 4 原型验证阶段评估
- MCP Backend 的并发风险 — CLI Backend 优先，MCP 为可选方案

</deferred>

---

*Phase: 03-风险评估*
*Context gathered: 2026-03-28*
