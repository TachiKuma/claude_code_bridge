---
doc_type: feature-design-review
feature: 2026-07-31-herdr-user-surfaces-parity
status: passed
review_state: passed
review_reason: ""
reviewer_id: "019fb727-8ae7-7093-832a-69e7d6668faa"
reviewed: 2026-07-31
round: 2
---

# herdr-user-surfaces-parity feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-31-herdr-user-surfaces-parity/herdr-user-surfaces-parity-design.md`
- Checklist: `.codestable/features/2026-07-31-herdr-user-surfaces-parity/herdr-user-surfaces-parity-checklist.yaml`
- Intent / brainstorm: none
- Roadmap: `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-roadmap.md`
- Roadmap items: `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml`
- Related docs: `.codestable/attention.md`
- Code facts checked: `lib/cli/services/start_foreground.py`, `lib/mobile_gateway/terminal.py`, `lib/mobile_gateway/service.py`, `lib/cli/services/config_ui.py`, `lib/cli/services/doctor.py`, `lib/cli/render_runtime/ops_views_doctor.py`, `lib/ccbd/project_view/service.py`, `lib/ccbd/handlers/ping_runtime/payloads.py`, `lib/cli/services/ping.py`, `lib/cli/services/ps.py`, `lib/cli/services/layout_status.py`, `lib/cli/render_runtime/ops_views_basic.py`, `lib/cli/services/diagnostics_runtime/bundle.py`, `lib/cli/services/diagnostics_runtime/sources.py`

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: `019fb720-5c6f-7960-801c-e808aa50eb50` round 1, `019fb727-8ae7-7093-832a-69e7d6668faa` round 2
- Raw output: round 1 requested changes for support tier projection, mounted surface, Mobile terminal seam, diagnostics bundle source, and `PanePresentation` spelling; round 2 confirmed those substantive findings were covered and only found a PowerShell quoting block in `CMD-007`
- Merge policy: 已逐条核验并合并；round 2 后的 `CMD-007` quoting 与 DOD wording 为 focused closure
- Gate effect: round 2 reviewer completed；focused closure 本地验证通过后放行

## 2. Design Summary

- Goal: 将 Herdr backend evidence 安全投影到 foreground attach、Mobile terminal、Config UI、doctor、ping、mounted state、project view 和 diagnostics bundle。
- Key contracts: `HerdrSurfaceProjection` 包含 backend identity、capability status、support tier projection/source、beta/blocking gaps、degraded next action 和 redacted evidence refs；`TerminalTargetV2` 与 `TerminalOperationAdapter` 约束 Mobile websocket/history/message 不再依赖 tmux socket/session/%pane。
- Steps: 8 个 pending steps，已拆分 ProjectView/ping、foreground、Mobile terminal、support surfaces、Config UI、regression/scope guard 和 Native Windows transcript。
- Checks: 9 个 pending checks，覆盖 upstream admission、projection consistency、redaction、foreground/Mobile/Config UI、tmux/rmux regression、scope guard 和 manual transcript。
- Baseline / validation: checklist YAML、roadmap items YAML、PowerShell-safe `CMD-007` 已本地通过；`CMD-003` 在实现阶段应因 upstream acceptance 未完成而 dependency-blocked。

## 3. Findings

### blocking

none

### important

none

### nit

none

### suggestion

- S5 已按 reviewer 建议拆为 support surfaces 与 Config UI 两个 step；后续 implementation 保持同样原子边界即可。

### learning

- Mobile terminal 当前 websocket/history/message 三条路径分别通过 tmux attach target、history target、pane message target 运行；设计阶段明确 operation adapter seam 可以避免在 `MobileGatewayService` 中散落 Herdr 特例。
- mounted 在当前仓库不是独立 daemon 入口；设计已收紧为 ping / ps / layout status / render 的 mounted state projection。

### praise

- design 对 Herdr 不伪装 tmux、raw restore token 不进入 public payload、Herdr agent state 不作为 completion authority 的边界清晰。
- support tier 只作为 current projection/source 输出，明确不在本 feature 宣称 final `supported`。

## 4. User Review Focus

- 用户需要重点拍板：本 feature 只做 user surfaces 的 evidence projection，不做 release/package/support final claim；完整 public workflow evidence key set 由后续 validation/support feature 承担。
- implement 需要重点遵守：ProjectView/ping 是事实源；doctor/mounted/diagnostics/Config UI 只读消费同一 projection；Mobile terminal 三条操作路径走 backend-neutral adapter；public payload redaction 必须覆盖 restore token、provider secret 和 terminal buffer 全量。
- code review / QA / acceptance 需要重点复核：support tier projection/source 是否在各 surface 一致，diagnostics bundle 是否只包含 redacted source artifact，Herdr blocked/partial 状态是否有 actionable next action，tmux/rmux regression 是否不退化。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | AC-001 到 AC-012 均映射到 S1 到 S8、证据类型和命令 / 动作 | none |
| DoD Contract | pass | E | DOD-DESIGN、DOD-IMPL、DOD-REVIEW、DOD-QA、DOD-ACCEPT 与 Required Artifacts 完整 | none |
| Steps and checks traceability | pass | E | checklist steps/checks 均为 pending，source 可回到 design AC / DOD / step | none |
| Roadmap contract compliance | pass | C | roadmap item 要求 beta gaps、degraded next action、support tier；design/checklist 已补 support tier projection/source 且不宣称 supported | none |
| Module interface design | pass | C | ProjectView/ping source、Mobile operation adapter、foreground attach、Config UI readonly、diagnostics bundle source 均有挂载点 | implementation 复核 seam 是否落到小 helper / adapter |
| Validation and artifacts | pass | E | `validate-yaml` 两项通过，PowerShell-safe `CMD-007` 通过，manual CMD-008 保持 acceptance gate | none |

Summary: E=4, C=2, H=0, H-only core checks=none。

## 6. Residual Risk

- upstream `provider-runtime-on-herdr` 与 `herdr-bounded-recovery-boundary` 当前只有 design-review passed；实现前必须严格执行 `CMD-003`，缺 acceptance evidence 时 dependency-blocked。
- diagnostics bundle 的 redaction 需要 implementation/QA 实际打开 tar manifest 和 archive members 断言。
- `ps` / `layout_status` 现有代码主要读 local state 和 namespace/runtime state；实现时必须确认 Herdr projection 不只出现在 ping/doctor。

## 7. Verdict

- Status: passed
- Next: 在 epic child batch 中交回 `cs-epic`；不对单个 child 触发用户确认，不进入 implementation。

## 8. Focused Closure

- Closed findings: round 2 FDR-001 `CMD-007` PowerShell quoting；nit DOD-IMPL-002 source wording。
- Attributed delta: 仅修改 design/checklist 中 `CMD-007` inline command quoting，并把 DOD-IMPL-002 文案从 `support tier projection` 补为 `support tier projection/source`。
- Verification:
  - `$env:PYTHONDONTWRITEBYTECODE='1'; python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-31-herdr-user-surfaces-parity/herdr-user-surfaces-parity-checklist.yaml" --yaml-only` passed
  - `$env:PYTHONDONTWRITEBYTECODE='1'; python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml"` passed
  - `python -c 'import subprocess, re; ... assert not forbidden.search(text)'` passed in PowerShell
- Classification: focused closure 只改变 shell quoting 和等价文案，不改变行为、公开契约、架构边界、验收语义或范围。
