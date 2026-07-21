---
doc_type: feature-review
feature: 2026-07-20-ccbd-windows-tcp-loopback-transport
status: blocked
reviewer: subagent
reviewed: 2026-07-22
round: 4
lane_a_state: completed
lane_a_ref: "019f8704-e9a9-7fe3-9195-5c5cf3ccaa64"
lane_a_reason: "independent Task agent reviewer completed full rerun after REV-007/REV-008 fix; returned one blocking handshake finding and one important endpoint validation finding"
lane_b_state: failed
lane_b_ref: ""
lane_b_reason: "ocr review --audience agent --format text --concurrency 2 --timeout 5 timed out after 184s before returning mergeable findings"
---

# ccbd-windows-tcp-loopback-transport 代码审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-20-ccbd-windows-tcp-loopback-transport/ccbd-windows-tcp-loopback-transport-design.md`
- Checklist: `.codestable/features/2026-07-20-ccbd-windows-tcp-loopback-transport/ccbd-windows-tcp-loopback-transport-checklist.yaml`
- Evidence pack: `.codestable/features/2026-07-20-ccbd-windows-tcp-loopback-transport/ccbd-windows-tcp-loopback-transport-evidence-pack.md`
- Gate results: `.codestable/features/2026-07-20-ccbd-windows-tcp-loopback-transport/ccbd-windows-tcp-loopback-transport-scope-gate.json`
- DoD results: `.codestable/features/2026-07-20-ccbd-windows-tcp-loopback-transport/ccbd-windows-tcp-loopback-transport-dod-results.json`
- Implementation evidence: 当前工作区 diff、REV-007/REV-008 review-fix 后 targeted pytest、独立 reviewer `019f8704-e9a9-7fe3-9195-5c5cf3ccaa64` 输出、主线程本地行级核验。
- Diff basis: `git status --short` + 当前 unstaged/untracked diff；无 staged diff。新增文件为 untracked，已作为本轮 scope 读取。
- Review mode: full-rereview after material review-fix
- Baseline dirty files: 当前 dirty 文件均属于本 feature / epic goal-state；未发现无关业务 dirty 文件。

### Independent Review

- Detection: Task agent 可用；OCR CLI `where.exe ocr` 和 `ocr llm test` 可用。
- 环节 A 独立隔离 Task agent: independent-agent + completed，ref `019f8704-e9a9-7fe3-9195-5c5cf3ccaa64`。
- 环节 B OCR CLI: failed；`ocr review --audience agent --format text --concurrency 2 --timeout 5` 外层 184s 超时，未返回可合并 findings。
- OCR severity mapping: High->blocking/important, Medium->nit/suggestion, Low->discarded。
- Merge policy: 环节 A findings 已逐条本地事实核验并合并；环节 B 已启动但失败，按协议不能定稿 `passed`。
- Gate effect: blocked；需要先做 review-fix 并在下一轮重跑 code review / OCR lane。

## 2. Diff Summary

- 新增：`lib/ccbd/control_plane_transport/endpoint_store.py`、`token_auth.py`、`windows_tcp.py`、`test/test_ccbd_windows_tcp_loopback_transport.py`、`test/test_ccbd_windows_tcp_loopback_import_guard.py`、本 feature 的 DoD / evidence pack / scope gate artifacts。
- 修改：`lib/ccbd/control_plane_transport/endpoint.py`、`factory.py`、`__init__.py`、`lib/ccbd/socket_client_runtime/transport.py`、`lib/ccbd/socket_server_runtime/server.py`、`lib/ccbd/socket_server_runtime/lifecycle.py`、`lib/ccbd/app_runtime/lifecycle.py`、`lib/ccbd/services/mount.py`、feature checklist、roadmap goal-state。
- 删除：none
- 未跟踪 / staged：新增 feature artifacts、新增 adapter/helper/tests 未跟踪；无 staged diff。
- 风险热点：Windows 首启 transport selection、token ACL proof、auth handshake timing、endpoint descriptor validation、endpoint/marker/token cleanup ownership、bootstrap self-ping、Unix fallback 不漂移。

## 3. Adversarial Pass

- 假设的生产 bug：token prelude 在 client 侧没有服务端确认，bad token 连接可能看似成功，后续 RPC 才以超时/断连暴露。
- 主动攻击过的反例：bad token 文件、旧 `unix_socket` endpoint descriptor、缺 `token_ref` descriptor、坏 `port`、descriptor missing / generation mismatch 下 owned token 清理、预置 marker touch 失败、Unix client/server 回归。
- 结果：REV-007 / REV-008 修复已闭合；bad token connect 阶段诊断与 endpoint 结构化校验仍有事实支撑，进入 findings。

## 4. Findings

### blocking

- [ ] REV-009 `lib/ccbd/control_plane_transport/windows_tcp.py:59` / `lib/ccbd/control_plane_transport/token_auth.py:123` client `connect()` 没有等待服务端确认 token handshake。
  - Evidence: `connect()` 在 `sock.connect()` 后调用 `client_authenticate(sock, token_file.token)` 并立即返回 socket；`client_authenticate()` 只 `_send_auth_line()`，没有读取 server ack。服务端验证只发生在 `listener.accept()` 的 `server_authenticate()` 中。
  - Impact: bad token 或被篡改 token 文件会拿到“看似连接成功”的 client socket，失败延后到第一次 RPC/读写，无法在 connect 阶段稳定映射为 `RpcTransportAuthError`。这削弱 AC-005 / handshake-before-handler 的可诊断性，也会让 bootstrap 或 client 调用呈现为超时/空响应。
  - Expected fix scope: 在 transport-owned auth 层补显式 ack/round-trip，保证 `WindowsTcpControlPlaneTransport.connect()` 返回前服务端已确认 token；bad/missing token 必须结构化失败，且 handler 仍不得执行。补 client bad-token connect 阶段失败测试。

### important

- [ ] REV-010 `lib/ccbd/control_plane_transport/factory.py:33` / `lib/ccbd/control_plane_transport/windows_tcp.py:254` Windows legacy socket path 入口对 endpoint descriptor 形状校验过晚。
  - Evidence: `transport_for_legacy_socket_path()` 在 Windows 下读取到任意 descriptor 后，只要 `transport.endpoint is not None` 就返回 `WindowsTcpControlPlaneTransport`；若记录是旧 `unix_socket` 或截断的 `tcp_loopback`，后续 `_endpoint_host_port()` / `load_token_file(str(token_ref or ''))` 可能抛 `ValueError`、`IsADirectoryError` 等原生异常。
  - Impact: 迁移、回滚或脏 runtime root 中的旧 descriptor 会变成难诊断故障，不符合 Windows control-plane endpoint canonical-first 与结构化 failure mapping 的目标。
  - Expected fix scope: 在 factory、endpoint load 或 `connect()` 前置闸门中拒绝非 `tcp_loopback` / 缺 `port` / 缺 `token_ref` / 损坏 descriptor，并映射到类似 `RpcTransportAuthError('endpoint-invalid')` 的项目内错误。补旧 `unix_socket` descriptor、缺字段、坏 JSON/坏 port 的诊断测试。

### nit

none

### suggestion

- [ ] REV-006 `lib/ccbd/control_plane_transport/factory.py:33` / `lib/ccbd/socket_client_runtime/transport.py:12` Windows client 在 endpoint descriptor 缺失时仍会 fallback 到 legacy Unix transport。
  - Evidence: `transport_for_legacy_socket_path(..., prefer_windows=False)` 在 `os.name == 'nt'` 且 `transport.endpoint is None` 时落到 `endpoint_from_legacy_socket_path()`。
  - Impact: Windows client 缺 descriptor 时可能暴露 “unix domain sockets unsupported” 而不是 `endpoint-missing`，这是诊断质量问题，不是本轮 blocking。
  - Suggested boundary: client 侧 Windows 也返回 `WindowsTcpControlPlaneTransport(None, ...)`，但要补 Unix 回归。

### learning

- `endpoint_store.unlink_endpoint()` 的 expected generation guard 方向正确：缺 generation / mismatch 均不删除 descriptor。
- marker 删除已绑定 `endpoint_deleted and marker_created`，避免删除既有 legacy marker。
- owned token cleanup 独立于 descriptor deletion，符合 secret hygiene。

### praise

- REV-007 / REV-008 的修复边界清晰：marker ownership 与 token ownership 拆开处理，测试覆盖 descriptor missing / generation mismatch / preexisting marker。
- Unix adapter 和 server lifecycle 回归未漂移，目标测试仍通过。

## 5. Test And QA Focus

- QA 必须重点复核：bad token 在 client `connect()` 阶段结构化失败；旧/损坏 endpoint descriptor 的错误分类；Windows 无 descriptor 首启；真实 ACL owner/SID/allow-read 收敛；shutdown descriptor missing / generation mismatch 下 token 清理；Unix client/server 回归。
- Evidence pack residual risks / gate warnings：DoD runner 和 scope gate 为 passed；scope-gate `changed_files` 为空，review 已改用真实工作区 diff 与 untracked 文件补足覆盖。OCR lane 本轮仍超时失败。
- 建议新增或加强的测试：client bad-token connect；legacy `unix_socket` descriptor on Windows；missing `token_ref`；bad `port`；损坏 JSON；bootstrap auth failure path。
- 不能靠 review 完全确认的点：真实 Windows ACL 输出、域用户 / 非英文环境 PowerShell identity 输出形态、跨用户 token 读取拒绝、目标机防火墙/安全软件对 loopback 的影响。

## 6. Residual Risk

- OCR review 未返回可用 findings；本报告只合并了独立 Task agent 和主线程事实核验。
- Windows 真机 ACL / same-user 拒绝 / loopback 行为仍需 QA 和 acceptance 复核。

## 7. Verdict

- Status: blocked
- Next: 回到 implementation review-fix，先处理 REV-009；建议同时处理 REV-010。修复后重跑 `cs-code-review`，并重试 OCR lane 或按协议记录 unavailable / failed。

## 8. Focused Closure

- Closed findings: REV-001, REV-002, REV-003, REV-007, REV-008
- Partially addressed: REV-005 -> split into REV-007 / REV-008 and now closed.
- Attributed delta:
  - `lib/ccbd/control_plane_transport/endpoint_store.py`
  - `lib/ccbd/control_plane_transport/windows_tcp.py`
  - `lib/ccbd/socket_server_runtime/server.py`
  - `test/test_ccbd_windows_tcp_loopback_transport.py`
- Targeted verification:
  - `python -m pytest -q test/test_ccbd_windows_tcp_loopback_transport.py` -> 15 passed
  - `python -m pytest -q test/test_ccbd_control_plane_transport_unix.py test/test_ccbd_socket_server.py` -> 16 passed
  - `python -m pytest -q test/test_ccbd_windows_tcp_loopback_import_guard.py` -> 2 passed
  - `python -m pytest -q test/test_ccbd_bootstrap_probe.py test/test_ccbd_control_plane_transport_fake.py` -> 6 passed, 5 skipped
  - `python -m pytest -q test/test_v2_start_service.py -k "ccbd or endpoint or ping or socket"` -> 2 passed, 18 deselected
  - `python -m pytest -q test/test_ccbd_socket_server.py test/test_ccbd_socket_lifecycle.py` -> 2 passed, 5 skipped
  - `git diff --check` -> passed
- Classification: 本轮包含生产行为修复后的完整复审；不是 focused-closure-only。独立 reviewer 发现新的 handshake blocking，因此不得进入 QA。
