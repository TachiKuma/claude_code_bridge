---
doc_type: feature-design-review
feature: 2026-07-27-sidebar-settings-rmux-mouse-routing
status: passed
review_state: passed
review_reason: ""
reviewer_id: "019fa43e-d621-7cf2-8238-f8ae64df1bf6"
reviewed: 2026-07-27
round: 2
---

# sidebar-settings-rmux-mouse-routing feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-27-sidebar-settings-rmux-mouse-routing/sidebar-settings-rmux-mouse-routing-design.md`
- Checklist: `.codestable/features/2026-07-27-sidebar-settings-rmux-mouse-routing/sidebar-settings-rmux-mouse-routing-checklist.yaml`
- Brainstorm: `.codestable/features/2026-07-27-sidebar-settings-rmux-mouse-routing/sidebar-settings-rmux-mouse-routing-brainstorm.md`
- Roadmap: `.codestable/roadmap/windows-rmux-ux-parity-hardening/windows-rmux-ux-parity-hardening-roadmap.md`
- Items: `.codestable/roadmap/windows-rmux-ux-parity-hardening/windows-rmux-ux-parity-hardening-items.yaml`
- Parent evidence: `.codestable/features/2026-07-27-sidebar-settings-click-e2e/evidence/manual-foreground-retest.md`、`.codestable/features/2026-07-27-sidebar-settings-click-e2e/evidence/windows-rmux-ux-parity-evidence.json`
- Code facts checked: `lib/cli/services/tmux_ui_runtime/service.py`、`test/test_v2_tmux_ui.py`、`tools/ccb-agent-sidebar/src/tui.rs`、`tools/ccb-agent-sidebar/src/mouse_probe.rs`

### Independent Review

- Status: completed
- Detection: independent-agent
- Round 1 reviewer: `019fa438-3ecd-7600-abc4-d5fe7bbd1206`
- Round 1 result: changes-requested，1 blocking + 2 important + 1 nit。
- Round 2 reviewer: `019fa43e-d621-7cf2-8238-f8ae64df1bf6`
- Round 2 result: passed，无 blocking / important。
- Merge policy: 两轮 finding 已逐条本地核验；第一轮 blocking/important 已通过 design/checklist 修订关闭，nit 已通过 brainstorm 补充关闭。
- Gate effect: passed；返回 `cs-epic` child batch，design 保持 draft，等待 epic 统一确认。

## 2. Design Summary

- Goal: 在不影响 `x` KillProject、普通 sidebar click、普通 pane drag/right/wheel 的前提下，寻找 Windows/rmux settings-only 鼠标通道；不可实现时投影 `unsupported_capability`。
- Key contracts: route 只能三选一：`rmux_precise_route`、`wezterm_precise_route`、`unsupported_capability`。
- Important correction: `rmux_precise_route` 不再要求 `send-keys -M` 透传；只要有坐标或等价 settings-only 条件，精确命中后发送 `c` 是合法 route。
- Steps: 6 步，按 rmux audit → WezTerm audit → route 选择 → 接入/投影 → 前台反向验收 → schema/清洁度推进。
- Checks: 7 条，覆盖 capability evidence、settings-only 反向验证、unsupported projection 和清洁度。
- Baseline / validation: 复用父 feature foreground retest、UX JSON、Rust probe、禁止 broad fallback 测试；新增 child UX JSON validator。

## 3. Findings

### blocking

none

### important

none

### nit

none

### suggestion

- [ ] FDR-004 `sidebar-settings-rmux-mouse-routing-checklist.yaml` 实现阶段可进一步让 `CMD-005` 断言 `details.sidebar_settings_routing.selected_route` 属于 `rmux_precise_route | wezterm_precise_route | unsupported_capability`。
  - Evidence: design 要求在 `details.sidebar_settings_routing` 摘要最终结论；当前 validator 已覆盖 roadmap 顶层 schema。
  - Impact: 非阻塞；只是把 feature-specific route 错误从人工 evidence review 前移到命令校验。

### learning

- 当前代码事实支持“精确坐标命中后发送 `c`”作为 settings-only route：tmux 路径已有 settings action，settings/x 精确条件依赖 `mouse_x/mouse_y`；Windows/rmux fallback 当前只做 sidebar 二分并透传 `-M`。
- `send-keys -M` 是否透传应作为 ordinary sidebar mouse passthrough 能力记录，不应阻塞 settings-only 坐标 route。

### praise

- design/brainstorm/items 均明确拒绝 broad sidebar-left-click fallback，直接回应 owner 决策。
- 反向验收覆盖 `x`、普通 sidebar 和普通 pane drag/right/wheel，能防止 settings-only route 漂移成全 sidebar fallback。

## 4. User Review Focus

- 用户需要重点拍板：若 rmux/WezTerm 均无精确 settings-only 通道，是否接受 `blocked/unsupported_capability` 作为本 feature 终态。
- implement 需要重点遵守：不能恢复 broad fallback；`send-keys -M` 不透传不能单独否决坐标精确 route；pass 必须来自真实前台 settings-only 点击。
- code review / QA / acceptance 需要重点复核：capability evidence 是否可复现、UX JSON 是否可被 supportability 消费、`x` 与普通 sidebar 是否未被 settings 覆盖。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | design §3 覆盖 AC-001..AC-007，并映射 S1..S6 | none |
| DoD Contract | pass | E | design DoD + checklist `dod.commands` 含 YAML、pytest、cargo、UX JSON validator | none |
| Steps and checks traceability | pass | E | checklist steps/checks 均指向 design §3 | none |
| Roadmap contract compliance | pass | E/C | design frontmatter 绑定 roadmap item；brainstorm confirmed；baseline reuse/delta 已补齐 | none |
| Module interface design | pass | C | 只在 capability 成立时接入 runtime binding；无新增 production schema module | 实现阶段复核 helper 是否保持窄职责 |
| Validation and artifacts | pass | E | checklist S1/S2/S5/S6 明确 evidence artifact，CMD-005 校验 UX JSON | 可选增强 selected_route validator |

Summary: E=5, C=1, H=0, H-only core checks=none。

## 6. Residual Risk

- 真实 Windows + WezTerm + rmux 前台行为仍必须由 owner 环境验证；implementation/code review 只能证明绑定、evidence schema 和防退化测试，不能替代最终前台 transcript。

## 7. Verdict

- Status: passed
- Next: 返回 `cs-epic` child batch；当前 design 保持 `draft`，不在单 feature 阶段标 `approved`。

## 8. Focused Closure

- Closed findings: Round 1 `FDR-001`、`FDR-002`、`FDR-003`、nit。
- Attributed delta: design route contract、baseline reuse/delta、UX JSON validator；checklist S1/CMD-005/S6 deliverables；brainstorm baseline reuse/delta。
- Verification: roadmap items YAML passed；feature checklist YAML passed；第二轮 independent reviewer passed。
- Classification: 修订改变了 route 契约，已做完整第二轮独立复审；brainstorm nit 只补已在 design 中存在的 baseline reuse/delta，不改变行为、公开契约或验收语义。
