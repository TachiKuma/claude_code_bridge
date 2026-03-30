---
name: continue
description: 附加当前项目最新 context-transfer 历史文件
---

# Continue（附加最新历史）

## 概述

Find the newest Markdown in `./.ccb/history/` (or legacy `./.ccb_config/history/`) and reply with an `@file` reference so Claude loads it.

## 流程

1. Locate the newest `.md` under the current project's history folder.
2. If none exists, report that no history file was found.
3. Reply with a single line `@<path>` and nothing else.

## 执行（强制）

```bash
latest="$(ls -t "$PWD"/.ccb/history/*.md 2>/dev/null | head -n 1)"
if [[ -z "$latest" ]]; then
  latest="$(ls -t "$PWD"/.ccb_config/history/*.md 2>/dev/null | head -n 1)"
fi
if [[ -z "$latest" ]]; then
  echo "No history file found in ./.ccb/history."
  exit 0
fi
printf '@%s\n' "$latest"
```

## 输出规则

- When a history file exists: output only `@<path>` on a single line.
- When none exists: output the error message and stop.

## 示例

- `/continue` -> `@/home/bfly/workspace/hippocampus/.ccb/history/claude-20260208-225221-9f236442.md`
