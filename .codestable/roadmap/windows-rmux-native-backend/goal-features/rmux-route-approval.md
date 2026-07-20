---
doc_type: roadmap-goal-feature
roadmap: windows-rmux-native-backend
roadmap_item: rmux-route-approval
feature: 2026-07-19-rmux-route-approval
status: pending
---

# rmux-route-approval Goal Feature Spec

## 1. Identity

- Roadmap item: $slug
- Feature dir: $dir
- Design: $dir/rmux-route-approval-design.md
- Checklist: $dir/rmux-route-approval-checklist.yaml
- Design review: $dir/rmux-route-approval-design-review.md
- Review output: $dir/rmux-route-approval-review.md
- QA output: $dir/rmux-route-approval-qa.md
- Acceptance output: $dir/rmux-route-approval-acceptance.md
- Depends on: rmux-capability-gate
- Feature kind: $(System.Collections.Hashtable.kind)

## 2. Deliverable

Rmux route approval evidence 与 decision summary

## 3. Core Runtime Path

none；以 approval/report/schema/docs/guard 证据替代用户运行路径。

## 4. Mandatory Commands

- $_
- $_
- $_

## 5. Gates And Recovery

- Implementation gate: checklist steps done, scope-gate, dod-runner and evidence-pack passed.
- Review gate: independent cs-code-review passed with no unresolved blocking findings.
- QA gate: cs-feat QA passed and covers design scenarios, DoD commands and review QA focus.
- Acceptance gate: cs-feat acceptance passed via pproval-report.md#goal-acceptance, checklist checks passed and roadmap item writeback complete.
- Recovery: implementation defects return to implementation then review/QA/acceptance; stage evidence defects repair the owning stage only.

## 6. Evidence And Cleanliness

- Evidence required: design/checklist/review/QA/acceptance, gate JSON, evidence pack, command outputs, roadmap/items writeback.
- Cleanliness: no debug output, temporary TODO/FIXME/XXX, commented-out code, dead imports, same-name validation shims or unexplained scope drift.