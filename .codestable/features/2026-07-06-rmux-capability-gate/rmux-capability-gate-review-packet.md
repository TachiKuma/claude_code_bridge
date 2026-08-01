---
doc_type: feature-review-packet
feature: 2026-07-06-rmux-capability-gate
stage: implementation
created: 2026-07-20
---

# rmux-capability-gate Review Packet

## Role

你是本 feature 的独立代码审查 agent。只读，不修改文件，不更新 checklist/design/review/QA/acceptance。

请基于仓库当前状态审查 `rmux-capability-gate` implementation 是否满足已批准 design/checklist，并输出：

- `blocking`
- `important`
- `nit`
- `suggestion`
- `learning`
- `praise`
- `residual-risk`
- `Test And QA Focus`
- 最终 `Verdict: passed | changes-requested | blocked`

每条 finding 必须有文件路径、行号或仓库事实证据、影响、建议修复边界。

## Canonical Inputs

- Attention: `.codestable/attention.md`
- Design: `.codestable/features/2026-07-06-rmux-capability-gate/rmux-capability-gate-design.md`
- Checklist: `.codestable/features/2026-07-06-rmux-capability-gate/rmux-capability-gate-checklist.yaml`
- Evidence pack: `.codestable/features/2026-07-06-rmux-capability-gate/rmux-capability-gate-evidence-pack.md`
- Scope gate: `.codestable/features/2026-07-06-rmux-capability-gate/rmux-capability-gate-scope-gate.json`
- DoD results: `.codestable/features/2026-07-06-rmux-capability-gate/rmux-capability-gate-dod-results.json`
- Current blocked placeholder review: `.codestable/features/2026-07-06-rmux-capability-gate/rmux-capability-gate-review.md`

## Implementation Files To Review

- `scripts/probe_rmux_capability.py`
- `test/test_rmux_capability_probe.py`
- `.codestable/features/2026-07-06-rmux-capability-gate/rmux-capability-gate-checklist.yaml`
- Latest capability report under `.codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate/`

## Validation Evidence

Fresh DoD runner evidence is in `rmux-capability-gate-dod-results.json`.

Known passing commands:

- `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-06-rmux-capability-gate/rmux-capability-gate-checklist.yaml" --yaml-only`
- `python -m pytest -q test/test_rmux_capability_probe.py`
- `python "scripts/probe_rmux_capability.py" --work-root ".codestable/roadmap/windows-rmux-native-backend/drafts/rmux-capability-gate"`
- `python -m pytest -q test/test_codex_pane_status_probe.py`

Latest probe reports `blocking_gaps: 7`. Treat those as Rmux capability facts for later route approval, not automatically as implementation failure.

## Review Focus

1. Does `CapabilityReport` contain the required schema fields and mechanically derived `blocking_gaps`?
2. Does command catalog cover the roadmap command set?
3. Does semantic catalog cover the design-required scenarios?
4. Are `partial` / `workaround` invariants represented structurally, without relying on `notes`?
5. Do command/semantic records and blocking gaps carry `degrade_impact` and `consequence`?
6. Can every evidence path be resolved through `artifact_index`, and are artifacts redacted?
7. Does probe flow preserve preflight -> namespace -> command probes -> semantic probes -> capture fidelity -> gap generation -> cleanup?
8. Does capture fidelity distinguish fixture parser-facing evidence from true Windows Rmux artifacts?
9. Does implementation avoid production `RmuxBackend`, resolver changes, `runtime.mux.backend`, `CCB_MUX_BACKEND`, and transparent rmux-as-tmux substitution?
10. Are tests strong enough to fail on schema/gap/redaction/artifact/capture regressions?

## Scope Notes

- `.codestable/gates/roadmap-goal-gates.yaml` had a pre-existing CRLF dirty signal and is not part of this feature implementation.
- Do not treat CodeStable planning artifacts as production code, but do verify they are coherent evidence for the gate.
