---
doc_type: feature-design-review
feature: 2026-07-20-rmux-daemon-ownership-boundary
status: passed
review_state: passed
review_reason: ""
reviewer_id: "019f7c29-2e22-7db2-9246-b220ef40bb6c"
reviewed: 2026-07-20
round: 2
---

# rmux-daemon-ownership-boundary feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-20-rmux-daemon-ownership-boundary/rmux-daemon-ownership-boundary-design.md`
- Checklist: `.codestable/features/2026-07-20-rmux-daemon-ownership-boundary/rmux-daemon-ownership-boundary-checklist.yaml`
- Roadmap: `.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-roadmap.md` §4.5、`.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml`
- Related designs: `.codestable/features/2026-07-19-mux-backend-contract/mux-backend-contract-design.md`、`.codestable/features/2026-07-19-windows-namespace-ipc-schema/windows-namespace-ipc-schema-design.md`、`.codestable/features/2026-07-20-windows-job-object-runtime-evidence/windows-job-object-runtime-evidence-design.md`
- Code facts checked: `lib/ccbd/services/ownership.py`、`lib/ccbd/keeper_runtime/loop.py`、`lib/ccbd/start_flow.py`、`lib/cli/services/tmux_project_cleanup.py`、`lib/provider_runtime/health.py`、`lib/ccbd/services/health_assessment/provider_pane.py`、`lib/ccbd/services/health_monitor_runtime/provider.py`

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: subagent `019f7c29-2e22-7db2-9246-b220ef40bb6c`
- Raw output: round 1 提出 2 个 blocking、2 个 important、2 个 nit；round 2 focused closure 判定全部 closed，remaining findings 为 none，verdict 为 `passed`。
- Merge policy: 主 agent 已按 reviewer findings 修订 cleanup plan 形状、start_result 验收、daemon evidence 命名、version/capability diagnostics 和文案 typo。
- Gate effect: independent review completed and merge verified；允许交回 `cs-epic` child design batch。

## 2. Design Summary

- Goal: 定义 Rmux daemon discovery/start/health/crash/cleanup 的 ownership 边界和 diagnostics evidence。
- Key contracts: `RmuxDaemonRef`、`RmuxDaemonEvidence`、`RmuxCleanupPlan`；`daemon_process_evidence` 仅描述 Rmux daemon observation，不复用 provider `ProcessRef`。
- Authority boundary: ccbd lease / lifecycle / namespace state 仍是 project authority；Rmux daemon 只能是 backend evidence。
- Cleanup policy: shared daemon 默认 `leave_running`，per-project cleanup 只清 namespace / project scope，daemon-wide cleanup 只在 explicit force 下允许。
- Diagnostics: `backend_daemon_*` 字段覆盖 discovery/start/health/crash/cleanup/version/capability，不覆盖 ccbd daemon / namespace / tmux placement 字段。

## 3. Findings

### blocking

none

### important

none

### nit

none

### learning

- `daemon_process_evidence` 这个名字比 `process_ref` 更能保住边界，不会和 provider job evidence 混淆。
- shared daemon 的默认安全策略必须显式写成 `leave_running`，否则 cleanup plan 容易被执行层误解。
- start_result 需要单独成为 evidence 节点，不能只靠 discovery/health 推断。

## 4. User Review Focus

- 实现时先守住 cleanup plan 的顺序和默认 `leave_running` 语义，再谈 daemon-wide shutdown。
- start_result success/failure 都要能证明 ccbd owner 不变。
- diagnostics projection 统一使用 `backend_daemon_*` 前缀，不引入新的 `backend_daemon_ref` 聚合 key。
- `daemon_process_evidence` 只能做诊断，不能进入 provider kill eligibility。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Roadmap §4.5 alignment | pass | E/C | discovery/start/health/crash/cleanup boundary 均被覆盖 | none |
| Authority boundary | pass | C | ccbd authority 与 Rmux daemon evidence 分离清楚 | none |
| Cleanup plan executable shape | pass | C | `RmuxCleanupPlan` 现在包含 scope、targets、daemon_action、force、ordered_steps、status、diagnostics | none |
| Start result coverage | pass | C | checklist 已覆盖 start_result 成功 / 失败 / owner 不变 | none |
| Diagnostics projection | pass | C | `backend_daemon_*` 字段与 version/capability status 已补齐 | none |
| YAML validation | pass | E | checklist / roadmap items 校验通过 | none |

Summary: E=2, C=4, H=0, H-only core checks=none。

## 6. Residual Risk

- 后续实现仍需确保 backend core 不把 daemon evidence 当作 authority 或 process kill eligibility。
- shared daemon cleanup 的执行层必须严格遵守 plan ordering，否则会绕过默认 `leave_running`。

## 7. Verdict

- Status: passed
- Next: 交回 `cs-epic` child design batch；本 feature design 保持 `draft`，等待所有子 feature design-review passed 后统一 owner 确认。

## 8. Focused Closure

- Closed findings: blocking/important/nit 全部关闭
- Attributed delta: `.codestable/features/2026-07-20-rmux-daemon-ownership-boundary/rmux-daemon-ownership-boundary-design.md`、`.codestable/features/2026-07-20-rmux-daemon-ownership-boundary/rmux-daemon-ownership-boundary-checklist.yaml`
- Verification: independent reviewer `019f7c29-2e22-7db2-9246-b220ef40bb6c` confirmed remaining findings none；YAML 校验通过；workflow-next 可恢复到当前 child 仅缺 design-review 的状态，写入本文件后应继续 batch。
- Classification: 本次 closure 只收紧设计契约、验证命令和兼容边界，不改变生产代码。
