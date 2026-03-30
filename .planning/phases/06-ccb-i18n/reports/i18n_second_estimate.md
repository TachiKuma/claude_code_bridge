# CCB i18n Second Estimate

## Inputs

- 基线方案：`docs/feasibility-study/05-CCB-i18n-详细实施方案.md`
- 盘点脚本：`scripts/audit_ccb_i18n_surface.py`
- 盘点结果：`i18n_surface_inventory.md`

## Audit Outcome

- 锁定范围共识别 153 个用户可见 surface。
- 其中 137 个已经走 `t()` 翻译 key，16 个仍为硬编码。
- 剩余硬编码高度集中，没有发现新的架构级阻塞。

| 文件 | 条目数 | 硬编码数 | 结论 |
|------|--------|----------|------|
| `lib/mail/sender.py` | 18 | 6 | Phase 05 的主工作面，需迁移 SMTP 错误与重试消息 |
| `lib/mail_tui/wizard.py` | 59 | 5 | 主要剩余为默认 provider 选择列表的硬编码显示名 |
| `lib/web/templates/dashboard.html` | 22 | 3 | 仅剩 JS `console.error` 错误文本 |
| `lib/web/templates/mail.html` | 43 | 2 | 仅剩 JS `console.error` 错误文本 |
| `lib/web/routes/daemons.py` | 6 | 0 | API 用户消息已接入翻译系统 |
| `lib/web/routes/mail.py` | 5 | 0 | API 用户消息已接入翻译系统 |

## Revised Estimate

| 批次 | 范围 | 主要内容 | 估算 |
|------|------|----------|------|
| A | `lib/mail_tui/wizard.py` | provider 选择列表去硬编码，补 TUI/向导 smoke | 0.5 天 |
| B | `lib/web/templates/dashboard.html` + `lib/web/templates/mail.html` + `lib/web/app.py` | 清理模板中的 JS 错误文本，确认模板翻译入口对 `en/zh/xx` 一致可用 | 0.5-1 天 |
| C | `lib/web/routes/*.py` | 以回归验证为主，不建议再做大规模改写 | 0.25 天 |
| D | `lib/mail/sender.py` | 迁移 SMTP 连接/重试等剩余文本，确保主题/正文/错误在 pseudo locale 下可见 | 1-1.5 天 |
| E | `tests/test_mail_i18n.py` + `tests/test_web_i18n.py` | Mail/Web/TUI 回归和 pseudo locale 收口 | 0.5-1 天 |

## Conclusion

- Mail/Web/TUI 的翻译接入已经比原先估计更靠前，Phase 05 不再是“从零迁移”，而是“剩余硬编码清扫 + 回归验证”。
- 真正的剩余风险集中在邮件发送链路，因为它同时影响 SMTP 错误、重试日志、主题和正文模板。
- Web API 路由层已基本完成，不建议在 Phase 05 重复改写；应把时间投入模板和 `mail/sender.py`。

## Blocking Items

- `lib/mail/sender.py` 仍有 6 处硬编码，且位于错误链路与重试链路，优先级最高。
- `lib/mail_tui/wizard.py` 的 provider 显示名仍为硬编码列表，需要与现有 `ccb.mail_tui.provider.*` key 对齐。
- 两份模板中的 `console.error(...)` 仍为英文硬编码，虽不影响主 UI，但会让 pseudo locale smoke 不完整。
