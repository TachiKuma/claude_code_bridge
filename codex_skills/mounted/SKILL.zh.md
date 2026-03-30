---
name: mounted
description: 以 JSON 输出当前已挂载的 CCB providers
metadata:
  short-description: 以 JSON 输出当前已挂载的 CCB providers
---

# 已挂载 Providers

输出当前项目中哪些 CCB providers 处于“mounted”状态。

## 定义

`mounted = has_session && daemon_on`

## Execution

```bash
ccb-mounted
```
