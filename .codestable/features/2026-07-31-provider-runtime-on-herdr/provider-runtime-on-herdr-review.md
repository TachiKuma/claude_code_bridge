---
doc_type: feature-review
feature: 2026-07-31-provider-runtime-on-herdr
status: passed
reviewer: subagent
reviewed: 2026-08-03
round: 2
lane_a_state: completed
lane_a_ref: "019fc3f8-6f43-77a1-87ec-de13940b95dd"
lane_a_reason: "S7 evidence review by Huygens; no blocking, one important fixed before final report"
lane_b_state: skipped
lane_b_ref: ""
lane_b_reason: "ocr CLI available, but workspace dirty scope is broader than current S7 files; protocol requires local scoped line review instead of bare workspace OCR"
---

# provider-runtime-on-herdr 代码审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-31-provider-runtime-on-herdr/provider-runtime-on-herdr-design.md`
- Checklist: `.codestable/features/2026-07-31-provider-runtime-on-herdr/provider-runtime-on-herdr-checklist.yaml`
- Implementation evidence: `.codestable/features/2026-07-31-provider-runtime-on-herdr/provider-runtime-on-herdr-implementation.md`
- S7 evidence:
  - `.codestable/features/2026-07-31-provider-runtime-on-herdr/evidence/public-providers-snapshot.json`
  - `.codestable/features/2026-07-31-provider-runtime-on-herdr/evidence/native-windows-x64-all-provider-herdr-workflow-transcript.md`
  - `.codestable/features/2026-07-31-provider-runtime-on-herdr/evidence/cmd004-baseline-exemption.md`
- Roadmap state: `.codestable/roadmap/windows-native-herdr-ccb/goal-state.yaml`、`windows-native-herdr-ccb-items.yaml`、`windows-native-herdr-ccb-roadmap.md`
- Diff basis: 当前工作区 unstaged/untracked diff；staged diff 为空。
- Review mode: full-rereview for S7 evidence after prior S6 review.
- Baseline dirty files: 工作区存在大量其他 feature / S1-S6 既有 dirty；本报告只归因 S7 evidence、provider-runtime-on-herdr 状态文档和 roadmap handoff。

### Independent Review

- Detection: Task agent 可用；OCR CLI 可用。
- 环节 A 独立隔离 Task agent: subagent completed，reviewer `Huygens`，ref `019fc3f8-6f43-77a1-87ec-de13940b95dd`。
- 环节 B OCR CLI: skipped。原因：`git status` 非 ignored dirty scope 远超 S7 current scope，按 protocol 不跑裸 workspace OCR，改本地主线程 scoped line review。
- OCR severity mapping: High->blocking/important, Medium->nit/suggestion, Low->discarded。
- Merge policy: 独立 reviewer findings 已逐条本地核验；一个 important 和一个 nit 已在定稿前修复。
- Gate effect: `reviewer=subagent`，无 blocking / important 遗留。

## 2. Diff Summary

- 新增：
  - `evidence/public-providers-snapshot.json`
  - `evidence/native-windows-x64-all-provider-herdr-workflow-transcript.md`
  - `evidence/cmd004-baseline-exemption.md`
- 修改：
  - `provider-runtime-on-herdr-checklist.yaml`
  - `provider-runtime-on-herdr-implementation.md`
  - `provider-runtime-on-herdr-review.md`
  - roadmap `goal-state.yaml` / `items.yaml` / `roadmap.md`
- 删除：none
- 未跟踪 / staged：S7 evidence 和既有 provider-runtime implementation/review artifacts 当前为 untracked；staged 为空。
- 风险热点：blocked evidence 被误投影为 supported、provider catalog 漏项、CMD-004 core command 既有红灯归因、scope guard 全局 dirty 隔离。

## 3. Adversarial Pass

- 假设的生产 bug：blocked transcript 被下游当成 all-provider Herdr supported 证据，导致 release/support 或 public matrix 过早放行。
- 主动攻击过的反例：当前 catalog 新增 `qoder/qoderclicn` 漏 row、Markdown 表有 provider 缺失、`blocked` 被写成 `pass/supported`、CMD-004 失败被吞成全量通过、scope guard 全局失败被误报为干净。
- 结果：catalog 和 transcript 覆盖 20/20；blocked 语义在 transcript、implementation、checklist、roadmap 中均保持；CMD-004 已补 baseline-risk evidence；全局 CMD-009 失败保持既有 dirty 归因。

## 4. Findings

### blocking

none

### important

- [x] REV-001 `provider-runtime-on-herdr-implementation.md:163` CMD-004 core command 失败需要明确 baseline-risk / QA residual evidence。
  - Evidence: design 将 CMD-004 标为 core / fix-or-block；S7 记录 120 秒超时，`-x` 首个失败为 `codex runtime bootstrap missing declared artifacts: input.fifo, output.fifo`。
  - Impact: 下游不能把 S7 理解为 runtime launch regression 全量干净。
  - Fix: 新增 `evidence/cmd004-baseline-exemption.md`，明确这是 S4 前已记录的 Codex bridge bootstrap 基线风险；implementation 和 checklist 改为引用该 baseline-risk，禁止解释为 CMD-004 全量通过。
  - Verification: YAML 校验、diff check、scoped content guard 通过。

### nit

- [x] REV-002 `evidence/public-providers-snapshot.json:15` snapshot source line 只写 `:5`，未覆盖 optional provider 行。
  - Fix: 改为 `lib/provider_core/registry_runtime/builtin_backends.py:5-23`；transcript source ref 同步为 `:5-23`。

### suggestion

- [ ] REV-003 `evidence/native-windows-x64-all-provider-herdr-workflow-transcript.md:73` 后续可追加 machine-readable provider workflow blocked matrix JSON，减少 QA/acceptance 解析 Markdown 表的成本。当前人工可读 transcript 足以支撑 S7，不阻塞。

### learning

- 当前 public provider catalog 为 20 项，`qoder` 和 `qoderclicn` 是相对 design baseline 的新增公开 provider，S7 transcript 必须覆盖它们。
- CMD-011 blocked evidence 是 admissible manual evidence，但不能变成 supportability projection；真正 supported 仍需要逐 provider Native Windows x64 Herdr launch/ask/pend-completion/cancel pass transcript。

### praise

- transcript 多处明确 `blocked` 和“不得宣称 supported”，roadmap 也保持 `provider-runtime-on-herdr` 为 `in-progress`，没有提前写 acceptance passed。

## 5. Test And QA Focus

- QA 必须复核 `public-providers-snapshot.json` 与当前 catalog 一致，并确认 transcript rows 覆盖全部 20 个 provider。
- QA 必须复核 `cmd004-baseline-exemption.md`：CMD-004 只能作为 baseline-risk 隔离，不能被折叠成 pass。
- QA 必须继续隔离全局 CMD-009 既有 dirty `test/test_herdr_backend_client.py`，不能把全局 guard 失败误归因到 S7，也不能声称全局 scope guard 干净。
- 建议新增或加强的测试：后续可补 provider workflow blocked matrix JSON 的 schema check；当前不阻塞。
- 不能靠 review 完全确认的点：真实 provider credentials / production API readiness 未验证；所有 provider workflow 仍是 blocked，不是 pass。

## 6. Residual Risk

- CMD-004 全量 runtime launch bundle 仍有 Codex bridge bootstrap 基线红灯；已归因并要求 QA 保留 baseline-risk。
- 工作区 dirty 范围很大，本 review 只覆盖 S7 current scope；全局 clean 需要后续 owner 单独收敛。
- 所有 public provider 的 Native Windows x64 Herdr workflow 都是 blocked evidence；任何 support/release/public matrix 投影必须继续 fail closed。

## 7. Verdict

- Status: passed
- Next: Goal lane 进入 `cs-feat` QA 阶段。QA 重点复核 provider catalog freshness、all-provider blocked evidence、CMD-004 baseline-risk、scope guard dirty 隔离和 blocked/supported 投影。

## 8. Focused Closure

- Closed findings: REV-001, REV-002
- Attributed delta:
  - `evidence/cmd004-baseline-exemption.md`
  - `evidence/public-providers-snapshot.json`
  - `evidence/native-windows-x64-all-provider-herdr-workflow-transcript.md`
  - `provider-runtime-on-herdr-implementation.md`
  - `provider-runtime-on-herdr-checklist.yaml`
- Targeted verification:
  - checklist YAML validation: passed
  - public-providers snapshot JSON validation: passed
  - scoped S7 content guard: passed
  - scoped diff check: passed
- Classification: docs/evidence-only closure;未改变业务行为、公开契约、安全、数据、并发或架构，只加强 baseline-risk 归因和 source refs。
