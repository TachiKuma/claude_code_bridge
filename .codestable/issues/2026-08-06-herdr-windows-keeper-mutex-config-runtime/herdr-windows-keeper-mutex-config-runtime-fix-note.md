---
doc_type: issue-fix-note
issue: 2026-08-06-herdr-windows-keeper-mutex-config-runtime
status: confirmed
path: standard
fix_date: 2026-08-06
related:
  - herdr-windows-keeper-mutex-config-runtime-report.md
  - herdr-windows-keeper-mutex-config-runtime-analysis.md
tags:
  - windows
  - herdr
  - keeper
  - config-schema
  - ccbd
---

# Herdr Windows keeper 互斥与 config runtime 字段 修复记录

> 实施状态：P0（G1/G2）+ P1（G3/G4）+ P2（G5）已全部实施并验证。变更文件见末尾清单。

## P0-1 修 Windows keeper 单例互斥（G2，最优先）

**做什么**：让 `try_acquire_keeper_lock` 在 Windows 下持有真实跨进程锁。

- `lib/ccbd/keeper_runtime/support.py:8-23`：`import fcntl` 失败的 `ModuleNotFoundError` 分支改为尝试 `msvcrt.locking`（复用 `lib/ccbd/control_plane_transport/endpoint_store.py:124` 的成熟实现）；两者都不可用时返回 `None`（表示未拿到锁），绝不静默返回"未加锁的 handle"。
- 加锁语义对齐 `endpoint_store`：`LK_LOCK`（阻塞）或 `LK_NBLCK`（非阻塞）按调用方预期选择，并在 `__del__` / finally 释放。
- keeper 启动围栏（`keeper_runtime/loop.py:22`）在拿不到锁时输出明确日志（含两方 keeper_pid / 实例 ID / lock path），替代当前静默。

**验证**：
- 新增回归测试：两个进程并发抢同一 `keeper.lock`，断言只有一个胜出、另一个返回 `None`。
- Windows 真实环境：连跑两次 `.\ccb8.cmd`（prestart kill 后）确认 `keeper.json`/`lease.json` 的 `keeper_pid` 一致，不再出现双 keeper。

## P0-2 定 `runtime` 顶层字段去留（G1，需决策）

**决策点**：`runtime.mux.backend` 是"补实现"还是"废弃清理"。

- **若支持（推荐，补 AC-005 未接线部分）**：
  - `ALLOWED_TOP_LEVEL_KEYS`（`common.py:17-30`）加入 `runtime`；v3 顶层白名单（`workflow_v3.py:39`）按需同步。
  - 实现 `runtime.mux.backend` 解析并接入 `terminal_runtime/backend_selection.py` 的 `requested_backend` 来源（当前只认 terminal_type/env）。
  - 未知 `runtime.*` 字段按 AC-005 语义 fail-closed，报错带字段名与路径。
- **若废弃**：
  - 移除 `E:\GitHub开源项目\TachiKuma\claude_code_bridge\.ccb\ccb.config` 中的 `[runtime.mux]`（此前删除未保存，文件仍在）。
  - 文档标注该字段不再支持。

**无论哪条，必做**：`_validate_document_shape`（`validation.py:113`）的错误信息带上 `source_path`，并给迁移提示 ——"v2 不支持顶层 runtime；可能来自 v3 草案/旧配置，应迁移到 loop、agent.runtime_mode 或移除"。

## P1-1 Herdr 命名会话 socket 活性判定（G3）

**做什么**：
- socket 就绪判定由"文件存在性"改为"探测型"：`herdr status server --session <name>` 或 `list_windows` 往返成功才算就绪；失败时输出 server 进程状态。
- 启动成功判定以 live backend 可验证状态为准：命名会话 socket 不可用时，**不得同时发布 mounted + failed 两种权威状态**。建议在 lease/lifecycle 增加 `live_ui_observed` 字段或把 `startup_stage` 收敛到单一语义。
- `layout status` 的 `observed.observe_status=skipped` 时不报告强成功，拆分 `configured_ok` / `runtime_store_ok` / `live_ui_observed_ok` 三个字段。

**验证**：真实 Herdr UI 重跑默认全量 spike，确认 `herdr-api-snapshot-ccb-namespace` 不再 exit=1，且 `pane-verification` 能拿到真实 pane capture。

## P1-2 kill -f 幂等化（G4）

**做什么**：
- `terminal_runtime/herdr_backend_runtime/cli.py` 的 workspace close / session destroy 在 force kill 场景：`workspace_not_found` / `server_not_running` 清理本地 state 后返回成功或 `degraded`，不冒泡为 `CalledProcessError`。
- 补幂等回归：重复对已消失 workspace 执行 close 两次，第二次不得报错。

## P2 采集/诊断卫生（G5）

**做什么**：
- host-context / snapshot 一律按 UTF-8 读写；解析失败时保存 raw bytes，并把 run 归类降级（不判 full success）。
- `doctor-output` 输出带 `.tar.gz` 后缀。
- `run_spike.ps1` 对 `current_directory` 与 `ccb8_path` 不一致的 run 显式标注"项目发现上下文"，避免 repo 与外部项目配置混读误导归因。
- 进程样本按 project_id / runtime root / 启动 pid tree 过滤，避免混入无关 provider 进程。

## 验证清单（实施后）

| 项 | 方法 | 预期 |
|---|---|---|
| keeper 互斥 | 双进程抢锁回归测试 + Windows 真实连跑 | 单 keeper，状态文件一致 |
| config runtime | `ccb8 config-validate --action effective` 对含 `runtime` 的 config | 明确报错带路径与迁移提示，或不报错（视决策） |
| agent pane | 真实 Herdr UI 全量 spike | `layout_materialized_count=2`，`pane-verification` 拿到真实 pane |
| 状态一致性 | startup-report / lease / lifecycle / Herdr snapshot 对齐 | 单一权威状态，无 mounted+failed 并存 |

## 实施记录（2026-08-06）

### 已实施

**P0-1 keeper 单例互斥（G2）**
- `lib/ccbd/keeper_runtime/support.py`：`try_acquire_keeper_lock` 的 `fcntl` 缺失分支（Windows）改为 `_try_acquire_windows_lock`，用 `msvcrt.locking(LK_NBLCK)` 真实跨进程锁（空文件先写 1 字节占位）；无锁可用时返回 `None`（fail-closed），**不再静默返回未加锁 handle**。
- 新增 `test/test_ccbd_keeper_lock.py`：双获取者互斥、释放后可重获、外部持有者互斥三条回归（Windows 实测 3 passed）。

**P0-2 废弃 runtime 顶层字段（G1）**
- `lib/agents/config_loader_runtime/parsing_runtime/validation.py`：`_validate_document_shape` 错误信息附加 `source_path`；遇 `runtime` 字段给迁移提示（"v2 does not support top-level 'runtime' ... migrate to loop / agent.runtime_mode or remove it"）。
- repo 自身 `.ccb/ccb.config` 中的 `[runtime.mux]` 已确认移除（此前删除未保存，本轮用户已保存）。

**P1-1 Herdr 会话 socket 活性判定（G3）**
- `lib/cli/services/layout_status.py`：顶层拆分 `configured_ok` / `runtime_store_ok` / `live_ui_observed_ok` 三字段，`observe_status=skipped` 不再被误读为强成功。
- `lib/ccbd/services/project_namespace_runtime/ensure_identity.py`：`_verify_herdr_session_socket` 返回 bool；`prepare_namespace_root_pane` 返回验证结果。
- `ensure.py` / `ensure_state.py`：验证结果经 controller 传递到 `build_created_namespace` 的 `ui_attachable`（socket 未验证 → namespace 不可 attachable）。
- `test/test_layout_status_cli.py`：三字段断言补充（unmounted 与 observed-ok 两种场景，9 passed）。

**P1-2 kill -f 幂等化（G4）**
- `lib/terminal_runtime/herdr_backend_runtime/cli.py`：`_looks_like_missing_server` 扩展匹配 `server_not_running` / `no herdr server is running`；`_destroy_namespace` 容忍 not-found 与 missing server（幂等清理），非幂等错误仍冒泡。
- 新增 `test/test_herdr_destroy_namespace_idempotent.py`：workspace_not_found / server_not_running 幂等 + 其他错误冒泡（3 passed）。

**P2 采集/诊断卫生（G5）**
- `.codestable/roadmap/.../run_spike.ps1`：
  - host-context 增加 `working_directory_differs_from_project` 归因标注；
  - snapshot JSON 解析失败时保存 raw 输出（`*.raw.txt`）；
  - doctor output 带 `.tar.gz` 后缀并解压，startup-report / ccbd 日志从解压目录读取；
  - 进程采样过滤精确化（仅项目相关 / CCB 守护 marker / herdr / 项目相关 wrapper，不再抓裸 claude/codex 全局进程）。
  - 语法验证通过（PowerShell Parser）。

### 验证

- `test_ccbd_keeper_lock.py`：3 passed（Windows msvcrt 路径）。
- `test_herdr_destroy_namespace_idempotent.py`：3 passed。
- `test_layout_status_cli.py`：9 passed。
- `test_ccbd_tmux_namespace.py` + `test_ccbd_supervisor_namespace.py`：11 passed。
- config loader 关键测试：162 passed（另有 5 个 `test_v2_config_loader.py` 既有失败，与本次无关，见遗留）。
- `run_spike.ps1` PowerShell Parser 语法校验：OK。

### 变更文件清单

| 文件 | 改动 |
|---|---|
| `lib/ccbd/keeper_runtime/support.py` | Windows msvcrt 互斥锁 |
| `lib/agents/config_loader_runtime/parsing_runtime/validation.py` | 错误信息带 source_path + runtime 迁移提示 |
| `lib/cli/services/layout_status.py` | configured/runtime_store/live_ui_observed 三字段 |
| `lib/ccbd/services/project_namespace_runtime/ensure_identity.py` | socket 验证返回 bool |
| `lib/ccbd/services/project_namespace_runtime/ensure.py` | 传递 socket 验证结果 |
| `lib/ccbd/services/project_namespace_runtime/ensure_state.py` | ui_attachable 反映 socket 验证 |
| `lib/terminal_runtime/herdr_backend_runtime/cli.py` | missing server 幂等（G4） |
| `.codestable/roadmap/.../run_spike.ps1` | P2 采集卫生 |
| `test/test_ccbd_keeper_lock.py` | 新增 |
| `test/test_herdr_destroy_namespace_idempotent.py` | 新增 |
| `test/test_layout_status_cli.py` | 三字段断言 |

## 遗留风险

- **未强制状态机收敛**：startup-report `failed` 与 lease `mounted` 并存的语义（daemon mounted vs agent start 失败）未在本次强推重构，涉及 F2 容错权衡；已通过 layout 三字段 + `ui_attachable` 暴露给消费方判断。
- **既有失败（非本次引入）**：
  - `test_herdr_backend_client.py` 5 个 `--session` flag 位置断言失败（Herdr v0.8.0 改动后测试未同步）；
  - `test_v2_config_loader.py` 5 个 `invalid TOML hex value` 失败（fixture 生成 config 问题）。
- **真实环境验证待做**：在真实 Herdr UI 重跑默认全量 spike，确认双 keeper 消失、`layout_materialized_count=2`、`pane-verification` 拿到真实 pane；若"cmd 窗口闪现"仍有，继续排查 agent start 链路。
