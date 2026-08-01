---
doc_type: roadmap-goal-plan
roadmap: windows-rmux-ux-parity-hardening
status: awaiting-authorization
created: 2026-07-26
---

# windows-rmux-ux-parity-hardening Goal Plan

## 1. Scope

- Roadmap: `.codestable/roadmap/windows-rmux-ux-parity-hardening/windows-rmux-ux-parity-hardening-roadmap.md`
- Items: `.codestable/roadmap/windows-rmux-ux-parity-hardening/windows-rmux-ux-parity-hardening-items.yaml`
- Goal state: `.codestable/roadmap/windows-rmux-ux-parity-hardening/goal-state.yaml`
- Goal protocol: `.codestable/roadmap/windows-rmux-ux-parity-hardening/goal-protocol.md`
- Execution order: the topological order returned by `codestable-workflow-next.py epic`.

## 2. Feature Execution Order

1. `windows-rmux-wezterm-native-interaction-parity`：普通 pane 使用 WezTerm GUI-native 交互，sidebar 继续全接管；性质 mixed；依赖 none。
2. `windows-rmux-output-capture-parity`：建立 machine capture、provider completion、用户可见历史的 evidence contract；性质 mixed；依赖 `windows-rmux-wezterm-native-interaction-parity`。
3. `windows-rmux-pane-identity-layout-parity`：收口 pane identity/layout/binding 恢复证据与最小 drift 修复；性质 mixed；依赖 `windows-rmux-wezterm-native-interaction-parity`。
4. `windows-rmux-visual-no-popup-parity`：恢复或替代视觉状态并证明 Windows/rmux no-popup；性质 mixed；依赖 `windows-rmux-wezterm-native-interaction-parity`。
5. `windows-rmux-lifecycle-recovery-ux-parity`：覆盖 reattach、terminal close、kill cleanup、pane/provider/rmux daemon crash 的 UX recovery evidence；性质 mixed；依赖 `windows-rmux-pane-identity-layout-parity`、`windows-rmux-output-capture-parity`。
6. `windows-rmux-supportability-parity-contract`：聚合 5 个 UX dimension 和 base packaging projection，输出 doctor/docs/support tier 一致契约；性质 non-functional；依赖前 5 项全部 done。

## 3. Roadmap Core Acceptance Paths

- Native Windows + WezTerm + rmux foreground interaction：普通 pane 左键、拖选、右键、滚轮不被 CCB/rmux 劫持，sidebar 控件仍可用。
- Rmux output/capture parity：machine capture、provider completion 和用户可见 history 三条 evidence lane 各自有证据，不互相替代。
- Pane identity/layout parity：pane id/index canonicalization、layout 重建和 agent-pane binding 恢复可由 evidence JSON 与 targeted tests 证明。
- Visual no-popup：Windows/rmux 状态栏、边框、标题相关命令不得产生 Git Bash 或 console popup；动态 restore 只能在 no-popup probe 通过后启用。
- Lifecycle recovery UX：reattach、terminal_closed、kill_cleanup、pane_crash、provider_crash、rmux_daemon_crash 要么 pass，要么有 degraded diagnostics、residue report 和 next action。
- Supportability projection：`rmux_supportability` 聚合 upstream evidence，唯一对外 tier 字段为 `support_tier`，不得绕过 base packaging owner 边界。

## 4. Assumptions

- `windows-rmux-native-backend` 已 accepted 的 base backend、full-chain smoke、validation matrix 和 packaging/docs evidence 可作为 baseline ref，但不能替代本 roadmap 的 UX parity evidence。
- 当前 host 为 native Windows；GUI/WezTerm/rmux live 证据可能需要 manual transcript 或 live lane，缺环境时只能记录 partial/blocked，不能声明 full pass。
- Provider credential/quota/auth failure 不等于 rmux/system failure，必须单独归因。
- Implementation 前的依赖 gate 严格要求上游 roadmap item `done`；design-review passed 只满足 child batch design admission。

## 5. Top Risks

1. 把 base backend “能跑通”误当作 UX parity。缓解：每个 feature 必须产出 `evidence/windows-rmux-ux-parity-evidence.json`，并写明 baseline/delta。
2. GUI/live evidence 不可用时误报 supported。缓解：缺 native Windows + WezTerm + rmux live evidence 时只能 partial/blocked，supportability 聚合 fail closed。
3. supportability 越权修改 packaging/npm/release owner contract。缓解：supportability 只做 UX overlay，base projection 仍由 `rmux-packaging-docs-contracts` 拥有。

## 6. Mandatory Validation Commands

Feature-level commands are defined in each checklist and mirrored under `goal-features/*.md`. Final aggregate commands:

- `python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-rmux-ux-parity-hardening/windows-rmux-ux-parity-hardening-items.yaml"`
- `python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-rmux-ux-parity-hardening/goal-state.yaml" --yaml-only`
- `python -m pytest -q test/test_v2_tmux_ui.py`
- `python -m pytest -q test/test_windows_rmux_output_capture_parity_evidence.py test/test_windows_rmux_pane_identity_layout_parity.py test/test_windows_rmux_visual_no_popup_parity.py test/test_windows_rmux_lifecycle_recovery_ux_parity.py test/test_windows_rmux_supportability_parity_contract.py`
- `python -m pytest -q test/test_rmux_send_capture_logging.py test/test_rmux_completion_capture_fixtures.py test/test_rmux_backend_core.py test/test_rmux_windows_validation_matrix.py`
- `python -m pytest -q test/test_rmux_packaging_docs_contracts.py test/test_cli_doctor_rmux_packaging.py test/test_ccbd_diagnostics_bundle_rmux.py test/test_rmux_docs_consistency_gate.py`
- `python "C:/Users/Administrator/.codex/plugins/cache/codestable/codestable/1.0.4/skills/cs-onboard/tools/codestable-goal-consistency-gate.py" --roadmap ".codestable/roadmap/windows-rmux-ux-parity-hardening"`

## 7. Policies

- DoD Policy: each feature must finish implementation, independent code review, QA, acceptance, checklist steps/checks, UX evidence JSON and roadmap writeback before it is `accepted`.
- Gate Policy: scope-gate, dod-runner, evidence-pack, review/QA/acceptance gates and final consistency gate must pass; missing CodeStable tools require runtime repair, not same-name shim creation.
- Provider Policy: archguard/meta-cc/provider helpers unavailable is a warning/fallback, not automatic failure; review, QA or audit must explain any provider warning that touches core evidence.
- Verification Recovery: missing pytest/npm/cargo/runner dependencies may be restored through normal dependency/config paths only; do not fake validation output.
- Evidence Recovery: live/manual GUI gaps must be recorded as partial/blocked with reason and next action; H-only or manual-only core checks require explicit evidence treatment in QA/audit.

## 8. Final Audit Inputs

- `goal-audit.md` and optional `goal-evidence-summary.md`.
- `codestable-goal-consistency-gate.py --roadmap .codestable/roadmap/windows-rmux-ux-parity-hardening`.
- Six feature review / QA / acceptance reports, evidence packs, gate JSON and checklist statuses.
- All six `evidence/windows-rmux-ux-parity-evidence.json` files.
- Provider warnings, E/C/H summary, manual/live evidence dispositions and supportability projection.

## 9. Authorizations

- Goal acceptance authorization: pending, ref `approval-report.md#goal-acceptance`.
- Automatic per-feature scoped commit authorization: pending, ref `approval-report.md#goal-commits`.
- This package does not authorize remote push, merge, publish, release, deploy, promotion or production cutover.
