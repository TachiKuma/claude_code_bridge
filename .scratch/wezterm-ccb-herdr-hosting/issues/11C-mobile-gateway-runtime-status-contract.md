# 11C：Agents 面板/mobile gateway runtime_status 契约

**What to build：** 确认 Agents 面板和 mobile gateway 消费同一个 `project_view.runtime_status` 读模型。
本节点聚焦契约与脱敏：前台三态、运行时状态、job/ask 状态同时可见，但 prompt/reply/API key/OAuth
token 不进入面板或 gateway payload。

**Blocked by：** 11A（稳定 runtime_status 读模型）

**Status:** done

**Evidence to inspect：** `lib/mobile_gateway/service.py`、`tools/ccb-agent-sidebar/src/model.rs`、
`tools/ccb-agent-sidebar/src/status.rs`、`test/test_mobile_gateway_service.py`、
`test/test_ccbd_project_view.py`

- [x] mobile gateway 不重算 runtime 状态，只转发/裁剪 `project_view.runtime_status`
- [x] `frontend_status` 三态能在 gateway payload 中稳定表达
- [x] `done` 显示为运行时完成但业务未确认，不关闭 job
- [x] `unknown` 显示为未知/重连中，不显示为空闲
- [x] 脱敏测试覆盖 prompt/reply/API key/OAuth token

**Validation：**

- `pytest test/test_mobile_gateway_service.py test/test_ccbd_project_view.py`

**Evidence:** `lib/mobile_gateway/service.py`
（`_REDACTED_AGENT_KEYS` 与 `_redact_project_view_payload` 的 agent 级裁剪）、
`test/test_mobile_gateway_service.py`（契约与脱敏测试）

**Notes：** gateway 对 `view.agents[].runtime_status` 保持透传（不重算），并在 agent 级
防御性裁剪 `prompt/reply/api_key/oauth_token/transcript`；`done` 保留 `unseen_done=true`
且 job 不关闭，`unknown` 不降级为 idle，`frontend_status` 三态稳定表达。侧栏 Rust 仅作
evidence 复核，未改动。
