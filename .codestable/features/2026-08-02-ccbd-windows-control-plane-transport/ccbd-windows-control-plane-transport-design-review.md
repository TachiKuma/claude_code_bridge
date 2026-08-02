---
doc_type: feature-design-review
feature: 2026-08-02-ccbd-windows-control-plane-transport
status: passed
review_state: passed
review_reason: ""
reviewer_id: "019fbffa-2870-7ca2-b183-793148cec530"
reviewed: 2026-08-02
round: 1
---

# ccbd-windows-control-plane-transport feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-08-02-ccbd-windows-control-plane-transport/ccbd-windows-control-plane-transport-design.md`
- Checklist: `.codestable/features/2026-08-02-ccbd-windows-control-plane-transport/ccbd-windows-control-plane-transport-checklist.yaml`
- Intent / brainstorm: none
- Roadmap: `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-roadmap.md`, `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml`
- Related docs: `.codestable/requirements/native-windows-ccb-via-herdr.md`; old accepted references `2026-07-20-ccbd-control-plane-transport-seam` and `2026-07-20-ccbd-windows-tcp-loopback-transport`
- Code facts checked: `lib/ccbd/socket_server_runtime/lifecycle.py`, `lib/ccbd/control_plane_transport/` directory presence

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: `019fbffa-2870-7ca2-b183-793148cec530`
- Raw output: first pass returned `changes-requested` with 2 blocking findings and 1 important finding; focused closure returned `passed`.
- Merge policy: findings were locally verified against design/checklist, then patched in the same design chain.
- Gate effect: passed after focused closure confirmed all findings are closed.

## 2. Design Summary

- Goal: add a roadmap child feature that restores Native Windows `ccb->ccbd` control-plane transport before Herdr namespace lifecycle resumes.
- Key contracts: `ccbd.control_plane_transport` seam, Unix AF_UNIX adapter, Windows TCP loopback adapter, same-user token handshake, endpoint descriptor, diagnostics redaction and legacy `socket_path` projection.
- Steps: 7 steps; highest-risk steps are token ACL convergence, Windows TCP listener/connector, and CMD-013 retry.
- Checks: 9 checks; each maps to AC/DOD rows in the design.
- Baseline / validation: YAML validation, focused pytest for transport/bootstrap/start service, redaction/import guards, and Native Windows CMD-013 transcript.

## 3. Findings

### blocking

- [x] FDR-001 `ccbd-windows-control-plane-transport-design.md` same-user token ACL/权限“收敛”标准不可证伪。
  - Evidence: initial design required fail-fast when ACL cannot be proven but did not define proof criteria.
  - Impact: implementation and acceptance could disagree on whether token ACL is safe.
  - Expected fix scope: define pass/fail evidence for current-user-only readability and map it to checklist.
  - Closure: design now defines current-user runtime root, current-user readability, owner/allow identity match, absence of non-current-user read ACEs, and structured evidence; checklist S3/check now requires the same.

- [x] FDR-002 `ccbd-windows-control-plane-transport-design.md` / checklist missing unreadable token coverage.
  - Evidence: success criteria mentioned unreadable token, while AC/checklist only covered missing/bad token.
  - Impact: acceptance could pass without testing a declared auth failure class.
  - Expected fix scope: add unreadable token to AC, checklist, and validation mapping.
  - Closure: AC-005, checklist S3 and the auth failure check now include `missing/bad/unreadable token`.

### important

- [x] FDR-003 diagnostics payload legacy `socket_path` compatibility was not explicitly checklist-tracked.
  - Evidence: design success criteria required ping/doctor/startup/mounted payload compatibility, but checklist S6 only covered redaction/scope.
  - Impact: payload compatibility could regress while redaction tests still pass.
  - Closure: design AC-007 and checklist S6/check now require legacy `socket_path` compatibility: Unix original path, Windows null/empty.

### nit

none

### suggestion

none

### learning

- Security boundary terms such as same-user token need positive pass criteria, not only fail-fast wording.

### praise

- The feature boundary cleanly separates `ccb<->ccbd` control-plane transport from Herdr namespace/provider/recovery work.

## 4. User Review Focus

- 用户需要重点拍板：新增 child feature 是否按 draft design 的边界承接 seam + Windows TCP/token，而不是把该工作混入 namespace feature。
- implement 需要重点遵守：handler 前认证、token redaction、Unix 不漂移、Windows endpoint canonical-first。
- code review / QA / acceptance 需要重点复核：ACL proof、unreadable token failure、legacy `socket_path` payload compatibility、CMD-013 是否推进出 AF_UNIX blocker。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | design AC-001..AC-009 map to checklist checks and commands | none |
| DoD Contract | pass | E | DOD rows include design, implementation, QA, acceptance, commands, artifacts | none |
| Steps and checks traceability | pass | E | checklist steps/checks reference design AC/DOD rows | none |
| Roadmap contract compliance | pass | E | items.yaml inserts `ccbd-windows-control-plane-transport` before `ccbd-herdr-namespace-lifecycle` | none |
| Module interface design | pass | E/C | design includes interface/seam/dependency strategy and code fact in current lifecycle | none |
| Validation and artifacts | pass | E | CMD-001..CMD-008 and Required Artifacts are explicit | none |

Summary: E=5, C=1, H=0, H-only core checks=none。

## 6. Residual Risk

- Windows ACL evidence can vary by localized Windows output, inherited ACEs, domain users, and filesystem policy. Implementation must keep ACL parser/runner injectable and fail closed when evidence is ambiguous.
- CMD-013 may expose the next Herdr namespace lifecycle failure after control-plane startup is fixed; that would belong to `ccbd-herdr-namespace-lifecycle`, not this transport feature.

## 7. Verdict

- Status: passed
- Next: 交回 epic child batch；新增 child design 仍为 `draft`，等待 owner 统一确认后才能进入实现。

## 8. Focused Closure

- Closed findings: FDR-001, FDR-002, FDR-003.
- Attributed delta: design/checklist only; added ACL proof criteria, unreadable token coverage, and legacy `socket_path` payload compatibility.
- Verification: checklist YAML validation passed; focused grep confirmed all new terms exist in design/checklist; independent reviewer focused closure returned `passed`.
- Classification: focused closure candidate. The patch tightens acceptance semantics and traceability without changing behavior scope, public roadmap boundary, or architecture placement.
