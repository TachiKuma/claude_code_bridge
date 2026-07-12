# Agentic Loop Workflow Implementation Status

Date: 2026-07-12
Status: In progress
Branch: `workflow/agentic-loop-topology`
Worktree: `/home/bfly/yunwei/ccb_worktrees/agentic-loop-topology`

## Current Phase

The active release target is single-lane production closure: one visible frontdesk-started task lane with
one semantic orchestration bundle and one to four independently reviewed
`Worker + Reviewer` workgroups. Multi-lane Roadmap scheduling remains out of
scope.

G0-G5 source/fake scope is complete. Wave 3 landed the controller-owned G3
ready-frontier scheduler, real R2 Git transactions, T1 topology authority,
crash recovery, strict release, and runtime accelerator ownership. G5 then
proved the integrated scheduler through one-to-four-workgroup source/fake
runtime flows. Decision 027 and a visible two-workgroup Codex baseline now pass
in G6. Decision 028 is also real-provider verified, including an exact
Frontdesk-owned silent Planner handoff and genuine bounded rework in both
workgroups. A follow-up long-root real-provider run additionally proves that
successful silence produces no caller delivery, managed MCP callers honor the
mounted lease socket, isolated Workers read project-root PlanTree authority,
and compact inline Round Reviewer evidence closes the round. The remaining
phase is the broader visible real-provider matrix:
three/four workgroups, in-flight restart, busy-retain, and provider-profile
qualification. This is not yet a packaged-candidate or default-enablement
claim.

## Authority

- Goal and waves:
  [goals/single-lane-multi-workgroup-release-goal.md](goals/single-lane-multi-workgroup-release-goal.md)
- Detailed contracts and tests:
  [topics/single-lane-multi-workgroup-modification-and-test-plan.md](topics/single-lane-multi-workgroup-modification-and-test-plan.md)
- Accepted boundary:
  [decisions/025-single-lane-multi-workgroup-release-gate.md](decisions/025-single-lane-multi-workgroup-release-gate.md)
- Frozen interfaces:
  [decisions/026-authority-envelope-and-adaptive-workgroup-selection.md](decisions/026-authority-envelope-and-adaptive-workgroup-selection.md)
- Worker-owned review and minimal controller:
  [decisions/027-worker-owned-review-chain-and-minimal-controller.md](decisions/027-worker-owned-review-chain-and-minimal-controller.md)
- Frontdesk-owned Planner silence handoff:
  [decisions/028-frontdesk-owned-planner-silence-handoff.md](decisions/028-frontdesk-owned-planner-silence-handoff.md)

Provider replies remain evidence only. Scripts own bundle, task, node,
integration, topology, round, and release authority. Mount topology remains
physical placement/lifecycle state, not a semantic dispatch graph.
Decision 027 now supersedes the controller-owned Reviewer/rework relay:
Workers must collaborate directly with their assigned Reviewer through a
bounded restricted chain, while the controller validates lineage and retains
only mechanical authority.
Decision 028 likewise supersedes the Controller-observed Frontdesk semantic
relay: Frontdesk authors one silent Planner ask; Controller code only validates,
deduplicates, records activation, and wakes or recovers the runner.

## Last Landed

- `8d3fc102`: multi-workgroup scheduler and durable node state machine.
- `92da3faf`: full-frontier auto-advance, exact-once/rework/result/release fixes.
- `bca51abd`: scheduler binding to real R2 and raw T1 topology authority.
- `fb4b26c7`: explicit phase2 test-runtime ownership and bounded cleanup.
- `96172d92`: persisted runtime accelerator ownership and safe takeover.
- `94ea6d73`: fail-closed accelerator recovery and corrupt-authority handling.
- `5163ad6f`: G5 source/fake runtime campaign harness and ten-scenario matrix.
- `9fceb5de`: terminal failed workgroup quarantine, restore, and R2 exclusion.
- `b42ec3b2`: project-bound recovery of spilled G5 fake-provider contracts.
- `8f9b62f2`: Frontdesk-owned Planner silent handoff and minimal Controller
  boundary.
- `6646f6a3`: successful-silence delivery suppression, mounted-lease socket
  authority, absolute Worker authority refs, and compact round evidence.

Wave 3 evidence:
[history/single-lane-wave3-g3-scheduler-closure-20260711.md](history/single-lane-wave3-g3-scheduler-closure-20260711.md).

G5 evidence:
[history/single-lane-g5-source-fake-acceptance-20260711.md](history/single-lane-g5-source-fake-acceptance-20260711.md).

Decision 027 real-provider checkpoint:
[history/g6-worker-owned-review-chain-real-provider-20260712.md](history/g6-worker-owned-review-chain-real-provider-20260712.md).

Decision 028 direct-handoff and real-rework checkpoint:
[history/decision028-frontdesk-direct-handoff-real-provider-20260712.md](history/decision028-frontdesk-direct-handoff-real-provider-20260712.md).

Earlier accepted checkpoints remain in the G1, R1, Wave 1, and Wave 2 history
records linked from the goal, including
[history/single-lane-r1-authority-runtime-closure-20260711.md](history/single-lane-r1-authority-runtime-closure-20260711.md).

## Next Target

Complete the remaining G6 rows: three/four workgroups, real overlap, in-flight
restart, busy-retain, and strict provider-profile qualification. Preserve the
accepted Decision 027/028 Codex baselines and aggregate raw evidence into B7
without normalizing protocol failures.

## Execution Queue

- Waves 0-3, complete: F1, R1, C1/P1, R2/T1/E1, and G3 are integrated.
- G5, complete: direct source/fake full-flow acceptance owned by `talk2`.
- G6, active: two-workgroup Codex baseline passed; remaining visible matrix
  and provider-profile qualification pending.
- G7, gated: package/install/update/rollback readiness.
- G8, separate: publication requires explicit user authorization.

## Active TODO

1. Run frontdesk-started three- and four-workgroup natural tasks proving real
   overlap, Worker-owned Reviewer order, deterministic integration, root
   output, sidebar/window evidence, and zero residue.
2. Run a separate restart/failure G6 scenario covering durable intent replay,
   node failure, rollback/busy-retain behavior, and cleanup. Real bounded
   Reviewer rework is already proven in both nodes of the Decision 028 run.
3. Qualify each claimed provider/profile against the strict first-line role
   protocol; retain non-compliant rows as non-success.
4. Normalize and audit raw task/job/topology/Git/UI evidence against B7 before
   accepting any real-provider row.

## Blocked By

No external dependency blocks G6 beyond live provider availability. Packaging,
default enablement, and publication remain intentionally gated by G6/G7
evidence and explicit user authorization.

## Validation And Acceptance

Workers may implement bounded repairs, but `talk2` directly runs and audits
acceptance. Visible real validation must use fresh projects under
`/home/bfly/yunwei/test_ccb2`, explicit source `ccb_test`, inherited provider
environment, a project-local `AGENT_ROLES_STORE`, and an inspectable separate
terminal/UI. Script output cannot substitute for opened-project evidence.

## Last Verified

- G3 plus Wave 2 adjacent scheduler/integration gate: `495 passed`.
- Full non-provider-blackbox repository gate: `4210 passed, 2 skipped, 21 deselected`.
- Current-run command-line residue: `0`; cwd-owned runtime residue: `0`.
- Runtime accelerator count was conserved across the full gate: `6 -> 6`.
- Changed-source `py_compile`, `pyflakes`, and `git diff --check`: passed.
- G5 final source/fake campaign:
  `/home/bfly/yunwei/test_ccb2/talk2-g5-final-20260711130355-evidence`,
  campaign status `pass`, row count `10`, B7 SHA256
  `b228c8a550580d4e1f0e2f72339aeb3972102f4efaeefb9313dd95e83f7ff806`.
- Integrated G5 branch checks: `test_single_lane_multi_workgroup_smoke.py`
  `37 passed`; G5 adjacent scheduler/R2/Phase6/campaign suite `126 passed`;
  changed-source `py_compile`, `pyflakes`, `git diff --check`, and narrow
  residue scans passed.
- Post-G5 full non-provider-blackbox gate:
  `4263 passed, 2 skipped, 21 deselected in 569.98s`. No current pytest-root
  runtime process remained; five pytest socket files were not connectable.
- Decision 027 visible Codex checkpoint: two mixed-DAG nodes integrated,
  Worker root jobs `job_f2ed8ef562ba` and `job_889b4e0bb44e` each created one
  Reviewer chain child, Round Reviewer returned `pass`, project-root unittest
  discovery passed `79` tests, post-round dynamic/retained/incomplete counts
  were `0/0/0`, and project-level shutdown left no process or socket residue.
- Post-checkpoint focused gate: Worker-owned scheduler/RolePack/smoke/ask/
  dispatcher bundle `274 passed`; adjacent capacity/task/topology/RolePack
  bundle `294 passed`; dispatcher/callback bundle `112 passed`; ask service
  `44 passed`.
- Final non-provider-blackbox repository gate: `4306 passed, 2 skipped,
  21 deselected in 707.09s`. Its pytest root left no process or socket
  residue. The accepted G6 project and one discovered stale 2026-07-10 test
  project were both closed with project-level `ccb_test kill -f`; no runtime
  owned by this workflow worktree remained.
- Decision 028 visible Codex checkpoint: Frontdesk job `job_6c88e4472b20`
  submitted exactly one silent Planner job `job_2584ecf35c46`; two parallel
  workgroups each received one real `rework_required` and one passing recheck;
  root verification passed `7` tests; Round Reviewer `job_8a99582b80cd`
  passed; task authority ended `done/pass`; all dynamic panes, agents,
  worktrees, and temporary branches were removed; project-level shutdown left
  no process or socket residue.
- Decision 028 affected source gate: `393 passed`; accelerator/CLI regression
  gate `30 passed`; former heartbeat race `10/10 passed`; final full
  non-provider-blackbox repository gate `4321 passed, 2 skipped, 21 deselected
  in 642.29s`. Post-suite workflow/pytest process and socket scans were empty.
- Decision 028 closure follow-up: long-root project
  `decision028-silence-round-inline-final4-20260712085421` completed
  Frontdesk -> silent Planner -> Orchestrator -> Worker-owned Reviewer chain ->
  Git integration -> compact inline Round Reviewer -> task result -> release.
  Root verification passed `13` tests; final dynamic/retained/incomplete counts
  were `0/0/0`; project shutdown left no related process residue.
- Closure source gates: complete G5 real-CLI/fake-runtime matrix `39 passed`;
  final non-provider-blackbox repository gate `4324 passed, 2 skipped,
  21 deselected in 671.99s`; changed-source `py_compile`, `pyflakes`, and
  `git diff --check` passed.

## Non-Claims

The branch is not production-ready. The accepted two-workgroup Codex rows do
not prove the complete three/four-group, restart, busy-retain, or
cross-provider G6 matrix, packaged candidate behavior, production/default
enablement, or publication. Those claims remain behind G6-G8.

The bounded earlier Phase 1-6 claim remains archived in
[history/phase1-6-acceptance-report-20260705.md](history/phase1-6-acceptance-report-20260705.md).
