---
doc_type: feature-acceptance
feature: 2026-08-02-ccbd-windows-control-plane-transport
status: passed
audit_state: completed
audit_reason: ""
auditor_id: ""
acceptance_authorization_ref: "approval-report.md#goal-acceptance"
accepted: 2026-08-02
round: 1
---

# ccbd-windows-control-plane-transport 验收报告

> 阶段：Goal feature acceptance
> 验收日期：2026-08-02
> 关联方案 doc：`.codestable/features/2026-08-02-ccbd-windows-control-plane-transport/ccbd-windows-control-plane-transport-design.md`

## 1. 接口契约核对

- [x] `ccbd.control_plane_transport` seam 存在，Unix/TCP/fake adapter、endpoint store、token auth 均落在设计挂载点。
- [x] Windows endpoint canonical authority 为 `tcp_loopback` + host/port/token_ref/generation；legacy `socket_path` 只作兼容投影。
- [x] JSON-line RPC handler 未作为本 feature 改动目标；auth 在 handler 前完成。
- [x] DoD manual evidence 使用 JSON manifest，不再把自由 Markdown transcript 文件存在等同 pass。

## 2. 行为与决策核对

- [x] Unix 仍走 AF_UNIX adapter，stale cleanup/bootstrap/client 行为由 regression 覆盖。
- [x] Windows 默认走 TCP loopback + same-user token。
- [x] ACL 无法证明、bad/missing/unreadable token 不 publish 或不进入 handler。
- [x] bootstrap self-ping 走同一 transport connect + token handshake。
- [x] 明确不做已核对：未实现 named pipe production adapter，未改 RPC schema/handler，未改 Herdr namespace/provider/recovery/user-surface/release。

## 3. 验收场景核对

- [x] AC-001 Unix regression：CMD-003 14 passed。
- [x] AC-002 Windows endpoint publish：CMD-004 19 passed。
- [x] AC-003 ACL fail-fast：CMD-004 覆盖。
- [x] AC-004 valid token handshake：CMD-004 覆盖。
- [x] AC-005 invalid token no handler：CMD-004 覆盖。
- [x] AC-006 bootstrap auth path：CMD-005 53 passed, 1 skipped。
- [x] AC-007 diagnostics redaction / legacy projection：CMD-007 2 passed。
- [x] AC-008 scope boundary：review + scope gate passed。
- [x] AC-009 CMD-013 retry：`ccbd-windows-control-plane-transport-cmd008-evidence.json` 证明 `transport_blocker=resolved`、`forbidden_error_observed=false`；source transcript 的 downstream namespace lifecycle 仍 blocked，已留给后续 feature。

QA 报告：`.codestable/features/2026-08-02-ccbd-windows-control-plane-transport/ccbd-windows-control-plane-transport-qa.md` status passed。

## 4. 术语一致性

- control-plane transport、Windows TCP loopback adapter、same-user token、endpoint descriptor 均与 design 术语一致。
- 防冲突结论保持：该 transport 不是 Herdr mux transport，不是 provider runtime transport。

## 5. 领域影响盘点

- 新增长期结构：`ccbd.control_plane_transport` seam。当前 roadmap/design 已承载该结构；暂不在 acceptance 内代写 ADR。
- 后续建议：若 transport seam 后续被更多 roadmap 复用，可用 `cs-domain` 补 ADR 或 CONTEXT 术语。

## 6. requirement delta / clarification 回写

- Requirement: `native-windows-ccb-via-herdr`。
- 本 feature 是 roadmap 内部前置能力补齐，不改变用户侧 supported 承诺边界；无需 requirement delta。

## 7. roadmap 回写

- `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml`：`ccbd-windows-control-plane-transport` 已更新为 `status: done`。
- `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-roadmap.md`：第 5 个子 feature 状态已同步为 accepted。
- `goal-state.yaml`：当前 feature status 已更新为 accepted，`current_feature_index` 推进到 5。

## 8. attention.md 候选盘点

- 候选：CodeStable DoD runner 的 manual command 不能只看 transcript 文件存在，必须绑定 JSON manifest 和关键语义字段。
- 不直接写 attention.md；如后续多次出现，建议走 `cs-note`。

## 9. 遗留

- CMD-006 Windows `fcntl` collection baseline：后续独立处理。
- token payload 通过 PowerShell child command text 短暂可见：后续 hardening。
- Herdr namespace create / foreground attach / reload apply 仍 blocked：后续 `ccbd-herdr-namespace-lifecycle`。

## 10. 最终审计

- 验证证据来源：`ccbd-windows-control-plane-transport-qa.md`。
- Evidence sources：`ccbd-windows-control-plane-transport-evidence-pack.md`、`ccbd-windows-control-plane-transport-dod-results.json`、`ccbd-windows-control-plane-transport-scope-gate-results.json`。
- 聚合命令：
  - `python -m pytest -q test/test_codestable_dod_runner.py` -> 9 passed。
  - `python .codestable/tools/codestable-dod-runner.py --checklist ... --stage qa` -> passed。
  - `python .codestable/tools/validate-yaml.py --file ...checklist.yaml --yaml-only` -> passed。
  - `git diff --check` -> passed with line-ending warning only.
- 场景复核：re-verified 9 / trust-prior-verify 0。
- 交付物复核：code、tests、review、QA、DoD JSON、manual manifest、roadmap items/main doc、goal-state 均已落盘。
- 完整工作区复核：`笔记.md` 为范围外 dirty 文件，未纳入本 feature。
- diff 清洁度：通过；scope-gate TODO/FIXME/XXX warnings 为规则文本/design marker，不是新增生产临时代码。
- 知识沉淀出口：manual evidence manifest 规则为 attention 候选；不在 acceptance 内直接写入。
- 结论：通过。该 feature 只解除 control-plane transport blocker，不声明 Herdr namespace lifecycle 通过。
