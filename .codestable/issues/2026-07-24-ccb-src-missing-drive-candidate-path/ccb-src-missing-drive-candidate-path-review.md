---
doc_type: issue-review
issue: 2026-07-24-ccb-src-missing-drive-candidate-path
status: passed
reviewer: subagent
reviewed: 2026-07-24
round: 1
lane_a_state: completed
lane_a_ref: "019f93af-81b5-77b2-a4be-bf13ae730c00"
lane_a_reason: ""
lane_b_state: unavailable
lane_b_ref: ""
lane_b_reason: "ocr llm test failed with 403 Forbidden"
---

# ccb-src 缺失盘符候选路径代码审查报告

## 1. Scope And Inputs

- Design: none
- Checklist: none
- Evidence pack: none
- Gate results: none
- DoD results: none
- Implementation evidence: `.codestable/issues/2026-07-24-ccb-src-missing-drive-candidate-path/ccb-src-missing-drive-candidate-path-fix-note.md`
- Diff basis: `git diff -- ccb-src.ps1 .codestable/issues/2026-07-24-ccb-src-missing-drive-candidate-path/`
- Review mode: initial
- Baseline dirty files: `lib/provider_backends/claude/launcher.py`, `lib/provider_backends/claude/launcher_runtime/service.py`

### Independent Review

- Detection: subagent 可用；OCR CLI 存在但 `ocr llm test` 返回 403 Forbidden。
- 环节 A 独立隔离 Task agent: independent-agent + completed
- 环节 B OCR CLI: unavailable
- OCR severity mapping: High -> blocking/important, Medium -> nit/suggestion, Low -> discarded
- Merge policy: subagent 结果已本地核验后合并；OCR 未启用原因已记录。
- Gate effect: subagent 已完成，允许定稿。

## 2. Diff Summary

- 新增：`.codestable/issues/2026-07-24-ccb-src-missing-drive-candidate-path/ccb-src-missing-drive-candidate-path-fix-note.md`
- 修改：`ccb-src.ps1`
- 删除：none
- 未跟踪 / staged：issue 目录新增文件未跟踪；无 staged diff
- 风险热点：Windows PowerShell 路径解析、调用方 cwd 恢复、退出码保持

## 3. Adversarial Pass

- 假设的生产 bug：缺失盘符仍可能在候选路径拼接或探测阶段抛错，阻断启动。
- 主动攻击过的反例：不存在的 `E:/.../ccb.py` 候选路径；从外部 cwd 调用 `--help` 后目录恢复；PowerShell AST 解析。
- 结果：未升级为 finding。

## 4. Findings

### blocking

none

### important

none

### nit

none

### suggestion

- `ccb-src.ps1` 当前 `git diff --check` 仅提示后续 Git 触碰时 LF 会替换为 CRLF。这不是本次功能问题，不建议混入当前修复；若项目需要行尾归一化，应单独处理。

### learning

- `ccb-src.ps1:31` 到 `ccb-src.ps1:45` 将固定候选根改为普通字符串，并用 `[System.IO.Path]::Combine(...)` 组合 `ccb.py`，避免 `Join-Path "E:/" ...` 在缺失盘符时提前抛错。
- `ccb-src.ps1:45` 使用 `Test-Path -ErrorAction SilentlyContinue`，缺失盘符探测结果为 `False`，不会中断候选扫描。

### praise

none

## 5. Test And QA Focus

- QA 必须重点复核：在可接受停止/重启 CCB 的窗口运行完整 `& "./ccb-src.ps1" kill -f; if ($LASTEXITCODE -eq 0) { & "./ccb-src.ps1" } else { exit $LASTEXITCODE }` 链路。
- Evidence pack residual risks / gate warnings：OCR 不可用已记录；完整 runtime 重启链路未在本轮执行。
- 建议新增或加强的测试：若后续为 Windows launcher 建测试，可覆盖缺失盘符候选路径和外部 cwd 调用。
- 不能靠 review 完全确认的点：真实 rmux 默认化、`.ccb` 状态改写、daemon 生命周期。

## 6. Residual Risk

- 未运行完整 kill/start 链路；该验证会停止并重启当前项目 CCB 运行时，留给用户可接受窗口执行。

## 7. Verdict

- Status: passed
- Next: issue 修复可进入收尾；完整 runtime 重启链路建议作为手工 QA 补跑。

## 8. Focused Closure

none
