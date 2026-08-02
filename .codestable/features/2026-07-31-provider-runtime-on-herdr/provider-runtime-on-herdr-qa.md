---
doc_type: feature-qa
feature: 2026-07-31-provider-runtime-on-herdr
status: passed
runner_state: completed
runner_reason: ""
runner_id: "019fc3fe-f0d0-7ca3-8dd1-63f9c2407f9d"
tested: 2026-08-03
round: 1
---

# provider-runtime-on-herdr QA 报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-31-provider-runtime-on-herdr/provider-runtime-on-herdr-design.md`
- Checklist: `.codestable/features/2026-07-31-provider-runtime-on-herdr/provider-runtime-on-herdr-checklist.yaml`
- Review: `.codestable/features/2026-07-31-provider-runtime-on-herdr/provider-runtime-on-herdr-review.md`
- Implementation evidence: `.codestable/features/2026-07-31-provider-runtime-on-herdr/provider-runtime-on-herdr-implementation.md`
- S7 evidence:
  - `.codestable/features/2026-07-31-provider-runtime-on-herdr/evidence/public-providers-snapshot.json`
  - `.codestable/features/2026-07-31-provider-runtime-on-herdr/evidence/native-windows-x64-all-provider-herdr-workflow-transcript.md`
  - `.codestable/features/2026-07-31-provider-runtime-on-herdr/evidence/cmd004-baseline-exemption.md`
- Diff basis: 当前工作区 unstaged/untracked diff；staged diff 为空。
- Baseline dirty files: 工作区 dirty 范围很大；本 QA 只归因 provider-runtime-on-herdr S7 evidence / 状态文档 / roadmap handoff。
- Feature type: mixed。S1-S6 是运行时功能集成；S7 是证据、manual blocked transcript 和 regression/scope gate。
- Core evidence gate: S7 不运行真实 provider workflow；真实 provider `ask/pend/completion/cancel` 会触发外部 provider/API 或本机 AI bridge，本轮没有生产 API 调用授权，因此保留 per-provider blocked evidence 是设计允许的 QA 结果，不是 QA failure。

## 2. Verification Matrix

| ID | 来源 | 核心性 | 场景 / 风险 | 证据类型 | 命令或动作 | 期望 | 结果 |
|---|---|---|---|---|---|---|---|
| QA-001 | design AC-012 / review focus | core-functional/manual-evidence | 当前 public provider catalog freeze 来自源码和 registry 输出 | JSON / Python | 比对 `CORE_PROVIDER_NAMES + OPTIONAL_PROVIDER_NAMES` 与 snapshot | provider count=20，包含 `qoder/qoderclicn`，无 fake/test doubles | pass |
| QA-002 | design AC-012 / review focus | core-functional/manual-evidence | transcript 逐 provider 覆盖 launch/ask/pend-completion/cancel | Markdown parser | 解析 transcript provider rows | 20/20 provider rows，四列全 `blocked` | pass |
| QA-003 | review REV-001 / residual risk | supporting | CMD-004 不得被解释为全量 pass | Markdown / static | 读取 `cmd004-baseline-exemption.md` | frontmatter/status/verdict 均为 baseline-risk，正文明确不能解释为 CMD-004 全量通过 | pass |
| QA-004 | review focus / roadmap gate | core-functional/projection | blocked evidence 不得被写成 acceptance passed 或 supported | static / YAML | 扫 checklist、implementation、review、roadmap | provider-runtime roadmap 保持 in-progress；无 acceptance passed；有“不得宣称 supported” | pass |
| QA-005 | design AC-013 | supporting | S7 scope 不越界到 recovery/user-surface/release/support/Herdr client owner | static guard | scoped S7 content/path guard | S7 scope 无 forbidden owner 命中 | pass |
| QA-006 | review residual risk | supporting | 全局 CMD-009 dirty 隔离 | static / review evidence | 复核 implementation/review/runner output | 全局 guard 仅作为既有 dirty residual risk，不宣称全局干净 | pass |

## 3. Command Results

- `provider_snapshot_check` → exit 0：当前源码 public provider set 与 snapshot 一致，`provider_count=20`。
- `transcript_rows_check` → exit 0：transcript 解析到 20 行，全部 provider 的 launch/ask/pend-completion/cancel 均为 `blocked`。
- `cmd004_baseline_exemption_check` → exit 0：CMD-004 baseline-risk 文档存在并禁止解释为全量通过。
- `blocked_projection_check` → exit 0：roadmap item/goal-state 均保持 provider-runtime `in-progress`；未写 acceptance passed / supported。
- `s7_scope_content_check` → exit 0：S7 evidence 无 forbidden owner/content 命中。
- YAML / JSON / diff checks：
  - checklist YAML validation：passed
  - roadmap items YAML validation：passed
  - goal-state YAML validation：passed
  - public provider snapshot JSON validation：passed
  - scoped `git diff --check`：exit 0，仅 CRLF/LF warning

## 4. Scenario Results

- [x] QA-001 provider catalog snapshot：pass
  - Evidence: runner 和本地 Python check 均确认 `CORE_PROVIDER_NAMES + OPTIONAL_PROVIDER_NAMES` 与 snapshot declared order 一致，catalog set 一致，无 fake/test doubles。
- [x] QA-002 all-provider transcript：pass
  - Evidence: transcript provider rows 为 20/20，四个 workflow status 列均为 `blocked`。
- [x] QA-003 CMD-004 baseline-risk：pass
  - Evidence: `cmd004-baseline-exemption.md` 明确 `baseline-risk` 和“不能解释为 CMD-004 全量通过”。
- [x] QA-004 blocked/supported projection：pass
  - Evidence: roadmap item 和 goal-state 仍为 `in-progress`；acceptance 文件不存在；实现/review/transcript 均禁止宣称 supported。
- [x] QA-005 scope boundary：pass
  - Evidence: S7 scoped path/content guard 通过。
- [x] QA-006 dirty isolation：pass
  - Evidence: 全局 CMD-009 命中既有 dirty `test/test_herdr_backend_client.py`，已作为 residual risk 记录。

## 5. Findings

### failed

none

### blocked

none

### residual-risk

- 所有 20 个 public provider 的 Native Windows x64 Herdr workflow 仍是 blocked evidence，不能投影为 supported。
- CMD-004 全量 runtime launch bundle 仍是 Codex bridge bootstrap baseline-risk，不能当作全量 pass。
- 工作区 dirty 范围较大；全局 scope guard 仍命中既有 dirty `test/test_herdr_backend_client.py`，本轮只确认 S7 scope 无命中。

## 6. Cleanliness

- Debug output: pass
- Temporary TODO/FIXME/XXX: pass
- Commented-out code: pass
- Unused imports / dead code from this feature: pass，S7 没有业务代码改动
- Out-of-scope files: pass，S7 scoped evidence / status / roadmap 无 forbidden owner 命中

## 7. Verdict

- Status: passed
- Next: `cs-feat` acceptance 阶段。acceptance 必须继续 fail closed：blocked provider workflow evidence 不能投影为 supported；CMD-004 只能按 baseline-risk 处理。
