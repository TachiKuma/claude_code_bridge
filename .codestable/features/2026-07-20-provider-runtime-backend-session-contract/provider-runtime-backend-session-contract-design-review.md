---
doc_type: feature-design-review
feature: 2026-07-20-provider-runtime-backend-session-contract
status: passed
review_state: passed
review_reason: ""
reviewer_id: "019f7c1b-32f3-7450-baac-b18d2867ac5c"
reviewed: 2026-07-20
round: 2
---

# provider-runtime-backend-session-contract feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-20-provider-runtime-backend-session-contract/provider-runtime-backend-session-contract-design.md`
- Checklist: `.codestable/features/2026-07-20-provider-runtime-backend-session-contract/provider-runtime-backend-session-contract-checklist.yaml`
- Roadmap: `.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-roadmap.md` §4.7、`.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml`
- Related designs: `.codestable/features/2026-07-19-mux-backend-contract/mux-backend-contract-design.md`、`.codestable/features/2026-07-19-windows-namespace-ipc-schema/windows-namespace-ipc-schema-design.md`、`.codestable/features/2026-07-20-windows-job-object-runtime-evidence/windows-job-object-runtime-evidence-design.md`
- Code facts checked: `lib/cli/services/runtime_launch_runtime/session_files.py`、`lib/cli/services/runtime_launch.py`、`lib/provider_backends/codex/launcher.py`、`lib/provider_backends/native_cli_support/launcher.py`、`lib/provider_backends/pane_log_support/session.py`、`lib/provider_core/session_binding_evidence_runtime/fields.py`、`lib/ccbd/services/provider_runtime_facts.py`
- Provider env facts checked: `lib/provider_backends/codex/launcher_runtime/bridge.py`、`lib/provider_backends/codex/comm_runtime/session_runtime_runtime/loading.py`、`lib/provider_backends/codex/bridge_runtime/service.py`、`lib/provider_backends/gemini/comm_runtime/session_runtime.py`、`lib/provider_backends/opencode/runtime/session_runtime.py`

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: subagent `019f7c1b-32f3-7450-baac-b18d2867ac5c`
- Raw output: round 1 提出 2 个 blocking、2 个 important、1 个 nit；round 2 focused closure 判定全部 closed，remaining findings 为 none，verdict 为 `passed`。
- Merge policy: 主 agent 已按 reviewer findings 修订 provider-specific env 范围、protected-key canonical-wins merge、`ProviderRuntimeFacts` typed evidence 字段、allowlist guard 和 `tmux_session` 术语。
- Gate effect: independent review completed and merge verified；允许交回 `cs-epic` child design batch。

## 2. Design Summary

- Goal: 将 provider launch、session payload、runtime health、provider facts 和 provider env 迁移到 backend-neutral mux canonical 字段，同时保留旧 tmux alias。
- Key contracts: `provider_runtime/session_payload.py` 统一生成 `terminal="mux"`、`backend_family`、`backend_impl`、`pane_ref`、`namespace_ref`、`compat`；reader canonical-first、alias-fallback。
- Merge policy: shared canonical keys 永远 canonical wins；`provider_payload` 冲突写入 `payload_diagnostics.protected_key_conflicts`，不得覆盖 shared canonical。
- Provider env: `CCB_MUX_*` canonical-first；`CCB_TMUX_*`、`CODEX_TMUX_SESSION`、`GEMINI_TMUX_SESSION`、`OPENCODE_TMUX_SESSION`、`CODEX_TMUX_LOG` 仅 compatibility fallback。
- Facts contract: `ProviderRuntimeFacts` 扩展 `backend_family`、`backend_impl`、`pane_ref`、`namespace_ref`，旧 `terminal_backend`、`pane_id`、`tmux_socket_*` 保留为兼容投影。

## 3. Findings

### blocking

none

### important

none

### nit

none

### learning

- provider env 不能只覆盖 `CCB_TMUX_*`；当前 Codex/Gemini/OpenCode runtime loader 还有 provider-specific `*_TMUX_SESSION` 读取面。
- `tmux_session` 在当前 session payload 中是历史 pane alias，不应被实现者误当成 namespace 或 tmux session name。
- guard 必须区分合法 compatibility alias 与 canonical tmux 泄漏；裸 grep `tmux_session` / `tmux_socket` 会和兼容要求冲突。

## 4. User Review Focus

- 实现时优先守住 protected-key canonical-wins merge，避免 provider-specific payload 重新成为 backend authority。
- Provider-specific env loader 要用 `CCB_MUX_PANE_ID` canonical-first，再 fallback 到旧 `*_TMUX_SESSION`。
- `ProviderRuntimeFacts` 新字段应作为 typed evidence 落地，不能只塞 diagnostics 文本。
- CMD-007 应实现为 allowlist guard test，合法 alias 只允许出现在 session payload helper、reader fallback、tests fixture 和 adapter compatibility 边界。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Roadmap §4.7 alignment | pass | E/C | writer、reader、provider env、runtime facts、backend context 均有对应契约 | none |
| Provider env scope | pass | E | 设计和 checklist 已覆盖 Codex/Gemini/OpenCode provider-specific `*_TMUX_SESSION` 与 `CODEX_TMUX_LOG` | none |
| Merge policy atomicity | pass | C | S2 改为 protected-key canonical-wins，可独立验证 provider payload 冲突不能覆盖 canonical | none |
| ProviderRuntimeFacts field shape | pass | C | 已明确 `backend_family`、`backend_impl`、`pane_ref`、`namespace_ref` typed evidence | none |
| Guard accuracy | pass | C | CMD-007 改为 allowlist guard test，避免合法 compat alias 被误判 | none |
| Checklist YAML | pass | E | `validate-yaml.py --yaml-only` 通过 | none |
| Roadmap items YAML | pass | E | `validate-yaml.py` 通过 | none |

Summary: E=4, C=4, H=0, H-only core checks=none。

## 6. Residual Risk

- `mux-backend-contract` 与 `windows-namespace-ipc-schema` 仍是 design-review passed / in-progress 状态；本 feature 可完成 design gate，implementation 前仍需依赖项严格 done。
- Provider-specific launcher 数量多，后续实现必须以 CMD-007 allowlist guard 和 focused env loader tests 防漏。

## 7. Verdict

- Status: passed
- Next: 交回 `cs-epic` child design batch；本 feature design 保持 `draft`，等待所有子 feature design-review passed 后统一 owner 确认。

## 8. Focused Closure

- Closed findings: B1、B2、I1、I2、N1
- Attributed delta: `.codestable/features/2026-07-20-provider-runtime-backend-session-contract/provider-runtime-backend-session-contract-design.md`、`.codestable/features/2026-07-20-provider-runtime-backend-session-contract/provider-runtime-backend-session-contract-checklist.yaml`
- Verification: independent reviewer `019f7c1b-32f3-7450-baac-b18d2867ac5c` confirmed remaining findings none；YAML 校验通过；workflow-next 可恢复到当前 child 仅缺 design-review 的状态，写入本文件后应继续 batch。
- Classification: 本次 closure 只收紧设计契约、验证命令和兼容边界，不改变生产代码。
