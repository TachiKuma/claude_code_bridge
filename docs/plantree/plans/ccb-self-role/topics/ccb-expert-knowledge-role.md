# CCB Expert Knowledge Role

Date: 2026-06-10

## Direction

`ccb_self` should become the project-local CCB expert, not only a runtime
maintenance operator.

The role should be able to quickly answer or resolve CCB-related questions
across:

- runtime health, mailbox, pane, provider, config, and recovery;
- CCB source architecture and module ownership;
- command usage, config grammar, role binding, and common workflows;
- new feature behavior, release status, validation gates, and plan-to-code
  traceability;
- CCB-owned pane text/visual state when self-supervision needs to see the real
  provider/tool UI, not only control-plane summaries.

This expands knowledge and guidance authority. It does not make `ccb_self`
daemon authority, lifecycle authority, or business-task owner.

## Current Gap

The current Role Pack is strong at maintenance:

- `ccb-self-diagnose`
- `ccb-self-recover`
- `ccb-self-chain`
- `ccb-comm-reply-recover`
- `ccb-config`

It is still weak at expert CCB knowledge:

- no source/module navigation skill;
- no command/usage explanation skill;
- no new-feature/release-awareness workflow;
- no compact CCB architecture reference package;
- no dedicated CCB-owned pane-view self-supervision skill;
- no knowledge-refresh discipline after features land.

## Capability Model

### Maintenance Skills

Keep the existing maintenance skills. They own repair workflows and should not
be diluted with broad product documentation.

### Expert Skills

Add a small set of broad expert skills:

- `ccb-architecture-navigator`: answer "where is this implemented", "how does
  this flow work", "which contract governs this", and "what test proves it".
- `ccb-feature-usage`: answer "how do I use this command/config/feature" from
  CLI source, docs, and tests, with concrete examples and file references.
- `ccb-release-update-awareness`: answer "what changed", "is this feature
  landed", "is this in the current release line", and "what validation gate
  applies" from git, plan-tree, release docs, and tests.
- `ccb-pane-view-diagnose`: analyze CCB-owned pane text captures, especially
  bottom/current prompt content, with screenshot fallback for visual/layout
  ambiguity after control-plane target resolution.

Do not create a separate skill for every CCB subsystem. Use references to
route domain-specific detail.

### Expert References

Add concise reference indexes to the Role Pack. They should point to canonical
source files, docs, and tests instead of copying long implementation detail.

Recommended references:

- `references/ccb-source-map.md`: repo module map and ownership boundaries.
- `references/ccb-command-surface.md`: CLI command groups, config surfaces,
  and usage evidence paths.
- `references/ccb-runtime-flows.md`: ccbd, keeper, ask/reply, mailbox,
  provider, pane, heartbeat, restart, and reload flows.
- `references/ccb-role-and-config-system.md`: role packs, projection,
  `.ccb/ccb.config`, reload, restart impact, and config authority.
- `references/ccb-release-and-test-gates.md`: release phases, CI gates,
  source `ccb_test` discipline, and real-runtime validation paths.
- `references/ccb-knowledge-refresh.md`: how the role refreshes expert
  references after source changes land.

## Answering Rules

When acting as a CCB expert, `ccb_self` should:

- inspect local source/docs/tests before answering unstable or specific CCB
  behavior questions;
- cite concrete files and commands when giving architecture, usage, or release
  answers;
- distinguish live runtime authority, source implementation, documented
  contract, plan-tree intent, and stale residue;
- say when a feature is planned, implemented, tested, released, or merely
  present in a dirty local branch;
- prefer local repo evidence over memory;
- avoid broad refactors or implementation takeover unless the user explicitly
  asks for coding work.

## Knowledge Refresh

Refresh should be explicit and cheap in v1.

Triggers:

- user asks `ccb_self` to refresh CCB knowledge;
- a CCB feature lands or is pushed;
- release validation completes;
- heartbeat or maintenance diagnosis reveals a new recurring failure class;
- role assets are updated.

Inputs:

- `git diff`, `git log`, changed files, and commit ids;
- docs and plan-tree status;
- tests added or changed;
- release/check output;
- runtime incident artifacts when relevant.

Outputs:

- updated expert reference indexes;
- updated role memory only when identity or hard boundaries change;
- updated skills only when the workflow itself changes;
- a short evidence note with commit/test references.

## V1 Slice

First implement a narrow expert upgrade:

1. Update Role identity wording from pure "maintenance operator" to
   "CCB runtime and architecture expert".
2. Add `ccb-architecture-navigator`.
3. Add `ccb-pane-view-diagnose` and make it the text-capture-first assessor
   path for ambiguous running-supervision incidents.
4. Add `ccb-source-map.md` and `ccb-command-surface.md`.
5. Update tests so the Role manifests the new skills/references and
   distributable text stays free of local source paths.
6. Validate with prompt-style checks:
   - locate a CLI command implementation and tests;
   - explain an ask/reply failure path;
   - explain a config reload versus restart impact;
   - identify whether a newly landed feature is implemented and tested;
   - classify a CCB-owned screenshot as visual evidence, not authority.

## Later Slices

- Add `ccb-feature-usage`.
- Add `ccb-release-update-awareness`.
- Add `ccb-knowledge-refresh` as either a skill or helper command.
- Add structured MCP helpers for source/command lookup after the manual
  reference model proves useful.
- Consider a compact local generated index only after manual references become
  too slow or too stale.

## Risks

- Context bloat: mitigate with reference indexes and progressive disclosure.
- Stale expert docs: mitigate with explicit knowledge-refresh triggers and
  validation checks.
- Authority confusion: keep runtime/source/plan/release distinctions explicit.
- Overreach into business work: keep "CCB expert" scoped to CCB itself and
  require explicit user intent for feature implementation.
- Screenshot privacy: restrict fallback screenshot/visual inspection to
  CCB-owned panes/windows, prefer text capture when it is enough, and avoid
  quoting sensitive UI text.

## Acceptance Criteria

- A fresh `ccb_self` session can answer common CCB architecture and usage
  questions with file-backed evidence.
- The Role Pack has a clear expert knowledge package without duplicating the
  whole repo into memory.
- New CCB functionality has a documented refresh path into `ccb_self` expert
  references.
- Maintenance repair skills remain separate and usable.
- Pane-view diagnosis is available for self-supervision, remains bounded to
  CCB-owned surfaces, and keeps evidence-only semantics.
