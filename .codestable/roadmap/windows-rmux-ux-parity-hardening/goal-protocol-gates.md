# Goal Gate Policy

## 1. 通用 Gate Result

每个 gate 输出必须包含 gate id、feature identity、canonical inputs、input digests、stage、kind、status、blocking、warnings、evidence 和 providers。`protocol-only` gate 不是可直接调用脚本，机器 runner 不得把它当缺失脚本。

## 2. feature_design.before_approve

必须有：

- design-review passed
- checklist YAML 可解析
- Acceptance Coverage Matrix
- DoD Contract

goal 模式不接管未 approved design。

## 3. implementation.before_review

必须运行：

- scope-gate
- dod-runner
- evidence-pack

检查：

- checklist steps 全部 `done`。
- 当前 diff 没有未解释的范围外文件。
- 清洁度通过。
- checklist `dod.commands` 的 core 命令有执行证据。
- evidence pack 已生成并包含 Scope、DoD Results、Validation Commands、Scope And Cleanliness、Residual Risks。

## 4. review.before_pass

必须运行 review evidence gate。

- review 基于当前 diff。
- review `status=passed`。
- review 必须由独立 Task agent reviewer 完成，除非已有 owner 明确批准 local-only fallback。
- 无 unresolved blocking。
- review 明确消费 evidence pack 和 gate results。

## 5. qa.before_acceptance

必须运行 QA evidence gate。

- QA `status=passed`。
- QA matrix 覆盖 design 关键场景、DoD commands、review QA focus、evidence pack residual risks。
- 功能性核心路径有实际运行证据。
- 非功能性 feature 有替代证据理由。
- QA 不得把核心缺口写成 residual-risk。

## 6. acceptance.before_done

必须运行 acceptance DoD gate。

- acceptance `status=passed`。
- checklist checks 全 `passed`。
- blocking DoD 均有 pass evidence。
- roadmap item 已回写。
- residual risk 不包含核心验收缺口。

## 7. roadmap_audit.before_complete

必须运行：

```bash
python3 C:/Users/Administrator/.codex/plugins/cache/codestable/codestable/1.0.4/skills/cs-onboard/tools/codestable-goal-consistency-gate.py --roadmap .codestable/roadmap/windows-rmux-ux-parity-hardening
```

检查：

- goal-state 全部 features 为 `accepted`。
- approval-report 对 `goal-acceptance`、`goal-commits` 的授权均为 approved。
- items.yaml 条目均为 `done` 或带理由 `dropped`。
- 每个 feature 的 design、checklist、review、QA、acceptance、evidence pack、gate results 存在且 identity 匹配。
- checklist steps 全 `done`，checks 全 `passed`。
- final aggregate commands 已重跑或有非核心 trust-prior 理由。
- provider warnings 已解释。
- `goal-audit.md` 已落盘且 `status=passed`。

## 8. Provider Policy

- provider unavailable 不阻塞基础流程。
- provider warning 必须被 review / QA / audit 解释。
- 未解释的核心风险可阻塞。
- meta-cc 首批只读取已有摘要文件或记录 unavailable。
