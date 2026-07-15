# Open Questions

Date: 2026-07-15

## Resolved

- Logical-window authority remains in config plus pane identity; generation
  window ids are derived from the request-scoped tmux snapshot and are not
  duplicated into a new `managed_windows` authority map.

## Open

1. What provider-specific concurrency caps satisfy cold-start speed without
   unacceptable CPU, memory, auth, or session contention?
2. After Linux, macOS, and WSL baselines exist, what p50/p95 budgets should
   replace the initial startup targets?
3. Should foreground-first/background-warm readiness remain opt-in or become
   the default after the unchanged eager-mount path meets its own SLO?
4. What are the target p50/p95 budgets for click-to-pane-focus and
   click-to-stable-sidebar-refresh?
5. Should high-throughput `ask` workloads use a persistent client/forwarder, or
   should the CLI remain process-per-call with lower-level batching only?
