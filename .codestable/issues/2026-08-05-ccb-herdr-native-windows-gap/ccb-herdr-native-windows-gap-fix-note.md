---
doc_type: issue-fix-note
issue: ccb-herdr-native-windows-gap
status: fixed
root_cause_type: logic
tags:
  - native-windows
  - herdr-integration
  - herdr-cli-adapter
  - argument-ordering
  - capability-gate
  - spike-harness
  - keeper-state-reset
  - permission-error
  - snapshot-parsing
---

# CCB Native Windows Herdr 集成 gap 修复记录

## 根因

### 发现顺序和时间线

本 issue 经过两轮诊断：

**第一轮（代码审查阶段）**：
- 根因一（主）：`HerdrCliRequestAdapter` 中 `--session` 参数顺序错误
- 根因二（次）：capability evidence 中 `verdict` 字段缺失容错
- 根因三（采集）：`run_spike.ps1` 缺少 3 个采集维度

**第二轮（spike 采集数据分析）**：
- 根因四（阻塞）：外部项目 `D:\C#Project\GitHub\AvaPrintDesigner\.ccb\ccbd\keeper.json` 残留状态未在 prestart cleanup 中重置，导致 `restart_count=20` 和 `keeper_restart_suppressed` 跨会话持续存在
- 根因五（阻塞）：keeper 进程写入 `D:\.c8\rs\<project_id>\ccbd\keeper.json` 时遇到 `PermissionError: [WinError 5] 拒绝访问`（`os.replace` 在 Windows 需要目标目录 DELETE 权限），导致 keeper 持续崩溃无法启动新 ccbd
- 根因六（采集稳定性）：spike 脚本 `api snapshot` JSON 解析不兼容中文路径编码 + `result.snapshot` 嵌套结构

### 根因一（主）：`HerdrCliRequestAdapter` 中 `--session` 参数顺序与 Herdr 0.7.5 不兼容

`lib/terminal_runtime/herdr_backend_runtime/cli.py` 中 3 处将 `--session` 参数放在子命令之前（`herdr --session X status --json`），导致 Herdr 0.7.5 将其解析为 TUI attach 路径而非 machine-readable JSON 路径，所有 CCB → Herdr CLI 交互失败。

此修复与上一轮 spike 脚本修复 `Add-HerdrSessionArgs`（将 `--session` 追加到命令末尾）保持一致。

### 根因二（次）：capability evidence 中 `verdict` 字段缺失容错

`_normalize_herdr_capability_projection()` 在 loaded evidence JSON 缺少 `verdict` 字段时，capability gate 无法 deduce 为 `"partial"`，导致 `herdr_capability_report_supported()` 判定为 malformed。

### 根因三（采集）：`run_spike.ps1` 缺少 3 个采集维度

- CCB 启动期全量状态文件（`lease.json`, `keeper.json`, `lifecycle.json`, `startup-report.json`）
- Pane 物化验证（pane identity tokens + pane content capture）
- Backend resolver 路由证据（diagnose 输出中的 Herdr/backend 相关行 + 环境变量）

### 根因四（阻塞）：`ccb8.ps1` wrapper prestart cleanup 未重置 `.ccb/ccbd/keeper.json`

`Invoke-PrestartCleanup` 调用 `Stop-SourceDevRuntimePids` + `Run-BoundedKillForce` 后，`Reset-SourceDevStateFiles` 只处理了 `D:\.c8\rs\` 下的 `lease.json` 和 `lifecycle.json`，缺失：
1. `D:\.c8\rs\<project_id>\ccbd\keeper.json` 的 reset
2. `.ccb/ccbd/keeper.json` 的 reset

导致前次会话的 `restart_count=20` + `state=failed` + `last_failure_reason=keeper_restart_suppressed` 跨会话持续存在，新的 keeper 进程继承过时状态后无法正确启动 ccbd。

### 根因五（阻塞）：keeper 文件写入权限错误

`keeper.stderr.log` 记录：`PermissionError: [WinError 5] 拒绝访问: '.keeper.json.xxx.tmp' -> 'keeper.json'`

`lib/storage/atomic.py:150` 的 `os.replace(tmp_path, target)` 在 Windows 上需要目标文件的父目录有 DELETE 权限。`D:\.c8\rs\` 下的文件由上一代 keeper（可能在不同用户上下文下）创建，权限归属不一致时 `os.replace` 失败 → keeper 崩溃 → ccbd 无法启动。

### 根因六（采集稳定性）：snapshot JSON 解析失败

`herdr api snapshot` 输出包含中文字符路径 `E:\\GitHub开源项目\\TachiKuma\\claude_code_bridge`，PowerShell `ConvertFrom-Json` 对此编码不兼容。且 snapshot 响应是嵌套结构 `{"result":{"snapshot":{...}}}`，直接从顶层取 `.snapshot` 会拿到 null。

## 改动

### cli.py（3 处参数顺序）

- `lib/terminal_runtime/herdr_backend_runtime/cli.py:1020` — `_command()`: `command = [executable, *args, "--session", effective_session]`
- `lib/terminal_runtime/herdr_backend_runtime/cli.py:1085` — `_start_server()`: `command = [executable, "server", "--session", session_name]`
- `lib/terminal_runtime/herdr_backend_runtime/cli.py:1141` — `_server_status_running()`: `command = [executable, "status", "server", "--json", "--session", session_name]`
- `lib/terminal_runtime/herdr_backend_runtime/cli.py:1372-1380` — `_redacted_argv()`: 修复 send_text 参数 redaction，正确识别 `pane_id` 后、`--session` 前的文本参数位置

### api.py（verdict 容错）

- `lib/terminal_runtime/api.py:289` — `_normalize_herdr_capability_projection()`: 新增 `_deduce_herdr_verdict()` 调用
- `lib/terminal_runtime/api.py:323-328` — 新增 `_deduce_herdr_verdict()`: 当 `adapter_recommendation="continue-with-gaps"` 且 `failure_class="windows-beta-gap"` 且 `verdict` 为空时，auto-derive `verdict="partial"`

### ccb8.ps1（keeper 状态重置 + prestart cleanup 扩展）

- `ccb8.ps1:426-459` — 新增 `Reset-ProjectCcbdStateFiles()`: 重置 `.ccb/ccbd/keeper.json`（`state=stopped`, `restart_count=0`），写入失败时 delete + recreate
- `ccb8.ps1:498-501` — `Invoke-PrestartCleanup()`: 新增调用 `Reset-ProjectCcbdStateFiles`
- `ccb8.ps1:411-416` — `Reset-SourceDevStateFiles()` 的 `keeper.json` 分支: 新增 `restart_count=0` 和 `last_restart_at=$now` 重置

### run_spike.ps1（4 处增强）

- 采集维度 1-3：startup state files、pane verification、backend route evidence（同第一轮）
- `run_spike.ps1:710-732` — `ccb8-ping-all` 改为最多 3 次重试（每次间隔 3 秒），解决 ccbd starting 期间时序竞争
- `run_spike.ps1:799-821` — snapshot 解析容错：`ReadAllText` 使用 UTF-8 编码 + 先尝试 `result.snapshot` 再尝试 `.snapshot` + ConvertFrom-Json 失败时保存 raw text

### test_herdr_backend_client.py（参数顺序断言更新）

- 8 处 `command[1:3] == ["--session", ...]` → `command[-2:] == ["--session", ...]`
- 2 处 `command[-1]` / workspace_id ref 适配
- 1 处 `popen_commands` 断言更新
- 1 处 `pane run` 子命令断言更新
- 1 处 `attach_namespace` 命令断言更新
- 1 处 send_text redaction 测试更新

## 验证

- `python -m pytest test/test_herdr_backend_client.py -q`
  - `169 passed`
- `python -m pytest test/test_json_store.py test/test_ccbd_bootstrap_probe.py test/test_ccbd_windows_tcp_loopback_transport.py test/test_mux_backend_contract.py test/test_terminal_runtime_backend_selection.py test/test_v2_project_namespace_backend.py -q`
  - `257 passed, 1 skipped`（全量）
- `powershell -NoProfile -ExecutionPolicy Bypass -File "run_spike.ps1" -SelfTest`
  - `herdr_ui_integration_spike_selftest: passed`

## 遗留风险

- `--session` 参数顺序改变假设 Herdr 0.7.5+ 接受子命令后 `--session` 作为选项。spike 脚本 `Add-HerdrSessionArgs` 已验证此约定可行
- capability evidence `verdict` auto-derive 仅在 `continue-with-gaps` + `windows-beta-gap` 组合时触发
- `Reset-ProjectCcbdStateFiles` 通过 delete+recreate 处理权限不足的情况，但若目录本身无写权限则仍有残留风险
- keeper `PermissionError`（根因五）可能在 `D:\.c8\rs\` 目录权限不一致时再次出现，prestart cleanup 只能缓解不能从根本上解决 `os.replace` 在 Windows 上的 DELETE 权限要求
- 完整的 Herdr UI 内重跑 spike 是下一步验证的高价值活动
