# CCB i18n Migration Strategy

## 1. Scope Decision

- 继续沿用 Phase 04/05 已建立的统一翻译入口，不重新设计新的 i18n 抽象。
- 把 `i18n_surface_inventory.md` 中的 16 个剩余硬编码作为 Phase 05 的唯一新增迁移目标。
- 对已经走 `t()` 的 API 路由保持最小改动，只做回归验证，避免无效 churn。

## 2. Targeted Migration Plan

### Batch A: Mail TUI

- 文件：`lib/mail_tui/wizard.py`
- 剩余问题：默认 provider 选择列表仍然直接 `print("  1. Claude")` 等硬编码。
- 策略：新增或复用 `ccb.mail_tui.provider.*` / `ccb.mail_tui.simple.*` key，统一通过 `t()` 输出 provider 显示名。

### Batch B: Web Templates

- 文件：`lib/web/templates/dashboard.html`、`lib/web/templates/mail.html`
- 剩余问题：模板主体已翻译，但 `<script>` 中仍有 `console.error('Failed to fetch ...')`。
- 策略：把这类错误文本并入 `ccb.web.dashboard.*` / `ccb.web.mail.*`，通过模板注入的 `ui` 常量使用，保持 `en/zh/xx` 一致。

### Batch C: Web API

- 文件：`lib/web/routes/daemons.py`、`lib/web/routes/mail.py`
- 当前状态：用户可见 `message/detail` 已基本全部来自 `t()`。
- 策略：Phase 05 不主动重构，只补测试，确保 API 返回消息在 `zh` 与 `xx` 下可验证。

### Batch D: Mail Sender

- 文件：`lib/mail/sender.py`
- 剩余问题：
  - `No password stored for ...`
  - `SMTP connection failed: ...`
  - `Failed to connect to SMTP`
  - `[smtp] Retry ... after error: ...`
- 策略：统一迁移到 `ccb.mail.sender.*` 命名空间，错误与重试日志都走 `t()`，并让 pseudo locale 覆盖主题、正文和错误输出。

## 3. Namespace Guidance

| 表面 | 命名空间 |
|------|----------|
| Mail TUI 向导与 Textual UI | `ccb.mail_tui.*` |
| Dashboard 模板与脚本 | `ccb.web.dashboard.*` |
| Mail 页面模板与脚本 | `ccb.web.mail.*` |
| Web API 返回消息 | `ccb.web.mail_api.*` / `ccb.web.daemons.*` |
| SMTP 连接、重试、主题、正文 | `ccb.mail.sender.*` |

## 4. Execution Order

1. `lib/mail_tui/wizard.py`
2. `lib/web/templates/dashboard.html`
3. `lib/web/templates/mail.html`
4. `lib/mail/sender.py`
5. `tests/test_mail_i18n.py` + `tests/test_web_i18n.py`

## 5. Verification Strategy

- 每完成一个批次就运行对应 smoke，而不是等所有文件改完再总测。
- Web 侧重点：
  - 模板渲染结果在 `CCB_LANG=zh` / `CCB_LANG=xx` 下可见翻译文本或 pseudo marker
  - API `message/detail` 不再回退为裸英文硬编码
- Mail 侧重点：
  - SMTP 错误、测试邮件主题/正文、pane output 邮件都能看到 `zh` / `xx` 结果
  - pseudo locale 不破坏主题格式和正文结构
