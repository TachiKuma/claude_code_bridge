# 11B：pane 所有权迁移读模型验证

**What to build：** 用端到端式 fake runtime 场景补齐 `project_view.runtime_status` 在 pane 重启、迁移、
重新 attach、事件乱序/重复、断线重连后的状态归属验证。实现只修投影缺口，不扩大生命周期下放范围。

**Blocked by：** 10C（重连重读 snapshot）、11A（runtime_status 组装边界）

**Status:** done

**Evidence to inspect：** `lib/ccbd/project_view/runtime_status.py`、
`lib/ccbd/project_view/service.py`、
`lib/ccbd/services/runtime_runtime/refresh.py`、
`test/test_ccbd_project_view.py`、
`test/test_ccbd_runtime_refresh.py`、
`test/test_herdr_runtime_contracts.py`

- [x] pane_id 改变时旧 pane 状态不沿用
- [x] snapshot 出现目标 pane 但无匹配记录时，不回退 root summary
- [x] 乱序/重复事件不改变当前投影
- [x] 重连后 `runtime_status.cache_key` 跟随 generation/pane_id 改变
- [x] Provider/job/lifecycle 字段不被 Herdr `done` 误判为业务完成

**Validation：**

- `pytest test/test_ccbd_project_view.py test/test_ccbd_runtime_refresh.py`

**Evidence:** `test/test_ccbd_project_view.py`、
`test/test_ccbd_runtime_refresh.py`、
`test/test_herdr_runtime_contracts.py`
