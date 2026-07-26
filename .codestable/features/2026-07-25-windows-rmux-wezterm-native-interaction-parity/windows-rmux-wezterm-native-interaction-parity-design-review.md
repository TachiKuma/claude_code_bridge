---
doc_type: feature-design-review
feature: 2026-07-25-windows-rmux-wezterm-native-interaction-parity
status: passed
review_state: passed
review_reason: ""
reviewer_id: "019f96f8-30c4-7f23-999a-f412735f503d"
reviewed: 2026-07-27
round: 3
---

# windows-rmux-wezterm-native-interaction-parity feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-design.md`
- Checklist: `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-checklist.yaml`
- Intent / brainstorm: `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-brainstorm.md`
- Roadmap: none
- Related docs: `.codestable/brainstorms/windows-rmux-ux-parity-hardening/brainstorm.md`
- Code facts checked: `lib/cli/services/tmux_ui_runtime/service.py`, `test/test_v2_tmux_ui.py`, `tools/ccb-agent-sidebar/src/tui.rs`

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: `019f96f8-30c4-7f23-999a-f412735f503d`
- Raw output: 第二轮复审结论为无 blocking / important；上一轮 FDR-001~004 均已关闭；剩余 nit 已由主 agent focused closure 修正 checklist S3 文案。
- Merge policy: 已逐条核验并合并；未直接照抄未经核验结论。
- Gate effect: none

## 2. Design Summary

- Goal: Windows/rmux/WezTerm 前台交互选择 GUI-native parity，普通 pane 透明化，sidebar 专属接管。
- Key contracts: 普通 pane 不被 copy-mode、paste-buffer 或普通左键 mouse passthrough 劫持；sidebar 保留 mouse/header/KillProject 行为；不新增交互模式配置。
- Steps: 5 步，风险热点是 live rmux snapshot 与真实 WezTerm GUI 手工验收。
- Checks: 10 条，已追踪到 design §1、AC IDs 和 checklist steps。
- Baseline / validation: checklist YAML 已通过；后续实现需跑 `test/test_v2_tmux_ui.py`、sidebar cargo tests、py_compile、rmux live binding snapshot 和手工 WezTerm runbook。

## 3. Findings

### blocking

none

### important

none

### nit

none

### suggestion

- [ ] FDR-005 `design §3.4 / manual runbook artifacts` QA 阶段可把 manual runbook 固定为最小字段：OS、WezTerm 版本、rmux 可用性、实际操作结果、残留限制分类。
  - Evidence: design 已要求 `manual-wezterm-runbook.md` 或 QA 同名小节，但未规定字段 schema。
  - Impact: 不影响 design 可执行性；结构化字段能提高 acceptance 复核效率。

### learning

- unit、live binding snapshot、manual WezTerm runbook 分层是合理的：unit 证明 binding 生成，live 证明 rmux 接受，manual 才能证明 GUI-native 体验。
- output/capture parity 被留到后续 brainstorm，避免把 provider completion capture 与前台滚轮混成一个 feature。

### praise

- design 明确记录当前代码和测试仍按旧语义断言普通 pane wheel copy-mode，避免把待实现状态误写成已完成事实。
- seam 保持在既有 `_apply_sidebar_mouse_controls()` / fallback 分支内，没有为一次 binding 收紧引入新 adapter，符合 KISS / YAGNI。

## 4. User Review Focus

- 用户需要重点拍板：是否确认 Windows/rmux 前台交互采用 GUI-native parity，而不是 tmux-like mouse parity。
- implement 需要重点遵守：普通 pane 不进入 copy-mode、不走 paste-buffer、不裸透传普通左键；sidebar 全接管且 `x` 保持 KillProject。
- code review / QA / acceptance 需要重点复核：live binding snapshot 不能替代真实 WezTerm 手工记录；skipped live test 不能计 full pass。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | design §3.3 覆盖 AC-001~AC-007，每个核心场景有 step 与证据类型 | none |
| DoD Contract | pass | E | design §3.4 与 checklist `dod.commands` 均列出核心命令和 artifact | none |
| Steps and checks traceability | pass | E | checklist checks source 已追踪到 `design §1`、AC、S step | none |
| Roadmap contract compliance | n/a | E | 本 feature 非 roadmap 起头；相关二期维度记录在 brainstorm | none |
| Module interface design | pass | C | design §2.1 说明 seam 在 existing UI binding owner；代码事实位于 `service.py` | none |
| Validation and artifacts | pass | E | design §2.4 / §3.4 指定 live snapshot、manual runbook、skip/blocked/partial 归因 | QA 阶段重点执行 |

Summary: E=5, C=1, H=0, H-only core checks=none。

## 6. Residual Risk

- GUI-native 行为最终仍依赖真实 Windows + WezTerm + rmux 前台手工证据；live snapshot 只能证明 root binding 字符串，不足以证明拖选、右键粘贴和滚轮体验完全符合预期。QA / acceptance 必须按 DOD-QA-001 / DOD-ACCEPT-001 卡住 full pass。

## 7. Verdict

- Status: passed
- Next: 交给用户整体 review；用户确认 design 后才能把 `status` 改为 `approved` 并进入实现阶段。

## 8. Focused Closure

- Closed findings: first-round FDR-001, FDR-002, FDR-003, FDR-004, markdown table nit, second-round S3 wording nit
- Attributed delta: design/checklist 仅补强左键 focus 追踪、测试断言反转边界、live/manual artifact 路径、skip/blocked/partial 归因、check source 和表格列数；second-round 后只收紧 checklist S3 文案。
- Verification: `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-checklist.yaml" --yaml-only` 通过。
- Classification: 修订没有改变用户目标、公开 UX 决策、架构边界或 feature 范围；只是把验证语义和证据路径写得可执行。

## Round 3 (2026-07-27 实测更正复审)

审查范围：仅 design.md + checklist.yaml，采信事实基准（rmux 0.9.0 实测支持 `if-shell`/`select-pane`/`-t =`/格式算术；根因＝fallback 误用无 `-t` 的 `select-pane -M` ＋ sidebar `if-shell` 漏 `-t`）。逐条结论如下：

1. 一致性（design 各节 ↔ checklist）—— minor：全文无残留旧方案矛盾文字，未出现「保留 select-pane -M focus」类表述；§2.1/§2.2 现状节把 `select-pane -M` 与漏 `-t` 的 `if-shell` 明确标为缺陷，变化节统一改 `-t =` / 透传，口径自洽；成功标准 / §2.4 / AC-003/004/008 / DoD-IMPL-001/002 / checklist steps 1-2 与 checks 均一致。AC-001..008 各有对应 check，映射完整。
2. 方案-实测一致 —— minor：§2.1 已用「2026-07-27 实测更正」显式记录 rmux 支持能力，并解释 `#{mouse_pane}` 不作 `-t` 自动解析→走 fallback 合理、但 fallback 应改 `-t =`；无遗留「rmux 不支持 if-shell/select-pane」错误表述，修法与事实基准逐条吻合。
3. 残留分类自洽 —— minor：3（右键粘贴）/4（滚轮）＝GUI-native 预期残留、2（选区起点行 off-by-one）＝rmux daemon 内部坐标映射（rmux 外部二进制），与关键决策①一致且明确「不计 AC 失败」（AC-007）；1/5/6 明确归为 fallback bug 必修，风险节 1 特别与「capture 限制」区分。
4. 范围守护 —— minor：scope guard 限定 Windows + `backend_impl=rmux` fallback；§3.2 反向核对与「明确不做」覆盖不加模式开关、不碰 provider capture/completion、不改 install/support tier、不改 KillProject、不动 Rust TUI（除回退）；AC-006/DoD-IMPL-003 守住 tmux 回归。未越界。
5. 盲区闭合（核心）—— minor：AC-008 ＋测试更新要求明确断言「绑定内容正确」（普通 pane 左键＝`select-pane -t =` 非 `-M`；sidebar header＝无条件 `send-keys -t = -M` 透传、不含漏 `-t` 的 `if-shell`），显式覆盖旧用例「只验 `list-keys` 含绑定串」盲区，并以 Rust `header_action_at`（⚙ `pane_width-4`/x `pane_width-2`）命中单测作行为证据。派发盲区已闭合。

结论：blocking＝0；设计与实测事实、关键决策、残留分类、范围守护、派发盲区全部自洽，测试要求已从「注册断言」升级为「内容/派发断言」。review_state: **passed**。
