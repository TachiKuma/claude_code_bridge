# Goal Final Audit Protocol

## 1. 启动

所有 feature accepted 后打印：

```text
CS_ROADMAP_GOAL_AUDIT_START
Roadmap: windows-rmux-ux-parity-hardening
Features to verify: 6
Commands to re-run: <去重命令列表>
```

读取 roadmap 主文档、items.yaml、goal-plan、goal-state、approval-report、goal-features、每个 feature 的 design/checklist/review/QA/acceptance/evidence pack/gate results。

## 2. 核验

先运行机器一致性 gate：

```bash
python3 C:/Users/Administrator/.codex/plugins/cache/codestable/codestable/1.0.4/skills/cs-onboard/tools/codestable-goal-consistency-gate.py --roadmap .codestable/roadmap/windows-rmux-ux-parity-hardening
```

失败时不得打印完成标记；按 blocking 项补齐证据或回退状态后重跑。

必须核验：

- all items terminal：`done` 或 `dropped(reason)`。
- roadmap feature bijection：item feature 指针与 accepted feature 无缺失、额外或重复。
- canonical feature evidence：路径、doc_type、feature identity 均归属当前 feature。
- goal authorizations：同 roadmap canonical approval-report 的 `goal-acceptance` 与 `goal-commits` 均 approved。
- all feature artifacts passed：review、QA、acceptance 均 passed。
- all checklist passed：steps done、checks passed。
- no core residual risk：核心 UX parity 缺口不得被写成 residual。
- provider risks explained。
- writebacks complete or not applicable。

## 3. 最终聚合命令

按 goal-plan 执行 final aggregate commands。功能性核心命令不能因耗时跳过。外部网络、凭证、GUI、WezTerm 或 rmux 不可用时，判断是否属于核心验收路径；核心不可验证则 handoff。

## 4. 工作区与清洁度

检查 tracked / staged / unstaged / untracked、调试输出、临时 TODO/FIXME/XXX、注释掉代码、同名工具 shim、临时 runner、临时下载包、`__pycache__`。未解释命中会阻塞最终完成。

## 5. 审计报告

写 `.codestable/roadmap/windows-rmux-ux-parity-hardening/goal-audit.md`：

```markdown
---
doc_type: roadmap-goal-audit
roadmap: windows-rmux-ux-parity-hardening
status: passed|blocked
audited: YYYY-MM-DD
round: 1
---

# windows-rmux-ux-parity-hardening Goal 最终审计

## 1. Scope
## 2. Roadmap State
## 3. Final Aggregate Commands
## 4. Core Acceptance Paths
## 5. Deliverables And Writebacks
## 6. QA Residual Risk Review
## 7. Provider And E/C/H Evidence Summary
## 8. Workspace And Cleanliness
## 9. Verdict
```

## 6. 完成与学习反思

无缺口时打印：

```text
CS_ROADMAP_GOAL_AUDIT_COMPLETE
CS_ROADMAP_GOAL_LEARNING_REVIEW
CS_ROADMAP_GOAL_COMPLETE
```

learning reflection 只筛选候选，不自动写 `.codestable/compound/`；需要用户确认后再运行 `cs-keep`。
