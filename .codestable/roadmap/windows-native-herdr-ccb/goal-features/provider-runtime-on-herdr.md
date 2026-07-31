# provider-runtime-on-herdr

- Roadmap item: `provider-runtime-on-herdr`
- Design: `.codestable/features/2026-07-31-provider-runtime-on-herdr/provider-runtime-on-herdr-design.md`
- Checklist: `.codestable/features/2026-07-31-provider-runtime-on-herdr/provider-runtime-on-herdr-checklist.yaml`
- Design review: `.codestable/features/2026-07-31-provider-runtime-on-herdr/provider-runtime-on-herdr-design-review.md`
- Review: `.codestable/features/2026-07-31-provider-runtime-on-herdr/provider-runtime-on-herdr-review.md`
- QA: `.codestable/features/2026-07-31-provider-runtime-on-herdr/provider-runtime-on-herdr-qa.md`
- Acceptance: `.codestable/features/2026-07-31-provider-runtime-on-herdr/provider-runtime-on-herdr-acceptance.md`
- Depends on: `ccbd-herdr-namespace-lifecycle`
- Nature: functional
- Core runtime path: all public providers in Herdr pane through ask, pend, completion and cancel.
- Mandatory commands: approved checklist `dod.commands`.
- Evidence required: provider catalog freeze, provider workflow tests/transcripts, completion authority evidence, cancellation evidence.
- Failure recovery: Herdr agent state may be diagnostic evidence only, never completion authority.
