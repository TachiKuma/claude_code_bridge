# ccbd-herdr-namespace-lifecycle

- Roadmap item: `ccbd-herdr-namespace-lifecycle`
- Design: `.codestable/features/2026-07-31-ccbd-herdr-namespace-lifecycle/ccbd-herdr-namespace-lifecycle-design.md`
- Checklist: `.codestable/features/2026-07-31-ccbd-herdr-namespace-lifecycle/ccbd-herdr-namespace-lifecycle-checklist.yaml`
- Design review: `.codestable/features/2026-07-31-ccbd-herdr-namespace-lifecycle/ccbd-herdr-namespace-lifecycle-design-review.md`
- Review: `.codestable/features/2026-07-31-ccbd-herdr-namespace-lifecycle/ccbd-herdr-namespace-lifecycle-review.md`
- QA: `.codestable/features/2026-07-31-ccbd-herdr-namespace-lifecycle/ccbd-herdr-namespace-lifecycle-qa.md`
- Acceptance: `.codestable/features/2026-07-31-ccbd-herdr-namespace-lifecycle/ccbd-herdr-namespace-lifecycle-acceptance.md`
- Depends on: `herdr-backend-client`
- Nature: functional
- Core runtime path: ccbd project namespace lifecycle, layout/reflow, foreground attach, kill/restart/reload on Herdr.
- Mandatory commands: approved checklist `dod.commands`.
- Evidence required: namespace schema tests, CLI/ccbd lifecycle tests, foreground/manual transcript when marked core.
- Failure recovery: keep provider/recovery/user-surface/release changes out of this feature.
