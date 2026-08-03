---
doc_type: feature-evidence
feature: 2026-07-31-native-windows-public-workflow-validation-matrix
artifact: blocked-evidence
status: blocked
---

# Blocked Evidence

## Reason

Native Windows public workflow transcripts are not fully captured for every
required workflow and public provider.

## Encoding Rule

The matrix intentionally records non-pass rows instead of pass rows when a
workflow, provider workflow, Mobile terminal, Config UI, Windows npm install
dry-run, strict source admission, or Herdr auto-restore disabled evidence is
missing. Workflow and provider detail rows use `blocked`; the Windows npm
install dry-run top-level gate uses `not-run` until a concrete dry-run artifact
is captured, with the reason carried by `beta_gaps` and `residual_risks`.

## Support Rule

The blocked matrix keeps:

- `support_tier_is_candidate=true`
- `support_projection_allowed=false`
- `support_tier=beta`

This is candidate evidence for the later supportability projection feature. It
is not a final Windows support claim.
