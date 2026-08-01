---
doc_type: feature-design-review
feature: 2026-07-20-ccbd-rmux-namespace-lifecycle
status: passed
review_state: passed
review_reason: ""
reviewer_id: "019f7cb1-5984-78d3-ba17-fdcab23fc44d"
reviewed: 2026-07-20
round: 1
---

# ccbd-rmux-namespace-lifecycle feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-20-ccbd-rmux-namespace-lifecycle/ccbd-rmux-namespace-lifecycle-design.md`
- Checklist: `.codestable/features/2026-07-20-ccbd-rmux-namespace-lifecycle/ccbd-rmux-namespace-lifecycle-checklist.yaml`
- Intent / brainstorm: none
- Roadmap: `.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-roadmap.md`、`.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml`
- Related docs: roadmap §4.1 / §4.5 / §4.6 / §4.9；前序 Rmux backend、namespace IPC、provider runtime、daemon ownership、ccbd TCP transport child designs
- Code facts checked:
  - `lib/ccbd/services/project_namespace_runtime/controller.py`
  - `lib/ccbd/services/project_namespace_runtime/backend.py`
  - `lib/ccbd/services/project_namespace_runtime/ensure_context.py`
  - `lib/ccbd/services/project_namespace_runtime/ensure.py`
  - `lib/ccbd/services/project_namespace_runtime/destroy.py`
  - `lib/ccbd/services/project_namespace_runtime/models.py`
  - `lib/ccbd/services/project_namespace_runtime/records.py`
  - `lib/cli/services/start_foreground.py`
  - `lib/cli/services/kill.py`
  - `lib/ccbd/project_view/service.py`
  - `lib/ccbd/services/health_assessment/tmux_runtime/namespace.py`
  - `lib/ccbd/services/project_namespace_runtime/slot_replacement.py`
  - `lib/ccbd/start_flow_runtime/service_tmux.py`

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: `019f7cb1-5984-78d3-ba17-fdcab23fc44d`
- Raw output: 首轮 `changes-requested`，提出 3 个 important；两轮 focused closure 后 verdict `passed`
- Merge policy: 主 agent 已核验 roadmap、代码事实和 reviewer findings，修订 design/checklist 后由同一 reviewer 做 focused closure
- Gate effect: 独立 reviewer completed + closure verified；允许定稿 `passed`

## 2. Design Summary

- Goal: 将 RmuxBackend 接入 `ccbd` project namespace ensure、layout projection、foreground attach 和 `ccb kill`，形成 native Windows 的第一条用户可见 Rmux namespace 闭环。
- Key contracts: namespace state canonical-first；legacy tmux aliases 只兼容；ensure/reflow/kill 通过 ProjectNamespaceBackend；foreground attach 通过 MuxBackend / NamespaceLifecycle attach 或前序批准 adapter；kill phase 保持 remote stop、local prepare、kill namespace、daemon diagnostics、final cleanup 的阶段语义。
- Steps: 9 个步骤，覆盖 namespace_ref state bridge、backend factory、ensure/reflow/layout projection、foreground attach、kill phase、cross-cutting readers、diagnostics、Rmux focused smoke、scope guard。
- Checks: 8 项检查，覆盖 canonical state、backend factory、layout projection、attach seam、selection mismatch、kill phase、cross-cutting readers、diagnostics 和 scope guard。
- Baseline / validation: YAML 校验、namespace backend / foreground attach / kill / start-ping regression、project view / health / slot replacement / runtime binding / doctor-ping projection、scope guard。

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

- Foreground attach 能力归属在 roadmap §4.1 的 MuxBackend / NamespaceLifecycle，而不是 §4.6 的 ProjectNamespaceBackend；本 feature 只能消费已批准契约，不能私自扩接口。
- `ccb kill` 的 local prepare 阶段是 evidence / registry 收集，不等于实际 PID termination；final PID cleanup / orphan cleanup / report merge 仍是 kill 完整性的必要阶段。

### praise

- canonical-first / legacy alias 策略明确，尤其是 Rmux path legacy tmux socket 为 null、不写 placeholder，能防止 authority 回退到旧 `tmux_socket_path`。
- 修订后 design 覆盖当前代码中最危险的 tmux 强依赖面：project view、project_focus、start_flow/runtime binding、health、slot replacement、clear/restart、layout/doctor/ping。

## 4. User Review Focus

- 用户需要重点拍板：本 child 是 start/attach/kill 的 namespace lifecycle 闭环，不包含 full-chain ask smoke、accelerator guard、process liveness 或 supervision/recovery。
- implement 需要重点遵守：不得把 attach 新塞进 ProjectNamespaceBackend；不得在 CLI/ccbd 调用层直接拼 `rmux` / `tmux` 命令；Rmux legacy tmux socket alias 必须为 null。
- code review / QA / acceptance 需要重点复核：foreground attach no-tmux guard、kill final cleanup 未丢失、cross-cutting readers 不因 legacy socket 缺失误判 unavailable、tmux regression 不漂移。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | design §3.1 / §3.3 覆盖 AC-001 至 AC-009 | none |
| DoD Contract | pass | E | design §3.4 覆盖 Design / Implementation / Review / QA / Acceptance DoD 与 validation commands | none |
| Steps and checks traceability | pass | E | checklist steps/checks 对应 design §2.4、§3.1、§3.4；YAML 校验通过 | none |
| Roadmap contract compliance | pass | E | roadmap item `ccbd-rmux-namespace-lifecycle`、§4.1、§4.5、§4.6、§4.9 与 design 边界对齐 | none |
| Module interface design | pass | C | Code facts show controller/backend/start_foreground/kill/project_view 等 tmux assumptions；design 已收束到 ProjectNamespaceBackend、MuxBackend attach 与 canonical namespace projection | implementation 不足时回前序 contract 修订 |
| Validation and artifacts | pass | E | checklist `dod.commands` 标注 new/new-or-extended，并覆盖 attach、kill phase、cross-cutting readers、diagnostics、guard | none |

Summary: E=5, C=1, H=0, H-only core checks=none。

## 6. Residual Risk

- 本 review 假设前序 `MuxBackend`、tmux adapter、namespace IPC schema、provider runtime session、Rmux core/send/capture、daemon ownership、TCP transport 按 design 落地。若 implementation 发现 attach、pane identity 或 layout projection 能力不足，应回前序 contract 修订，不应在本 feature 临时加浅封装。
- Windows/Rmux focused smoke 仍不能替代最终 `ccbd-windows-full-chain-smoke`；accelerator guard 和 process liveness 仍是 full-chain blocker。

## 7. Verdict

- Status: passed
- Next: 返回 `cs-epic` child design batch loop，继续下一个 epic child；本 child design 保持 `draft`，等待所有 child design-review 通过后由 epic 统一确认。

## 8. Focused Closure

- Closed findings: FDR-001、FDR-002、FDR-003
- Attributed delta: `.codestable/features/2026-07-20-ccbd-rmux-namespace-lifecycle/ccbd-rmux-namespace-lifecycle-design.md`、`.codestable/features/2026-07-20-ccbd-rmux-namespace-lifecycle/ccbd-rmux-namespace-lifecycle-checklist.yaml`
- Verification: reviewer `019f7cb1-5984-78d3-ba17-fdcab23fc44d` final focused closure verdict `passed`；checklist YAML 与 roadmap items YAML 校验通过
- Classification: 修订只关闭 reviewer 提出的契约澄清与验证覆盖问题，未修改生产代码；没有改变 feature 范围、roadmap 边界或前序接口所有权
