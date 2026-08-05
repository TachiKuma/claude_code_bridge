---
doc_type: issue-fix-note
issue: 2026-08-05-herdr-ui-spike-run-findings
status: confirmed
path: standard
fix_date: 2026-08-05
related:
  - herdr-ui-spike-run-findings-report.md
  - herdr-ui-spike-run-findings-analysis.md
  - herdr-ui-spike-run-findings-unified.md
source_audit: .codestable/audits/2026-08-05-herdr-ccb-recent-changes/index.md
tags:
  - ccb8-cli
  - ccbd-socket
  - run_spike.ps1
  - herdr-session
  - windows
---

# Herdr UI Spike 运行发现 — 修复记录

## 1. 根因摘要

本轮修复覆盖 Herdr UI spike 全量采集 `run-20260805-165854` 暴露的 6 项缺陷（F1–F6），根因来自分析阶段确认的 4 类问题：

| F# | 严重度 | 根因 | 根因类型 |
|----|--------|------|----------|
| F1 | P1 | `ccb8 ps` 路由到 `start` 命令处理器——Python CLI 代码正确，根因在外部项目包装器层参数传递 | config |
| F2 | P1 | CCB Herdr 会话 socket 在两次 run 之间丢失——`_start_server` 的 2s 验证不足以覆盖 Windows 环境下的 socket 绑定延迟 | concurrency |
| F3 | P2 | 分类逻辑使用 `ping-ccbd`（守护进程级，读到过渡态 `unmounted`）而非 `ping-all`（agent 级，带重试） | concurrency |
| F4 | P2 | CCB 创建独立 Herdr 会话是结构性设计，非 bug | config（无需代码改动） |
| F5 | P3 | `CCB_RUNTIME_STATE_HOME` 重定位后状态文件在运行时根目录，脚本假设在 `.ccb/ccbd/` | config |
| F6 | P3 | 用户尚未填写 `manual-observation.md` 观察字段 | missing-guard（无需代码改动） |

## 2. 实际采用方案

### F1：argv 诊断日志（防御层）

- **做什么**：在 `run_cli_entrypoint()` 入口增加 `_log_received_argv()`，受环境变量 `CCB_DEBUG_ARGV=1` 控制，将 Python 进程实际收到的 argv 写入 stderr
- **为何选此方案**：外部项目 `ccb8.ps1`/`ccb8.cmd` 不在本仓库，无法直接修复包装器；该日志可帮助下次出现时快速定位是 Python CLI 还是包装器的问题
- **分析方案对应**：方案 B 防御层（方案 A 主修复在外部项目，需单独处理）

### F2：Herdr session socket 可用性验证

- **做什么**：在 `ensure_identity.py` 的 `prepare_namespace_root_pane()` 中，`create_session()` 成功返回后，调用 `_verify_herdr_session_socket()` 进行 socket 可达性验证——通过 `backend.list_windows()` 轻量操作确认 socket 响应，最多等待 10s，失败时记录 warning 但不阻塞启动
- **为何选此方案**：`_start_server()` 内部已有 2s 验证循环，但该验证在 server 进程刚启动时执行；本次新增的验证在 session 创建完成后再次确认，覆盖 server 启动后 socket 绑定不稳定或延迟的场景
- **分析方案对应**：方案 A（ccbd 侧 socket 可用性验证）

### F3：分类逻辑改用 ping-all 为权威挂载信号

- **做什么**：将 `run_spike.ps1:1234-1237` 的分类决策链改为优先使用 `$pingAllSuccess`（agent 级，带重试），仅当 ping-all 失败时才回退到 `ping-ccbd`（守护进程级）区分"守护进程未挂载"和"特定 provider 失败"
- **为何选此方案**：最小改动（仅 8 行），最高准确性——`ping-all` 的重试机制已经处理了 ccbd 启动中期问题
- **分析方案对应**：方案 A

### F4：会话分叉文档说明

- **做什么**：无需代码改动。已在统一文档和审计 index.md 中注明 CCB 创建独立 Herdr 会话是结构性设计
- **分析方案对应**：仅文档说明

### F5：启动状态文件路径修正

- **做什么**：在 `run_spike.ps1:990-1003` 中，从已采集的 `runtime-root-ref.json` 解析 `runtime_state_root` 和 `project_id`，构建运行时状态根目录路径（如 `D:\.c8\rs\{project_id}\ccbd\`）作为第一搜索位置，fallback 到 `.ccb/ccbd/`；采集失败时在 manifest 中记录跳过原因和搜索路径
- **为何选此方案**：直接修复根因，与 `CCB_RUNTIME_STATE_HOME` 重定位机制一致
- **分析方案对应**：方案 A

### F6：用户观察字段

- **做什么**：无需代码改动。下次 Herdr UI 运行 spike 时提醒用户补填 `manual-observation.md`
- **分析方案对应**：用户提醒

## 3. 改动文件清单

| 文件 | 改动说明 | 对应发现 |
|------|----------|----------|
| `lib/cli/entrypoint_runtime.py` | 新增 `_log_received_argv()` + `run_cli_entrypoint()` 入口调用 | F1 |
| `lib/ccbd/services/project_namespace_runtime/ensure_identity.py` | 新增 `_verify_herdr_session_socket()` + 在 `create_session()` 后调用；**review 修复**: 改用 `backend.list_windows()` 通过 `_mux_namespace_ref` 正确构建 payload（原直接调用缺少 `namespace_id`，导致验证是空操作） | F2, B1 |
| `.codestable/roadmap/.../run_spike.ps1` | F3: 分类逻辑改用 `$pingAllSuccess` 优先；F5: ccbd 状态文件从运行时根目录采集 + 跳过原因日志；**review 修复**: `$ccbdFilesCollected` 单布尔值改为 `$copiedCcbdFiles` hashtable 按文件跟踪 | F3, F5, REV-004 |
| `.codestable/audits/.../index.md` | 状态同步：标记已修复项、新增发现、更新下一步建议和复核结论 | 统一/文档 |
| `.codestable/issues/.../analysis.md` | frontmatter 更新：`status: confirmed`、`root_cause_type: multi`、交叉引用 | 分析确认 |
| `.codestable/issues/.../approval-report.md` | 新建：ConfirmFixPlan checkpoint 审批记录 | 流程 |
| `.codestable/issues/.../unified.md` | 新建：审计 × spike 交叉引用统一视图 | 统一/文档 |

**范围外**（分析已声明但不在此轮修复，或非本仓库文件）：
- 外部项目 `ccb8.ps1`/`ccb8.cmd`（F1 主修复）
- 审计#02、#03、#04、#05、#08、#09、#10、#11（独立审计发现，未在本 issue 范围内）

## 4. 验证结果

| 验证项 | 方法 | 结果 |
|--------|------|------|
| `run_spike.ps1` AST parse | PowerShell `-SelfTest` | ✅ passed |
| `run_spike.ps1` 语法 | `[Parser]::ParseFile` | ✅ 无语法错误 |
| `entrypoint_runtime.py` 语法 | `py_compile` | ✅ ok |
| `ensure_identity.py` 语法 | `py_compile` | ✅ ok |
| F3 分类逻辑 | 逻辑审查：ping-all 成功时跳过 ping-ccbd 检查 | ✅ 正确 |
| F5 路径回退 | 逻辑审查：先查运行时根目录，再 fallback `.ccb/ccbd/` | ✅ 正确 |

**未执行**（需要 Herdr UI 真实环境）：
- 真实 Herdr UI 全链路采集验证（F1+F2+F3+F5 联合效果）
- `CCB_DEBUG_ARGV=1 ccb8 ps` 端到端诊断日志验证
- Herdr session socket 创建→销毁→重建 压力场景

## 5. 遗留事项

| 事项 | 优先级 | 说明 |
|------|--------|------|
| F1 主修复 | P1 | 需在外部项目 `D:\C#Project\GitHub\AvaPrintDesigner\ccb8.ps1` 中检查并修复 `ps` 参数传递。当前仅加了防御性诊断日志 |
| F2 真实环境验证 | P1 | 需在 Herdr UI 环境中运行默认全量 spike 采集，确认 CCB 会话 `api snapshot` 不再返回 `NotFound` |
| 下次全量采集 | P1 | F1+F2+F3+F5 全部修复后，在 Herdr UI 重新运行默认全量采集，确认真实 CCB 会话 pane capture 证据完整 |
| 审计#02、#05、#09 | P1 | 闪窗回退、共享模块提取、detail 脱敏——独立审计发现，不在本轮 issue 范围 |
| 审计#03、#04、#08、#10、#11 | P2 | 排期修复项 |
| F6 用户填写 | P3 | 下次 spike 运行时提醒补填 `manual-observation.md` |
