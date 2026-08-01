---
doc_type: roadmap-goal-feature
roadmap: windows-rmux-native-backend
roadmap_item: rmux-supervision-recovery
feature: 2026-07-20-rmux-supervision-recovery
status: accepted
---

# rmux-supervision-recovery Goal Feature Spec

## 1. Identity

- Roadmap item: $slug
- Feature dir: $dir
- Design: $dir/rmux-supervision-recovery-design.md
- Checklist: $dir/rmux-supervision-recovery-checklist.yaml
- Design review: $dir/rmux-supervision-recovery-design-review.md
- Review output: $dir/rmux-supervision-recovery-review.md
- QA output: $dir/rmux-supervision-recovery-qa.md
- Acceptance output: $dir/rmux-supervision-recovery-acceptance.md
- Depends on: ccbd-rmux-namespace-lifecycle
- Feature kind: $(System.Collections.Hashtable.kind)

## 2. Deliverable

Rmux pane/provider/daemon supervision recovery diagnostics

## 3. Core Runtime Path

见 design 的 Acceptance Coverage Matrix 与 checklist dod.commands。

## 4. Mandatory Commands

- $_
- $_
- $_
- $_
- $_
- $_
- $_

## 5. Gates And Recovery

- Implementation gate: checklist steps done, scope-gate, dod-runner and evidence-pack passed.
- Review gate: independent Task agent review passed with no unresolved blocking findings.
- QA gate: QA passed with DoD commands, fake evidence recovery smoke, diagnostics projection and scope guard evidence.
- Acceptance gate: Task agent functional acceptance passed; checklist checks passed and roadmap item writeback complete.
- Recovery: implementation defects return to implementation then review/QA/acceptance; stage evidence defects repair the owning stage only.

## 6. Evidence And Cleanliness

- Evidence required: design/checklist/review/QA/acceptance, gate JSON, evidence pack, command outputs, roadmap/items writeback.
- Cleanliness: no debug output, temporary TODO/FIXME/XXX, commented-out code, dead imports, same-name validation shims or unexplained scope drift.
