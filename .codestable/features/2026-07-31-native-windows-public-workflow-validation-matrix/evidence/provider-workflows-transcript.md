---
doc_type: feature-evidence
feature: 2026-07-31-native-windows-public-workflow-validation-matrix
artifact: provider-workflows-transcript
status: blocked
---

# Provider Workflow Transcript

## Provider Catalog Freeze

The provider set is frozen in
`.codestable/features/2026-07-31-native-windows-public-workflow-validation-matrix/evidence/public-providers-freeze.json`.
It is generated from
`build_default_provider_manifests(include_optional=True, include_test_doubles=False)`.

Current frozen providers:

- `agy`
- `claude`
- `codex`
- `copilot`
- `crush`
- `cursor`
- `deepseek`
- `droid`
- `gemini`
- `grok`
- `kimi`
- `kiro`
- `mimo`
- `omp`
- `opencode`
- `pi`
- `qoder`
- `qoderclicn`
- `qwen`
- `zai`

## Required Provider Workflow Rows

Every public provider requires independent Herdr pane evidence for:

- `ask`
- `pend`
- `completion`
- `cancel`

The matrix stores the roadmap summary shape as
`provider_workflow_rows[provider][workflow] = status` and detailed evidence in
`provider_workflow_detail_rows["{provider}:{workflow}"]`.

## Current Result

- Verdict: blocked.
- Reason: the full public provider x workflow transcript set has not been
  captured on the current Native Windows x64 host.
- Matrix status: all provider workflow rows are `blocked`.
- Support candidate: `support_projection_allowed=false`.

