# 04：细粒度 `agent_status` 进入运行时读模型

**What to build:** CCB 消费 Herdr 更细的 `agent_status` 作为 Host Runtime 事实，丰富 project view、gateway 或等价读模型中的运行时状态展示；这些状态只影响运行时展示，不影响 ask/job completion、恢复、取消、continuation 或 provider completion 判定。

**Blocked by:** 01：Herdr 原生 events 成为主状态通道.

**Status:** done

- [x] 读模型能表达 Herdr 的 `working`、`blocked`、`idle`、`done`、`unknown` 等运行时状态。
- [x] `blocked` 能表达为等待用户输入或审批，供用户定位需要处理的 agent。
- [x] `done` 只表示运行时完成，可保留 unseen done 或等价提示，不直接关闭 CCB job。
- [x] `unknown` 保持不确定语义，不降级为空闲或健康。
- [x] 运行时状态更新不会改变业务完成、业务失败、恢复、取消、continuation 或 provider completion 的判定。
- [x] 读模型对外输出继续做敏感字段裁剪，不泄漏 prompt、reply、API key、OAuth token、transcript 或等价敏感内容。
- [x] 局部门禁覆盖 runtime fact source 与 business completion authority 分离，以及 project view/gateway 对 Herdr 状态的外部展示语义。

**Validation:**

- `pytest -q test/test_ccbd_project_view.py::test_project_view_herdr_runtime_status_maps_done_without_closing_job test/test_ccbd_project_view.py::test_project_view_herdr_runtime_status_keeps_unknown_unknown test/test_ccbd_project_view.py::test_project_view_herdr_agent_status_exposes_source_without_business_authority test/test_ccbd_project_view.py::test_project_view_herdr_runtime_status_reads_snapshot_when_state_fields_are_missing`
- `python -m compileall -q lib/ccbd/project_view/runtime_status.py test/test_ccbd_project_view.py`

**Evidence:** Herdr runtime status 读模型现在显式输出 `agent_status`、`agent_status_source`、`agent_status_seq` 与 `agent_status_fallback_reason`；`blocked` 继续映射为 `waiting_for_user`，`done` 仅保留 `unseen_done` 且 job 仍为 running，`unknown` 继续保持 unknown。移动 gateway 对 `runtime_status` 仍按 project view payload 原样转发；当前环境缺少 `cryptography`，对应 gateway 测试无法收集。
