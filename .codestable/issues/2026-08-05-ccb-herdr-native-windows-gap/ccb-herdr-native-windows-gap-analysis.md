---
doc_type: issue-analysis
issue: ccb-herdr-native-windows-gap
status: confirmed
root_cause_type: logic
related: [ccb-herdr-native-windows-gap-report.md]
tags:
  - native-windows
  - herdr-integration
  - herdr-cli-adapter
  - argument-ordering
  - spike-harness
  - capability-gate
---

# CCB Native Windows Herdr 集成 gap 根因分析

## 1. 问题定位

采集脚本 (`run_spike.ps1`) 和 CCB Herdr 运行时 (`lib/terminal_runtime/herdr_backend_runtime/cli.py`) 各有独立根因，下面逐一分析。

### 子问题一：采集脚本广度不够

| 关键位置 | 说明 |
|---|---|
| `run_spike.ps1:627-663` | 当前采集命令清单：herdr baseline + ccb wrapper check + ccb diagnose + ccb start + post-start check（ping/ps/layout/doctor） |
| `run_spike.ps1:730` | `layoutMaterializationComplete` 判断只看 `layout_materialized_count >= ExpectedAgents`，不验证 pane 内容 |
| `run_spike.ps1:751-753` | `classification` 路由链缺少 backend resolver 路由结果检查 |
| `lib/ccbd/supervisor_runtime/lifecycle.py:15-87` 的 `start_supervisor()` | 启动流程中 `startup-report.json` 记录了完整的 namespace ensure 和 start flow 结果，但 spke 脚本不采集 |
| `lib/ccbd/keeper_runtime/state.py` | keeper 状态文件（`keeper.json`）记录了 keeper restart_count 和 failure reason，采集遗漏 |

缺失维度的具体位置：
- **Backend resolver 路由结果**：`lib/terminal_runtime/backend_resolver.py:64-180` 的 `resolve_mux_backend_v2()` 返回 selection/failure，当前 spke 完全不采集
- **Pane 级别物化验证**：`lib/terminal_runtime/herdr_backend_runtime/cli.py:695-705` 的 `_capture_pane()` 和 `lib/ccbd/services/project_namespace_pane.py` 的 `snapshot_project_namespace_panes()`，当前 spke 不直接验证 pane 内容
- **CCB 启动期全量状态**：`lib/ccbd/supervisor_runtime/reporting.py` 的 `record_startup_report()` 写入 `startup-report.json`、`lib/ccbd/keeper_runtime/state.py` 写入 `keeper.json`
- **CCB 磁盘层快照**：`.ccb/` 目录下的 `lease.json`、`lifecycle.json`、`runtime-root-ref.json`

### 子问题二：CCB Herdr 集成无法稳定运行

| 关键位置 | 说明 |
|---|---|
| **`lib/terminal_runtime/herdr_backend_runtime/cli.py:1020`** | **主根因**：`--session` 参数放置在子命令之前，导致 Herdr 0.7.5 走 attach/TUI 路径而非返回 JSON |
| `lib/terminal_runtime/herdr_backend_runtime/cli.py:1079-1085` | `_start_server()` 同样用 `herdr --session X server` 顺序，启动 herdr server 时也可能失败 |
| `lib/terminal_runtime/herdr_backend_runtime/cli.py:1140-1141` | `_server_status_running()` 同样用 `herdr --session X status server --json` 顺序 |
| `lib/terminal_runtime/api.py:225` | `_herdr_capability_gate()` 调用 `herdr_capability_report_supported()`，该函数依赖 `verdict` 字段 — 如 capability evidence 缺失此字段，gate 会 fail-open 被 block |
| `lib/ccbd/keeper_runtime/failure_policy.py:28-32` | keeper 重试计数达到 20 次后进入 `keeper_restart_suppressed:max_start_failures`，这是启动失败的后果而非原因 |

## 2. 失败路径还原

### 采集脚本广度不够 — 缺失覆盖的路径

**正常采集路径**（当前）：
运行 `run_spike.ps1` → 采集 Herdr baseline → 检查 wrapper 文件 → 运行 `ccb8 --diagnose` → 启动进程采样器 → detach 启动 `ccb8` → Post-start 采集 Herdr status/snapshot + CCB ping/ps/layout/doctor → 等待采样器结束 → 生成 summary.json

**缺失的采集路径**：
1. **Backend resolver 路由采集缺失**：CCB 启动时 `TerminalBackendSelection._get_herdr_backend()` (`lib/terminal_runtime/backend_selection.py:57`) 调用 `resolve_mux_backend_v2()` 判断 backend 路由 — spike 脚本完全不记录此路径的输入/输出
2. **Pane 物化深度验证缺失**：`run_spike.ps1:730` 只看 `layout_materialized_count` 数量是否 ≥ `ExpectedAgents`，不验证：
   - Pane 是否实际在 Herdr 中存在且 alive
   - Pane 的 tokens/identity 是否正确设置
   - Pane 内容是否可捕获（`capture_pane` 操作）
3. **启动期状态文件缺失**：`start_supervisor()` (`lifecycle.py:42-87`) 调用 `ensure_project_namespace()` 和 `run_start_flow_fn()` — start flow 中的每个阶段、及其写入的状态文件（`startup-report.json`、`keeper.json`）均不采集

### CCB Herdr 启动失败路径

**期望路径**（代码设计）：
用户 `ccb8.cmd` → PowerShell wrapper `ccb8.ps1`（设置环境变量）→ `python ccb.py start` → CCB daemon 启动 → `RuntimeSupervisor.start()` → `start_supervisor()` → `ensure_project_namespace()` → Herdr backend 选中 → Herdr session 创建 → Herdr workspace/pane 创建 → provider agent 启动 → CCB mounted

**实际失败路径**：
用户 `ccb8.cmd` → PowerShell wrapper 设置 Herdr 环境变量 → CCB daemon 启动 → `start_supervisor()` → `_herdr_platform_gate()` 返回 `supported=True`（`api.py:350-367`）→ `_herdr_capability_gate()` **可能** 因为 capability evidence 中缺少 `verdict` 字段而判断为 malformed（`api.py:225-231`）→ 即使 capability gate 通过，`HerdrCliRequestAdapter._command()` 生成 `herdr --session X status --json` 参数顺序（`cli.py:1020`）→ Herdr 0.7.5 将 `--session` 解析为 TUI attach 而非 JSON 子命令 → 命令不返回 JSON → `_json_command()` 抛出 `"Herdr command did not return JSON"`（`cli.py:979-984`）→ MuxCommandErrorV2 → ccbd 启动失败 → keeper 重试启动 ccbd → ccbd 再次以相同方式失败 → 重复 20 次 → keeper 进入 `keeper_restart_suppressed:max_start_failures`（`failure_policy.py:28-32`）→ CCB 永远无法进入 mounted 状态

**分叉点**：
1. **一级分叉点** — `lib/terminal_runtime/herdr_backend_runtime/cli.py:1020`：`command = [executable, "--session", effective_session, *args]` — 这里的参数顺序导致 `--session` 在子命令前，与 Herdr 0.7.5 的解析器不兼容
2. **二级分叉点** — `lib/terminal_runtime/api.py:225`：`herdr_capability_report_supported(capabilities)` — 若 capability evidence 中缺少 `verdict` 字段，gate 直接判定为 malformed

## 3. 根因

### 根因一（主）：`HerdrCliRequestAdapter._command()` 中 `--session` 参数位置错误

**根因类型**：logic（参数顺序假设与实际 CLI 不匹配）

**根因描述**：
`lib/terminal_runtime/herdr_backend_runtime/cli.py:1020` 处的 `_command()` 方法构建 Herdr CLI 命令时，将 `--session` 参数放在子命令之前：

```python
command = [executable, "--session", effective_session, *args]
```

例如生成：
```
herdr --session ccb-herdr status --json
herdr --session ccb-herdr workspace create --label myproject
herdr --session ccb-herdr pane split X --direction right --ratio 0.5
```

但 Herdr 0.7.5（本机版本）的参数解析器要求子命令在前，`--session` 作为命令选项在子命令之后：

```
herdr status --json --session ccb-herdr
herdr workspace create --label myproject --session ccb-herdr
herdr pane split X --direction right --ratio 0.5 --session ccb-herdr
```

当 `--session` 在子命令前时，Herdr 0.7.5 将其当作全局 attach/TUI 指令，尝试以交互模式 attach 到指定 session — 导致 `_json_command()` 期望的 JSON 输出永远不会被返回，命令最终以 `"Herdr command did not return JSON"` 失败。

**此问题在上轮 issue `herdr-ui-integration-spike-harness-followup` 中已在 spike 脚本层面修复**（`Add-HerdrSessionArgs` 将 `--session` 追加到命令末尾），**但核心运行时 `HerdrCliRequestAdapter` 中的三个关键位置尚未修复**：

1. `cli.py:1020` — `_command()`：所有 Herdr CLI 操作的入口
2. `cli.py:1085` — `_start_server()`：`herdr --session X server`
3. `cli.py:1141` — `_server_status_running()`：`herdr --session X status server --json`

**是否有多个根因**：是。

### 根因二（次）：capability evidence 中可能缺少 `verdict` 字段

**根因类型**：data-format（capability evidence JSON 格式与 capability gate 期望不匹配）

**根因描述**：
`lib/terminal_runtime/api.py:225` 的 `_herdr_capability_gate()` 调用 `herdr_capability_report_supported(capabilities)`，该函数 (`capabilities.py:213-225`) 检查 `verdict` 字段是否在 `{"pass", "partial"}` 中：

```python
def herdr_capability_report_supported(capabilities: Mapping[str, object]) -> bool:
    adapter_recommendation = str(capabilities.get("adapter_recommendation") or "").strip()
    verdict = str(capabilities.get("verdict") or "").strip()  # ← 空字符串会被拒绝
    ...
    return (
        adapter_recommendation in {"continue", "continue-with-gaps"}
        and verdict in {"pass", "partial"}  # ← 空字符串不在其中
        ...
    )
```

当前 capability evidence 文件 (`herdr-contract-spike-evidence.json`) 中设置了 `adapter_recommendation: "continue-with-gaps"` 和 `failure_class: "windows-beta-gap"`，但需要确认 `verdict` 字段是否已设置。如果缺失，capability gate 会判定为 `"Herdr capability evidence is malformed"`，所有 Herdr 操作被 block。

### 根因三（采集）：`run_spike.ps1` 缺少 5 个关键采集维度

**根因类型**：missing-guard（采集覆盖率不足，导致错误无法定位）

**根因描述**：当前采集覆盖 3 个维度（CCB control-plane、Herdr baseline、进程采样），但缺失 5 个维度：backend resolver 路由结果、pane 级别物化验证、CCB 启动期全量状态文件、Herdr session 级别健康、CCB 磁盘层快照（`.ccb/` 关键文件）。

## 4. 影响面

- **影响范围**：
  - 根因一影响所有 `herdr` backend（`backend_impl="herdr"`）的 CCB 操作 — 在 Herdr 0.7.5 的 machine-readable 路径下，所有通过 `HerdrCliRequestAdapter` 发起的 CLI 命令（`server_info`、`create_session`、`create_pane`、`set_pane_identity`、`capture_pane` 等 20+ 操作）都会失败
  - 根因二影响 capability gate 初始化，一旦触发会导致 Herdr backend 在 auto 模式下不选中
  - 根因三影响所有后续调试 — 任何 CCB-Herdr 集成问题都难以在一次 spike 中定位  

- **潜在受害模块**：
  - `HerdrBackend` (`lib/terminal_runtime/herdr_backend.py`): 所有方法都通过 `HerdrSocketClient` → `HerdrCliRequestAdapter` 调用 Herdr CLI
  - `ensure_project_namespace()` (`lib/ccbd/services/project_namespace_runtime/ensure.py`): namespace 创建、topology materialization
  - `TerminalBackendSelection._get_herdr_backend()` (`lib/terminal_runtime/backend_selection.py:57`): auto 模式下 Herdr 后端选中
  - `RuntimeSupervisor.start()` (`lib/ccbd/supervisor.py:65`): CCB 启动流程
  - `keeper_main.py` (ccbd/keeper): keeper 会因 ccbd 重复失败而进入 suppressed 状态

- **数据完整性风险**：无直接数据损坏风险。但 keeper 进入 suppressed 后，`.ccb/ccbd/keeper.json` 中的 `restart_count` 会异常增长，可能导致后续启动永久抑制。

- **严重程度复核**：维持 **P1**。虽然可以使用 tmux/rmux 作为 workaround，但 Herdr 是 Native Windows 环境的唯一合理后端选择，此问题会完全阻断 Native Windows 用户的使用。

## 5. 修复方案

### 方案 A：修复 `--session` 参数顺序（最小改动）

- **做什么**：
  1. 修改 `cli.py:1020` 中的 `_command()`，将 `--session` 参数追加到 args 末尾：`command = [executable, *args, "--session", effective_session]`
  2. 同步修改 `cli.py:1085` 的 `_start_server()`：`command = [executable, "server", "--session", session_name]`
  3. 同步修改 `cli.py:1141` 的 `_server_status_running()`：`command = [executable, "status", "server", "--json", "--session", session_name]`
  4. 补充测试 `test/test_herdr_backend_client.py` 中验证 `--session` 参数位置
- **优点**：改动范围极小（3 行），直接命中根因，与原 spike 脚本修复一致
- **缺点 / 风险**：如果某些 Herdr 版本反而要求 `--session` 在前，此改动会引入反向不兼容。需要确认 Herdr 0.7.5+ 的命令行规范
- **影响面**：`lib/terminal_runtime/herdr_backend_runtime/cli.py` 3 处，`test/test_herdr_backend_client.py` 补测试

### 方案 B：修复采集脚本广度 + 扩展 Herdr adapter 容错回退

- **做什么**：
  1. 扩展 `run_spike.ps1` 采集能力，新增 5 个采集维度（backend resolver、pane 验证、startup 状态文件、session 健康、磁盘快照）
  2. 在 `cli.py:_command()` 中增加参数顺序兼容逻辑：先用 `--session` 在后的顺序尝试，失败时回退到 `--session` 在前的顺序
  3. 在 `api.py:_herdr_capability_gate()` 中对缺失 `verdict` 字段做容错处理，当 `adapter_recommendation="continue-with-gaps"` 且 `failure_class="windows-beta-gap"` 时 auto-deduce verdict
- **优点**：更强健的兼容性，采集覆盖完整，可以适应未来 Herdr 版本变化
- **缺点 / 风险**：改动范围较大（spike 脚本 + 2 个 Python 模块），容错逻辑增加了复杂度，可能掩盖真实 failed 状态
- **影响面**：`run_spike.ps1`（大量扩展）、`cli.py`（容错逻辑）、`api.py`（verdict auto-deduce）、测试文件

### 方案 C：只修复 Herdr adapter + 补全 capability evidence（推荐）

- **做什么**：
  1. 修复 `cli.py` 中的 `--session` 参数顺序（与方案 A 相同的 3 处改动）
  2. 在 `api.py:_herdr_capability_gate()` 中补一行：当 `adapter_recommendation="continue-with-gaps"` 且 `failure_class="windows-beta-gap"` 且 `verdict` 为空时，auto-derive verdict 为 `"partial"`（因为 `windows-beta-gap` 即表示部分能力可用）
  3. 扩展 `run_spike.ps1` 新增 5 个采集维度中最重要的 3 个：backend resolver 路由、pane 物化验证、CCB 启动期状态文件
- **优点**：平衡了根因修复与采集覆盖，不增加过度容错复杂度，capability evidence 的格式恢复只做最小容错
- **缺点 / 风险**：采集脚本扩展需要谨慎避免引入新的 Herdr TUI 超时问题。spike 脚本工作量较大
- **影响面**：`cli.py`（3 处）、`api.py`（~5 行）、`run_spike.ps1`（新增 3 个采集阶段）、测试

### 推荐方案

**推荐方案 C**，理由：

1. **根因最直接**：`--session` 参数顺序是已验证的根因（上轮 spke 脚本修复后成功），修复此问题即可恢复 CCB Herdr 运行时到可工作状态
2. **capability evidence 容错最小化**：只做一行 auto-derive，不引入复杂的回退链，保持 capability gate 的 fail-closed 安全语义
3. **采集覆盖恰好够用**：选择 3 个最高价值的采集维度（backend resolver 路由最直接定位路由失败、pane 验证确认物化结果、startup 状态文件提供 startup flow 的诊断依据），避免采集脚本过于臃肿引入新的超时/不兼容问题
4. **不与已有修复冲突**：不改变 spike 脚本中已验证通过的 `Add-HerdrSessionArgs`、`ccb8-wrapper-file-check`、`create_no_window` 等逻辑
