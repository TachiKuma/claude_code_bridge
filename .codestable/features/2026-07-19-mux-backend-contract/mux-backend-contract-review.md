---
doc_type: feature-review
feature: mux-backend-contract
status: passed
reviewer_id: "019f89ab-deb0-7861-adbd-be813d3a07b4"
updated_at: "2026-07-22"
---

# mux-backend-contract Review

## Scope

审查 `mux-backend-contract` 的 contract/fake backend 实现、本轮 psmux 兼容修复，以及相关测试与 CodeStable 产物。

## Reviewer

- Task agent: `019f89ab-deb0-7861-adbd-be813d3a07b4`
- 运行方式：只读独立 review，完成后已关闭。

## Findings

初次 review 发现两条 important 风险，均已修复并经 focused closure 通过：

- `is_tmux_compat_subset` 曾扫描 `_tmux_base()` 全部参数，可能因 socket/config path 含 `psmux` 误判普通 tmux。
- `_apply_optional_tmux_policy` 曾丢失 `_tmux_run_ready` transient retry 语义。

## Closure

Focused closure verdict: `pass`。

reviewer 验证：

```text
python -m pytest -q test/test_v2_project_namespace_backend.py::test_ensure_server_policy_retries_transient_optional_window_policy test/test_v2_project_namespace_backend.py::test_tmux_compat_subset_ignores_socket_paths_containing_psmux
```

结果：`2 passed`。

## Residual Risks

- 回归命令为目标抽样，不等价于全仓全量测试。
- psmux/rmux 兼容层当前对 tmux UI/policy 命令采取保守跳过，后续 adapter 可根据真实能力报告细化。
