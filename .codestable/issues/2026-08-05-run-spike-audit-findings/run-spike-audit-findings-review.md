---
doc_type: issue-review
issue: 2026-08-05-run-spike-audit-findings
status: passed
reviewer: subagent
reviewed: 2026-08-05
round: 1
lane_a_state: completed
lane_a_ref: "019fd10d-a555-7602-bcc7-1e8c49e8149e"
lane_a_reason: ""
lane_b_state: skipped
lane_b_ref: ""
lane_b_reason: "当前工作区存在本轮范围外 dirty/untracked 文件，ocr review 不支持安全限定到本轮两个文件，按协议跳过裸 workspace 扫描。"
---

# run-spike-audit-findings 代码审查报告

## 1. Scope And Inputs

- Issue fix note: `.codestable/issues/2026-08-05-run-spike-audit-findings/run-spike-audit-findings-fix-note.md`
- Audit findings: `.codestable/audits/2026-08-05-herdr-ccb-recent-changes/finding-01.md`, `finding-06.md`, `finding-07.md`
- Implementation evidence: 本轮 `run_spike.ps1` diff、PowerShell self-test、AST parse、wrapper-only 成功/失败冒烟
- Diff basis: 当前工作区 unstaged diff
- Review mode: initial + focused closure
- Baseline dirty files: 工作区存在多个本轮范围外 dirty/untracked 文件；本报告只审 `run_spike.ps1` 和本 issue 目录。

### Independent Review

- Detection: 独立 Task agent 可用；OCR CLI 可用但 scope 歧义跳过。
- 环节 A 独立隔离 Task agent: independent-agent completed。
- 环节 B OCR CLI: skipped。
- Merge policy: 独立 reviewer findings 已本地核验，important 均已修复并复核 closure。
- Gate effect: `reviewer: subagent`，可放行。

## 2. Diff Summary

- 新增：`.codestable/issues/2026-08-05-run-spike-audit-findings/run-spike-audit-findings-fix-note.md`, `.codestable/issues/2026-08-05-run-spike-audit-findings/run-spike-audit-findings-review.md`
- 修改：`.codestable/roadmap/windows-native-herdr-ccb/drafts/herdr-ui-integration-spike/run_spike.ps1`
- 删除：none
- 风险热点：PowerShell 采集流程、证据分类、Herdr session 选择。

## 3. Adversarial Pass

- 假设的生产 bug：局部采集或 pane capture 失败但 summary 仍显示完成。
- 主动攻击过的反例：wrapper-only 成功、wrapper-only 失败、ping retry 中间失败、CCB namespace snapshot 失败 fallback、pane read 失败统计。
- 结果：独立 reviewer 提出的 important 已通过代码修正和局部验证关闭。

## 4. Findings

### blocking

none

### important

none

### nit

- [ ] REV-001 `run_spike.ps1:602` `Get-HerdrArgs` 当前未被调用，后续可清理。非本轮阻塞项。

### suggestion

- `-OnlyDimension pane-verification` 适合已有 CCB/Herdr 会话的局部重采集；后续可在 report 中补充 precondition 文案。

### learning

- 对 PowerShell 返回单个 `[ordered]` 对象的函数调用，调用侧需要 `@(...)` 固定数组语义，避免 `.Count` 退化为字典键数量。

### praise

- pane capture session 现在跟随 snapshot source，直接修复 finding 01 的证据错位根因。

## 5. Test And QA Focus

- QA 必须重点复核：真实 Herdr UI 环境默认全量运行，确认 `pane read` command JSON 中 `--session` 等于 snapshot source 对应 session。
- 建议新增或加强的测试：如后续保留该 PowerShell 脚本，可增加 Pester 覆盖 dimension selection、snapshot fallback、failed command summary。
- 不能靠 review 完全确认的点：真实 Herdr UI pane 内容采集需要现场环境。

## 6. Residual Risk

- 未执行真实 Herdr UI 全链路采集；acceptance 前仍需默认全量跑一次。
- finding 05 需要跨 `run_spike.ps1` 与 `ccb8.ps1` 抽共享模块，本轮按用户限定未处理。

## 7. Verdict

- Status: passed
- Next: 用户在 Herdr UI 环境中运行默认全量 spike 采集，确认真实 pane capture 证据。

## 8. Focused Closure

- Closed findings: reviewer important 1、reviewer important 2，以及 closure 中新增的 pane capture 失败统计和 ping retry 统计问题。
- Attributed delta: `run_spike.ps1` 中 `Read-HerdrSnapshotCandidate`、`Get-FailedCommandSummaries`、canonical `ccb8-ping-all`、pane capture `$commands += $captureResult`、partial classification fields。
- Targeted verification: `run_spike.ps1 -SelfTest` passed；PowerShell AST parse ok；wrapper-only 成功/失败冒烟分别得到 `partial-dimension-complete` 和 `partial-dimension-failed`。
- Classification: behavior fix，已由同一独立 reviewer focused closure 复核，无剩余 blocking/important。
