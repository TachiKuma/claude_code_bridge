---
doc_type: issue-review
issue: 2026-07-24-source-ccb-startup-windows-tcp-auth
status: passed
reviewer: subagent
reviewed: 2026-07-24
round: 1
lane_a_state: completed
lane_a_ref: "019f91f0-3e18-71c3-8364-fe4960a496f7"
lane_a_reason: ""
lane_b_state: skipped
lane_b_ref: ""
lane_b_reason: "本次为后端 Python/测试改动，未涉及视觉 UI OCR 场景"
---

# source-ccb-startup-windows-tcp-auth 代码审查报告

## 1. Scope And Inputs

- Issue fix-note: `.codestable/issues/2026-07-24-source-ccb-startup-windows-tcp-auth/source-ccb-startup-windows-tcp-auth-fix-note.md`
- Implementation evidence: 真实复跑用户启动命令，`start_status: ok`，`ccbd_state=mounted`，无 `UnicodeDecodeError`
- Diff basis: 当前工作区中本 issue 可归因改动
- Review mode: initial
- Baseline dirty files: 工作区存在多处既有改动，本报告只审本 issue 文件

### Independent Review

- Detection: subagent 可用，OCR CLI 未用于本后端改动
- 环节 A 独立隔离 Task agent: independent-agent completed
- 环节 B OCR CLI: skipped
- OCR severity mapping: High->blocking/important, Medium->nit/suggestion, Low->discarded
- Merge policy: 子审查结果已本地核验后合并
- Gate effect: reviewer=subagent

## 2. Diff Summary

- 新增：`.codestable/issues/2026-07-24-source-ccb-startup-windows-tcp-auth/source-ccb-startup-windows-tcp-auth-fix-note.md`
- 修改：`lib/ccbd/control_plane_transport/windows_tcp.py`、`test/test_ccbd_windows_tcp_loopback_transport.py`、`lib/workspace/git_worktree.py`、`lib/workspace/materializer.py`、`test/test_v2_workspace_manager.py`
- 删除：none
- 未跟踪 / staged：`ccb-src.ps1` 等既有未跟踪文件不属于本 review 范围
- 风险热点：Windows TCP 启动时序、Git 中文路径解码

## 3. Adversarial Pass

- 假设的生产 bug：抢先合法连接完成认证但不发送请求时，worker 可能先阻塞在抢先连接上。
- 主动攻击过的反例：抢先合法连接、慢预认证连接、慢滴入认证、Git 中文路径输出、真实源码启动命令。
- 结果：自检连接按本地端口匹配后优先入队，相关测试和真实启动均通过。

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

- Windows 下捕获 Git 文本输出应显式指定 UTF-8，并用 `errors='replace'` 防止中文路径触发默认 GBK 解码异常。

### praise

none

## 5. Test And QA Focus

- QA 必须重点复核：在源码仓库根目录复跑 `& "./ccb-src.ps1" kill -f; if ($LASTEXITCODE -eq 0) { & "./ccb-src.ps1" } else { exit $LASTEXITCODE }`
- Evidence pack residual risks / gate warnings：none
- 建议新增或加强的测试：已新增抢先合法连接和 Git UTF-8 kwargs 回归测试
- 不能靠 review 完全确认的点：none

## 6. Residual Risk

- `.ccb/debug-subprocess-run.log` 是本次定位过程中产生的临时运行日志，未自动删除。

## 7. Verdict

- Status: passed
- Next: owner 验收后可进入收尾提交。

## 8. Focused Closure

none
