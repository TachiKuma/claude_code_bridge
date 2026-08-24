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

补充：当快照里已经出现目标 `pane_id` 但未命中任何 pane 记录时，不再回退 root summary，直接返回
unknown，避免旧 pane 状态在重连/迁移后回流。

补充：`project_view` 缓存现在会跟随 `AgentRegistry` 的 `project_view_revision` 失效，避免 runtime
更新后继续回放旧响应。

补充：`runtime_status` 现在把 `callback_wait` 的 `chain_*` 元数据并入同一读模型，便于 Herdr 视图
直接消费运行时、job 与 callback 的合并结果，而不必再回看顶层散字段。

补充：`runtime_status` 现在也带上 `reload_drain` 与 `provider_control`，把生命周期阻断和恢复控制
边界一起收进同一读模型里。

**Split after architecture/code comparison（2026-08-24）：** 当前 `project_view` 已能输出 Herdr 运行时
状态、前台三态、callback、reload drain 和 provider control，但合并逻辑仍集中在
`lib/ccbd/project_view/service.py` 的大构建路径中；优化后 archify 图仍把它归入泛化的
`runtime-core`，没有形成独立读模型边界。父节点只保留读模型目标，剩余工作拆到：

- `11A-runtime-status-read-model-dto.md`：抽出稳定的 runtime_status 组装边界，保持行为等价。
- `11B-pane-ownership-transition-read-model.md`：用 pane 重启/迁移/重新 attach/乱序/重复/重连场景补齐端到端投影。
- `11C-mobile-gateway-runtime-status-contract.md`：验证 Agents 面板/mobile gateway 对同一读模型的消费和脱敏。

- [ ] 完整合并运行时/Provider/pane/job/lifecycle/前台三态为单一读模型（由 11A 承接）
- [x] 状态映射：`working→working`、`blocked→waiting_for_user`、`idle→idle`、
      `done→idle+unseen_done=true`、`unknown→unknown`（不降级为 idle）
- [x] Herdr `done` 不直接关闭 job；`unknown` 不投影为 idle
- [x] `runtime_status` 缓存按 project id/agent name/runtime generation/pane id 复合键失效
- [x] 面板同时显示运行时状态与 job/ask 状态，不混成一个权威
- [ ] pane 重启/迁移/重新 attach/事件乱序/重复/断线重连都不泄漏旧状态（由 11B/11C 承接）
