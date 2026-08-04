# Herdr UI integration ccbd bootstrap 问题报告

## 现象

在外部项目 `D:/C#Project/GitHub/AvaPrintDesigner` 中，从 Herdr 内置 PowerShell 运行 `.\ccb8.cmd` 后，没有出现 `.ccb/ccb.config` 定义的两个 provider CLI pane，只观察到多个 `cmd` 窗口短暂闪现。闪现期间 Herdr 左侧 agents 面板曾出现 `claude`。

## 采集证据

- spike run：`.codestable/roadmap/windows-native-herdr-ccb/drafts/herdr-ui-integration-spike/evidence/run-20260804-200104`
- 分类：`ccb-mounted-not-proven`
- `ccb8-ping-ccbd`：`ccbd is unavailable: lease_missing`
- `ccb8-ping-all`：`project ccbd is starting; wait for keeper to finish startup`
- `ccb8-layout-status`：配置里有 `agent1:codex`、`agent2:claude`，但两个 agent 都是 `state=missing`、`pane=None`
- keeper 记录：`restart_count=20`，最后进入 `keeper_restart_suppressed:max_start_failures`

## 影响

Herdr 能显示 `claude` 只能作为 UI/diagnostics 观察，不能证明 CCB runtime 已 mounted，也不能证明 CCB provider pane 已 materialize。

