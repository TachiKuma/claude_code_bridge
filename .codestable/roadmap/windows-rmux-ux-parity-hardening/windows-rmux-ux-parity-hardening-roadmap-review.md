---
doc_type: roadmap-review
roadmap: windows-rmux-ux-parity-hardening
status: passed
review_state: passed
review_reason: ""
reviewer_id: "019f97ff-95e7-7dd3-8195-f69265eec8b6"
reviewed: 2026-07-25
round: 4
---

# windows-rmux-ux-parity-hardening roadmap 审查报告

## 1. Scope And Inputs

- Roadmap: `.codestable/roadmap/windows-rmux-ux-parity-hardening/windows-rmux-ux-parity-hardening-roadmap.md`
- Items: `.codestable/roadmap/windows-rmux-ux-parity-hardening/windows-rmux-ux-parity-hardening-items.yaml`
- Related docs:
  - `.codestable/attention.md`
  - `.codestable/brainstorms/windows-rmux-ux-parity-hardening/brainstorm.md`
  - `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-brainstorm.md`
  - `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-design.md`
  - `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-design-review.md`
  - `.codestable/reference/shared-conventions.md`
  - `.codestable/reference/approval-conventions.md`
  - `.codestable/roadmap/windows-rmux-ux-parity-hardening/approval-report.md`
  - `C:/Users/Administrator/.agents/skills/cs-epic/SKILL.md`
  - `C:/Users/Administrator/.agents/skills/cs-epic/references/review/protocol.md`
  - `C:/Users/Administrator/.agents/skills/cs-feat/references/design/protocol.md`
  - `C:/Users/Administrator/.agents/skills/cs-onboard/tools/codestable-workflow-next.py`
- Requirement docs: none (`related_requirements: []`)
- Code facts checked: CodeStable workflow tooling only；本轮 focused review 只审 design admission gate。

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: `019f97ff-95e7-7dd3-8195-f69265eec8b6`
- Raw output: focused closure verdict 为 `passed`，blocking / important / nit 均为 none。reviewer 确认 `workflow-next epic` 与 `workflow-next feature --epic-child-batch` 三条路径均已先执行 per-item brainstorm admission gate，且规则只在 `brainstorm_required is True` 时启用。
- Merge policy: 主 agent 已本地核验 reviewer 结论，并用临时 fixture 验证 pending admission 会返回 `user_gate -> cs-brainstorm`，confirmed admission 会继续 design/design-review。
- Gate effect: none

## 2. Roadmap Summary

- Goal completion signal: native Windows + WezTerm + rmux 从“全链路可跑”升级为可证伪的日用 UX parity：前台交互、输出/capture、pane identity/layout、视觉无弹窗、生命周期恢复、doctor/install/supportability 都有证据。
- Module split: 6 个模块分别对应 Foreground Interaction、Output And Capture、Pane Identity And Layout、Visual No-Popup Surface、Lifecycle And Recovery UX、Supportability Contract。
- Interface contracts: 定义 UX parity JSON evidence、foreground interaction policy、capture case、pane identity snapshot、visual command policy、lifecycle report、support projection。
- Design admission gate: 每个子 feature 创建或实质更新 design 前，必须先有该 item 自身的 confirmed `$cs-brainstorm` 和 owner 进入 design 批准；该 gate 已被 `workflow-next epic` / `feature --epic-child-batch` 机械执行。
- Items: 6 条；`windows-rmux-wezterm-native-interaction-parity` 是唯一 minimal loop，已有 confirmed feature-brainstorm；其余 5 条 planned 且 `brainstorm_status: pending`，后续会停到 `$cs-brainstorm`。
- Dependency shape: DAG，无未知依赖、无自依赖、无环。

## 3. Findings

### blocking

none

### important

none

### nit

none

### suggestion

- 可以把 `design_admission` 从单字符串演进为对象，例如 `{status, approval_ref, brainstorm_ref}`，提高 workflow-next 的诊断可读性。本轮不强制，因为现有字段已足以表达阻断状态。

### learning

- 文档级 gate 必须落到 workflow-next / stage protocol；否则连续 batch loop 可能绕过人工 notes。
- `$cs-brainstorm` 的“充分深入讨论”质量无法完全机械判断；机械 gate 只判存在性、状态和引用一致性，内容质量留给 design-review 复核。

### praise

- roadmap 明确区分 roadmap 总体 brainstorm 与每个 child 自身的 feature-brainstorm，避免用规划层输入替代 design admission。
- items.yaml 已为 6 个 item 都写入 `brainstorm_required`、`brainstorm`、`brainstorm_status`、`design_admission`，并被工具消费。

## 4. User Review Focus

- 用户需要重点拍板：是否确认 Windows/rmux/WezTerm 普通 pane 采用 GUI-native parity，而不是 tmux-like mouse parity。
- 用户需要重点拍板：是否接受 `evidence/windows-rmux-ux-parity-evidence.json` 作为 6 个子 feature 的共同 UX parity 证据协议。
- 用户需要重点拍板：是否接受 `rmux-packaging-docs-contracts` 继续作为 base support projection / npm / `install.ps1` / release guard 单一 owner，本 roadmap 只做 UX parity overlay。
- 后续 feature-design 需要重点复核：每个 child design 必须引用自身 brainstorm，并记录 owner 已批准/通过进入 design。
- 不能靠 roadmap review 完全确认的点：真实 native Windows + WezTerm 前台体验、rmux live 环境、真实 provider auth/quota 外部条件。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Granularity Gate | pass | E | roadmap §2 说明 6 个维度横跨交互、capture、identity、visual、lifecycle、supportability，不能塞进 single feature | none |
| Goal Coverage Matrix | pass | E | roadmap §5 覆盖 6 个核心 completion signals、item、验证入口和 evidence type | child design 落地时复核 |
| DAG and minimal loop | pass | E | items.yaml 6 条，无未知依赖；唯一 `minimal_loop=true` 是 interaction item | none |
| Brainstorm admission fields | pass | E | items.yaml 6 条均有 `brainstorm_required`、`brainstorm_status`、`design_admission`；roadmap 定义枚举 | none |
| Brainstorm admission enforcement | pass | C | `workflow-next epic` 和 `feature --epic-child-batch` 在 design 缺失、changes-requested、draft design 缺 review 三条路径均先检查 admission；pending 返回 `cs-brainstorm` gate，confirmed 继续 | none |
| Interface contract usability | pass | E | roadmap §4 定义 evidence JSON、policy、capture、identity、visual、lifecycle、support projection 契约 | child checklist 必须加 JSON 校验 |
| Supportability owner boundary | pass | C | roadmap §2 / §4.7 / §5 明确消费 `rmux-packaging-docs-contracts`，不重复定义 npm/install/release gate | supportability item 实现时 fail-closed |

Summary: E=5, C=2, H=0, H-only core checks=none。

## 6. Residual Risk

- 真实 native Windows + WezTerm 前台证据是 UX parity 核心弱依赖；skip 或缺 live/manual evidence 不能计 full pass。
- 先行 interaction design 的 metadata / brainstorm 引用已补齐，但其 design-review 是补齐 traceability 之前通过的；由于本轮没有改变设计契约，只作为 focused closure 记录，进入实现前仍应复核 admission 引用。
- `$cs-brainstorm` 的讨论质量仍需 design-review 人审，不应只依赖机械字段。

## 7. Focused Closure

- RMR-001 fixed：`C:/Users/Administrator/.agents/skills/cs-onboard/tools/codestable-workflow-next.py` 新增 `item_design_admission_blocker()`；`_epic_next()` 在 child design/design-review 前检查 admission；`_feature_next()` 在 design 缺失、design-review changes-requested、draft design 缺 review 三条路径前检查 admission。
- RMR-002 fixed：`.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-design.md` frontmatter 已补 `roadmap`、`roadmap_item`、`brainstorm`，正文新增 Design admission 小节，引用 confirmed feature-brainstorm 并记录 admission evidence。
- RMR-003 fixed：roadmap Design 前置 Brainstorm Gate 已定义 `brainstorm_status: pending|confirmed` 与 `design_admission: blocked_until_owner_brainstorm_approval|admitted`，并说明 admitted 的证据条件与迁移条件。
- RMR-004 fixed：items.yaml 后 5 个 pending item notes 已统一为“创建或实质更新 design 不得启动”。
- Protocol fixed：`cs-epic/SKILL.md` 与 `cs-feat/references/design/protocol.md` 已说明 per-item brainstorm admission gate，且 `epic_child_batch: true` 不得绕过。
- Verification:
  - `python -m py_compile "C:/Users/Administrator/.agents/skills/cs-onboard/tools/codestable-workflow-next.py"` passed。
  - 临时 epic fixture：pending brainstorm admission 返回 `status=user_gate` / `next_action=cs-brainstorm`。
  - 临时 epic fixture：confirmed brainstorm admission 继续 `cs-feat design/design-review`。
  - 临时 feature fixture：pending brainstorm admission + missing design 返回 `cs-brainstorm`。
  - 临时 feature fixture：pending brainstorm admission + draft design missing review 返回 `cs-brainstorm`。
  - 临时 feature fixture：confirmed brainstorm admission + draft design missing review 继续 `cs-feat design-review`。
  - 当前项目 roadmap、items、approval report、先行 design 均通过 `.codestable/tools/validate-yaml.py`。

## 8. Verdict

- Status: passed
- Next: 交给用户 review。用户确认 roadmap 后，才能把 roadmap `status` 改为 `active`；之后 child batch 会在后续 5 个 pending item 上停到 `$cs-brainstorm`，直到 owner 逐项确认进入 design。
