---
doc_type: feature-review
feature: 2026-07-31-herdr-user-surfaces-parity
status: passed
reviewer: subagent+ocr
reviewed: 2026-08-03
round: 6
lane_a_state: completed
lane_a_ref: "019fc5d7-3ae4-7881-8367-501600b3055e"
lane_a_reason: "round 6 independent reviewer: no blocking/important/nit/suggestion findings"
lane_b_state: completed
lane_b_ref: "ocr review round 6"
lane_b_reason: "OCR completed with one Medium Config UI reason precision nit/suggestion; no blocking"
---

# herdr-user-surfaces-parity 代码审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-31-herdr-user-surfaces-parity/herdr-user-surfaces-parity-design.md`
- Checklist: `.codestable/features/2026-07-31-herdr-user-surfaces-parity/herdr-user-surfaces-parity-checklist.yaml`
- Evidence pack: `.codestable/features/2026-07-31-herdr-user-surfaces-parity/evidence/cmd-008-native-windows-surface-transcript.md`
- Gate results: none
- DoD results: checklist CMD-001..CMD-008 与 implementation report 记录
- Implementation evidence: `.codestable/features/2026-07-31-herdr-user-surfaces-parity/herdr-user-surfaces-parity-implementation.md`
- Diff basis: 当前工作区 unstaged/untracked diff；无 staged diff
- Review mode: full-rereview
- Baseline dirty files: `笔记.md` 是本轮外既有 dirty baseline，不归入本 feature 结论；review 报告和 CMD-008 transcript 为本 feature 新产物。

### Independent Review

- Detection: Task agent 可用；OCR CLI 可用并已同步完成 round 6。
- 环节 A 独立隔离 Task agent: independent-agent + completed，ref `019fc5d7-3ae4-7881-8367-501600b3055e`。
- 环节 B OCR CLI: completed，ref `ocr review round 6`。
- OCR severity mapping: High -> blocking/important, Medium -> nit/suggestion, Low -> discarded。
- Merge policy: 已逐条核验独立 reviewer 与 OCR 输出；blocking/important 仅在有仓库事实支撑时合并。
- Gate effect: 环节 A 与环节 B 均完成；reviewer 字段为 `subagent+ocr`，可进入 Goal lane QA。

## 2. Diff Summary

- 新增：`.codestable/features/2026-07-31-herdr-user-surfaces-parity/evidence/cmd-008-native-windows-surface-transcript.md`、本 review 报告。
- 修改：feature checklist/design/implementation、roadmap goal-state、`lib/ccbd/handlers/ping_runtime/payloads.py`、`lib/ccbd/herdr_surface_projection.py`、`lib/cli/services/config_ui.py`、doctor/diagnostics runtime 文件、`lib/mobile_gateway/service.py`、`lib/mobile_gateway/terminal.py`、Windows path/storage helpers 与相关 tests。
- 删除：none
- 未跟踪 / staged：CMD-008 transcript 与本 review 报告未跟踪；staged none。
- 风险热点：public payload redaction、Mobile terminal backend-neutral target、Config UI supported hard gate、diagnostics bundle archive/staging、Windows path rendering、doctor temporary path classification、production Herdr adapter 缺失时的 fail-closed 行为。

## 3. Adversarial Pass

- 假设的生产 bug：Herdr surface 在某条用户可见路径仍被当作 tmux target，或 partial projection 被错误当成 supported。
- 主动攻击过的反例：Mobile history/message/websocket 的 blocked 与 supported path、pane evidence mismatch、默认 production factory 缺真实 Herdr adapter、Config UI pass gate、diagnostics archive escape、CRLF no-op save、provider capability lazy probing、Windows external drive archive path。
- 结果：round 1-5 暴露的问题均已修复并复审关闭；round 6 未发现 blocking/important。Config UI blocked reason 的文案精度保留为非阻塞建议。

## 4. Findings

### blocking

- none

已关闭历史：

- REV-R1 diagnostics archive escape、Config UI CRLF no-op save、provider capabilities eager probing、shared hard gate 过宽：已修复并由后续复审关闭。
- REV-R2 support tier gate 未要求 beta/source、non-agent target 覆盖不足：已修复并由后续复审关闭。
- REV-R3 agent attach blocked path、diagnostics missing-before-guard、capabilities/catch issues：已修复并由后续复审关闭。
- REV-R4 HTTP/WS `terminal_blocked` serialization 与 Herdr pane binding：已修复并由后续复审关闭。
- REV-R5 default production wiring 仍落 tmux：已修复并由 round 6 独立 reviewer 关闭。

### important

- none

### nit

- [ ] REV-006 `lib/cli/services/config_ui.py:289` Config UI blocked reason 对 hard gate 失败只输出 `capability_status=...`，当 capability 已是 `supported` 但 support tier/source/beta gaps/blocking gaps/degraded action 不满足 gate 时，文案不够精确。
  - Source: ocr round 6 Medium，经本地核验为可诊断性建议。
  - Disposition: 非阻塞；当前 payload 同时包含完整 `herdr_surface_projection`，下游可据此判断真实失败字段。为避免非阻塞文案触发新的生产 diff，本轮不再修改。

### suggestion

- none

### learning

- Herdr public surface gate 必须集中在 shared projection helper；让各 surface 自己判断 supportability 容易出现 partial/supported 漂移。
- Windows public payload 路径形状需要明确 POSIX 化边界，否则测试会在 Linux/Windows 间产生非功能性漂移。

### praise

- Mobile blocked path 与 supported target path 均有 HTTP POST、websocket、history/message 覆盖，能证明 Herdr 不再被强制映射到 tmux socket/session/%pane。
- Diagnostics staging 先做 archive escape guard，再处理 missing/error，错误优先级更安全。

## 5. Test And QA Focus

- QA 必须重点复核 AC-002..AC-012：ProjectView/ping/doctor/mounted/diagnostics projection 一致性，foreground supported/blocked，Mobile supported/blocked，Config UI pass/blocked gate，tmux/rmux regression，scope/redaction guard，Native Windows transcript。
- Fresh verification 已记录：
  - CMD-004：`130 passed, 29 deselected`
  - CMD-005：`106 passed, 1 skipped, 74 deselected`
  - CMD-006：`231 passed`
  - py_compile touched files：passed
  - checklist/items YAML validation：passed
  - `git diff --check`：passed，只有既有 LF->CRLF warning
  - CMD-007 scope/redaction guard：passed
- Evidence pack residual risks / gate warnings：CMD-008 transcript 是 harness + true-host upstream evidence 的组合；QA/acceptance 需要确认它足以覆盖 Native Windows surface parity，不把本 feature升级成最终 support tier claim。
- 建议新增或加强的测试：none blocking；Config UI reason 精度可在后续诊断 polish 中补。
- 不能靠 review 完全确认的点：真实 Herdr adapter 在 production 环境可用性仍属于后续 validation/supportability feature；本 feature 只证明 surface projection 与 blocked/pass gate。

## 6. Residual Risk

- `笔记.md` 是无关 dirty baseline，后续 QA/acceptance/提交归因时必须继续排除。
- 本 review 报告与 CMD-008 transcript 仍是未跟踪 feature artifact，acceptance 前需要纳入本 feature 交付物。
- Config UI blocked reason 仍可更精确，但不影响 hard gate 语义；完整 projection 已暴露失败字段。
- Native Windows transcript 复用了同 roadmap true-host Herdr namespace lifecycle evidence，并用本 feature harness 覆盖 surface pass/blocked；acceptance 仍需核对 transcript 与 AC-012 的映射。

## 7. Verdict

- Status: passed
- Next: 进入 `cs-feat` Goal lane QA 阶段，生成 `.codestable/features/2026-07-31-herdr-user-surfaces-parity/herdr-user-surfaces-parity-qa.md`；QA passed 后再进入 acceptance。

## 8. Focused Closure

- none；本轮为 round 6 完整复审。
