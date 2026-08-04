---
doc_type: issue-fix-note
issue: 2026-08-04-herdr-ui-integration-ccbd-bootstrap
status: fixed
fixed: 2026-08-04
scope: spike-harness-followup
---

# Herdr UI integration spike harness 后续修复

## 问题

`run-20260804-222025` 已证明 CCB 在 Herdr 中 mounted，`ping all` 成功，且两个静态 provider pane 已 materialize：

- `agent1` / `codex` -> `mux:w1:p3`
- `agent2` / `claude` -> `mux:w1:p4`

但采集仍有两个 harness 异常：

- `herdr status server --json` / `herdr api snapshot` 在脚本中超时，并捕获到 TUI ANSI 输出。
- `ccb8-wrapper-self-test` 返回 `command_status: invalid` / `invalid start command`。

## 根因

- Herdr 0.7.5 的命令参数解析要求子命令在前、`--session` 作为命令选项在后；脚本原先生成 `herdr --session <name> status server --json`，会走 attach/TUI 路径。
- 外部项目 `D:/C#Project/GitHub/AvaPrintDesigner/ccb8.ps1` 不是仓库根当前 wrapper 模板，不支持 `--wrapper-self-test`。脚本把该私有自测协议当作外部 wrapper 必备能力，导致命令落到 `ccb.py --wrapper-self-test` 后被 start parser 拒绝。
- 仓库根 `ccb8.ps1` 的 `--wrapper-self-test` 分支执行后未 `exit 0`，也存在 fallthrough 风险。
- `observed_windows_flash=true` 的最新进程样本中，可见 CCB wrapper 预启动链路 `cmd.exe -> powershell.exe -> ccb8.ps1 -> python.exe ccb.py kill -f`。其中 `Run-BoundedKillForce` 仍使用 `Start-Process -WindowStyle Hidden`，在 Herdr/Windows 控制台组合下仍可能制造短暂外部窗口。

## 改动

- `run_spike.ps1` 新增 `Add-HerdrSessionArgs`，把 Herdr session 参数追加到子命令后：
  - `herdr status server --json --session <name>`
  - `herdr api snapshot --session <name>`
- `run_spike.ps1` 不再调用外部 wrapper 的 `--wrapper-self-test`，改为 `ccb8-wrapper-file-check`，只检查 `ccb8.cmd` / `ccb8.ps1` 存在且没有 UTF-8 BOM。
- `run_spike.ps1` 的 `ccb8-start-project` detached 启动不再使用 `Start-Process -WindowStyle Hidden`，改为 `System.Diagnostics.ProcessStartInfo`，并显式设置 `UseShellExecute=false`、`CreateNoWindow=true`，降低 `cmd.exe -> powershell.exe` 启动链路制造外部控制台闪窗的概率。
- 仓库根 `ccb8.ps1` 的 `--wrapper-self-test` 分支补 `exit 0`，避免自测通过后继续执行主 CLI。
- 仓库根和外部项目 `D:/C#Project/GitHub/AvaPrintDesigner/ccb8.ps1` 的 `Run-BoundedKillForce` 改为 `ProcessStartInfo`，显式设置 `UseShellExecute=false`、`CreateNoWindow=true` 并重定向 stdout/stderr，避免预启动 `python ccb.py kill -f` 子进程弹出外部控制台。

## 验证

- `powershell -NoProfile -ExecutionPolicy Bypass -File ".codestable/roadmap/windows-native-herdr-ccb/drafts/herdr-ui-integration-spike/run_spike.ps1" -SelfTest` -> passed
- `herdr status server --json --session "ccb-herdr-avaprintdesigner-source-dev"` -> 立即返回 JSON，不再进入 TUI
- `D:/C#Project/GitHub/AvaPrintDesigner/ccb8.cmd --diagnose` -> exit 0
- `E:/GitHub开源项目/TachiKuma/claude_code_bridge/ccb8.ps1 --wrapper-self-test` -> `wrapper_self_test: passed`
- `D:/C#Project/GitHub/AvaPrintDesigner/ccb8.ps1 --wrapper-self-test` -> `wrapper_self_test: passed`
- 静态搜索确认仓库根和外部项目 `ccb8.ps1` 中已无 `Start-Process` / `WindowStyle`，预启动清理路径记录 `CreateNoWindow=true`
- `run-20260804-230805` 复验后 Herdr CLI 和 wrapper file check 均已 exit 0；后续闪窗 mitigation 需要再跑一次真实 UI spike，确认 `ccb8-start-project.json` 中 `create_no_window=true` 且 owner 不再观察到外部窗口闪现。
- `run-20260805-040538` 已确认 `observed_windows_flash=false`，同时 `ping_all_success=true`、`layout_materialized_count=2`、`layout_materialization_complete=true`；这是当前链路下闪窗问题关闭的最终证据。

## 遗留风险

- 真实 Herdr UI pane 内后续只需做稳定性回归，闪窗问题本身已在 `run-20260805-040538` 中关闭。
- 若仍闪现，当前证据应继续区分 CCB 可控 `ccb8-start-project` 链路和环境中已有的 `codegraph.cmd` / `codex-dual` 噪声，不再把它和 layout materialization 混为同一个阻塞项。
