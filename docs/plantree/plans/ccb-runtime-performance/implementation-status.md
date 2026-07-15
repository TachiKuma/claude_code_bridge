# Implementation Status

Date: 2026-07-15

## Current Phase

P0-P3 core implementation and Linux source-runtime validation are complete for
the reported 20-second startup path. The false explicit multi-window relaunch
defect is fixed, provider preparation is reuse-aware and exactly once for actual
launches, global tmux/process observations are request-scoped, unchanged pane
identity and durable records are not rewritten, and startup timings are visible
through the persisted report and `doctor`.

The implementation sequence, invariants, SLOs, test matrix, and rollback rules
are recorded in
[topics/startup-critical-path-optimization-2026-07-15.md](topics/startup-critical-path-optimization-2026-07-15.md).

## Active TODO

- Add remaining P0 counters for tmux commands, process snapshots, projection
  file/byte scans, and durable writes if production diagnostics need them.
- Run equivalent warm/cold baselines on macOS and WSL, especially mounted-drive
  metadata paths.
- Qualify real Codex and Claude provider starts separately from the completed
  deterministic Codex-stub runtime test.
- Decide P4 provider-specific concurrency limits only from cold-start evidence;
  do not enable unbounded parallel startup.

## Blockers

- No implementation blocker remains for the landed P0-P3 core.
- Final provider concurrency caps and slow-filesystem SLOs remain evidence
  dependent and do not block the correctness fix.

## Last Landed

- `af2818d Add runtime performance profiling and latency fast paths`: lifecycle
  profiling harness, detached tmux prepare cache, project_focus fast path,
  pending sidebar-refresh support, tests, and plan evidence.
- `4347082 Optimize project view recent job scans`: pure Python adaptive
  ProjectView recent-job scanning through `JobStore.list_project_view_recent_jobs`,
  preserving the old per-agent maximum scan limit while reducing common-case
  initial reads.

## Next Commit Target

Package only the reviewed startup files, contracts, tests, and runtime
performance PlanTree updates. Keep unrelated dirty worktree changes out. P4
concurrency and P5 readiness remain separate future changes.

## Last Verified

- Isolated source-runtime project:
  `/home/bfly/yunwei/test_ccb2/startup-perf-talk1-20260715` with 5 explicit
  windows, 10 Codex-stub agents, isolated `HOME` / `CCB_SOURCE_HOME`, and the
  absolute source `ccb_test` wrapper.
- Cold start after clean kill: `2.20s`. Twenty unchanged warm starts ranged
  from `0.52s` to `0.64s`, p50 about `0.555s`, p95 `0.63s`.
- Warm report proved 10 `attached`, zero relaunches, zero provider preparation,
  actual tmux window ids `@0` through `@4`, and no repeated pane relabel actions.
- `doctor` surfaced `startup_last_timings_ms` and
  `startup_last_provider_prepare_count=0`.
- Focused changed-surface regression: `322 passed`.
- Full Python run: `5069 passed, 2 skipped`, then one restore-contract failure.
  The failure was corrected and its black-box test plus impacted startup tests
  passed (`8 passed`); the broader changed-surface matrix passed afterward.
- `git diff --check` passed.
- 2026-07-15 static startup trace covered `start_flow_runtime`,
  `start_preparation`, binding matching, topology health assessment, provider
  preparation/materialization, Codex live identity, tmux topology discovery,
  and durable runtime stores.
- Read-only live facts confirmed an explicit five-window layout with entry
  window `@0` and managed panes in `@0` through `@4`, while project state holds
  only one `workspace_window_id`.
- The inherited Codex plugin projection source contained about 5,279 files and
  87 MB, confirming that repeated scans/copies have material amplification.
- Source runtime profile artifact:
  `/tmp/perf_realtarget/real_provider_cpu_profile_accurate3.json`
- Worker1 harness review:
  `python -m pytest -q test/test_perf_runtime_lifecycle_profile.py`
  passed with `11 passed`.
- Worker1 smoke checks from `/home/bfly/yunwei/test_ccb2`:
  `/tmp/ccb_runtime_profile_startup_diagnose_scoped.json` and
  `/tmp/ccb_runtime_profile_load_sleep_scoped.json`.
- Worker2/main tmux prepare cache review:
  `PYTHONPATH=lib python -m pytest -q
  test/test_cli_runtime_launch_tmux_panes.py test/test_v2_runtime_launch.py -q`
  passed.
- Main focus fast-path review:
  `PYTHONPATH=lib python -m pytest -q
  test/test_ccbd_project_focus.py test/test_sidebar_click.py` passed with
  `15 passed`.
- Combined targeted regression:
  `PYTHONPATH=lib python -m pytest -q
  test/test_perf_runtime_lifecycle_profile.py
  test/test_cli_runtime_launch_tmux_panes.py test/test_v2_runtime_launch.py
  test/test_ccbd_project_focus.py test/test_sidebar_click.py` passed with
  `117 passed`.
- Project_view dirty-state regression:
  `PYTHONPATH=lib python -m pytest -q
  test/test_ccbd_project_view.py test/test_ccbd_service_graph.py` passed with
  `65 passed`; this verifies current consistency but does not accept worker3's
  mismatched project_view/Rust-helper slice.
- Project_view pending-refresh blocker fix:
  `PYTHONPATH=lib python -m pytest -q
  test/test_ccbd_project_focus.py test/test_sidebar_click.py
  test/test_ccbd_project_view.py test/test_ccbd_service_graph.py` passed with
  `81 passed`.
- Final targeted regression:
  `PYTHONPATH=lib python -m pytest -q
  test/test_perf_runtime_lifecycle_profile.py
  test/test_cli_runtime_launch_tmux_panes.py test/test_v2_runtime_launch.py
  test/test_ccbd_project_focus.py test/test_sidebar_click.py
  test/test_ccbd_project_view.py test/test_ccbd_service_graph.py` passed with
  `183 passed`.
- Sidebar single-RPC working-tree slice:
  `PYTHONPATH=lib python -m pytest -q test/test_sidebar_click.py
  test/test_ccbd_socket_client.py test/test_ccbd_service_graph.py` passed with
  `27 passed`; `python -m py_compile
  dev_tools/perf_sidebar_click_latency.py` passed; `git diff --check` passed
  for the touched sidebar/RPC/test/plan paths.
- Source wrapper smoke after runtime helper change:
  `/home/bfly/yunwei/ccb_source/ccb_test --diagnose` and
  `ccb_test config validate` passed from `/home/bfly/yunwei/test_ccb2`.
- Shell/system bucket split:
  `PYTHONPATH=lib python -m pytest -q test/test_perf_runtime_lifecycle_profile.py`
  passed with `12 passed`; `python -m py_compile
  dev_tools/perf_runtime_lifecycle_profile.py
  test/test_perf_runtime_lifecycle_profile.py` passed.
  High-load artifact: `/tmp/ccb_runtime_shellsplit_profile_v2.json`.
  Startup artifact: `/tmp/ccb_runtime_shellsplit_startup_profile.json`.
- Worker report artifact:
  `.ccb/ccbd/artifacts/text/completion-reply/job_21a7c0c0b62a-art_19c8d2c809734472.txt`
- Rust helper benchmark evidence remains in
  `dev_tools/perf_results/python_rust_phase3_native_output_helper.json`,
  `python_rust_phase4_storage_scan_helper.json`, and
  `python_rust_phase12_storage_summary_helper.json`.

## Execution Notes

- `talk1` owns analysis, implementation, and verification directly for this
  workstream. Do not dispatch worker agents unless the user explicitly changes
  that instruction.
- Source runtime validation must run from `/home/bfly/yunwei/test_ccb2` with
  `/home/bfly/yunwei/ccb_source/ccb_test` and isolated `HOME` /
  `CCB_SOURCE_HOME`.
- Do not use the source checkout as a live runtime directory and do not mutate
  its installed-release `.ccb` runtime state during source validation.
