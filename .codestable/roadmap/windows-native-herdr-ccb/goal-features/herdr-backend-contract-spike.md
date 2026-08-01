# herdr-backend-contract-spike

- Roadmap item: `herdr-backend-contract-spike`
- Design: `.codestable/features/2026-07-31-herdr-backend-contract-spike/herdr-backend-contract-spike-design.md`
- Checklist: `.codestable/features/2026-07-31-herdr-backend-contract-spike/herdr-backend-contract-spike-checklist.yaml`
- Design review: `.codestable/features/2026-07-31-herdr-backend-contract-spike/herdr-backend-contract-spike-design-review.md`
- Review: `.codestable/features/2026-07-31-herdr-backend-contract-spike/herdr-backend-contract-spike-review.md`
- QA: `.codestable/features/2026-07-31-herdr-backend-contract-spike/herdr-backend-contract-spike-qa.md`
- Acceptance: `.codestable/features/2026-07-31-herdr-backend-contract-spike/herdr-backend-contract-spike-acceptance.md`
- Depends on: `windows-x64-v852-baseline-gate`
- Nature: mixed
- Core runtime path: Herdr session/pane/send/capture/kill/restore and provider dry-run spike on Native Windows x64.
- Mandatory commands: approved checklist `dod.commands`.
- Evidence required: spike JSON, host evidence, Herdr schema/version ref, isolated server/socket evidence, route recommendation.
- Failure recovery: if minimum primitive fails, persist blocked evidence and stop downstream adapter route.
