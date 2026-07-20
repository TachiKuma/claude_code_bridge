# CodeStable Roadmap Goal Protocol

本文件复制到 `.codestable/roadmap/windows-rmux-native-backend/goal-protocol.md` 后，由 `/goal` 会话读取。详细执行规则拆到同目录子文档，避免单个 md 超过 300 行。

## 1. 先读文件

- `.codestable/roadmap/windows-rmux-native-backend/goal-state.yaml`
- `.codestable/roadmap/windows-rmux-native-backend/goal-plan.md`
- `.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-roadmap.md`
- `.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml`
- `.codestable/roadmap/windows-rmux-native-backend/goal-features/*.md`
- `.codestable/roadmap/windows-rmux-native-backend/goal-protocol-feature-loop.md`
- `.codestable/roadmap/windows-rmux-native-backend/goal-protocol-gates.md`
- `.codestable/roadmap/windows-rmux-native-backend/goal-protocol-audit.md`

## 2. 启动检查

- 所有 feature design frontmatter 必须是 `status: approved`。
- `goal-state.yaml` 使用 `current_feature_index`，语义为 0-based。
- `baseline_ref` 在 git 仓库内必须能解析为 SHA。
- `goal-plan.md` 必须包含 roadmap 核心验收路径、最终聚合命令、DoD Policy、Gate Policy、Provider Policy。
- `acceptance_authorization: approved`，且 ref 指向同 roadmap 的 `approval-report.md#goal-acceptance`、命名决策为 approved；空 ref、伪路径、缺文件或 rejected 均不得启动或继续 driver。
- `commit_authorization: approved` 也须独立指向 `approval-report.md#goal-commits` 且命名决策为 approved；acceptance ref 不可复用。缺失或拒绝时不得启动、继续或提交。
- 运行 `python3 <cs-onboard skill 目录>/tools/codestable-workflow-next.py epic --roadmap <roadmap-dir> --json`；只有 `dispatch_goal` / `awaiting` 且 evidence 同时返回两份预期 ref 才可启动或继续 driver。
- checklist `steps` 和 `checks` 初始状态必须为 `pending`；goal 执行中按阶段更新。

## 3. Goal 模式接管

用户粘贴 `/goal` 或主流程派发 driver，只代表启动已授权执行包；acceptance 与自动 commit 必须各有独立 `ApprovalRef`。普通流程逐 feature checkpoint 在 goal 模式下改为写入报告、状态和审计记录。

```haskell
data GoalHandoffReason
  = OwnerStop | ScopeChange | IndependentReviewUnavailable
  | UnapprovedHOnlyCoreCheck | CoreEvidenceUnavailable
  | CorePathUnverified | RepeatedFailure
data GoalRun = RunFeature Index | RunFinalAudit | Complete | Handoff GoalHandoffReason

handoffReason :: GoalState -> Maybe GoalHandoffReason
handoffReason s
  | ownerStopped s                   = Just OwnerStop
  | approvedScopeChanged s           = Just ScopeChange
  | reviewerBlocked s                = Just IndependentReviewUnavailable
  | unapprovedHOnlyCoreCheck s       = Just UnapprovedHOnlyCoreCheck
  | coreEnvironmentMissing s         = Just CoreEvidenceUnavailable
  | corePathUnverified s             = Just CorePathUnverified
  | sameFailureCount s >= 3          = Just RepeatedFailure
  | otherwise                        = Nothing

nextGoal :: GoalState -> GoalRun
nextGoal s
  | Just reason <- handoffReason s    = Handoff reason
  | Just i <- nextPendingFeature s    = RunFeature i
  | not (finalAuditPassed s)          = RunFinalAudit
  | otherwise                         = Complete
```

### 3.1 Target-Platform Evidence Policy

本 goal 的终点是 `windows-rmux-native-working`：native Windows 上 `ccb -> ccbd -> rmux` 真链路跑通。`coreEnvironmentMissing` 只适用于目标平台核心证据缺失；不得把本机缺少 `socket.AF_UNIX`、WSL 不可用、Unix-only `AF_UNIX` 测试跳过，单独判定为本 milestone 的 `CoreEvidenceUnavailable`。

`ccbd-control-plane-transport-seam` 的 Unix adapter 行为仍必须由 fake/unit/import guard 等可用证据证明 seam 没有破坏调用层；真实 Unix `AF_UNIX` bootstrap/lifecycle/stale-cleanup 证据在 native Windows goal 中是 compatibility residual。若 QA 只缺这类 Unix-only 真实主机证据，且 `approval-report.md` 已记录 owner 接受该目标平台证据边界，driver 应继续推进到 Windows TCP loopback feature，而不是要求 Unix/WSL/CI 证据作为恢复条件。

相反，native Windows 上会阻断 collection、start、ping、ask、kill 或 full-chain smoke 的问题仍是目标平台核心阻塞。例如 `mobile_gateway.terminal -> import fcntl` 这类 Windows collection baseline 不能被 `AF_UNIX` residual policy 自动豁免；必须修复、隔离为 Windows-safe import，或由 owner 单独记录可接受缺口。

## 4. 启动标记

```text
CS_ROADMAP_GOAL_START
Roadmap: windows-rmux-native-backend
Features: <数量>
Baseline ref: <sha|no-git>
Plan: .codestable/roadmap/windows-rmux-native-backend/goal-plan.md
Protocol: .codestable/roadmap/windows-rmux-native-backend/goal-protocol.md
```

## 5. 执行顺序

`nextGoal` 是顺序真相。`RunFeature i` 读取 goal-feature/design/checklist，执行 feature loop 与
stage gates；accepted 后先更新 state/items/index，再复核 commit 授权并 scoped-commit，所有状态更新后工作树干净才进入下一 feature。
`RunFinalAudit` 执行 `goal-protocol-audit.md`。

## 6. 完成标记

只有最终审计通过后，先把 `goal-state.yaml` 顶层更新为 `status: complete`，再打印：

```text
CS_ROADMAP_GOAL_COMPLETE
```

如果无法继续：

先把 `goal-state.yaml` 顶层更新为 `status: handoff`，并写入
`handoff_reason` / `handoff_next`；保留 `current_feature_index`、features 和 driver
字段，使主流程能从仓库事实恢复 handoff。然后打印：

```text
CS_ROADMAP_GOAL_HANDOFF
Reason: <具体阻塞>
Next: <建议动作>
```
