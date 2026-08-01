---
doc_type: feature-acceptance
feature: 2026-07-31-mux-backend-contract-herdr-v2
status: passed
audit_state: not-started
audit_reason: ""
auditor_id: ""
acceptance_authorization_ref: approval-report.md#goal-acceptance
accepted: 2026-08-01
round: 1
---

# mux-backend-contract-herdr-v2 验收报告

## 授权

以 goal-state `acceptance_authorization_ref: approval-report.md#goal-acceptance`（approved）显式进入
验收（ResumeGoalAcceptance）。该授权来自 canonical `approval_groups.goal-execution`，confirmation id
`goal-execution-2026-08-01-windows-native-herdr-ccb`，机械核验为 approved；未把 Goal driver 运行当作 owner 批准。

## 前置门槛

- Code review：`status=passed`，`reviewer: subagent`，review gate passed，0 blocking，2 条 info 级观察（非阻塞）。
- QA：`status=passed`，无 unresolved failed/blocked；DoD 命令 fresh 全绿 + 运行时功能驱动全部断言通过。
- before_review gates：scope-gate / dod-runner / evidence-pack 均 `passed`。

## Acceptance Coverage（design AC-001..010）

| AC | 验收点 | 证据 | 结论 |
|---|---|---|---|
| AC-001 | tmux/rmux refs/tests 兼容不退化 | CMD-003 34 passed、CMD-004 16 passed；运行时 linux->rmux | passed |
| AC-002 | Herdr namespace/pane refs 表达 herdr-native/herdr/herdr_socket/restore_token | contract 单测 + 运行时 make_namespace_ref | passed |
| AC-003 | MuxCapabilitiesV2 含 windows_beta_gaps/blocking_gaps，blocking fail-closed | 运行时 beta-gap -> unsupported-capability | passed |
| AC-004 | MuxCommandErrorV2 支持 schema-mismatch 与 evidence | contract 单测 | passed |
| AC-005 | Fake Herdr backend 驱动 create/split/send/capture/kill 不依赖 Herdr JSON | fake backend 单测 | passed |
| AC-006 | 显式 Herdr request 无 capability evidence fail-closed（herdr-capability-missing，不建生产 backend） | 运行时 no-evidence 断言 | passed |
| AC-007 | platform-gate-blocked / herdr-unavailable / schema-mismatch 各带 refs | 运行时 no-platform-gate + 结构化失败单测 | passed |
| AC-008 | auto：Native Win x64 直路由 Herdr，缺 evidence blocked；非 Windows/WSL 保留 tmux/rmux | 运行时 herdr-success + linux-legacy | passed |
| AC-009 | 缺上游 spike evidence / stop 建议 / blocked verdict / 非 none failure_class / blocking_gaps / unknown 时 fail-closed 且有 blocked fixture | CMD-006 exit 0 | passed |
| AC-010 | 不改 provider runtime/ccbd durable state/package metadata/doctor tier，不新增生产 Herdr client | CMD-005 scope guard exit 0 | passed |

## DoD Results

CMD-001..006 fresh 全部 `exit 0`：checklist/items YAML 校验通过；contract+selection 34 passed；
v2 namespace 16 passed；scope guard 无越界；上游 spike fail-closed guard 与 blocked fixture 一致。

## Gate Results

- scope-gate.json：passed（`lib/terminal_runtime/*` 与本 feature 目录，无 provider/ccbd/package 越界）
- dod-results.json：passed（CMD-001..006 exit 0）
- evidence-pack-results.json：passed
- code review gate：passed（reviewer: subagent）
- qa gate：passed

## Writeback

- checklist：10 项 checks 全部 `pending -> passed`（steps 早已全 done）。
- items.yaml：`mux-backend-contract-herdr-v2` `status: in-progress -> done`，notes 更新为交付摘要。
- roadmap 主文档：item 3 `状态：in-progress -> accepted`，备注更新。
- reference/architecture/requirement：按 design 第 4 节，本 feature 为内部 contract 层，
  不改对外 requirement/architecture 文档；为下游 `herdr-backend-client` 提供内部 CCB contract。

## Residual Risks

- `archguard` / `meta_cc` provider 维持 skipped：本 feature 无跨模块架构改动，风险低，evidence pack 已如实标注；非核心验收缺口。
- review info 观察①：`_has_supported_herdr_capabilities` 在完全缺 ref 时归类 `unsupported-capability` 而非
  `herdr-capability-missing`——两路径均 fail-closed（effective_backend=None），仅措辞差异，记为可选后续，不阻塞。

## Delivery Record

- 新增 `lib/terminal_runtime/{mux_backend_contract,fake_mux_backend,backend_resolver}.py`。
- 新增/扩展 `test/test_terminal_runtime_backend_selection.py`、`test/test_mux_backend_contract.py`、`test/test_herdr_spike_no_production_route.py`。
- 前序 review 发现的三处 fail-open 已由 issue `2026-08-01-mux-backend-contract-herdr-v2` 修复并回归。

## Verdict

**passed** —— 全部 AC 有实际证据、DoD/Gate 全绿、writeback 完成、残留风险非核心且如实记录。
