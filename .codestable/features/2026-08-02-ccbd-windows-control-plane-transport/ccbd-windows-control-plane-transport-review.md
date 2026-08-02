---
doc_type: feature-review
feature: 2026-08-02-ccbd-windows-control-plane-transport
status: passed
reviewer: subagent
reviewed: 2026-08-02
round: 4
lane_a_state: completed
lane_a_ref: "019fc043-d458-7cc0-86bd-d3cfa486b6bd"
lane_a_reason: "第二轮完整复审通过；第四轮针对 DoD manual evidence 语义校验提出 important，已按 focused closure 关闭。"
lane_b_state: skipped
lane_b_ref: ""
lane_b_reason: "当前 workspace 含范围外 dirty 文件 笔记.md；不裸跑 workspace OCR，改为独立 Task agent + 本地行级 focused closure。"
---

# ccbd-windows-control-plane-transport 代码审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-08-02-ccbd-windows-control-plane-transport/ccbd-windows-control-plane-transport-design.md`
- Checklist: `.codestable/features/2026-08-02-ccbd-windows-control-plane-transport/ccbd-windows-control-plane-transport-checklist.yaml`
- Evidence pack: `.codestable/features/2026-08-02-ccbd-windows-control-plane-transport/ccbd-windows-control-plane-transport-evidence-pack.md`
- Gate results: `.codestable/features/2026-08-02-ccbd-windows-control-plane-transport/ccbd-windows-control-plane-transport-scope-gate-results.json`
- DoD results: `.codestable/features/2026-08-02-ccbd-windows-control-plane-transport/ccbd-windows-control-plane-transport-dod-results.json`
- Implementation evidence: transport diff、focused tests、DoD runner manual evidence gate、CMD-008 manifest。
- Diff basis: 当前 working tree 中本 feature 相关文件；范围外 `笔记.md` 未纳入 verdict。
- Review mode: full-rereview + focused-closure。
- Baseline dirty files: `笔记.md` 为范围外用户改动。

### Independent Review

- 环节 A 独立隔离 Task agent: completed，agent id `019fc043-d458-7cc0-86bd-d3cfa486b6bd`。
- 环节 B OCR CLI: skipped，原因见 frontmatter。
- Merge policy: 独立 reviewer findings 经本地事实核验后合并；第四轮 important 已用 focused closure 关闭。
- Gate effect: none；`reviewer: subagent` 放行 Goal lane QA。

## 2. Diff Summary

- 新增：`ccbd-windows-control-plane-transport-cmd008-evidence.json`、`test/test_codestable_dod_runner.py`。
- 修改：`lib/ccbd/control_plane_transport/*`、`lib/ccbd/socket_client_runtime/transport.py`、focused transport/bootstrap/client tests、DoD runner、checklist/evidence/review artifacts。
- 删除：none。
- 风险热点：Windows token ACL、handler 前认证、endpoint generation cleanup、manual evidence fail-closed。

## 3. Adversarial Pass

- 假设的生产 bug：Native Windows 仍绕回 AF_UNIX，或 bad token 进入 JSON-line handler。
- 主动攻击过的反例：无 endpoint client、bad token、owner mismatch ACL proof、generation path traversal、response frame trailing data、bootstrap probe failure、endpoint write/unlink 交错、manual transcript blocked 被误包装成 passed。
- 结果：transport blocking 均有 focused tests；manual evidence 现在要求 JSON manifest、feature/command/status/source_ref/scope/observations 语义匹配。

## 4. Findings

### blocking

none

### important

none

### nit

none

### suggestion

- [ ] REV-S1 `lib/ccbd/control_plane_transport/token_auth.py` Windows secure token create 仍通过 PowerShell command text 传递 token payload。
  - Evidence: 独立 reviewer 指出 token 不会先明文落盘，但同一用户可见的 PowerShell 子进程命令行可能短暂包含 token。
  - Impact: 不违反本 feature 的文件保护边界；属于后续 hardening。

### learning

- 手工 DoD 不能只验证 artifact 存在；必须有机器可读 manifest 绑定 feature、command 与关键语义。
- CMD-013 原始 transcript 的 namespace lifecycle 失败归属后续 `ccbd-herdr-namespace-lifecycle`，本 feature 只声明 control-plane blocker removed。

### praise

- transport seam 保持在 adapter 边界，未扩散到 RPC handler。
- focused tests 覆盖 Unix regression、Windows TCP/token、bootstrap auth path 和 DoD runner gate 语义。

## 5. Test And QA Focus

- QA 必须重点复核：Unix regression、Windows TCP endpoint publish、ACL 失败不 publish、bad token 不触发 handler、bootstrap self-ping 走 authenticated listener、shutdown 只清理当前 generation、CMD-008 manifest 不掩盖 downstream blocked。
- Gate warnings：CMD-006 是 Windows `fcntl` collection baseline，按 checklist `document-baseline` 处理。
- 不能靠 review 完全确认的点：Native Windows namespace create / foreground attach / reload apply 仍在后续 lifecycle feature 中 blocked。

## 6. Residual Risk

- CMD-006 Windows `fcntl` collection baseline 未由本 feature 修复。
- token payload 在 PowerShell 子进程命令行中短暂可见，建议后续改 stdin/ctypes DACL 创建。

## 7. Verdict

- Status: passed
- Next: Goal lane 进入 QA。

## 8. Focused Closure

- Closed findings: REV-3-001、REV-3-002、REV-4-001。
- Attributed delta: `.codestable/tools/codestable-dod-runner.py`、`test/test_codestable_dod_runner.py`、checklist CMD-008、`ccbd-windows-control-plane-transport-cmd008-evidence.json`。
- Targeted verification:
  - `python -m pytest -q test/test_codestable_dod_runner.py` -> 9 passed。
  - `python .codestable/tools/validate-yaml.py --file ...checklist.yaml --yaml-only` -> passed。
  - `python .codestable/tools/codestable-dod-runner.py ... --stage qa` -> passed，CMD-008 evidence includes `transport_blocker=resolved` and `downstream_namespace_lifecycle_status=blocked`。
  - `python -m compileall -q .codestable/tools/codestable-dod-runner.py test/test_codestable_dod_runner.py` -> passed。
  - `git diff --check` scoped to touched runner/feature files -> passed。
- Classification: gate/test/artifact closure only；未改变 production transport 行为、RPC schema、安全边界或 Herdr lifecycle。
