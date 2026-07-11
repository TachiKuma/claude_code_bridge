# Agentic Loop Workflow Implementation Status

Date: 2026-07-11
Status: In progress
Branch: `workflow/agentic-loop-topology`
Worktree: `/home/bfly/yunwei/ccb_worktrees/agentic-loop-topology`

## Current Phase

The active release target is single-lane production closure: one visible frontdesk-started task lane with
one semantic orchestration bundle and one to four independently reviewed
`Worker + Reviewer` workgroups. Multi-lane Roadmap scheduling remains out of
scope.

G0-G4 source implementation is complete. Wave 3 landed the controller-owned
G3 ready-frontier scheduler, real R2 Git transactions, T1 topology authority,
crash recovery, strict release, and runtime accelerator ownership. The current
phase is G5 direct source/fake acceptance. This is an acceptance phase, not a
claim that live multi-workgroup providers or Config V3 opened projects pass.

## Authority

- Goal and waves:
  [goals/single-lane-multi-workgroup-release-goal.md](goals/single-lane-multi-workgroup-release-goal.md)
- Detailed contracts and tests:
  [topics/single-lane-multi-workgroup-modification-and-test-plan.md](topics/single-lane-multi-workgroup-modification-and-test-plan.md)
- Accepted boundary:
  [decisions/025-single-lane-multi-workgroup-release-gate.md](decisions/025-single-lane-multi-workgroup-release-gate.md)
- Frozen interfaces:
  [decisions/026-authority-envelope-and-adaptive-workgroup-selection.md](decisions/026-authority-envelope-and-adaptive-workgroup-selection.md)

Provider replies remain evidence only. Scripts own bundle, task, node,
integration, topology, round, and release authority. Mount topology remains
physical placement/lifecycle state, not a semantic dispatch graph.

## Last Landed

- `8d3fc102`: multi-workgroup scheduler and durable node state machine.
- `92da3faf`: full-frontier auto-advance, exact-once/rework/result/release fixes.
- `bca51abd`: scheduler binding to real R2 and raw T1 topology authority.
- `fb4b26c7`: explicit phase2 test-runtime ownership and bounded cleanup.
- `96172d92`: persisted runtime accelerator ownership and safe takeover.
- `94ea6d73`: fail-closed accelerator recovery and corrupt-authority handling.

Wave 3 evidence:
[history/single-lane-wave3-g3-scheduler-closure-20260711.md](history/single-lane-wave3-g3-scheduler-closure-20260711.md).

Earlier accepted checkpoints remain in the G1, R1, Wave 1, and Wave 2 history
records linked from the goal, including
[history/single-lane-r1-authority-runtime-closure-20260711.md](history/single-lane-r1-authority-runtime-closure-20260711.md).

## Next Target

Run G5 directly from this integrated branch: prove one-node compatibility and
real scheduler-driven two-, three-, and four-workgroup fake/source flows,
including restart, bounded rework, partial, blocked, replan, integration
failure, busy-retain, release, and E1/B7 agreement.

## Execution Queue

- Waves 0-3, complete: F1, R1, C1/P1, R2/T1/E1, and G3 are integrated.
- G5, active: direct source/fake full-flow acceptance owned by `talk2`.
- G6, gated: visible opened-project Codex/Claude acceptance.
- G7, gated: package/install/update/rollback readiness.
- G8, separate: publication requires explicit user authorization.

## Active TODO

1. Inventory existing source/fake harnesses and freeze the executable G5 case matrix.
2. Run one-node compatibility plus two-, three-, and four-workgroup full flows.
3. Run crash/restart, rework, failure, rollback, busy-retain, and release cases.
4. Normalize raw evidence through E1 and reject any false pass or residue mismatch.
5. Open fresh visible real-provider roots only after the G5 matrix passes.

## Blocked By

No external dependency blocks G5. G6, packaging, default enablement, and
publication remain intentionally gated by direct G5 evidence.

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

## Non-Claims

The branch is not production-ready. G3 source closure does not prove fake-provider full-flow acceptance, a visible
real multi-workgroup project, Config V3 opened-project behavior, packaged
candidate behavior, production/default enablement, or publication. Those
claims remain behind G5-G8.

The bounded earlier Phase 1-6 claim remains archived in
[history/phase1-6-acceptance-report-20260705.md](history/phase1-6-acceptance-report-20260705.md).
