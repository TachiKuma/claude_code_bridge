# windows-x64-release-surface

- Roadmap item: `windows-x64-release-surface`
- Design: `.codestable/features/2026-07-31-windows-x64-release-surface/windows-x64-release-surface-design.md`
- Checklist: `.codestable/features/2026-07-31-windows-x64-release-surface/windows-x64-release-surface-checklist.yaml`
- Design review: `.codestable/features/2026-07-31-windows-x64-release-surface/windows-x64-release-surface-design-review.md`
- Review: `.codestable/features/2026-07-31-windows-x64-release-surface/windows-x64-release-surface-review.md`
- QA: `.codestable/features/2026-07-31-windows-x64-release-surface/windows-x64-release-surface-qa.md`
- Acceptance: `.codestable/features/2026-07-31-windows-x64-release-surface/windows-x64-release-surface-acceptance.md`
- Depends on: `windows-x64-v852-baseline-gate`, `herdr-user-surfaces-parity`
- Nature: mixed
- Core runtime path: npm/install/update/native helper/managed Python release surface and Windows dry-run evidence.
- Mandatory commands: approved checklist `dod.commands`, including `npm pack --dry-run` and Windows `npm install` dry-run where applicable.
- Evidence required: release surface projection, package metadata gate, source install preservation, doctor/docs guard, scope guard.
- Failure recovery: no npm publish, release, promotion or push.
