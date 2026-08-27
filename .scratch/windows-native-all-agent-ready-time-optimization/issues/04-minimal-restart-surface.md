# 04：最小重启面与 Restart-Required 语义

**What to build:** 基于配置指纹定位受影响的 agent，只替换/重启匹配到的 agent，不扩散到未受影响 agent。Config UI 保存 provider 启动相关配置（API、model、startup_args、env）后，只更新 desired 状态并记录 `restart-required`；不热改正在运行的 provider。desired/live 差异始终对用户可见。

**Blocked by:** T02（需要缓存和指纹定位机制来判定 affected agent）。

**Status:** done（commit `528aa3c6`）

- [x] Affected agent 定位机制：
  - 当 provider 配置变化时，计算新旧 LaunchPlan 指纹 → 对比缓存指纹 → 指纹不匹配的 agent 标记为 affected。
  - 只对 affected agent 执行重启/替换，未受影响 agent 保持原运行状态。
  - 指纹比较只使用稳定的输入字段（provider、model、startup_args、env 等），忽略运行时状态。
- [x] `restart-required` 语义实现：
  - Config UI 保存 provider 启动相关配置后，只更新 `.ccb/ccb.config` 中的 desired 状态。
  - 不自动重启 provider，不热改正在运行的 provider 进程。
  - desired 状态与 live 状态差异对外可见：读模型暴露 `desired_config` / `live_config` / `drift_detected` / `restart_required`。
- [x] 触发替换/重启的入口：
  - 用户主动调用 `ccb restart` / `ccb replace-agent` 时执行替换。
  - 或用户通过 Config UI "Apply & Restart" 按钮触发。
  - 替换流程内部调用 T03 并发 ready gate 验证重启后的 Agent Ready。
- [x] 替换不波及未 affected agent：
  - 未 affected agent 的 binding、session、pane 保持，不被关闭或重建。
  - affected agent 启动失败只影响该 agent，不影响其他 agent。
- [x] Herdr deferred / restart-intent 语义严格区分：
  - Herdr 记录 "deferred" 或 "restart-intent" 只表示动作被延后或待处理。
  - deferred 不得展示为 "provider 已 restart" 或 "Agent Ready"。
  - 只有 affected agent 实际通过 ready gate 后，deferred 才转为 agent-ready。
- [x] desired/live 差异对外暴露：
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

**Evidence:** Affected agent 定位基于 `agents.launch_config_fingerprint` 的稳定 restart-bound 配置签名；Config UI 保存只写 desired 配置并记录 `config-restart-intent.json`，不会热改 live provider；provider settings 与 Config UI 均只记录实际 affected agent；`project_view` / `provider_control` 暴露 `desired_config`、`live_config`、`drift_detected`、`restart_required`，deferred restart intent 不会被投影为 Agent Ready。

**验证记录（2026-08-27）：**

- `pytest -q "test/test_config_ui.py" -k "save_records_only_restart_bound_changed_agents or validates_saves_with_digest_guard_and_hot_reloads"`：通过。
- `pytest -q "test/test_provider_control_settings.py"`：通过。
- `pytest -q "test/test_ccbd_start_preparation.py"`：通过。
- `pytest -q "test/test_ccbd_project_view.py" -k "provider_control or config_drift or restart_required or runtime_status"`：通过。
- `pytest -q "test/test_config_restart_intent.py"`：通过。
- `python -m compileall "lib/agents/launch_config_fingerprint.py" "lib/ccbd/start_preparation.py" "lib/cli/services/config_ui.py" "lib/ccbd/project_view/service.py"`：通过。
- `pytest -q "test/test_config_ui.py"`：当前本机环境缺少 `cryptography`，`prepare_config_ui` 导入 `mobile_gateway.relay_admission` 时失败；其余 37 项通过、1 项跳过。
