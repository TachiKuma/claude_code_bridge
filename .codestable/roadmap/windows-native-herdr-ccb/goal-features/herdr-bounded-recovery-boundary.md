# herdr-bounded-recovery-boundary

- Roadmap item: `herdr-bounded-recovery-boundary`
- Design: `.codestable/features/2026-07-31-herdr-bounded-recovery-boundary/herdr-bounded-recovery-boundary-design.md`
- Checklist: `.codestable/features/2026-07-31-herdr-bounded-recovery-boundary/herdr-bounded-recovery-boundary-checklist.yaml`
- Design review: `.codestable/features/2026-07-31-herdr-bounded-recovery-boundary/herdr-bounded-recovery-boundary-design-review.md`
- Review: `.codestable/features/2026-07-31-herdr-bounded-recovery-boundary/herdr-bounded-recovery-boundary-review.md`
- QA: `.codestable/features/2026-07-31-herdr-bounded-recovery-boundary/herdr-bounded-recovery-boundary-qa.md`
- Acceptance: `.codestable/features/2026-07-31-herdr-bounded-recovery-boundary/herdr-bounded-recovery-boundary-acceptance.md`
- Depends on: `provider-runtime-on-herdr`
- Nature: mixed
- Core runtime path: CCB-owned bounded recovery with Herdr restore as backend operation/evidence.
- Mandatory commands: approved checklist `dod.commands`.
- Evidence required: recovery policy tests, auto-restore disabled evidence, crash/backoff/circuit evidence.
- Failure recovery: if Herdr auto restore cannot be disabled/proved disabled, block supported path.
