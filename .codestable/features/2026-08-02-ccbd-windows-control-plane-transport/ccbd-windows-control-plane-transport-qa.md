---
doc_type: feature-qa
feature: 2026-08-02-ccbd-windows-control-plane-transport
status: passed
runner_state: completed
runner_reason: ""
runner_id: "019fc056-2009-7173-aeb6-8aa6fc7137fb"
tested: 2026-08-02
round: 1
---

# ccbd-windows-control-plane-transport QA 报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-08-02-ccbd-windows-control-plane-transport/ccbd-windows-control-plane-transport-design.md`
- Checklist: `.codestable/features/2026-08-02-ccbd-windows-control-plane-transport/ccbd-windows-control-plane-transport-checklist.yaml`
- Review: `.codestable/features/2026-08-02-ccbd-windows-control-plane-transport/ccbd-windows-control-plane-transport-review.md`
- Evidence pack: `.codestable/features/2026-08-02-ccbd-windows-control-plane-transport/ccbd-windows-control-plane-transport-evidence-pack.md`
- Gate results: `.codestable/features/2026-08-02-ccbd-windows-control-plane-transport/ccbd-windows-control-plane-transport-scope-gate-results.json`
- DoD results: `.codestable/features/2026-08-02-ccbd-windows-control-plane-transport/ccbd-windows-control-plane-transport-dod-results.json`
- Diff basis: current working tree scoped to control-plane transport, socket client runtime, focused tests, DoD runner, and feature artifacts.
- Baseline dirty files: `笔记.md` is out of scope.
- Feature type: functional.
- Core evidence gate: all AC-001..AC-009 have unit/integration/guard/manual evidence; AC-009 only proves the AF_UNIX control-plane blocker is gone and downstream namespace lifecycle remains blocked.

## 2. Verification Matrix

| ID | 来源 | 核心性 | 场景 / 风险 | 证据类型 | 命令或动作 | 期望 | 结果 |
|---|---|---|---|---|---|---|---|
| QA-001 | AC-001 | core-functional | Unix AF_UNIX 与 fake transport 不退化 | unit | CMD-003 | 14 passed | pass |
| QA-002 | AC-002..005 | core-functional | Windows TCP endpoint/token/auth/ACL/handler gate | unit/integration | CMD-004 | 19 passed | pass |
| QA-003 | AC-006 | core-functional | bootstrap self-ping 走同一 transport/auth path | regression | CMD-005 | 53 passed, 1 skipped | pass |
| QA-004 | AC-007/008 | core-functional | token redaction、no named pipe、no RPC schema/handler scope drift | guard | CMD-007 | 2 passed | pass |
| QA-005 | AC-009 | core-functional | CMD-013 不再因 AF_UNIX unsupported 失败 | manual manifest | CMD-008 manifest | transport_blocker=resolved, downstream lifecycle=blocked | pass |
| QA-006 | review focus | supporting | DoD runner manual evidence fail-closed | unit | `python -m pytest -q test/test_codestable_dod_runner.py` | 9 passed | pass |
| QA-007 | gate warning | supporting | Windows start-service collection baseline | pytest | CMD-006 | documented `fcntl` import baseline | pass-with-warning |

## 3. Command Results

- `python -m pytest -q test/test_codestable_dod_runner.py` -> exit 0: 9 passed.
- `python .codestable/tools/codestable-dod-runner.py --checklist ... --stage qa` -> exit 0: DoD passed; CMD-006 warning retained; CMD-008 manifest evidence present.
- CMD-003 -> exit 0: 14 passed.
- CMD-004 -> exit 0: 19 passed.
- CMD-005 -> exit 0: 53 passed, 1 skipped.
- CMD-007 -> exit 0: 2 passed.
- CMD-006 -> exit 2: documented baseline, `mobile_gateway.terminal` imports `fcntl` on Windows during collection.

## 4. Scenario Results

- [x] QA-001 Unix regression: pass.
  - Evidence: CMD-003.
- [x] QA-002 Windows TCP/token/auth: pass.
  - Evidence: CMD-004.
- [x] QA-003 bootstrap auth path: pass.
  - Evidence: CMD-005.
- [x] QA-004 redaction/scope guard: pass.
  - Evidence: CMD-007.
- [x] QA-005 CMD-013 transport blocker: pass for this feature only.
  - Evidence: `ccbd-windows-control-plane-transport-cmd008-evidence.json`.
  - Notes: source transcript still records namespace create, ping, foreground attach, reload apply as blocked; this belongs to `ccbd-herdr-namespace-lifecycle`.

## 5. Findings

### failed

none

### blocked

none

### residual-risk

- CMD-006 remains a Windows `fcntl` collection baseline outside this feature.
- token payload may briefly appear in PowerShell child command text; follow-up hardening recommended.
- Downstream Herdr namespace lifecycle remains blocked and must not be claimed here.

## 6. Cleanliness

- Debug output: pass.
- Temporary TODO/FIXME/XXX: pass for production/test diff; scope-gate warnings are existing rule text/design marker false positives.
- Commented-out code: pass.
- Unused imports / dead code from this feature: pass.
- Out-of-scope files: pass; `笔记.md` excluded.

## 7. Verdict

- Status: passed
- Next: `cs-feat` acceptance 阶段。
