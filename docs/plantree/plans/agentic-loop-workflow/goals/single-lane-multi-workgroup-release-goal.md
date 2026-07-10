# Single-Lane Multi-Workgroup Release Goal

Date: 2026-07-10
Status: Ready for implementation

## Goal

Ship the next CCB version only after one visible, frontdesk-started Workflow
Lane can execute a real macro task through multiple independently reviewed
workgroups and a controlled integration gate:

```text
frontdesk
  -> planner
  -> optional task_detailer
  -> one orchestrator bundle
  -> deterministic controller
  -> 1..4 (worker + reviewer) workgroups
  -> integration worktree and tests
  -> project-root promotion and verification
  -> ccb_round_reviewer
  -> script-owned task result
  -> complete dynamic release
```

The same release must add opt-in Config V3 for dynamic workflow role/provider/
model/capacity declaration, preserve Config V2 static behavior, and pass clean
package/install/update gates.

## Current Baseline

Already available and preserved:

- frontdesk-to-planner handoff, route selection, optional detailer, one-pair
  direct execution, bounded review/rework, round review, rollback, and release;
- durable ask submission intent, callback/persisted-terminal resume, and
  unknown-submission pause;
- dynamic role profiles, Git worktree substrate, mount-only topology,
  deterministic window placement, six-pane execution windows, overflow,
  busy-retain, release retry, and visible sidebar evidence;
- source/fake and real-provider single-workgroup evidence.

Blocking gaps:

- the direct engine still creates one hard-coded coder/reviewer pair;
- stage state, submission intent, result synthesis, and promotion are scalar;
- existing multi-node tests stop at mount/layout/release and do not execute one
  task through several reviewed workgroups;
- parallel workers cannot safely promote their deltas independently to the
  shared project root;
- no structured orchestration-bundle authority is imported and validated;
- `max_nodes` currently counts physical profile instances, not semantic
  workgroups;
- Config V3 is design-only and its older draft incorrectly treats immaculate
  roles as resident.

## Scope

- One project, one active Workflow Lane, one macro task, one loop round.
- One to four workgroups, each exactly one worker and one reviewer.
- Parallel, serial, and mixed acyclic dependency graphs.
- One bounded reviewer rework cycle per node by default.
- Git-worktree-isolated multi-workgroup execution and controller-owned
  integration.
- Exact-once event-driven ask submission and crash recovery.
- Visible window/pane placement, busy retain, full release, and residue audit.
- Config V3 parser/compiler/validator/migration dry-run and V2 regression.
- Source, fake-provider, real-provider, package, fresh-install, upgrade, and
  rollback verification.

## Non-Goals

- Concurrent Roadmap Graph lanes or multiple global planners.
- Multiple orchestrators for one bundle.
- Arbitrary user-authored workflow DSL or topology communication graph.
- Automatic semantic merge-conflict resolution.
- Non-Git multi-workgroup write execution in the first release.
- Long-running workflow daemon or unlimited rework.
- Default conversion of existing V2 projects to V3.
- Gemini release gating. Provider-specific claims for OpenCode or Grok require
  separate authenticated evidence and are not inferred from core Codex/Claude
  tests.

## Release Invariants

1. Provider replies are evidence, never task/topology/runtime authority.
2. Only scripts import bundle, node, integration, round, and task state.
3. Mount topology contains agents, windows, placement, lifecycle, and observed
   readiness only; no semantic dispatch DSL is reintroduced.
4. A reviewer never reviews an unpromoted shared-project guess. It reviews the
   exact node worktree tree digest later committed by the controller.
5. No node result enters integration before its reviewer passes.
6. No task reaches `done` before all required nodes, integration tests,
   project-root verification, and round review pass.
7. A partial, blocked, replan, unknown, or failed final result cannot leave an
   unaccepted promoted project-root delta.
8. Slow providers remain pending. Observer health limits may diagnose a broken
   runtime, but elapsed business time alone is not a task failure.
9. All dynamic immaculate roles release or produce bounded busy/residue
   evidence; resident frontdesk/planner remain visible.
10. V2 static config behavior remains byte/behavior compatible where the
    existing contract is defined.

## Implementation Phases

### G0 Contract And Baseline Freeze

- Land Decision 025, bundle schema, node/round state schema, result mapping,
  workspace/integration policy, V3 role lifecycle correction, and evidence
  contract.
- Freeze current one-workgroup tests and a V2 config corpus before source
  changes.
- Record the exact source test baseline and dirty/generated-file exclusions.

Gate: planning links resolve, schemas have rejection cases, and no core
behavior is left to implementation-time interpretation.

### G1 Bundle Authority And One-Node Generalization

- Add `ccb.loop.orchestration_bundle.v1` validation and script-owned import.
- Add a deterministic one-node bundle for the validated simple fast path.
- Replace scalar worker/reviewer stage state with a node map while preserving
  existing one-node external behavior.
- Remove the normal post-worker orchestrator aggregation call; retain fresh
  activation only for structural replan.

Gate: all current one-workgroup tests pass through the generalized engine and
provider replies still cannot write authority.

### G2 Worktree And Integration Kernel

- Add clean-Git/scope preflight, node worktree/branch creation, tree-digest
  capture, reviewer-pass commit, deterministic integration worktree, merge,
  test, project-root promotion, and rollback.
- Reject overlapping parallel scope claims, wrong-base workspaces, reviewer
  tree drift, merge conflicts, and project-root drift.

Gate: deterministic two-node synthetic tests prove disjoint merge, dependency
wave, conflict failure, rollback, and preservation of unrelated files.

### G3 Multi-Workgroup Scheduler And Lifecycle

- Submit all ready-frontier workers in one runner activation.
- Resume from callbacks or persisted terminal jobs without polling or business
  timeout.
- Submit each reviewer only after its worker; run bounded node-local rework;
  unblock dependents only after reviewed integration.
- Generalize topology, naming, placement, capacity, release, busy-retain, and
  residue evidence for one to four pairs plus dynamic control roles.

Gate: exact-once crash-window tests and fake-provider 2/3/4-workgroup flows
pass, including callback permutations and full cleanup.

### G4 Config V3

- Implement V3 version dispatch, models, validator, effective compiler,
  `config validate --json`, effective-config reporting, and migration dry-run.
- Require resident `frontdesk`/`planner`; require dynamic detailer,
  orchestrator, coder, code reviewer, and round reviewer profiles.
- Validate provider/model/RolePack/default resolution, workgroup/agent limits,
  profile maxima, Git-worktree multi-group policy, generated names, and
  forbidden V2/V3 field mixing.

Gate: V2 corpus is unchanged; valid V3 opens a generated dynamic project;
invalid V3 fails before provider or tmux startup.

### G5 Direct Source And Fake-Provider Acceptance

- Run focused unit/integration suites, full source suite, py_compile, static
  schema guards, source-wrapper smoke, and fake-provider matrix.
- Prove one-node compatibility plus 2, 3, and 4-workgroup task completion,
  rework, partial, blocked, replan, integration failure, restart recovery,
  busy retain, and release.

Gate: no skipped required case, no normalized false pass, no unbounded residue,
and no topology dispatch authority.

### G6 Visible Real-Provider Acceptance

- From `/home/bfly/yunwei/test_ccb2`, use the current source `ccb_test`, inherit
  system provider environment, use a lab-local Role store, and open a visible
  project/UI.
- Start with a natural user prompt to frontdesk and inspect every handoff.
- Run separate real tasks with two, three, and four workgroups. The four-group
  run is mandatory if V3 permits `max_workgroups = 4`.
- Prove actual worker overlap, per-node reviewer order, integration, tests,
  project-root output, round review, pane/sidebar state, and zero final dynamic
  residue.
- Restart ccbd during active work once and inject one provider/node failure in
  a separate run.

Gate: raw project/task/job/topology/Git/UI evidence agrees with B7. Scripts may
prepare and collect evidence but cannot substitute for the opened project.

### G7 Release Candidate And Publication

- Merge the accepted workflow branch into a clean release commit through the
  project branch policy; do not publish from a dirty worktree.
- Query the current npm version, choose the next unused SemVer feature release,
  synchronize package/version/changelog surfaces, and create the exact tag
  only after the commit is frozen.
- Run `npm pack --dry-run`, inspect contents, install the packed candidate into
  a fresh external prefix, verify `ccb`, `ask`, config V2, config V3, roles,
  and a visible installed-candidate workflow task.
- Test update from the current public stable version and a rollback to that
  version.
- Publish only to the explicitly confirmed registry/package/version, then
  verify registry metadata, fresh install, CLI entrypoints, payload download,
  tag, and release notes.

Gate: package name, version, registry, artifact hash, commit, tag, install
evidence, and explicit publication intent all agree.

## Required Real Tasks

Use inspectable tasks whose work units are independently meaningful but need a
final integration gate. At minimum:

- two groups: Python library core + CLI/tests;
- three groups: persistence/domain module + command/API module + documentation
  and integration tests;
- four groups: parser/model + storage + CLI + test/documentation integration,
  with at least one declared dependency wave.

Prompts must be ordinary product requests. They must not tell frontdesk how to
route, tell orchestrator how many groups to create, or tell providers which
test result to report.

## Acceptance Summary

The goal is complete only when:

- one-node behavior is regression clean;
- real 2/3/4-workgroup evidence exists for the advertised maximum;
- all required nodes are independently reviewed before integration;
- exact-once restart recovery and failure semantics are proven;
- project-root authority and rollback are correct;
- UI placement and dynamic release are visibly correct;
- V3 is implemented and validated while V2 remains compatible;
- a clean packed candidate installs and executes the same workflow externally;
- final release metadata is explicit and the publication is verified.

## Evidence

The canonical evidence fields and test matrix are defined in
[../topics/single-lane-multi-workgroup-modification-and-test-plan.md](../topics/single-lane-multi-workgroup-modification-and-test-plan.md).
Release evidence belongs under `history/` and must link to the exact commit,
config digest, package hash, project root, and raw runtime paths.
