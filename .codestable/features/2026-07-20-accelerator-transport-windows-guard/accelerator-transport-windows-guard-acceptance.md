---
doc_type: feature-acceptance
feature: 2026-07-20-accelerator-transport-windows-guard
status: passed
audit_state: completed
audit_reason: ""
auditor_id: ""
acceptance_authorization_ref: approval-report.md#goal-acceptance
accepted: 2026-07-21
round: 1
---

# accelerator-transport-windows-guard 验收报告

> 阶段：阶段 3（验收闭环）
> 验收日期：2026-07-21
> 关联方案 doc：`.codestable/features/2026-07-20-accelerator-transport-windows-guard/accelerator-transport-windows-guard-design.md`

验证证据来源：`accelerator-transport-windows-guard-qa.md` round 1（status: passed）+ 本次 final audit 抽样复核。Goal 授权：`goal-state.yaml` `acceptance_authorization_ref: approval-report.md#goal-acceptance`，且同 unit `approval-report.md` `approvals.goal-acceptance: approved`。

## 1. 接口契约核对

对照方案第 2.1 节名词层：

**接口示例逐项核对**：
- [x] `accelerator_transport_available()` / `accelerator_unsupported_reason()`（`lib/runtime_accelerator/platform.py`）：单一 availability helper 和稳定 reason `unsupported_platform:windows_no_af_unix` 已落地。
- [x] `client.call()`：创建 `socket.AF_UNIX` 前先检查 availability；unsupported transport 转为 `AcceleratorError`。
- [x] `RuntimeAcceleratorHandle` fallback handle：`enabled=True/process=None/error=<reason>/socket_path=<resolved>` 已由 lifecycle test 覆盖。

**名词层"现状 → 变化"核对**：
- [x] `AcceleratorError` 继续作为 client 对外失败类型；`call_or_fallback()` 不扩 catch-all。
- [x] unsupported accelerator transport 被归一为 clean fallback，不误归因为 missing binary、startup timeout 或 owner mismatch。
- [x] ownership connectability / reclaim / corrupt recovery 在 no-AF_UNIX 下 fail-closed，不删除 evidence。

**流程图核对**（第 2.2 节 mermaid）：
- [x] `codex ask/poll starts -> accelerator enabled -> transport available? -> no -> AcceleratorError/fallback handle -> python polling path` 有代码落点：`client.py`、codex polling wrapper、`lifecycle.py`、`ownership.py` 与 focused tests 覆盖。

无偏差。

## 2. 行为与决策核对

**需求摘要逐项验证**：
- [x] no-AF_UNIX 下 `poll_with_accelerator()` 返回 `None`，不抛 `AttributeError`：QA-004 passed。
- [x] `call()` 抛 `AcceleratorError("unsupported_platform:windows_no_af_unix")`，`call_or_fallback()` 触发 fallback：QA-003 passed。
- [x] lifecycle unsupported transport 不 binary lookup / reclaim / mkdir / Popen，返回 fallback handle：QA-005 passed。
- [x] ownership socket probe、direct reclaim、corrupt owner recovery 不抛 `AttributeError`，不误删 evidence：QA-006 passed。
- [x] AF_UNIX 可用平台既有 tests 不漂移：aggregate pytest passed with platform skips only。

**明确不做逐项核对**（第 3.2 节反向核对项）：
- [x] 未新增 Windows accelerator TCP / named pipe server/client。
- [x] 未扩大 `poll_with_accelerator()` 为 catch-all。
- [x] unsupported platform 下不启动 sidecar、不 reclaim owner、不删除 socket、不杀 legacy pid。
- [x] 未修改 ccbd 控制面 transport seam、Rmux backend、process liveness、provider parser、packaging/docs。
- [x] 未改变 Unix AF_UNIX accelerator 协议与 response parsing。

**关键决策落地**：
- [x] 单一 availability helper：`lib/runtime_accelerator/platform.py`。
- [x] client fallback 语义：unsupported transport 只转 `AcceleratorError`，call site 仍只捕获该类型。
- [x] lifecycle 语义：fallback handle 发生在 startup side effect 之前。
- [x] ownership 语义：unsupported transport direct reclaim no-op；corrupt owner recovery blocked/warning 并保留证据。

**挂载点反向核对（可卸载性）**：
- [x] 挂载点清单均有代码落点：`client.py`、`lifecycle.py`、`ownership.py`、`platform.py`、codex polling tests 和 runtime accelerator tests。
- [x] **反向 grep**：`socket.AF_UNIX` 在 `lib/runtime_accelerator` 生产代码仅命中 `client.py` 和 `ownership.py`，均在 availability guard 之后；测试命中为 Unix listener 覆盖。
- [x] **拔除沙盘推演**：移除 `platform.py` 会导致三处 import 失败，说明 helper 是真实单一 owner；后续提交必须纳入该文件。

## 3. 验收场景核对

- [x] **AC-001** no-AF_UNIX 调用 `runtime_accelerator.client.call()`：抛 `AcceleratorError`，reason 稳定，QA-003 passed。
- [x] **AC-002** `call_or_fallback()` no-AF_UNIX：返回 fallback 值，QA-003 passed。
- [x] **AC-003** codex accelerator 默认 enabled 且 no-AF_UNIX：`poll_with_accelerator()` 返回 `None`，QA-004 passed。
- [x] **AC-004** `poll_submission()` no-AF_UNIX 有可读 session：走普通 reader fallback，QA-004 passed。
- [x] **AC-005** lifecycle no-AF_UNIX：fallback handle 且不执行 startup side effect，QA-005 passed。
- [x] **AC-006** ccbd startup actions 消费 unsupported handle：输出 `runtime_accelerator_fallback:unsupported_platform:windows_no_af_unix`，QA-005 passed。
- [x] **AC-007** connectability no-AF_UNIX：返回 `False`，QA-006 passed。
- [x] **AC-008** direct reclaim no-AF_UNIX：不 terminate、不删 owner/socket evidence，QA-006 passed。
- [x] **AC-009** corrupt recovery no-AF_UNIX：blocked/warning 并保留 evidence，QA-006 passed。
- [x] **AC-010** Windows baseline：`Path("/repo")` expectation 已平台中立，aggregate pytest passed。
- [x] **AC-011** Unix / AF_UNIX regression：aggregate pytest passed with platform skips only。
- [x] **AC-012** scope guard：diff scope passed，无越界。

**功能性前端**：本 feature 无 UI，用 runtime unit/regression evidence 替代，无需浏览器核对。

**review 报告重点复核**：
- [x] `{slug}-review.md` 第 5 节 Test And QA Focus 已逐条覆盖。
- [x] `{slug}-review.md` 第 6 节 residual risk 已逐条处理：真实 full-chain smoke 留给最终 feature；Windows accelerator transport 是明确不做项。

**QA 报告重点复核**：
- [x] 验证证据来源：`accelerator-transport-windows-guard-qa.md` round 1（passed）。
- [x] QA Verification Matrix 覆盖 design 关键场景、DoD commands、review QA focus、evidence pack residual。
- [x] failed / blocked 项为 none。
- [x] residual-risk 未承载核心验收缺口。
- [x] Evidence pack、DoD Results、Gate Results 已复核；blocking DoD 均有 pass evidence。CMD-006 原始 warning 已由显式文件列表复跑关闭。

## 4. 术语一致性

- `runtime accelerator`：代码命中仍集中于 runtime accelerator 模块与 codex polling；未与 ccbd control-plane RPC transport 混用。
- `unsupported_platform:windows_no_af_unix`：`platform.py`、tests、QA/report 使用一致。
- `clean fallback`：client error、polling `None`、lifecycle handle error、ownership no-op/fail-closed 语义一致。
- 防冲突：无 Windows accelerator transport、无 `RpcTransport` seam 复用。

无不一致。

## 5. 领域影响盘点（提示而非代写）

- **流程级约束**：runtime accelerator 是性能优化；native Windows 无 AF_UNIX 时必须 clean fallback，不能阻断 `ccb ask`。该约束已写入 roadmap/design/acceptance，建议后续需要长期沉淀时走 `cs-domain` 或 `cs-keep`。
- **结构性选择**：新增 `lib/runtime_accelerator/platform.py` 作为 availability helper 单一 owner；目前是模块内窄 helper，不需要 ADR。
- **新名词**：无需要写入 `requirements/CONTEXT.md` 的用户层新术语。

本节仅登记 + 建议，不在 accept 内改 CONTEXT.md 或写 ADR。

## 6. requirement delta / clarification 回写

design frontmatter `requirement:` 为空；本 feature 修复 native Windows fallback 行为，不新增用户可见能力、不改长期 requirement。→ **无 requirement 影响**，跳过。

## 7. roadmap 回写

design frontmatter `roadmap: windows-rmux-native-backend` / `roadmap_item: accelerator-transport-windows-guard`，两字段成对存在：
- [x] `items.yaml` 找到 `slug: accelerator-transport-windows-guard`，当前 `status: in-progress` + `feature: 2026-07-20-accelerator-transport-windows-guard` 核对无误。
- [x] 改 `status: done`，并用 `validate-yaml.py` 校验。
- [x] 同步 `windows-rmux-native-backend-roadmap.md` 子 feature 清单对应条目状态。

## 8. attention.md 候选盘点

- 候选 1：Windows PowerShell 不展开 `rg` 里的 `test/test_runtime_accelerator_*.py` glob，需用显式文件列表。该坑已在本 QA / review 中记录，若后续反复命中可用 `cs-note` 写入 attention.md；本 accept 不直接修改 attention。
- 其余无"每个 feature 都会撞一次"的新环境/工具/工作流候选。

## 9. 遗留

- 后续优化点：若未来要支持 Windows accelerator transport，应单独设计 TCP/named-pipe server/client、owner identity、安全 reclaim、binary packaging，不从本 guard feature 顺手扩展。
- 已知限制：
  - 本 feature 未执行真实 native Windows full-chain `ccb ask` smoke；终点证据由后续 `ccbd-windows-full-chain-smoke` 负责。
  - Windows accelerator transport 仍未实现；当前仅保证 clean fallback。
  - `lib/runtime_accelerator/platform.py` 当前是 untracked 文件，scoped commit 前必须纳入。
- 实现阶段顺手发现：原 CMD-006 PowerShell glob 写法不可移植，已用显式文件列表复跑并关闭风险。

## 10. 最终审计

用最终工作区反查原始设计：

**聚合命令复验**：
- CMD-001 checklist YAML valid → exit 0（re-verified）。
- CMD-002 items YAML valid → exit 0（re-verified；acceptance 回写后需再次复跑）。
- CMD-003 aggregate runtime accelerator tests → `46 passed, 3 skipped`（re-verified）。
- CMD-004 focused codex accelerator tests → `6 passed`（re-verified）。
- CMD-005 scope guard → only runtime accelerator and focused tests（re-verified；untracked `platform.py` 属本 feature）。
- CMD-006 explicit AF_UNIX grep → exit 0，guard 后生产命中 + Unix-only test 命中（re-verified）。

**场景抽样复核**：AC-001/002/003/004/005/006/007/008/009 由 fresh pytest 覆盖；AC-010/011 由 aggregate regression 覆盖；AC-012 由 scope guard + review 覆盖。

**交付物 / 工作区 / diff 清洁度**：
- 交付物齐全：review passed、QA passed、acceptance passed、availability helper、client/lifecycle/ownership guard diff、focused tests、scope/evidence/DoD artifacts。
- 清洁度：debug/TODO/注释代码/死 import 均 pass。
- 工作区仍包含未提交的 current feature code/spec/report/state 改动；进入下一 feature 前需 scoped commit，但本轮未执行 git commit。

**覆盖率诚实标记**：re-verified = CMD-001/002/003/004/005/006 + AC-001..AC-012；trust-prior-verify = 独立 reviewer code line evidence；residual-risk = final full-chain smoke / Windows accelerator transport out of scope。

**结论**：无未处理验收缺口。所有 checklist checks → passed。

## Verdict

- Status: passed
- Goal 授权：`ResumeGoalAcceptance approval-report.md#goal-acceptance`，与 goal-state 匹配、approval-report `goal-acceptance: approved`。
- Next：feature status → accepted，`current_feature_index` 2→3。进入下一 feature 前按 goal protocol 需要 scoped commit；本轮遵守高风险 Git 操作确认规则，未自动提交。
