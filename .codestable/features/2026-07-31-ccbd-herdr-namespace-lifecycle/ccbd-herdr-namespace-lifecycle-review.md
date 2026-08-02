---
doc_type: feature-review
feature: 2026-07-31-ccbd-herdr-namespace-lifecycle
status: passed
reviewed: 2026-08-02
round: 4
lane_a_state: completed
lane_a_ref: "019fc330-e839-7e31-9c5b-b67371b7e53d"
lane_a_reason: "Round 4 独立 Task agent reviewer Confucius returned passed；Round 3 blocking/important closure 已经核验关闭。"
lane_b_state: completed
lane_b_ref: "ocr-sync-2026-08-02-round4"
lane_b_reason: "Round 4 OCR final rerun only hit controller env predicate medium；本地核验为当前 scope 噪声：controller predicate 只认 capability report/socket ref，且比 terminal runtime 的任一 CCB_HERDR_* configured 判定更窄。"
---

# ccbd-herdr-namespace-lifecycle 代码审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-31-ccbd-herdr-namespace-lifecycle/ccbd-herdr-namespace-lifecycle-design.md`
- Checklist: `.codestable/features/2026-07-31-ccbd-herdr-namespace-lifecycle/ccbd-herdr-namespace-lifecycle-checklist.yaml`
- Evidence pack: none
- Gate results: none
- DoD results: none
- Implementation evidence: `.codestable/features/2026-07-31-ccbd-herdr-namespace-lifecycle/ccbd-herdr-namespace-lifecycle-implementation.md`
- CMD-013 evidence: `.codestable/features/2026-07-31-ccbd-herdr-namespace-lifecycle/evidence/cmd-013-native-windows-herdr-transcript.md`
- Diff basis: 当前工作区 unstaged/untracked diff；存在大量前置 feature dirty diff，结论只覆盖可归因到本 feature 与本轮 review-fix 的代码。
- Review mode: qa-fix-rereview-required
- Baseline dirty files: `.codestable`、`lib/`、`test/` 多处历史变更仍未提交；`provider-runtime-on-herdr-admission-blocked.md` 属于后续 admission 产物，不纳入本 feature review。

### Independent Review

- Detection: Task agent 可用；OCR CLI 可用。
- 环节 A 独立隔离 Task agent: Round 1 completed，ref `019fc309-1391-7ce1-9346-e2c428dfd9db`；Round 2 completed，ref `019fc319-dbea-7041-9935-20d09f6f3690`；Round 3 completed，ref `019fc327-c769-7bc2-b827-d449fa537260`，changes-requested；Round 4 completed，ref `019fc330-e839-7e31-9c5b-b67371b7e53d`，passed。
- 环节 B OCR CLI: Round 1 completed；Round 2 completed，ref `ocr-sync-2026-08-02-round2`；Round 3 completed；Round 4 completed，ref `ocr-sync-2026-08-02-round4`。
- OCR severity mapping: High→blocking/important, Medium→nit/suggestion, Low→discarded。
- Merge policy: Round 1/2/3/4 结果已本地事实核验并合并；Round 4 独立 reviewer 无 blocking/important。
- Gate effect: review gate passed；可进入 `ccbd-herdr-namespace-lifecycle` QA 定稿。

## 2. Diff Summary

- 新增：`lib/ccbd/reload_sensitive_diagnostics.py`；本 review 报告。
- 修改：`lib/ccbd/services/project_namespace_runtime/additive_patch_apply.py`、`lib/ccbd/reload_apply_stages.py`、`lib/ccbd/start_flow_runtime/service.py`、`test/test_ccbd_reload_apply.py`、`test/test_v2_ccbd_start_flow.py`、`test/test_herdr_backend_client.py`。
- 删除：none。
- 未跟踪 / staged：`provider-runtime-on-herdr-admission-blocked.md` 与 `lib/ccbd/reload_sensitive_diagnostics.py` 当前未跟踪；前者不属于本 review 范围，后者属于本轮修复。
- 风险热点：restore token public diagnostics 泄露、Herdr deferred provider runtime readiness 误报、跨 session namespace ref、历史 dirty diff 归因。
- QA-fix 增量：`backend.py` 新增 requested session alias map，解决 Herdr backend authoritative server session name 与 desired session alias 不一致时的 ensure 回归。

## 3. Adversarial Pass

- 假设的生产 bug：Herdr 的 internal namespace evidence 或 deferred runtime 状态被当成 public/success evidence，导致 token 泄露或启动报告假阳性。
- 主动攻击过的反例：restore_session token mismatch、reload namespace patch failed、socket handler payload、CLI renderer、Herdr provider runtime deferred、不同 session namespace ref、dirty diff 归因。
- 结果：REV-001、REV-002、OCR-002 已修；OCR-001 归为前置 dirty residual risk；需要 Round 2 独立复审验证修复没有引入新问题。

## 4. Findings

### blocking

- [x] REV-001 `lib/ccbd/services/project_namespace_runtime/additive_patch_apply.py:225` reload namespace patch failure 会把 `MuxCommandErrorV2.evidence` 原样传播到 public diagnostics。
  - Source: independent-agent。
  - Evidence: `NamespacePatchApplyResult.to_record()`、`reload_apply_stages.namespace_patch_failed()` 和 reload renderer 会公开 `error_evidence`；Herdr restore error evidence 含 `expected_restore_token` / `actual_restore_token`。
  - Impact: raw restore token 可能进入 socket payload、CLI 输出或日志，违反 design 的 public namespace payload redaction 契约。
  - Closure: 新增 `ccbd.reload_sensitive_diagnostics`；`NamespacePatchApplyResult.to_record()`、`_failure_result()`、`namespace_patch_failed()` 统一脱敏 `*restore_token` key。
  - Verification: `python -m pytest -q "test/test_ccbd_reload_apply.py" -k "namespace_patch_failure or runtime_mount_defers_provider_runtime_for_herdr_namespace" --basetemp "D:/tmp/pytest-ccb-herdr-review-reload-2" -p no:cacheprovider` -> 3 passed。

### important

- [x] REV-002 `lib/ccbd/start_flow_runtime/service.py:144` Herdr provider runtime deferred 后仍把 T4/T6 readiness 标为 reached。
  - Source: independent-agent。
  - Evidence: Herdr namespace 分支返回 deferred agent result，但后续 readiness recorder 无条件标记 `T4_requested_agents_ready`，并在 requested agents 等于 desired agents 时标记 `T6_fully_warm`。
  - Impact: startup report 可能显示 fully warm，掩盖 provider runtime 尚未启动的真实状态，影响 provider-runtime-on-herdr admission 和后续 QA 判断。
  - Closure: Herdr deferred 分支将 T4/T6 标记为 `not_reached_at_rpc_return`，source 为 `ccbd_start_flow_provider_runtime_deferred_on_herdr`。
  - Verification: `python -m pytest -q "test/test_v2_ccbd_start_flow.py" -k "runtime_supervisor_start_defers_provider_runtime_for_herdr_namespace or runtime_supervisor_start_records_readiness_timeline" --basetemp "D:/tmp/pytest-ccb-herdr-review-start-2" -p no:cacheprovider` -> 1 passed。

- [x] OCR-002 `lib/ccbd/services/project_namespace_runtime/backend.py:867` `_mux_namespace_ref()` 曾忽略传入 `session_name`，跨 session helper 可能使用 cached namespace ref。
  - Source: ocr。
  - Evidence: OCR High；本地核验确认 helper path 会影响 V2 backend calls。
  - Closure: `_mux_namespace_ref()` 使用 `_mux_namespace_ref_if_present(backend, session_name=session_name)` 重建请求 session 的 ref；新增 `test_v2_mux_backend_helpers_rebuild_namespace_ref_for_requested_session`。
  - Verification: `python -m pytest -q "test/test_v2_project_namespace_backend.py" -k "rebuild_namespace_ref_for_requested_session or v2_mux_backend_helpers_use_namespace_refs_without_tmux_fallback" --basetemp "D:/tmp/pytest-ccb-herdr-review-backend-2" -p no:cacheprovider` -> 2 passed。

- [x] QA-001 `lib/ccbd/services/project_namespace_runtime/backend.py:858` qa-fix：严格 session 过滤破坏 Herdr authoritative server session name preservation。
  - Source: QA。
  - Evidence: CMD-004 首跑 `test_project_namespace_controller_preserves_herdr_server_session_name` failed；`ensure_window()` 在 `create_session()` 返回 actual server session name 后仍用 requested session lookup，找不到 cached ref。
  - Closure: `_remember_mux_namespace_ref()` 记录 requested session alias 与 actual session alias；`_mux_namespace_ref_if_present()` 先按 alias map 查找，再按 exact ref 过滤，避免其他 session 误用。
  - Verification: `python -m pytest -q "test/test_v2_project_namespace_state.py" "test/test_v2_project_namespace_backend.py" -k "namespace or mux or herdr or restore_token or redacted or presentation or capability" --basetemp "D:/tmp/pytest-ccb-herdr-qa-cmd004-rerun" -p no:cacheprovider` -> 60 passed；`python -m pytest -q "test/test_v2_project_namespace_backend.py" -k "namespace_state_fields_rejects_cached_namespace_ref_for_different_session or rebuild_namespace_ref_for_requested_session or v2_mux_backend_helpers_use_namespace_refs_without_tmux_fallback" --basetemp "D:/tmp/pytest-ccb-herdr-qa-backend-alias" -p no:cacheprovider` -> 3 passed。

- [x] REV-005 `lib/ccbd/services/project_namespace_runtime/backend.py:93` `remember_namespace_state_ref()` 从 durable state 恢复 namespace ref 时未记录 desired/legacy alias。
  - Source: independent-agent Round 3。
  - Impact: fresh backend 从 Herdr state 恢复后只知道 actual `namespace_session_name`，不知道 desired `tmux_session_name`；后续 helper 可能构造错误 `namespace_ref(desired, desired)`。
  - Closure: `remember_namespace_state_ref()` 把 `state.tmux_session_name` 作为 `requested_session_name` 传给 `_remember_mux_namespace_ref()`；新增 fresh backend second ensure 测试。
  - Verification: `python -m pytest -q "test/test_v2_project_namespace_state.py" -k "preserves_herdr_server_session_name or restores_herdr_state_alias_on_fresh_backend or default_backend_factory" --basetemp "D:/tmp/pytest-ccb-herdr-review-state-alias-fresh" -p no:cacheprovider` -> 7 passed；CMD-004 post fix -> 63 passed。

- [x] OCR-003 `lib/ccbd/services/project_namespace_runtime/additive_patch_agents.py:87` excluded moved agent membership 未字符串化。
  - Source: OCR Round 3。
  - Closure: 使用 `agent_name = str(appended.agent)` 统一 membership、order lookup 和 returned panes key。
  - Verification: additive patch focused -> 26 passed。

- [x] OCR-004 `lib/ccbd/services/project_namespace_runtime/backend.py:871` namespace ref alias map 累积 stale aliases。
  - Source: OCR Round 3。
  - Closure: 每次 `_remember_mux_namespace_ref()` 重建 alias map，仅保留当前 active namespace requested/actual aliases。
  - Verification: backend alias focused -> 4 passed。

- [x] OCR-005 `lib/ccbd/services/project_namespace_runtime/controller.py:74` Herdr runtime configured heuristic 对弱 env hints 过宽。
  - Source: OCR Round 3。
  - Closure: 仅 `CCB_HERDR_CAPABILITY_REPORT` / `CCB_HERDR_SOCKET_REF` 作为强 Herdr runtime signal；单独 `CCB_HERDR_SESSION` / `CCB_HERDR_EXE` 不强制 Herdr selection。
  - Verification: default backend focused -> 41 passed / 3 passed。

### nit

- [x] REV-003 `test/test_herdr_backend_client.py:1278` restore token fixture 使用单冒号，不符合 `session::workspace` contract。
  - Source: independent-agent。
  - Closure: fixture 改为 `restored-session::workspace-1`。
  - Verification: `python -m pytest -q "test/test_herdr_backend_client.py" -k "split_accepts_project_namespace_ref_without_known_namespace_cache" --basetemp "D:/tmp/pytest-ccb-herdr-review-client"` -> 1 passed。

### suggestion

- REV-004 `lib/ccbd/services/project_namespace_runtime/backend.py:100` `namespace_state_fields()` 在 mux backend cached ref 不匹配目标 `session_name` 时返回 legacy `tmux-family` 空字段。
  - Source: independent-agent Round 2。
  - Disposition: non-blocking suggestion。当前 ensure/reflow 相邻路径会先经 V2 helper 重建目标 session ref，新增测试覆盖“不把旧 ref 写入 state”；长期可考虑对 mux/Herdr ref 缺失 fail closed 或显式重建，避免未来新增调用点静默降级。

### learning

- reload/apply diagnostics 属于 public-ish surface；任何来自 backend exception 的 `evidence` 进入 result/payload/renderer 前必须按 key 语义脱敏。
- Round 2 确认脱敏 key matcher 已覆盖 snake_case、camelCase、hyphen 变体，并递归覆盖 Mapping/list/tuple。

### praise

- Round 2 独立 reviewer 确认 `NamespacePatchApplyResult.to_record()`、`namespace_patch_failed()` 与 CLI renderer 形成 API payload、stage diagnostics、CLI 输出的脱敏闭环。
- Round 2 独立 reviewer 确认 Herdr deferred 分支不启动 provider runtime，并把 T4/T6 标记为 `not_reached_at_rpc_return`；生产 start flow 已接收 namespace family/impl 参数。
- Round 4 独立 reviewer 确认 `test_blank_namespace_ref_clears_previous_aliases` 覆盖了空 alias 清理边界，避免旧 requested alias 残留。

### Round 4 Closure

- 独立 Task agent `019fc330-e839-7e31-9c5b-b67371b7e53d` returned passed；blocking/important/nit/suggestion 均为 none。
- 核验点：fresh backend durable Herdr state 会把 `state.tmux_session_name` 作为 requested alias 恢复；alias map 每次按当前 active namespace ref 重建，空 alias 会清理旧 `_ccb_project_namespace_ref_aliases`。
- 核验点：`additive_patch_agents.py` 对 appended agent 使用 `str()` 归一化后再做 membership、order lookup、result key 与 reflow 判断。
- 核验点：Herdr forced selection 的强 env signal 只认 `CCB_HERDR_CAPABILITY_REPORT` / `CCB_HERDR_SOCKET_REF`；显式 Herdr selection 失败仍 fail closed。
- OCR Round 4 只剩 `controller.py::_herdr_runtime_configured()` predicate medium；本地核验为噪声：controller 当前判定比 terminal runtime 更窄，不会重新引入弱 `CCB_HERDR_SESSION` / `CCB_HERDR_EXE` 强制 Herdr selection。

## 5. Test And QA Focus

- QA 必须重点复核：reload namespace patch failure 的 API payload、CLI 渲染、transcript 中都不出现 raw restore token。
- QA 必须重点复核：Herdr deferred provider runtime 的 startup report 不把 T4/T6 或 `timeline_complete` 误报成功。
- QA 必须重点复核：旧 cached namespace ref 不得污染新 session 的 V2 helper call 或 state fields。
- 建议新增或加强的测试：Round 2 reviewer 需要复看 `lib/ccbd/reload_sensitive_diagnostics.py` 的 key 匹配是否过宽/过窄，以及 `namespace_patch` nested diagnostics 是否仍可能通过其他 result model 泄露。
- 不能靠 review 完全确认的点：Native Windows CMD-013 transcript 仍需在 QA/acceptance 中复核真实 topology 与 public output。

## 6. Residual Risk

- OCR-001 `lib/ccbd/control_plane_transport/endpoint_store.py::unlink_token` 最后一次 `PermissionError` 被吞，可能留下 stale token。该文件属于前置 Windows transport dirty diff，不归因到本 feature review-fix；acceptance 前需要按前置 feature 归因或单独处理。
- 当前工作区 dirty diff 很大，scope guard 不能直接把全工作区当成本 feature 结论。Round 2 必须显式列出 review scope files 并过滤 `.codestable/`、后续 admission 产物和前置 dirty diff。
- `additive_patch_apply.py` 的 `error = str(exc)` 仍是字符串级原样输出；当前 Herdr `MuxCommandErrorV2.detail` 未拼 raw token，token 在 `evidence` 中按 key 脱敏，所以本轮可接受。QA 应继续防止后续 backend 把 restore token 拼进异常 detail/message 或放入非 token 命名 key。
- `lib/terminal_runtime/herdr_backend_runtime/cli.py` 的 create-session session scope comment 已核验为非 Round 4 alias closure 新问题：当前实现用 project namespace title 作为 session scope，测试 `test_herdr_cli_request_adapter_create_session_uses_project_namespace_title_as_session_scope` 覆盖。

## 7. Verdict

- Status: passed
- Next: 回到 `ccbd-herdr-namespace-lifecycle` QA 定稿。

## 8. Focused Closure

none；本轮 review-fix 修改了生产行为和 public diagnostics 语义，不满足 focused closure 条件。
