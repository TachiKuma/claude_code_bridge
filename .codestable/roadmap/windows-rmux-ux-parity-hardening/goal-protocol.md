# CodeStable Roadmap Goal Protocol

本文件由 `/goal` 会话读取。详细执行规则在同目录：

- `goal-protocol-feature-loop.md`
- `goal-protocol-gates.md`
- `goal-protocol-audit.md`

## 1. 先读文件

- `.codestable/roadmap/windows-rmux-ux-parity-hardening/goal-state.yaml`
- `.codestable/roadmap/windows-rmux-ux-parity-hardening/goal-plan.md`
- `.codestable/roadmap/windows-rmux-ux-parity-hardening/windows-rmux-ux-parity-hardening-roadmap.md`
- `.codestable/roadmap/windows-rmux-ux-parity-hardening/windows-rmux-ux-parity-hardening-items.yaml`
- `.codestable/roadmap/windows-rmux-ux-parity-hardening/goal-features/*.md`
- `.codestable/roadmap/windows-rmux-ux-parity-hardening/goal-protocol-feature-loop.md`
- `.codestable/roadmap/windows-rmux-ux-parity-hardening/goal-protocol-gates.md`
- `.codestable/roadmap/windows-rmux-ux-parity-hardening/goal-protocol-audit.md`

## 2. 启动检查

- 所有 feature design frontmatter 必须是 `status: approved`。
- `goal-state.yaml` 的 `current_feature_index` 为 0-based。
- `baseline_ref` 在 git 仓库内必须能解析为 SHA。
- `goal-plan.md` 必须包含 roadmap 核心验收路径、最终聚合命令、DoD Policy、Gate Policy、Provider Policy。
- `acceptance_authorization: approved`，且 ref 指向同 roadmap 的 `approval-report.md#goal-acceptance`、命名决策为 approved。
- `commit_authorization: approved`，且 ref 指向同 roadmap 的 `approval-report.md#goal-commits`、命名决策为 approved。
- 运行 `python3 C:/Users/Administrator/.codex/plugins/cache/codestable/codestable/1.0.4/skills/cs-onboard/tools/codestable-workflow-next.py epic --roadmap .codestable/roadmap/windows-rmux-ux-parity-hardening --json`；只有 `dispatch_goal` / `awaiting` 且 evidence 同时返回两份预期 ref 才可启动或继续 driver。
- checklist `steps` 和 `checks` 初始状态必须为 `pending`；goal 执行中按阶段更新。

## 3. Goal 模式接管

`/goal` 只代表启动已授权执行包；acceptance 与自动 commit 必须各有独立 `ApprovalRef`。普通逐 feature checkpoint 在 goal 模式下改为写入报告、状态和审计记录。

```text
CS_ROADMAP_GOAL_START
Roadmap: windows-rmux-ux-parity-hardening
Features: 6
Baseline ref: <sha>
Plan: .codestable/roadmap/windows-rmux-ux-parity-hardening/goal-plan.md
Protocol: .codestable/roadmap/windows-rmux-ux-parity-hardening/goal-protocol.md
```

执行顺序以 `goal-state.yaml` 的 `features` 和 `current_feature_index` 为准。进入每个 feature 前必须读取对应 `goal-features/<feature-slug>.md`，并用 `codestable-workflow-next.py feature --require-implementation-ready` 机械核验依赖严格 `done`。

## 4. 完成与 handoff

只有最终审计通过后，先把 `goal-state.yaml` 顶层更新为 `status: complete`，再打印：

```text
CS_ROADMAP_GOAL_COMPLETE
```

无法继续时，先把 `goal-state.yaml` 顶层更新为 `status: handoff`，并写入 `handoff_reason` / `handoff_next`，再打印：

```text
CS_ROADMAP_GOAL_HANDOFF
Reason: <具体阻塞>
Next: <建议动作>
```
