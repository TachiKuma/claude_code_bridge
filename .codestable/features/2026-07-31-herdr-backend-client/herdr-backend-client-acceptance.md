---
doc_type: feature-acceptance
feature: 2026-07-31-herdr-backend-client
status: passed
audit_state: not-started
audit_reason: ""
auditor_id: ""
acceptance_authorization_ref: approval-report.md#goal-acceptance
accepted: 2026-08-02
round: 2
---

# herdr-backend-client 验收报告

## 0. Reopen Acceptance 2026-08-02

Scope: owner approved `ReopenBackendClient` to fix real Herdr server lifecycle and split direction defects discovered during `ccbd-herdr-namespace-lifecycle` CMD-013 probing.

### Acceptance Delta

- [x] Herdr CLI adapter owns server lifecycle startup for server-backed commands: on real Herdr NotFound it starts `herdr --session <name> server` and retries the original command.
- [x] Existing recorded server process is checked with `poll()`; exited process records are cleared and respawned on the next NotFound.
- [x] `server_info` remains read-only and does not start Herdr server.
- [x] `bottom` maps to Herdr `down`, preventing CMD-013 vertical layout from collapsing into horizontal layout.
- [x] `left/up/unknown` directions fail closed before any Herdr command, avoiding external side effects and silent topology corruption.
- [x] Real Herdr smoke passed on `C:/Users/Administrator/AppData/Local/Programs/Herdr/herdr.exe`.

### Evidence

- Evidence file: `.codestable/features/2026-07-31-herdr-backend-client/evidence/real-herdr-server-lifecycle-direction-fix.md`
- Review closure: `.codestable/features/2026-07-31-herdr-backend-client/herdr-backend-client-review.md#0-reopen-review-2026-08-02`
- QA delta: `.codestable/features/2026-07-31-herdr-backend-client/herdr-backend-client-qa.md#0-reopen-qa-2026-08-02`

### Verdict

passed. The previous acceptance residual risk "real Herdr host smoke not run" is resolved for server lifecycle and split direction. Remaining `send_text` / `pane run` semantic risk is explicitly out of this reopen scope.

Note: full-worktree scope guard is currently polluted by pre-existing `ccbd-herdr-namespace-lifecycle` diffs. Reopen-scoped guard for backend-client files and reports passed; no provider/runtime/recovery/doctor/package/release files are attributable to this backend-client reopen.

> 阶段：Goal feature acceptance
> 验收日期：2026-08-02
> 关联方案 doc：`.codestable/features/2026-07-31-herdr-backend-client/herdr-backend-client-design.md`

## 1. 接口契约核对

**接口示例逐项核对**：

- [x] `HerdrBackendClient` contract：`server_info/create_session/restore_session/create_pane/send_text/capture_pane/kill_pane` 均由 `HerdrSocketClient` 实现，并只返回 `MuxNamespaceRefV2`、`MuxPaneRefV2`、`MuxOperationEvidenceV2` 或 structured error。
- [x] `HerdrBackend` facade：实现 `TerminalBackend` 所需的 session/pane/send/capture/kill/is_alive/activate 入口；不把 raw Herdr JSON 暴露给调用层。
- [x] resolver/factory 接口：`api.py` 通过 `_herdr_backend_factory` 注入 `HerdrBackend`，`backend_selection.py` 先走 `resolve_mux_backend_v2` gate，再构造 backend。

**名词层“现状 → 变化”逐项核对**：

- [x] 新增 `lib/terminal_runtime/herdr_backend.py` 与 `herdr_backend_runtime/*`，按 `tmux_backend.py` + runtime package convention 拆分。
- [x] Herdr schema/capability/error/evidence 均留在 terminal_runtime adapter 边界内；ccbd/provider/runtime 未被提前接入。
- [x] `TerminalBackendSelection` 增加 Herdr factory 与 platform/capability report 注入，不改 tmux 默认路径。

**流程图核对**：

- [x] capability gate：`HerdrCapabilityGate.from_spike_evidence` 与 `_herdr_capability_gate` 覆盖缺失、畸形、unknown、gaps、非 continue/pass。
- [x] schema gate：`HerdrSocketClient.server_info()` 在 mutation 前执行，mismatch 抛 `MuxCommandErrorV2(category="schema-mismatch")`。
- [x] operations：create/restore/pane/send/capture/kill 均有 fake socket/CLI 单测覆盖。
- [x] resolver/factory route：explicit `herdr` 和 `auto` gate pass/fail 均有 selection tests。

## 2. 行为与决策核对

**需求摘要逐项验证**：

- [x] schema mismatch 为 structured `schema-mismatch`，包含 expected/actual schema、platform、arch 和 socket evidence。
- [x] capability evidence 缺失、stop/needs-upstream-issue、blocked/failed、failure_class 非 none、blocking gaps、unknown status 均 fail closed。
- [x] HerdrBackend 返回 `backend_family="herdr-native"`、`backend_impl="herdr"`、`ipc_kind="herdr_socket"`。
- [x] explicit `herdr` failure 抛 `MuxCommandErrorV2`；auto/default Herdr prepare/factory failure 返回 `None` 且不 fallback tmux。
- [x] 非 Windows auto/default 保持 tmux 路径，不因新增 Herdr adapter 改变默认行为。

**明确不做逐项核对**：

- [x] 未修改 `lib/ccbd/services/project_namespace_state_runtime/` 或 project namespace lifecycle。
- [x] 未修改 `lib/provider_runtime/`、`lib/provider_backends/` 或 provider completion 逻辑。
- [x] 未修改 doctor/support tier、package metadata、installer、release/update surface。
- [x] 未把 Herdr agent state 写成 CCB completion verdict。

**关键决策落地**：

- [x] `send_text` 使用 Herdr `pane run` 是本 feature 已接受适配决策，已在 review/QA residual risk 中标注。
- [x] explicit socket override 只接受 exact `ipc_ref`；默认 CLI adapter 可接受 exact `herdr://{session_name}`，foreign session ref 被归一化。
- [x] restore token 必须 exactly one `session::workspace`，响应 namespace/session/token 必须匹配。

**挂载点反向核对（可卸载性）**：

- [x] 挂载点均落在 design 第 2.3 节：`lib/terminal_runtime/herdr_backend.py`、`herdr_backend_runtime/*`、`api.py`、`api_selection.py`、`backend_resolver.py`、`backend_selection.py` 和 focused tests。
- [x] `rg -n "HerdrBackend|HerdrSocketClient|HerdrCapabilityGate|HerdrCliRequestAdapter|_herdr_backend_factory|resolve_mux_backend_v2|CCB_HERDR" "lib/terminal_runtime" "test"` 只显示 terminal_runtime 与测试内引用。
- [x] 拔除沙盘推演：删除 Herdr backend/runtime、新测试和 api/selection/resolver Herdr 接线即可卸载本 feature；ccbd/provider/package 无残留。

## 3. 验收场景核对

- [x] AC-001 缺 upstream evidence：QA-001 pass，capability gate blocked。
- [x] AC-002 stop/gaps/unknown：QA-002 pass，fail closed。
- [x] AC-003 schema pass：QA-003 pass。
- [x] AC-004 schema mismatch：QA-004 pass。
- [x] AC-005 create/restore session refs：QA-005 pass。
- [x] AC-006 pane IO/evidence：QA-006 pass。
- [x] AC-007 explicit route success：QA-007 pass。
- [x] AC-008 explicit route failure：QA-007 pass，failure 不 fallback。
- [x] AC-009 auto selection：QA-008 pass。
- [x] AC-010 scope boundary：QA-010 pass。

**review 报告重点复核**：

- [x] 真实 Herdr CLI/host shape：当前 PATH 无 `herdr`，未运行实机 smoke；design 将 fake socket/CLI 单元和 contract tests 定义为本 feature 核心证据，真实 host 留作后续集成 residual risk。
- [x] session-scoped IPC ref 与 explicit socket override：已有单测覆盖 exact current socket、exact session-scoped、foreign ref normalization。
- [x] legacy pane lifecycle：已记录为 residual risk，不承载 durable refs 验收。

**QA 报告重点复核**：

- [x] 验证证据来源：`.codestable/features/2026-07-31-herdr-backend-client/herdr-backend-client-qa.md`，frontmatter `status: passed`。
- [x] QA matrix 覆盖 design AC、DoD commands、review Test And QA Focus 和 residual risk。
- [x] failed / blocked 项为 none。
- [x] residual-risk 不承载本 feature 核心验收缺口。
- [x] Evidence pack、DoD Results、Gate Results：本 feature 无这些独立产物；QA 报告已记录为 none，DoD 命令均 fresh 运行通过。

## 4. 术语一致性

- Herdr backend/client/capability/schema 术语在 code、tests、design、review、QA 中一致。
- `herdr-native`、`herdr`、`herdr_socket` 使用来自 `mux_backend_contract` 的 V2 contract，不重复定义 family/impl/ipc 字面契约。
- 禁用方向核对：content guard 对本 feature diff 中 provider completion/support/release 相关 terms 退出 0；完整仓库已有 `completion_source` 命中属于既有 provider 代码，不归因本 feature。

## 5. 领域影响盘点（提示而非代写）

- [x] 新名词候选：`HerdrBackend`、`HerdrSocketClient`、Herdr capability/schema gate。它们属于 roadmap §4.4 的内部 adapter 术语，当前 design/acceptance 已记录；完整领域术语可在后续 `cs-domain` 统一沉淀。
- [x] 结构性选择候选：Herdr adapter 作为 terminal_runtime deep module，resolver/factory 只接 gated backend。该选择有 ADR 价值，但本 feature 不在 acceptance 直接代写 ADR。
- [x] 流程级约束候选：Herdr 缺 evidence/schema/capability/platform 时 fail closed；后续若多 feature 复用，应走 `cs-keep` 或 `cs-domain` 沉淀。

## 6. requirement delta / clarification 回写

- Requirement ref: `.codestable/requirements/native-windows-ccb-via-herdr.md`，status 为 `draft`。
- Capability impact: 本 feature 实现 roadmap 已批准的内部 Herdr backend adapter 子能力，不单独改变用户故事、support tier 或 public workflow boundary。
- Writeback verdict: requirement unchanged。无需在 acceptance 阶段自由重写 requirement，也无需生成新的 req delta。

## 7. roadmap 回写

- [x] `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml`：`herdr-backend-client` `status: in-progress -> done`，notes 更新为交付摘要。
- [x] `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-roadmap.md`：第 3 节 item 4 `状态：in-progress -> accepted`，备注更新。
- [x] `.codestable/roadmap/windows-native-herdr-ccb/goal-state.yaml`：`herdr-backend-client` `status: pending -> accepted`，`current_feature_index: 3 -> 4`。

## 8. attention.md 候选盘点

- [x] 本 feature 未暴露需要补入 `attention.md` 的新全局规则。
- [x] `.codestable` checklist 的 CRLF warning 已是本次上下文中的已知事项，不在 acceptance 内重复写 attention。
- [x] 真实 Herdr executable 未在 PATH 属于本机集成环境状态，不是每个 feature 都必须知道的长期仓库规则。

## 9. 遗留

- 后续优化点：真实 Herdr host integration/QA，验证 `workspace create/list`、`pane split/run/read/close` 输出形态与 pane lifecycle。
- 已知限制：`send_text` via `pane run` 是当前适配决策；stdin-style input 需要另开协议/adapter 能力修正。
- 已知限制：legacy string pane IDs 只在创建它们的 backend 实例内可靠；跨进程/durable 操作应使用 `MuxPaneRefV2`。
- 实现阶段顺手发现：无需要本 feature 内继续处理的越界项。

## 10. 最终审计

- 验证证据来源：`herdr-backend-client-qa.md`，`status: passed`。
- Evidence sources：evidence pack / DoD results / gate results 均为 none；design DoD commands 已由 QA fresh 运行。
- 聚合命令：py_compile exit 0；checklist YAML exit 0；roadmap items YAML exit 0；focused Herdr/selection tests 150 passed；V2/herdr contract 8 passed；contract+selection regression 35 passed；contract+selection+spike regression 38 passed；CMD-006/CMD-007 exit 0；`git diff --check` exit 0，仅已知 CRLF warning。
- 场景复核：re-verified 13 / trust-prior-verify 0。
- 交付物复核：代码、schema/capability/error/evidence、route、review、QA、acceptance、roadmap、goal-state 均已落盘。
- 完整工作区复核：tracked diff 与 untracked files 均已纳入判断；baseline dirty `笔记.md` 排除。
- diff 清洁度：通过；`rg` 只命中测试中的有意 `python -c "print(...)"` 字符串。
- 知识沉淀出口：Herdr adapter deep module 与 fail-closed gate 是 `cs-domain`/`cs-keep` 候选；无 attention/doc-api 立即必改项。
- workflow-next：`codestable-workflow-next.py epic --roadmap ".codestable/roadmap/windows-native-herdr-ccb" --json` exit 0，返回 `status: dispatch_goal`，evidence 含 `approval-report.md#goal-acceptance` 与 `approval-report.md#goal-commits`。
- Commit boundary：当前会话明确禁止执行 `git commit`；因此未按 goal loop 进入 scoped commit，也未继续下一 feature。
- 结论：通过。Goal acceptance authorization `approval-report.md#goal-acceptance` 已机械核验为 approved，本 feature acceptance completed。

## Verdict

**passed** —— design/checklist/review/QA/roadmap 回写均满足；残留风险为后续集成验证项，不阻塞本 feature。
