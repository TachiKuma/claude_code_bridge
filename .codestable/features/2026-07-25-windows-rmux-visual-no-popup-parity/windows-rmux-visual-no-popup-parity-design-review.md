---
doc_type: feature-design-review
feature: 2026-07-25-windows-rmux-visual-no-popup-parity
status: passed
review_state: passed
review_reason: ""
reviewer_id: "019f987d-1153-7973-a01b-15229f1107e5"
reviewed: 2026-07-25
round: 2
---

# windows-rmux-visual-no-popup-parity feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-25-windows-rmux-visual-no-popup-parity/windows-rmux-visual-no-popup-parity-design.md`
- Checklist: `.codestable/features/2026-07-25-windows-rmux-visual-no-popup-parity/windows-rmux-visual-no-popup-parity-checklist.yaml`
- Intent / brainstorm: `.codestable/features/2026-07-25-windows-rmux-visual-no-popup-parity/windows-rmux-visual-no-popup-parity-brainstorm.md`
- Roadmap: `.codestable/roadmap/windows-rmux-ux-parity-hardening/windows-rmux-ux-parity-hardening-roadmap.md`
- Related docs: `.codestable/issues/2026-07-24-windows-rmux-git-bash-popup/windows-rmux-git-bash-popup-fix-note.md`, `.codestable/features/2026-07-20-rmux-packaging-docs-contracts/rmux-packaging-docs-contracts-acceptance.md`
- Code facts checked: `lib/cli/services/tmux_ui_runtime/service.py`, `lib/ccbd/start_flow_runtime/service_tmux.py`, `lib/cli/services/tmux_ui_runtime/activation.py`, `config/ccb-tmux-on.sh`, `test/test_v2_tmux_ui.py`

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: `019f987d-1153-7973-a01b-15229f1107e5`
- Raw output: round 1 reported two blocking, one important, one nit, one suggestion；round 2 reported no blocking/important and `verdict: passed`。
- Merge policy: 已逐条核验，并把成立 finding 合并；round 2 确认 FDR-001 到 FDR-004 和 S7 suggestion 已关闭。
- Gate effect: independent review completed，允许本地合并为 passed。

## 2. Design Summary

- Goal: 以 evidence-gated dynamic restore 方式恢复或替代 Windows/rmux 动态视觉状态，保留 static fallback fail-closed。
- Key contracts: `WindowsRmuxVisualCommandPolicy`、`WindowsRmuxPopupProbeCase`、`VisualNoPopupReport` 和 roadmap §4.1 `windows-rmux-ux-parity-evidence.json`。
- Steps: 8 步，风险热点是真实 shell activation 入口、policy enum 不得漂移、per-surface owner/source 归因、live no-popup 证据不能用 headless 结果替代。
- Checks: 10 条，覆盖 brainstorm admission、static fallback baseline、activation audit、per-surface candidate contract、dynamic gate、live/manual evidence、scope guard。
- Baseline / validation: 复用 Git Bash popup fix-note、当前 `_shell_commands_supported()` static fallback、existing no-shell test，以及 `rmux-packaging-docs-contracts` accepted support baseline。

## 3. Findings

### blocking

- [x] FDR-001 `.codestable/features/2026-07-25-windows-rmux-visual-no-popup-parity/windows-rmux-visual-no-popup-parity-design.md#2.2` static fallback audit 漏掉真实 UI activation 入口。
  - Evidence: round 1 design 主要覆盖 `apply_project_tmux_ui()`；但 `lib/ccbd/start_flow_runtime/service_tmux.py::tmux_layout_for_start()` 会调用 `set_tmux_ui_active_fn(True)`，`lib/cli/services/tmux_ui_runtime/activation.py::set_tmux_ui_active()` 会运行 `config/ccb-tmux-on.sh`。该 shell 脚本当前仍有 `#(${status_script} modern)` 和 `after-select-pane run-shell -b ... ccb-border.sh` 路径。
  - Impact: implementation 可能只让 Python project UI no-popup，通过 `ccbd start` 真实 activation 时仍复现 Git Bash / console popup。
  - Expected fix scope: design/checklist 必须把 `set_tmux_ui_active()` / `ccb-tmux-on.sh` 纳入 baseline、static audit、验收场景、DoD 和命令入口。
  - Closure: design 成功标准、baseline、§2.2 流程约束、§2.3 挂载点、S3、AC-002、DOD-IMPL-003、CMD-004 和 checklist S3 均已纳入真实 activation 入口；round 2 reviewer confirmed。

- [x] FDR-002 `.codestable/roadmap/windows-rmux-ux-parity-hardening/windows-rmux-ux-parity-hardening-roadmap.md#4.5` `popup_probe_status` enum 被扩展为 `blocked`，违反 roadmap 契约。
  - Evidence: roadmap §4.5 只允许 `popup_probe_status: Literal["pass", "failed", "not-run"]`。
  - Impact: supportability 或 diagnostics 消费 policy 时会遇到 roadmap 未定义状态，破坏跨 feature 共享协议。
  - Expected fix scope: 对外 `WindowsRmuxVisualCommandPolicy.popup_probe_status` 恢复为 roadmap enum；环境 blocked 用 UX evidence 的 `evidence_status/failure_class/residual_risks` 表达。
  - Closure: design §2.1 已将 policy enum 收敛为 `pass|failed|not-run`，并新增投影规则：环境 blocked 写入 roadmap §4.1 evidence，细粒度 `WindowsRmuxPopupProbeCase.verdict=blocked` 不污染对外 policy enum；round 2 reviewer confirmed。

### important

- [x] FDR-003 `.codestable/features/2026-07-25-windows-rmux-visual-no-popup-parity/windows-rmux-visual-no-popup-parity-design.md#2.1` `title` 与 `ccbd health` owner/source 不够深。
  - Evidence: round 1 design 未逐 surface 说明 current owner/source、现有执行路径、禁止路径和候选 no-popup execution。`git`、`health`、`pane_title_display`、`border`、`resize_hook` 的来源不同，误放到同一 status shell adapter 会复活 popup 风险或重复 owner。
  - Impact: implementation 容易把 title、health、border 都塞回 shell status/hook，绕开现有 pane option、lease/source 或 Python gate。
  - Expected fix scope: 增加 per-surface candidate contract，至少覆盖 current owner/source、existing execution path、forbidden path、candidate execution、artifact/probe requirement。
  - Closure: design §2.1 已新增 per-surface candidate contract，覆盖 `git`、`health`、`pane_title_display`、`border`、`resize_hook`；checklist 和 AC-009 已同步；round 2 reviewer confirmed。

### nit

- [x] FDR-004 `.codestable/features/2026-07-25-windows-rmux-visual-no-popup-parity/windows-rmux-visual-no-popup-parity-design.md#1` `rmux-packaging-docs-contracts` baseline 缺 canonical acceptance path。
  - Evidence: round 1 design 提到 packaging/docs support baseline，但未给出 accepted artifact 的 canonical path。
  - Closure: design §1 Baseline reuse / delta 已补 `.codestable/features/2026-07-20-rmux-packaging-docs-contracts/rmux-packaging-docs-contracts-acceptance.md`。

### suggestion

- [x] FDR-005 `S7` 可拆为 restore-if-probe-passed 与 final scope/validation guard。
  - Evidence: 单步同时负责动态恢复和范围收口，容易把 static-only pass 误判为缺少 production dynamic restore。
  - Closure: design §2.4 和 checklist 已拆为 S7 `restore-if-probe-passed` 与 S8 `final scope / validation guard`。

### learning

- `service.py::_shell_commands_supported()` 已对 Windows + `backend_impl=rmux` fail closed；但 `ccbd start` 路径通过 shell activation 脚本进入 UI activation，这个入口必须同等纳入 no-popup gate。
- roadmap §4.1 与 §4.5 的职责分层有效：policy enum 保持窄状态，环境不可运行/blocked 由 UX evidence 的 status、failure_class 和 residual_risks 表达。

### praise

- design 保持 evidence-first：不默认恢复 shell hook，也不默认引入 Windows hidden process renderer。
- 挂载点和 scope guard 明确限制在 visual/no-popup parity，不污染 capture、identity、lifecycle 或 support tier。

## 4. User Review Focus

- 用户需要重点拍板：接受 static fallback 是安全 baseline；动态 Git branch、health、title、border/status 只有 probe pass 后才恢复。
- implement 需要重点遵守：真实 activation 入口必须和 Python project UI 一样 fail closed；`popup_probe_status` 不得扩展 roadmap enum。
- code review / QA / acceptance 需要重点复核：native Windows + WezTerm no-popup 证据不可用时不能写 full pass；任何 enabled dynamic candidate 必须有 no-popup probe pass artifact。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | AC-001 到 AC-010 覆盖 static audit、activation audit、policy schema、dynamic gate、popup probe、UX evidence 和 scope guard；round 2 reviewer confirmed | none |
| DoD Contract | pass | E | DOD-IMPL-001 到 DOD-IMPL-009 与 CMD-003/CMD-004/CMD-005/CMD-006 覆盖核心 evidence、activation、enum 和 scope guard | none |
| Steps and checks traceability | pass | E | checklist S1-S8 与 10 条 checks 可追溯到 design §2/§3；S3、S4、S7、S8 已按 findings 修订 | none |
| Roadmap contract compliance | pass | E/C | design §2.1 投影 roadmap §4.1 与 §4.5，`popup_probe_status` 严格保持 `pass|failed|not-run` | none |
| Module interface design | pass | C | visual command policy / popup probe report 是 evidence seam；production dynamic restore 只在 probe pass 后最小启用 | implementation 保持 hidden execution owner 单一 |
| Validation and artifacts | pass | E/C | Required Artifacts、feature evidence path、schema/policy tests、activation transcript、manual observation 和 scope guard 已列出 | implementation 创建真实测试与 evidence artifact |

Summary: E=4, C=2, H=0, H-only core checks=none。

## 6. Residual Risk

- `config/ccb-tmux-on.sh` 当前仍是有风险入口；本 design 已把它转为 implementation 必须关闭或审计的核心验收项。
- native Windows + WezTerm + rmux no-popup 仍依赖 live/manual evidence；QA/acceptance 不能用 skipped 或 headless 结果写 full pass。
- roadmap §7 仍保留 `rmux-packaging-docs-contracts` 进行中的历史观察措辞；不阻塞本 feature design，acceptance 摘要应以 canonical acceptance artifact 为准。

## 7. Verdict

- Status: passed
- Next: epic child batch 可返回 `cs-epic`，继续下一个 child feature gate。

## 8. Focused Closure

- Closed findings: FDR-001, FDR-002, FDR-003, FDR-004, FDR-005
- Attributed delta: design/checklist 的 activation static audit、policy enum 投影规则、per-surface candidate contract、packaging acceptance path、restore-if-probe-passed 与 final scope guard。
- Verification: checklist YAML validate passed；items YAML validate passed；round 2 independent reviewer reported no blocking/important and `verdict: passed`。
- Classification: FDR-001 到 FDR-003 的修订改变 evidence/roadmap contract，已通过第二轮完整独立复审；FDR-004 和 FDR-005 是基线引用与步骤清晰度修订。最终 verdict 为 passed。
