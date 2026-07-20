---
doc_type: roadmap-goal-feature
roadmap: windows-rmux-native-backend
roadmap_item: rmux-backend-core
feature: 2026-07-20-rmux-backend-core
status: pending
---

# rmux-backend-core Goal Feature Spec

## 1. Identity

- Roadmap item: $slug
- Feature dir: $dir
- Design: $dir/rmux-backend-core-design.md
- Checklist: $dir/rmux-backend-core-checklist.yaml
- Design review: $dir/rmux-backend-core-design-review.md
- Review output: $dir/rmux-backend-core-review.md
- QA output: $dir/rmux-backend-core-qa.md
- Acceptance output: $dir/rmux-backend-core-acceptance.md
- Depends on: tmux-backend-contract-adapter, windows-namespace-ipc-schema, windows-shell-log-builder, provider-runtime-backend-session-contract, rmux-daemon-ownership-boundary
- Feature kind: $(System.Collections.Hashtable.kind)

## 2. Deliverable

Rmux namespace/session/window/pane backend core

## 3. Core Runtime Path

见 design 的 Acceptance Coverage Matrix 与 checklist dod.commands。

## 4. Mandatory Commands

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