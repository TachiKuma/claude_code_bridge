# Phase 6 Research: CCB i18n 实施

**Date:** 2026-03-30
**Status:** Ready for planning

## Objective

回答一个问题：**要把 `05-CCB-i18n-详细实施方案.md` 落成可执行计划，代码层面最关键的实施切面和验证门槛是什么？**

## Current Truth From Code

### 1. R0 阻断项都是真实问题，不是文档假设

- `lib/i18n_core.py`
  - 外部翻译直接 `update()` 到内置翻译上。
  - 缺失 key 直接返回 key。
  - 只对协议字符串做 runtime warning，不做 merge reject。
- `lib/i18n.py`
  - 兼容层仍依赖旧的 locale 检测逻辑。
- `tests/test_i18n_core.py`
  - 当前测试覆盖了原型 happy path，但没有覆盖“部分翻译缺失 -> 英文回退”与“外部翻译 reject”。

### 2. CLI 核心已经有 i18n 落点，但覆盖面明显不足

- `t()` 已出现在：
  - `lib/codex_comm.py`
  - `lib/gemini_comm.py`
  - `lib/opencode_comm.py`
  - `bin/cpend`
  - `bin/gpend`
  - `bin/opend`
- 仍存在大量用户可见字符串散落在：
  - `bin/ask`
  - `bin/cask`
  - `bin/gask`
  - `bin/oask`
  - `bin/dask`
  - `ccb`

### 3. Mail/Web/TUI 是后续最大工作量来源

已确认存在硬编码文案的代表性文件：

- `lib/mail_tui/wizard.py`
- `lib/web/templates/dashboard.html`
- `lib/web/templates/mail.html`
- `lib/web/routes/daemons.py`
- `lib/web/routes/mail.py`
- `lib/mail/sender.py`

这些文件混合了：

- 终端交互文案
- HTML 模板静态文本
- API `message/detail` 字段
- 邮件主题与正文模板

因此它们不能沿用“只替换 print 文本”的简单策略，必须先盘点再迁移。

## Recommended Execution Slices

### Slice A: Core semantics repair

先修 `i18n_core` 的语义缺口，避免后续所有迁移都建立在错误回退链和弱保护之上。

### Slice B: CLI production hardening

把 CLI 核心作为第一批生产化目标，因为：

- 覆盖面相对集中
- 验证成本最低
- 最容易建立 CI 守卫

### Slice C: Inventory before expansion

Mail/Web/TUI 必须先出清单、分类和第二版估算。盘点本身就是交付物，不应当被视为“前置杂项”。

### Slice D: Full migration only after guardrails

全量迁移必须依赖：

1. 稳定的 `i18n_core`
2. 完整的翻译文件结构
3. 覆盖率 / 完整性检查脚本
4. 盘点报告和目标范围

## Validation Architecture

### Layer 1: Core correctness

- `python -W error -m pytest tests/test_i18n_core.py -q`
- 目标：回退链、协议 reject、locale 检测全部通过，且没有 `DeprecationWarning`

### Layer 2: Translation integrity

需要新增并固化两个检查：

- `python scripts/check_translation_coverage.py`
  - 检查目标 CLI 文件里的 `t()` 使用和缺失 key
- `python scripts/check_translation_completeness.py`
  - 检查 `en.json` / `zh.json` / `xx.json` 的 key 集一致

### Layer 3: CI enforcement

`.github/workflows/test.yml` 目前主要跑 `test/`，而 i18n 新测试位于 `tests/`。Phase 6 必须统一入口，避免脚本存在但 CI 未执行。

### Layer 4: Surface inventory

Mail/Web/TUI 盘点应当生成机器可复查的产物：

- `i18n_surface_inventory.md`
- `i18n_second_estimate.md`

二者必须包含文件路径、行号、原始文本、分类和建议命名空间。

### Layer 5: Migration regression

全量迁移后至少需要三类验证：

- CLI smoke
- API / template smoke
- pseudo locale smoke (`CCB_LANG=xx`)

## Risks To Preserve In The Plans

- 不要把协议字符串翻译检查和真实文案翻译迁移混在一个提交面里。
- 不要先改 Mail/Web/TUI 再补盘点，否则第二版估算会失真。
- 不要只写“统一错误文案”，必须给出具体 key、模板和目标文件。
- 不要假设 `.github/workflows/test.yml` 已覆盖 `tests/` 目录，它目前没有对齐。

## Planning Recommendation

最佳计划拆分是 5 个执行计划：

1. `06-01` 修复 `i18n_core` 阻断项
2. `06-02` 扩展 CLI 核心翻译覆盖
3. `06-03` 建立语言切换、CI 守卫与测试补全
4. `06-04` 盘点 Mail/Web/TUI 并更新估算
5. `06-05` 按清单执行全量迁移与回归验证

---

*Phase: 06-ccb-i18n*
*Research completed: 2026-03-30*
