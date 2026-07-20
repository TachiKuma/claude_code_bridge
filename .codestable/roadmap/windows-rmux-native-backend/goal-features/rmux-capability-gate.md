---
doc_type: roadmap-goal-feature
roadmap: windows-rmux-native-backend
roadmap_item: rmux-capability-gate
feature: 2026-07-06-rmux-capability-gate
status: pending
---

# rmux-capability-gate Goal Feature Spec

## 1. Identity

- Roadmap item: $slug
- Feature dir: $dir
- Design: $dir/rmux-capability-gate-design.md
- Checklist: $dir/rmux-capability-gate-checklist.yaml
- Design review: $dir/rmux-capability-gate-design-review.md
- Review output: $dir/rmux-capability-gate-review.md
- QA output: $dir/rmux-capability-gate-qa.md
- Acceptance output: $dir/rmux-capability-gate-acceptance.md
- Depends on: none
- Feature kind: $(System.Collections.Hashtable.kind)

## 2. Deliverable

Windows Rmux capability probe 与 gap report

## 3. Core Runtime Path

见 design 的 Acceptance Coverage Matrix 与 checklist dod.commands。

## 4. Mandatory Commands

- $_
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