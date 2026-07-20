---
doc_type: feature-design-review
feature: 2026-07-20-ccbd-windows-tcp-loopback-transport
status: passed
review_state: passed
review_reason: ""
reviewer_id: "019f7ca8-62f3-7461-a459-3c3a0eb5f80b"
reviewed: 2026-07-20
round: 1
---

# ccbd-windows-tcp-loopback-transport feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-20-ccbd-windows-tcp-loopback-transport/ccbd-windows-tcp-loopback-transport-design.md`
- Checklist: `.codestable/features/2026-07-20-ccbd-windows-tcp-loopback-transport/ccbd-windows-tcp-loopback-transport-checklist.yaml`
- Intent / brainstorm: none
- Roadmap: `.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-roadmap.md`、`.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml`
- Related docs: roadmap §4.9 / §8 Windows control-plane transport blocker；前序 feature `ccbd-control-plane-transport-seam`
- Code facts checked:
  - `lib/ccbd/socket_client_runtime/transport.py`
  - `lib/ccbd/socket_server_runtime/lifecycle.py`
  - `lib/ccbd/socket_server_runtime/bootstrap_probe.py`
  - `lib/ccbd/system.py`
  - `.codestable/features/2026-07-20-ccbd-control-plane-transport-seam/ccbd-control-plane-transport-seam-design.md`
  - `.codestable/features/2026-07-20-ccbd-control-plane-transport-seam/ccbd-control-plane-transport-seam-design-review.md`

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: `019f7ca8-62f3-7461-a459-3c3a0eb5f80b`
- Raw output: 首轮 `changes-requested`，提出 2 个 important；focused closure 后 verdict `passed`
- Merge policy: 主 agent 已核验 roadmap、前序 seam design 和代码事实；修订 design/checklist 后由同一 reviewer 做 focused closure
- Gate effect: 独立 reviewer completed + closure verified；允许定稿 `passed`

## 2. Design Summary

- Goal: 实现 Windows TCP loopback control-plane transport adapter，绑定 `127.0.0.1:0`，通过 same-user token handshake 接入前序 transport seam。
- Key contracts: Windows 默认 `tcp_loopback`，Unix 不漂移；endpoint canonical authority 是 `host/port/token_ref`；token ACL 无法证明收敛时 fail-fast；handshake 必须在 JSON-line handler 前完成；bootstrap self-ping 走同一 auth path。
- Steps: 7 个步骤，覆盖 endpoint store/platform selection、token ACL、TCP listener/connector、handler 前握手、bootstrap、diagnostics redaction、regression guard。
- Checks: 8 项检查，覆盖平台默认、listen endpoint、ACL fail-fast、handshake、bootstrap、canonical-first endpoint、redaction 和 scope guard。
- Baseline / validation: YAML 校验、TCP adapter/token/handshake tests、bootstrap/seam regression、start/ping 抽样、secret/no named pipe/no schema change guard。

## 3. Findings

### blocking

none

### important

none

### nit

none

### suggestion

- 后续 implementation / code review 应重点检查 Windows ACL evidence 是否按当前用户 SID / owner 收敛；无法可靠解析本地化 `icacls`、继承 ACE 或等价 ACL evidence 时必须归为 `token-unprotectable`。

### learning

- 当前代码事实仍显示 server loop 在 `accept()` 后入队，worker 再进入 JSON-line `handle_connection()`；因此 Windows token auth 必须落在 transport `accept/connect` 边界，不能放进 handler。

### praise

- design 与 roadmap §4.9 / items.yaml item 18 对齐：TCP loopback、same-user token、ACL fail-fast、bootstrap self-ping、handler/schema 不变、named pipe 不实现、pid liveness 不混入均有设计证据和 checklist 追踪。

## 4. User Review Focus

- 用户需要重点拍板：本 child 只实现 TCP loopback adapter；named pipe 仍只是 documented fallback，触发条件留给后续 ADR / owner 决策。
- implement 需要重点遵守：只能消费前序 `ccbd-control-plane-transport-seam`，不得在 CLI/server loop 直接加 Windows 分支；bad/missing token 不能进入 handler queue。
- code review / QA / acceptance 需要重点复核：token ACL fail-fast、不 publish endpoint 的失败路径、bootstrap 同 auth path、`socket_path` null projection、diagnostics/log/snapshot/error/artifact token redaction。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | design §3.1 / §3.3 覆盖 AC-001 至 AC-008 | none |
| DoD Contract | pass | E | design §3.4 覆盖 Design / Implementation / Review / QA / Acceptance DoD 与 validation commands | none |
| Steps and checks traceability | pass | E | checklist steps/checks 对应 design §2.4、§3.1、§3.4；YAML 校验通过 | none |
| Roadmap contract compliance | pass | E | roadmap §4.9 和 item `ccbd-windows-tcp-loopback-transport` 要求 TCP loopback + token ACL + fail-fast；design frontmatter / summary 对齐 | none |
| Module interface design | pass | C | 前序 seam design/review 已定义 endpoint/factory/listener/connection/bootstrap primitive；本 design 只新增 Windows adapter/token/store 归属 | implementation 必须先消费 seam |
| Validation and artifacts | pass | E | checklist `dod.commands` 覆盖 YAML、unit、regression、diagnostics、guard；redaction covers 已扩到 diagnostics/log/snapshot/error/artifact | none |

Summary: E=5, C=1, H=0, H-only core checks=none。

## 6. Residual Risk

- Windows ACL 证明仍是实现高风险点；code review / QA 必须检查本地化 `icacls`、继承 ACE、Administrators / SYSTEM 语义和失败归类。
- 当前生产代码仍是 AF_UNIX 直连形态；本 child 实现时必须依赖前序 seam 的落地结果，不能绕过 seam 直接改 CLI 或 server loop。

## 7. Verdict

- Status: passed
- Next: 返回 `cs-epic` child design batch loop，继续下一个 epic child；本 child design 保持 `draft`，等待所有 child design-review 通过后由 epic 统一确认。

## 8. Focused Closure

- Closed findings: FDR-001、FDR-002
- Attributed delta: `.codestable/features/2026-07-20-ccbd-windows-tcp-loopback-transport/ccbd-windows-tcp-loopback-transport-design.md`、`.codestable/features/2026-07-20-ccbd-windows-tcp-loopback-transport/ccbd-windows-tcp-loopback-transport-checklist.yaml`
- Verification: reviewer `019f7ca8-62f3-7461-a459-3c3a0eb5f80b` focused closure verdict `passed`；checklist YAML 与 roadmap items YAML 校验通过
- Classification: 修订只关闭 reviewer 提出的契约澄清问题，未修改生产代码；没有改变 feature 范围、公开 RPC schema、handler 行为或 roadmap 边界
