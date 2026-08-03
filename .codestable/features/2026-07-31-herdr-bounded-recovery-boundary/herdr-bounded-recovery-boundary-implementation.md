---
doc_type: feature-implementation
feature: 2026-07-31-herdr-bounded-recovery-boundary
status: ready-for-review
implemented: 2026-08-03
---

# herdr-bounded-recovery-boundary implementation report

## 第一性原则 pre-pass

- 外部行为：Herdr backend 下 CCB 是唯一 recovery owner；Herdr auto restore 只有 `disabled` 可进入 recovery-capable path；public recovery event ledger 只暴露 sanitized refs 与 `restore_token_present`。
- 不可破约束：不把 Herdr agent state 当 completion/recovery success authority；不泄漏 raw restore token；不触碰 provider completion、Mobile/Config UI、doctor/support、package/release/update/installer/public matrix、Herdr socket schema/client owner。
- 最小充分改动：集中修改 runtime recovery policy、supervision recovery/event、lifecycle start recovery gate、pane lifecycle recovery primitive，并新增 focused tests。
- 必须不写：不新增 Herdr socket/client/schema；不发布、不 commit；不把 Herdr server `not_running` 伪造成 recovery pass。

## 按步骤改动与证据

### S1 Admission and policy contract

- 改动：
  - `lib/ccbd/services/runtime_recovery_policy.py`：新增 `HerdrRecoveryPolicy`、`HERDR_RECOVERY_OWNER="ccb"`、90 秒 probation、3 次 Herdr circuit threshold、auto-restore mode gate。
  - `test/test_ccbd_herdr_recovery_boundary.py`：新增 policy/auto-restore focused tests。
- TDD：
  - RED：`python -m pytest -q "test/test_ccbd_herdr_recovery_boundary.py" -k "herdr and owner" --basetemp "D:/tmp/ccb-herdr-recovery-s1-red" -p no:cacheprovider`，失败为缺少 Herdr policy API。
  - GREEN/VERIFY：同文件 focused 6 passed；restore helpers 2 passed；supervision recovery/backoff/blocked 9 passed。
- Admission：
  - checklist YAML passed。
  - roadmap items YAML passed。
  - provider-runtime-on-herdr acceptance/artifact refs check passed。

### S2 Evidence ledger and redaction

- 改动：
  - `lib/ccbd/supervision/recovery_events.py`：Herdr runtime recovery event 自动追加 `recovery_evidence_ledger`，包含 owner、auto restore mode、probation/circuit、health、action/reason、sanitized `namespace_ref`、`pane_ref`、`restore_token_present`、`herdr_agent_state_ref`。
  - 复用 `provider_runtime.session_payload.redacted_namespace_ref()` 与 `namespace_restore_token_present()`。
- TDD：
  - RED：`python -m pytest -q "test/test_ccbd_herdr_recovery_boundary.py" -k "ledger or redacts" --basetemp "D:/tmp/ccb-herdr-recovery-s2-red" -p no:cacheprovider`，失败为缺少 `recovery_evidence_ledger`。
  - GREEN/VERIFY：Herdr focused 7 passed；supervision recovery 9 passed；restore helpers 2 passed。
- Guard：
  - 本轮文件 scoped redaction/probation/circuit guard passed。
  - 全局 CMD-008 在当前 dirty worktree 误命中既有大 diff 中的 `support/unsupported` 与旧 raw-token fixture，作为基线风险记录到 S6。

### S3 Probation/circuit state machine

- 改动：
  - `runtime_recovery_policy.recovery_circuit_threshold()` 集中选择 Herdr policy threshold。
  - `lib/ccbd/supervision/recovery.py`、`recovery_transitions.py` 使用 runtime-aware threshold；非 Herdr 仍保留原 6 次阈值。
- TDD：
  - RED：`python -m pytest -q "test/test_ccbd_herdr_recovery_boundary.py" -k "circuit and threshold" --basetemp "D:/tmp/ccb-herdr-recovery-s3-red" -p no:cacheprovider`，第 4 次仍 `recovering`。
  - GREEN/VERIFY：Herdr threshold test 1 passed；generic circuit/backoff/provider-blocked 4 passed；Herdr focused 8 passed。

### S4 Recovery action routing

- 改动：
  - `runtime_recovery_policy.runtime_health_recoverable()` 支持 Herdr `process-dead`、`namespace-crashed`、`daemon-unavailable`。
  - lifecycle start recovery `support.py`/`slots.py` 改用同一 policy/capability gate；Herdr auto restore 非 `disabled` 时 blocked，不调用 refresh。
  - `recovery_events.py` 为 Herdr recovery ledger 映射 canonical action：`provider_restart`、`namespace_recover`、`daemon_recover`、`pane_recover`、`circuit_open`。
- TDD：
  - RED：S4 focused 首次 5 failed，缺 Herdr health admission 与 lifecycle gate；namespace action test 首次返回 `pane_recover`。
  - GREEN/VERIFY：S4 focused 8 passed；Herdr focused 16 passed；restore helpers 2 passed。

### S5 Provider pane primitive

- 改动：
  - `lib/provider_backends/pane_log_support/lifecycle_recovery.py`：非 tmux-compatible session 走 backend-neutral rebinding path，使用 structured pane target respawn，不要求 `%pane`，不调用 tmux ownership/identity；仍复用 crash log、provider recovery block 与 attach log。
- TDD：
  - RED：`python -m pytest -q "test/test_ccbd_herdr_recovery_boundary.py" -k "backend_neutral_pane_ref" --basetemp "D:/tmp/ccb-herdr-recovery-s5-red" -p no:cacheprovider`，返回 `respawn unavailable`。
  - GREEN/VERIFY：S5 case 1 passed；pane crash reason 9 passed；pane log support session 4 passed；Herdr focused 17 passed。

### S6 Regression and scope guard

- 自动化：
  - `python -m pytest -q "test/test_v2_ccbd_supervision_loop.py" "test/test_ccbd_restore_helpers.py" "test/test_pane_crash_reason.py" -k "recovery or recover or crash or backoff or blocked" --basetemp "D:/tmp/ccb-herdr-recovery-final-regression" -p no:cacheprovider`：20 passed, 24 deselected。
  - `python -m pytest -q "test/test_ccbd_herdr_recovery_boundary.py" -k "herdr or recovery or probation or circuit or restore or owner" --basetemp "D:/tmp/ccb-herdr-recovery-final-herdr" -p no:cacheprovider`：17 passed。
  - `python -m pytest -q "test/test_ccbd_runtime_refresh.py" "test/test_ccbd_health_monitor_rebind.py" -k "recovery or recover or herdr or restored or blocked" --basetemp "D:/tmp/ccb-herdr-recovery-final-refresh" -p no:cacheprovider`：3 passed, 3 deselected。
  - Scoped `git diff --check` on this feature files：passed。
  - 本轮文件 scope/content guard：passed。
  - 清洁度 grep `console.log|console.error|print|TODO|FIXME|XXX`：no matches。
- 基线风险：
  - checklist CMD-004 指向不存在的旧文件 `test/test_ccbd_rmux_supervision_recovery.py`；本轮使用实际存在的 `test/test_v2_ccbd_supervision_loop.py` 覆盖 rmux/tmux recovery baseline。
  - 全局 CMD-007/CMD-008 会扫描当前工作区此前 child 的大量 dirty diff，不能作为本轮 scoped cleanliness 结论；本轮未回滚或修改这些既有 dirty。

### S7 Native Windows recovery evidence

- 新增 evidence：`.codestable/features/2026-07-31-herdr-bounded-recovery-boundary/evidence/native-windows-x64-herdr-recovery-blocked-evidence.md`
- 结论：本机 Windows 10.0.19045，Herdr binary 存在；`herdr.exe --session "ccb-direct-shell-probe-20260802" status --json` 返回 server `not_running`、`capabilities=null`。
- 使用边界：这是 auto-restore-not-proven blocked evidence，不是 recovery pass，不证明 Windows release-ready。

## 最后一轮本地审计

- checklist YAML：passed。
- roadmap items YAML：passed。
- provider-runtime-on-herdr implementation admission：passed。
- Herdr focused tests：17 passed。
- recovery/restore/crash regression：20 passed, 24 deselected。
- runtime refresh/rebind focused：3 passed, 3 deselected。
- scoped diff check：passed。
- 方案外触碰：本轮未修改 provider completion、Mobile/Config UI、doctor/support、package/release/update/installer/public matrix、Herdr socket schema/client owner。

## 交付物索引

- Code:
  - `lib/ccbd/services/runtime_recovery_policy.py`
  - `lib/ccbd/supervision/recovery.py`
  - `lib/ccbd/supervision/recovery_transitions.py`
  - `lib/ccbd/supervision/recovery_events.py`
  - `lib/ccbd/services/dispatcher_runtime/lifecycle_start_runtime/recovery_runtime/support.py`
  - `lib/ccbd/services/dispatcher_runtime/lifecycle_start_runtime/recovery_runtime/slots.py`
  - `lib/provider_backends/pane_log_support/lifecycle_recovery.py`
- Tests:
  - `test/test_ccbd_herdr_recovery_boundary.py`
- CodeStable:
  - `herdr-bounded-recovery-boundary-checklist.yaml`
  - `evidence/native-windows-x64-herdr-recovery-blocked-evidence.md`

## 下一步

Goal lane implementation 完成，进入 `cs-code-review`。Review passed 后进入 QA；若 review 有 blocking findings，只修 review 指定范围。

## Review-fix 证据

- 目标：`REV-001`。修复 Herdr recovery metadata 未进入真实 `AgentRuntime` 持久化与 refresh/attach supervision 路径的问题。
- 改动：`AgentRuntime` / runtime store 增加 redacted backend refs、namespace/pane refs、token-presence、auto-restore mode 和 agent-state ref；provider runtime facts 从 session payload 提取并经 `RuntimeService.attach()`、attach records 和 registry 持久化；recovery event ledger 使用 runtime token-presence 布尔值，不读取或输出 raw token。
- RED：新增 runtime store roundtrip 与 refresh 透传测试首次因 `AgentRuntime` 缺字段失败；随后发现上层 `RuntimeService.attach()` 未透传新参数。
- GREEN/VERIFY：
  - `python -m pytest -q "test/test_ccbd_herdr_recovery_boundary.py" --basetemp "D:/tmp/ccb-herdr-review-fix-all-herdr2" -p no:cacheprovider`：19 passed。
  - `python -m pytest -q "test/test_v2_ccbd_supervision_loop.py" "test/test_ccbd_restore_helpers.py" "test/test_pane_crash_reason.py" -k "recovery or recover or crash or backoff or blocked" --basetemp "D:/tmp/ccb-herdr-review-fix-regression3" -p no:cacheprovider`：20 passed, 24 deselected。
  - `python -m pytest -q "test/test_v2_agent_store.py" "test/test_ccbd_runtime_refresh.py" "test/test_ccbd_health_monitor_rebind.py" -k "roundtrip or refresh_provider_binding or recovery or herdr" --basetemp "D:/tmp/ccb-herdr-review-fix-regression4" -p no:cacheprovider`：5 passed, 2 deselected。
- 边界：未修改 Herdr socket/client/schema、provider completion 或其他 roadmap child；真实 Herdr server 仍由 S7 blocked evidence 表示。

## Review-fix 证据（round 2）

- 目标：`REV-002`、`REV-003`、`REV-004`，对应 Laplace rereview 的 3 个 blocking findings。
- `REV-002` 修复：
  - 改动文件：`lib/provider_runtime/session_payload.py`、`lib/ccbd/services/provider_runtime_facts.py`、`test/test_ccbd_herdr_recovery_boundary.py`。
  - 处理方式：新增 provider runtime backend ref / generic restore-token redaction helper；`build_provider_runtime_facts()` 从 raw namespace ref 推导 `namespace_restore_token_present`，只持久化 redacted `namespace_ref` 和 redacted `provider_runtime_backend_ref.namespace_ref`。
  - 证据：新增 `test_herdr_refresh_redacts_raw_restore_token_from_runtime_record`，确认 refresh 后 `AgentRuntime.to_record()` 不含 raw token，且保留 presence bool。
- `REV-003` 修复：
  - 改动文件：`lib/ccbd/supervision/recovery_events.py`、`test/test_ccbd_herdr_recovery_boundary.py`。
  - 处理方式：`append_recovery_event()` details 入口先递归移除任意 key 为 `restore_token` 的字段，再生成 public details 和 recovery evidence ledger。
  - 证据：新增 `test_herdr_recovery_event_details_redact_nested_restore_tokens`，覆盖 `details.namespace_ref` 和 `details.provider_runtime_backend_ref.namespace_ref` 的 nested raw token。
- `REV-004` 修复：
  - 改动文件：`lib/ccbd/services/runtime_recovery_policy.py`、`lib/ccbd/supervision/loop_runtime.py`、`lib/ccbd/supervision/recovery.py`、`lib/ccbd/supervision/recovery_transitions.py`、`test/test_ccbd_herdr_recovery_boundary.py`。
  - 处理方式：新增 `should_record_recovery_capability_block()`，让 background loop 对 Herdr `observe-only|unsupported|unknown` recoverable health 进入 recovery；`recover_runtime()` 在 backend refresh 前写 durable `recover_blocked`，health 为 `provider-recovery-blocked`，ledger action 为 `blocked`。
  - 证据：新增 `test_herdr_auto_restore_not_disabled_records_blocked_recovery`，确认不调用 `refresh_provider_binding(recover=True)`，且事件/ledger 写入 blocked evidence。
- RED：
  - `python -m pytest -q "test/test_ccbd_herdr_recovery_boundary.py" --basetemp "D:/tmp/ccb-herdr-reviewfix-red" -p no:cacheprovider`：5 failed, 19 passed。失败点分别为 event details raw token 泄露、runtime record raw token 泄露、非 disabled Herdr auto-restore 未进入 recovery evidence path。
- GREEN/VERIFY：
  - `python -m pytest -q "test/test_ccbd_herdr_recovery_boundary.py" --basetemp "D:/tmp/ccb-herdr-reviewfix-green1" -p no:cacheprovider`：24 passed。
  - `python -m pytest -q "test/test_v2_ccbd_supervision_loop.py" "test/test_ccbd_restore_helpers.py" "test/test_pane_crash_reason.py" -k "recovery or recover or crash or backoff or blocked" --basetemp "D:/tmp/ccb-herdr-reviewfix-recovery-regression" -p no:cacheprovider`：20 passed, 24 deselected。
  - `python -m pytest -q "test/test_v2_agent_store.py" "test/test_ccbd_runtime_refresh.py" "test/test_ccbd_health_monitor_rebind.py" -k "roundtrip or refresh_provider_binding or recovery or herdr" --basetemp "D:/tmp/ccb-herdr-reviewfix-runtime-regression" -p no:cacheprovider`：5 passed, 2 deselected。
  - Scoped `git diff --check` on review-fix files：passed。
- 边界：
  - 本轮只修复 review blocking；未处理 `REV-005` 的真实 production `herdr_auto_restore_mode` producer，仍作为 QA/acceptance residual risk。
  - `lifecycle_start` 继续拒绝非 disabled Herdr auto-restore 且不调用 refresh；durable evidence 由 background supervision recovery path 写入，避免在无 event context 的 queue slot helper 中新增第二套事件写入路径。

## Review-fix 证据（round 3）

- 目标：`REV-006`、`REV-007`，对应 Sartre rereview 的 2 个 blocking findings。`REV-005` 保持 important residual risk，不在本轮 review-fix 扩范围实现 production capability producer。
- `REV-006` 修复：
  - 改动文件：`lib/agents/models_runtime/runtime_runtime/agent.py`、`lib/ccbd/services/runtime_runtime/attach_values.py`、`test/test_ccbd_herdr_recovery_boundary.py`。
  - 处理方式：`AgentRuntime.to_record()` 作为最终 runtime metadata 边界，输出前 redacts `namespace_ref.restore_token` 和 nested `provider_runtime_backend_ref.namespace_ref.restore_token`，同时合成 `namespace_restore_token_present`；`RuntimeService.attach()` normalization 也提前 redacts explicit raw refs。
  - 证据：新增 `test_agent_runtime_to_record_redacts_direct_raw_restore_token` 和 `test_runtime_service_attach_redacts_raw_restore_token`，覆盖直接构造与 attach 两条旁路。
- `REV-007` 修复：
  - 改动文件：`lib/ccbd/services/dispatcher_runtime/lifecycle_start_runtime/recovery_runtime/slots.py`、`test/test_ccbd_herdr_recovery_boundary.py`。
  - 处理方式：lifecycle-start 对 Herdr capability-blocked admission 调用同一 `mark_recovery_blocked()` transition，写 `recover_blocked` supervision event / Herdr recovery ledger；仍不调用 `refresh_provider_binding(recover=True)`，并且只对 `should_record_recovery_capability_block()` 命中的 Herdr recovery-capability block 写入，不覆盖既有 hard-blocked health。
  - 证据：新增 `test_lifecycle_start_blocked_herdr_auto_restore_writes_evidence`，覆盖 `observe-only` queue/start slot 路径的 durable blocked evidence。
- RED：
  - `python -m pytest -q "test/test_ccbd_herdr_recovery_boundary.py" --basetemp "D:/tmp/ccb-herdr-sartre-red" -p no:cacheprovider`：3 failed, 24 passed。失败点分别为 lifecycle-start 无 `recover_blocked` event、direct `AgentRuntime.to_record()` raw token 泄露、`RuntimeService.attach()` raw token 泄露。
  - 首次 GREEN 尝试暴露循环 import：`AgentRuntime` 不能依赖 `provider_runtime` 包；已改为本文件私有 sanitizer，避免 agents -> provider_runtime -> agents 反向导入。
- GREEN/VERIFY：
  - `python -m pytest -q "test/test_ccbd_herdr_recovery_boundary.py" --basetemp "D:/tmp/ccb-herdr-sartre-green3" -p no:cacheprovider`：27 passed。
  - `python -m pytest -q "test/test_v2_ccbd_supervision_loop.py" "test/test_ccbd_restore_helpers.py" "test/test_pane_crash_reason.py" -k "recovery or recover or crash or backoff or blocked" --basetemp "D:/tmp/ccb-herdr-sartre-recovery-regression" -p no:cacheprovider`：20 passed, 24 deselected。
  - `python -m pytest -q "test/test_v2_agent_store.py" "test/test_ccbd_runtime_refresh.py" "test/test_ccbd_health_monitor_rebind.py" -k "roundtrip or refresh_provider_binding or recovery or herdr" --basetemp "D:/tmp/ccb-herdr-sartre-runtime-regression" -p no:cacheprovider`：5 passed, 2 deselected。
  - Scoped `git diff --check` on Sartre review-fix files：passed。
- 边界：
  - 未修改 provider completion、Mobile/Config UI、doctor/support、package/release/update/installer/public matrix、Herdr socket schema/client owner。
  - 未宣称真实 Herdr recovery supported；`REV-005` 和 S7 Herdr server `not_running` 继续交给 QA/acceptance 作为 blocked/fail-closed evidence。

## Review-fix 证据（round 4）

- 目标：`R4-001`，对应 Bohr round 4 blocking finding。
- 改动文件：
  - `lib/ccbd/services/dispatcher_runtime/lifecycle_start_runtime/recovery_runtime/slots.py`
  - `test/test_ccbd_herdr_recovery_boundary.py`
- 处理方式：`iter_runnable_agent_slots()` 在生产 `tick_jobs()` 扫描 queued degraded runtime 时，若 Herdr recovery admission 返回 `blocked`，先复用 `_record_lifecycle_recovery_blocked()` 写 `recover_blocked` supervision event / Herdr recovery ledger，再跳过 slot；`drop` 仍保持原 backoff/drop 语义，不调用 refresh。
- RED：
  - `python -m pytest -q "test/test_ccbd_herdr_recovery_boundary.py" -k "tick_records_blocked" --basetemp "D:/tmp/ccb-herdr-r4-red" -p no:cacheprovider`：失败，`registry.current.health` 仍为 `process-dead`，证明 `tick_jobs()` 生产路径没有写 durable blocked evidence。
- GREEN/VERIFY：
  - `python -m pytest -q "test/test_ccbd_herdr_recovery_boundary.py" -k "tick_records_blocked" --basetemp "D:/tmp/ccb-herdr-r4-green-focused" -p no:cacheprovider`：1 passed, 27 deselected。
  - `python -m pytest -q "test/test_ccbd_herdr_recovery_boundary.py" -k "tick_records_blocked" --basetemp "D:/tmp/ccb-herdr-r4-idempotent" -p no:cacheprovider`：1 passed, 27 deselected，覆盖第二次 `tick_jobs()` 不重复写 `recover_blocked` event。
  - `python -m pytest -q "test/test_ccbd_herdr_recovery_boundary.py" --basetemp "D:/tmp/ccb-herdr-r4-green-all" -p no:cacheprovider`：28 passed。
  - `python -m pytest -q "test/test_ccbd_herdr_recovery_boundary.py" --basetemp "D:/tmp/ccb-herdr-r4-green-all2" -p no:cacheprovider`：28 passed。
  - `python -m pytest -q "test/test_v2_ccbd_supervision_loop.py" "test/test_ccbd_restore_helpers.py" "test/test_pane_crash_reason.py" -k "recovery or recover or crash or backoff or blocked" --basetemp "D:/tmp/ccb-herdr-r4-recovery-regression" -p no:cacheprovider`：20 passed, 24 deselected。
  - `python -m pytest -q "test/test_v2_agent_store.py" "test/test_ccbd_runtime_refresh.py" "test/test_ccbd_health_monitor_rebind.py" -k "roundtrip or refresh_provider_binding or recovery or herdr" --basetemp "D:/tmp/ccb-herdr-r4-runtime-regression" -p no:cacheprovider`：5 passed, 2 deselected。
  - `git diff --check -- "lib/ccbd/services/dispatcher_runtime/lifecycle_start_runtime/recovery_runtime/slots.py" "test/test_ccbd_herdr_recovery_boundary.py"`：passed。
  - `rg --line-number "console\\.log|console\\.error|TODO|FIXME|XXX" "lib/ccbd/services/dispatcher_runtime/lifecycle_start_runtime/recovery_runtime/slots.py" "test/test_ccbd_herdr_recovery_boundary.py"`：no matches。
- 边界：
  - 本轮只闭合 R4-001，没有实现 `REV-005` 的真实 production `herdr_auto_restore_mode` producer。
  - 未修改 provider completion、Mobile/Config UI、doctor/support、package/release/update/installer/public matrix、Herdr socket schema/client owner。
