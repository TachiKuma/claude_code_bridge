# Phase 6: CCB i18n 实施 - Context

**Gathered:** 2026-03-30
**Status:** Ready for execution
**Source:** `docs/feasibility-study/05-CCB-i18n-详细实施方案.md`

<domain>
## Phase Boundary

本阶段只处理 **CCB i18n 落地**，不包含 GSD 全量国际化和多 AI 协作增强。执行范围以修订后的实施路径为准：

1. 先消除 `i18n_core` 原型与文档之间的 P0 偏差。
2. 再把 CLI 核心 i18n 从“原型可用”提升为“生产可用”。
3. 然后盘点 Mail/Web/TUI 文案面，形成第二版估算。
4. 最后按盘点结果执行 CCB 全量迁移与回归验证。

</domain>

<decisions>
## Locked Decisions

### Phase decomposition
- **D-01:** Phase 6 采用 5 个执行计划，顺序为 `R0 修复 -> CLI 生产化 -> 语言切换/CI -> 文案盘点 -> 全量迁移`。
- **D-02:** 本阶段的需求映射固定为 `I18N-01` 到 `I18N-06`，不在本阶段引入 GSD i18n 或多 AI 集成需求。

### Runtime behavior
- **D-03:** `lib/i18n_core.py` 的真实回退链必须是 `当前语言 -> en.json -> key 本身`，而不是“缺 key 直接返回 key”。
- **D-04:** 外部翻译目录 `~/.ccb/i18n/<namespace>/<lang>.json` 仍保留，但命中协议白名单的值必须 **reject**，不能只告警后继续合并。
- **D-05:** `locale.getdefaultlocale()` 在本阶段内全部替换为 `locale.getlocale()`，并保持 `LANG/LC_ALL/LC_MESSAGES` 的优先级。

### Scope control
- **D-06:** CLI 核心范围锁定在 `ccb`、`bin/ask`、各 provider wrapper、`lib/*_comm.py` 以及直接向终端输出用户文案的入口。
- **D-07:** Mail/Web/TUI 在进入全量迁移前，必须先产出盘点清单和第二版工时估算；不得跳过盘点直接开始大面积替换。
- **D-08:** 协议字符串、命令名、环境变量、JSON 键、完成标记保持不翻译；翻译系统只能处理用户可见文案。

### the agent's Discretion
- 翻译 key 的具体命名层级可以在 `ccb.command.*`、`ccb.mail.*`、`ccb.web.*` 等命名空间内细化。
- 盘点脚本的实现语言可选 Python；优先复用现有 `scripts/` 和 `rg` 能力，不额外引入依赖。
- Web 模板的翻译注入方式可以是上下文函数、模板 helper 或预渲染字典，但必须避免在模板中硬编码文案。

</decisions>

<canonical_refs>
## Canonical References

**执行 Phase 6 前必须阅读以下文件。**

### Primary plan source
- `docs/feasibility-study/05-CCB-i18n-详细实施方案.md` — 本阶段唯一的范围与顺序基线

### Existing design and validation
- `.planning/phases/02-架构设计/designs/i18n_core_design.md` — `i18n_core` 设计契约
- `.planning/phases/02-架构设计/designs/translation_structure.md` — 翻译目录与 JSON 结构
- `.planning/phases/04-原型验证/04-01-PLAN.md` — 当前原型是如何落地的
- `.planning/phases/04-原型验证/04-VERIFICATION.md` — 原型验证结论和遗留人工验证项

### Current implementation hotspots
- `lib/i18n_core.py` — 回退链、外部覆盖、协议白名单校验
- `lib/i18n.py` — 向后兼容层和语言检测
- `tests/test_i18n_core.py` — 当前 i18n 原型测试
- `scripts/check_protocol_strings.py` — 现有协议白名单检查
- `ccb` — 顶层 CLI 入口，后续 `--lang` / `config lang` 的主承载点
- `lib/ccb_config.py` — `.ccb-config.json` 读取逻辑，可扩展语言配置

### Known uncovered surfaces
- `lib/mail_tui/wizard.py` — TUI 与 simple wizard 文案
- `lib/web/templates/dashboard.html` — Web dashboard 模板
- `lib/web/templates/mail.html` — Mail Web 配置页模板
- `lib/web/routes/daemons.py` — Web API 返回消息
- `lib/web/routes/mail.py` — Mail API 返回消息和测试邮件文案
- `lib/mail/sender.py` — 发送邮件正文模板

</canonical_refs>

<code_context>
## Existing Code Insights

### Verified from source
- `lib/i18n_core.py` 当前只在“整份语言文件不存在”时回退英文；单个 key 缺失时直接返回 key。
- `lib/i18n_core.py` 当前直接 `self.translations.update(external)`，然后只做 runtime warning。
- `lib/i18n_core.py` 与 `lib/i18n.py` 仍使用 `locale.getdefaultlocale()`。
- `lib/i18n/ccb/` 当前只有 `en.json`、`zh.json`、`xx.json` 三份翻译文件。
- `.github/workflows/test.yml` 仍以 `test/` 为主测试目录，而 i18n 新测试位于 `tests/`。

### Immediate execution implications
- 计划 01 需要同时修改实现和测试，先把阻断项闭环。
- 计划 02 和 03 都依赖计划 01 的稳定核心，但可以在执行时分成两个工作面：翻译覆盖 / CI 与语言切换。
- 计划 04 的产物不是代码功能，而是盘点报告、估算报告和迁移策略。
- 计划 05 必须消费计划 04 的盘点结果，不能在没有清单的情况下开始“全量替换”。

</code_context>

<deferred>
## Deferred Ideas

- GSD 全量国际化
- 多 AI 协作增强（`MULTI-*`）
- 更多自然语言（如日语、韩语）翻译
- MCP backend 或额外前端国际化框架

</deferred>

---

*Phase: 06-ccb-i18n*
*Context gathered: 2026-03-30 via feasibility-study PRD*
