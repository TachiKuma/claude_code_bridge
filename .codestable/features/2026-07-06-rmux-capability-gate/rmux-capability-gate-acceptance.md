---
doc_type: feature-acceptance
feature: 2026-07-06-rmux-capability-gate
status: accepted
accepted: 2026-07-20
approval_ref: .codestable/roadmap/windows-rmux-native-backend/approval-report.md#goal-acceptance
qa_ref: .codestable/features/2026-07-06-rmux-capability-gate/rmux-capability-gate-qa.md
review_ref: .codestable/features/2026-07-06-rmux-capability-gate/rmux-capability-gate-review.md
latest_capability_report: .codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T094438Z-4728/capability-report.json
---

# rmux-capability-gate 验收报告

## 1. Acceptance Input

- Resume authorization: `approval-report.md#goal-acceptance`
- Review: passed by independent Task agent reviewer `019f7ed3-c18a-7d80-808b-2ce35b2d0e75`
- QA: passed
- DoD runner: passed at `stage=acceptance`
- Latest capability report: `.codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/run-20260720T094438Z-4728/capability-report.json`

## 2. Acceptance Checks

| Check | Result |
|---|---|
| CapabilityReport schema contains required top-level fields | passed |
| Command catalog covers roadmap command set | passed |
| Semantic catalog covers required semantic set | passed |
| `partial` / `workaround` invariants are represented structurally | passed |
| `blocking_gaps` are derived mechanically and carry degrade context | passed |
| Evidence paths are relative and indexed by `artifact_index` | passed |
| Probe failure handling is structured | passed |
| Redaction and no-full-environment rule are covered by tests | passed |
| Scope guard avoids production `RmuxBackend`, runtime config and backend selection changes | passed |
| Windows true-host capability report exists | passed |

## 3. Accepted Outcome

This feature is accepted as a capability gate. It establishes repeatable Windows Rmux fact collection and produces a conservative report with `probe_status=completed` and `blocking_gaps=7`.

The accepted state does not approve the Rmux route. The next feature, `rmux-route-approval`, must consume the seven gaps and decide whether to continue, pause or reselect.

## 4. Roadmap Writeback

- `windows-rmux-native-backend-items.yaml`: `rmux-capability-gate` should be `done`.
- `windows-rmux-native-backend-roadmap.md`: child feature 1 should be marked `accepted` with the latest capability report path.
- `goal-state.yaml`: feature status should be `accepted`, `current_feature_index` should advance to the next feature.

## 5. Delivery Record

- QA report written: `.codestable/features/2026-07-06-rmux-capability-gate/rmux-capability-gate-qa.md`
- Acceptance report written: `.codestable/features/2026-07-06-rmux-capability-gate/rmux-capability-gate-acceptance.md`
- Checklist checks marked passed.
- Roadmap item and goal-state updated.
- Local commit intentionally not performed in this turn.

## 6. Residual Risks

- Seven capability gaps remain and must be consumed by route approval.
- The goal protocol normally performs a scoped commit before advancing; this turn is left as handoff because local commit was explicitly disallowed.

## 7. Verdict

Accepted. The epic should resume from `current_feature_index=1` after the current accepted feature state is committed or otherwise explicitly resumed. When `rmux-route-approval` is reached, it must consume the seven recorded blocking gaps.
