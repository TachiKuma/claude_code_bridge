---
name: autonew
description: 向 provider 面板发送 /new 开启新会话
metadata:
  short-description: 向 provider 面板发送 /new 开启新会话
---

# 自动新建会话

Send `/new` command directly to a provider's terminal pane to start a new session.

## 用法

```
autonew <provider>
```

Providers: gemini, codex, opencode, droid, claude

## 执行（强制）

```bash
autonew $PROVIDER
```

## 规则

- This command sends `/new` directly to the provider's pane without any wrapping.
- Use this to clear/reset a provider's session.

## 示例

- `/autonew gemini` - Start new Gemini session
- `/autonew codex` - Start new Codex session
