# Phase 4: 原型验证 - Context

**Gathered:** 2026-03-30
**Status:** Ready for planning

<domain>
## Phase Boundary

实现最小原型验证 i18n_core、CCBCLIBackend、协议保护、文件锁等关键技术点。基于 Phase 1-3 的分析和设计，将设计方案落地为可运行代码并通过测试验证。

**范围调整：** PROTO-01(i18n_core) 和 PROTO-03(协议保护) 完整实现；PROTO-02(CCBCLIBackend)、PROTO-04(TaskHandle)、PROTO-05(文件锁) 简化为概念验证级别（完整代码但 mock 测试）。

</domain>

<decisions>
## Implementation Decisions

### 原型范围和优先级
- **D-01:** 核心优先策略 — PROTO-01 和 PROTO-03 完整实现，其他 3 个 PROTO 简化为概念验证
- **D-02:** Phase 3 的 26 小时估算作为参考上限（核心代码 16h + 测试 8h + 原型翻译 2h）

### i18n_core 原型实现 (PROTO-01)
- **D-03:** 完整实现 Phase 2 设计文档中的 I18nCore 类，包括日志系统、语言检测、外部翻译覆盖、回退机制
- **D-04:** lib/i18n.py 修改为调用 i18n_core，验证向后兼容性
- **D-05:** 迁移 lib/i18n.py 现有的全部消息（56 条）到 JSON 翻译文件
- **D-06:** 创建 3 种语言翻译文件：en.json、zh.json、xx.json（伪翻译）
- **D-07:** 伪翻译策略：所有文本前后添加 [«»] 标记 + 拉长字符串长度（用 x 填充），测试布局溢出
- **D-08:** 原型代码直接放在 lib/ 目录下（lib/i18n_core.py），与生产代码结构一致

### 协议字符串保护 (PROTO-03)
- **D-09:** 实现 CI 检查脚本 scripts/check_protocol_strings.py，对照 protocol_whitelist.json 检查翻译值
- **D-10:** 协议保护采用双层策略：CI 值检查 + 运行时验证（i18n_core 加载时检查白名单）

### CCBCLIBackend (PROTO-02)
- **D-11:** 完整实现 CCBCLIBackend 4 个方法（submit/poll/ping/list_providers）
- **D-12:** 使用 mock 测试验证，不依赖真实 CCB 环境
- **D-13:** TaskHandle/TaskResult 作为独立模块实现（lib/task_models.py）

### 文件锁 (PROTO-05)
- **D-14:** 基于现有 lib/process_lock.py 实现跨平台 FileLock 类
- **D-15:** 使用单元测试验证加锁/解锁/超时逻辑，仅验证当前系统（Windows）

### 验证方式和验收标准
- **D-16:** 单元测试 + Demo 脚本（i18n_core 仅有）
- **D-17:** 使用 Python 内置 unittest 框架，不引入新依赖
- **D-18:** 验证报告：分 PROTO 报告 + 汇总报告，每个报告包含测试结果、关键发现、风险或建议
- **D-19:** 每个原型的验收标准：单元测试全部通过 + Demo 可运行 + 验证报告完成

### Claude's Discretion
- FileLock 类的具体实现细节（复用 process_lock.py 的模式）
- 运行时验证的错误消息格式和日志级别
- Demo 脚本的具体展示内容和格式
- 伪翻译文件中字符串拉长的倍数
- 协议检查脚本的具体命令行参数

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 2 架构设计
- `.planning/phases/02-架构设计/designs/i18n_core_design.md` — i18n_core 完整设计（类定义、命名空间、回退、日志、类型注解）
- `.planning/phases/02-架构设计/designs/ccb_cli_backend_design_v3.md` — CCBCLIBackend v3 设计（退出码映射、单任务约束、Windows 兼容）
- `.planning/phases/02-架构设计/designs/protocol_protection_design.md` — 协议保护设计（双层策略、白名单格式、CI 脚本）
- `.planning/phases/02-架构设计/designs/task_models_design.md` — TaskHandle/TaskResult 数据结构设计
- `.planning/phases/02-架构设计/designs/translation_structure.md` — 翻译文件组织结构

### Phase 3 风险评估
- `.planning/phases/03-风险评估/03-CONTEXT.md` — Phase 3 所有实现决策
- `.planning/phases/03-风险评估/reports/i18n_effort_estimation.md` — i18n 改造工作量估算（原型 26h）
- `.planning/phases/03-风险评估/reports/multi_ai_effort_estimation.md` — 多 AI 集成工作量估算
- `.planning/phases/03-风险评估/reports/file_lock_analysis.md` — 文件锁分析报告
- `.planning/phases/03-风险评估/reports/protocol_mistranslation_risk.md` — 协议误翻译风险评估
- `.planning/phases/03-风险评估/03-CONTEXT.md` — 双层保护、单任务约束、ProviderLock 复用等决策

### 现有代码
- `lib/i18n.py` — 现有 i18n 实现（56 条消息），需要迁移并修改为调用 i18n_core
- `lib/process_lock.py` — 现有文件锁实现，FileLock 应复用其模式
- `lib/cli_output.py` — 退出码定义（EXIT_OK=0, EXIT_ERROR=1, EXIT_NO_REPLY=2）

### 项目文档
- `.planning/PROJECT.md` — 项目背景、核心价值、约束
- `.planning/REQUIREMENTS.md` — Phase 4 的 5 个需求（PROTO-01 到 05）
- `.planning/protocol_whitelist.json` — 协议字符串白名单（300 项）

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `lib/i18n.py` — 现有 t() 函数 API、MESSAGES 字典、detect_language()，56 条消息待迁移
- `lib/process_lock.py` — 跨平台文件锁模式，FileLock 可复用
- `lib/cli_output.py` — CCB 退出码常量定义，CCBCLIBackend poll() 依赖
- `bin/ask` / `bin/pend` — CCB CLI 命令，CCBCLIBackend 需要包装的底层命令
- `.planning/protocol_whitelist.json` — 协议白名单 300 项，CI 检查脚本直接使用

### Established Patterns
- CCB 使用环境变量 CCB_LANG 进行语言检测
- CCB 使用 subprocess.run() 调用外部命令
- 参数化消息格式化 t(key, **kwargs) 已被广泛使用
- JSON 配置文件模式（protocol_whitelist.json、配置文件等）

### Integration Points
- lib/i18n.py → lib/i18n_core.py（i18n.py 修改为调用 i18n_core）
- lib/i18n_core.py → lib/i18n/ccb/{en,zh,xx}.json（翻译文件目录）
- scripts/check_protocol_strings.py → .planning/protocol_whitelist.json（白名单）
- lib/task_models.py → lib/ccb_cli_backend.py（TaskHandle 作为 Backend 的返回类型）
- i18n_core 加载外部翻译时 → runtime 验证对照白名单

</code_context>

<specifics>
## Specific Ideas

- 伪翻译文件不仅用于测试框架，还可以展示国际化后不同语言的视觉效果
- i18n_core 与 i18n.py 的兼容性验证是关键 — 现有 CCB 代码不应因为切换到 i18n_core 而破坏
- FileLock 复用 process_lock.py 的模式但作为独立类，便于 GSD 未来复用
- 分 PROTO 的验证报告结构有助于 Phase 5 文档交付直接引用

</specifics>

<deferred>
## Deferred Ideas

- 真实 CCB 环境中的 CCBCLIBackend 集成测试 — 概念验证阶段使用 mock 即可
- 跨平台文件锁的多平台实际验证 — 仅验证当前系统（Windows）
- MCP Backend 实现 — CLI Backend 优先，MCP 为可选方案
- 并发文件锁的多进程竞争测试 — 单元测试验证逻辑即可

</deferred>

---

*Phase: 04-原型验证*
*Context gathered: 2026-03-30*
