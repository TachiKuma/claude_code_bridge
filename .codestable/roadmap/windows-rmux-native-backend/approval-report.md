---
doc_type: approval-report
unit: .codestable/roadmap/windows-rmux-native-backend
status: approved
reason: route-choice
approvals:
  roadmap-review: approved
  roadmap-plan: approved
  all-child-designs: approved
  goal-acceptance: approved
  goal-commits: approved
approval_groups:
  roadmap-execution:
    status: approved
    confirmation_id: roadmap-execution-2026-07-19-windows-rmux-native-backend
    decisions:
      roadmap-review: approved
      roadmap-plan: approved
  child-designs:
    status: approved
    confirmation_id: child-designs-2026-07-20-windows-rmux-native-backend
    decisions:
      all-child-designs: approved
  goal-execution:
    status: approved
    confirmation_id: goal-execution-2026-07-20-windows-rmux-native-backend
    decisions:
      - goal-acceptance
      - goal-commits
created_at: 2026-07-19
---

# Approval Report

## Decision History

- 2026-07-19: Owner stated "windows-rmux-native-backend的review通过，开始执行cs-epic". Recorded as approval to proceed with the epic despite Round 6 important findings being carried as residual risk.
- 2026-07-20: Owner stated "确认一批准所有 child designs". Recorded as approval of all passed child feature designs under `windows-rmux-native-backend`; each child design frontmatter was updated to `status: approved`.
- 2026-07-20: Owner stated "确认授权 Goal execution". Recorded as approval of `approval_groups.goal-execution` with confirmation id `goal-execution-2026-07-20-windows-rmux-native-backend`, covering `goal-acceptance` and `goal-commits`.
- 2026-07-20: Owner confirmed the target environment is native Windows and requested CodeStable docs to treat `AF_UNIX` absence as an expected platform fact for this milestone. Recorded as a scope/evidence decision: Unix-only `AF_UNIX` real-host evidence is compatibility evidence, not a blocking core gate for `windows-rmux-native-working`; native Windows blockers such as `mobile_gateway.terminal -> import fcntl` remain milestone blockers until fixed or separately accepted.
- 2026-07-20: Owner decided to split the out-of-scope Windows runtime import/locking/atomic-write compatibility changes (touching `lib/mobile_gateway/terminal.py`, `lib/storage/locks.py`, `lib/storage/atomic.py`, `lib/maintenance_heartbeat/lock.py` plus two import-guard tests) out of `ccbd-control-plane-transport-seam` into a separate feature, because they fall outside that feature's reviewed `scope-gate.json` `allowed_prefixes`. The changes are preserved under `pending-split/windows-runtime-import-lock-compat/` (patch + tests + NOTE) and the feature working tree was restored to its reviewed scope. Owner **separately accepts** the `mobile_gateway.terminal -> import fcntl` Windows collection gap as a documented baseline for `ccbd-control-plane-transport-seam` per its checklist `CMD-005: failure_handling: document-baseline`; the Windows-safe import fix and native `AF_UNIX`-on-Windows transport are deferred to the split feature and `ccbd-windows-tcp-loopback-transport` respectively. This satisfies goal-protocol §3.1's "owner 单独记录可接受缺口" escape hatch, so `goal-state.yaml` is transitioned from `handoff` back to `running` and QA for `ccbd-control-plane-transport-seam` may resume, recording CMD-005 as a documented baseline with real Unix `AF_UNIX` evidence as compatibility residual.
- 2026-07-21: Owner stated "Goal driver 恢复后的首步：1. 将 goal-state.yaml.status 从 handoff → running（依据 resume_note 和 approval-report.md 决策） 2. 对 index 2 accelerator-transport-windows-guard（review-blocked）按 owner 决策继续 QA 3. 完成后按 goal-protocol 推进后续 features，最终目标为 ccbd-windows-full-chain-smoke". Recorded as approval to resume the roadmap goal from the `IndependentReviewUnavailable` handoff and continue the current feature toward QA. This is not a git, push, merge, release, deploy, or production authorization; review gate evidence still must be satisfied by a visible Task agent reviewer where available, or by a separately named local-only fallback if no reviewer can be used.

## Decision Needed

none

## Why Now

`cs-epic` requires a recoverable owner approval surface before moving from reviewed roadmap planning into execution-oriented child design / goal stages.

All child designs are now approved and the goal package has been generated. The next step is a separate execution authorization because Goal mode can run implementation, review, QA, acceptance, and local scoped commits.

## Context

Roadmap review Round 6 recorded three important findings:

- shared Windows pid liveness coverage must include both `ccbd.system.process_exists` and `cli.kill_runtime.processes.is_pid_alive`;
- ccbd transport endpoint changes must synchronize startup / diagnostics contract deltas before or inside the transport implementation work;
- active roadmap state needed canonical approval evidence.

This approval accepts proceeding while preserving those findings as required follow-up constraints for downstream feature design and implementation.

All non-dropped child feature designs now have passed design-review reports. The 2026-07-20 child design approval is a batch approval for those designs only; it does not approve implementation results, QA, acceptance, goal execution, commits, push, merge, release, deploy, or production changes.

The 2026-07-20 native Windows evidence decision narrows the current milestone's core proof obligation to native Windows behavior. It does not claim Unix `AF_UNIX` compatibility is verified on this host; it permits the goal driver and later QA/audit stages to carry Unix-only runtime proof as a documented compatibility residual while requiring Windows TCP loopback, accelerator guard, process liveness, Rmux lifecycle, and final full-chain smoke to supply the milestone's core evidence.

## Options

- Approved: proceed with `cs-epic` for `windows-rmux-native-backend`, carrying Round 6 important findings as residual risk and downstream hard constraints.
- Rejected: stop execution and return to planning revision before any child design or goal work.
- Approve Goal execution: authorize both `goal-acceptance` and `goal-commits` for the generated package.
- Reject Goal execution: keep the package as handoff material and do not dispatch a Goal driver.

## Recommendation

Approved, because the findings are actionable constraints that can be enforced in downstream feature design without changing the roadmap's top-level direction.

## Risks And Tradeoffs

- Proceeding without editing the roadmap body means downstream feature design must explicitly consume the Round 6 findings.
- If later feature design ignores these findings, the roadmap should return to planning update and review.

## Non-Automatic Actions

This approval does not authorize git commit, git push, merge, release, deploy, publishing, production changes, or changing upstream repository state.

The pending Goal execution authorization may authorize local per-feature scoped commits only if `goal-commits` is explicitly approved. It still does not authorize remote push, merge, publish, release, deploy, promotion, production cutover, or changing upstream repository state.

## After You Answer

Proceed with `cs-epic` state restoration and continue to the next recoverable stage.

If Goal execution is approved, atomically mark `approval_groups.goal-execution`, `goal-acceptance`, and `goal-commits` approved with the same confirmation id, then sync `goal-state.yaml` to `ready-to-dispatch`. If rejected, persist handoff and do not dispatch.
