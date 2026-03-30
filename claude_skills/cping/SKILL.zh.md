---
name: cping
description: 测试 AI provider 连通性
metadata:
  short-description: 测试 AI provider 连通性
---

# 检查 AI Provider 连通性

测试指定 AI provider 的连通性。

## 用法

The first argument must be the provider name:
- `gemini` - Test Gemini
- `codex` - Test Codex
- `opencode` - Test OpenCode
- `droid` - Test Droid
- `claude` - Test Claude

## 执行（强制）

Use `ccb-ping` wrapper to avoid conflict with system `ping`:
```
Bash(ccb-ping $PROVIDER)
```

## 示例

- `/cping gemini`
- `/cping codex`
- `/cping claude`
