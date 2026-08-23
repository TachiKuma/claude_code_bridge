# 11：project_view 合并读模型 + Herdr→CCB 状态映射（Phase 3）

**What to build：** 在 `project_view` 的 activity/runtime status resolver 中合并：Herdr 运行时状态、
Provider hook 状态、pane/status-line 状态、CCB job/callback 元数据、lifecycle guard，以及前台三态。
遵循「Provider-native activity 是执行状态权威、CCB job 是工作流元数据、lifecycle guard 是归属
边界」。建立 Herdr→CCB 映射，并按复合键失效缓存。

**Blocked by：** 04（前台三态投影）、10（事件模型/投影）

**Status:** partial

**Implementation:** `3b4f75b4`

**Evidence:** `lib/ccbd/project_view/service.py`、`lib/platforms/windows/herdr/runtime/events.py`、
`test/test_ccbd_project_view.py`、`test/test_herdr_runtime_contracts.py`

**Notes:** `project_view` 已新增 Herdr runtime/前台三态的读模型基础与状态映射；完整替换所有
Provider/pane/job/lifecycle 来源、以及 pane 重启/迁移/重连端到端验证仍未关闭。

补充：`_herdr_runtime_state_from_snapshot` 现在优先读取目标 `pane_id` 对应的局部快照，再回退到根级
摘要，避免迁移后仍被旧的 root summary 盖掉局部 pane 状态。

- [ ] 完整合并运行时/Provider/pane/job/lifecycle/前台三态为单一读模型
- [x] 状态映射：`working→working`、`blocked→waiting_for_user`、`idle→idle`、
      `done→idle+unseen_done=true`、`unknown→unknown`（不降级为 idle）
- [x] Herdr `done` 不直接关闭 job；`unknown` 不投影为 idle
- [x] `runtime_status` 缓存按 project id/agent name/runtime generation/pane id 复合键失效
- [x] 面板同时显示运行时状态与 job/ask 状态，不混成一个权威
- [ ] pane 重启/迁移/重新 attach/事件乱序/重复/断线重连都不泄漏旧状态
