---
doc_type: roadmap-goal-feature
roadmap: windows-rmux-native-backend
roadmap_item: ccbd-windows-full-chain-smoke
feature: 2026-07-20-ccbd-windows-full-chain-smoke
status: accepted
---

# ccbd-windows-full-chain-smoke Goal Feature Spec

## 1. Identity

- Roadmap item: `ccbd-windows-full-chain-smoke`
- Feature dir: `.codestable/features/2026-07-20-ccbd-windows-full-chain-smoke`
- Design: `.codestable/features/2026-07-20-ccbd-windows-full-chain-smoke/ccbd-windows-full-chain-smoke-design.md`
- Checklist: `.codestable/features/2026-07-20-ccbd-windows-full-chain-smoke/ccbd-windows-full-chain-smoke-checklist.yaml`
- Design review: `.codestable/features/2026-07-20-ccbd-windows-full-chain-smoke/ccbd-windows-full-chain-smoke-design-review.md`
- Review output: `.codestable/features/2026-07-20-ccbd-windows-full-chain-smoke/ccbd-windows-full-chain-smoke-review.md`
- QA output: `.codestable/features/2026-07-20-ccbd-windows-full-chain-smoke/ccbd-windows-full-chain-smoke-qa.md`
- Acceptance output: `.codestable/features/2026-07-20-ccbd-windows-full-chain-smoke/ccbd-windows-full-chain-smoke-acceptance.md`
- Depends on: ccbd-windows-tcp-loopback-transport, ccbd-rmux-namespace-lifecycle, accelerator-transport-windows-guard, ccbd-windows-process-liveness
- Feature kind: standard

## 2. Deliverable

native Windows `ccb -> ccbd -> rmux` start / ask / kill transcript smoke。当前 canonical evidence 使用 `artifacts/rmux-windows-validation/manual-transcript.json` 和 `artifacts/rmux-windows-validation/rmux_windows_validation_report.json`；历史 PS5 / PS7 transcript 路径在当前 checkout 不作为 pass 依据。

## 3. Core Runtime Path

见 design 的 Acceptance Coverage Matrix 与 checklist dod.commands。

## 4. Mandatory Commands

- `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-20-ccbd-windows-full-chain-smoke/ccbd-windows-full-chain-smoke-checklist.yaml" --yaml-only`
- `python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml"`
- `python -m pytest -q test/test_ccbd_windows_full_chain_smoke.py`
- `python "scripts/rmux_windows_validation_matrix.py" --lane windows_true_host --scope full --transcript "artifacts/rmux-windows-validation/manual-transcript.json" --json`
- `python "scripts/rmux_windows_validation_matrix.py" --validate-manifest --json`
- `python "scripts/ccbd_windows_full_chain_smoke.py" --scope-guard --diff-base HEAD --json`

## 5. Gates And Recovery

- Implementation gate: checklist steps done, scope-gate, dod-runner and evidence-pack passed.
- Review gate: independent cs-code-review passed with no unresolved blocking findings.
- QA gate: cs-feat QA passed and covers design scenarios, DoD commands and review QA focus.
- Acceptance gate: cs-feat acceptance passed, checklist checks passed and roadmap item writeback complete.
- Recovery: implementation defects return to implementation then review/QA/acceptance; stage evidence defects repair the owning stage only.

## 6. Evidence And Cleanliness

- Evidence required: design/checklist/review/QA/acceptance, gate JSON, evidence pack, command outputs, roadmap/items writeback.
- Cleanliness: no debug output, temporary TODO/FIXME/XXX, commented-out code, dead imports, same-name validation shims or unexplained scope drift.
