---
doc_type: approval-report
unit: .codestable/roadmap/windows-native-herdr-ccb
status: approved
reason: goal-execution
approvals:
  roadmap-review: approved
  roadmap-plan: approved
  all-feature-designs: approved
  ccbd-windows-control-plane-transport-design: approved
  goal-acceptance: approved
  goal-commits: approved
approval_groups:
  child-designs:
    status: approved
    confirmation_id: child-designs-2026-08-02-windows-native-herdr-ccb
    decisions:
      all-feature-designs: approved
      ccbd-windows-control-plane-transport-design: approved
  goal-execution:
    status: approved
    confirmation_id: goal-execution-2026-08-01-windows-native-herdr-ccb
    decisions:
      - goal-acceptance
      - goal-commits
created_at: 2026-07-31
---

# Approval Report

## Decision History

- 2026-07-31：owner 回复“批准”，批准 `approval-report.md#roadmap-review` 与 `approval-report.md#roadmap-plan`，授权将 `windows-native-herdr-ccb` roadmap 从 `draft` 改为 `active` 并进入后续 child design batch。
- 2026-07-31：owner 确认 draft requirement `.codestable/requirements/native-windows-ccb-via-herdr.md`，要求基于 Herdr 全能力 parity 达到 Windows x64 CCB supported；旧的 roadmap review 与 child design-review 已被该 requirement update 取代，需要重新独立审查。
- 2026-07-31：owner 回复“确认”，批准修订后的 `windows-native-herdr-ccb` roadmap，授权将 roadmap 从 `draft` 改回 `active`，并进入 child design-review 重审。
- 2026-08-01：owner 回复“所有 child design统一确认batch-approved”，批准 `approval-report.md#all-feature-designs`，授权将 `windows-native-herdr-ccb` 下 11 个已审查通过的 child feature design 统一标记为 `status: approved`。
- 2026-08-01：owner 通过 `/goal` 启动指令确认 Goal execution，批准 `approval_groups.goal-execution`，同一 confirmation id `goal-execution-2026-08-01-windows-native-herdr-ccb` 覆盖 `approval-report.md#goal-acceptance` 与 `approval-report.md#goal-commits`。
- 2026-08-01：goal driver 执行到 feature 4 `herdr-backend-client` 时，发现其 design 的仓库事实假设在分支 `codestable/windows-native-herdr-ccb-v852-source` 不成立（rmux_backend analog 与 `test/test_rmux_backend_core.py` 不存在、factory 仅 tmux），触发 handoff。owner 指示经 cs-epic/cs-feat 修订该 child design + checklist（对齐真实树、修 CMD-005、明确 factory 接线），已由独立 Task agent design-review **round 4 passed**。该 design 已从 `approved` 重开为 `draft`，`all-feature-designs` 对 `herdr-backend-client` 一项待 owner 再确认；其余 10 个 child design 的 approved 不变。
- 2026-08-01：owner 回复“确认”，批准修订后的 `herdr-backend-client` design + checklist，标记其 `status: approved`，授权清除 goal-state handoff 恢复 `ready-to-dispatch`，由 goal driver 从 `current_feature_index=3` 续跑 feature 4。既有 `goal-execution`/`goal-commits` 授权不变，仍不含 push。
- 2026-08-02：owner 指出早前「环境无 herdr」前提错误——真实 herdr `0.7.5-preview` 位于 `C:\Users\Administrator\AppData\Local\Programs\Herdr\herdr.exe`。goal driver 用真实 herdr 对 ccbd `HerdrCliRequestAdapter` 做首次端到端契约验证（独立 Task agent 真跑，证据 `.../evidence/cmd-013-herdr-cli-contract-verification.md`）：契约字段级几乎完全对齐、5 个必需 capability 真实可用，但暴露 herdr socket client/adapter 层的对接缺陷（server 生命周期无归属、split direction 词汇三方不对齐会污染 CMD-013 reload 布局）。缺陷全部属已 accepted 的 `herdr-backend-client` scope，且当前 feature `ccbd-herdr-namespace-lifecycle` 明确 `herdr_socket_client_changes: forbidden`。goal driver 无权自授权重开 accepted feature / 违反当前 scope guard / 新增 roadmap item，触发 ScopeBoundaryChange owner-stop。既有授权不变。
- 2026-08-02：owner 回复“确认重开后端客户端”，批准 `approval-report.md#decision-needed` 的推荐选项 `ReopenBackendClient`。授权重开已 accepted 的 `herdr-backend-client`，在其 scope 内修复真实 Herdr server 生命周期启动 seam 与 split direction 归一，并补真实 Herdr 回归证据；修复通过 review/QA/acceptance 后恢复 goal-state，回到 `ccbd-herdr-namespace-lifecycle` 采 CMD-013。
- 2026-08-02：goal driver 继续采集 CMD-013，真实 Herdr 可执行与 capability report 已可用，但 `ccb -n` 在 Herdr namespace 创建前失败：`ccbd` 启动日志记录 `RuntimeError: unix domain sockets are not supported on this platform`。当前 `v8.5.2` Herdr 分支缺少旧 `windows-rmux-native-backend` 已验收的 `ccbd-control-plane-transport-seam` / `ccbd-windows-tcp-loopback-transport` 生产代码；直接移植会改变当前 child approved scope，触发新的 ScopeBoundaryChange owner-stop。
- 2026-08-02：owner 选择“新增子项，参考 Windows TCP loopback control-plane transport 的实现”。已新增 `ccbd-windows-control-plane-transport` 作为 `herdr-backend-client` 与 `ccbd-herdr-namespace-lifecycle` 之间的前置 child feature，draft design/checklist 已落盘；goal-state 指针转到该新子项，等待独立 design-review/确认后继续。
- 2026-08-02：owner 回复“确认”，批准新增 `ccbd-windows-control-plane-transport` design + checklist。该 design 已由独立 Task agent `019fbffa-2870-7ca2-b183-793148cec530` review/focused closure 通过；本 report 将 `approval_groups.child-designs` 刷新为 `child-designs-2026-08-02-windows-native-herdr-ccb`，覆盖当前 12 个 child 的 design approval，既有 `goal-execution`/`goal-acceptance`/`goal-commits` 授权不变且仍不含 push。

## Current Decision Needed（已解决）

CMD-013 真实 Native Windows x64 transcript 已落盘到
`.codestable/features/2026-07-31-ccbd-herdr-namespace-lifecycle/evidence/cmd-013-native-windows-herdr-transcript.md`，
但 verdict 为 blocked。阻断点不是 Herdr backend client，而是当前分支的 `ccbd` control-plane
仍为 AF_UNIX-only，Native Windows 下无法启动 public `ccb -> ccbd` 链路。

需要 owner 决定如何把 Windows control-plane transport 前置补回当前 Herdr roadmap。

Resolution: owner selected **CreateRoadmapItem** on 2026-08-02. The roadmap now has
`ccbd-windows-control-plane-transport` as an explicit child feature before
`ccbd-herdr-namespace-lifecycle`.

## Current Options

- **ApproveTransportImport**：批准把旧 rmux 路线中已 accepted 的
  `ccbd-control-plane-transport-seam` 与 `ccbd-windows-tcp-loopback-transport` 移植到当前 Herdr
  roadmap，作为 CMD-013 前置修复。
- **CreateRoadmapItem**：新增独立 child feature，放在 `ccbd-herdr-namespace-lifecycle` 前，重新走
  design / review / QA / acceptance。
- **KeepHandoff**：保持 handoff，暂不继续 CMD-013 与后续 provider/runtime features。

## Current Recommendation

**ApproveTransportImport**。该能力在旧 rmux roadmap 已通过 review/QA/acceptance，并且是
Native Windows public workflow 的硬前置；当前 Herdr roadmap 漏掉它会导致所有后续
`ccb` public workflow 验证不可达。移植仍需 fresh focused tests 与 CMD-013 复跑，不能直接继承旧 pass。

Owner chose the more conservative **CreateRoadmapItem** path. This keeps scope ownership
cleaner than importing transport work into the existing namespace feature, at the cost of
one additional design-review/QA/acceptance loop.

## Decision Needed（已解决）

真实 herdr 首次端到端接触暴露 `herdr-backend-client`（已 accepted）的对接缺陷，需 owner 决定修复归属与排期，goal 才能继续采 CMD-013 transcript。

Resolution: owner approved **ReopenBackendClient** on 2026-08-02.

### 三个缺陷（详见 `.../evidence/cmd-013-herdr-cli-contract-verification.md`）

1. **【高·根本 blocker】server 生命周期无归属**。herdr socket 命令不自动拉起 server，adapter/client/ccbd 均无启动 `herdr server` 的逻辑；现有 11 个 roadmap feature 无一负责启动。第一个写操作即 `NotFound`。
2. **【中·会污染 CMD-013】split direction 词汇三方不对齐**。ccbd 传 `right`/`bottom`，adapter 只认 `left/right/up/down`（`bottom` 落 fallback→`right`），herdr 只收 `right/down`。垂直布局退化成水平，reload transcript 记录错误拓扑。
3. **【中·本 goal 不触发】`send_text`→`pane run` 语义**。`pane run` 把文本当命令执行；字面输入应走 `pane send-text`。ccbd 当前无独立 send_text 调用，不阻塞本 goal，记录待用户输入面 feature 处理。

## Options

- **ReopenBackendClient**：经 `cs-feat` 重开已 accepted 的 `herdr-backend-client`，修缺陷 1（server 生命周期，可能需新增启动 seam）+ 缺陷 2（direction 词汇归一），补真实 herdr 契约回归；完成后回到 `ccbd-herdr-namespace-lifecycle` 采 CMD-013。
- **FileIssues**：以 `cs-issue` 立独立 bug（缺陷 2/3 明确是 adapter bug），server 生命周期（缺陷 1，属架构缺口）另以新 roadmap item 承接。
- **NewRoadmapItem**：server 生命周期作为新 feature/item 插入 roadmap（放在 `ccbd-herdr-namespace-lifecycle` 之前作为依赖），direction 词汇归一并入其中或并入 backend-client 重开。
- **KeepBlocked**：暂不修，保持 handoff。

## Recommendation

**ReopenBackendClient**。三缺陷同源（`herdr-backend-client` 只对 spike/fake 契约验证过，从未对真实 herdr 验证），集中在同一 feature 一次修复 + 补真实 herdr 契约回归最内聚；server 生命周期作为该 feature 内新增启动 seam 处理，避免拆散到多个 item。修复后当前 feature 无需改动即可采到干净 CMD-013 transcript。

## Prior Decision Needed（已解决，保留）

none

## Why Now

Goal execution authorization 已落盘。`goal-state.yaml` 必须使用同一 confirmation id 同步为 `ready-to-dispatch`。

## Context

当前 epic 目标是基于 Herdr 建立 Native Windows x64 CCB public workflow parity 路线。Roadmap 原拆为 11 个 child feature；本次 owner 决策新增第 12 个前置 child `ccbd-windows-control-plane-transport`，覆盖 Native Windows `ccb->ccbd` 控制面 transport seam / TCP loopback/token。当前 child set 覆盖 Windows x64 / CCB `v8.5.2` 基线、Herdr socket spike、mux backend contract V2、Herdr backend client、ccbd control-plane transport、ccbd namespace、provider runtime、bounded recovery、用户可见面、release surface、validation matrix 与 supportability projection。

以下 child feature design-review 已重新通过，且已在本 report 中 batch-approved。Goal package 已按同一顺序落盘并获得 Goal execution authorization：

- `windows-x64-v852-baseline-gate`
- `herdr-backend-contract-spike`
- `mux-backend-contract-herdr-v2`
- `herdr-backend-client`
- `ccbd-herdr-namespace-lifecycle`
- `provider-runtime-on-herdr`
- `herdr-bounded-recovery-boundary`
- `herdr-user-surfaces-parity`
- `windows-x64-release-surface`
- `native-windows-public-workflow-validation-matrix`
- `herdr-supportability-projection`

## Options

- Approved: 批准所有已通过独立 review 的 child design，允许进入 goal package 阶段。
- Rejected: 停留在 child design confirmation gate，并指出需要重审或修订的 child design。
- Approve Goal execution: 已授权 `approval_groups.goal-execution`，同时批准 `goal-acceptance` 和 `goal-commits`。
- Reject Goal execution: 保留 goal package 作为 handoff 材料，不派发 driver，不执行 acceptance / commit。

## Recommendation

Proceed with Goal execution。当前 12 个 child design 均已 approved，goal package 与授权均已落盘；implementation、review、QA、acceptance 和 scoped commit 仍由 goal protocol 的 gate 逐项控制。

## Risks And Tradeoffs

- 批准 design 不代表实现已经完成，也不代表 acceptance、QA、commit 或 release 已授权。
- 后续 implementation 仍必须按 DAG 和每个 child checklist 执行；batch approval 只放行 goal package，不放宽实现依赖。
- Native Windows x64 真机验证、Herdr API 事实、docs/doctor guard、release surface gate 和 support projection artifact 仍是 implementation / QA / acceptance 的硬证据。
- Goal execution 会允许本地 scoped commit；每个 feature accepted 后仍必须机械复核 `goal-commits` authorization，且不包含 push。

## Non-Automatic Actions

本 Goal execution 授权只允许本 roadmap 下每个 feature accepted 后的本地 scoped commit。

不会自动执行 remote push、merge、release、publish、deploy、promotion、production cutover、npm 发布、远端 API 调用或任何生产状态变更。

## After You Answer

按 Goal driver 规则继续执行 `goal-state.yaml` 中的 feature loop。
