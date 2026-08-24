# Phase 5 旧路径删除门禁（13C）

日期：2026-08-24

关联工单：`.scratch/wezterm-ccb-herdr-hosting/issues/13-old-path-deletion-governance.md`、
`13A-agent-id-authority-contract.md`、`13B-delete-ccb-pane-agent-report-patch.md`、
`13C-architecture-and-live-validation-gate.md`

关联门禁脚本：`scripts/phase5_deletion_gate.py`（可重跑）

关联测试：`test/test_phase5_deletion_gate.py`

## 目的

把 Phase 5「删除只为旧边界存在的复杂度」从散落的散文约定，收敛为一个**可重跑、
fail-closed 的删除门禁**。本节点**不删除任何业务代码**，只建立验收证据清单与检查脚本：

- 每个删除项在删除前必须有等价 characterization test、Windows live validation 证据、
  以及明确的 rollback 条件；
- 只要有任一证据缺失或未通过，门禁即整体判定 `blocked` 并以非零退出码收束，父工单
  （13/13A/13B/13C）据此保持 blocked，**不允许进入删除（contract）步骤**。

## 门禁如何运行

```bash
python scripts/phase5_deletion_gate.py         # 人类可读报告
python scripts/phase5_deletion_gate.py --json  # 结构化 JSON 报告（schema=ccb.phase5.deletion_gate.v1）
```

退出码：`0` = 全部删除项证据齐备可放行；`2` = 门禁未通过（blocked）。

live validation 证据以 JSON 落盘于 `plans/architecture-optimization/live-validation/`，
顶层须同时含 `passed: true` 与非空 `evidence` 记录才算通过；裸 `{"passed": true}` 空桩、
文件缺失或解析失败一律 fail-closed。

> 单一事实源：删除项清单以脚本 `DELETION_ITEMS` 为准，下方「待删除项验收清单」是供人阅读的
> 镜像。改动删除项、证据路径或 rollback 文案时以脚本为准并重跑门禁，本文档随之同步。

## 优化前后关键差异（治理已完成项）

老目录 `E:\claude_code_bridge`（优化前）与当前目录（优化后）的关键差异，已由父工单 13 的
逐项治理记录，均已带 characterization test 落地：

| 删除项 | 优化前 | 优化后 | 状态 |
| --- | --- | --- | --- |
| `CCB_HERDR_CAPABILITY_REPORT` 正常启动路径 | 启动路径依赖临时 capability report 文件 | capability 证据来自握手/binding | 已删除 |
| bootstrap capability probe 与临时文件写入 | bootstrap 做 read-only probe 并写临时文件 | 只解析可执行文件、确认会话、返回 socket ref | 已删除 |
| 宽 CLI 操作白名单 | 宽白名单放行低层 operation | 仅保留诊断/兼容 fallback | 已收窄 |
| `backend_resolver` 低层 capability 组合判断 | `semantic_status` 并列作为低层 gate 条件 | 只看 `command_status` | 已移除 |

## 待删除项验收清单（仍 blocked）

以下删除项由门禁脚本 `DELETION_ITEMS` 声明，当前均因缺 live validation 证据而 blocked：

### 1. `delete-ccb-pane-agent-report-patch`（来源 13B，阻塞于 13A）

- **删除内容**：`tmux_runtime` 中 CCB 主动补 Herdr Agent 身份（`report_pane_agent`）的正常路径。
- **characterization test**：`test/test_herdr_runtime_contracts.py`、
  `test/test_v2_project_namespace_state.py`。
- **live validation**：
  - `live-validation/agent-id-authority.json`——需实机证明 Herdr 在 runtime ensure/agent start
    后稳定回写 `agent_id`，reconnect/restore 后不漂移；
  - `live-validation/archi-hotspot-baseline.json`——`archi .` / archify 可重跑且 Herdr/CLI
    runtime hotspot 不恶化。
- **rollback 条件**：删除后若 reconnect/restore 出现 `agent_id` 漂移，或 runtime binding 丢失
  pane/agent/provider/generation 归属，恢复 `report_pane_agent` 补丁并保持 blocked-by-13A。

### 2. `narrow-backend-capability-compat-gate`（来源 13C）

- **删除内容**：`backend.py` / `runtime/capabilities.py` / `project_namespace_runtime/backend.py`
  的兼容 capability gate，仅保留诊断/兼容 fallback。
- **characterization test**：`test/test_herdr_backend_client.py`、`test/test_ccbd_project_view.py`、
  `test/test_mobile_gateway_service.py`。
- **live validation**：
  - `live-validation/no-wezterm-gui-fallback.json`——无 WezTerm GUI 时可观测回退；
  - `live-validation/mux-multi-project-attach.json`——有 mux 时多项目 attach 符合「同窗堆 tab」；
  - `live-validation/mobile-gateway-redaction.json`——面板/mobile gateway 不泄漏
    prompt/reply/API key/OAuth token；
  - `live-validation/archi-hotspot-baseline.json`——`archi .` / archify 可重跑且 Herdr/CLI
    runtime hotspot 不恶化。
- **rollback 条件**：删除兼容 gate 后若明确选择 Herdr 后端在不可用时不再 fail-closed，或
  `project_view` / mobile gateway 泄漏敏感字段，恢复兼容 gate。

## 与上游阻塞的关系

本门禁只把「删除是否可放行」变成可重跑判定，不改变阻塞事实：

- 13A（Herdr 原生 `agent_id` 权威）与 12C（Herdr 原生 restart/backoff/cleanup）仍需 Herdr
  上游能力与 Windows live validation 环境；
- 在这些证据以 `passed=true` 落盘于 `live-validation/` 之前，门禁对相关删除项持续报 blocked，
  这正是期望行为——避免在证据不足时误删旧路径。
