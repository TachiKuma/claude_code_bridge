---
doc_type: issue-report
issue: ccb-herdr-native-windows-gap
status: confirmed
severity: P1
summary: CCB在Native Windows环境中配合Herdr运行时，采集脚本广度不够，且CCB-Herdr集成存在系统性gap导致无法稳定运行
tags:
  - native-windows
  - herdr-integration
  - ccbd-bootstrap
  - spike-harness
  - terminal-runtime
---

# CCB Native Windows Herdr 集成 gap 问题报告

## 1. 问题现象

**问题一：采集脚本广度不够**

`run_spike.ps1` 当前的采集覆盖主要聚焦在 CCB control-plane 状态（`ccb8 ping`、`ccb8 ps`、`ccb8 layout status`）和 Herdr server 基线（`herdr status server --json`、`herdr api snapshot`），但缺少以下关键维度的采集：

- Herdr pane 级别的物化验证（pane 是否实际创建、pane 内容是否可捕获）
- Herdr 命名空间元数据深度检查（token、agent label、namespace epoch）
- CCB 后端解析器实际路由结果检查（哪个 backend 被选中、capability 检查是否通过）
- CCB 启动期完整状态文件采集（startup-report.json、keeper state、supervisor state）
- CCB 磁盘层产物的快照（`.ccb/` 目录下关键文件的完整采集）
- Herdr session 级别健康状况（所有 session 列表、session liveness）

**问题二：CCB 无法在 Native Windows 环境中配合 Herdr 正常运行**

基于历史 issue trail (`herdr-ui-integration-ccbd-bootstrap`)，之前已经修复了多个问题（`--json` 不兼容、`api snapshot` 回退、wrapper 闪窗等），且最新 `run-20260805-040538` 证明 CCB 可以在 Herdr 中 mounted 并 materialize layout（`layout_materialized_count=2, layout_materialization_complete=true, observed_windows_flash=false`）。但用户报告当前仍存在问题收敛不够彻底，可能涉及以下 gap：

- CCB backend resolver 在 auto 模式下是否稳定选中 herdr
- Herdr capability gate 在实际环境中是否返回 supported
- CCB 稳定性和 keeper 重试抑制逻辑（之前出现过 `restart_count=20, keeper_restart_suppressed:max_start_failures`）
- Herdr session 生命周期与 CCB namespace 生命周期的一致性

## 2. 复现步骤

1. 在 Native Windows x64 环境中，确保 Herdr 0.7.5+ 已安装并运行
2. 进入一个已配置 CCB 的项目目录
3. 运行 `ccb8.cmd`（即 `ccb8 start`）
4. 观察到：provider pane 可能未 materialize 或 CCB control-plane 未进入 mounted 状态

采集脚本复现：
1. 运行 `run_spike.ps1` 采集全量证据
2. 观察到：采集输出缺少 pane 级别验证和 backend resolver 路由信息

## 3. 期望 vs 实际

**期望行为**：
- `ccb8 start` 在 Native Windows + Herdr 环境中应稳定启动 CCB，创建 Herdr workspace 和 provider pane，进入 mounted 状态，且不出现 cmd 窗口闪现
- `run_spike.ps1` 应采集足够的证据覆盖 CCB 启动全链路（从 Herdr session 创建到 provider pane materialize），使问题能在采集数据中被定位

**实际行为**：
- CCB 启动可能在多个环节失败（keeper 重试耗尽、start_flow_failed、layout materialization 未完成），且具体失败原因因环境而异
- `run_spike.ps1` 采集范围不足以覆盖所有可能的失败环节，导致问题定位需要多次反复

## 4. 环境信息

- 涉及模块 / 功能：CCB startup flow、Herdr backend integration、spike harness
- 相关文件 / 函数：
  - `lib/ccbd/supervisor.py` - `RuntimeSupervisor.start()`
  - `lib/ccbd/supervisor_runtime/lifecycle.py` - `start_supervisor()`
  - `lib/ccbd/services/project_namespace_runtime/ensure.py` - `ensure_project_namespace()`
  - `lib/terminal_runtime/herdr_backend.py` - `HerdrBackend`
  - `lib/terminal_runtime/herdr_backend_runtime/cli.py` - `HerdrCliRequestAdapter`
  - `lib/terminal_runtime/herdr_backend_runtime/client.py` - `HerdrSocketClient`
  - `lib/terminal_runtime/backend_resolver.py` - `resolve_mux_backend_v2()`
  - `lib/terminal_runtime/mux_backend_contract.py` - `make_namespace_ref()`
  - `lib/storage/json_store.py` - `JsonStore.load()`
  - `.codestable/roadmap/windows-native-herdr-ccb/drafts/herdr-ui-integration-spike/run_spike.ps1`
- 运行环境：Windows 10 Pro x64, Python 3.14, Herdr 0.7.5
- 其他上下文：
  - 之前的 issue `herdr-ui-integration-ccbd-bootstrap` 已完成多轮修复，review passed
  - 最新的 spike run `run-20260805-040538` 已确认 mounted + layout materialization complete + no window flash
  - 但仍存在后端稳定性 gap 和采集全面性 gap

## 5. 严重程度

**P1 严重** — CCB 在 Native Windows + Herdr 环境中的运行是核心功能路径，虽然已有证据表明某些 run 可以成功（`run-20260805-040538`），但用户反馈当前仍存在不稳定和采集不足问题。有 workaround（使用 tmux/rmux），但会阻碍 Native Windows 用户的使用。

## 备注

- 此 issue 涉及两个关联子问题，建议 sequencing：先扩展采集脚本实现一次完整采集，再根据采集结果诊断 CCB-Herdr 集成 gap
- 已有 issue `herdr-ui-integration-ccbd-bootstrap` 的修复应作为本 issue 的起点，不应回退已有成果
- 采集脚本 `run_spike.ps1` 当前版本已有自测（`-SelfTest`）通过
