---
doc_type: feature-design-review
feature: 2026-07-06-rmux-capability-gate
status: passed
reviewed: 2026-07-06
round: 3
---

# rmux-capability-gate feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-06-rmux-capability-gate/rmux-capability-gate-design.md`
- Checklist: `.codestable/features/2026-07-06-rmux-capability-gate/rmux-capability-gate-checklist.yaml`
- Intent / brainstorm: none
- Roadmap: `.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-roadmap.md`
- Roadmap items: `.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml`
- Related docs:
  - `.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-roadmap-review.md`
  - `docs/ccbd-windows-psmux-plan.md`
- Code facts checked:
  - `scripts/probe_codex_pane_status.py`
  - `test/test_codex_pane_status_probe.py`
  - `lib/terminal_runtime/backend_selection.py`
  - `lib/terminal_runtime/tmux.py`
  - `lib/terminal_runtime/tmux_backend.py`
  - `lib/terminal_runtime/tmux_send.py`
  - `lib/terminal_runtime/tmux_logs.py`
  - `lib/terminal_runtime/tmux_panes_runtime/queries_runtime/service.py`
  - `lib/provider_pane_status/codex_pane.py`
  - `lib/provider_pane_status/claude_pane.py`
  - `lib/ccbd/project_view/service.py`
  - `lib/ccbd/services/project_namespace_runtime/materialize_topology.py`
  - `lib/ccbd/services/project_namespace_runtime/agent_window_reflow.py`
  - `lib/ccbd/services/project_namespace_runtime/move_patch_agents.py`
  - `lib/ccbd/services/project_namespace_runtime/remove_patch_agents.py`

### Independent Review

- Status: completed
- Detection: native-agent
- Provider / agent:
  - round 1/2: subagent `019f3774-2360-7733-84a4-2575aa1db7cd`
  - round 3: subagent `019f3792-a5c1-7081-b4df-6e46f7886f0c`
- Raw output:
  - round 1 返回 `changes-requested`，包含 Windows evidence failure handling、parser-facing capture contract、workaround schema、artifact_index 结构等问题。
  - round 2 复审返回 `Verdict: passed`。
  - 用户后续独立审核提出 F1/F2/N1/N2/N3：capture fidelity 归一化覆盖被高估、OSC/非 CSI 缺口、缺 degrade impact/consequence、fixture 与真实 Rmux artifacts 不可互替、Codex/Claude 是全部现存 pane-status parser、daemon 预状态缺失。
  - round 3 复审返回 `Verdict: passed`，`blocking: none`、`important: none`；仅有 nit/suggestion，已收进 checklist/design。
- Merge policy: 已逐条核验并修订 design/checklist；所有实质 finding 已转为可执行契约。
- Gate effect: none；独立 review completed 且无未处理 blocking / important。

## 2. Design Summary

- Goal: 建立 Windows Rmux capability gate，产出 capability report、artifact index、blocking gaps、degrade 语境和 Windows 真机 evidence，作为后续 `rmux-route-approval` 的事实输入。
- Key contracts:
  - `CapabilityReport` 必含 `probe_status`、`preflight.daemon_pre_state`、`commands`、`semantics`、`blocking_gaps`、`artifact_index`。
  - `partial` / `workaround` 必须有结构化 `workaround`，blocking gap 推导不读取 `notes`。
  - 每个 command/semantic 和 blocking gap 必须携带 `degrade_impact` / `consequence`，但 probe 不基于它们批准路线。
  - capture fidelity 必须覆盖尾部空白、CSI/OSC/非 CSI 转义、wrapping、宽字符、last-N 截断，并区分 consumer-strip 与 direct-stdout 两类 parser 入口。
- Steps: 7 步，按 schema、command probe、semantic probe、capture fidelity、artifact/report、Windows runbook、验证回归切分。
- Checks: 23 条，覆盖名词契约、编排骨架、流程级约束、范围守护、挂载点和验收场景。
- Baseline / validation: checklist YAML 和 roadmap items YAML 均已通过 `validate-yaml.py`；实现阶段核心命令包括 probe 单测、Windows 真机 probe 和既有 Codex pane probe 回归。

## 3. Findings

### blocking

none

Resolved:

- FDR-001：Windows 真机核心验证命令 `CMD-003` 原为 `document-baseline`，与 DOD-IMPL-002 冲突。已改为 `fix-or-block`。

### important

none

Resolved:

- FDR-002：capture fidelity 未绑定 parser-facing 入口。已补充 Codex/Claude parser、consumer-strip 路径和 direct-stdout 路径。
- FDR-003：`status=workaround` 与 `workaround` 字段语义不够硬。已补充 `WorkaroundEvidence` schema invariant。
- FDR-004：`artifact_index` 缺最小结构。已补充 index 示例和 evidence 反查规则。
- FDR-005：capture fidelity 归一化覆盖被高估。已逐维标注：尾部空白由 `rstrip()` 吸收；CSI 可由 `strip_ansi` 处理；OSC/非 CSI、wrapping、宽字符、last-N 截断不能假设被 normalize 吸收。
- FDR-006：report 缺 degrade 语境。已新增 `degrade_impact` / `consequence`，并要求 blocking gap 携带同样语境。

### nit

none

Resolved:

- FDR-007：Step 5 粒度偏大。已拆成 `artifact/report 输出` 与 `Windows 真机 runbook`。
- FDR-008：`probe_completed` 字段形态不固定。已收紧为 `probe_status: completed|skipped|failed`。
- FDR-009：checklist `dod.evidence_required` 粗于 design Required Artifacts。已补 `artifacts_directory`、`daemon_pre_state_evidence`、`qa_report`、`acceptance_report`。
- FDR-010：checklist semantic catalog 的 daemon wording 不一致。已统一为 `daemon crash/cleanup evidence`。

### suggestion

none

Accepted:

- FDR-011：capture fidelity 建议同时保留 `get_pane_content()` consumer-strip 路径和 `project_view.pane_text_hint()` direct-stdout 路径。已写入 design/checklist。

### learning

- 当前代码仍是 tmux-only：`backend_selection.py` 只有 `selected == 'tmux'` 分支；本 feature 的范围守护明确不改 resolver。
- Codex/Claude 是 `provider_pane_status` 下全部现存 pane-status parser；没有 pane-status parser 的 provider 不在本 feature parser-facing 范围内。
- Codex/Claude parser 与 terminal consumer 的 ANSI stripping 均为 CSI-only；OSC/非 CSI 转义需要作为失败样例或真实 artifact 风险记录。
- `project_view.pane_text_hint()` 直接使用 `capture-pane` stdout，和 `get_pane_content()` 的 consumer-strip 路径不同，capture fidelity 需要同时覆盖。

### praise

- 范围边界清楚：不新增 `RmuxBackend`、不启用 opt-in config、不批准 route。
- 挂载点清单克制：只列 probe CLI、probe tests、roadmap drafts/report 产物约定。
- Windows 真机 evidence 被明确设为 route approval 前置阻塞条件，避免“无实测但继续实现”。
- `degrade_impact` / `consequence` 提供 route approval 语境，但不把路线决策塞回 probe。

## 4. User Review Focus

- 用户需要重点拍板：
  - 是否认可本 feature 只产出 `probe_status` / report / artifacts / blocking gaps / degrade 语境，不产出 route approval。
  - 是否认可 capture fidelity 覆盖全部现存 pane-status parser（Codex/Claude），且 fixture 与 Windows 真机 Rmux artifacts 不可互替。
  - 是否认可无 Windows 真机 evidence 时不能进入 `rmux-route-approval`。
- implement 需要重点遵守：
  - 不改 `backend_selection.py`，不新增 production `RmuxBackend`，不新增 `runtime.mux.backend` / `CCB_MUX_BACKEND`。
  - `partial` / `workaround` 不允许只写 notes；必须有结构化 workaround evidence。
  - 每个 evidence 路径必须能从 `artifact_index` 反查，且 artifact 已脱敏。
  - 每个 command/semantic 和 blocking gap 都要有 `degrade_impact` / `consequence`。
  - capture fidelity 要覆盖 consumer-strip 与 direct-stdout 两条 parser-facing 路径。
- code review / QA / acceptance 需要重点复核：
  - Windows probe 命令失败或缺 report/artifacts 是 blocking。
  - report 内 unsupported/partial gaps 是事实结果，不等于 route approved 或 route rejected。
  - OSC/非 CSI、wrapping、宽字符至少一个 normalize 兜不住的失败样例存在。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | design 3.3 覆盖 AC-001 至 AC-008，并映射到 S1-S7、证据类型和命令/动作 | none |
| DoD Contract | pass | E | design 3.4 + checklist `dod.commands` 字段一致；CMD-003 为 `fix-or-block` | none |
| Steps and checks traceability | pass | E | checklist steps/checks 可追溯到 design 2.1、2.2、2.3、3.1、3.2 | none |
| Roadmap contract compliance | pass | E/C | design 遵守 roadmap 4.2：probe completed 与 route approved 分离，command/semantic catalog 覆盖 required set | none |
| Module interface design | pass | E/C | design 2.1 明确 Capability Gate 是 report seam，不新增 runtime adapter；interface 检查覆盖 depth、seam、dependency strategy | none |
| Validation and artifacts | pass | E | design/checklist 明确 YAML、pytest、Windows probe、artifact index、redaction、daemon pre-state 和 required artifacts | Windows 真机 evidence 在实现/QA 阶段产出 |

Summary: E=6, C=2, H=0, H-only core checks=none。

## 6. Residual Risk

- Rmux 外部能力仍未验证；必须等实现阶段 Windows 真机 probe 产出 report/artifacts 后，才能判断 required gaps。
- capture fidelity 的真实风险依赖 ConPTY/Rmux 输出；parser-facing fixture 只能证明最小解析路径，最终仍需 Windows artifacts。
- `degrade_impact=unknown` 可能出现在 probe 无法判断用户可见后果时；route approval 必须把 unknown 当作需要人工判断的风险，而不是默认可降级。

## 7. Verdict

- Status: passed
- Next: 交给用户整体 review；用户确认后才能把 design 从 `draft` 改为 `approved`，再进入 `cs-feat-impl`。
