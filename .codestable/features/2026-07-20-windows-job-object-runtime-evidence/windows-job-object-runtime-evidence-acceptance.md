---
doc_type: feature-acceptance
feature: windows-job-object-runtime-evidence
status: accepted
reviewer_id: "019f8a7d-b828-77b3-a947-03fbd9016f71"
updated_at: "2026-07-22"
---

# windows-job-object-runtime-evidence Acceptance

## Acceptance Checks

- pass：runtime authority 与 provider facts 已承载 canonical `process_ref`。
- pass：`process_ref` builder / normalizer / cleanup eligibility 集中在 `provider_runtime/process_ref.py`。
- pass：Windows cleanup gate 不再无条件信任 pid；普通 pid file 不能绕过 process evidence，ccbd lease / keeper authority record 有窄放行路径。
- pass：health 在 pane evidence 前检查 process evidence，`pane alive != provider healthy` 可测试。
- pass：project view 暴露 `process_ref` diagnostics。
- pass：review、QA、functional acceptance 与 DoD commands 均通过。

## Evidence

- Terminal acceptance Task agent：`019f8a7d-b828-77b3-a947-03fbd9016f71`。
- Independent review Task agent：`019f8a72-5013-7fb3-abf6-40dc45c61f6b`。
- Functional acceptance report：`.codestable/goals/2026-07-22-windows-job-object-runtime-evidence/functional-acceptance.md`。
- Final iteration：`.codestable/goals/2026-07-22-windows-job-object-runtime-evidence/iterations/002.md`。
- QA report：`.codestable/features/2026-07-20-windows-job-object-runtime-evidence/windows-job-object-runtime-evidence-qa.md`。

## Delivery Record

`windows-job-object-runtime-evidence` 已接受。roadmap item 已写回 `done`，epic goal-state feature status 已写回 `accepted`，下一项 handoff 指向 `provider-runtime-backend-session-contract`。
