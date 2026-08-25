# 05：防 Herdr hook 与 seq 架空 CCB 权威

**What to build:** CCB 管理的 provider home 不安装 Herdr 原生 agent hook；当环境中存在 hook 或竞争来源风险时，系统能暴露诊断信息并保持 `source=ccb` 权威，避免 hook 的 `time_ns` seq 架空 CCB 的单调 seq。

**Blocked by:** 02：`source=ccb` 成为 CCB 管理 pane 的身份权威.

**Status:** done

- [x] CCB 管理的 provider home 创建或更新流程不会安装 Herdr 原生 agent hook。
- [x] 如果检测到 CCB 管理范围内存在 Herdr hook 竞争风险，系统提供明确诊断，而不是静默采纳 hook 权威。
- [x] hook 产生的更细运行时事实不得替代 `source=ccb` 的身份/provider 权威。
- [x] hook 的 `time_ns` 级 seq 不得使 CCB 管理 pane 的 CCB 来源状态永久失效。
- [x] CCB 的 agent 状态上报保持单调 seq 约束，旧状态不能覆盖新状态。
- [x] 已存在的非 CCB hook 产物可以作为运行时事实被观察，但不能改变业务完成判定。
- [x] 局部门禁覆盖 provider home 不装 hook、竞争风险可诊断、seq 架空被阻断和 CCB source 权威保持。

**Validation:**

- `pytest -q test/test_provider_profiles.py::test_materialize_claude_home_config_filters_herdr_agent_hooks_with_diagnostics test/test_provider_profiles.py::test_materialize_gemini_home_config_filters_herdr_agent_hooks_with_diagnostics test/test_provider_hook_settings.py::test_prepare_provider_workspace_filters_herdr_codex_hooks_with_diagnostics test/test_ccbd_project_view.py::test_project_view_provider_control_exposes_redacted_herdr_hook_risk`
- `pytest -q test/test_provider_profiles.py::test_materialize_claude_home_config_merges_source_and_managed_hooks test/test_provider_profiles.py::test_materialize_gemini_home_config_preserves_runtime_hooks test/test_provider_hook_settings.py::test_prepare_provider_workspace_preserves_configured_codex_command_hooks test/test_provider_hook_settings.py::test_prepare_provider_workspace_preserves_omx_native_codex_hooks`
- `python -m compileall -q lib/provider_core/herdr_hook_guard.py lib/provider_backends/claude/launcher_runtime/home.py lib/provider_backends/gemini/launcher_runtime/home.py lib/provider_profiles/codex_home_config.py lib/ccbd/project_view/service.py test/test_provider_profiles.py test/test_provider_hook_settings.py test/test_ccbd_project_view.py`

**Evidence:** 新增共享 Herdr hook guard，Claude/Gemini/Codex managed home 写入 hooks 前会过滤 `herdr-agent-state`、`herdr agent-state` 和 `report_agent_session` 类原生 hook；检测到竞争风险时写入 `.ccb-herdr-hook-diagnostics.json`，project view 的 `provider_control.herdr_hook_risk` 只暴露状态、原因、`source=ccb` 权威与 seq 策略，不泄漏 hook command。普通 provider hooks 与允许的 Codex 原生 hooks 保持可继承。
