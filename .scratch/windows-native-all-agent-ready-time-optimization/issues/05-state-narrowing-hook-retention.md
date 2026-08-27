# 05：CCB 状态上报收窄与 Herdr Hook 保留加固

**What to build:** 确认并加固 CCB 不再通过 `HerdrAgentLifecycleBridge.sync()` 向 Herdr 持续同步 `AgentState.BUSY`、`AgentState.IDLE` 等普通工作状态的边界；确认 provider home 中的 Herdr 原生状态 hook 只做诊断保留不被删除；补充 `restart-required` vs `agent-ready` 的测试覆盖。

**NOTE:** 该工单的 `sync()` 停用 BUSY/IDLE 部分已有第一版实现（`lib/platforms/windows/herdr/lifecycle_bridge.py` sync 已 return False、`test/test_herdr_lifecycle_bridge.py` 已覆盖），本工单主要做加固和验证补充。

**Blocked by:** None（可以立即开始，与 T01 并行）。

**Status:** done

- [x] 确认 `HerdrAgentLifecycleBridge.sync()` 对 `AgentState.BUSY`、`AgentState.IDLE` 转发已停用：sync() 内部已 `del` 参数并 `return False`，没有向 Herdr 后端发送任何请求。
- [x] 确认既有测试覆盖 `sync_runtime` 调用 bridge.sync() 时不转发 activity state（`test_sync_runtime_does_not_forward_ccb_activity_state_to_herdr` 断言 reporter.calls == []）。
- [x] 确认 `test_bridge_reports_session_once_without_activity_state` 断言 BUSY/IDLE 不产生 Herdr 调用。
- [x] 确认 `filter_herdr_agent_hooks` 在 `herdr_hook_guard.py` 中只做诊断记录，不清除运行时所需 hook：当前返回克隆配置与 clear diagnostics，不删除 Herdr 原生观测 hook。
- [x] 补充测试：重复调用 sync() 带上不同 BUSY/IDLE 状态，Bridge 后端调用计数仍为 0。
- [x] 补充测试：provider home 配置生成时 `herdr-agent-state` hook 不被清除（确认 provider home 生成路径保留 hook）。
- [x] 补充测试：`restart-required` 状态与 `agent-ready` 状态的语义区分：配置保存后处于 restart-required 时，ready gate 不返回 true；只有 provider 实际重启并通过 health/ping 后才返回 true。
- [x] 补充 `restart-required` 语义的 e2e 行为覆盖：Config UI 保存 → desired 变更 → restart-required 标记出现 → agent 未重启时 `status` 显示 `restart-required` → agent 重启并通过 ready gate 后 restart-required 清除。
- [x] 确认 WezTerm 内启动不携带 `wezterm cli spawn` 额外 UI tab 的代码路径，改为优先 `herdr session attach <session>`。

**Validation:**

- `pytest -q test/test_herdr_lifecycle_bridge.py`
- `pytest -q test/test_observational_aggregation_integration.py -k "ccb_activity_state"`
- `pytest -q test/test_provider_hook_settings.py`
- `pytest -q test/test_v2_ccbd_dispatcher.py -k "sync_runtime"`
- 新增测试：多轮 sync() 调用不增加后端调用计数
- 新增测试：provider home 配置中 herdr-agent-state hook 保留
- 新增测试：restart-required 状态下 ready gate 返回 false

**Evidence:** Bridge sync() 已停用 BUSY/IDLE 转发、hook 仅诊断不删除、restart-required vs agent-ready 语义可测试覆盖。

**验证记录（2026-08-27）：**

- `pytest -q "test/test_herdr_lifecycle_bridge.py"`：通过。
- `pytest -q "test/test_observational_aggregation_integration.py" -k "ccb_activity_state"`：通过。
- `pytest -q "test/test_provider_hook_settings.py"`：通过。
- `pytest -q "test/test_ready_gate_evaluator.py" "test/test_config_restart_intent.py"`：通过。
- `pytest -q "test/test_config_ui.py" -k "saves_api_change_without_hot_reload_and_schedules_restart or hot_reload_keeps_matching_restart_intent_when_restart_is_required or restart_required_flows_into_ready_gate"`：通过。
- `pytest -q "test/test_provider_profiles.py" -k "preserves_herdr_agent_hooks"`：通过。
- `pytest -q "test/test_v2_start_foreground.py" -k "replaces_current_wezterm_pane_without_spawning or wezterm_spawn"`：通过。
- `python -m compileall "lib/ccbd/ready_gate/evaluator.py" "lib/cli/services/config_restart_intent.py" "lib/ccbd/start_flow_runtime/deps.py" "lib/ccbd/start_flow_runtime/service.py" "lib/ccbd/start_flow.py" "test/test_config_ui.py"`：通过。
- `git diff --check`：通过。
- `pytest -q "test/test_v2_ccbd_dispatcher.py" -k "sync_runtime"`：当前测试集中无匹配用例，62 项 deselected；实际 `sync_runtime` 覆盖位于 `test/test_herdr_lifecycle_bridge.py`。
- `pytest -q`：当前本机环境缺少 `cryptography`，测试收集阶段在 `mobile_gateway.relay_admission` 导入链失败；目标测试均已通过。
- `graphify update .`：通过；`graphify-out` 已更新，期间提示既有第三方 Gradle/Kotlin 文件语法提取警告。

**审查记录（2026-08-27）：**

- Standards 轴：无发现。
- Spec 轴：首轮指出 ready gate action 未按本次 targets 收窄、缺少 e2e 行为覆盖；已修复并复审无发现。
