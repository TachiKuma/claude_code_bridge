---
doc_type: issue-review
issue: 2026-08-04-herdr-ui-integration-ccbd-bootstrap
status: passed
reviewer: subagent+ocr
reviewed: 2026-08-04
round: 2
lane_a_state: completed
lane_a_ref: ""
lane_a_reason: ""
lane_b_state: completed
lane_b_ref: ""
lane_b_reason: ""
---

# Herdr UI integration ccbd bootstrap 代码审查报告

## 1. Scope And Inputs

- Report: `.codestable/issues/2026-08-04-herdr-ui-integration-ccbd-bootstrap/herdr-ui-integration-ccbd-bootstrap-report.md`
- Analysis: `.codestable/issues/2026-08-04-herdr-ui-integration-ccbd-bootstrap/herdr-ui-integration-ccbd-bootstrap-analysis.md`
- Fix note: `.codestable/issues/2026-08-04-herdr-ui-integration-ccbd-bootstrap/herdr-ui-integration-ccbd-bootstrap-fix-note.md`
- Implementation evidence: 当前工作区 diff 与验证命令输出
- Diff basis: `git diff` / `git status --short`
- Review mode: focused-closure
- Baseline dirty files: `.codestable/brainstorms/windows-native-herdr-ccb/brainstorm.md`、`笔记.md`（与本次修复无关，未纳入结论）

### Independent Review

- Detection: 独立 Task agent 可用，OCR CLI 可用
- 环节 A 独立隔离 Task agent: independent-agent / completed
- 环节 B OCR CLI: completed
- OCR severity mapping: High→blocking/important, Medium→nit/suggestion, Low→discarded
- Merge policy: 已逐条本地核验并合并
- Gate effect: none

## 2. Diff Summary

- 修改：`lib/storage/json_store.py`
- 修改：`lib/terminal_runtime/herdr_backend_runtime/cli.py`
- 修改：`test/test_json_store.py`
- 修改：`test/test_herdr_backend_client.py`
- 修改：`.codestable/roadmap/windows-native-herdr-ccb/drafts/herdr-ui-integration-spike/run_spike.ps1`
- 修改：`.codestable/roadmap/windows-native-herdr-ccb/drafts/herdr-ui-integration-spike/README.md`
- 修改：`.codestable/roadmap/windows-native-herdr-ccb/follow-ups/herdr-ui-integration-spike.md`
- 修改：`.codestable/issues/2026-08-04-herdr-ui-integration-ccbd-bootstrap/herdr-ui-integration-ccbd-bootstrap-analysis.md`
- 修改：`.codestable/issues/2026-08-04-herdr-ui-integration-ccbd-bootstrap/herdr-ui-integration-ccbd-bootstrap-fix-note.md`
- 风险热点：共享存储异常语义、Herdr CLI 兼容层、UI spike 判定逻辑

## 3. Adversarial Pass

- 假设的生产 bug：Herdr list 命令失败被误当成成功，或 spike 把未完成的 provider/runtime 误判为通过
- 主动攻击过的反例：非 JSON 输出、真实命令失败、`ping all` 未成功、坏 JSON 文件、短暂半写入
- 结果：已关闭为修复项；未留下 blocking

## 4. Findings

### blocking

none

### important

none

### nit

none

### suggestion

none

### learning

- Herdr 0.7.5 的 `workspace list` / `pane list` 不支持 `--json`，机器可读状态应走 `api snapshot`。

### praise

- `run_spike.ps1` 继续保留了可读的命令引用和进度条，不影响证据追踪。

## 5. Test And QA Focus

- QA 必须重点复核：在真实 Herdr UI pane 内重跑 `run_spike.ps1`，确认 `ccb8-start-project.stderr.txt` 不再出现 `unknown option: --json`
- 建议新增或加强的测试：已补 `HerdrCliRequestAdapter` 的 snapshot fallback 与命令失败不回退测试
- 不能靠 review 完全确认的点：真实 Herdr UI 下的窗口 materialize 是否仍受环境态影响

## 6. Residual Risk

- 当前仍依赖一次真实 Herdr UI 复验来最终闭环；本轮只完成了代码级修复与回归测试

## 7. Verdict

- Status: passed
- Next: 按 issue 收尾

## 8. Focused Closure（无则写 none）

- Closed findings: REV-001, REV-002, REV-003
- Attributed delta:
  - `lib/terminal_runtime/herdr_backend_runtime/cli.py:762-768`、`:856-866`
  - `lib/storage/json_store.py:12-20`、`:60-84`
  - `.codestable/roadmap/windows-native-herdr-ccb/drafts/herdr-ui-integration-spike/run_spike.ps1:577-624`
- Targeted verification:
  - `python -m pytest test/test_herdr_backend_client.py test/test_json_store.py -q` -> `170 passed`
  - `python -m pytest test/test_ccbd_bootstrap_probe.py test/test_ccbd_windows_tcp_loopback_transport.py -q` -> `26 passed, 1 skipped`
  - `powershell -NoProfile -ExecutionPolicy Bypass -File ".codestable/roadmap/windows-native-herdr-ccb/drafts/herdr-ui-integration-spike/run_spike.ps1" -SelfTest` -> `passed`
  - `ocr review --audience agent --exclude ".codestable/**,笔记.md" ...` -> `0 finding(s)`
- Classification: test/docs/type/metadata/fallback-only changes；未改变公开协议、安全边界、并发或架构
