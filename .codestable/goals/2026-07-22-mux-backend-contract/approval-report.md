---
doc_type: approval-report
unit: .codestable/goals/2026-07-22-mux-backend-contract
status: resolved
reason: blocker
approvals:
  owner-resume-2026-07-22: "ResumeWith: backend-resolver-opt-in-contract 已验收通过，继续 mux-backend-contract。"
approval_groups: {}
created_at: 2026-07-22
---

# Approval Report

## Decision History

- 2026-07-22：owner 明确说明 `backend-resolver-opt-in-contract` 已验收通过，并要求继续 `mux-backend-contract`。本 goal 按 `ResumeWith` 恢复推进。

## Decision Needed

`mux-backend-contract` implementation artifacts are in place, but full CMD-004 is blocked by a ccbd Windows token ACL startup failure outside this feature's declared scope. Owner needs to decide how to handle that cross-boundary blocker before the goal can continue.

## Why Now

The feature checklist marks CMD-004 as core. After correcting its stale test path, the command reaches `test_v2_phase2_entrypoint.py::test_ccb_start_restore_keeps_bound_runtime_refs`, where ccbd exits before ready due to token ACL owner convergence:

`RpcTransportAuthError: token-unprotectable: Windows token owner did not converge to the current user`

This failure is in `ccbd.control_plane_transport.token_auth` / `windows_tcp`, not in the new mux contract or fake backend modules.

## Context

This goal explicitly does not modify ccbd control-plane transport endpoint schema. Fixing the failure likely belongs to the prior `ccbd-windows-tcp-loopback-transport` capability area, or to a follow-up issue/feature for Windows token ACL convergence. The current mux contract implementation has passing focused evidence:

- contract/fake backend tests pass;
- YAML validation passes;
- backend selection + agent reflow focused regression passes;
- `test_v2_phase2_entrypoint.py` passes when excluding the single failing restore binding test.

## Options

- Recommended: split or route the ccbd token ACL startup failure to its owning capability, fix it there, then resume CMD-004 and continue `mux-backend-contract`.
- Alternative: owner accepts this ccbd token ACL failure as a documented external blocker for this feature's CMD-004 and authorizes continuing review/QA only for the mux contract diff.
- Stop: keep this goal blocked until owner manually resolves the transport/auth environment or changes the epic validation plan.

## Recommendation

Choose the recommended option. It preserves feature boundaries and avoids hiding a real Windows control-plane failure under a mux contract implementation.

## Risks And Tradeoffs

- Splitting/fixing the ccbd blocker may delay `mux-backend-contract`, but keeps acceptance evidence honest.
- Continuing with a documented external blocker speeds up mux contract review, but weakens the core regression gate and risks carrying a broken Windows startup path forward.
- Keeping the goal blocked is safe but leaves the epic goal driver unable to advance past `mux-backend-contract`.

## Non-Automatic Actions

This decision does not authorize git commit, git push, merge, release, deploy, production changes, global package changes, or remote operations. It also does not authorize changing ccbd transport/auth behavior unless owner explicitly chooses the recommended split/fix route.

## After You Answer

If owner chooses split/fix, resume by creating or routing the ccbd token ACL blocker to the appropriate issue/feature, then rerun CMD-004. If owner accepts documented external blocker, record that decision and proceed to independent review/QA for the mux contract diff only. If owner chooses stop, keep this goal blocked.
