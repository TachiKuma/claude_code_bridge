---
doc_type: feature-review
feature: 2026-07-27-sidebar-settings-rmux-mouse-routing
status: passed
reviewer: subagent
reviewed: 2026-07-27
round: 1
lane_a_state: completed
lane_a_ref: "019fa455-e630-7710-8b31-74f8933c69d9"
lane_a_reason: "independent reviewer completed initial review and focused closure"
lane_b_state: skipped
lane_b_ref: ""
lane_b_reason: "ocr available, but current scoped diff is CodeStable evidence/spec only and workspace has unrelated dirty files; protocol excludes .codestable from OCR line findings"
---

# sidebar-settings-rmux-mouse-routing 代码审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-27-sidebar-settings-rmux-mouse-routing/sidebar-settings-rmux-mouse-routing-design.md`
- Checklist: `.codestable/features/2026-07-27-sidebar-settings-rmux-mouse-routing/sidebar-settings-rmux-mouse-routing-checklist.yaml`
- Evidence pack:
  - `evidence/rmux-mouse-capability.md`
  - `evidence/wezterm-settings-only-channel.md`
  - `evidence/capability-summary.json`
  - `evidence/windows-rmux-ux-parity-evidence.json`
  - `evidence/foreground-reverse-validation.md`
  - `evidence/validation-summary.md`
- Parent evidence:
  - `.codestable/features/2026-07-27-sidebar-settings-click-e2e/evidence/manual-foreground-retest.md`
  - `.codestable/features/2026-07-27-sidebar-settings-click-e2e/evidence/sidebar-mouse-probe.json`
- Implementation evidence: checklist S1-S6 `done`，本轮仅写 capability / UX evidence，无 runtime code change。
- Diff basis: 当前 feature 目录为 untracked；另有大量 unrelated dirty runtime/test/docs 文件，不计入本轮归因。
- Review mode: initial + focused-closure
- Baseline dirty files: 存在，均按 unrelated baseline 处理。

### Independent Review

- Detection: subagent 可用；OCR CLI 可用且 `ocr llm test` passed。
- 环节 A 独立隔离 Task agent: independent-agent completed，ref `019fa455-e630-7710-8b31-74f8933c69d9`。
- 环节 B OCR CLI: skipped。原因：当前可归因范围是 `.codestable` evidence/spec；协议要求丢弃 `.codestable` OCR findings，且 workspace 有无关 dirty 文件，不能裸跑 workspace OCR。
- OCR severity mapping: High -> blocking/important, Medium -> nit/suggestion, Low -> discarded。
- Merge policy: 独立 reviewer 初审逐条本地核验；blocking/important 经 evidence-only 修复后由同一 reviewer focused closure，结论 passed。
- Gate effect: `subagent` reviewer gate satisfied。

## 2. Diff Summary

- 新增：
  - `.codestable/features/2026-07-27-sidebar-settings-rmux-mouse-routing/evidence/rmux-mouse-capability.md`
  - `.codestable/features/2026-07-27-sidebar-settings-rmux-mouse-routing/evidence/wezterm-settings-only-channel.md`
  - `.codestable/features/2026-07-27-sidebar-settings-rmux-mouse-routing/evidence/capability-summary.json`
  - `.codestable/features/2026-07-27-sidebar-settings-rmux-mouse-routing/evidence/windows-rmux-ux-parity-evidence.json`
  - `.codestable/features/2026-07-27-sidebar-settings-rmux-mouse-routing/evidence/foreground-reverse-validation.md`
  - `.codestable/features/2026-07-27-sidebar-settings-rmux-mouse-routing/evidence/validation-summary.md`
  - `.codestable/features/2026-07-27-sidebar-settings-rmux-mouse-routing/sidebar-settings-rmux-mouse-routing-review.md`
- 修改：
  - `.codestable/features/2026-07-27-sidebar-settings-rmux-mouse-routing/sidebar-settings-rmux-mouse-routing-checklist.yaml`
  - `.codestable/features/2026-07-27-sidebar-settings-click-e2e/evidence/manual-foreground-retest.md`
- 删除：none
- 未跟踪 / staged：当前 feature 目录整体 untracked；未 staged。
- 风险热点：evidence/schema correctness；无 runtime code、权限、数据、并发或 API 改动。

## 3. Adversarial Pass

- 假设的生产 bug：evidence-only feature 把 blocked 伪装成 pass，或通过 broad fallback 改变 sidebar / ordinary pane 行为。
- 主动攻击过的反例：
  - parent manual 与 persisted probe 是否自相矛盾。
  - S5 是否虚假宣称 x、普通 sidebar、普通 pane 已重新前台实测。
  - UX JSON 是否只接受任意合法 route，而不是锁定本轮 `unsupported_capability`。
  - 是否新增 `send-keys -t = c` broad fallback、token 泄露或默认 debug 输出。
- 结果：初审 1 个 blocking + 2 个 important 已通过 focused closure 关闭；无新阻塞项。

## 4. Findings

### blocking

none

### important

none

### nit

none

### suggestion

- SUG-001 后续 acceptance 可保持 `checks` pending 到验收阶段裁决，不建议 implementation 直接裁决 AC 状态。focused closure 已确认这不再与 S5 实现声明冲突。

### learning

- `unsupported_capability` 路径下，direct `c` 只能作为 settings action 健康诊断，不能作为 mouse click parity。
- rmux 0.9.0 可以在内部携带 mouse target/event，但普通 root binding 没有 settings hit-test 所需坐标或等价格式字段。

### praise

- 本轮没有引入 runtime fallback；UX JSON 明确 `runtime_behavior_changed=false`、`broad_fallback_added=false`。
- validator 已从 route enum 校验升级为精确锁定 `blocked/unsupported_capability`。

## 5. Test And QA Focus

- QA 必须重点复核：没有 runtime code change；没有 `send-keys -t = c` broad fallback；direct `c` 不被算作 mouse pass。
- Evidence pack residual risks / gate warnings：真实 settings click parity 仍是 `blocked/unsupported_capability`，不是 pass。
- 建议新增或加强的测试：none for this evidence-only route；后续若实现 rmux/WezTerm precise route，需要新增 x/ordinary sidebar 反向测试。
- 不能靠 review 完全确认的点：未来 rmux/WezTerm 版本是否新增坐标能力，需要独立 capability probe 更新。

## 6. Residual Risk

- 当前 feature 目录和父 evidence 仍是 untracked，最终合入时要防止和 unrelated runtime dirty 文件混在同一验收边界。
- `checks` 仍由后续 QA/acceptance 裁决；本 review 只确认 implementation evidence 与 selected route 自洽。

## 7. Verdict

- Status: passed
- Next: Goal lane feature 按 CodeStable 进入 QA / acceptance 衔接；当前产物可交回 epic owner 做后续统一 gate。

## 8. Focused Closure

- Closed findings:
  - REV-001 父 manual 与 `sidebar-mouse-probe.json` direct-c 状态矛盾。
  - REV-002 S5 过度宣称完整前台反向验收。
  - REV-003 validation-summary validator 不够精确。
- Attributed delta:
  - `.codestable/features/2026-07-27-sidebar-settings-click-e2e/evidence/manual-foreground-retest.md`
  - `.codestable/features/2026-07-27-sidebar-settings-rmux-mouse-routing/sidebar-settings-rmux-mouse-routing-checklist.yaml`
  - `.codestable/features/2026-07-27-sidebar-settings-rmux-mouse-routing/evidence/foreground-reverse-validation.md`
  - `.codestable/features/2026-07-27-sidebar-settings-rmux-mouse-routing/evidence/validation-summary.md`
- Targeted verification:
  - checklist YAML validator: passed
  - precise UX JSON validator: passed
  - scoped rg for old issue patterns: no matches
  - independent focused closure: passed
- Classification: evidence/docs/checklist wording only；未改变 runtime 行为、公开契约、安全、数据、并发或架构。
