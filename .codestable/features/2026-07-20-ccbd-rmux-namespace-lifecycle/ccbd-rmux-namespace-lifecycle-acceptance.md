---
doc_type: feature-acceptance
feature: 2026-07-20-ccbd-rmux-namespace-lifecycle
status: accepted
updated_at: "2026-07-23"
---

# ccbd-rmux-namespace-lifecycle Acceptance

## Acceptance Summary

本 feature 已 accepted。

完成内容：

- namespace state、ping、doctor、startup、kill report 写 canonical namespace projection，并保留 tmux aliases。
- `ProjectNamespaceController`、`ensure`、`reflow`、layout projection 已通过 backend resolver / factory 与 backend interface 消费 namespace。
- foreground attach 在 Rmux 路径走已批准的 attach capability / adapter，不再在 `start_foreground.py` 里直接拼 `tmux attach-session`。
- `ccb kill`、`project_view`、`project_clear/restart`、`layout_status`、`doctor`、`ping` 已改读 canonical namespace projection。

## Gate Evidence

- Checklist：`done`
- Review：独立 Task agent `pass`
- QA：`pass`
- Goal functional acceptance：独立 Task agent `pass`

## Residual Risks

- 未运行全量测试套件。
- Rmux Windows full-chain smoke 仍留给后续 roadmap item。
