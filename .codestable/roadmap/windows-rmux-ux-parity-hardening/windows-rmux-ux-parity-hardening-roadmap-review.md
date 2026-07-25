---
doc_type: roadmap-review
roadmap: windows-rmux-ux-parity-hardening
status: passed
review_state: passed
review_reason: ""
reviewer_id: "019f9740-3115-7543-8f4b-68bbb2bf1b5b"
reviewed: 2026-07-25
round: 2
---

# windows-rmux-ux-parity-hardening roadmap 审查报告

## 1. Scope And Inputs

- Roadmap: `.codestable/roadmap/windows-rmux-ux-parity-hardening/windows-rmux-ux-parity-hardening-roadmap.md`
- Items: `.codestable/roadmap/windows-rmux-ux-parity-hardening/windows-rmux-ux-parity-hardening-items.yaml`
- Related docs:
  - `.codestable/attention.md`
  - `.codestable/brainstorms/windows-rmux-ux-parity-hardening/brainstorm.md`
  - `.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-roadmap.md`
  - `.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml`
  - `.codestable/roadmap/windows-rmux-native-backend/goal-state.yaml`
  - `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/*`
  - `.codestable/features/2026-07-20-rmux-send-capture-logging/rmux-send-capture-logging-acceptance.md`
  - `.codestable/features/2026-07-20-rmux-windows-validation-matrix/rmux-windows-validation-matrix-acceptance.md`
  - `.codestable/features/2026-07-20-rmux-packaging-docs-contracts/rmux-packaging-docs-contracts-design-review.md`
- Requirement docs: none (`related_requirements: []`)
- Compound / drafts: none found for this roadmap directory / compound search
- Code facts checked:
  - `lib/cli/services/tmux_ui_runtime/service.py`
  - `lib/terminal_runtime/rmux_backend_runtime/targets.py`
  - `lib/terminal_runtime/rmux_backend_runtime/panes.py`
  - `lib/terminal_runtime/rmux_backend_runtime/io.py`
  - `tools/ccb-agent-sidebar/src/tui.rs`

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: `019f9740-3115-7543-8f4b-68bbb2bf1b5b`
- Raw output: 首轮 `changes-requested`，无 blocking，提出 4 条 important；主 agent 修订 roadmap/items 后 focused closure verdict 为 `passed`，剩余 blocking / important / nit / suggestion 均为 none。
- Merge policy: 已逐条本地核验 reviewer findings；修订点均能在 roadmap/items 或相关 accepted evidence 中定位。
- Gate effect: none

## 2. Roadmap Summary

- Goal completion signal: native Windows + WezTerm + rmux 从“全链路可跑”升级为可证伪的日用 UX parity：前台交互、输出/capture、pane identity/layout、视觉无弹窗、生命周期恢复、doctor/install/supportability 都有证据。
- Module split: 6 个模块分别对应 Foreground Interaction、Output And Capture、Pane Identity And Layout、Visual No-Popup Surface、Lifecycle And Recovery UX、Supportability Contract。
- Interface contracts: 定义 UX parity JSON evidence、foreground interaction policy、capture case、pane identity snapshot、visual command policy、lifecycle report、support projection。
- Items: 6 条；`windows-rmux-wezterm-native-interaction-parity` 是唯一 minimal loop，已先行 feature design；其余 5 条 planned。
- Dependency shape: DAG，无未知依赖、无自依赖、无环。

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

- 该 roadmap 与 `windows-rmux-native-backend` 的关系合理：旧 roadmap 证明 native backend/control-plane 基线，新 roadmap 聚焦用户可见 UX parity delta。
- GUI 行为不能只靠 binding 字符串证明；unit、live binding snapshot、native Windows + WezTerm 手工 runbook 三层证据需要同时存在或明确 blocked/partial。
- support tier 应由单一 base projection owner 和 UX overlay evidence 共同推导，不能由 README、installer、doctor 各自发明状态。

### praise

- 范围边界克制：不恢复旧 WezTerm backend，不改 Linux/macOS 默认，不把 provider auth/quota 误归为 Windows/rmux parity failure。
- DAG 简单，最小闭环清楚，先处理普通 pane GUI-native + sidebar 全接管能最快给用户可感知价值。
- 修订后 baseline reuse / delta 规则清楚，能降低后续 child feature 重做已验收 backend 基础工作的风险。

## 4. User Review Focus

- 用户需要重点拍板：是否确认 Windows/rmux/WezTerm 普通 pane 采用 GUI-native parity，而不是 tmux-like mouse parity。
- 用户需要重点拍板：是否接受 `evidence/windows-rmux-ux-parity-evidence.json` 作为 6 个子 feature 的共同 UX parity 证据协议。
- 用户需要重点拍板：是否接受 `rmux-packaging-docs-contracts` 继续作为 base support projection / npm / `install.ps1` / release guard 单一 owner，本 roadmap 只做 UX parity overlay。
- 后续 feature-design 需要重点复核：每个 child 都必须写 baseline reuse / delta 小节，并把旧 accepted evidence 与本 item 增量分开。
- 不能靠 roadmap review 完全确认的点：真实 native Windows + WezTerm 前台体验、rmux live 环境、真实 provider auth/quota 外部条件。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Granularity Gate | pass | E | roadmap §2 说明 6 个维度横跨交互、capture、identity、visual、lifecycle、supportability，不能塞进 single feature | none |
| Goal Coverage Matrix | pass | E | roadmap §5 覆盖 6 个核心 completion signals、item、验证入口和 evidence type | child design 落地时复核 |
| DAG and minimal loop | pass | E | items.yaml 6 条，无未知依赖；唯一 `minimal_loop=true` 是 interaction item | none |
| Interface contract usability | pass | E | roadmap §4 定义 evidence JSON、policy、capture、identity、visual、lifecycle、support projection 契约 | child checklist 必须加 JSON 校验 |
| Module interface depth | pass | C | 代码事实支持 mouse/status、rmux capture、pane canonicalization、sidebar KillProject 等 owner 落点 | feature design 时按各模块细化 |
| Baseline reuse / delta | pass | C | roadmap §4 / §5 / §7 已引用旧 accepted evidence，并限制本 roadmap 只补 UX parity delta | child design 必须继承 |
| Supportability owner boundary | pass | C | roadmap §2 / §4.7 / §5 明确消费 `rmux-packaging-docs-contracts`，不重复定义 npm/install/release gate | supportability item 实现时 fail-closed |

Summary: E=4, C=3, H=0, H-only core checks=none。

## 6. Residual Risk

- 每个 child design/checklist 仍需要实际落地 JSON evidence 校验命令和 baseline/delta 小节；roadmap 只能建立约束，不能替代后续执行。
- `rmux-packaging-docs-contracts` 当前仍是外部 base support owner；UX supportability 实现时必须继续 fail-closed 消费其最终 projection。
- 真实 native Windows + WezTerm 前台证据是 UX parity 核心弱依赖；skip 或缺 live/manual evidence 不能计 full pass。

## 7. Verdict

- Status: passed
- Next: 交给用户 review。用户确认后，才能把 roadmap `status` 改为 `active`，并在进入实现前补齐先行 interaction feature 的 `roadmap` / `roadmap_item` frontmatter。
