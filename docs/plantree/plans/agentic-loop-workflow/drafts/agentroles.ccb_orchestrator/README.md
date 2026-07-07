# CCB Loop Orchestrator Draft

This draft materializes the first `agentroles.ccb_orchestrator` RolePack for
the agentic loop plan. It is intentionally narrow: the role returns semantic
routes, capacity recommendations, ask drafts, aggregation notes, and
release-readiness evidence. It cannot run CCB commands or mutate config,
runtime files, tmux, provider sessions, or daemon state directly.

Primary references:

- capacity recommendations describe profile counts and blockers for the
  supervisor/runner to apply;
- worker/reviewer ask drafts use runner-provided agent names only;
- aggregation notes cite worker/reviewer evidence and report release readiness
  without invoking runtime commands.

This draft is installable by path for source tests, but it is not a published
Agent Roles catalog entry.
