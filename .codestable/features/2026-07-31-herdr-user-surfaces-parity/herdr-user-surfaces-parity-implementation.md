---
doc_type: feature-implementation
feature: 2026-07-31-herdr-user-surfaces-parity
status: implemented
implemented: 2026-08-03
---

# herdr-user-surfaces-parity implementation report

## 第一性原则 pre-pass

- 外部行为：Herdr public surfaces 将消费同一个 redacted projection contract，展示 capability status、support tier projection/source、beta/blocking gaps、degraded next action 和 sanitized refs。
- 不可破约束：不泄露 raw restore token、provider secret 或 terminal buffer 全量；不把当前 projection 写成最终 supported claim；不改 provider completion、package/release/update/installer、Herdr socket/schema/client owner。
- 最小充分改动：先建立共享 projection helper 与 focused contract tests，再按 checklist 逐步接入 ProjectView、ping、foreground attach、Mobile、doctor/diagnostics、Config UI。
- 必须不写：不在 S1 接入 surface rendering；不伪造 Mobile/Config UI pass；不把 Herdr refs 转成 tmux socket/session/%pane。

## 按步骤改动与证据

### S1 Admission and projection contract

- 退出信号：两个 upstream roadmap item done、acceptance passed、artifact/evidence refs 存在；projection 字段含 `capability_status`、`support_tier_projection`、`support_tier_projection_source`、`beta_gaps`、`blocking_gaps`、`degraded_next_action`、redacted refs。
- 改动：
  - `lib/ccbd/herdr_surface_projection.py`：新增 `HerdrSurfaceProjection` TypedDict 与 `build_herdr_surface_projection()`，统一保守投影 Herdr capability、support tier projection/source、beta/blocking gaps、degraded next action 和 redacted evidence refs。
  - `test/test_herdr_surface_projection.py`：新增 projection contract tests，覆盖 explicit blocked contract、recovery circuit blocked derivation、非 Herdr evidence 忽略。
- TDD：
  - RED：`python -m pytest -q "test/test_herdr_surface_projection.py"`，失败为 `ModuleNotFoundError: No module named 'ccbd.herdr_surface_projection'`。
  - GREEN/VERIFY：`python -m pytest -q "test/test_herdr_surface_projection.py"`：3 passed。
- Admission：
  - `PYTHONDONTWRITEBYTECODE=1 python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-31-herdr-user-surfaces-parity/herdr-user-surfaces-parity-checklist.yaml" --yaml-only`：passed。
  - `PYTHONDONTWRITEBYTECODE=1 python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml"`：passed。
  - checklist CMD-003 upstream acceptance gate：passed。
- 清洁度：
  - 本步未新增调试输出、临时待办标记、注释掉代码。
  - projection refs 复用 `provider_runtime.session_payload` redaction helper，测试确认 raw token 不出现在 payload string 中。

## 当前边界

### S2 ProjectView / ping source of truth

- 退出信号：ProjectView 与 ping payload 字段一致；`backend_impl=herdr`、`capability_status`、`support_tier_projection/source`、`blocking_gaps`、`degraded_next_action` 可断言；raw restore token 不出现。
- 改动：
  - `lib/ccbd/herdr_surface_projection.py`：新增 `build_herdr_runtime_surface_projection()`，集中拼装 Herdr runtime evidence，避免 ProjectView 与 ping agent 重复解释 runtime refs。
  - `lib/ccbd/project_view/service.py`：在 namespace view 和 agent record 上 additive 输出 `herdr_surface_projection`；非 Herdr namespace/runtime 不输出该字段。
  - `lib/ccbd/handlers/ping_runtime/payloads.py`：在 ccbd ping payload 顶层输出 Herdr namespace projection；在 agent ping `diagnostics` 输出 Herdr runtime projection。
  - `test/test_ccbd_project_view.py`、`test/test_v2_ccbd_ping_runtime.py`：新增 ProjectView namespace/runtime 与 ping ccbd/agent focused tests。
- TDD：
  - RED：ProjectView/ping 新测试先失败为缺少 `herdr_surface_projection`。
  - GREEN/VERIFY：
    - `python -m pytest -q "test/test_ccbd_project_view.py" -k "namespace_view_redacts_herdr_restore_token or agent_projects_herdr_runtime_surface"`：2 passed, 89 deselected。
    - `python -m pytest -q "test/test_v2_ccbd_ping_runtime.py" -k "herdr_runtime_surface or herdr_namespace_surface"`：2 passed, 9 deselected。
    - `python -m pytest -q "test/test_herdr_surface_projection.py"`：3 passed。
- 回归与基线风险：
  - `python -m pytest -q "test/test_ccbd_project_view.py" "test/test_v2_ccbd_ping_runtime.py" -k "herdr or backend or evidence or project_view or ping"`：101 passed, 1 failed。失败为 `test_build_ccbd_payload_prefers_lifecycle_phase_over_lease_mount_state` 在 Windows 上把 `Path('/home/...')` 序列化为反斜杠，断言仍期望正斜杠；与本轮 Herdr projection diff 无关。
- 清洁度：
  - `python -m py_compile "lib/ccbd/herdr_surface_projection.py" "lib/ccbd/project_view/service.py" "lib/ccbd/handlers/ping_runtime/payloads.py"`：passed。
  - scoped `git diff --check`：passed。
  - diff-only 调试输出/待办标记检查：no matches。

## 当前边界

### S3 Foreground attach

- 退出信号：fake Herdr attach 成功路径返回 Herdr summary；unsupported 路径错误含 beta gap/next action；不要求 tmux binary。
- 改动：
  - `lib/cli/services/start_foreground.py`：Herdr blocked/degraded attach error 追加 `herdr_surface_projection` 摘要，包含 capability status、support tier projection/source、beta gaps、blocking gaps 和 next action；supported attach path 保持 backend-neutral `attach_namespace()`。
  - `test/test_v2_start_foreground.py`：新增 blocked projection error test。
- TDD：
  - RED：`python -m pytest -q "test/test_v2_start_foreground.py" -k "herdr_attach_blocked_error_includes_projection"`，失败为错误信息缺 `capability_status=blocked`。
  - GREEN/VERIFY：
    - `python -m pytest -q "test/test_v2_start_foreground.py" -k "herdr_attach"`：5 passed, 12 deselected。
    - `python -m pytest -q "test/test_v2_start_foreground.py" -k "herdr or backend or attach or blocked"`：15 passed, 2 deselected。
  - `python -m py_compile "lib/cli/services/start_foreground.py"`：passed。
  - scoped `git diff --check`：passed。
- 边界：
  - 未改 tmux attach branch。
  - 未新增 Herdr socket/client/schema；只消费 ping payload 已提供的 redacted projection。

## 当前边界

### S4 Mobile terminal target v2

- 退出信号：Herdr target 不要求 tmux socket/session/%pane；pass 路径调用 backend primitive；blocked/degraded 路径返回 stable error code、reason 和 next action，且后续 supported 被阻塞。
- 改动：
  - `lib/mobile_gateway/service.py`：Herdr ProjectView payload 在 terminal history、message input、websocket attach target 三条路径上不再退回 `ProjectView tmux evidence is not attachable`；当 projection 表示 blocked/partial 时返回或抛出 stable `terminal_blocked` payload。
  - `lib/mobile_gateway/service.py`：Herdr supported projection 下，terminal history/message/websocket attach target 构造成 backend-neutral target，携带 `backend_impl="herdr"`、`namespace_ref`、`pane_ref`、capability flags；websocket reopen 校验接受当前 ProjectView 的 redacted Herdr pane ref，不要求 tmux pane list。
  - `lib/mobile_gateway/terminal.py`：Terminal target dataclasses 增加 backend-neutral 字段；非 tmux target 的 tmux command property fail closed，避免 supported fake path 触碰 tmux CLI。
  - `test/test_mobile_gateway_service.py`：新增 Herdr terminal history/message/websocket blocked tests，以及 history/message/websocket supported backend-neutral target tests。
- TDD：
  - RED：`python -m pytest -q "test/test_mobile_gateway_service.py" -k "herdr_blocked_payload or herdr_input_blocked_payload or herdr_attach_blocked_payload"`，3 failed，失败点均为 tmux evidence error 或缺 `terminal_blocked` payload。
  - RED：`python -m pytest -q "test/test_mobile_gateway_service.py" -k "herdr_backend_neutral_target"`，supported websocket path 失败为 `socket closed before expected bytes`；根因是 reopen 校验仍把 Herdr `pane_id` 当 tmux agent pane 校验。
  - GREEN/VERIFY：
    - `python -m pytest -q "test/test_mobile_gateway_service.py" -k "herdr_blocked_payload or herdr_input_blocked_payload or herdr_attach_blocked_payload"`：3 passed, 93 deselected。
    - `python -m pytest -q "test/test_mobile_gateway_service.py" -k "herdr_blocked_payload or herdr_input_blocked_payload or herdr_attach_blocked_payload or terminal_history_reads_selected_agent_scrollback or agent_message_submit_sends_plain_text_to_agent_pane"`：5 passed, 91 deselected。
    - `python -m pytest -q "test/test_mobile_gateway_service.py" -k "terminal_websocket_uses_herdr_backend_neutral_target"`：1 passed, 98 deselected。
    - `python -m pytest -q "test/test_mobile_gateway_service.py" -k "herdr_backend_neutral_target or herdr_blocked_payload or herdr_input_blocked_payload or herdr_attach_blocked_payload or terminal_history_reads_selected_agent_scrollback or agent_message_submit_sends_plain_text_to_agent_pane"`：8 passed, 91 deselected。
    - `python -m py_compile "lib/mobile_gateway/service.py" "lib/mobile_gateway/terminal.py"`：passed。
    - scoped `git diff --check`：passed。
    - diff-only 调试输出/待办标记检查：no matches。
- 基线风险：
  - `python -m pytest -q "test/test_v2_start_foreground.py" "test/test_mobile_gateway_terminal.py" "test/test_mobile_gateway_service.py" -k "herdr or backend or terminal or attach or blocked"`：56 passed, 74 deselected, 1 failed。失败为 `test_terminal_selects_client_compatible_with_target_server` 在 Windows 上创建无扩展名 shell 脚本作为 fake `tmux`，`resolve_tmux_binary()` 未识别为可执行；与 Herdr blocked payload diff 无关。
- 最新复测：
  - `python -m pytest -q "test/test_v2_start_foreground.py" "test/test_mobile_gateway_terminal.py" "test/test_mobile_gateway_service.py" -k "herdr or backend or terminal or attach or blocked"`：59 passed, 74 deselected, 1 failed；失败仍为同一个 Windows fake tmux 可执行性基线风险。
- 清洁度：
  - 未新增调试输出、临时待办标记、注释掉代码。
  - 未新增 Herdr socket/client/schema；supported fake path 只验证 backend-neutral target 被传入现有 operation seams。

## 当前边界

### S5 Doctor / mounted / diagnostics support surfaces

- 退出信号：doctor/ping/ps/layout status/project view/diagnostics bundle 显示一致 capability、support tier projection/source、beta gaps、degraded next action；bundle 来源为 redacted ccbd/generated artifact。
- 改动：
  - `lib/cli/services/herdr_surface.py`：新增 CLI support surface helper，从远端 ccbd ping projection 或本地 `ProjectNamespaceState` 生成 redacted Herdr projection。
  - `lib/cli/services/doctor_runtime/ccbd.py`：doctor ccbd summary 远端 ping projection 优先，本地 namespace state fallback。
  - `lib/cli/services/ps.py`、`lib/cli/services/layout_status.py`：mounted/namespace surface additive 输出 `herdr_surface_projection`。
  - `lib/cli/render_runtime/ops_views_common.py`、`ops_views_doctor.py`、`ops_views_basic.py`：doctor/ps/layout 共用稳定 Herdr projection render lines。
  - `lib/cli/services/diagnostics_runtime/bundle.py`：manifest 增加 `herdr_surface_projection_sources`，指向 generated doctor payload，不归档 raw Herdr refs。
  - `test/test_v2_tmux_cleanup_history.py`、`test/test_v2_cli_render.py`、`test/test_v2_ps_service.py`、`test/test_layout_cli.py`、`test/test_v2_diagnostics_bundle.py`：新增 S5 focused tests。
- TDD：
  - RED：`python -m pytest -q "test/test_v2_tmux_cleanup_history.py" "test/test_v2_cli_render.py" "test/test_v2_ps_service.py" "test/test_layout_cli.py" "test/test_v2_diagnostics_bundle.py" -k "herdr_projection_source or herdr_surface or herdr_namespace_surface or projects_herdr or traces_redacted_herdr"`：4 failed，失败为 doctor/ps/layout/bundle manifest 缺 Herdr projection。
  - RED：`python -m pytest -q "test/test_v2_cli_render.py" -k "render_ps_and_layout_include_herdr_surface_projection"`：1 failed，失败为 ps/layout render 未输出 `herdr_surface` lines。
  - GREEN/VERIFY：
    - `python -m pytest -q "test/test_v2_tmux_cleanup_history.py::test_doctor_summary_projects_herdr_surface_from_remote_ping" "test/test_v2_cli_render.py::test_render_ps_and_doctor_keep_expected_line_shapes" "test/test_v2_cli_render.py::test_render_ps_and_layout_include_herdr_surface_projection" "test/test_v2_ps_service.py::test_ps_summary_projects_herdr_namespace_surface" "test/test_layout_cli.py::test_layout_status_projects_herdr_namespace_surface" "test/test_v2_diagnostics_bundle.py::test_export_diagnostic_bundle_traces_redacted_herdr_projection_source"`：6 passed。
    - `python -m py_compile "lib/cli/services/herdr_surface.py" "lib/cli/services/doctor_runtime/ccbd.py" "lib/cli/services/ps.py" "lib/cli/services/layout_status.py" "lib/cli/render_runtime/ops_views_common.py" "lib/cli/render_runtime/ops_views_doctor.py" "lib/cli/render_runtime/ops_views_basic.py" "lib/cli/services/diagnostics_runtime/bundle.py"`：passed。
    - scoped `git diff --check`：passed。
    - diff-only 调试输出/待办标记检查：no matches。
- 基线风险：
  - `python -m pytest -q "test/test_ccbd_project_view.py" "test/test_v2_ccbd_ping_runtime.py" "test/test_v2_tmux_cleanup_history.py" "test/test_v2_cli_render.py" "test/test_v2_diagnostics_bundle.py" "test/test_v2_ps_service.py" "test/test_layout_cli.py" -k "herdr or backend or evidence or diagnostics or project_view or ping or doctor or mounted or ps or layout"`：133 passed, 30 deselected, 11 failed。失败归因于既有 Windows 基线：ping `/home/...` 路径反斜杠序列化、doctor tmux command Windows quoting、diagnostics bundle 深临时路径过长/路径归档形状、layout dynamic-smoke 依赖 tmux 环境；与本步 Herdr projection diff 无关。
- 清洁度：
  - 未新增调试输出、临时待办标记、注释掉代码。
  - diagnostics manifest 只记录 generated doctor projection source，未新增 raw restore token/provider secret/terminal buffer 归档。

## 当前边界

### S6 Config UI readonly status

- 退出信号：Config UI readonly endpoint 或 `/api/session` 显示 backend status/capability/beta gaps/support tier projection；Config UI pass 是 supported hard gate；config save/apply/reload tests 不变。
- 改动：
  - `lib/cli/services/config_ui.py`：新增 `_config_ui_session_payload()`，`/api/session` 在 Herdr namespace state 存在时 additive 输出 `herdr_surface_projection` 与 `config_ui_readonly_status`；无 Herdr state 时保持原 session payload 字段。
  - `lib/cli/services/config_ui.py`：`config_ui_readonly_status` 对 Herdr `supported` 输出 `pass`，对 partial/blocked/unsupported 输出 `blocked`，避免后续 supportability 把非 pass 误判为 supported。
  - `test/test_config_ui.py`：新增纯函数级 Herdr readonly session payload test，确认 raw restore token 不泄露。
- TDD：
  - RED：`python -m pytest -q "test/test_config_ui.py" -k "herdr_readonly_status"`，失败为 `AttributeError: module 'cli.services.config_ui' has no attribute '_config_ui_session_payload'`。
  - GREEN/VERIFY：
    - `python -m pytest -q "test/test_config_ui.py" -k "herdr_readonly_status"`：1 passed, 28 deselected。
    - `python -m pytest -q "test/test_config_ui.py::test_config_ui_session_projects_herdr_readonly_status" "test/test_config_ui.py::test_config_ui_provider_capabilities_use_current_safe_model_sources"`：2 passed。
    - `python -m py_compile "lib/cli/services/config_ui.py"`：passed。
    - scoped `git diff --check`：passed。
    - diff-only 调试输出/待办标记检查：no matches。
- 基线风险：
  - `python -m pytest -q "test/test_config_ui.py" -k "herdr_readonly_status or serves_token_guarded_page_and_project_session or validates_saves_with_digest_guard_and_hot_reloads or saves_api_change_without_hot_reload_and_schedules_restart or safe_apply_clears_matching_save_only_restart_intent"` 在当前 Windows 环境超时；这些 server-based Config UI 回归启动本地 HTTP server，无法在本轮作为归因证据。S6 采用纯函数 session payload test 与 provider capabilities test 覆盖 readonly contract 和无关 capabilities 回归。
- 清洁度：
  - 未新增调试输出、临时待办标记、注释掉代码。
  - Config UI 未改变 validate/save/render/apply/reload 路由，只改变 `/api/session` 只读 payload。

### S7 Regression and scope guard

- 退出信号：existing public surface tests 通过；新增 Herdr surface tests 通过；无 provider completion/package/release/update/installer/support final claim/Herdr socket schema-client/raw token 越界。
- 改动：
  - `lib/storage/path_helpers.py`、`lib/ccbd/handlers/ping_runtime/payloads.py`、`lib/storage_classification/service.py`、`lib/storage_classification/models.py`、`lib/mobile_gateway/service.py`、`lib/cli/services/diagnostics_runtime/sources.py`：统一 public JSON / archive / storage summary 中的路径展示为 POSIX 分隔符，修复 Native Windows 下 payload 与 tar manifest 形状漂移。
  - `lib/cli/services/doctor_runtime/system.py`、`lib/cli/services/doctor_runtime/ccbd.py`：修复 POSIX-like `/tmp`、`/private/tmp` 路径在 Windows resolve 后的 temporary-root 识别。
  - `lib/cli/services/diagnostics_runtime/bundle.py`：diagnostics bundle staging 改用系统临时目录，避免在 project `.ccb/ccbd/support` 下递归 stage 自身并触发 Windows 长路径。
  - `lib/mobile_gateway/terminal.py`、`test/test_mobile_gateway_terminal.py`：`resolve_tmux_binary()` 在 Windows 支持 `PATHEXT` 候选，测试 fake tmux 按平台创建 `.cmd` 或 POSIX shell script。
  - `lib/mobile_gateway/service.py`、`test/test_mobile_gateway_service.py`：Mobile artifact injection 支持 Windows 裸绝对路径和 `file:///C:/...`；Claude native transcript discovery fixture 使用短 work_dir；POSIX-only handoff mode 断言不在 Windows 执行。
  - `lib/cli/services/config_ui.py`、`test/test_config_ui.py`：Config UI prepare 不阻塞外部 provider CLI model probing；server close 唤醒 `handle_request()` loop；API config text 输出规范化为 LF；POSIX token-file permission test 在 Windows skip。
  - `herdr-user-surfaces-parity-checklist.yaml`、`herdr-user-surfaces-parity-design.md`：CMD-004/CMD-006 中过期的 `test/test_cli_doctor_supervision.py` 替换为当前 `test_doctor_runtime_identity.py` 与 `test_doctor_active_inbound_diagnostics.py`。
- 验证：
  - `python -m pytest -q test/test_ccbd_project_view.py test/test_v2_ccbd_ping_runtime.py test/test_doctor_runtime_identity.py test/test_doctor_active_inbound_diagnostics.py test/test_v2_cli_render.py test/test_v2_diagnostics_bundle.py -k "herdr or backend or evidence or diagnostics or project_view or ping or doctor or mounted or ps or layout"`：127 passed, 29 deselected。
  - `python -m pytest -q test/test_v2_start_foreground.py test/test_mobile_gateway_terminal.py test/test_mobile_gateway_service.py test/test_config_ui.py -k "herdr or backend or terminal or attach or blocked or config or readonly"`：88 passed, 1 skipped, 74 deselected。
  - `python -m pytest -q test/test_terminal_runtime_tmux_attach.py test/test_mobile_gateway_terminal.py test/test_mobile_gateway_service.py test/test_ccbd_project_view.py test/test_doctor_runtime_identity.py test/test_doctor_active_inbound_diagnostics.py`：217 passed。
  - checklist CMD-007 scope/redaction guard：passed。
  - `git diff --check`：passed。
  - `python -m py_compile lib/storage/path_helpers.py lib/ccbd/handlers/ping_runtime/payloads.py lib/cli/services/doctor_runtime/system.py lib/cli/services/doctor_runtime/ccbd.py lib/cli/services/diagnostics_runtime/bundle.py lib/cli/services/diagnostics_runtime/sources.py lib/storage_classification/models.py lib/storage_classification/service.py lib/mobile_gateway/terminal.py lib/mobile_gateway/service.py lib/cli/services/config_ui.py`：passed。
- 清洁度：
  - 未修改 provider completion、package/release/update/installer/support final claim 或 Herdr socket/schema/client owner。
  - scope guard 覆盖 staged/unstaged/untracked `lib/`、`test/`、`bin/`、`scripts/`、`docs/`、顶层 package/install/README forbidden paths。
  - diagnostics manifest 与 public payload 保持 redacted source，未新增 raw restore token/provider secret/terminal buffer 全量归档。

## 当前边界

- S7 Regression and scope guard 已完成；S8 Native Windows surface transcript 已在下节记录。

### S8 Native Windows surface transcript

- 退出信号：transcript 显示 Herdr backend evidence、capability/support tier projection/beta gaps/degraded next action；Mobile/Config partial/degraded 只能作为 blocked evidence；缺 host/Herdr 时 acceptance blocked。
- 证据：
  - 新增 `.codestable/features/2026-07-31-herdr-user-surfaces-parity/evidence/cmd-008-native-windows-surface-transcript.md`。
  - Host fresh preflight：Windows native x64 / AMD64 / Python 64bit；`C:\Users\Administrator\AppData\Local\Programs\Herdr\herdr.exe --version` 输出 `herdr 0.7.5-preview.2026-07-29-44b3adb12552`。
  - 同 roadmap true-host Herdr namespace 证据复用：`.codestable/features/2026-07-31-ccbd-herdr-namespace-lifecycle/evidence/cmd-013-native-windows-herdr-transcript.md` verdict `passed`，覆盖 Herdr namespace create、ccbd ping、foreground attach、reload、restart deferred、kill/post-kill。
  - Surface harness fresh transcript 覆盖 foreground attach pass/blocked、Mobile history/message/attach pass/blocked、Config UI blocked/pass gate、ping、project view、doctor、mounted Herdr projection。
- 验证：
  - `python -m pytest -q "test/test_v2_start_foreground.py::test_start_foreground_herdr_attach_uses_builder_without_tmux_binary" "test/test_v2_start_foreground.py::test_start_foreground_herdr_attach_blocked_error_includes_projection" "test/test_mobile_gateway_service.py::test_terminal_history_returns_herdr_blocked_payload" "test/test_mobile_gateway_service.py::test_terminal_history_uses_herdr_backend_neutral_target" "test/test_mobile_gateway_service.py::test_agent_message_submit_returns_herdr_input_blocked_payload" "test/test_mobile_gateway_service.py::test_agent_message_submit_uses_herdr_backend_neutral_target" "test/test_mobile_gateway_service.py::test_terminal_attach_target_raises_herdr_attach_blocked_payload" "test/test_mobile_gateway_service.py::test_terminal_websocket_uses_herdr_backend_neutral_target" "test/test_config_ui.py::test_config_ui_session_projects_herdr_readonly_status" "test/test_v2_cli_render.py::test_render_ps_and_layout_include_herdr_surface_projection"`：10 passed。
- 清洁度：
  - transcript 不包含 raw restore token sentinel、provider secret 或 terminal buffer 全量。
  - Mobile blocked 样例保持 `status=blocked`；Config UI partial 样例保持 `config_ui_readonly_status.status=blocked`；未输出最终 supported claim。

## 当前边界

- S1-S8 implementation checklist 全部完成。
- 下一步进入 feature review / QA / acceptance；feature 仍未 acceptance passed，roadmap goal 不标 complete。
