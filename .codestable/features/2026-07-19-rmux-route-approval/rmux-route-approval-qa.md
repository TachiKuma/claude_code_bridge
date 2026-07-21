---
doc_type: feature-qa
feature: 2026-07-19-rmux-route-approval
status: passed
runner_state: not-started
runner_reason: ""
runner_id: ""
tested: 2026-07-22
round: 1
---

# rmux-route-approval QA 报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-19-rmux-route-approval/rmux-route-approval-design.md`
- Checklist: `.codestable/features/2026-07-19-rmux-route-approval/rmux-route-approval-checklist.yaml`
- Review: `.codestable/features/2026-07-19-rmux-route-approval/rmux-route-approval-review.md`
- Evidence pack: `.codestable/features/2026-07-19-rmux-route-approval/rmux-route-approval-evidence-pack.md`
- Gate results: `.codestable/features/2026-07-19-rmux-route-approval/rmux-route-approval-scope-gate-results.json`
- DoD results: `.codestable/features/2026-07-19-rmux-route-approval/rmux-route-approval-dod-results.json`
- CMD-003 evidence: `.codestable/features/2026-07-19-rmux-route-approval/rmux-route-approval-cmd003-results.json`
- Diff basis: 当前 diff 只包含本 feature 的 CodeStable 产物与 roadmap goal-state；无 staged diff。
- Baseline dirty files: none outside this goal driver scope.
- Feature type: non-functional.
- Core evidence gate: 本 feature 不改 production runtime；QA 核心证据是 route authority、selected/superseded report facts、artifact hash、accepted workaround、downstream lock、roadmap admission 与 scope cleanliness 的一致性，不要求端到端用户运行路径。

## 2. Verification Matrix

| ID | 来源 | 核心性 | 场景 / 风险 | 证据类型 | 命令或动作 | 期望 | 结果 |
|---|---|---|---|---|---|---|---|
| QA-001 | AC-001 / CMD-003 | non-functional core | selected capability report 必须是 Windows completed report，且不能基于缺失或示例 evidence 批准路线 | schema/hash/manual | CMD-003 verifier | selected report 为 `rmux 0.9.0` / Windows / completed / `blocking_gaps=0` | pass |
| QA-002 | AC-002 / review focus | non-functional core | 旧 `rmux 0.8.0` 的 7 个 gaps 必须保留为 superseded facts | diff/manual | 读取 route summary 与 CMD-003 | superseded report hash、gap count 和 gap names 可恢复 | pass |
| QA-003 | AC-003 / review focus | non-functional core | accepted workaround 不能被写成无风险 | diff/manual | 读取 route summary、approval report、functional acceptance | `workaround_risk_decision` 表达 accepted via full-backend live evidence，并列出 downstream risk | pass |
| QA-004 | AC-004 / AC-006 / review focus | non-functional core | review/QA/acceptance 未闭合前不得解锁下游 | diff/manual | 读取 route summary 与 items.yaml | `route_approved=true` 且 `downstream_unlocked=false`；item 仍 `in-progress` | pass |
| QA-005 | DoD commands | non-functional core | checklist、route summary、items.yaml 和 gate JSON 必须可解析 | command | validate-yaml / json.tool | 所有命令 exit 0 | pass |
| QA-006 | 明确不做 / scope gate | non-functional core | 不应修改 production backend/resolver/transport 代码 | diff/grep | `git diff --name-only`、scope gate、关键词 grep | 改动只在 `.codestable/features/...` 与 roadmap state/items 范围内 | pass |
| QA-007 | evidence pack residual risks | supporting | provider signals skipped、OCR lane unavailable 不得掩盖核心证据缺口 | report review | 读取 evidence pack 与 review | 这些风险均为治理辅助信号，不影响 route facts 核验 | pass |

## 3. Command Results

- `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-19-rmux-route-approval/rmux-route-approval-checklist.yaml" --yaml-only` -> exit 0：checklist YAML valid。
- `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-19-rmux-route-approval/rmux-route-decision-summary.yaml" --yaml-only` -> exit 0：route summary YAML valid。
- `python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml"` -> exit 0：items YAML valid。
- `python -m json.tool` on `rmux-route-approval-cmd003-results.json`、`rmux-route-approval-dod-results.json`、`rmux-route-approval-scope-gate-results.json`、`rmux-route-approval-evidence-pack-results.json` -> exit 0：JSON valid。
- read-only CMD-003 verifier -> exit 0：selected report `rmux 0.9.0/windows/gaps=0`，superseded report `rmux 0.8.0/windows/gaps=7`，`foreground_attach` 与 `live_client_commands` evidence hash 匹配。
- `codestable-workflow-next.py feature --feature ".codestable/features/2026-07-19-rmux-route-approval" --require-implementation-ready --json` -> exit 0：implementation dependencies ready，review gate passed，QA missing before this report。
- `codestable-workflow-next.py epic --roadmap ".codestable/roadmap/windows-rmux-native-backend" --json` -> exit 0：visible goal driver recorded；no blocking。
- `git diff --name-only` / `git status --short`：tracked diff 只含 checklist 与 goal-state，untracked 均为本 feature gate/evidence/report artifacts。

## 4. Scenario Results

- [x] QA-001 selected capability report authority：pass。
  - Evidence: CMD-003 verifier 核对 selected report SHA256、`platform=windows`、`probe_status=completed`、`blocking_gaps_count=0`。
- [x] QA-002 superseded gaps preserved：pass。
  - Evidence: route summary 保留旧 canonical report SHA256 与 7 个 gaps；CMD-003 verifier 复核旧 report hash 与 gap count。
- [x] QA-003 workaround risk surfaced：pass。
  - Evidence: route summary 使用 `accepted-via-full-backend-live-evidence`，并列出 `attach-session`、`kill-server`、`refresh-client`、`attach_reattach` 的 evidence 与 downstream risk。
- [x] QA-004 downstream admission locked until acceptance：pass。
  - Evidence: `parent_handoff.route_approved=true`、`downstream_unlocked=false`；roadmap item 当前仍为 `in-progress`。
- [x] QA-005 schema / gate evidence：pass。
  - Evidence: YAML、JSON、workflow-next 命令均 exit 0。
- [x] QA-006 scope / cleanliness：pass。
  - Evidence: scope gate changed_files 覆盖本轮生成产物；当前没有 production 代码 diff。
- [x] QA-007 provider / OCR residual classification：pass。
  - Evidence: provider signals skipped 与 OCR lane unavailable 只影响辅助审查覆盖，不影响 selected report、approval ref 和 route summary 的核心核验。

## 5. Findings

### failed

none

### blocked

none

### residual-risk

- full-backend report 中 `attach-session`、`refresh-client`、`kill-server`、`attach_reattach` 仍依赖 accepted live evidence / workaround；这不是当前 route blocker，但下游 `rmux-backend-core`、`rmux-send-capture-logging`、`ccbd-windows-full-chain-smoke` 必须继续显式消费这些风险。
- 未重放 `windows-rmux-full-backend` live foreground/client commands，只复核 report hash、functional acceptance 摘要、live evidence 文件存在性和 hash。对本治理 feature 足够；真实运行闭环留给后续 Windows native backend feature。

## 6. Cleanliness

- Debug output: pass。
- Temporary TODO/FIXME/XXX: pass；唯一命中是 design 中的清洁度规则文本。
- Commented-out code: pass；本 feature 不改生产代码。
- Unused imports / dead code from this feature: pass；无代码改动。
- Out-of-scope files: pass；scope gate 与 `git status --short` 均显示改动在本 feature / roadmap goal-state 范围内。

## 7. Verdict

- Status: passed
- Next: `cs-feat` acceptance 阶段。
