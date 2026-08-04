---
doc_type: follow-up
slug: herdr-ui-integration-spike
status: active
created: 2026-08-04
source_brainstorm: .codestable/brainstorms/windows-native-herdr-ccb/brainstorm.md
---

# herdr-ui-integration-spike

## 背景

owner 在外部项目中从 Herdr 内置 PowerShell 运行 `.\ccb8.cmd` 时，没有看到 `.ccb/ccb.config` 定义的两个 agent CLI 对话界面，只观察到多个 `cmd` 窗口短暂闪现后关闭；闪退前 Herdr 左侧 agents 面板曾出现 `claude`。在 Herdr 中手动启动 `claude` 表现正常，但这只证明 Herdr 能承载 Claude CLI，不证明 CCB provider runtime 已接管。

## Spike 产物

- Harness：`.codestable/roadmap/windows-native-herdr-ccb/drafts/herdr-ui-integration-spike/run_spike.ps1`
- Runbook：`.codestable/roadmap/windows-native-herdr-ccb/drafts/herdr-ui-integration-spike/README.md`
- Evidence 目录：`.codestable/roadmap/windows-native-herdr-ccb/drafts/herdr-ui-integration-spike/evidence/`

## 验证目标

- 必须在真实 Herdr UI client 的 PowerShell pane 内运行，要求 `HERDR_ENV` 或等价 Herdr UI 环境存在。
- 捕获运行 `ccb8.cmd` 前后的 Herdr session/workspace/pane 状态；Herdr 0.7.5 的 workspace/pane 机器可读状态来自 `api snapshot`，不调用 `workspace list --json` / `pane list --json`。
- `-n` reset path 会触发交互确认，不作为 UI integration 主路径。
- 以 200ms 采样 `cmd.exe`、`powershell.exe`、`python.exe`、`node.exe`、`claude.exe`、`herdr.exe` 等进程，抓取短暂闪退窗口的 PID/命令行证据。
- 捕获 `ccb8 --diagnose`、`ccb8`、`ping ccbd`、`ping all`、`ps`、`doctor ps`、`layout status`、`doctor --output` 的 stdout/stderr 和 exit code。
- 记录 Herdr 左侧 agents panel 的人工观察；除非 Herdr CLI 暴露该状态，否则它只能作为 diagnostics evidence。

## 判定口径

- 若 `ccb8.cmd` 启动失败，优先归为 source/dev wrapper 或启动链路失败。
- 若 `ping ccbd` 已 mounted 但 `ping all` 未成功，优先归为 provider runtime 状态未证明。
- 若 CCB mounted 但 `ccb8 layout status --json` 没有两个 provider pane id，优先归为 layout/materialization projection gap。
- 若 Herdr panel 显示 `claude` 但 CCB runtime state 失败，必须保持 CCB provider authority，Herdr agent detection 只进 diagnostics。
- 本 spike 不宣称 Native Windows supported，不改变 support tier。

## 最新进展：2026-08-04

- 外部项目 `ccb8` 残留已清理；`ccb8.cmd` / `ccb8.ps1` 已先备份到 spike `backups/` 目录。
- `JsonStore.load()` 已加启动期短重试和路径化 `invalid JSON` 错误，降低 ccbd bootstrap 阶段被瞬时状态文件损坏打断的概率。
- 最新 run `run-20260804-205310` 显示 CCB 已 mounted，但 `layout_materialized_count=0`；doctor bundle 记录 `start_flow_failed`，`failure_reason=unknown option: --json`。
- Herdr adapter 不再对 list 命令追加 `--json`，并在 list 失败或输出不可解析时回退 `api snapshot`；spike harness 也改为采集 `api snapshot`，避免 Herdr 0.7.5 的 list 命令卡住或报 `unknown option`。
- spike harness 改为采集 `ccb8 layout status --json`，并新增 `layout_materialization_complete` 判定。
- spike harness 分类已把 `ping all` 成功纳入 layout materialized / panel observation 通过类前置。
- 当前下一次真实 UI 验收闭环是：在 Herdr pane 内运行 spike，先要求 `ccb8-start-project.stderr.txt` 不再出现 `unknown option: --json`，再要求 `ping ccbd` mounted、`ping all` 成功、`layout_materialized_count >= expected_agents`。
