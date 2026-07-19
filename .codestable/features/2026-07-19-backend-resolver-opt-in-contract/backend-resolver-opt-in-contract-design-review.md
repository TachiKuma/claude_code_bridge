---
doc_type: feature-design-review
feature: 2026-07-19-backend-resolver-opt-in-contract
status: passed
review_state: passed
review_reason: ""
reviewer_id: ""
reviewed: 2026-07-19
round: 2
---

# backend-resolver-opt-in-contract feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-19-backend-resolver-opt-in-contract/backend-resolver-opt-in-contract-design.md`
- Checklist: `.codestable/features/2026-07-19-backend-resolver-opt-in-contract/backend-resolver-opt-in-contract-checklist.yaml`
- Intent / brainstorm: none
- Roadmap: `.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-roadmap.md`、`.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml`
- Related docs: `.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-roadmap-review.md`、`.codestable/features/2026-07-19-rmux-route-approval/rmux-route-approval-design.md`、`.codestable/features/2026-07-19-rmux-route-approval/rmux-route-approval-design-review.md`
- Code facts checked: `lib/terminal_runtime/backend_selection.py`、`lib/terminal_runtime/api_selection.py`、`lib/terminal_runtime/api.py`、`lib/agents/config_loader_runtime/common.py`、`lib/agents/config_loader_runtime/parsing_runtime/validation.py`、`lib/agents/config_loader_runtime/parsing_runtime/workflow_v3.py`、`lib/agents/models_runtime/config_runtime/project.py`、`lib/cli/services/doctor.py`、`lib/cli/services/ping.py`、`lib/cli/services/start_foreground.py`

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: subagent `019f7aff-ed19-7190-a6e9-b15f923077e5`、subagent `019f7b08-6962-7ca1-9af0-1eb5a15819fc`
- Raw output: round 1 判定 2 blocking、1 important；主 agent 修订优先级、selection schema、startup/foreground diagnostics 后，round 2 复核无 blocking，剩 1 important 和 1 nit；主 agent通过 focused closure 收紧验证命令并修正文案。
- Merge policy: 主 agent 已逐条本地核验 reviewer findings，并将可证实问题修入 design/checklist。
- Gate effect: independent review completed and merge verified；focused closure 不改变核心契约，仅补验证命令和措辞。

## 2. Design Summary

- Goal: 定义 mux backend opt-in、selection result、fail-fast/fallback 和 diagnostics 契约。
- Key contracts: success `MuxBackendSelection` 与 roadmap §4.0 同构，包含 `backend_impl` 且 `effective_backend` 非空；failure 使用 typed diagnostics；优先级为 CLI > project > user > env > platform。
- Steps: 6 步，覆盖 config schema、resolver policy、route/capability reader、API/startup/foreground、diagnostics、regression matrix。
- Checks: 12 项，覆盖 tmux 默认、explicit rmux fail-fast、auto fallback、priority、schema、config fail-closed、diagnostics、旧 session 兼容和不越界。
- Baseline / validation: checklist YAML、items YAML、resolver unit tests、config/doctor/ping/start/foreground pytest selector。

## 3. Findings

### blocking

none

### important

none

### nit

none

### suggestion

none

### learning

- `CCB_MUX_BACKEND` 只能作为低优先级临时输入；若压过 project/user config，会违反 roadmap §4.0。
- selection failure 不应污染 success schema；下游需要稳定读取 `backend_impl` 和非空 `effective_backend`。
- foreground attach 是用户最先感知 backend 选择失败的路径，诊断验收不能只覆盖 doctor/ping。

### praise

- design 没有越界实现 `RmuxBackend`、provider session payload 或 ccbd control-plane transport。
- v2/v3 config validator 都被纳入验收，避免 `runtime.mux.backend` 只在单一路径可用。

## 4. User Review Focus

- 用户需要重点拍板：是否接受 `runtime.mux.backend` 作为持久配置字段，以及 env 低于 project/user config 的优先级。
- implement 需要重点遵守：explicit `rmux` fail-fast；`auto` fallback 必须带 reason；failure 不返回 nullable success object。
- code review / QA / acceptance 需要重点复核：startup/foreground attach、doctor/ping/diagnostic bundle 都能展示 selection diagnostics；旧 tmux socket/session 字段仍兼容。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | design §3.3 覆盖 AC-001 到 AC-008，并映射 S1 到 S6 | none |
| DoD Contract | pass | E | design §3.4 定义 config、resolver、fail-fast/fallback、tmux regression、diagnostics DoD | none |
| Steps and checks traceability | pass | E | checklist steps/checks 可追溯到 design §2.4、§3.1、§3.3、§3.4 | none |
| Roadmap contract compliance | pass | E/C | priority 和 `MuxBackendSelection` schema 已对齐 roadmap §4.0 | none |
| Module interface design | pass | E/C | resolver policy 与 backend factory/API facade 分离，failure diagnostics 独立于 success schema | none |
| Validation and artifacts | pass | E | CMD-003 覆盖 resolver，CMD-004 覆盖 config/doctor/ping/start/foreground | none |

Summary: E=6, C=2, H=0, H-only core checks=none。

## 6. Residual Risk

- route approval ref 尚未真实 approved；implementation 必须通过 injected reader 锁语义，不能直接读 drafts、运行 probe 或从 `probe_status=completed` 推断 approval。
- Rmux availability check 的实际实现留给后续 backend / packaging 路线；本 feature 只定义 selection policy 和诊断形状。

## 7. Verdict

- Status: passed
- Next: 交回 `cs-epic` child design batch；本 feature design 保持 `draft`，等待所有子 feature design-review passed 后统一 owner 确认。

## 8. Focused Closure

- Closed findings: FDR-001、FDR-002、FDR-003、FDR-004、FDR-005
- Attributed delta: `.codestable/features/2026-07-19-backend-resolver-opt-in-contract/backend-resolver-opt-in-contract-design.md` 与 `.codestable/features/2026-07-19-backend-resolver-opt-in-contract/backend-resolver-opt-in-contract-checklist.yaml`
- Verification: round 2 independent reviewer `019f7b08-6962-7ca1-9af0-1eb5a15819fc` 确认 round 1 blocking 均已实质关闭；后续 important 通过 CMD-004 selector 收紧关闭；checklist 与 roadmap items YAML 校验通过。
- Classification: 最后一轮 closure 只调整验证命令与文案，不改变行为、公开契约、架构边界、验收语义或范围；无需启动第三轮完整复审。
