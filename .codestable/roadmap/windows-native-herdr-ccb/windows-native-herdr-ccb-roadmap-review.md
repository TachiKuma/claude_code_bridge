---
doc_type: roadmap-review
roadmap: windows-native-herdr-ccb
status: passed
review_state: passed
review_reason: ""
created: 2026-07-30
reviewed: 2026-07-31
round: 2
reviewer: 019fb8b8-2b7c-7160-9b3a-f05048a10630
reviewer_id: 019fb8b8-2b7c-7160-9b3a-f05048a10630
tags: [windows, native-windows, herdr, x64, roadmap-review]
---

# windows-native-herdr-ccb roadmap 审查报告

## 1. Scope And Inputs

- Roadmap: `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-roadmap.md`
- Items: `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml`
- Requirement: `.codestable/requirements/native-windows-ccb-via-herdr.md`
- Related docs: `.codestable/brainstorms/windows-native-herdr-ccb/brainstorm.md`, `.codestable/brainstorms/windows-native-herdr-ccb/feasibility-report.md`, `.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-roadmap.md`
- Feature docs checked: 11 个 child feature design / checklist / design-review frontmatter
- Code facts checked: none，本轮为 requirement-driven roadmap/design 文档重审

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: Pauli `019fb8b8-2b7c-7160-9b3a-f05048a10630`
- Raw output: 独立 reviewer 返回 blocking none、2 个 important、1 个 nit、1 个 suggestion 和 residual risks
- Merge policy: 主 agent 已逐条按 roadmap/items/design-review 文件事实核验并修复 important / suggestion
- Gate effect: roadmap review passed；child design-review 仍保持 `changes-requested`，需要后续逐项重审

## 2. Roadmap Summary

- Goal completion signal: 以用户自备 Herdr 的全能力 parity 为基础，让 Native Windows x64 达到 CCB supported。
- Hard gates: strict CCB `v8.5.2` 源头新分支、Native Windows 直接路由 Herdr、所有公开 provider 的 `ask/pend/completion/cancel`、Mobile terminal、Config UI、Herdr auto restore disabled、Windows npm install dry-run。
- Module split: platform gate、Herdr spike、backend contract/client、ccbd namespace、provider runtime、recovery、user surfaces、release surface、validation matrix、supportability projection。
- Items: 11 个 item；`herdr-backend-contract-spike` 是唯一 minimal loop；items.yaml 为 DAG，无未知依赖。

## 3. Findings

### blocking

none

### important

- [x] RMR-001 `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-roadmap.md#5` roadmap §5 的人工状态摘要仍写 `planned` / `未启动`，与 items.yaml 中 11 个 `in-progress` feature 指针冲突。
  - Evidence: 独立 reviewer 指出 roadmap §5 与 `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml` 不一致。
  - Impact: 人工 review 可能误判 child design 尚未生成。
  - Fix: 已把 11 个 child 的状态改为 `in-progress`，并填入对应 `2026-07-31-*` feature 目录。

- [x] RMR-002 11 个 child design-review frontmatter 已是 `changes-requested`，但正文 verdict/gate effect 仍可读成当前 `passed`。
  - Evidence: 独立 reviewer 指出多个 `*-design-review.md` 的 `Status: passed` / gate effect 文案残留。
  - Impact: 人工读者可能误把旧 review 当作当前可批准依据。
  - Fix: 已把 11 个 child design-review 正文 gate effect / verdict 改为 superseded / changes-requested；frontmatter 保持 `changes-requested`。

### nit

- [x] RMR-003 旧 roadmap review findings 段会与当前 `changes-requested` 混淆。
  - Fix: 已用本轮 review 报告替换旧报告，仅保留当前审查结论。

### suggestion

- [x] RMR-004 roadmap §4.7 应明确 `public_providers` 的来源。
  - Fix: 已补充 `public_providers` 必须来自当前公开 provider catalog，或 acceptance 冻结清单；新增公开 provider 后必须进入 provider workflow rows。

## 4. User Review Focus

- 用户需要重点拍板：是否接受 strict `v8.5.2` 源头新分支、Native Windows 直路由 Herdr、all-provider、Mobile/Config、auto-restore disabled 和 npm install dry-run 作为 supported 硬门槛。
- 后续 feature-design 需要重点复核：11 个 child design-review 已被 requirement update 取代，必须重新审查后才能进入 all-feature-designs 统一确认。
- 不能靠 roadmap review 完全确认的点：Herdr socket API/schema、Herdr auto restore 是否可关闭、所有公开 provider 凭证/CLI 可用性、专用 Windows x64 真机 transcript。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Granularity Gate | pass | E | roadmap §2 明确跨平台、backend、provider、UI、release/support 多模块 | none |
| Goal Coverage Matrix | pass | E | roadmap Goal Coverage Matrix 覆盖 strict v8.5.2、Herdr、all-provider、Mobile/Config、recovery、npm dry-run、supportability | child design-review 复核 |
| DAG and minimal loop | pass | E | items.yaml 11 个 item，无未知依赖；`herdr-backend-contract-spike` 唯一 minimal loop | none |
| Interface contract usability | pass | E | roadmap §4 写到 TypedDict / Literal / failure reason / hard gate 级别 | child design-review 复核 |
| Module interface depth | pass | E | backend selection、Mux V2、Herdr client、provider runtime、recovery、workflow evidence 均有 owner/seam 说明 | none |

Summary: E=5, C=0, H=0, H-only core checks=none。

## 6. Residual Risk

- Herdr socket API/schema 尚未锁定；roadmap 已用 spike 和 schema gate 管控，但实现前仍是外部事实风险。
- 当前工作区不是 strict `v8.5.2` 实现基线；实现前必须从 CCB 源头拉取 `v8.5.2` 并新建分支。
- all-provider 真机 transcript 依赖 Windows x64 主机、Herdr 和各 provider 凭证；缺任一项只能 blocked，不能 supported。

## 7. Verdict

- Status: passed
- Next: 进入 child design-review 重审；全部通过后再请求 all-feature-designs 统一确认。
