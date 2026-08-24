# 11A：runtime_status 读模型组装边界

**What to build：** 从 `lib/ccbd/project_view/service.py` 中抽出稳定的 runtime_status 读模型组装边界。
本节点是行为等价重构：输入仍来自 runtime、Provider 状态、job/callback、reload drain、provider
control 和 frontend 三态；输出字段保持兼容。

**Blocked by：** 11（当前合并读模型基础）

**Status:** ready-for-agent

**Evidence to inspect：** `lib/ccbd/project_view/service.py`、
`lib/platforms/windows/herdr/ccbd_surface_projection.py`、`test/test_ccbd_project_view.py`

- [ ] 新增小模块或内部 DTO，集中描述 `runtime_status` 字段和来源
- [ ] `project_view` 主构建函数只调用组装器，不直接拼所有来源字段
- [ ] 保持 `working/blocked/idle/done/unknown` 映射行为不变
- [ ] 保持 callback、reload drain、provider control、frontend 字段兼容
- [ ] 回归测试证明输出快照等价

**Validation：**

- `pytest test/test_ccbd_project_view.py`

