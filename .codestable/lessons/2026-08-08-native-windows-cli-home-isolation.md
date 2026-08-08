---
status: observed
scope: Native Windows 启动 / CLI 运行时隔离
date: 2026-08-08
---
规则：`.\ccb8.cmd` 这类 native Windows/source-dev 启动路径要把 CLI 视作“受管但干净”的运行时，`HOME`、`USERPROFILE`、`XDG_*`、`CODEX_HOME` 等应指向项目或受管私有目录，而不是复用用户系统配置；provider home 解析继续以受管 home + 选择性投影为准。
适用 / 不适用：适用于 native Windows 或 source-dev 启动时的 CLI 配置隔离、provider 登录态和模型缓存投影；不适用于显式要求读取真实用户全局 profile，或通过 `CCB_SOURCE_HOME` 明确指定来源 home 的场景。
证据：
- [ccb8.ps1](../ccb8.ps1)
- [provider_core/source_home.py](../lib/provider_core/source_home.py)
- [provider_backends/native_cli_support/home.py](../lib/provider_backends/native_cli_support/home.py)
候选归宿：project-doc
