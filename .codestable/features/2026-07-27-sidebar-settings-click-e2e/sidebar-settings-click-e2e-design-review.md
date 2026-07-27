---
doc_type: feature-design-review
feature: 2026-07-27-sidebar-settings-click-e2e
status: passed
review_state: passed
review_reason: ""
reviewer_id: "019fa3c8-5dc9-76d0-b896-164d4ed62c10"
reviewed: 2026-07-27
round: 3
---

# sidebar-settings-click-e2e feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-27-sidebar-settings-click-e2e/sidebar-settings-click-e2e-design.md`
- Checklist: `.codestable/features/2026-07-27-sidebar-settings-click-e2e/sidebar-settings-click-e2e-checklist.yaml`
- Intent / brainstorm: `.codestable/features/2026-07-27-sidebar-settings-click-e2e/sidebar-settings-click-e2e-brainstorm.md`
- Roadmap: `.codestable/roadmap/windows-rmux-ux-parity-hardening/windows-rmux-ux-parity-hardening-roadmap.md`
- Roadmap items / goal: `.codestable/roadmap/windows-rmux-ux-parity-hardening/windows-rmux-ux-parity-hardening-items.yaml`, `.codestable/roadmap/windows-rmux-ux-parity-hardening/goal-state.yaml`, `.codestable/roadmap/windows-rmux-ux-parity-hardening/goal-features/sidebar-settings-click-e2e.md`
- Related docs: `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/evidence/root-cause-review-and-feature-split.md`
- Code facts checked: `tools/ccb-agent-sidebar/src/tui.rs`, `tools/ccb-agent-sidebar/src/args.rs`, `lib/cli/services/tmux_ui_runtime/service.py`, `lib/ccbd/services/project_namespace_runtime/sidebar_helper.py`, `lib/ccbd/services/project_namespace_runtime/materialize_topology.py`, `lib/ccbd/services/project_namespace_runtime/topology_plan.py`, `lib/ccbd/services/project_namespace_pane.py`

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: round 1 `019fa3ba-8308-7271-89d5-e7b244781955`; round 2 `019fa3c1-8d1d-7bb3-b123-0d8bcd523a2d`; round 3 `019fa3c8-5dc9-76d0-b896-164d4ed62c10`
- Raw output: round 1 reported 3 blocking + 3 important；round 2 reported 1 blocking + 2 important；round 3 reported no blocking/important, 1 nit 和 1 residual-risk。
- Merge policy: 已逐条核验 reviewer finding，并用 design / checklist / roadmap / code facts 确认成立项和 closure。
- Gate effect: independent review completed，允许本地合并为 passed。

## 2. Design Summary

- Goal: 诊断并修复 native Windows + WezTerm + rmux 下 sidebar settings 点击端到端无反应问题。
- Key contracts: canonical owner 是顶层 roadmap item `sidebar-settings-click-e2e`；probe seam 固定为 opt-in env `CCB_AGENT_SIDEBAR_MOUSE_PROBE`；UX parity JSON 必须拒绝无归因 non-pass evidence。
- Steps: 8 步，覆盖 pane identity/fingerprint、role/target failure、Windows/rmux fallback binding、event/action probe、config UI visible failure、foreground transcript、scope guard。
- Checks: 7 条 AC 覆盖 identity、binding、mouse event/action、config UI ready/failed、helper/pane option 归因和非目标路径守护。
- Baseline / validation: 复用父 feature 根因审查、现有 rmux binding 测试、Rust sidebar hit-test/config UI 单测、helper fingerprint/topology refresh 机制；新增 foreground transcript 和 probe evidence。

## 3. Findings

### blocking

- [x] FDR-001 `CMD-005` 未落实 roadmap non-pass evidence 契约。
  - Evidence: round 1 指出 checklist 的 JSON validator 只校验 required fields / enum / 类型，不能拒绝 `evidence_status=blocked` 且无 residual/failure detail。
  - Impact: supportability 可能消费一个“校验通过但无归因”的失败证据。
  - Closure: design 成功标准和 CMD-005 已要求 artifact refs 非空且存在、non-pass 必须有 `residual_risks` 或 `failure_detail`、`blocked|failed` 时 `failure_class != none`。round 3 reviewer confirmed。

- [x] FDR-002 opt-in probe 启用路径不可执行。
  - Evidence: `tools/ccb-agent-sidebar/src/args.rs:34-53` 未知参数失败，`topology_plan.py:162-169` 生成固定 sidebar launch args；原 design 允许 env 或 CLI 二选一但未定传播。
  - Impact: AC-003 可能只剩单测 seam，真实 sidebar pane 无法产出 event/action 证据。
  - Closure: design 选择单一 env `CCB_AGENT_SIDEBAR_MOUSE_PROBE=<path>`，明确启动/respawn 前设置、已运行 ccbd 需重启或证明父进程 env、输出路径和清理规则；checklist S5 同步。round 3 reviewer confirmed。

- [x] FDR-003 config UI 启动失败可见状态描述误导。
  - Evidence: `tui.rs:531-537` 的同步 launch 失败写 `last_error`，现有测试只断言 `config ui launch failed:`；`config_ui_status_line()` 只覆盖 async launch status。
  - Impact: cargo test 可能通过但用户仍看不到 `config ui failed:`，表现为“无反应”。
  - Closure: design AC-005 和 checklist S6 明确覆盖同步 spawn/launch 失败与子进程运行后失败，且要求渲染层可见失败状态，不只写内部 `last_error`。round 3 reviewer confirmed。

- [x] FDR-007 roadmap 双重认领 split child。
  - Evidence: round 2 指出父 item `split_children.sidebar-settings-click-e2e` 与顶层 item / `goal-state.yaml` 同时携带 owner-like pointer。
  - Impact: epic/goal 恢复可能 fail-closed 或 supportability 重复计入。
  - Closure: 父 item 的 split child 已降级为 `owner: trace-only` + `canonical_item`，移除 `feature` / brainstorm / design admission；canonical owner 只保留顶层 item 和 `goal-state.yaml` 同名 row。CMD-006 workflow-next 已通过；round 3 reviewer confirmed。

### important

- [x] FDR-004 `send-keys c` 范围术语冲突。
  - Evidence: 非 fallback `#{mouse_pane}` 路径已有 `send-keys c` 坐标命令；原 design 容易被读成全局禁止。
  - Closure: design 明确只拒绝 Windows/rmux fallback / `without_mouse_pane_format` 恢复 `send-keys -t = c`，非 fallback 路径 out-of-scope。round 3 reviewer confirmed。

- [x] FDR-005 Acceptance Coverage Matrix 漏 S3。
  - Evidence: checklist S3 是 pane target / role failure tests；round 2 指出 matrix 未承接 S3 / AC-006。
  - Closure: matrix 已新增 `pane target / role failure | S3` 和 `helper stale / pane option 异常归因 | S2, S3`。round 3 reviewer confirmed。

- [x] FDR-006 Goal lane 交付物投影不足。
  - Evidence: design/checklist 有 CMD-005/CMD-006，但 goal-feature projection 原摘要未列这些命令。
  - Closure: design 增加 Required artifacts / Goal lane projection；goal-feature §4 明确继承 checklist `dod.commands`，并摘要列出 CMD-005/CMD-006。round 3 reviewer confirmed。

### nit

- [x] FDR-008 roadmap 历史状态文案可能误导当前状态。
  - Evidence: round 3 指出 roadmap §5 的 split 说明仍写 `sidebar-settings-click-e2e` 状态 failed，而 canonical item 已 in-progress。
  - Closure: roadmap 文案已改为“历史拆分状态：failed；当前执行状态见顶层 roadmap item `sidebar-settings-click-e2e`”。

### suggestion

- none

### learning

- split child 一旦提升为顶层可恢复 item，父 item 的拆分清单只能保留 trace-only 索引，不能携带 `feature` 指针或 design admission 等 owner-like 字段。
- 对前台 GUI 交互失败，`list-keys` 和本进程 hit-test 单测只能做 supporting evidence；core evidence 必须覆盖真实 pane identity、binding、event/action 和用户可见结果。

### praise

- 设计把“无反应”拆成 identity、binding、event/action、config UI status 四段，每段都有可证伪证据。
- probe seam 选择 env 而非 CLI 参数，与当前 `args.rs` 和 topology 固定 launch args 的代码事实一致，避免扩大参数契约。

## 4. User Review Focus

- 用户需要重点拍板：接受 settings click 先走诊断优先，不在本 feature 中合并 KillProject 或普通 pane drag/right/wheel。
- implement 需要重点遵守：probe 默认关闭、有界输出；前台 QA 必须在持有 env 的 ccbd/namespace 下运行；失败归因不能跳过 identity/binding/event/action 顺序。
- code review / QA / acceptance 需要重点复核：同步 config UI launch 失败也必须进入渲染层可见失败状态；UX parity JSON 的 non-pass 归因必须可机器校验；父 split trace 不得重新变成 owner。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | matrix 覆盖 S1-S8，包含 S3 / AC-006、CMD-005 JSON、foreground transcript 和 scope guard | none |
| DoD Contract | pass | E | DOD-DESIGN/IMPL/QA/GOAL 覆盖 design gate、probe/evidence、foreground QA、goal projection | none |
| Steps and checks traceability | pass | E | checklist YAML validate passed；steps/checks 均 pending 且可追溯到 design §3 | none |
| Roadmap contract compliance | pass | E/C | canonical owner 为顶层 item + goal-state；父 split trace-only；UX parity schema 对齐 roadmap §4.1 | none |
| Module interface design | pass | C | probe seam 放在 env + bounded evidence，Rust CLI 参数不扩张；config UI failure contract 指向渲染层 | implementation 写真实 seam |
| Validation and artifacts | pass | E/C | CMD-001 到 CMD-006 覆盖 pytest/cargo/py_compile/JSON/workflow-next；goal-feature 继承 checklist commands | implementation 产出 evidence 文件 |

Summary: E=4, C=2, H=0, H-only core checks=none。

## 6. Residual Risk

- Native Windows + WezTerm + rmux 前台点击仍必须由人工 transcript 或真实 GUI evidence 证明；自动化不能替代 core pass。
- `CCB_AGENT_SIDEBAR_MOUSE_PROBE` 依赖 ccbd/namespace 父进程环境；QA 必须重启对应父进程或证明 respawn 继承了 env。
- 如果 `send-keys -M` 被证据证明不能稳定到达 crossterm，本 feature 需要回 design 修订 foreground interaction policy，而不是继续扩大 Rust hit-test 修复。

## 7. Verdict

- Status: passed
- Next: epic child batch 可返回 `cs-epic`；继续处理下一个 split child design，当前 feature 不进入实现。

## 8. Focused Closure

- Closed findings: FDR-001, FDR-002, FDR-003, FDR-004, FDR-005, FDR-006, FDR-007, FDR-008
- Attributed delta: design/checklist/items.yaml/goal-state/goal-feature/roadmap 中的 non-pass JSON validator、probe env 传播、config UI failure 可见性、fallback `send-keys c` 范围、S3 matrix 映射、goal projection、canonical owner、roadmap 历史状态文案。
- Verification: checklist YAML validate passed；roadmap YAML parse passed；`codestable-workflow-next.py feature --epic-child-batch` passed；`codestable-workflow-next.py epic` passed；git diff whitespace check passed；round 3 independent reviewer reported no blocking/important。
- Classification: FDR-001 到 FDR-007 改变验收语义、owner 恢复或 goal projection，已分别通过第二/第三轮完整独立复审；FDR-008 是文案澄清，无行为、公开契约、架构边界、验收语义或范围变化。
