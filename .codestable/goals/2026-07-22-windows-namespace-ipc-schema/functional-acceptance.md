---
doc_type: goal-functional-acceptance
goal: windows-namespace-ipc-schema
status: pass
reviewer_id: "019f8a19-78e1-77b3-9025-9772dd8bf21d"
final_iteration: "iterations/001.md"
---

# windows-namespace-ipc-schema Functional Acceptance

## Reviewer

- Task agent id：`019f8a19-78e1-77b3-9025-9772dd8bf21d`
- Role：Acceptance

## Scope

核验 `ProjectNamespaceState` / `ProjectNamespaceEvent`、`build_ccbd_payload()`、doctor summary / render、`attach_started_project_namespace()`、feature review / QA / roadmap 回写与最终 iteration 之间的一致性。

## Acceptance Checks

1. state/event canonical fields 与旧 tmux 记录双向兼容。
2. canonical payload 可投影为完整 `MuxNamespaceRef`，且 `namespace_id == project_id`、`namespace_backend_family == tmux-family`。
3. ping/doctor 同时输出 canonical 和 legacy alias，且顶层 `tmux_socket_path` 不被 namespace alias 覆盖。
4. foreground attach canonical-first、legacy fallback，行为不变。
5. 旧回归、feature review、QA 和 roadmap 回写均已完成。

## Functional Evidence

- 只读 pytest：`94 passed`。
- feature review：`passed`。
- QA：`passed`。
- checklist / roadmap items YAML：`All files valid`。
- `CMD-004` 的 Windows control-plane 失败已记录为 baseline，不构成本 feature 阻塞。

## Verdict

pass

## Residual Risks

- `CMD-004` 在 native Windows 下仍保留两个既有 transport/shutdown 基线失败，已在 QA 中记档。

## Delivery Record

本 feature 已交付 canonical namespace schema、payload 投影、foreground attach 兼容输入与回归测试，并完成 roadmap 回写。
