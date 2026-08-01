# herdr-backend-client

- Roadmap item: `herdr-backend-client`
- Design: `.codestable/features/2026-07-31-herdr-backend-client/herdr-backend-client-design.md`
- Checklist: `.codestable/features/2026-07-31-herdr-backend-client/herdr-backend-client-checklist.yaml`
- Design review: `.codestable/features/2026-07-31-herdr-backend-client/herdr-backend-client-design-review.md`
- Review: `.codestable/features/2026-07-31-herdr-backend-client/herdr-backend-client-review.md`
- QA: `.codestable/features/2026-07-31-herdr-backend-client/herdr-backend-client-qa.md`
- Acceptance: `.codestable/features/2026-07-31-herdr-backend-client/herdr-backend-client-acceptance.md`
- Depends on: `mux-backend-contract-herdr-v2`
- Nature: mixed
- Core runtime path: Herdr socket client, schema/version gate, capability gate and resolver/factory route.
- Mandatory commands: approved checklist `dod.commands`.
- Evidence required: client unit tests, schema mismatch fixtures, capability report, fail-closed diagnostics.
- Failure recovery: fix adapter boundary without leaking raw Herdr JSON into callers.
