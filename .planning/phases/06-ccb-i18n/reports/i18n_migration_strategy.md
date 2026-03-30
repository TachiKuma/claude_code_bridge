# CCB i18n Migration Strategy

## 1. Mail TUI

- `run_simple_wizard()` 的 `print()/input()/getpass()` 文案统一迁移到 `ccb.mail_tui.*`
- Textual `Static/Label/Button` 文案通过常量或 helper 统一出键，避免把字符串散落在多个 Screen 类里

## 2. Web Templates

- 在 `lib/web/app.py` 中注入模板 helper，例如 `t` 或 `translations`
- `dashboard.html`、`mail.html` 不再直接写静态英文
- 模板中的按钮、标题、说明文案走 `ccb.web.dashboard.*` / `ccb.web.mail.*`

## 3. Web API

- `HTTPException(detail=...)` 的用户可见 detail 统一走翻译 key
- `{success, message}` 返回体中的 `message` 统一走翻译 key
- provider、daemon 名称继续保留协议含义，不本地化

## 4. Mail Sender

- 主题和正文模板拆到 `ccb.mail.sender.*`
- 允许保留 provider 名称和 thread id，但提示文案必须可翻译
- 伪本地化必须能覆盖正文和主题，便于检查截断与显示

## 5. Execution Order

1. `wizard.py`
2. `dashboard.html` / `mail.html`
3. `web/routes/*.py`
4. `mail/sender.py`
5. 回归与 pseudo locale smoke
