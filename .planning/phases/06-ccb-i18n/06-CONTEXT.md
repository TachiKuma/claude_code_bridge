# Phase 6: CCB i18n 实施 - Context

**Gathered:** 2026-03-30
**Status:** Ready for planning
**Source:** `docs/feasibility-study/05-CCB-i18n-详细实施方案.md` + 用户讨论扩展

<domain>
## Phase Boundary

本阶段处理 **CCB i18n 全量落地**，不包含 GSD 全量国际化和多 AI 协作增强。执行范围：

1. 先消除 `i18n_core` 原型与文档之间的 P0 偏差。
2. 再把 CLI 核心 i18n 从"原型可用"提升为"生产可用"。
3. 然后盘点 Mail/Web/TUI 文案面，形成第二版估算。
4. 最后按盘点结果执行 CCB 全量迁移与回归验证。

**本次扩展范围（在原有基础上新增）：**
5. Skill 模板全量翻译（12 个 SKILL.md 文件）。
6. Install 脚本补漏（install.ps1 ~80+ 条 / install.sh ~100+ 条硬编码字符串迁移到消息字典）。
7. CLI argparse help 文本全量 t() 包裹。
8. Config 模板混合翻译（用户可见说明翻译，代码块/JSON schema/命令示例保持英文）。

</domain>

<decisions>
## Locked Decisions

### Phase decomposition
- **D-01:** Phase 6 采用 5 个执行计划，顺序为 `R0 修复 -> CLI 生产化 -> 语言切换/CI -> 文案盘点 -> 全量迁移`。
- **D-02:** 本阶段的需求映射固定为 `I18N-01` 到 `I18N-06`，不在本阶段引入 GSD i18n 或多 AI 集成需求。

### Runtime behavior
- **D-03:** `lib/i18n_core.py` 的真实回退链必须是 `当前语言 -> en.json -> key 本身`，而不是"缺 key 直接返回 key"。
- **D-04:** 外部翻译目录 `~/.ccb/i18n/<namespace>/<lang>.json` 仍保留，但命中协议白名单的值必须 **reject**，不能只告警后继续合并。
- **D-05:** `locale.getdefaultlocale()` 在本阶段内全部替换为 `locale.getlocale()`，并保持 `LANG/LC_ALL/LC_MESSAGES` 的优先级。

### Scope control
- **D-06:** CLI 核心范围锁定在 `ccb`、`bin/ask`、各 provider wrapper、`lib/*_comm.py` 以及直接向终端输出用户文案的入口。
- **D-07:** Mail/Web/TUI 在进入全量迁移前，必须先产出盘点清单和第二版工时估算；不得跳过盘点直接开始大面积替换。
- **D-08:** 协议字符串、命令名、环境变量、JSON 键、完成标记保持不翻译；翻译系统只能处理用户可见文案。

### Skill 模板 (新增 D-09)
- **D-09:** 12 个 SKILL.md 模板文件进行全量翻译，包括 short-description、description、使用说明、规则指令和示例。翻译方式：每个 SKILL.md 提供中英双语版本（如 `SKILL.en.md` / `SKILL.zh.md`），安装脚本根据语言设置选择注入对应版本。

### Install 脚本 (新增 D-10)
- **D-10:** install.ps1 中约 80+ 条硬编码 Write-Host 字符串全量迁移到 Get-Msg 字典。Write-Warning 统一改为 Write-Host "[WARNING] ..." 格式，消除 PowerShell 系统前缀的本地化不一致问题。install.sh 同步进行相同的全量迁移处理。

### CLI argparse help (新增 D-11)
- **D-11:** `ccb` 主入口文件中所有 argparse 的 `description=`、`help=` 参数替换为 t() 调用。需要在语言检测完成后（或在 t() 函数支持延迟求值）才能构建 parser，确保 help 输出与用户语言设置一致。

### Config 模板 (新增 D-12)
- **D-12:** Config 模板文件（`claude-md-ccb.md`、`agents-md-ccb.md`、`clinerules-ccb.md`、`tmux-ccb.conf`）采用混合翻译策略：用户可见的说明文本（role 描述、规则说明、注释）进行 i18n；代码块、JSON schema、命令示例保持英文不变。实现方式：提供双语版本文件，安装时根据语言选择注入。

### the agent's Discretion
- 翻译 key 的具体命名层级可以在 `ccb.command.*`、`ccb.mail.*`、`ccb.web.*`、`ccb.skill.*`、`ccb.install.*` 等命名空间内细化。
- 盘点脚本的实现语言可选 Python；优先复用现有 `scripts/` 和 `rg` 能力，不额外引入依赖。
- Web 模板的翻译注入方式可以是上下文函数、模板 helper 或预渲染字典，但必须避免在模板中硬编码文案。
- Skill 模板的双语版本文件命名约定（`SKILL.en.md` / `SKILL.zh.md` 或其他方案）由实现决定。
- argparse t() 包裹的具体实现方式（延迟构建 parser 或 monkey-patch）由实现决定。

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
- `ccb` — 顶层 CLI 入口，后续 `--lang` / `config lang` / argparse help 的主承载点
- `lib/ccb_config.py` — `.ccb-config.json` 读取逻辑，可扩展语言配置

### Install scripts (新增范围)
- `install.ps1` — Windows PowerShell 安装脚本，含 Get-Msg 框架和 ~80+ 条硬编码字符串
- `install.sh` — Unix/Linux 安装脚本，含 msg() 框架和 ~100+ 条硬编码字符串

### Skill templates (新增范围)
- `claude_skills/` — 12 个 Claude skill SKILL.md 模板目录
- `config/skills/` — Codex/Droid skill 模板目录
- `install.ps1` §Install-ClaudeSkills / §Install-CodexSkills / §Install-FactorySkills — skill 安装逻辑
- `install.sh` §install_skills — Unix skill 安装逻辑

### Config templates (新增范围)
- `config/claude-md-ccb.md` — CLAUDE.md 注入模板（~40-50 条用户可见字符串）
- `config/claude-md-ccb-route.md` — 路由配置模板
- `config/agents-md-ccb.md` — AGENTS.md 注入模板（~30-40 条字符串）
- `config/clinerules-ccb.md` — .clinerules 注入模板
- `config/tmux-ccb.conf` — WezTerm/tmux 配置模板

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
- `lib/i18n_core.py` 当前只在"整份语言文件不存在"时回退英文；单个 key 缺失时直接返回 key。
- `lib/i18n_core.py` 当前直接 `self.translations.update(external)`，然后只做 runtime warning。
- `lib/i18n_core.py` 与 `lib/i18n.py` 仍使用 `locale.getdefaultlocale()`。
- `lib/i18n/ccb/` 当前只有 `en.json`、`zh.json`、`xx.json` 三份翻译文件。
- `.github/workflows/test.yml` 仍以 `test/` 为主测试目录，而 i18n 新测试位于 `tests/`。

### Install script i18n status
- `install.ps1` 已有 `Get-CCBLang()` 和 `Get-Msg()` 框架，但消息字典仅含 7 个 key，大量 Write-Host 直接使用硬编码英文。
- `install.sh` 已有 `detect_lang()` 和 `msg()` 框架，消息字典覆盖较完整但仍需审查遗漏。
- `Write-Warning` 的前缀（如 "警告:"）来自 PowerShell 系统行为，需改为 Write-Host 统一格式。

### Skill template i18n status
- 12 个 Claude skill（`claude_skills/`）均为纯英文 SKILL.md，无 i18n 机制。
- Codex/Droid skills 通过 install.ps1 install.sh 从 `config/skills/` 复制，同样纯英文。
- 当前安装逻辑不支持双语版本选择。

### CLI argparse status
- `ccb` 主入口文件已有大量 `t()` 调用用于运行时消息。
- argparse 定义中的 `description=` 和 `help=` 全部为硬编码英文字符串。
- `--lang` 参数已存在于 argparse 定义中，但 parser 在语言检测前构建。

### Config template i18n status
- 所有 config 模板均为纯英文 markdown，无 i18n 机制。
- 安装时直接复制文件内容注入，无语言选择逻辑。

### Immediate execution implications
- 计划 01 需要同时修改实现和测试，先把阻断项闭环。
- 计划 02 和 03 都依赖计划 01 的稳定核心，但可以在执行时分成多个工作面。
- 计划 04 的产物不仅是代码功能，还包括盘点报告、估算报告和迁移策略。
- 计划 05 必须消费计划 04 的盘点结果。
- 新增范围（D-09 ~ D-12）需要纳入现有计划或在计划 05 全量迁移阶段统一执行。

</code_context>

<specifics>
## Specific Ideas

- install.ps1 的 "警告:" 前缀来自 PowerShell Write-Warning 系统行为，需统一改为 Write-Host "[WARNING] ..." 格式。
- ccb -help 输出的英文 help text 是用户最先接触的界面，应优先处理。
- Skill 模板的翻译需保持 AI 指令的可执行性——翻译后的 prompt 仍需被 AI 正确理解。
- Config 模板中代码块和命令示例保持英文，确保技术命令的可复制性。

</specifics>

<deferred>
## Deferred Ideas

- GSD 全量国际化
- 多 AI 协作增强（`MULTI-*`）
- 更多自然语言（如日语、韩语）翻译
- MCP backend 或额外前端国际化框架

</deferred>

---
*Phase: 06-ccb-i18n*
*Context gathered: 2026-03-30 via discuss-phase + user scope expansion*
