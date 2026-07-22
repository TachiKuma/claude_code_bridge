---
doc_type: goal-functional-acceptance
goal: "windows-job-object-runtime-evidence"
status: pass
reviewer_id: "019f8a7d-b828-77b3-a947-03fbd9016f71"
final_iteration: "iterations/002.md"
---

# windows-job-object-runtime-evidence 功能验收

## Reviewer

- Task agent role: Acceptance
- Task agent id: `019f8a7d-b828-77b3-a947-03fbd9016f71`
- 运行方式：可见 Task agent 只读功能验收，不修改仓库文件。
- 生命周期：验收结果已消费，agent 已关闭；关闭时 previous_status 为 completed/pass。

## Scope

验收 `.codestable/goals/2026-07-22-windows-job-object-runtime-evidence/goal.md` 中记录的 owner-level acceptance criteria：`process_ref` runtime evidence contract、runtime / provider facts / helper manifest roundtrip、health pane/process evidence 分离、Windows kill / cleanup gating、diagnostics exposure、checklist 与 roadmap item 写回。

## Acceptance Checks

- pass：`AgentRuntime` 和 `ProviderRuntimeFacts` 能承载 `process_ref`；旧 runtime 记录缺失 `process_ref` 时仍可加载。
- pass：`provider_runtime/process_ref.py` 是 builder、normalizer、destructive cleanup eligibility 的集中 seam。
- pass：`process_ref` 区分 `windows_job_object`、`process_tree`、`legacy_pid`；`evidence_state` 为枚举，不持久化 handle。
- pass：`runtime_health()` 在 pane health 前检查 process evidence；pane alive 不会掩盖 missing / stale / degraded process evidence。
- pass：Windows cleanup gate 不再无条件信任 pid，改走 `process_ref` / authority record；`taskkill /T` 保持在终止 primitive 层。
- pass：project view 暴露 `process_ref` diagnostics；checklist 与 roadmap item 已写回。

## Functional Evidence

- `lib/provider_runtime/process_ref.py` 提供 `ProcessRef` 类型、builder、normalizer、health mapping 与 destructive cleanup eligibility。
- `lib/agents/models_runtime/runtime_runtime/agent.py` 与 `lib/agents/store.py` 通过 normalizer 持久化 / 加载 `process_ref`。
- `lib/ccbd/services/provider_runtime_facts.py` 生成并携带 `process_ref`。
- `lib/ccbd/services/health_monitor_runtime/status.py` 在 pane health 前消费 `process_ref_health()`。
- `lib/runtime_pid_cleanup/matching.py` 将 Windows ownership gate 改为 `process_ref` / authority record / control-plane evidence，不再无条件 `return True`。
- `lib/ccbd/project_view/service.py` 在 agent record 中暴露 `process_ref` 诊断投影。
- 独立 review agent `019f8a72-5013-7fb3-abf6-40dc45c61f6b` 首轮指出 4 项 blocking；focused closure 返回 `verdict: pass`。

## Verification

- `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-20-windows-job-object-runtime-evidence/windows-job-object-runtime-evidence-checklist.yaml" --yaml-only` -> passed。
- `python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml"` -> passed。
- `python -m pytest -q "test/test_v2_provider_health_store.py" "test/test_ccbd_health_monitor_rebind.py" "test/test_ccbd_health_assessment_provider_pane.py"` -> `9 passed`。
- `python -m pytest -q "test/test_provider_helper_cleanup.py" "test/test_cli_kill_runtime_processes.py" "test/test_v2_kill_service.py" "test/test_ccbd_stop_flow_runtime.py"` -> `48 passed`。
- `python -m pytest -q "test/test_ccbd_project_view.py" "test/test_ccbd_runtime_refresh.py" "test/test_ccbd_registry.py" -k "process_ref or runtime_authority or job or pane_state"` -> `17 passed, 75 deselected`。
- focused validation selector -> `32 passed, 117 deselected`。
- CMD-006 guard -> expected matches；无无条件 Windows pid cleanup 门。
- `git diff --check` -> clean。

## Verdict

`pass`。

## Residual Risks

- 未做真实 Windows Job Object attach / handle lifecycle 真机 smoke；当前交付是 runtime evidence contract 与 cleanup gating seam。
- 后续 `rmux-supervision-recovery` / Windows full-chain smoke 仍需验证真实 job object 退出、stale 和 recovery 行为。

## Delivery Record

本功能验收对应 final iteration：`.codestable/goals/2026-07-22-windows-job-object-runtime-evidence/iterations/002.md`。`windows-job-object-runtime-evidence` 可进入 accepted/done 写回，epic 下一项为 `provider-runtime-backend-session-contract`。
