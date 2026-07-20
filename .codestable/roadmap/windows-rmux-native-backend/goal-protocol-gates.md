# Goal Gate Policy

## 1. 通用 Gate Result

```haskell
data GateKind = Executable | ProtocolOnly
data GateStatus = Passed | Failed | NeedsHuman | Awaiting | Blocked | Skipped
data Gate = Design | Implementation | Review | QA | Acceptance | RoadmapAudit
data Recovery = ReviseDesign | FixImplementation | FixReview | FixQAThenReview | FixAcceptance | FixAudit

recover :: Gate -> Recovery
recover Design         = ReviseDesign
recover Implementation = FixImplementation
recover Review         = FixReview
recover QA             = FixQAThenReview
recover Acceptance     = FixAcceptance
recover RoadmapAudit   = FixAudit

maySkip :: Bool -> Maybe Reason -> Bool
maySkip core reason = not core && isJust reason
```

每个 gate 输出：

```json
{
  "gate_id": "gate-name",
  "feature": "YYYY-MM-DD-feature-slug",
  "inputs": {"design|checklist|feature_dir|out": "canonical repo-relative path"},
  "input_digests": {"design|checklist|out": "sha256"},
  "stage": "stage.name",
  "kind": "executable|protocol-only",
  "status": "passed|failed|needs-human|awaiting|blocked|skipped",
  "blocking": [],
  "warnings": [],
  "evidence": [],
  "providers": {}
}
```

`Failed` 表示已完成且发现可修复 blocking；`NeedsHuman` 表示缺 owner 输入 / 能力，`Awaiting` 表示外部工作已启动，`Blocked` 表示可观察失败或终止态；`Skipped` 受 `maySkip` 约束。

`kind: protocol-only` 表示该 gate 是协议阶段规则，由对应 review / QA / acceptance / audit 技能读取 evidence 后执行；它不是可直接调用的脚本，机器 runner 不应把它当成缺失脚本。
旧 gate result 缺 `kind` 时只可归一为 `executable`；不得从缺字段推断 `protocol-only`。

## 1.1 Target-Platform Core Evidence

本 roadmap goal 的核心平台是 native Windows。gate 判断 `core` 时必须先区分：

- **target-platform core evidence**：native Windows 上 `ccb -> ccbd -> rmux` 的控制面、mux、provider path、start/ask/kill/full-chain smoke 证据。
- **compatibility evidence**：Linux/macOS/WSL/Unix `AF_UNIX` 真实 socket 行为、现有 tmux 路径不漂移等跨平台兼容性证据。

缺少 target-platform core evidence 阻塞 QA / acceptance / audit。缺少 compatibility evidence 只有在该 feature 的当前目标明确承诺“本轮必须证明该兼容性”时才阻塞；否则可以在 owner 已记录目标平台证据边界后作为 residual risk 进入后续 Windows 核心 feature。

`ccbd-control-plane-transport-seam` 是特殊边界：它抽 seam 并保留 Unix adapter，但本 milestone 的目标不是在 native Windows 主机证明真实 `AF_UNIX` 行为。当前主机没有 `socket.AF_UNIX` 或 WSL 不可用时，真实 Unix `AF_UNIX` tests skipped 不得单独阻塞 `windows-rmux-native-working`；后续 `ccbd-windows-tcp-loopback-transport` 和 `ccbd-windows-full-chain-smoke` 才是 Windows 控制面核心证据。

Windows collection / import / runtime blocker 不属于 compatibility residual。`mobile_gateway.terminal -> import fcntl`、accelerator `AF_UNIX` AttributeError、Windows pid liveness 等会阻断 native Windows 命令的缺口必须修复或单独记录 owner decision。

## 2. feature_design.before_approve

必须有：

- design-review passed
- checklist YAML 可解析
- Acceptance Coverage Matrix
- DoD Contract

失败按 `recover Design`；goal 模式不接管未 approved design。

## 3. implementation.before_review

必须运行：

- `scope-gate`
- `dod-runner`
- `evidence-pack`

`scope-gate` / `dod-runner` / `evidence-pack` 从当前 `cs-onboard` skill 包 `tools/` 运行；缺脚本说明本机 CodeStable 安装不完整，应先更新 / 重装 CodeStable。

检查：

- checklist steps 全部 `done`。
- 当前 diff 没有未解释的范围外文件。
- 清洁度通过。
- checklist `dod.commands` 的 core 命令有执行证据。
- evidence pack 已生成并包含 Scope、DoD Results、Validation Commands、Scope And Cleanliness、Residual Risks。

失败按 `recover Implementation`；缺 evidence 时补证据，不能进入 review。

## 4. review.before_pass

必须运行 `review-evidence-gate`。

检查：

- review 基于当前 diff。
- review `status=passed`。
- review 必须由独立 Task agent reviewer 完成；frontmatter `reviewer: subagent` 或 `subagent+ocr` 是默认放行锚点。`reviewer: ocr` / `self` 只能作为用户显式降级 fallback，不能静默通过。
- 无 unresolved blocking。
- review 明确消费 evidence pack 和 gate results。
- high-risk provider warnings 已解释或交给 QA。

失败按 `recover Review`；缺 evidence 则补证据，reviewer 不独立则 handoff / 重启独立 review。

## 5. qa.before_acceptance

必须运行 `qa-evidence-gate`。

检查：

- QA `status=passed`。
- QA matrix 覆盖 design 关键场景、DoD commands、review QA focus、evidence pack residual risks。
- 功能性核心路径有实际运行证据。
- 非功能性 feature 有替代证据理由。
- QA 没有把核心缺口写成 residual-risk。
- native Windows milestone 中，Unix-only `AF_UNIX` 真实主机证据缺失可以写成 compatibility residual，前提是 QA 同时证明 seam/fake/import guard 证据已覆盖目标平台继续推进所需边界，并引用 `approval-report.md` 的 native Windows evidence decision。
- Windows collection / import blocker 不能借 Unix residual policy 放行；若影响 CMD-005、start/ping/doctor/ask/kill 的收集或运行，QA 必须保持 failed/blocked，除非 owner 对该具体 Windows 缺口另行记录可接受决策。
- 高风险 feature 建议启用独立 QA Task agent；其输出必须由主流程核验并写入 QA 报告，runner 不替代正式 verdict，结果消费后按 Task agent 生命周期关闭。

失败按 `recover QA`。

## 6. acceptance.before_done

必须运行 `acceptance-dod-gate`。

检查：

- acceptance `status=passed`。
- checklist checks 全 `passed`。
- blocking DoD 均有 pass evidence。
- roadmap item 已回写。
- residual risk 不包含核心验收缺口。
- residual risk 可以包含非目标平台 compatibility 缺口，例如 native Windows 主机无法执行真实 Unix `AF_UNIX` lifecycle；acceptance 必须明确说明该缺口不覆盖 Windows milestone core，并把真正的 Windows 控制面证明交给 `ccbd-windows-tcp-loopback-transport` / `ccbd-windows-full-chain-smoke`。
- 可选只读 acceptance Task agent auditor 只能提供复核 findings；checklist / roadmap / requirement / acceptance 状态写入必须由主流程 owner 完成，结果消费后按 Task agent 生命周期关闭。

失败先归因：`StageEvidenceDefect` 按 `recover Acceptance`；`ImplementationDefect` 回 implementation 后重跑 review / QA / acceptance。

## 7. roadmap_audit.before_complete

必须运行：

- `goal-consistency-gate`
- `goal-audit-gate`

检查：

- goal-state 全部 features 为 `accepted`。
- goal-state 与同 roadmap canonical `approval-report.md` 对 `goal-acceptance`、`goal-commits` 的授权均机械核验为 approved。
- items.yaml 条目均为 `done` 或有理由 `dropped`。
- 每个非 dropped item 恰好对应一个 feature；item 的 `feature` 指针与 canonical feature_dir identity 必须匹配，禁止缺失、额外或重复 feature。
- feature_dir、design、checklist、review、QA、acceptance 必须是当前 slug 的 canonical 路径，frontmatter `doc_type` / `feature` 必须匹配当前 feature。
- 四份 executable gate JSON 只接受 `status=passed`，`gate_id`、`feature` identity、canonical `inputs` 与文件型 input SHA-256 必须匹配当前 feature；scope/dod/evidence stage 只接受 `implementation.before_review|acceptance`，DoD contract 只接受 `feature_design.before_approve|acceptance`，其他值均阻断并重跑对应 gate。
- 每个 feature 的 approved design、review / QA / acceptance / evidence pack / gate results / DoD contract results / DoD results 存在。
- review / QA / acceptance 均 `status=passed`，checklist steps 全 `done`，checks 全 `passed`。
- final aggregate commands 已重跑或有非核心 trust-prior 理由。
- provider warnings 已解释。
- goal-audit.md 已落盘且 `status=passed`。
- roadmap final audit 的 `noCoreResidualRisk` 以 native Windows milestone 为准：Unix-only `AF_UNIX` compatibility residual 不阻塞最终审计；native Windows full-chain smoke、TCP loopback auth、accelerator guard、Windows process liveness、Rmux namespace lifecycle 的缺口仍阻塞。

失败按 `recover RoadmapAudit`；同项三轮仍失败则 handoff。

## 8. Provider Policy

- provider unavailable 不阻塞基础流程。
- provider warning 必须被 review / QA / audit 解释。
- 未解释的核心风险可阻塞。
- meta-cc 首批只读取已有摘要文件或记录 unavailable。
