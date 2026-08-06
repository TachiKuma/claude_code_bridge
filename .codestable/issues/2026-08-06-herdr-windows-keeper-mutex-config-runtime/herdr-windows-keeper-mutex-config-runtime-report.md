---
doc_type: issue-report
issue: 2026-08-06-herdr-windows-keeper-mutex-config-runtime
status: confirmed
severity: P1
summary: 外部项目 Herdr UI 启动 CCB 失败 — config 顶层 runtime 字段被 v2 校验拒绝（schema 脱节），叠加 Windows keeper 互斥失效导致双 keeper 并发、状态文件分裂，agent pane 始终无法 materialize
tags:
  - windows
  - herdr
  - ccb8-cli
  - keeper
  - config-schema
  - ccbd
---

# Herdr Windows keeper 互斥与 config runtime 字段 Issue Report

## 1. 问题现象

在外部项目 `D:/C#Project/GitHub/AvaPrintDesigner` 中，从 Herdr UI 内运行 `.\ccb8.cmd`：

1. **config 校验失败**：输出 `command_status: failed` / `error: config contains unknown top-level fields: runtime`，start 未进入守护进程拉起流程。
2. **启动后 agent pane 不出现**：即使 config 校验通过、ccbd 报告 mounted，外部项目也只看到多个 `cmd` 窗口短暂闪现后关闭；Herdr 左侧 agents 面板曾在闪现期间出现 `claude`，但两个配置的 Codex pane 从未 materialize。

## 2. 采集证据

### 2.1 spike run 与分类

| run_id | 分类 | command_failure_count | 失败命令 |
|---|---|---|---|
| `run-20260806-081057` | mounted-with-herdr-panel-observation | 1 | `herdr-api-snapshot-ccb-namespace`（exit=1） |
| `run-20260806-085134`（删除 `D:\C#Project\.ccb` 后） | mounted-with-herdr-panel-observation | 1 | `herdr-api-snapshot-ccb-namespace`（exit=1） |
| `run-20260806-085751`（同上，第二次） | mounted-with-herdr-panel-observation | 1 | `herdr-api-snapshot-ccb-namespace`（exit=1） |

证据目录：`.codestable/roadmap/windows-native-herdr-ccb/drafts/herdr-ui-integration-spike/evidence/`

### 2.2 config 校验失败（用户手动运行）

- 报错来源：`lib/agents/config_loader_runtime/parsing_runtime/validation.py:113-118` `_validate_document_shape()`，抛 `ConfigValidationError('config contains unknown top-level fields: runtime')`。
- 白名单：`lib/agents/config_loader_runtime/common.py:17-30` `ALLOWED_TOP_LEVEL_KEYS` **不含 `runtime`**。
- 触发 config：含 `[runtime.mux] backend = "rmux"` 的 v2 config。已确认存在的实例：
  - `D:\C#Project\.ccb\ccb.config`（外部项目父目录锚点，**已在本次 issue 中被删除**）；
  - `E:\GitHub开源项目\TachiKuma\claude_code_bridge\.ccb\ccb.config`（repo 自身 config，仍含 `[runtime.mux]`）。

### 2.3 startup-report 状态口径冲突

`run-20260806-081057/.../ccbd/startup-report.json`（doctor bundle 内）：

- `status: failed`；
- `failure_reason`：`{"id":"cli:pane:list","error":{"code":"server_not_running","message":"no herdr server is running at C:\Users\Administrator\AppData\Roaming\herdr\sessions\ccb-avaprintdesigner-575a971f\herdr.sock; ..."}}`；
- 同期 `lease.json` / `lifecycle.json` 却标记 `mount_state: mounted` / `health: healthy` / `phase: mounted`。

即：CCB 内部 runtime store 认为 mounted，Herdr 实际证据（命名会话 socket 不可用）不支持"可见挂载"。`herdr.sock` 文件存在（24B，2026-08-04 15:00 创建）但对应 server 进程未运行（死 socket）。

### 2.4 Windows keeper 互斥失效（双 keeper 实锤）

两个新 run 的 `startup-state-files/` 状态文件：

| run | keeper.json `keeper_pid` | lease.json `keeper_pid` | ccbd_pid |
|---|---|---|---|
| `run-20260806-085134` | 15916 | 6944 | 9660 |
| `run-20260806-085751` | 6440 | 6944 | 9660 |

- ccbd(9660) 跨多个 run 一直未重启；keeper 每次 prestart 后换新（15916 → 6440），但 lease 里的 keeper_pid(6944) 始终未更新 → **keeper.json 与 lease.json 状态权威分裂**。
- `process-samples.jsonl`（run-20260806-085751）同时存在两个 `keeper_main.py` 进程：pid 6440（parent 10132）、pid 7192（parent 15464）。
- `ccbd.stderr.log` 尾部（D:\.c8\rs\{project_id}\ccbd\ccbd.stderr.log）：
  - `ModuleNotFoundError: No module named 'fcntl'`；
  - `StartupFenceError: expected startup lifecycle rejected: startup_id mismatch`。

### 2.5 附带证据

- `doctor.json` `entrypoint.status = degraded`，reason `bare_ccb_resolves_outside_current_install`：裸 `ccb` 解析到 `.ccb-source-dev/bin/ccb.CMD`，与 source install 根不一致。
- `ccbd.stderr.log` 反复出现 `workspace wB1/wB3 not found`（Herdr workspace close 幂等性缺口）。
- host-context.json 含中文路径，默认 gbk 解码即 `UnicodeDecodeError`（采集/诊断编码卫生缺口）。

## 3. 影响

1. **P0 — 外部项目无法启动两个 Codex agent**：mount 成功但 agent pane 从不 materialize，界面看不到任何可用 pane。
2. **P0 — 状态权威不可信**：mounted 与 failed 同时发布，任何依赖状态文件的上游（monitor、UI、spike 采集）都可能读到互相矛盾的结果。
3. **P1 — 配置 schema 欠账**：`runtime` 顶层字段是已验收（AC-005）但未实现的设计，任何命中者 fail-closed 且报错不含文件路径，排障成本高。
4. **P1 — 多 keeper 竞争**：反复 prestart、启动围栏拒绝（startup_id mismatch）、状态文件互相覆盖，是"cmd 窗口闪现后关闭"的直接来源。
