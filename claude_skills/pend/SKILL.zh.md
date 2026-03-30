---
name: pend
description: 查看 AI provider 最新回复
metadata:
  short-description: 查看 AI provider 最新回复
---

# Pend - 查看最新回复

查看指定 AI provider 的最新回复。

## 用法

The first argument must be the provider name:
- `gemini` - View Gemini reply
- `codex` - View Codex reply
- `opencode` - View OpenCode reply
- `droid` - View Droid reply
- `claude` - View Claude reply

Optional: Add a number N to show the latest N conversations.

## 执行（强制）

```bash
pend $ARGUMENTS
```

## 示例

- `/pend gemini`
- `/pend codex 3`
- `/pend claude`
