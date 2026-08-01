---
doc_type: feature-design-review
feature: 2026-07-31-ccbd-herdr-namespace-lifecycle
status: passed
review_state: passed
review_reason: ""
reviewer_id: 019fb91b-f137-7bb3-943b-19df389bbc42
reviewed: 2026-08-01
round: 5
---

# ccbd-herdr-namespace-lifecycle feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-31-ccbd-herdr-namespace-lifecycle/ccbd-herdr-namespace-lifecycle-design.md`
- Checklist: `.codestable/features/2026-07-31-ccbd-herdr-namespace-lifecycle/ccbd-herdr-namespace-lifecycle-checklist.yaml`
- Intent / brainstorm: none
- Roadmap: `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-roadmap.md`
- Roadmap items: `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml`
- Related docs: `.codestable/attention.md`
- Code facts checked: `lib/ccbd/project_view/service.py`, `lib/ccbd/handlers/project_restart.py`, `lib/ccbd/services/project_namespace_state_runtime/models.py`, `lib/ccbd/services/project_namespace_runtime/backend.py`, `lib/ccbd/services/project_namespace_runtime/additive_patch_apply.py`, `additive_patch_windows.py`, `additive_patch_agents.py`, `move_patch_agents.py`, `remove_patch_agents.py`, `agent_window_reflow.py`

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: round 4 `019fb6d5-3c0e-7af1-b1f9-7c7656e276cb` changes-requested；round 5 `019fb91b-f137-7bb3-943b-19df389bbc42` passed.
- Raw output: round 5 未发现 blocking / important；确认 scope 只覆盖 ccbd namespace lifecycle、layout/reflow、foreground attach、kill/restart/reload，public payload/project view/foreground/event/log 均受 redacted projection 约束，Herdr foreground attach fail closed 且不 fallback tmux，provider/recovery/doctor/support/Mobile/Config/release/install 边界均有 guard。
- Merge policy: 主线程逐条用 design/checklist/roadmap/code 事实核验；两个 important 已做 focused closure。
- Gate effect: independent review completed and merged; final verdict passed.

## 2. Design Summary

- Goal: 将 Herdr backend 接入 ccbd project namespace lifecycle、layout/reflow、foreground attach、kill、restart 和 reload，同时保持 ccbd 为 project authority。
- Key contracts: Herdr 不伪装为 `tmux-family`；internal namespace ref 可含 opaque restore token，public payload 只能输出 redacted projection；Herdr restart 在本 feature 下只返回 unsupported/deferred evidence，不实现 provider pane restart。
- Steps: 8 个稳定步骤 `S0` 到 `S7`，覆盖 admission、state/redaction、per-operation helper gate、layout/reflow、foreground attach、kill/reload/restart boundary、scope guard、regression/manual evidence。
- Checks: 14 条 pending checks，全部可追踪到 AC/DOD/CMD。
- Baseline / validation: checklist YAML、roadmap YAML、focused pytest、scope/content guard、Native Windows x64 foreground/manual transcript。

## 3. Findings

### blocking

none

### important

none

### nit

none

### suggestion

none

### learning

- reload patch 的真实执行面不只在 high-level reload handler，也包括 additive/move/remove/reflow 模块；design 已把这些模块纳入 AC-010 和 CMD-011。
- Herdr restart 与 provider pane restart 的边界必须显式 deferred，否则容易提前进入 `provider-runtime-on-herdr` 范围。

### praise

- design 将 project view、event/log redaction、reload primitive fail-closed、Windows manual transcript 全部纳入 core DoD。

## 4. User Review Focus

- 用户需要重点拍板：本 child 只保证 Herdr namespace lifecycle 与 foreground attach；Herdr provider pane restart 在本 feature 下返回 unsupported/deferred evidence。
- implement 需要重点遵守：S0 admission 未证明前置 V2/HerdrBackend/attach capability 落地时必须 dependency-blocked；public payload 必须走 redacted projection helper。
- code review / QA / acceptance 需要重点复核：reload patch 不得静默 skip 后 published/noop 成功；Native Windows x64 foreground/manual transcript 是本 feature acceptance 必需证据。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E,C | design AC-001..AC-013 与 checklist steps/checks/CMD 对齐 | none |
| DoD Contract | pass | E | design DOD-DESIGN/IMPL/REVIEW/QA/ACCEPT 与 Required Artifacts 完整 | none |
| Steps and checks traceability | pass | E | checklist steps 使用稳定 `id: S0..S7`，checks 指向 AC/DOD/CMD | none |
| Roadmap contract compliance | pass | E,C | roadmap Goal Coverage 要求 Windows foreground/manual，design AC-011/CMD-013/Required Artifacts 已纳入 | none |
| Module interface design | pass | E,C | per-operation V2 capability gate、foreground attach builder seam、restart unsupported/deferred surface 已写明 | none |
| Validation and artifacts | pass | E | CMD-001..CMD-013 与 evidence_required 覆盖 YAML、pytest、guards、manual transcript | none |

Summary: E=6, C=3, H=0, H-only core checks=none。

## 6. Residual Risk

- 当前仓库尚无 Herdr V2/HerdrBackend 真实实现面；implementation 必须先通过 S0 admission，不能只依据前置 design-review passed。
- log redaction 的最终安全性依赖实现阶段统一 helper 和测试覆盖；design 已设 CMD-012 硬 gate。

## 7. Verdict

- Status: passed
- Next: 交回 `cs-epic` child batch loop，继续后续 workflow hook；本 feature design 仍保持 `draft`，等待 epic 统一确认。

## 8. Focused Closure

- Closed findings: round 4 FDR-001、FDR-002、nit traceability。
- Attributed delta:
  - design 删除“Native Windows 真机证据仍由后续 validation matrix 负责”的旧矛盾，改为本 feature 必须收集最小 foreground/manual transcript。
  - design/checklist 补 `build_project_restart_agent_handler()` 与 `build_project_restart_panes_handler()` 两条 restart public surface，要求 Herdr 下返回 unsupported/deferred evidence，不允许 scheduled path 静默丢证据。
  - checklist 将 tmux/rmux regression source 修为 AC-012，scope boundary source 修为 AC-013。
- Verification:
  - `validate-yaml.py --yaml-only` for checklist: passed。
  - `validate-yaml.py` for roadmap items: passed。
  - 本地核验 design/checklist 已含 AC-011、CMD-013、restart agent/panes handler、no scheduled silent success、AC-012/AC-013 traceability。
- Classification: 本 closure 只关闭独立 reviewer 指出的 stale contradiction 与 surface traceability；未新增实现范围，Herdr provider pane restart 仍明确留给后续 feature。
- Focused closure: round 5 nit 将术语表 `restore_token_present` 统一为 `namespace_restore_token_present`，不改变行为、公开契约、验收语义或范围。
