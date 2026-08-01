---
doc_type: feature-ff-note
feature: project-source-wrapper
date: 2026-07-23
requirement:
tags: [windows, powershell, source-runtime, wrapper]
---

## 做了什么

给外部 `CodeStable` 项目新增项目内 `ccb-src` wrapper，可从该项目直接运行本仓库源码版 `ccb.py`，且不修改已安装的全局 `ccb`。

## 改了哪些

- `D:/C#Project/GitHub/CodeStable/.codestable/tools/ccb-src.ps1` - 新增 PowerShell wrapper，推导项目根目录、定位源码仓库、临时注入 `CCB_SOURCE_ALLOWED_ROOTS` 后转发参数。
- `D:/C#Project/GitHub/CodeStable/.codestable/tools/ccb-src.cmd` - 新增 CMD shim，便于 WezTerm/CMD 场景调用同一个 PowerShell wrapper。
- `D:/C#Project/GitHub/CodeStable/.ccb/ccb.config` - 将本机忽略的旧式 provider 列表迁移为 `agent_name:provider` layout 格式。

## 怎么验证的

已验证 `ccb-src.ps1 --help` 与 `ccb-src.cmd --help` 均返回 0；调用前后全局 `ccb` 仍解析到 `C:/Users/Administrator/AppData/Local/codex-dual/bin/ccb.bat`，`CCB_SOURCE_ALLOWED_ROOTS` 未泄漏到调用 shell。另跑 `ccb-src.ps1 config validate --json`，源码 wrapper 成功进入外部项目配置校验，返回的是该项目 `.ccb/ccb.config` 自身的 invalid token 诊断。
复审修复后补充验证：`ccb-src.cmd --project C:/` 与 `ccb-src.cmd --project=C:/` 均返回非 0，证明项目内 wrapper 会拒绝覆盖绑定项目；`CCB_SRC_EXIT_PROCESS` 也不会泄漏到调用 shell。
二次复审修复后补充验证：`ccb-src.cmd --project "<当前项目>" --help` 与 `ccb-src.cmd --project="<当前项目>" --help` 都返回非 0，且输出命中 wrapper 自身的 `does not accept --project overrides` 拒绝信息；`ccb-src.cmd config validate --json` 对外传播非零退出码。
配置迁移后补充验证：`ccb-src.ps1 config validate --json` 返回 `config_status: valid`，layout 为 `codex:codex, gemini:gemini, opencode:opencode, claude:claude`；`ccb-src.ps1 doctor` 能进入 source install 诊断。
