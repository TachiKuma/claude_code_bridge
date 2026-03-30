---
name: ask
description: 将用户请求异步发送给指定 AI provider
metadata:
  short-description: 将用户请求异步发送给指定 AI provider
---

# 询问 AI Provider

通过 ask 将用户请求发送给指定 AI provider。

## 用法

The first argument must be the provider name. The message MUST be provided via stdin
(heredoc or pipe), not as CLI arguments, to avoid shell globbing issues:
- `gemini` - Send to Gemini
- `claude` - Send to Claude
- `opencode` - Send to OpenCode
- `droid` - Send to Droid

## 执行（强制）

```bash
CCB_CALLER=codex ask $PROVIDER <<'EOF'
$MESSAGE
EOF
```

## 规则

- After running the command, say "[Provider] processing..." and immediately end your turn.
- Do not wait for results or check status in the same turn.
- The task ID and log file path will be displayed for tracking.

## 示例

- `/ask gemini What is 12+12?` (send via heredoc)
- `CCB_CALLER=codex ask gemini <<'EOF'`
  `What is 12+12?`
  `EOF`

## 说明

- If it fails, check backend health with the corresponding ping command (`ccb-ping <provider>` (e.g., `ccb-ping gemini`)).
- Codex-managed sessions default to foreground; use `--background` or `CCB_ASK_BACKGROUND=1` for async.
