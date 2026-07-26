# Goal Feature Loop

## 1. 进入 Feature

读取：

- `goal-features/<feature-slug>.md`
- feature design
- feature checklist
- roadmap item
- 当前代码上下文

进入实现前运行：

```bash
python3 C:/Users/Administrator/.codex/plugins/cache/codestable/codestable/1.0.4/skills/cs-onboard/tools/codestable-workflow-next.py feature --feature <feature-dir> --require-implementation-ready --json
```

只有当前 item 的全部 `depends_on` 都严格为 `done` 时，才把该 feature 状态改为 `implementing`。`dropped` 或仅 design-review `passed` 只满足 child batch design admission，不满足实现准入。

打印：

```text
CS_ROADMAP_GOAL_FEATURE_START
Feature: <N>/<总数> <feature-slug>
Design: <路径>
Checklist: <路径>
Depends on: <依赖|none>
Mandatory commands: <命令列表>
Evidence required: <证据列表>
```

## 2. Implementation

必须显式进入 `cs-feat` implementation 阶段，禁止仅凭本协议摘要替代主入口协议。

- 先做基线预检。
- 按 checklist steps 顺序实现。
- 每步完成后只把该 step 的 `status` 从 `pending` 改为 `done`。
- 不修改 `checks`；checks 只由 acceptance 更新。
- 每步留下命令、手工、API、浏览器或 diff 证据。
- 实现结束后运行 implementation.before_review gates：scope-gate、dod-runner、evidence-pack。

## 3. Code Review

按 `cs-code-review` 执行，只读审查并写 `{feature-slug}-review.md`。

- review 必须基于当前 diff、design、checklist、evidence pack 和 gate results。
- review 必须由独立 Task agent reviewer 完成，除非已有 owner 明确批准 local-only fallback。
- review blocking 时打印 `CS_ROADMAP_GOAL_REVIEW_FIX`，回 implementation 修复后重跑 review。

## 4. QA

按 `cs-feat` QA 阶段执行，只读运行验证并写 `{feature-slug}-qa.md`。

- QA 覆盖 design 关键场景、DoD commands、review QA focus、evidence pack residual risks。
- 功能性核心路径必须有实际运行证据。
- 非功能性 feature 必须写明替代证据理由。
- QA failed 时打印 `CS_ROADMAP_GOAL_QA_FIX`，回 implementation 后重跑 review 和 QA。

## 5. Acceptance

按 `cs-feat` acceptance 阶段执行：

- 从 `goal-state.yaml` 读取 `acceptance_authorization_ref`，以 `ResumeGoalAcceptance ApprovalRef` 显式进入。
- 确认 review passed 且无 unresolved blocking。
- 确认 QA passed 且无 unresolved failed / blocked。
- 填 `{feature-slug}-acceptance.md`。
- 把 checklist checks 从 `pending` 改为 `passed`。
- 回写 roadmap item 为 `done`，并按 design 第 4 节处理 docs / architecture / requirement 回写。

## 6. Feature 完成

打印 `CS_ROADMAP_GOAL_FEATURE_VERIFY`，列出 Implementation / Review / QA / Acceptance / Commands / Deliverables / Cleanliness / Roadmap item。

全部通过后：

- 当前 feature 状态改为 `accepted`。
- `current_feature_index` 加 1，并把 accepted 状态、roadmap/items 回写和新 index 一起持久化。
- 再次运行 epic workflow-next，只有 authorization evidence 同时返回 `approval-report.md#goal-acceptance` 与 `approval-report.md#goal-commits` 时才允许 scoped commit。
- commit 成功后运行 `git status --short`，只有工作树干净才能进入下一条。
- 打印 `CS_ROADMAP_GOAL_FEATURE_DONE`。
