---
doc_type: feature-design-review
feature: 2026-07-31-herdr-user-surfaces-parity
status: passed
review_state: passed
review_reason: ""
reviewer_id: "019fb939-b530-7641-aa3b-e46c827497ac"
reviewed: 2026-08-01
round: 3
---

# herdr-user-surfaces-parity feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-31-herdr-user-surfaces-parity/herdr-user-surfaces-parity-design.md`
- Checklist: `.codestable/features/2026-07-31-herdr-user-surfaces-parity/herdr-user-surfaces-parity-checklist.yaml`
- Intent / brainstorm: none
- Requirement: `.codestable/requirements/native-windows-ccb-via-herdr.md`
- Roadmap: `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-roadmap.md`
- Roadmap items: `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml`
- Related docs: `.codestable/attention.md`
- Code facts checked: `lib/cli/services/start_foreground.py`、`lib/mobile_gateway/terminal.py`、`lib/mobile_gateway/service.py`、`lib/cli/services/config_ui.py`、`lib/cli/services/doctor.py`、`lib/cli/render_runtime/ops_views_doctor.py`、`lib/ccbd/project_view/service.py`、`lib/ccbd/handlers/ping_runtime/payloads.py`、`lib/cli/services/ping.py`、`lib/cli/services/ps.py`、`lib/cli/services/layout_status.py`、`lib/cli/render_runtime/ops_views_basic.py`、`lib/cli/services/diagnostics_runtime/bundle.py`、`lib/cli/services/diagnostics_runtime/sources.py`

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: round 1 `019fb720-5c6f-7960-801c-e808aa50eb50` changes-requested；round 2 `019fb727-8ae7-7093-832a-69e7d6668faa` changes-requested；requirement update 后 round 3 `019fb939-b530-7641-aa3b-e46c827497ac` changes-requested。
- Raw output: round 3 确认设计主体覆盖 foreground attach、Mobile terminal、Config UI、doctor、ping、mounted、project view、diagnostics bundle、Mobile/Config supported hard gate、Herdr no tmux fallback、ProjectView/ping 一致事实源、provider completion authority 和 upstream admission；唯一 blocking 是 `CMD-007` 声明与实际扫描范围不一致，nit 是 design CMD-008 漏列 Config UI。
- Merge policy: 已逐条核验 reviewer finding 与 design/checklist/roadmap/code 事实；只合并有仓库事实支撑的结论。
- Gate effect: round 3 blocking 已通过 focused closure 关闭；design-review gate passed。

## 2. Design Summary

- Goal: 将 Herdr backend evidence 安全投影到 foreground attach、Mobile terminal、Config UI、doctor、ping、mounted、project view 和 diagnostics bundle。
- Key contracts: `HerdrSurfaceProjection` 包含 backend identity、capability status、support tier projection/source、beta/blocking gaps、degraded next action 和 redacted evidence refs；Mobile terminal 与 Config UI 是 supported hard gate；Herdr 不伪装成 tmux socket/session/%pane。
- Steps: 8 个 pending steps，覆盖 upstream admission、ProjectView/ping、foreground、Mobile terminal、doctor/mounted/diagnostics、Config UI、regression/scope guard、Native Windows transcript。
- Checks: 9 个 checks，覆盖 projection consistency、redaction、foreground/Mobile/Config UI、tmux/rmux regression、scope guard 和 manual transcript。
- Baseline / validation: CMD-003 是 upstream acceptance dependency gate；CMD-007 覆盖 provider completion、package/release/update/installer/support final claim、redaction、Herdr socket schema/client owner；CMD-008 manual transcript 包含 Config UI。

## 3. Findings

### blocking

none

### important

none

### nit

none

### suggestion

- 后续可以把 CMD-007 的长内联 Python 沉淀为只读工具脚本，降低 quoting 和路径覆盖漂移风险。当前 design 阶段不新增工具脚本。

### learning

- Mobile terminal 当前 websocket/history/message 三条路径分别通过 tmux attach target、history target、pane message target 运行；设计阶段明确 operation adapter seam 可以避免在 `MobileGatewayService` 中散落 Herdr 特例。
- mounted 在当前仓库不是独立 daemon 入口；设计已收紧为 ping / ps / layout status / render 的 mounted state projection。
- public surface parity 不能只显示 backend available，必须同时显示 blocked/partial reason、support tier projection source 和下一步。

### praise

- design 对 Herdr 不伪装 tmux、raw restore token 不进入 public payload、Herdr agent state 不作为 completion authority 的边界清晰。
- Mobile terminal 与 Config UI 都被列为 supported hard gate，符合 updated requirement 的严格 supported 口径。
- CMD-007 focused closure 后覆盖顶层 package/install/README/docs、docs/bin/scripts/lib/test staged/unstaged/untracked 内容，同时排除 `.codestable` 文档自身。

## 4. User Review Focus

- 用户需要重点拍板：本 feature 只做 user surfaces 的 evidence projection，不做 package/release/update/installer/support final claim；完整 public workflow evidence key set 由后续 validation/support feature 承担。
- implement 需要重点遵守：ProjectView/ping 是事实源；doctor/mounted/diagnostics/Config UI 只读消费同一 projection；Mobile terminal 三条操作路径走 backend-neutral adapter；public payload redaction 必须覆盖 restore token、provider secret 和 terminal buffer 全量。
- code review / QA / acceptance 需要重点复核：support tier projection/source 是否在各 surface 一致，diagnostics bundle 是否只包含 redacted source artifact，Herdr blocked/partial 状态是否有 actionable next action，tmux/rmux regression 是否不退化。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | AC-001 到 AC-012 均映射到 S1 到 S8、证据类型和命令 / 动作，CMD-008 已包含 Config UI。 | none |
| DoD Contract | pass | E/C | DOD-IMPL-006 约束 provider completion、package/release/update/installer/support final claim、Herdr socket schema/client owner；CMD-007 已覆盖对应 paths/text。 | none |
| Steps and checks traceability | pass | E | checklist steps/checks 均为 pending，source 可回到 design AC / DOD / step。 | none |
| Roadmap contract compliance | pass | E/C | roadmap item 要求 beta gaps、degraded next action、support tier；design/checklist 输出 projection/source 且不宣称 supported。 | none |
| Module interface design | pass | C | ProjectView/ping source、Mobile operation adapter、foreground attach、Config UI readonly、diagnostics bundle source 均有挂载点。 | implementation 复核 seam 是否落到小 helper / adapter。 |
| Validation and artifacts | pass | E/C | design/checklist/items YAML passed；CMD-007 在 PowerShell 下执行通过，且包含顶层 forbidden files 与 support claim 检测。 | none |

Summary: E=4, C=2, H=0, H-only core checks=none。

## 6. Residual Risk

- upstream `provider-runtime-on-herdr` 与 `herdr-bounded-recovery-boundary` 当前只有 design-review passed；实现前必须严格执行 `CMD-003`，缺 acceptance evidence 时 dependency-blocked。
- diagnostics bundle 当前代码会 stage 多类 runtime/log/snapshot/provider-state 文件；实现阶段必须用真实 bundle fixture 证明 raw restore token、provider secret、terminal buffer 全量不会进入 tarball。
- `ps` / `layout_status` 现有代码主要读 local state 和 namespace/runtime state；实现时必须确认 Herdr projection 不只出现在 ping/doctor。

## 7. Verdict

- Status: passed
- Next: 回到 `cs-epic` child design batch loop；本 child design 保持 `draft`，等待 epic 的所有 child design 统一确认。

## 8. Focused Closure

- Closed findings: round 1 surface/projection findings；round 2 `CMD-007` PowerShell quoting；round 3 `FDR-001` CMD-007 覆盖缺口、`FDR-002` design CMD-008 漏 Config UI。
- Attributed delta: design/checklist 将 package/release/update/installer/support final claim 和 Herdr socket schema/client owner 纳入 scope guard；`CMD-007` 改为基于全部 changed/untracked paths 检查 forbidden files，并扫描顶层/docs/bin/scripts/lib/test 的 staged/unstaged/untracked 内容；support claim regex 扩展到 `support_tier: supported`、`support_tier = "supported"` 和明文 supported claim；design CMD-008 补 Config UI。
- Verification: `validate-yaml.py` 校验 design、checklist、roadmap items 均通过；`git diff --check` 通过；从 checklist 读取并执行 CMD-007，在 PowerShell 下通过；本地断言确认 CMD-007 包含 `bad=sorted(p for p in paths if p in forbidden_files`、`support_tier\\s*[:=]`、`README.md`、`install.ps1`、`docs`。
- Classification: 本轮 closure 只修复 validation guard 覆盖范围与 manual command 文案，不改变 user surface 行为、公开契约、架构边界、验收语义或实现范围。
