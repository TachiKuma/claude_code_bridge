# Roadmap

Date: 2026-07-15

## Done

- Captured a real lifecycle CPU profile from an isolated source runtime under
  `/home/bfly/yunwei/test_ccb2` using `/home/bfly/yunwei/ccb_source/ccb_test`.
  Evidence:
  [history/real-lifecycle-cpu-profile-2026-06-16.md](history/real-lifecycle-cpu-profile-2026-06-16.md).
- Confirmed the currently landed Rust helpers improve local paths but do not
  explain the dominant lifecycle CPU share in the sampled workload.
- Established the current optimization priority: shell/tmux/subprocess
  orchestration first, then provider lifecycle policy, then CCB core only if it
  remains above the agreed threshold after those reductions.
- Added a repeatable lifecycle profiling harness and reviewed it for
  source-runtime-safe invocation and project-scoped process attribution.
- Added a low-risk detached tmux prepare cache keyed by socket identity and
  environment fingerprint.
- Added a narrow project_focus fast path that queues sidebar refresh through
  project_view when available, while preserving synchronous refresh fallback.
- Fixed the pending sidebar-refresh crash exposed by that fast path by adding
  the missing project_view refresh metrics helper and regression coverage.
- Split the previous `shell-system` bucket with corrected project-scoped
  profiling. Evidence:
  [history/shell-system-bucket-split-2026-06-16.md](history/shell-system-bucket-split-2026-06-16.md).
  High-load submission CPU is dominated by `ask-cli-subprocess`; startup CPU is
  dominated by provider launch/mount, not tmux server work.
- Added a working-tree interactive-latency slice for sidebar clicks:
  `ccb __sidebar-click` can now focus through one daemon RPC
  (`project_sidebar_click`) instead of a CLI-side `project_view` request
  followed by a second focus request, with old-daemon fallback preserved.
- Added `dev_tools/perf_sidebar_click_latency.py` as a focused single-RPC
  latency probe for live daemon socket measurements.
- Fixed explicit multi-window startup binding so logical window and namespace
  epoch determine reuse while actual tmux window ids remain runtime facts.
- Enforced zero provider preparation for reuse and one preparation pass for
  launch/relaunch, including one Codex managed-home projection per launch.
- Added request-scoped tmux and Codex process snapshots, tmux pane-identity
  batching, unchanged-identity suppression, and scoped no-op persistence.
- Added persisted startup stage/per-agent timings and surfaced them through
  `doctor`.
- Validated a 5-window, 10-agent isolated source runtime: 20 warm starts had
  p50 about `0.555s`, p95 `0.63s`, 10/10 attaches, zero relaunches, and zero
  provider preparation.

## In Progress

- Cross-platform and real-provider qualification of the completed startup
  critical-path implementation.
- Remaining optional P0 counters and decision evidence for bounded cold-launch
  concurrency.

## Next

1. Add remaining tmux/process/projection/write counters if production evidence
   shows stage timings alone are insufficient.
2. Run macOS, WSL ext4, and WSL mounted-drive warm/cold baselines.
3. Run exact real Codex primary and Claude cross-provider qualification.
4. Add measured, bounded provider-launch concurrency only after the serial
   authority stages are explicit.
5. Evaluate foreground-first readiness as a separate opt-in policy after the
   current startup semantics meet their performance and reliability gates.
6. Resume persistent/batched ask and interactive-latency work after the startup
   regression is isolated and accepted.

## Deferred

- Full CCB core rewrite or broad Rust migration.
- Provider CLI internal optimization.
- Default-enabling opt-in Rust storage summary without broader fixture evidence.
