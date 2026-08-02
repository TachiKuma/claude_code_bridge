---
doc_type: feature-implementation
feature: 2026-07-31-provider-runtime-on-herdr
status: completed
updated_at: 2026-08-03
---

# provider-runtime-on-herdr implementation

## 当前状态

S1 admission、S2 Backend-neutral runtime launch、S3 Provider runtime session payload、S4 Provider session lifecycle、S5 Ask/pend/completion authority、S6 Cancellation and provider pane restart surface、S7 Scope/regression/manual evidence 均已完成。当前进入实现后 review gate；CMD-011 只有逐 provider blocked evidence，不是 supported 证据。

## S1 Admission 记录

- 前置 `mux-backend-contract-herdr-v2`、`herdr-backend-client`、`ccbd-herdr-namespace-lifecycle` 均已是 roadmap done / feature accepted。
- provider CMD-003 admission focused pytest 通过：`224 passed`。
- `provider-runtime-on-herdr-admission-blocked.md` 已更新为 `status: passed`。

## S2 实现记录

本轮将 provider pane launch 的最小运行时边界从 tmux-only 入口中拆出：

- 新增 `lib/cli/services/runtime_launch_runtime/pane_runtime.py`，集中处理 assigned pane launch。Herdr pane ref 明确为 `backend_impl=herdr` 时走 `respawn_pane(pane_ref, command=[start_cmd], cwd=..., env={})`，并做一次 best-effort `capture_pane(lines=1)` 作为 launch evidence。
- `launch_tmux_runtime()` 保留旧函数名和 tmux 行为，但通过 `launch_runtime_pane()` 接收 Herdr `assigned_pane_ref`；Herdr identity 走 `set_pane_identity(pane_ref, ...)`，tmux identity 仍走原 `apply_ccb_pane_identity()`。
- `ensure_agent_runtime()` 在存在 Herdr `assigned_pane_ref` 时不再要求本机 `tmux` binary，但仍要求 provider executable。
- `runtime_launch._runtime_backend_factory()` 在 `namespace_backend_impl=herdr` 且有 `namespace_ref` 时选择 `get_backend('herdr')`，并把 namespace ref 绑定到 backend，供 HerdrBackend 校验 pane ref。
- ccbd start flow 继续在 Herdr namespace 缺少完整 namespace ref 或 assigned pane 时 deferred；当 namespace ref 和所有目标 agent pane 都齐备时，透传 `namespace_ref`、`assigned_pane_ref`、`namespace_backend_impl` 给 provider runtime。

## 验证证据

- `python -m pytest -q "test/test_runtime_launch_timings.py" --basetemp "D:/tmp/pytest-provider-runtime-s2-timings-factory" -p no:cacheprovider`  
  结果：`7 passed`
- `python -m pytest -q "test/test_v2_ccbd_start_flow.py" -k "herdr_namespace or herdr_assigned_pane" --basetemp "D:/tmp/pytest-provider-runtime-s2-start-flow" -p no:cacheprovider`  
  结果：`2 passed`
- `python -m pytest -q "test/test_v2_project_namespace_backend.py" -k "herdr or mux or namespace or pane" --basetemp "D:/tmp/pytest-provider-runtime-s2-namespace-backend" -p no:cacheprovider`  
  结果：`22 passed`
- `python -m pytest -q "test/test_runtime_launch_timings.py" "test/test_v2_ccbd_start_flow.py" "test/test_v2_project_namespace_backend.py" -k "launch_tmux_runtime_uses_herdr_assigned_pane_ref_without_tmux_fallback or skips_tmux_tool_check_for_herdr_assigned_pane or runtime_backend_factory_binds_herdr_namespace_ref or runtime_supervisor_start_defers_provider_runtime_for_herdr_namespace or runtime_supervisor_starts_provider_runtime_for_herdr_assigned_pane or v2_mux_backend_helpers_use_namespace_refs_without_tmux_fallback" --basetemp "D:/tmp/pytest-provider-runtime-s2-relevant-final" -p no:cacheprovider`  
  结果：`6 passed, 59 deselected`
- `python -m py_compile ...` 覆盖本轮修改的 runtime launch、start flow 和测试文件。结果：通过。
- `git diff --check -- <本轮修改文件>` 结果：通过。

## S3 实现记录

本轮把 provider runtime session payload 补成 backend-neutral 可恢复结构：

- 新增 `lib/provider_runtime/session_payload.py`，集中维护 `ProviderRuntimeBackendRef` 构造、completion source kind 到 roadmap 粗粒度 `completion_source` 的映射、Herdr namespace restore token redaction、session backend/pane id 解析和 provider payload protected shared keys 合并诊断。
- `write_session_file()` 增加 `backend_family`、`backend_impl`、`namespace_ref`、`pane_ref` 参数。Herdr payload 写入 `terminal="mux"`、`backend_impl="herdr"`、`namespace_ref`、`pane_ref`、`managed_home`、`completion_source`、`completion_source_kind`、`namespace_restore_token_present` 和 `provider_runtime_backend_ref`；raw `restore_token` 不写入 session JSON。
- provider payload 不再能覆盖 shared runtime keys，例如 `terminal`、`backend_impl`、`pane_id`、`tmux_socket_name`；冲突记录到 `provider_payload_conflicts`，provider-native keys 如 `codex_session_id` 仍正常保留。
- `launch_tmux_runtime()` 保留旧入口名，但把 S2 的 Herdr `assigned_pane_ref` / `namespace_ref` 透传给 session writer，确保真实 Herdr provider pane launch 后能写出 V2 payload。
- `TerminalBackendSelection.get_backend_for_session()` 识别 top-level `backend_impl="herdr"` 和 `provider_runtime_backend_ref.backend_impl="herdr"`，直接构造 Herdr backend 并绑定 `_ccb_project_namespace_ref`；未知 backend_impl fail-closed，不再默认回 tmux。legacy tmux/rmux/缺字段 session 继续走 tmux-compatible factory。

## S3 验证证据

- RED 证据：新增 S3 用例后，`python -m pytest -q "test/test_v2_runtime_launch_session_files.py" "test/test_terminal_runtime_backend_selection.py" --basetemp "D:/tmp/pytest-provider-runtime-s3-red" -p no:cacheprovider` 失败为 5 个预期缺口：writer 缺 backend refs 参数、provider payload 覆盖 shared keys、Herdr session resolver 回 tmux、provider_runtime_backend_ref 未识别、未知 backend 未 fail-closed。
- GREEN focused bundle：`python -m pytest -q "test/test_provider_runtime_session_payload_guard.py" "test/test_v2_runtime_launch_session_files.py" "test/test_terminal_runtime_backend_selection.py" "test/test_runtime_launch_timings.py" --basetemp "D:/tmp/pytest-provider-runtime-s3-focused-final-2" -p no:cacheprovider`  
  结果：`32 passed`
- `python -m py_compile "lib/provider_runtime/session_payload.py" "lib/cli/services/runtime_launch_runtime/session_files.py" "lib/cli/services/runtime_launch_runtime/tmux_runtime.py" "lib/cli/services/runtime_launch.py" "lib/terminal_runtime/backend_selection.py" "test/test_provider_runtime_session_payload_guard.py" "test/test_v2_runtime_launch_session_files.py" "test/test_terminal_runtime_backend_selection.py"`  
  结果：通过。
- `git diff --check -- "lib/provider_runtime/session_payload.py" "lib/cli/services/runtime_launch_runtime/session_files.py" "lib/cli/services/runtime_launch_runtime/tmux_runtime.py" "lib/cli/services/runtime_launch.py" "lib/terminal_runtime/backend_selection.py" "test/test_provider_runtime_session_payload_guard.py" "test/test_v2_runtime_launch_session_files.py" "test/test_terminal_runtime_backend_selection.py"`  
  结果：通过。

## S4 实现记录

本轮将 provider session lifecycle 的 liveness/log 边界从 tmux ownership 逻辑中拆开：

- `provider_runtime.session_payload` 增加 `pane_ref_from_session()` 和 `session_uses_tmux_compatible_pane()`，为 lifecycle 提供 canonical session backend 判断。
- `PaneLogProjectSessionBase` 和 `ClaudeProjectSession` 的 `pane_id` 读取改为使用 session payload helper，并暴露 `pane_ref`。Herdr session 可从 top-level `pane_ref` 或 `provider_runtime_backend_ref.pane_ref` 恢复 pane identity。
- `pane_log_support.lifecycle_common` 新增 backend-neutral `pane_lifecycle_target()` / `backend_is_alive()`。Herdr session 用 `pane_ref` 调用 backend `is_alive()` / `ensure_pane_log()`，没有 `ensure_pane_log` 时 best-effort 走 `capture_pane(lines=1)`；tmux-compatible session 保持原 tmux pane id 行为。
- `pane_log_support.lifecycle.ensure_pane()` 只在 tmux-compatible session 执行 `apply_session_tmux_identity()`、`inspect_tmux_pane_ownership()`、`tmux_rebound_pane()` 和 project-slot reclaim。Herdr capability unsupported 通过 `MuxCommandErrorV2` 转成 actionable failure detail，不再抛出或误走 tmux fallback。
- Claude/Codex 的 provider-specific attach helper 收敛到共享 attach，避免 Herdr `pane_ref` 被重新降级为字符串；Gemini/Opencode/Droid 已经使用共享 attach。

## S4 验证证据

- RED 证据：新增 S4 pane-log Herdr 用例后，`python -m pytest -q "test/test_pane_log_support_session.py" --basetemp "D:/tmp/pytest-provider-runtime-s4-red" -p no:cacheprovider` 失败为 2 个预期缺口：Herdr liveness 使用字符串 pane id、unsupported capability 未转为 actionable error。
- RED 证据：新增 Claude Herdr 用例后，`python -m pytest -q "test/test_pane_log_support_session.py" "test/test_claude_session_ensure_pane.py" "test/test_codex_session_ensure_pane.py" "test/test_gemini_session_ensure_pane.py" "test/test_opencode_session_ensure_pane.py" --basetemp "D:/tmp/pytest-provider-runtime-s4-claude-red" -p no:cacheprovider` 失败为 1 个预期缺口：Claude attach helper 将 Herdr pane_ref 降级为字符串。
- S4 focused bundle：`python -m pytest -q "test/test_pane_log_support_session.py" "test/test_claude_session_ensure_pane.py" "test/test_codex_session_ensure_pane.py" "test/test_gemini_session_ensure_pane.py" "test/test_opencode_session_ensure_pane.py" --basetemp "D:/tmp/pytest-provider-runtime-s4-focused-1" -p no:cacheprovider`  
  结果：`25 passed`
- CMD-005 focused：`python -m pytest -q "test/test_provider_runtime_session_payload_guard.py" "test/test_pane_log_support_session.py" "test/test_claude_session_ensure_pane.py" "test/test_gemini_session_ensure_pane.py" "test/test_opencode_session_ensure_pane.py" -k "session or pane or backend or herdr or mux or restore_token" --basetemp "D:/tmp/pytest-provider-runtime-s4-cmd005" -p no:cacheprovider`  
  结果：`15 passed`
- `python -m py_compile ...` 覆盖本轮修改的 provider runtime session payload、pane log support lifecycle、Claude/Codex session lifecycle 和新增测试。结果：通过。
- `git diff --check -- <本轮 S4 修改文件>` 结果：通过。

## 已知基线风险

- CMD-004 全量 runtime launch bundle 当前仍受既有 Codex bridge bootstrap 基线问题影响，失败为 `codex runtime bootstrap missing declared artifacts: input.fifo, output.fifo`。该问题在 S2 前已存在，本轮 focused Herdr launch 测试不依赖该路径。
- 全局 CMD-009 scope guard 当前会命中既有 dirty 文件 `test/test_herdr_backend_client.py` 的 Herdr client owner 路径；本轮改动文件范围内的 `git diff --check` 已通过，未触及 recovery、Mobile/Config UI、doctor/support、package/release/update/installer 或 Herdr socket schema/client owner。

## S5 实现记录

本轮保持 CCB provider execution / dispatcher completion tracker 为 completion authority，并把 Herdr 侧状态收敛为 diagnostics-only：

- 新增 `lib/provider_execution/completion_authority.py`，集中为 provider terminal decision 补 `completion_authority`、精确 `completion_source_kind` 和 roadmap 粗粒度 `completion_source`。
- `provider_execution.service_runtime.polling` 在 persist / emit terminal update 前统一补齐 authority diagnostics，保证 pending terminal decision 与 dispatcher 观察到的 decision 一致。
- `ccbd.services.dispatcher_runtime.polling_service` 在 Codex reply delivery acceptance gate 前调用同一 authority helper；声明 `completion_source_kind=herdr_agent_state` 或 `completion_source=herdr_agent_state` 的 completed verdict 会 fail closed 为 `herdr_agent_state_not_completion_authority`，Herdr agent state 仅保留 `herdr_agent_state_role=diagnostics_only`。
- `provider_execution.service_runtime.snapshots` 暴露 `completion_source_kind` / `completion_source`，让 active runtime snapshot 保留精确 completion source kind。
- Claude `idle_pane_round_result` terminal capture fallback 增加 `completion_fallback_source=terminal_capture`、`completion_fallback_kind=provider_declared`、`terminal_capture_role=provider_declared_fallback` 诊断标记，fallback 降级路径可见。
- 为 CMD-006/CMD-007 在 Native Windows 上稳定通过，补了两个窄兼容修复：runtime accelerator client 在缺少 `socket.AF_UNIX` 时返回 `AcceleratorError` 让 Codex polling 降级；AGY `export HOME=...` 解析在 Windows 下保留反斜杠路径。`test_v2_ask_service.py` 中两个 Windows path JSON fixture 改为 `json.dumps`，避免反斜杠生成无效 JSON。

## S5 验证证据

- RED 证据：`python -m pytest -q "test/test_provider_execution_service_runtime.py" "test/test_reply_delivery_polling_gate.py" --basetemp "D:/tmp/pytest-provider-runtime-s5-red" -p no:cacheprovider` 失败为 3 个预期缺口：terminal decision 缺 `completion_authority/completion_source_kind`、snapshot 缺 `completion_source_kind`、Herdr agent state completed verdict 未 fail closed。
- S5 focused：`python -m pytest -q "test/test_provider_execution_service_runtime.py" "test/test_reply_delivery_polling_gate.py" --basetemp "D:/tmp/pytest-provider-runtime-s5-green-2" -p no:cacheprovider`  
  结果：`19 passed`
- Completion focused：`python -m pytest -q "test/test_v2_completion_tracker.py" "test/test_v2_completion_orchestration.py" "test/test_provider_execution_service_runtime.py" "test/test_reply_delivery_polling_gate.py" --basetemp "D:/tmp/pytest-provider-runtime-s5-focused-final" -p no:cacheprovider`  
  结果：`26 passed`
- CMD-006：`python -m pytest -q "test/test_v2_phase2_ask.py" "test/test_v2_ask_service.py" "test/test_reply_delivery_start_completion.py" "test/test_v2_completion_orchestration.py" "test/test_cancel_flags.py" -k "ask or pend or completion or reply_delivery or cancel or provider" --basetemp "D:/tmp/pytest-provider-runtime-s5-cmd006-final" -p no:cacheprovider`  
  结果：`48 passed`
- CMD-007：`python -m pytest -q "test/test_claude_execution_polling.py" "test/test_gemini_execution_hook.py" "test/test_opencode_execution_polling.py" "test/test_native_cli_completion.py" "test/test_codex_reply_delivery.py" -k "completion or hook_artifact or reply_delivery or terminal_capture or herdr" --basetemp "D:/tmp/pytest-provider-runtime-s5-cmd007-final" -p no:cacheprovider`  
  结果：`26 passed, 23 deselected`
- CMD-010 guard：本轮 `lib/test` diff 和 untracked S5 files 扫描通过，未出现 `herdr_agent_state` 直接产生 completed verdict 的模式。
- `python -m py_compile ...` 覆盖本轮 S5 修改文件。结果：通过。
- `git diff --check -- <本轮 S5 修改文件>` 结果：通过。

## S6 实现记录

本轮补齐 Herdr cancellation / restart surface，但不接管 bounded recovery owner：

- `provider_execution.common_runtime.terminal.interrupt_and_clear_runtime_target()` 继续优先使用 tmux-compatible `send_key(C-c/Escape/C-u)`；当后端没有 `send_key` 但有 `send_text` 时，发送控制字符 `\x03\x1b\x15` 作为 best-effort interrupt，不把 backend 结果解释为 completion。
- `provider_execution.service.interrupt_active_submission()` 优先使用 runtime_state 中的结构化 `pane_ref`，没有安全 `pane_ref` 时才回退 `pane_id`。这让 Herdr cancel 能以 backend-neutral pane ref 定位目标，不要求 `%N` tmux pane id。
- `provider_execution.service_runtime.snapshots` 将安全的 `pane_ref` 暴露到 active runtime snapshot，仍过滤 backend/reader/prompt/reply_buffer 等非公开对象。
- review-fix 后收窄 `pane_ref` 语义：只有 `backend_impl=herdr` 且 `pane_id/session_name` 完整时才优先使用结构化 ref，否则回退字符串 `pane_id`；active runtime snapshot 对 `pane_ref` 做字段级 allowlist，仅公开 `backend_impl/pane_id/session_name/window_name/agent_slug`。
- `ccbd.handlers.project_restart` 对 Herdr namespace 的 restart 保持 `unsupported/deferred`，并返回明确 `restart_evidence`：`restart_surface=provider_runtime_required`、`respawn_evidence=not_attempted`、`session_binding_evidence=not_attempted`。该路径不构造 `TmuxBackend`，不调用 pane recovery/rebound。
- 修复 S6 基线红灯：`start_agent_runtime()` 在复用已 restored/healthy 的既有 provider session binding 且 authority 字段等价时，不再重复写 runtime store；Windows 路径分隔符差异按等价比较处理。
- `test/test_ccb_restart.py` 的 restart socket 用例局部隔离 shutdown project-stop teardown，避免当前 Windows 非 tmux 环境的 namespace backend auto-selection 干扰 restart RPC target 测试。

## S6 验证证据

- Warm reuse baseline：`python -m pytest -q "test/test_ccbd_start_agent_runtime.py::test_real_runtime_service_warm_reuse_preserves_restored_without_store_write" --basetemp "D:/tmp/pytest-provider-runtime-s6-warm-reuse" -p no:cacheprovider`  
  结果：`1 passed`
- Review-fix target focused：`python -m pytest -q "test/test_provider_execution_service_runtime.py::test_interrupt_active_submission_prefers_structured_pane_ref" "test/test_provider_execution_service_runtime.py::test_interrupt_active_submission_uses_control_input_without_send_key" "test/test_provider_execution_service_runtime.py::test_interrupt_active_submission_uses_pane_id_for_tmux_family_pane_ref" "test/test_provider_execution_service_runtime.py::test_interrupt_active_submission_falls_back_when_herdr_pane_ref_incomplete" "test/test_provider_execution_service_runtime.py::test_active_runtime_snapshots_expose_bounded_safe_state" --basetemp "D:/tmp/pytest-provider-runtime-s6-review-fix-targeted" -p no:cacheprovider`  
  结果：`5 passed`
- Restart evidence focused：`python -m pytest -q "test/test_ccb_restart.py::test_project_restart_agent_handler_defers_herdr_namespace_without_tmux_backend" "test/test_v2_ccbd_start_flow.py::test_project_restart_panes_handler_defers_herdr_without_scheduled_success" --basetemp "D:/tmp/pytest-provider-runtime-s6-restart-evidence" -p no:cacheprovider`  
  结果：`2 passed`
- CMD-008：`python -m pytest -q "test/test_ccbd_start_agent_runtime.py" "test/test_ccbd_health_assessment_provider_pane.py" -k "runtime or pane or restart or herdr or unsupported or deferred" --basetemp "D:/tmp/pytest-provider-runtime-s6-cmd008-rerun" -p no:cacheprovider`  
  结果：`18 passed`
- Cancel/runtime focused：`python -m pytest -q "test/test_cancel_flags.py" "test/test_provider_execution_service_runtime.py" -k "cancel or cancelled or runtime or pane or restart or herdr" --basetemp "D:/tmp/pytest-provider-runtime-s6-review-fix-cancel" -p no:cacheprovider`  
  结果：`21 passed`
- Restart focused：`python -m pytest -q "test/test_ccb_restart.py" "test/test_v2_ccbd_start_flow.py" -k "restart or herdr or deferred or unsupported" --basetemp "D:/tmp/pytest-provider-runtime-s6-restart" -p no:cacheprovider`  
  结果：`15 passed, 31 deselected`
- CMD-006：`python -m pytest -q "test/test_v2_phase2_ask.py" "test/test_v2_ask_service.py" "test/test_reply_delivery_start_completion.py" "test/test_v2_completion_orchestration.py" "test/test_cancel_flags.py" -k "ask or pend or completion or reply_delivery or cancel or provider" --basetemp "D:/tmp/pytest-provider-runtime-s6-review-fix-cmd006" -p no:cacheprovider`  
  结果：`48 passed`
- `python -m py_compile ...` 覆盖本轮 S6 修改文件。结果：通过。
- 本轮 8 个代码/测试文件范围 `git diff --check`、S6 forbidden content guard、CMD-010 Herdr agent state completed guard 均通过。

## S7 实现记录

本轮只补证据和 guard，不修改业务代码：

- 冻结当前 public provider catalog snapshot：`evidence/public-providers-snapshot.json`。
  - 来源为 `lib/provider_core/registry_runtime/builtin_backends.py` 的 `CORE_PROVIDER_NAMES + OPTIONAL_PROVIDER_NAMES`，并用 `build_default_provider_catalog(include_optional=True, include_test_doubles=False).providers()` 做等价 registry 输出。
  - 当前 public provider 数量为 20；相比 design 基线新增 `qoder`、`qoderclicn`，已纳入 snapshot 和 transcript rows。
- 生成 Native Windows x64 all-provider Herdr workflow transcript：`evidence/native-windows-x64-all-provider-herdr-workflow-transcript.md`。
  - Herdr CLI 可用：`herdr 0.7.5-preview.2026-07-29-44b3adb12552`。
  - `codex`、`claude`、`gemini`、`opencode`、`droid`、`cursor` 命令存在；其余 provider CLI 缺失。
  - 未执行真实 provider `ask` / `pend` / completion / cancel，因为该动作会向外部 provider/API 或本机 AI bridge 发请求，本轮没有明确生产 API 调用授权，也没有逐 provider credential readiness 证明。
  - 全部 20 个 public provider 均有 explicit blocked row；该证据满足“不得遗漏 provider”，但不支持宣称任何 provider supported。

## S7 验证证据

- Catalog focused：`python -m pytest -q "test/test_v2_provider_catalog.py" "test/test_v2_execution_registry.py" "test/test_v2_provider_core_registry.py" --basetemp "D:/tmp/pytest-provider-runtime-s7-catalog" -p no:cacheprovider`  
  结果：`9 passed`
- CMD-004：`python -m pytest -q "test/test_v2_runtime_launch.py" "test/test_runtime_launch_timings.py" "test/test_v2_runtime_launch_session_files.py" -k "runtime or launch or session or pane or mux or herdr or rmux" --basetemp "D:/tmp/pytest-provider-runtime-s7-cmd004" -p no:cacheprovider`  
  结果：120 秒超时且存在既有基线失败；`-x` 复跑首个失败为 `codex runtime bootstrap missing declared artifacts: input.fifo, output.fifo`，与 S4 已记录的 Codex bridge bootstrap 基线风险一致。已补 `evidence/cmd004-baseline-exemption.md`，下游只能将该项解释为已隔离的 baseline-risk，不能解释为 CMD-004 全量通过；QA 若要把 runtime launch regression 视作完全通过，必须先修复或重新基线 Codex bridge bootstrap artifacts。
- CMD-005：`python -m pytest -q "test/test_provider_runtime_session_payload_guard.py" "test/test_pane_log_support_session.py" "test/test_claude_session_ensure_pane.py" "test/test_gemini_session_ensure_pane.py" "test/test_opencode_session_ensure_pane.py" -k "session or pane or backend or herdr or mux or restore_token" --basetemp "D:/tmp/pytest-provider-runtime-s7-cmd005" -p no:cacheprovider`  
  结果：`15 passed`
- CMD-006：`python -m pytest -q "test/test_v2_phase2_ask.py" "test/test_v2_ask_service.py" "test/test_reply_delivery_start_completion.py" "test/test_v2_completion_orchestration.py" "test/test_cancel_flags.py" -k "ask or pend or completion or reply_delivery or cancel or provider" --basetemp "D:/tmp/pytest-provider-runtime-s7-cmd006" -p no:cacheprovider`  
  结果：`48 passed`
- CMD-007：`python -m pytest -q "test/test_claude_execution_polling.py" "test/test_gemini_execution_hook.py" "test/test_opencode_execution_polling.py" "test/test_native_cli_completion.py" "test/test_codex_reply_delivery.py" -k "completion or hook_artifact or reply_delivery or terminal_capture or herdr" --basetemp "D:/tmp/pytest-provider-runtime-s7-cmd007" -p no:cacheprovider`  
  结果：`26 passed, 23 deselected`
- CMD-008：`python -m pytest -q "test/test_ccbd_start_agent_runtime.py" "test/test_ccbd_health_assessment_provider_pane.py" -k "runtime or pane or restart or herdr or unsupported or deferred" --basetemp "D:/tmp/pytest-provider-runtime-s7-cmd008" -p no:cacheprovider`  
  结果：`18 passed`
- CMD-009：全局 scope guard 失败，命中既有 dirty `test/test_herdr_backend_client.py`（Herdr client owner 路径），非 S7 本轮文件；S7 scoped guard 对新增 evidence 文件通过。
- CMD-010：Herdr agent state completed guard 通过。
- `python -m json.tool "evidence/public-providers-snapshot.json"` 通过。
- `git diff --check -- <S7 evidence files>` 通过。

## 下一步

进入 `cs-code-review`。review 需要重点核对 S7 evidence 是否完整覆盖当前 provider catalog、blocked 归因是否没有被误投影为 supported，以及本轮是否未越界到 public validation matrix / recovery / support / release owner。
