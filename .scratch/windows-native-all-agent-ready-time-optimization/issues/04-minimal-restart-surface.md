# 04：最小重启面与 Restart-Required 语义

**What to build:** 基于配置指纹定位受影响的 agent，只替换/重启匹配到的 agent，不扩散到未受影响 agent。Config UI 保存 provider 启动相关配置（API、model、startup_args、env）后，只更新 desired 状态并记录 `restart-required`；不热改正在运行的 provider。desired/live 差异始终对用户可见。

**Blocked by:** T02（需要缓存和指纹定位机制来判定 affected agent）。

**Status:** pending

- [ ] Affected agent 定位机制：
  - 当 provider 配置变化时，计算新旧 LaunchPlan 指纹 → 对比缓存指纹 → 指纹不匹配的 agent 标记为 affected。
  - 只对 affected agent 执行重启/替换，未受影响 agent 保持原运行状态。
  - 指纹比较只使用稳定的输入字段（provider、model、startup_args、env 等），忽略运行时状态。
- [ ] `restart-required` 语义实现：
  - Config UI 保存 provider 启动相关配置后，只更新 `.ccb/ccb.config` 中的 desired 状态。
  - 不自动重启 provider，不热改正在运行的 provider 进程。
  - desired 状态与 live 状态差异对外可见：读模型暴露 `desired_config` / `live_config` / `drift_detected` / `restart_required`。
- [ ] 触发替换/重启的入口：
  - 用户主动调用 `ccb restart` / `ccb replace-agent` 时执行替换。
  - 或用户通过 Config UI "Apply & Restart" 按钮触发。
  - 替换流程内部调用 T03 并发 ready gate 验证重启后的 Agent Ready。
- [ ] 替换不波及未 affected agent：
  - 未 affected agent 的 binding、session、pane 保持，不被关闭或重建。
  - affected agent 启动失败只影响该 agent，不影响其他 agent。
- [ ] Herdr deferred / restart-intent 语义严格区分：
  - Herdr 记录 "deferred" 或 "restart-intent" 只表示动作被延后或待处理。
  - deferred 不得展示为 "provider 已 restart" 或 "Agent Ready"。
  - 只有 affected agent 实际通过 ready gate 后，deferred 才转为 agent-ready。
- [ ] desired/live 差异对外暴露：
  - `project_view.agent_status` 含 `desired_config`、`live_config`、`drift_detected` 字段。
  - Config UI 展示 drift 状态并标记 `restart-required` 或 `live-ok`。

**Validation:**

- `pytest -q test/test_v2_ccbd_start.py -k "affected_agent"`
- `pytest -q test/test_v2_ccbd_dispatcher.py -k "restart_required"`
- `pytest -q test/test_ccbd_project_view.py -k "config_drift"`
- 新增测试：单 agent 配置变化只标记该 agent 为 affected
- 新增测试：配置保存不触发自动重启，desired/live 差异可见
- 新增测试：替换时未 affected agent 保持不变
- 新增测试：deferred 不冒充 agent-ready，通过 ready gate 后才切换

**Evidence:** Affected agent 定位基于指纹比较，配置保存只更新 desired 不热改，替换只影响匹配到的 agent，desired/live 差异对外可观测。