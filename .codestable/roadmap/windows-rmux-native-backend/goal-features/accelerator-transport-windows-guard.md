---
doc_type: roadmap-goal-feature
roadmap: windows-rmux-native-backend
roadmap_item: accelerator-transport-windows-guard
feature: 2026-07-20-accelerator-transport-windows-guard
status: pending
---

# accelerator-transport-windows-guard Goal Feature Spec

## 1. Identity

- Roadmap item: $slug
- Feature dir: $dir
- Design: $dir/accelerator-transport-windows-guard-design.md
- Checklist: $dir/accelerator-transport-windows-guard-checklist.yaml
- Design review: $dir/accelerator-transport-windows-guard-design-review.md
- Review output: $dir/accelerator-transport-windows-guard-review.md
- QA output: $dir/accelerator-transport-windows-guard-qa.md
- Acceptance output: $dir/accelerator-transport-windows-guard-acceptance.md
- Depends on: none
- Feature kind: $(System.Collections.Hashtable.kind)

## 2. Deliverable

native Windows/no-AF_UNIX accelerator clean fallback

## 3. Core Runtime Path

见 design 的 Acceptance Coverage Matrix 与 checklist dod.commands。

## 4. Mandatory Commands

- $_
- $_
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