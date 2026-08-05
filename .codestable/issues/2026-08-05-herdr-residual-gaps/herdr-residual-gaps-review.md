---
doc_type: issue-review
issue: herdr-residual-gaps
status: passed
reviewer: self
reviewed: 2026-08-05
round: 1
lane_a_state: not-started
lane_a_ref: ""
lane_a_reason: ""
lane_b_state: not-started
lane_b_ref: ""
lane_b_reason: ""
---

# Herdr residual gaps 代码审查报告

## 1. Scope And Inputs

- Report: `.codestable/issues/2026-08-05-herdr-residual-gaps/herdr-residual-gaps-report.md`
- Analysis: `.codestable/issues/2026-08-05-herdr-residual-gaps/herdr-residual-gaps-analysis.md`
- Fix note: `.codestable/issues/2026-08-05-herdr-residual-gaps/herdr-residual-gaps-fix-note.md`
- Implementation evidence: `lib/terminal_runtime/herdr_backend_runtime/cli.py`、`test/test_herdr_backend_client.py`、现场 `C:\ccb8v` 启动验证
- Diff basis: 当前工作区未提交 diff；仅审本次可归因改动
- Review mode: focused-closure
- Baseline dirty files: `ccb8.cmd`、`lib/ccbd/services/project_namespace_state_runtime/stores.py`、`lib/storage/atomic.py`、`lib/storage/jsonl_store.py`、`test/test_storage_atomic.py`、`test/test_v2_cli_router.py`、`test/test_v2_project_namespace_state.py`、`笔记.md` 等，均不在本次修复范围

### Independent Review

- Detection: 独立 Task agent / OCR CLI 本轮未启用，采用本地只读审查
- 环节 A 独立隔离 Task agent: local-only + not-started
- 环节 B OCR CLI: not-started
- OCR severity mapping: 未启用
- Merge policy: 本地核验后合并
- Gate effect: none

## 2. Diff Summary

- 修改：`lib/terminal_runtime/herdr_backend_runtime/cli.py`、`test/test_herdr_backend_client.py`、`.codestable/issues/2026-08-05-herdr-residual-gaps/herdr-residual-gaps-fix-note.md`
- 风险热点：none

## 3. Adversarial Pass

- 假设的生产 bug：前台 attach 仍然走错 Herdr 子命令，导致 `ccb8` 启动后直接报错退出
- 主动攻击过的反例：attach 命令字符串、workspace focus 顺序、`restore_token` 泄露、启动后是否仍快速失败
- 结果：未发现 blocking / important

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

- Herdr 前台附着必须用显式 `session attach`，裸 `--session` 不应再作为 attach 路径

### praise

- `attach_namespace` 的测试同时覆盖了 workspace focus 顺序和敏感 token 不泄露，回归面够窄

## 5. Test And QA Focus

- QA 必须重点复核：`C:\ccb8v> .\ccb8 kill -f; .\ccb8`，确认不再出现 `foreground attach failed`
- Evidence pack residual risks / gate warnings：工具环境无法直接渲染 Herdr 交互 UI，只能依赖进程状态和错误日志验证
- 建议新增或加强的测试：none
- 不能靠 review 完全确认的点：交互 UI 是否在宿主终端中正常可见

## 6. Residual Risk

- 交互 UI 在不同终端宿主中的可见性仍需人工复核；当前验证已覆盖命令路径和启动结果

## 7. Verdict

- Status: passed
- Next: 按 issue 收尾

## 8. Focused Closure

- Closed findings: none
- Attributed delta: `lib/terminal_runtime/herdr_backend_runtime/cli.py`，`test/test_herdr_backend_client.py`
- Targeted verification: `pytest -q test/test_herdr_backend_client.py` -> `172 passed`; `pytest -q test/test_v2_start_foreground.py` -> `17 passed`; `C:\ccb8v` 实机启动不再快速报前台附着失败
- Classification: test/docs/metadata-only，未改变公开契约、安全、数据、并发或架构
