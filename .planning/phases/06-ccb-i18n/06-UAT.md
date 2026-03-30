---
status: testing
phase: 06-ccb-i18n
source:
  - 06-01-SUMMARY.md
  - 06-02-SUMMARY.md
  - 06-03-SUMMARY.md
  - 06-04-SUMMARY.md
  - 06-05-SUMMARY.md
  - 06-06-SUMMARY.md
started: 2026-03-30T23:05:48.9264960+08:00
updated: 2026-03-30T23:05:48.9264960+08:00
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

number: 1
name: Ask 帮助输出伪本地化
expected: |
  在仓库根目录运行 `CCB_LANG=xx ask --help`（Windows 可用 PowerShell 等价环境变量写法）。
  帮助输出应该显示伪本地化 marker（例如 `«...xx»`），且不应出现原始 `ccb.ask.*` key、
  `Translation key not found`、或直接回退成未翻译的英文 key 名。
awaiting: user response

## Tests

### 1. Ask 帮助输出伪本地化
expected: 在仓库根目录运行 `CCB_LANG=xx ask --help`。帮助输出显示伪本地化 marker，且不出现原始 `ccb.ask.*` key 或 `Translation key not found`。
result: [pending]

### 2. 持久语言切换影响主 CLI 帮助
expected: 运行 `ccb config lang zh` 后，再执行 `ccb --help`。主帮助、描述和参数说明应显示中文；恢复 `ccb config lang auto` 后，语言优先级回到环境变量/locale 逻辑。
result: [pending]

### 3. 子命令帮助文本已接入翻译
expected: 执行 `ccb mail --help`、`ccb droid --help`、`ccb config lang --help`。这些子命令的 description/help 文本应来自翻译系统，而不是硬编码英文句子。
result: [pending]

### 4. 中文配置模板可直接阅读
expected: 打开 `config/claude-md-ccb.zh.md`、`config/agents-md-ccb.zh.md`、`config/clinerules-ccb.zh.md`、`config/tmux-ccb.zh.conf`。说明性文字应为中文；命令示例、provider 名、代码块仍保持英文协议格式。
result: [pending]

### 5. 文案盘点报告已无剩余硬编码
expected: 打开 `.planning/phases/06-ccb-i18n/reports/i18n_surface_inventory.md`，报告顶部结果应表明当前为 `158 translated / 0 hardcoded`，不再有 Mail/Web/TUI 残余硬编码清单。
result: [pending]

## Summary

total: 5
passed: 0
issues: 0
pending: 5
skipped: 0
blocked: 0

## Gaps

<!-- none yet -->
