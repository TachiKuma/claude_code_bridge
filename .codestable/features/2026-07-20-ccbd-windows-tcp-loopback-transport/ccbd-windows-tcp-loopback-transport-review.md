---
doc_type: feature-review
feature: 2026-07-20-ccbd-windows-tcp-loopback-transport
status: passed
reviewer: subagent
reviewed: 2026-07-22
round: 5
lane_a_state: completed
lane_a_ref: "019f8758-4201-7ff2-bbcf-96f7919c6bb1"
lane_a_reason: "independent Task agent reviewer completed full rereview after REV-009/REV-010 and follow-up review-fix; no blocking or important findings"
lane_b_state: skipped
lane_b_ref: ""
lane_b_reason: "OCR CLI available, but workspace OCR scope was ambiguous because dirty paths included .codestable/reference/agent-conventions.md; per protocol, OCR was skipped and local line review covered current business scope"
---

# ccbd-windows-tcp-loopback-transport 代码审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-20-ccbd-windows-tcp-loopback-transport/ccbd-windows-tcp-loopback-transport-design.md`
- Checklist: `.codestable/features/2026-07-20-ccbd-windows-tcp-loopback-transport/ccbd-windows-tcp-loopback-transport-checklist.yaml`
- Evidence pack: `.codestable/features/2026-07-20-ccbd-windows-tcp-loopback-transport/ccbd-windows-tcp-loopback-transport-evidence-pack.md`
- Gate results: `.codestable/features/2026-07-20-ccbd-windows-tcp-loopback-transport/ccbd-windows-tcp-loopback-transport-scope-gate.json`
- DoD results: `.codestable/features/2026-07-20-ccbd-windows-tcp-loopback-transport/ccbd-windows-tcp-loopback-transport-dod-results.json`
- Implementation evidence: 当前工作区 diff、REV-009/REV-010 review-fix、后续 bootstrap/endpoint review-fix、targeted pytest、独立 reviewer `019f8758-4201-7ff2-bbcf-96f7919c6bb1` 输出、主线程本地行级核验。
- Diff basis: `git status --short` + 当前 unstaged diff；无 staged diff。业务 review scope 为 `lib/ccbd/control_plane_transport/factory.py`、`token_auth.py`、`windows_tcp.py`、`test/test_ccbd_control_plane_transport_unix.py`、`test/test_ccbd_windows_tcp_loopback_transport.py`。
- Review mode: full-rereview after material review-fix
- Baseline dirty files: `.codestable/reference/agent-conventions.md` 为本轮 CodeStable runtime sync 变更，已从业务代码 review scope 排除。

### Independent Review

- Detection: Task agent 可用；OCR CLI `where.exe ocr` 和 `ocr llm test` 可用。
- 环节 A 独立隔离 Task agent: independent-agent + completed，ref `019f8758-4201-7ff2-bbcf-96f7919c6bb1`。
- 环节 B OCR CLI: skipped；当前 dirty paths 包含 `.codestable/reference/agent-conventions.md`，`ocr review` 无显式文件列表参数，裸 workspace 会越过本 feature 业务 scope。
- OCR severity mapping: High->blocking/important, Medium->nit/suggestion, Low->discarded。
- Merge policy: 环节 A findings 已逐条本地事实核验并合并；OCR 因 scope ambiguous 跳过，本地行级审查覆盖当前业务 diff。
- Gate effect: passed；下游 gate 有 completed subagent reviewer 锚点。

## 2. Diff Summary

- 新增：none
- 修改：`lib/ccbd/control_plane_transport/factory.py`、`lib/ccbd/control_plane_transport/token_auth.py`、`lib/ccbd/control_plane_transport/windows_tcp.py`、`test/test_ccbd_control_plane_transport_unix.py`、`test/test_ccbd_windows_tcp_loopback_transport.py`
- 删除：none
- 未跟踪 / staged：无 staged diff；未发现本轮业务 scope 外未跟踪代码文件。
- 风险热点：Windows TCP token handshake 时序、bootstrap self-ping 并发/认证边界、endpoint descriptor validation、Windows direct endpoint 错误映射、Unix fallback 不漂移。

## 3. Adversarial Pass

- 假设的生产 bug：同机慢速 pre-auth 连接、坏旧 endpoint store 或 direct legacy descriptor 会让 Windows bootstrap / connect 偶发失败并暴露原生异常。
- 主动攻击过的反例：bad token 文件、旧 `unix_socket` descriptor、缺 `token_ref`、坏 JSON、坏 `port` / out-of-range port、bad host、address-only bad host/range、慢 pre-auth client、slow-drip pre-auth client、client 发 ping 前 worker 先读超时、坏旧 endpoint store 后 listen+bootstrap、Unix legacy fallback 回归。
- 结果：已闭合的反例均有生产修复与测试覆盖；真实 Windows ACL / 多用户权限 / loopback 环境策略留给 QA residual risk。

## 4. Findings

### blocking

none

### important

none

### nit

none

### suggestion

- [ ] 可补充 direct endpoint dict 的 host mismatch、address/host mismatch、zero/negative port 参数化测试。
  - Evidence: 当前生产代码会通过 `factory.py` / `windows_tcp.py` 映射为 `RpcTransportAuthError('endpoint-invalid')`；现有测试已覆盖主要 legacy/direct invalid descriptor。
  - Impact: 测试加固建议，不影响当前 gate。

### learning

- REV-009 已闭合：client 发送 token 后等待 server ack；server 只有 token compare 成功才 ack，bad token 在 `connect()` 阶段结构化失败。
- REV-010 已闭合：legacy store 与 Windows direct dict 的非法 endpoint 均映射为 `RpcTransportAuthError('endpoint-invalid')`，Unix legacy fallback 保持非 Windows 路径兼容。
- Bootstrap self-ping 修复的关键边界是认证后先由 client 写入 ping，再 enqueue authenticated connection，避免 worker 在请求写入前读超时。
- Server auth 读取使用绝对预算，slow-drip pre-auth client 不再能无限占住 listener accept。

### praise

- 修复保持在 control-plane transport seam 内，没有改 RPC schema、handler dispatch 或 named pipe / Rmux / pid liveness 范围。
- 测试矩阵覆盖了 review 发现的关键反例，同时保留 Unix/fake/socket/server 回归。

## 5. Test And QA Focus

- QA 必须重点复核：bad token 在 client `connect()` 阶段结构化失败且 handler 不执行；坏旧 endpoint store 后 `listen()` 发布 fresh endpoint 并 bootstrap 成功；slow pre-auth / slow-drip pre-auth client 不拖垮 bootstrap；direct endpoint dict 非法形状映射 `endpoint-invalid`；Unix legacy fallback 不漂移。
- Evidence pack residual risks / gate warnings：evidence pack 与 DoD results 是较早快照，`CMD-003` 仍记录 `7 passed`；本轮 review-fix 后当前命令结果已更新为 `33 passed`，进入 QA 前建议刷新 evidence pack。
- 建议新增或加强的测试：direct dict host mismatch、address/host mismatch、zero/negative port；已有 live mounted endpoint 时拒绝覆盖 / ownership guard 集成场景。
- 不能靠 review 完全确认的点：真实 Windows ACL owner/SID/allow-read 收敛、域用户 / 非英文 PowerShell ACL 输出、跨用户 token 读取拒绝、杀软/防火墙对 loopback 的影响。

## 6. Residual Risk

- OCR lane 未跑业务文件级 review：CLI 可用，但没有文件列表参数，当前 workspace dirty scope 混入 CodeStable runtime 文件；本轮以独立 Task agent + 主线程本地行级审查收口。
- CodeGraph 未初始化；结构审查通过文件读取、`rg` 和测试覆盖完成。
- 真实 Windows 多用户 ACL 与环境策略仍需 QA / acceptance 真机复核。
- design 中“已有 live listener 与 endpoint token 匹配时拒绝替换”的完整 ownership contract 可能由 app-level ownership guard 承担，本轮 review 未单独证明该集成场景。

## 7. Verdict

- Status: passed
- Next: Goal feature 通过 code review gate；下一步回到 epic / feature workflow 进入 QA。

## 8. Focused Closure

- Closed findings: REV-001, REV-002, REV-003, REV-007, REV-008, REV-009, REV-010, bootstrap-auth-accept-race, direct-endpoint-error-mapping, stale-endpoint-error-after-listen, slow-drip-preauth-budget
- Attributed delta:
  - `lib/ccbd/control_plane_transport/factory.py`
  - `lib/ccbd/control_plane_transport/token_auth.py`
  - `lib/ccbd/control_plane_transport/windows_tcp.py`
  - `test/test_ccbd_control_plane_transport_unix.py`
  - `test/test_ccbd_windows_tcp_loopback_transport.py`
- Targeted verification:
  - `python -m pytest -q test/test_ccbd_windows_tcp_loopback_transport.py` -> 33 passed
  - `python -m pytest -q test/test_ccbd_control_plane_transport_unix.py test/test_ccbd_socket_server.py` -> 16 passed
  - `python -m pytest -q test/test_ccbd_windows_tcp_loopback_import_guard.py` -> 2 passed
  - `python -m pytest -q test/test_ccbd_bootstrap_probe.py test/test_ccbd_control_plane_transport_fake.py` -> 6 passed, 5 skipped
  - `python -m pytest -q test/test_v2_start_service.py -k "ccbd or endpoint or ping or socket"` -> 2 passed, 18 deselected
  - `python -m pytest -q test/test_ccbd_socket_server.py test/test_ccbd_socket_lifecycle.py` -> 2 passed, 5 skipped
  - `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-20-ccbd-windows-tcp-loopback-transport/ccbd-windows-tcp-loopback-transport-checklist.yaml" --yaml-only` -> passed
  - `python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml"` -> passed
  - `git diff --check` -> passed
- Classification: 本轮不是 focused-closure-only；REV-009/REV-010 及后续 reviewer findings 涉及生产行为，已完成完整独立复审并由 subagent gate 放行。
