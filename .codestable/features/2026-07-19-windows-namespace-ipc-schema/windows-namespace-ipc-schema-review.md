---
doc_type: feature-review
feature: 2026-07-19-windows-namespace-ipc-schema
roadmap: windows-rmux-native-backend
roadmap_item: windows-namespace-ipc-schema
status: passed
reviewer_id: "019f8a14-1e14-7931-8490-c7fbaebad8d5"
updated_at: "2026-07-22"
---

# windows-namespace-ipc-schema Review

## Reviewer

- 初审 Task agent：`019f8a0b-487d-7451-b315-08d56809e522`
- 复审 Task agent：`019f8a14-1e14-7931-8490-c7fbaebad8d5`
- 模式：只读独立 code review。

## 初审发现

初审不通过，提出 3 个问题：

- blocking：`namespace_event_summary` 在 ping/doctor payload 合并中覆盖 state canonical namespace fields。
- high：`default_project_namespace_backend()` 通过 `CCB_TERMINAL_BACKEND + get_backend_for_session()` 实际解析/构造 rmux backend，超出本 feature 边界。
- medium：`namespace_backend_family` 只默认不固定，输入其他 family 时可能外泄。

## 修复摘要

- `build_ccbd_payload()` 和 doctor 本地 summary 改为 event 先合并、state 后合并；state canonical 字段优先，event 只补 `namespace_last_event_*`。
- `default_project_namespace_backend()` 去掉 `CCB_TERMINAL_BACKEND + get_backend_for_session()` 路径，继续使用 resolver 的 `get_backend()` 合同；显式 `CCB_MUX_BACKEND` / project config rmux 仍 fail-fast。
- `ProjectNamespaceState` / `ProjectNamespaceEvent` 在 `__post_init__` 中强制 `namespace_backend_family = "tmux-family"`，summary 不暴露输入的其他 family。
- 新增回归测试覆盖 event/state canonical 冲突、family 固定归一、`CCB_TERMINAL_BACKEND` 不驱动 namespace backend。

## 复审结论

复审结论：无 blocking / high / medium findings。

- spec compliance：pass。三个初审 finding 均已关闭，并有对应测试覆盖。
- code quality：pass。改动集中，兼容 legacy alias，merge precedence 简单可读。

## Verdict

通过。当前 diff 满足 `windows-namespace-ipc-schema` 的 review gate。
