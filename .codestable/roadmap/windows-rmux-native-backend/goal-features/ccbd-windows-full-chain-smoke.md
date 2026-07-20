---
doc_type: roadmap-goal-feature
roadmap: windows-rmux-native-backend
roadmap_item: ccbd-windows-full-chain-smoke
feature: 2026-07-20-ccbd-windows-full-chain-smoke
status: pending
---

# ccbd-windows-full-chain-smoke Goal Feature Spec

## 1. Identity

- Roadmap item: $slug
- Feature dir: $dir
- Design: $dir/ccbd-windows-full-chain-smoke-design.md
- Checklist: $dir/ccbd-windows-full-chain-smoke-checklist.yaml
- Design review: $dir/ccbd-windows-full-chain-smoke-design-review.md
- Review output: $dir/ccbd-windows-full-chain-smoke-review.md
- QA output: $dir/ccbd-windows-full-chain-smoke-qa.md
- Acceptance output: $dir/ccbd-windows-full-chain-smoke-acceptance.md
- Depends on: ccbd-windows-tcp-loopback-transport, ccbd-rmux-namespace-lifecycle, accelerator-transport-windows-guard, ccbd-windows-process-liveness
- Feature kind: $(System.Collections.Hashtable.kind)

## 2. Deliverable

native Windows ccb->ccbd->rmux start/ask/kill transcript smoke

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