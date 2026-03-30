---
name: ask
description: 将用户请求异步发送给指定 AI provider
metadata:
  short-description: 将用户请求异步发送给指定 AI provider
---

# 询问 AI Provider（异步）

Send the user's request to specified AI provider asynchronously.

## 用法

The first argument must be the provider name, followed by the message:
- `gemini` - Send to Gemini
- `codex` - Send to Codex
- `opencode` - Send to OpenCode
- `droid` - Send to Droid

## 执行（强制）

```
Bash(CCB_CALLER=claude ask $PROVIDER "$MESSAGE")
```

## 规则

- Follow the **Async Guardrail** rule in CLAUDE.md (mandatory).
- Local fallback: if output contains `CCB_ASYNC_SUBMITTED`, end your turn immediately.
- If submit fails (non-zero exit):
  - Reply with exactly one line: `[Provider] submit failed: <short error>`
  - End your turn immediately.

## 示例

- `/ask gemini What is 12+12?`
- `/ask codex Refactor this code`
- `/ask opencode Analyze this bug`
- `/ask droid Execute this task`

