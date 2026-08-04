# Herdr UI integration spike

## 目标

这个 spike 用来采集真实 Herdr UI 内运行外部项目 `.\ccb8.cmd` 时的证据，重点区分三类情况：

- `ccb8.cmd` / `ccb8.ps1` 启动链路立即失败，导致短暂 `cmd` 窗口闪退。
- CCB 已经 mounted，但 provider pane / CLI 没有按 `.ccb/ccb.config` materialize。
- Herdr 左侧 agents 面板观察到了 `claude`，但 CCB runtime 仍未取得 provider authority。

Herdr agents panel 的内容目前按人工观察记录；除非 Herdr CLI 暴露该状态，否则它不能作为 CCB completion/runtime authority。

## 运行方式

必须在真实 Herdr UI client 的 PowerShell pane 中运行。不要在 Codex 终端里直接启动外部项目 CCB。

```powershell
$repo = "E:/GitHub开源项目/TachiKuma/claude_code_bridge"
$project = "D:/C#Project/GitHub/AvaPrintDesigner"
$out = "$repo/.codestable/roadmap/windows-native-herdr-ccb/drafts/herdr-ui-integration-spike/evidence/run-$(Get-Date -Format yyyyMMdd-HHmmss)"

& "$repo/.codestable/roadmap/windows-native-herdr-ccb/drafts/herdr-ui-integration-spike/run_spike.ps1" `
  -ProjectRoot "$project" `
  -Ccb8Path "$project/ccb8.cmd" `
  -RepoRoot "$repo" `
  -OutputDir "$out" `
  -ExpectedAgents 2 `
  -ObservedWindowsFlash `
  -ObservedHerdrAgentsPanelText "claude"
```

如果只是检查脚本本身，不启动 CCB：

```powershell
& "E:/GitHub开源项目/TachiKuma/claude_code_bridge/.codestable/roadmap/windows-native-herdr-ccb/drafts/herdr-ui-integration-spike/run_spike.ps1" -SelfTest
```

## 产物

脚本会写入：

- `summary.json`：机器可读结论和每条命令的引用。
- `report.md`：人工阅读摘要。
- `host-context.json`：Herdr/CCB 环境上下文，敏感字段会做基础脱敏。
- `process-samples.jsonl`：运行 `ccb8.cmd` 前后的短周期进程采样，用来抓短暂 `cmd.exe` / `powershell.exe` / `python.exe` / provider 进程。
- `raw-command-refs/*.json|*.txt`：`herdr`、`ccb8 --diagnose`、`ccb8`、`ping`、`doctor ps`、`layout status`、`doctor --output` 等命令证据。
- `manual-observation.md`：Herdr 左侧 agents panel 与窗口闪退的人工观察补充位。

Herdr 0.7.5 的 `workspace list` / `pane list` 不支持 `--json`；脚本使用 `api snapshot` 采集机器可读 workspace/pane 状态。

`ccb8-start-project` 是启动证据点：脚本只确认它已启动并继续采样，不等待它阻塞主采集流程。不要默认使用 `-n`；当前证据显示 `ccb8.cmd -n` 会先触发 `Refresh project memory/context ... [y/N]` 交互确认，容易让自动采集卡在 reset prompt 上。

## 判读规则

- `blocked-not-herdr-ui`：既没有 `HERDR_ENV`，也没有 Herdr agents 面板等人工观察证据，证据不能回答 UI integration 问题。
- `ccb8-start-failed`：启动命令本身失败，优先看 `ccb8-start-project.stderr.txt` 和 `process-samples.jsonl`。
- `ccb-mounted-not-proven`：`ping ccbd` 没证明 mounted。
- `ccb-provider-ping-not-proven`：`ping ccbd` 已 mounted，但 `ping all` 未成功证明 provider runtime 状态。
- `mounted-but-layout-materialization-missing`：CCB mounted，但 `ccb8 layout status --json` 中未看到期望数量的 provider pane id。
- `mounted-but-panel-observation-missing`：CCB mounted 且 layout materialized，但还缺 Herdr agents panel 的人工观察。
- `mounted-with-herdr-panel-observation`：CCB mounted、`ping all` 成功、layout materialized，且记录了 Herdr panel 观察。

## 备份

清理外部项目残留前，`D:/C#Project/GitHub/AvaPrintDesigner/ccb8.cmd` 和 `ccb8.ps1` 已备份到：

```text
.codestable/roadmap/windows-native-herdr-ccb/drafts/herdr-ui-integration-spike/backups/
```

再次运行真实 UI spike 前，需要先把对应备份恢复到外部项目根目录，或显式用 `-Ccb8Path` 指向可执行 wrapper。

## 边界

- 不修改生产代码。
- 不执行 git commit / push / release。
- 不把 Herdr agent detection 当作 provider completion authority。
- 不宣称 Native Windows supported。
