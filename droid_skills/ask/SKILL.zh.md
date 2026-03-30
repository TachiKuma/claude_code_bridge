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
- `codex` - Send to Codex
- `opencode` - Send to OpenCode
- `claude` - Send to Claude
Optional flags after the provider:
- `--foreground` / `--background`
- Env overrides: `CCB_ASK_FOREGROUND=1` / `CCB_ASK_BACKGROUND=1`

## 执行（强制）

```bash
CCB_CALLER=droid command ask "$PROVIDER" <<'EOF'
$MESSAGE
EOF
```

## 规则

- STRICT: Execute the bash snippet in the Execution section, then immediately end your turn.
- Do not run any other commands/tools besides this snippet (no `gask/cask/oask/lask/dask`, no `pend`, no `ping`, no retries) unless the user explicitly asks.
- Do not add any extra commentary/output (including "processing..."); the `ask` command already prints the task id and log path.
- Do not wait for results or check status in the same turn.

## 示例

- `/ask gemini What is 12+12?` (send via heredoc)
- `CCB_CALLER=droid command ask gemini <<'EOF'`
  `What is 12+12?`
  `EOF`

## 说明

- If it fails, stop after reporting the failure output; only run diagnostics in a new turn if the user requests it.
