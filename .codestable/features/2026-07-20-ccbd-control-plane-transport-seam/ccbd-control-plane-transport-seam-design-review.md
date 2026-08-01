---
doc_type: feature-design-review
feature: 2026-07-20-ccbd-control-plane-transport-seam
status: passed
review_state: passed
review_reason: ""
reviewer_id: "019f7ca0-86b2-7f53-8c66-6b1d1b1e77e3"
reviewed: 2026-07-20
round: 1
---

# ccbd-control-plane-transport-seam feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-20-ccbd-control-plane-transport-seam/ccbd-control-plane-transport-seam-design.md`
- Checklist: `.codestable/features/2026-07-20-ccbd-control-plane-transport-seam/ccbd-control-plane-transport-seam-checklist.yaml`
- Intent / brainstorm: none
- Roadmap: `.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-roadmap.md`、`.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml`
- Related docs: roadmap §4.9 / §8 Windows control-plane transport blocker
- Code facts checked:
  - `lib/ccbd/socket_client_runtime/transport.py`
  - `lib/ccbd/socket_server_runtime/lifecycle.py`
  - `lib/ccbd/socket_server_runtime/bootstrap_probe.py`
  - `lib/ccbd/socket_server_runtime/protocol.py`
  - `lib/ccbd/socket_server_runtime/loop.py`
  - `lib/ccbd/system.py`
  - `lib/storage/paths.py` / `lib/storage/paths_ccbd.py`

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: `019f7ca0-86b2-7f53-8c66-6b1d1b1e77e3`
- Raw output: 首轮 `changes-requested`，提出 2 个 blocking 和 1 个 important；focused closure 后 verdict `passed`
- Merge policy: 主 agent 已核验源码事实，修订 design/checklist，并由同一 reviewer focused closure
- Gate effect: 独立 reviewer completed + closure verified；允许定稿 `passed`

## 2. Design Summary

- Goal: 为 ccbd 控制面 RPC 抽出 transport seam，Unix 保持 AF_UNIX 行为不变，并提供 fake transport 测试替身。
- Key contracts: endpoint descriptor canonical-first；legacy `socket_path` 兼容投影保留；connection protocol 覆盖 `settimeout/sendall/recv/close/__enter__/__exit__`；bootstrap 通过 adapter-facing primitive 封装 readiness/select/poll。
- Steps: 7 个步骤，覆盖 endpoint、interface/frame、Unix adapter、bootstrap probe、fake transport、lease/diagnostics、guard/regression。
- Checks: 7 项检查，覆盖 endpoint store/factory、Unix adapter、fake transport、frame/handler 不变、diagnostics 和 scope guard。
- Baseline / validation: YAML 校验、Unix/fake transport tests、bootstrap/server/client regression、start/ping diagnostics、AF_UNIX import guard。

## 3. Findings

### blocking

none

### important

none

### nit

none

### suggestion

none

### learning

- 控制面 transport seam 不能只抽 connect/listen；bootstrap readiness、peer evidence、deferred connection 和 connection context-manager 也是现有契约的一部分。

### praise

- 修订后 design 明确把 endpoint store/factory 放进 transport boundary，能避免 CLI/keeper/doctor 后续各自分叉平台判断。

## 4. User Review Focus

- 用户需要重点拍板：本 child 只交付 seam + Unix adapter + fake transport，不交付 Windows TCP loopback/token ACL/named pipe。
- implement 需要重点遵守：JSON-line frame、`RpcRequest/RpcResponse`、handler dispatch 和业务 op 不变；same-user/stale cleanup 不得降级为弱连接检查。
- code review / QA / acceptance 需要重点复核：fake transport 是否真的不依赖真实 socket 跑通 bootstrap/handler；Unix stale cleanup/live socket refusal 是否不漂移；legacy `socket_path` 是否仍可用。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | design §3.1 / §3.3 覆盖 AC-001 至 AC-008 | none |
| DoD Contract | pass | E | design §3.4 覆盖 Design / Implementation / Review / QA / Acceptance DoD 与 validation commands | none |
| Steps and checks traceability | pass | E | checklist steps/checks 对应 design §2.4、§3.1、§3.4 | none |
| Roadmap contract compliance | pass | E | roadmap item `ccbd-control-plane-transport-seam` 与 design frontmatter / summary 对齐 | none |
| Module interface design | pass | C | design §2.1 定义 endpoint/factory/interface/unix/fake；源码核验 protocol/loop/bootstrap 最小连接契约 | none |
| Validation and artifacts | pass | E | checklist `dod.commands` 覆盖 YAML、unit、regression、diagnostics、guard；YAML 校验通过 | none |

Summary: E=5, C=1, H=0, H-only core checks=none。

## 6. Residual Risk

- Windows TCP loopback adapter 的 token handshake、ACL 和 endpoint cleanup 仍需后续 item 设计；本 feature 只保证 seam 足够承载该 adapter，并通过 fake transport 证明 handler/frame 解耦。

## 7. Verdict

- Status: passed
- Next: 返回 `cs-epic` child design batch loop，继续下一个 epic child；本 child design 保持 `draft`，等待所有 child design-review 通过后由 epic 统一确认。

## 8. Focused Closure

- Closed findings: FDR-001、FDR-002、FDR-003
- Attributed delta: `.codestable/features/2026-07-20-ccbd-control-plane-transport-seam/ccbd-control-plane-transport-seam-design.md`、`.codestable/features/2026-07-20-ccbd-control-plane-transport-seam/ccbd-control-plane-transport-seam-checklist.yaml`
- Verification: reviewer `019f7ca0-86b2-7f53-8c66-6b1d1b1e77e3` focused closure verdict `passed`；checklist YAML 与 roadmap items YAML 校验通过
- Classification: 修订只关闭首轮 design-review findings，未修改生产代码；补强的是设计契约与 checklist 覆盖，不改变 roadmap 范围
