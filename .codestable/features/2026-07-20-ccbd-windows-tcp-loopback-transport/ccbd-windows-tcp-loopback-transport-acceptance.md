---
doc_type: feature-acceptance
feature: 2026-07-20-ccbd-windows-tcp-loopback-transport
status: passed
audit_state: not-started
audit_reason: ""
auditor_id: ""
acceptance_authorization_ref: approval-report.md#goal-acceptance
accepted: 2026-07-22
round: 1
---

# ccbd-windows-tcp-loopback-transport 验收报告

> 阶段：阶段 3（验收闭环）
> 验收日期：2026-07-22
> 关联方案 doc：`.codestable/features/2026-07-20-ccbd-windows-tcp-loopback-transport/ccbd-windows-tcp-loopback-transport-design.md`

## 1. 接口契约核对

**接口示例逐项核对**：
- [x] `TcpLoopbackEndpoint` 示例：`kind=tcp_loopback`、`host=127.0.0.1`、`port`、`token_ref`、`generation` → `endpoint.py` / `windows_tcp.py` 实际读取和验证这些字段。
- [x] Windows adapter seam：上层通过 `transport_for_endpoint()`、`transport_for_legacy_socket_path()`、listener / connection 接口使用 transport，未要求 CLI 或 handler 分叉。

**名词层“现状 → 变化”逐项核对**：
- [x] Windows TCP loopback adapter：`WindowsTcpControlPlaneTransport` 已落在 `lib/ccbd/control_plane_transport/windows_tcp.py`。
- [x] endpoint descriptor：`endpoint_store.py` 读写 `control-plane-endpoint.json`，Windows canonical authority 是 endpoint record。
- [x] same-user token：`token_auth.py` 生成 token file、收敛 ACL、执行 client/server handshake。
- [x] bootstrap self-ping：`tcp_bootstrap_readiness_probe()` 走 transport connect + authenticated accept + `RpcRequest(op='ping')`。
- [x] stale cleanup：`unlink_bound_endpoint()` 按 generation/token_ref 清理本 generation endpoint/token。

**流程图核对**：
- [x] generate token file → converge ACL → bind `127.0.0.1:0` → write endpoint → bootstrap probe → connect → token handshake → enqueue authenticated connection → JSON-line handler 均有实际落点。

## 2. 行为与决策核对

**需求摘要逐项验证**：
- [x] Windows 默认 `tcp_loopback`，Unix 仍 `unix_socket`：`factory.py` 与 `test_ccbd_windows_tcp_loopback_transport.py` 覆盖。
- [x] server listen 绑定 `127.0.0.1:0` 并发布 descriptor：`WindowsTcpControlPlaneTransport.listen()` 覆盖。
- [x] token 文件随机生成且无法证明 ACL 收敛时 fail-fast：`create_token_file()` / `converge_token_acl()` 覆盖。
- [x] client 读取 endpoint/token 后连接并完成 handshake：`connect()` + `client_authenticate()` 覆盖。
- [x] bootstrap self-ping 使用同一 token path：QA 的 bootstrap regression 覆盖。
- [x] JSON-line frame、RPC handler、业务 op 不变：guard 与 socket/server 回归覆盖。

**明确不做逐项核对**：
- [x] 未实现 named pipe adapter；`rg` 命中仅为设计、报告和 guard 文本。
- [x] 未修改 `RpcRequest` / `RpcResponse` schema；生产命中仍在既有 api models 与 socket protocol。
- [x] 未修 pid liveness、Rmux/backend/provider/session；相关命中属于其他 feature 或 existing owner。

**关键决策落地**：
- [x] Endpoint canonical-first：Windows direct endpoint 非法形状映射为 `RpcTransportAuthError('endpoint-invalid')`。
- [x] Token auth before handler：server 成功验证 token 后才返回 authenticated connection。
- [x] Bootstrap nonce ping 不新增 RPC op：仍用 `RpcRequest(op='ping')`。
- [x] Token redaction：diagnostics 只输出 token_ref、acl_status、fingerprint。

**挂载点反向核对（可卸载性）**：
- [x] `factory.py`、`windows_tcp.py`、`token_auth.py`、`endpoint_store.py`、Windows TCP tests、import guard 均在 design §2.3 清单内。
- [x] `rg` 反向核查显示新增 transport 引用集中在 `lib/ccbd/control_plane_transport`、socket server runtime seam、diagnostics endpoint projection 和目标测试。
- [x] 拔除沙盘推演：按设计清单移除 Windows adapter/helper/store/tests 后，剩余 Unix/fake/socket seam 仍可独立存在；socket server runtime 仅经 transport seam 调用。

## 3. 验收场景核对

- [x] AC-001 Windows platform factory：QA-003 pass。
- [x] AC-002 server listen / endpoint descriptor：QA-003 pass。
- [x] AC-003 ACL fail-fast：QA-003 pass。
- [x] AC-004 valid token handshake + ping：QA-003 pass。
- [x] AC-005 missing/bad token 不触发 handler：QA-003 pass。
- [x] AC-006 bootstrap self-ping：QA-004 pass。
- [x] AC-007 token redaction：QA-006 pass。
- [x] AC-008 scope guard：QA-006、QA-007、QA-008 pass。

**review 报告重点复核**：
- [x] bad token client `connect()` 结构化失败、坏 endpoint store 后 fresh endpoint、slow/slow-drip preauth、direct endpoint invalid、Unix fallback 均由 QA 矩阵覆盖。
- [x] Evidence pack 的旧 `CMD-003` 快照由 QA fresh `33 passed` 覆盖。
- [x] 真实 Windows 多用户 ACL / 防火墙策略保留为 residual risk，不承载核心自动化缺口。

**QA 报告重点复核**：
- [x] 验证证据来源：`ccbd-windows-tcp-loopback-transport-qa.md`。
- [x] QA status passed，failed / blocked 为 none。
- [x] 功能性核心路径有运行证据，residual-risk 不包含未运行的核心命令。
- [x] Evidence pack、DoD results、gate results 已复核；blocking DoD 有 pass evidence。

## 4. 术语一致性

- `tcp_loopback`：生产代码和测试命中集中在 endpoint / factory / windows_tcp / tests，含义一致。
- `token_ref` / `acl_status` / `fingerprint`：token diagnostics 与 endpoint record 一致。
- `named pipe` / `pywin32`：生产实现无 named pipe adapter 或 pywin32 dependency；命中仅为设计/报告/guard 文本。
- 防冲突：本 feature 未把 TCP loopback 误写成 Rmux/named-pipe mux transport。

## 5. 领域影响盘点（提示而非代写）

- [x] 结构性选择候选：Windows 控制面采用 TCP loopback + same-user token，named pipe 作为 documented fallback。建议后续 `cs-domain` 写 ADR；roadmap §4.9 已明确“落地后走 cs-domain 记 ADR”。
- [x] 新术语候选：`tcp_loopback` endpoint descriptor、same-user token、token_ref/fingerprint。当前无 `requirements/CONTEXT.md` 目录可写，accept 只登记候选。
- [x] 流程级约束候选：auth prelude 必须在 JSON-line handler 前完成；bad token 不入队；endpoint cleanup 只清本 generation。

## 6. requirement delta / clarification 回写

- Feature frontmatter `requirement` 为空，仓库当前无 `requirements/` 目录。
- 本 feature 是 roadmap-owned 内部控制面能力前置，不单独改变 owner-facing terminal workflow；用户可见全链路验收仍由 `ccbd-windows-full-chain-smoke` 承担。
- 结论：无独立 requirement 回写；领域/ADR 候选已在第 5 节登记。

## 7. roadmap 回写

- [x] `.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml` 中 `slug: ccbd-windows-tcp-loopback-transport` 已从 `in-progress` 回写为 `done`。
- [x] `.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-roadmap.md` 第 3 节子 feature 清单对应条目已从 `planned` 回写为 `accepted`。
- [x] YAML 校验通过后作为最终审计证据记录。

## 8. attention.md 候选盘点

- 本 feature 未暴露需要补入 `.codestable/attention.md` 的通用环境 / 工具 / 工作流规则。
- 可复用知识出口：Windows TCP vs named pipe 的稳定权衡更适合 `cs-domain` ADR，而不是 attention。

## 9. 遗留

- 后续优化点：direct endpoint dict 的 host mismatch、address/host mismatch、zero/negative port 已作为 review suggestion 记录，非阻塞。
- 已知限制：真实 Windows 多用户 ACL、域用户 / 本地化 ACL 输出、杀软或防火墙策略未由本机自动化完整证明。
- 实现阶段顺手发现：none。

## 10. 最终审计

- 验证证据来源：`ccbd-windows-tcp-loopback-transport-qa.md`
- Evidence sources：`ccbd-windows-tcp-loopback-transport-evidence-pack.md` / `ccbd-windows-tcp-loopback-transport-dod-results.json` / `ccbd-windows-tcp-loopback-transport-scope-gate.json`
- Inline Verification Matrix：不适用；Goal 模式使用独立 QA 报告。
- 聚合命令：
  - `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-20-ccbd-windows-tcp-loopback-transport/ccbd-windows-tcp-loopback-transport-checklist.yaml" --yaml-only` -> exit 0
  - `python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml"` -> exit 0
  - `python -m pytest -q test/test_ccbd_windows_tcp_loopback_transport.py` -> exit 0, 33 passed
  - `python -m pytest -q test/test_ccbd_bootstrap_probe.py test/test_ccbd_control_plane_transport_fake.py` -> exit 0, 6 passed / 5 skipped
  - `python -m pytest -q test/test_v2_start_service.py -k "ccbd or endpoint or ping or socket"` -> exit 0, 2 passed / 18 deselected
  - `python -m pytest -q test/test_ccbd_windows_tcp_loopback_import_guard.py` -> exit 0, 2 passed
  - `python -m pytest -q test/test_ccbd_control_plane_transport_unix.py test/test_ccbd_socket_server.py` -> exit 0, 16 passed
  - `python -m pytest -q test/test_ccbd_socket_server.py test/test_ccbd_socket_lifecycle.py` -> exit 0, 2 passed / 5 skipped
  - `git diff --check` -> exit 0
- 场景复核：re-verified 9 / trust-prior-verify 0。
- 交付物复核：代码、schema projection、transport route、tests、QA、roadmap writeback 通过；requirement 无独立回写。
- 完整工作区复核：dirty files 归属于 goal-state driver marker、QA/acceptance artifacts、checklist/roadmap/goal-state 回写；无未跟踪业务代码污染。
- diff 清洁度：通过；static scan 命中仅为 guard 文本和 `fingerprint()` symbol。
- 知识沉淀出口：ADR 候选已分流到第 5 节；attention 无候选。
- 结论：通过。
