---
doc_type: roadmap-goal-plan
roadmap: windows-rmux-native-backend
status: awaiting-authorization
created: 2026-07-20
---

# windows-rmux-native-backend Goal Plan

## 1. Scope

- Roadmap: .codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-roadmap.md
- Items: .codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml
- Goal state: .codestable/roadmap/windows-rmux-native-backend/goal-state.yaml
- Execution order: topological order from workflow-next.

## 2. Feature Execution Order

- $(System.Collections.Hashtable.slug): Windows Rmux capability probe 与 gap report；性质 $(System.Collections.Hashtable.kind)；依赖 none
- $(System.Collections.Hashtable.slug): ccbd control-plane transport seam、Unix adapter 与 fake transport；性质 $(System.Collections.Hashtable.kind)；依赖 none
- $(System.Collections.Hashtable.slug): native Windows/no-AF_UNIX accelerator clean fallback；性质 $(System.Collections.Hashtable.kind)；依赖 none
- $(System.Collections.Hashtable.slug): 共享跨平台 pid liveness helper 与 Windows WinAPI backend；性质 $(System.Collections.Hashtable.kind)；依赖 none
- $(System.Collections.Hashtable.slug): Rmux route approval evidence 与 decision summary；性质 $(System.Collections.Hashtable.kind)；依赖 rmux-capability-gate
- $(System.Collections.Hashtable.slug): Windows TCP loopback control-plane transport adapter；性质 $(System.Collections.Hashtable.kind)；依赖 ccbd-control-plane-transport-seam
- $(System.Collections.Hashtable.slug): Rmux opt-in resolver、fail-fast 与 diagnostics contract；性质 $(System.Collections.Hashtable.kind)；依赖 rmux-route-approval
- $(System.Collections.Hashtable.slug): MuxBackend 组合契约与 fake backend 测试替身；性质 $(System.Collections.Hashtable.kind)；依赖 backend-resolver-opt-in-contract
- $(System.Collections.Hashtable.slug): 现有 TmuxBackend 到 MuxBackend 的兼容 adapter；性质 $(System.Collections.Hashtable.kind)；依赖 mux-backend-contract
- $(System.Collections.Hashtable.slug): mux-neutral namespace state 与 ping/doctor projection；性质 $(System.Collections.Hashtable.kind)；依赖 mux-backend-contract
- $(System.Collections.Hashtable.slug): Windows shell/log command builders；性质 $(System.Collections.Hashtable.kind)；依赖 mux-backend-contract
- $(System.Collections.Hashtable.slug): Windows Job Object process-tree evidence；性质 $(System.Collections.Hashtable.kind)；依赖 windows-namespace-ipc-schema
- $(System.Collections.Hashtable.slug): backend-neutral provider session payload 和 health/recovery contract；性质 $(System.Collections.Hashtable.kind)；依赖 mux-backend-contract, windows-namespace-ipc-schema
- $(System.Collections.Hashtable.slug): Rmux daemon discovery/start/health/crash/cleanup ownership；性质 $(System.Collections.Hashtable.kind)；依赖 mux-backend-contract, windows-namespace-ipc-schema
- $(System.Collections.Hashtable.slug): Rmux namespace/session/window/pane backend core；性质 $(System.Collections.Hashtable.kind)；依赖 tmux-backend-contract-adapter, windows-namespace-ipc-schema, windows-shell-log-builder, provider-runtime-backend-session-contract, rmux-daemon-ownership-boundary
- $(System.Collections.Hashtable.slug): Rmux send/capture/logging semantics；性质 $(System.Collections.Hashtable.kind)；依赖 rmux-backend-core
- $(System.Collections.Hashtable.slug): ccbd Rmux project namespace ensure/attach/kill lifecycle；性质 $(System.Collections.Hashtable.kind)；依赖 rmux-send-capture-logging, windows-job-object-runtime-evidence, ccbd-windows-tcp-loopback-transport
- $(System.Collections.Hashtable.slug): Rmux pane/provider/daemon supervision recovery diagnostics；性质 $(System.Collections.Hashtable.kind)；依赖 ccbd-rmux-namespace-lifecycle
- $(System.Collections.Hashtable.slug): native Windows ccb->ccbd->rmux start/ask/kill transcript smoke；性质 $(System.Collections.Hashtable.kind)；依赖 ccbd-windows-tcp-loopback-transport, ccbd-rmux-namespace-lifecycle, accelerator-transport-windows-guard, ccbd-windows-process-liveness
- $(System.Collections.Hashtable.slug): Windows Rmux validation matrix、runner 与 report；性质 $(System.Collections.Hashtable.kind)；依赖 rmux-supervision-recovery
- $(System.Collections.Hashtable.slug): installer/package/docs/contracts 支持状态收口；性质 $(System.Collections.Hashtable.kind)；依赖 rmux-windows-validation-matrix

## 3. Roadmap Core Acceptance Paths

- Native Windows Rmux capability and route approval evidence.
- Opt-in backend resolver diagnostics proving explicit Rmux selection and fail-fast behavior.
- Existing tmux path regression remains green on Linux/macOS/WSL.
- Native Windows ccb -> ccbd -> rmux start/ping/ask/kill transcript, with probe_bypass=false.
- Native Windows control-plane evidence is the milestone core: `ccbd-windows-tcp-loopback-transport` and `ccbd-windows-full-chain-smoke` must prove Windows behavior; Unix-only `AF_UNIX` real-host evidence is compatibility residual for this milestone when unavailable on the current host.
- Windows validation matrix/report distinguishes fake, provider blackbox, true-host and manual transcript lanes.
- Packaging/docs contracts explicitly state Windows Rmux support level and installation boundaries.

## 4. Assumptions

- Rmux capability gate and route approval remain valid inputs for implementation.
- Native Windows true-host evidence may require manual or focused runner outside default CI.
- The current native Windows host is expected not to expose `socket.AF_UNIX`; goal recovery must not require WSL/Unix evidence for the Windows milestone unless the specific feature is claiming Unix compatibility as its own core deliverable.
- Provider credentials may be unavailable; provider failure must be classified separately from system failure.
- .codestable changes are local/TachiKuma-tracked and are not included in upstream SeemSeam scoped submissions unless explicitly requested.

## 5. Top Risks

1. Rmux command compatibility differs from tmux in subtle ways. Mitigation: capability gate, backend contract tests, provider completion golden fixtures.
2. Windows control-plane and mux concerns get mixed. Mitigation: keep ccbd transport, runtime accelerator, pid liveness and Rmux backend in separate feature boundaries.
3. Fake/probe/WSL evidence is mistaken for true-host pass. Mitigation: transcript schema requires native Windows + ccbd + rmux + probe_bypass=false and parser fail closed.

## 6. Mandatory Validation Commands

Feature-level commands are defined in each feature checklist and mirrored in goal-features/*.md. Final aggregate commands:

- $_
- $_
- $_
- $_
- $_

## 7. Policies

- DoD Policy: each feature must complete implementation, independent code review, QA, acceptance, checklist steps/checks and roadmap item writeback before status ccepted.
- Gate Policy: scope-gate, dod-runner, vidence-pack, review/QA/acceptance gates and final consistency gate must pass; missing CodeStable tools require runtime repair, not shim creation.
- Provider Policy: archguard/meta-cc/provider helpers unavailable is recorded as warning/fallback and must be explained by review/QA/audit; unexplained core provider risk can block.
- Verification Recovery: missing pytest/npm/runner dependencies may be installed or restored through normal dependency/config paths only; do not create same-name shim tools or fake validation output.
- Evidence Recovery: Unix-only `AF_UNIX` skipped tests are not a Windows milestone recovery blocker after the native Windows evidence decision is recorded; Windows collection/import blockers such as `mobile_gateway.terminal -> import fcntl` remain blockers until fixed or separately accepted.

## 8. Final Audit Inputs

- goal-audit.md and optional goal-evidence-summary.md.
- codestable-goal-consistency-gate.py --roadmap .codestable/roadmap/windows-rmux-native-backend.
- Feature review / QA / acceptance reports, evidence packs, gate JSON and checklist status.
- Provider warnings, E/C/H summary and H-only core check dispositions.

## 9. Authorizations

- Goal acceptance authorization: pending, ref pproval-report.md#goal-acceptance.
- Automatic per-feature scoped commit authorization: pending, ref pproval-report.md#goal-commits.
- This package does not authorize remote push, merge, publish, release, deploy, promotion or production cutover.
