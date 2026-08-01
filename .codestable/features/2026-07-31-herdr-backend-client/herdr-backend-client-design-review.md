---
doc_type: feature-design-review
feature: 2026-07-31-herdr-backend-client
status: passed
review_state: passed
review_reason: ""
reviewer_id: 019fb916-487d-7ac3-b8ca-09580201a0c6
reviewed: 2026-08-01
round: 3
---

# herdr-backend-client feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-31-herdr-backend-client/herdr-backend-client-design.md`
- Checklist: `.codestable/features/2026-07-31-herdr-backend-client/herdr-backend-client-checklist.yaml`
- Intent / brainstorm: none
- Roadmap: `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-roadmap.md`
- Related docs: `.codestable/features/2026-07-31-herdr-backend-contract-spike/herdr-backend-contract-spike-design.md`、`.codestable/features/2026-07-31-herdr-backend-contract-spike/herdr-backend-contract-spike-design-review.md`、`.codestable/features/2026-07-31-mux-backend-contract-herdr-v2/mux-backend-contract-herdr-v2-design.md`、`.codestable/features/2026-07-31-mux-backend-contract-herdr-v2/mux-backend-contract-herdr-v2-design-review.md`
- Code facts checked: `lib/terminal_runtime/mux_backend_contract.py`、`lib/terminal_runtime/backend_resolver.py`、`lib/terminal_runtime/backend_selection.py`、`lib/terminal_runtime/api.py`、`lib/terminal_runtime/rmux_backend.py`、`lib/terminal_runtime/rmux_backend_runtime/capabilities.py`、`lib/terminal_runtime/fake_mux_backend.py`、`lib/ccbd/services/project_namespace_state_runtime/models.py`、`test/test_rmux_backend_core.py`、`test/test_terminal_runtime_backend_selection.py`、`test/test_mux_backend_contract.py`、`test/test_v2_project_namespace_backend.py`

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: round 1 `019fb695-9630-7713-9c1c-185984702e17` changes-requested；round 2 `019fb6a0-d427-7e33-aae0-3d87e9b39ea3` passed；round 3 `019fb916-487d-7ac3-b8ca-09580201a0c6` passed.
- Raw output: round 3 未发现 blocking / important；确认 production Herdr socket client 设计范围正确，Native Windows x64 `auto` / platform default 直路由 Herdr blocked/success selection，缺 evidence 不 fallback tmux/rmux，Herdr 保持 `herdr-native`，capability gate 与 scope guards 覆盖充分。
- Merge policy: 已逐条核验 reviewer findings 与 design/checklist/roadmap/code 事实；blocking/important 已通过 design/checklist 修订关闭。
- Gate effect: independent review completed and merged; final verdict passed.

## 2. Design Summary

- Goal: 实现 terminal_runtime 层 Herdr production socket client、schema/version gate、capability gate、structured error、operation evidence，并以 gated route 接入 resolver/factory。
- Key contracts: Herdr adapter 必须依赖前置 V2 contract 单一来源；`HerdrBackendClient` 是内部 socket seam，public caller 只看 MuxBackend V2 refs/errors/evidence；platform gate 消费前置 baseline gate，不重写 doctor/install gate。
- Steps: 7 个 step，新增 S0 V2 implementation admission，随后处理 evidence admission、schema client、backend facade、resolver/factory route、scope guard、regression。
- Checks: 11 个 check 覆盖 V2 admission、evidence fail-closed、schema pass/mismatch、refs、pane IO、explicit route success/failure、Native Windows auto Herdr blocked/success selection、非 Windows auto/default unchanged 和 scope boundary。
- Baseline / validation: CMD-001/CMD-002 YAML gate；CMD-003 dependency admission；CMD-004/CMD-005 tests；CMD-006/CMD-007 scope/content guard。

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

- Production adapter child 需要显式 dependency admission；前置 child design-review passed 只允许继续设计，不等于 implementation-ready。
- Content guard 对 allowed paths 也要扫描 untracked 文件内容，否则新增测试或 adapter 文件可能绕过 forbidden term 检查。

### praise

- design 明确 raw Herdr JSON 不外露、缺 evidence/stop/blocking/unknown fail closed、Herdr agent state 不作为 provider completion authority，保持 roadmap §4.3/§4.4 的 adapter 隔离。

## 4. User Review Focus

- 用户需要重点拍板：本 child 是 production Herdr adapter，但仍不接入 ccbd namespace lifecycle、provider runtime、recovery、doctor/support 或 release surface。
- implement 需要重点遵守：先跑 V2 implementation admission；若 `MuxNamespaceRefV2` / `MuxCommandErrorV2` / `herdr-native` / `herdr_socket` / `schema-mismatch` 未落地，本 feature 必须 dependency-blocked。
- code review / QA / acceptance 需要重点复核：platform gate diagnostics、schema mismatch evidence、capability fail-closed、public facade 到 internal socket client mapping、scope/content guard。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | design §3.3 覆盖 V2 admission 与 AC-001 至 AC-010，并映射 step、证据类型和命令。 | none |
| DoD Contract | pass | E | design §3.4 覆盖 DOD-IMPL-000 至 DOD-ACCEPT-001、validation commands 和 required artifacts。 | implementation 先通过 dependency admission。 |
| Steps and checks traceability | pass | E | checklist steps/checks 均可追溯到 design AC / DOD；YAML 校验通过。 | none |
| Roadmap contract compliance | pass | E | roadmap §4.4 Herdr socket client/schema gate/evidence，§4.2 platform gate selection，§4.3 backend contract 均已映射。 | none |
| Module interface design | pass | C | 现有 rmux backend/capability gate 与 mux contract 代码支撑 adapter/facade 分层；design 已补 public-to-internal mapping。 | none |
| Validation and artifacts | pass | E | CMD-006/CMD-007 scope/content guard 当前执行通过；CMD-003 明确 dependency-blocked admission。 | V2 实现未落地时不可进入 adapter 实现。 |

Summary: E=5, C=1, H=0, H-only core checks=none。

## 6. Residual Risk

- 当前代码事实仍未包含 V2/Herdr contract；后续实现必须先通过 CMD-003 admission gate，不能跳过前置 child 或在 Herdr adapter 重复定义 V2 类型。
- 上游 `herdr-contract-spike-evidence.json` 当前不存在；实现阶段必须补 spike evidence 或 blocked fixture/result，不得伪造 capability success。

## 7. Verdict

- Status: passed
- Next: 回到 `cs-epic` child design batch loop；本 child design 保持 `draft`，等待 epic 的所有 child design 统一确认。

## 8. Focused Closure

- Closed findings: FDR-001、FDR-002、FDR-003、FDR-004、FDR-005。
- Attributed delta: 新增 S0 V2 implementation admission、DOD-IMPL-000、CMD-003 dependency-blocked；CMD-007 读取 modified/staged/untracked `lib/test` 内容；补 `platform_gate_reader` / `WindowsX64PlatformGate` provider 边界；补 public `HerdrBackend` 到 internal `HerdrBackendClient` mapping；收紧 items.yaml 为 acceptance 阶段按 epic/roadmap owner 协议回写。
- Verification: design/checklist/review YAML 均通过；roadmap items YAML 通过；CMD-006 当前执行通过；round 3 independent reviewer 返回 `passed`。
- Classification: 修订均为 design/checklist 契约和 guard 补强，没有进入 implementation，没有改变本 feature 的范围边界。
