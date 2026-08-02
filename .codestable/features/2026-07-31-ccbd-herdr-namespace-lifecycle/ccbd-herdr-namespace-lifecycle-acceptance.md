---
doc_type: feature-acceptance
feature: 2026-07-31-ccbd-herdr-namespace-lifecycle
status: passed
audit_state: completed
audit_reason: ""
auditor_id: "019fc339-f668-7073-89e2-e32f9a41197b"
acceptance_authorization_ref: "approval-report.md#goal-acceptance"
accepted: 2026-08-02
round: 1
---

# ccbd-herdr-namespace-lifecycle 验收报告

> 阶段：Goal feature acceptance
> 验收日期：2026-08-02
> 关联方案 doc：`.codestable/features/2026-07-31-ccbd-herdr-namespace-lifecycle/ccbd-herdr-namespace-lifecycle-design.md`

## 1. 接口契约核对

- [x] `ProjectNamespaceState` / event / ping / foreground summary 能表达 `herdr-native`、`herdr`、`herdr_socket`、namespace id/session/ipc 和 restore token presence。
- [x] raw `namespace_restore_token` 只保留在 private durable state / internal backend ref；public payload 只输出 `namespace_restore_token_present`。
- [x] project namespace helper 通过 MuxBackend V2 refs/capabilities 调用 Herdr；不把 Herdr 伪装成 tmux-family，也不走 tmux `_tmux_run` fallback。
- [x] foreground attach 对 Herdr 走 attach backend seam，不要求 tmux binary，不输出 raw token。
- [x] kill/reload/restart 边界保持 ccbd authority；restart provider pane 在本 feature 下明确 deferred，不伪造 provider runtime 成功。

## 2. 行为与决策核对

- [x] 需求摘要已落地：Herdr backend 可创建 project namespace、materialize topology、foreground attach、reload、kill，并给出 restart deferred evidence。
- [x] 明确不做已核对：未修改 provider runtime、recovery owner、Mobile/Config UI、doctor/support、package/release/update/installer/public validation matrix。
- [x] Herdr actual session name 与 requested project namespace alias 的差异已由 namespace ref alias map 处理；fresh durable restore 与 stale alias 清理均有 review/QA 证据。
- [x] Herdr runtime forced selection 只接受强 env signal：`CCB_HERDR_CAPABILITY_REPORT` / `CCB_HERDR_SOCKET_REF`。
- [x] reload failure diagnostics 通过 `ccbd.reload_sensitive_diagnostics` 在 API/stage/CLI public-ish surface 前脱敏。

## 3. 验收场景核对

- [x] AC-001 前置 V2/HerdrBackend admission：QA CMD-003 `174 passed, 12 deselected`。
- [x] AC-002/AC-003 state compatibility 与 Herdr state round-trip：QA CMD-004 latest pass，后续聚合复核 64 passed。
- [x] AC-004 public redaction：QA CMD-009、CMD-010、CMD-012、CMD-013 scan 均 pass。
- [x] AC-005..AC-007 V2 helper / ensure / layout / reflow：QA CMD-004 与 backend alias focused tests pass。
- [x] AC-008/AC-009 foreground attach ready/blocked：QA CMD-005 16 passed。
- [x] AC-010 kill/restart/reload：QA CMD-006 6 passed，CMD-011 26 passed，CMD-013 restart deferred/kill evidence present。
- [x] AC-011 Native Windows transcript：`evidence/cmd-013-native-windows-herdr-transcript.md` verdict passed，覆盖 create、foreground attach、reload dry/apply、restart deferred、kill/post-kill。
- [x] AC-012 tmux/rmux regression：foreground/project view/reload focused regression pass。
- [x] AC-013 scope boundary：CMD-007/CMD-008 scope/content guard pass。
- [x] Review QA focus 已覆盖：reload diagnostics redaction、Herdr deferred readiness、cached namespace ref isolation 均有 fresh evidence。
- [x] QA 报告：`.codestable/features/2026-07-31-ccbd-herdr-namespace-lifecycle/ccbd-herdr-namespace-lifecycle-qa.md` status passed。
- [x] 独立 acceptance auditor：Feynman `019fc339-f668-7073-89e2-e32f9a41197b` returned passed，无 blocking。

## 4. 术语一致性

- Herdr project namespace、ccbd project authority、Herdr namespace durable state、internal namespace ref、public namespace payload、MuxBackend V2 runtime path、foreground attach 均与 design 第 0 节术语一致。
- 防冲突结论保持：本 feature 不把 Herdr session 当 provider runtime session，不把 Herdr agent state 当 CCB completion authority。

## 5. 领域影响盘点

- 长期结构候选：Herdr namespace durable state 和 namespace ref alias map 是 project namespace runtime 的稳定契约。当前 roadmap/design/acceptance 已承载；不在 acceptance 内代写 ADR。
- 后续建议：若 alias map 或 restore token redaction 规则被后续 provider/recovery feature 复用，可走 `cs-domain` 或 `cs-keep` 沉淀。

## 6. requirement delta / clarification 回写

- Requirement: `native-windows-ccb-via-herdr`。
- 本 feature 是 roadmap 内部 capability step，未改变用户侧 Windows supported 承诺；provider runtime、Mobile/Config UI、release/support 仍由后续 child 承接。无需 requirement delta。

## 7. roadmap 回写

- `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml`：`ccbd-herdr-namespace-lifecycle` 保持 `status: done`，notes 更新为 accepted 语义。
- `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-roadmap.md`：第 6 个子 feature 状态同步为 accepted。
- `.codestable/roadmap/windows-native-herdr-ccb/goal-state.yaml`：当前 feature status 更新为 accepted；`provider-runtime-on-herdr` 的缺前置 acceptance blocker 可解除并进入 admission 复跑。
- Goal acceptance authorization：`.codestable/roadmap/windows-native-herdr-ccb/approval-report.md#goal-acceptance` 已 approved；`goal-state.yaml` 的 `acceptance_authorization_ref` 与本报告 frontmatter 匹配。

## 8. attention.md 候选盘点

- 候选：pytest 在本机应使用 `--basetemp "D:/tmp/..." -p no:cacheprovider`，避免默认 Temp / `.pytest_cache` 权限 warning 干扰。
- 不直接写 attention.md；如后续多次出现，建议走 `cs-note`。

## 9. 遗留

- `provider-runtime-on-herdr` 仍未实现；本 feature 只提供 Herdr namespace/pane evidence，不证明 ask/pend/completion/cancel。
- `endpoint_store.py::unlink_token` stale token 风险属于前置 Windows transport dirty diff，不归因本 feature。
- CMD-013 本轮 acceptance 未 live 重跑；QA 已扫描同日 Native Windows x64 transcript，作为 trust-prior manual evidence。

## 10. 最终审计

- 验证证据来源：`ccbd-herdr-namespace-lifecycle-qa.md`。
- Evidence sources：`ccbd-herdr-namespace-lifecycle-review.md`、`ccbd-herdr-namespace-lifecycle-implementation.md`、`evidence/cmd-013-native-windows-herdr-transcript.md`。
- 聚合命令：QA 记录 CMD-001..CMD-013 均 pass 或已有同日 manual evidence；`git diff --check` exit 0，仅 line-ending warning。
- 场景复核：re-verified 12 / trust-prior-verify 1。
- 交付物复核：code、tests、review、QA、CMD-013 transcript、checklist、roadmap items/main doc、goal-state 均已落盘。
- 完整工作区复核：工作区 dirty 很大，验收范围只覆盖本 feature 可归因文件和证据；不声明全工作区 clean。
- diff 清洁度：本 feature debug output、临时 TODO、注释掉代码、dead import、scope 越界均 pass。
- 知识沉淀出口：pytest basetemp/cacheprovider 规则为 attention 候选；不在 acceptance 内直接写入。
- 结论：通过。该 feature 解除 `provider-runtime-on-herdr` 的前置 acceptance blocker，但不声明 provider runtime 行为已通过。
