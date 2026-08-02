# windows-native-herdr-ccb Goal Plan

## Scope

- Roadmap: `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-roadmap.md`
- Items: `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml`
- Baseline ref: `a097e64bb53650582dba2a16964802173eda05e1`
- Requirement: `.codestable/requirements/native-windows-ccb-via-herdr.md`

## Feature Order

1. `windows-x64-v852-baseline-gate` - mixed - strict CCB `v8.5.2` source/new branch and Native Windows x64 gate.
2. `herdr-backend-contract-spike` - mixed - Herdr session/pane/send/capture/kill/restore spike evidence.
3. `mux-backend-contract-herdr-v2` - mixed - tmux/rmux/herdr backend contract V2.
4. `herdr-backend-client` - mixed - Herdr socket client, schema/version gate and capability evidence.
5. `ccbd-windows-control-plane-transport` - mixed - ccbd control-plane transport seam plus Windows TCP loopback/token adapter.
6. `ccbd-herdr-namespace-lifecycle` - functional - ccbd namespace lifecycle on Herdr backend.
7. `provider-runtime-on-herdr` - functional - all public providers ask/pend/completion/cancel on Herdr panes.
8. `herdr-bounded-recovery-boundary` - mixed - CCB-only bounded recovery with Herdr restore evidence.
9. `herdr-user-surfaces-parity` - mixed - foreground, Mobile, Config UI, doctor/ping/mounted/project view projection.
10. `windows-x64-release-surface` - mixed - npm/install/update/native helper/managed Python release surface gate.
11. `native-windows-public-workflow-validation-matrix` - mixed - Native Windows x64 public workflow evidence matrix.
12. `herdr-supportability-projection` - mixed - evidence-driven support tier, docs, doctor and residual risk projection.

Implementation entry for each item requires all `depends_on` items to be `done`; design-review passed is not implementation-ready.

## Roadmap Core Acceptance Paths

- Native Windows x64 platform gate and strict `v8.5.2` source/new branch evidence.
- User-provided Herdr detection, capability/schema validation and direct Native Windows auto-route to Herdr.
- Native Windows `ccb` process can start and connect to `ccbd` control plane through TCP loopback + same-user token, without regressing Unix AF_UNIX behavior.
- `ccb` project namespace lifecycle, foreground attach, kill/restart/reload and pane IO on Herdr.
- All public providers under Herdr pane through ask, pend, completion and cancel.
- Mobile terminal and Config UI parity on Herdr.
- CCB-owned bounded recovery with Herdr auto restore disabled or blocked.
- Windows npm install dry-run / pack dry-run code-level evidence without publish.
- Public workflow matrix and supportability projection proving unsupported/beta gaps are not overstated.

## Key Assumptions

- Current machine is the dedicated Native Windows x64 validation host.
- Herdr is user-provided; CCB detects and diagnoses it but does not install it.
- No remote push, npm publish, release, deploy, promotion or production cutover is authorized.

## Top Risks And Mitigation

1. Herdr API/capability mismatch blocks CCB primitive parity. Mitigation: spike and backend client fail closed before downstream implementation.
2. Provider/recovery authority drifts from CCB to Herdr. Mitigation: provider runtime and recovery boundary designs require CCB-owned completion, cancellation and recovery evidence.
3. Windows support is overstated. Mitigation: validation matrix and supportability projection require strict all-provider, Mobile/Config, npm dry-run, release surface, docs and doctor gates before `supported`.

## Mandatory Validation Set

- `python ".codestable/tools/validate-yaml.py" --file <design-or-review>`
- `python ".codestable/tools/validate-yaml.py" --file <checklist> --yaml-only`
- Each feature's `dod.commands` from its approved checklist.
- Native Windows x64 manual/transcript commands where the feature marks them core.
- `python "C:/Users/Administrator/.codex/plugins/cache/codestable/codestable/1.0.4/skills/cs-onboard/tools/codestable-workflow-next.py" feature --feature <feature-dir> --require-implementation-ready --json`

## Final Aggregate Commands

- `python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml"`
- `python "C:/Users/Administrator/.codex/plugins/cache/codestable/codestable/1.0.4/skills/cs-onboard/tools/codestable-goal-consistency-gate.py" --roadmap ".codestable/roadmap/windows-native-herdr-ccb"`
- Final feature DoD commands that remain core after all child acceptance reports.
- Windows `npm install` dry-run / `npm pack --dry-run` evidence required by release surface and matrix acceptance.

## Policies

- DoD Policy: checklist steps must move from `pending` to `done` during implementation; checks move to `passed` only during acceptance.
- Gate Policy: run scope-gate, dod-runner and evidence-pack before review; run review/QA/acceptance gates per `goal-protocol-gates.md`.
- Provider Policy: provider unavailable is recorded as provider warning unless it is a core public provider workflow gate; unexplained core provider warning blocks.
- Tool Recovery: if a real runner is missing, install or repair the real dependency/runner configuration. Do not add same-name shims or fake validation output.
- Provider fallback: archguard/meta-cc unavailable is recorded and explained by review/QA/audit, not silently ignored.

## Authorization

- Goal acceptance authorization ref: `approval-report.md#goal-acceptance`.
- Goal scoped commit authorization ref: `approval-report.md#goal-commits`.
- Both must be approved under the same `approval_groups.goal-execution` confirmation before dispatch.
