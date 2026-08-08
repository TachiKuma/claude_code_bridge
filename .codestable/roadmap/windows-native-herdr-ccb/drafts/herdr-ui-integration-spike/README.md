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

### Watch 模式：持续采集（2026-08-08 新增，推荐）

利用 wezterm 多 tab，持续观察其他 tab/pane 中的 CCB 相关信息，直到 Ctrl+C 结束：

1. 在 wezterm 的**第一个 tab** 启动 Watch 模式。
2. 在**其他 tab** 手动启动 CCB（如 `.\ccb8.cmd`）或操作 herdr。
3. 脚本持续读取这些 tab/pane 的终端文本、采样 CCB 相关进程、可选查询 herdr
   status，全部按时间序列记录。
4. 按 Ctrl+C 结束采集。**不主动执行 `.\ccb8.cmd`，也不清理任何 CCB 后台进程**
   （CCB 由你启动，归你所有）。

```powershell
& "$repo/.codestable/roadmap/windows-native-herdr-ccb/drafts/herdr-ui-integration-spike/run_spike.ps1" `
  -WatchMode `
  -ProjectRoot "$project" `
  -RepoRoot "$repo" `
  -WatchPollIntervalMs 2000 `
  -WatchProcessInterval 5
```

Watch 模式每次采集写入**独立子目录**
`…/herdr-ui-integration-spike/watch/watch-<yyyyMMdd-HHmmss>/`（与全量采集
`evidence/run-<ts>` 语义一致），不使用 `-OutputDir`。

Watch 模式参数：

- `-WatchMode`：启用持续采集模式。
- `-WatchPollIntervalMs`：轮询间隔（默认 2000ms）。
- `-WatchProcessInterval`：每 N 轮采样一次进程（默认 5）。
- `-WatchHerdrStatusInterval`：每 N 轮查询一次 `herdr status server --json`
  （默认 0 = 关闭）。
- `-WatchRecentEvents`：UI 显示最近事件数（默认 8）。
- `-WatchMaxPolls`：最多轮询 N 次后正常退出（默认 0 = 无限，直到 Ctrl+C）。
- `-WatchIncludeSelfPane`：默认排除自身 pane，加此参数则一并监控。
- `-WatchKeywords`：自定义文本过滤关键词，覆盖默认集（ccb/ccbd/herdr/codex/
  claude/keeper/provider/mount/pane/session 等）。
- `-WatchSelfTest`：watch 纯函数自检（不实际运行监控）。

Watch 模式产物（`watch/watch-<timestamp>` 下）：

- `watch-manifest.json`：启动配置（路径、关键词、自身 pane、轮询参数）。
- `watch-events.jsonl`：逐条记录每个 pane 的 CCB 相关文本行，含 pane/tab/
  window/title 归属。
- `process-samples-watch.jsonl`：周期性进程采样（ccbd/keeper/provider/herdr 等）。
- `herdr-status-watch.jsonl`：周期性 herdr status（开启 `-WatchHerdrStatusInterval` 时）。
- `watch-live.json`：实时状态（轮询计数、事件数、进程数），可被外部工具读取。
- `watch-config-access.jsonl`：**配置访问监控**（方案 A）——轮询关键配置文件的
  `LastAccessTime`/`LastWriteTime`，记录 cli 读取/修改配置的时机（cli 加载
  配置的过程在 python 进程内不可见，pane 文本看不到；NTFS `LastAccessTime`
  随读取更新，以此探测）。监控文件：
  - 项目：`<project>/.ccb/ccb.config`、`runtime-root-ref.json`、`project.identity.json`
  - 用户：`~/.ccb/ccb.config`、`.ccb-source-dev/home/.ccb/ccb.config`
  - 全局：`~/.claude/settings.json`、`~/.claude/config.json`、`~/.claude.json`、
    `~/.codex/config.toml`、`~/.codex/auth.json`
  事件类型：`config-read`（cli 读了该配置）、`config-modified`（配置被改写）、
  `config-appeared`/`config-disappeared`。
- `watch-summary.json`：Ctrl+C 结束时的汇总。

**Watch 模式与一次性采集的区别：**

| 维度 | 一次性采集（默认） | Watch 模式 |
|---|---|---|
| 启动 CCB | 主动执行 `.\ccb8.cmd` | 不主动执行，由你在其他 tab 启动 |
| 结束方式 | 全部维度跑完自动结束 | 持续运行直到 Ctrl+C |
| 清理后台 | finally 清理残留进程 | 不做任何清理（CCB 归你所有）|
| 可视化 | Write-Progress 进度条 | 实时状态块 + 旋转动画 + 最近事件滚动 |
| 采集粒度 | 一次性维度快照 | 持续时间序列记录 |

如果只是检查脚本本身，不启动 CCB：

```powershell
& "E:/GitHub开源项目/TachiKuma/claude_code_bridge/.codestable/roadmap/windows-native-herdr-ccb/drafts/herdr-ui-integration-spike/run_spike.ps1" -SelfTest
```

## 产物

脚本会写入：

- `summary.json`：机器可读结论和每条命令的引用。
- `report.md`：人工阅读摘要。
- `host-context.json`：Herdr/CCB 环境上下文，敏感字段会做基础脱敏。
- `process-samples.jsonl`：运行 `ccb8.cmd` 前后的进程采样，用来抓短暂 `cmd.exe` / `powershell.exe` / `python.exe` / provider 进程；需要覆盖启动后 steady-state 时，可把 `ProcessSampleSeconds` 设得更长。
- `raw-command-refs/*.json|*.txt`：`herdr`、`ccb8 --diagnose`、`ccb8`、`ping`、`doctor ps`、`layout status`、`doctor --output` 等命令证据。
- `manual-observation.md`：Herdr 左侧 agents panel 与窗口闪退的人工观察补充位。

Herdr 0.7.5 的 `workspace list` / `pane list` 不支持 `--json`；脚本使用 `api snapshot` 采集机器可读 workspace/pane 状态。带 session 的 Herdr 子命令必须使用 `herdr <subcommand> ... --session <name>`，不要使用 `herdr --session <name> <subcommand>`，否则会进入 attach/TUI 路径。

`ccb8-wrapper-file-check` 只验证外部项目 `ccb8.cmd` / `ccb8.ps1` 文件存在且没有 UTF-8 BOM。外部 wrapper 不要求支持仓库根模板的私有 `--wrapper-self-test` 参数；真实启动链路由 `ccb8 --diagnose` 和 `ccb8` 主启动继续验证。

`ccb8-start-project` 使用 `UseShellExecute=false` 和 `CreateNoWindow=true` 启动，避免 spike 自己的 `cmd.exe -> powershell.exe` 链路创建外部控制台窗口。外部项目 `ccb8.ps1` 的预启动 `python ccb.py kill -f` 清理也应使用 `CreateNoWindow=true`；若后续仍观察到闪窗，优先用 `process-samples.jsonl` 区分 CCB wrapper 链路与环境中已有的 `codegraph.cmd` / `codex-dual` 控制台进程。命令引用中会记录 spike 启动属性；`observed_windows_flash` 仍是人工观察字段。

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

当前外部项目根目录已有可执行 wrapper，可直接用于真实 UI spike。上述备份只作为回滚点保留。

## 边界

- 不修改生产代码。
- 不执行 git commit / push / release。
- 不把 Herdr agent detection 当作 provider completion authority。
- 不宣称 Native Windows supported。
