---
doc_type: feature-design-review
feature: 2026-07-31-herdr-supportability-projection
status: passed
review_state: passed
review_reason: ""
reviewer_id: "019fb96c-d2d2-7380-9daf-608b602688b1"
reviewed: 2026-08-01
round: 13
---

# herdr-supportability-projection feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-31-herdr-supportability-projection/herdr-supportability-projection-design.md`
- Checklist: `.codestable/features/2026-07-31-herdr-supportability-projection/herdr-supportability-projection-checklist.yaml`
- Intent / brainstorm: none
- Roadmap: `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-roadmap.md`
- Related docs: `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml`, existing Rmux support projection/docs/tests
- Code facts checked: `lib/terminal_runtime/rmux_packaging_support.py`, `lib/cli/render_runtime/ops_views_doctor.py`, `docs/ccbd-diagnostics-contract.md`

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: 019fb96c-d2d2-7380-9daf-608b602688b1
- Raw output: round 13 reviewer 返回 blocking/important/nit/suggestion 均为 none，确认 round 12 的 `non_pass_workflows` key namespace 与 sorted render 修订已关闭。
- Merge policy: 已逐条本地核验；无 blocking/important/nit/suggestion 需要修订。
- Gate effect: final verdict passed.

- Round 11 local validation before reviewer completion: design YAML passed, checklist YAML passed, design-review frontmatter passed, roadmap items YAML passed, scoped `git diff --check` passed; CMD-004 docs guard still fails on existing `docs/ccbd-diagnostics-contract.md` `doctor --bundle` lines 22、662、726 and remains an implementation target red light.
- Round 11 independent reviewer 返回 1 个 blocking、3 个 important；主 agent 已本地核验并修订 design/checklist：supported gate 增加 current provider catalog / parent provider freeze freshness，缺 freeze 或 freeze 与当前 catalog 不一致时不得 supported；`support_tier_source` 改为由 parent acceptance 状态和 artifact kind 显式映射为 `accepted_matrix` / `blocked_skeleton` / `missing`，不再从 `support_tier_is_candidate` 反推；doctor/docs render contract 增加 `provider_workflows_status` / `herdr_provider_workflows_status`；workflow/provider aggregate 折叠优先级固定为 `missing > blocked/failed/not-run > partial > pass`，并要求 mixed-status fixture。修订影响 supported gate 语义，需启动完整 round 12 复审，不走 focused closure。
- Round 12 local validation before reviewer completion: design YAML passed, checklist YAML passed, design-review frontmatter passed, roadmap items YAML passed, scoped `git diff --check` passed; CMD-004 docs guard still fails on existing `docs/ccbd-diagnostics-contract.md` `doctor --bundle` lines 22、662、726 and remains an implementation target red light.
- Round 12 independent reviewer 返回 0 个 blocking、1 个 important；主 agent 已本地核验并修订 design/checklist：`non_pass_workflows` key namespace 固定为 `workflow:<workflow>` 与 `provider:<provider>:<workflow>`，并要求 doctor/docs render 按 key 字典序输出；CMD-003 covers 补 `non_pass_workflows_key_namespace` 与 `non_pass_workflows_sorted_render`。修订影响 projection/render 可比性，需启动完整 round 13 复审，不走 focused closure。
- Round 13 local validation before reviewer completion: design YAML passed, checklist YAML passed, design-review frontmatter passed, scoped `git diff --check` passed; CMD-004 docs guard still fails on existing `docs/ccbd-diagnostics-contract.md` `doctor --bundle` lines 22、662、726 and remains an implementation target red light.

## 2. Design Summary

- Goal: 将 Native Windows Herdr validation evidence 投影为单一 support tier，并同步 README/docs/doctor/residual risk。
- Key contracts: machine-owned projection、fail-closed tier rule、doctor/docs single projection source、no release/promotion authority。
- Steps: 5 个步骤，风险热点是 missing matrix fail-closed、supported claim 过度、doctor/docs drift、scope guard。
- Checks: checklist 当前 YAML 合法，steps/checks 均为 pending。
- Baseline / validation: 已包含 YAML 校验、projection pytest、doctor render test、docs guard 和 scope guard。

## 3. Findings

### blocking

- none

### important

- none

### nit

- none

### suggestion

- FDR-SUG-001 `release surface gate 显式字段需按新 req 收紧`：旧 round 10 reviewer 曾建议支持 `release-equivalent`，但该结论已被 `native-windows-ccb-via-herdr` requirement update 取代。新设计必须要求 strict `v8.5.2` 源头/新分支 evidence，不接受 release-equivalent。

### learning

- Round 1 independent reviewer 返回 0 个 blocking、2 个 important、1 个 nit 和 1 个 suggestion；主 agent 已本地核验并修订 design/checklist：CMD-005 纳入当前 feature 与 roadmap `.codestable` 产物扫描，且在同一行含明确否定/禁止/风险语境时不误报；CMD-005 显式使用 UTF-8 解码 git output 并已在当前 PowerShell 环境运行通过；补充 matrix → projection 字段映射表，明确 candidate `support_tier` 不直接发布，final projection 必须重新校验 `support_projection_allowed`、required key set、workflow status/reason；补齐 doctor payload object key `herdr_supportability_projection` 与 render line key；CMD-004 允许 `rejected/intentionally rejected` 语境。
- Round 2 independent reviewer 返回 0 个 blocking、3 个 important；主 agent 已本地核验并修订 design/checklist：CMD-005 改用 YAML 单引号承载、raw 单反斜杠 regex，并加入 regex self-check samples；artifact refs 映射改为固定表并写明缺失降级；doctor render keys 补 `herdr_install_entry` / `herdr_windows_npm_enabled`。
- Round 3 independent reviewer 返回 2 个 blocking、2 个 important；主 agent 已本地核验并修订 design/checklist：CMD-005 不再保留一行 Python guard，改为 `test/test_herdr_supportability_scope_guard.py` pytest 验收门，要求负例 fixture、code-tokenized publish/push/tag guard 和明确否定 allowlist；matrix refs 改为 parent matrix JSON path → `validation_ref`、parent top-level `release_surface_ref` → `release_surface_ref`、当前 feature `docs-consistency.json` / `doctor-render.json` → `docs_consistency_ref` / `doctor_render_ref`，避免要求 parent matrix 预置 docs/doctor artifact key；doctor render/AC/checklist/CMD covers 补 `herdr_beta_gaps`、blocked workflows 和 residual risks；定义 current feature docs/doctor artifact 最小 JSON shape 与 `ok=true` supported gate。
- Round 4 independent reviewer 返回 1 个 blocking、2 个 important 和 1 个 nit；主 agent 已本地核验并修订 design/checklist：`doctor --output` payload key 统一为 `herdr_supportability_projection`；`support_tier_source` 明确只能取 `default` 或 `blocked`，不允许字面值 `default|blocked`；checklist S3 exit signal 补 beta gaps / residual risks；CMD-003 covers 明确 payload key 字面值和全部 Herdr doctor render refs/lines；CMD-005 `test_status` 改为 `new`。
- Round 5 independent reviewer 返回 2 个 blocking、2 个 important；主 agent 已本地核验并修订 design/checklist：projection schema 将 `blocked_workflows` 收敛为 `non_pass_workflows`，要求所有 `partial/blocked/failed/not-run` workflow 的 reason 用户可见；doctor/docs render keys 和 CMD-003 covers 增加 `required_workflows_status`、`non_pass_workflows`、partial render；`supported` gate 要求 release surface artifact 可加载且 pass、install/update/package gate 均 pass、`install_entry!="diagnostic_only"`、`windows_npm_enabled=true`；`validation_ref` 必须绑定 parent passed acceptance 指向的 matrix JSON，显式 path 只能作为已验收 artifact override 或 unit fixture；CMD-005 `test_status` 已改为 `new`，并核验 CMD-004 仍为 existing。
- Round 6 independent reviewer 返回 0 个 blocking、1 个 important、1 个 nit；主 agent 已本地核验并修订 design/checklist：成功标准同步 release surface supported gate；release-surface 映射绑定 `WindowsX64ReleaseSurfaceProjection` 真实字段，要求 `schema_version==1`、`implementation_admission=="admitted"`、`surface_state=="available"`、`artifact_status=="ready"`、`package_metadata_policy=="win32-enabled-postinstall-gated"`、`release_install_entry!="diagnostic_only"`、`update_entry!="diagnostic_only"`、`windows_npm_enabled==true`；CMD-003 covers 补 parent acceptance doc_type/status/matrix artifact bound 和 release surface 字段级 fixtures。
- Round 7 independent reviewer 返回 0 个 blocking、1 个 important；主 agent 已本地核验并修订 design/checklist：`docs-consistency.json` 与 `doctor-render.json` 必须绑定当前 projection 的 ref/hash，且 docs `support_tier` / doctor `rendered_support_tier` 必须等于 final projection tier；缺失、stale、`ok!=true` 或 tier/ref/hash 不一致时最高为 `beta`；CMD-003 covers 补 stale docs/doctor artifact downgrade 和 tier/ref/hash equality fixtures。
- Round 8 independent reviewer 返回 0 个 blocking、1 个 important、1 个 nit 和 1 个 suggestion；主 agent 已本地核验并修订 design/checklist：`HerdrSupportabilityProjection` 增加 `projection_hash`；hash 规则固定为 UTF-8 canonical JSON、sorted keys、紧凑分隔符、SHA-256，并排除 `projection_hash` / `docs_consistency_ref` / `doctor_render_ref` 三个自引用或 volatile 字段；docs/doctor guard 改为两阶段固定点，只有非 docs/doctor 条件已满足的 supported candidate 才能生成 / 验证 artifact，final projection 仅在两份 artifact `schema_version=1`、`ok=true`、`projection_hash` 和 tier 都匹配时保持 `supported`，否则最高 `beta`；CMD-003 covers 补 canonicalization、自引用排除、两阶段固定点、schema_version、projection_hash/tier match 和 stale downgrade。
- Round 9 independent reviewer 返回 0 个 blocking、1 个 important；主 agent 已本地核验并修订 design/checklist：明确 candidate hash 只用于 supported gate 验证；若 final 因 docs/doctor artifact 缺失、stale、`ok!=true` 或 tier/hash 不一致而降级，final `projection_hash` 必须基于降级后的 final projection 重新计算；CMD-003 covers 补 `final_downgrade_recomputes_projection_hash`。
- Round 10 independent reviewer 返回 0 个 blocking、0 个 important、0 个 nit、1 个 suggestion；主 agent 已本地核验：round 9 important 已关闭，projection identity、docs/doctor two-stage fixed point、final downgrade hash 重算和 Herdr doctor payload/render key 契约均已可执行追踪。

### praise

- 设计沿用 Rmux 的单一 projection owner 模式，但没有复用 Rmux 模块状态，避免 Herdr/Rmux 职责混杂。

## 4. User Review Focus

- 用户需要重点拍板：本 child 不单独停等确认；按 epic child batch loop 回到统一 design confirmation。
- implement 需要重点遵守：`supported` gate 必须 fail-closed；final downgraded projection 必须重算 `projection_hash`；docs/doctor artifacts 必须绑定 final projection hash 与 tier。
- code review / QA / acceptance 需要重点复核：CMD-003 的 projection/doctor fixtures、CMD-004 docs guard、CMD-005 scope guard 是否覆盖 stale ref、错误 key、错误 tier/hash、partial/non-pass workflow 和 publish/push/tag 越界。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | design/checklist 覆盖 parent matrix acceptance、release surface gate、docs/doctor artifact gate 和 scope guard | implementation 按 checklist 执行 |
| DoD Contract | pass | E | CMD-001..CMD-005 均已定义，new/existing 状态与 covers 已明确 | implementation 新增测试时保持 covers 对齐 |
| Steps and checks traceability | pass | E | S1..S5 均有对应 checks / DOD command / evidence_required | implementation 后更新 checklist 状态 |
| Roadmap contract compliance | pass | E | roadmap item 已绑定 feature，依赖 `native-windows-public-workflow-validation-matrix`，无 release/publish 授权越界 | 回到 epic child batch loop |
| Module interface design | pass | E | 单一 projection owner、payload key `herdr_supportability_projection`、render keys `herdr_*` 已明确 | code review 复核实际接口名 |
| Validation and artifacts | warn | E/C | design 已定义 docs/doctor artifacts shape、fixed point 和 hash 规则；真实 artifact 需实现期生成 | implementation 必须跑 CMD-003/004/005 |

Summary: E=6, C=0, H=0, H-only core checks=none。当前 gate 基于 design/checklist evidence 通过；实现期 artifact 仍需由对应 DOD 命令证实。

## 6. Residual Risk

- Round 1 reviewer `019fb831-1b6b-72f0-90e8-7f1a11cc1133` 已完成并被本地核验消费；对应修订影响 scope guard 与 matrix→projection 契约映射，已启动完整 round 2 复审。
- Round 2 reviewer `019fb846-9aab-7022-884d-e125096ec292` 已完成并被本地核验消费；返回 0 个 blocking、3 个 important。已修复 CMD-005 正则/YAML 承载和 self-check、artifact refs 固定映射和 supported 降级规则、doctor render keys 中 install entry / Windows npm enabled 缺口。
- Round 3 reviewer `019fb84e-3646-7442-a3b7-7ea78894e541` 已完成并被本地核验消费；返回 2 个 blocking、2 个 important。已修复 CMD-005 false negative、parent/current artifact 来源漂移、doctor beta gaps/blocked workflows 追踪缺口、docs consistency artifact shape 缺口。修订影响验收语义和 artifact 契约，需启动完整 round 4 复审，不走 focused closure。round 4 reviewer `019fb856-0546-7790-8c51-1c5edfb13cac` 已启动，本报告当前只是可恢复等待状态，不代表审查通过。
- Round 4 reviewer `019fb856-0546-7790-8c51-1c5edfb13cac` 已完成并被本地核验消费；返回 1 个 blocking、2 个 important 和 1 个 nit。已修复 payload key 漂移、doctor render covers 不完整、CMD-005 new test 状态和 `support_tier_source` 表述歧义。修订影响公开 doctor payload/render 契约，需启动完整 round 5 复审，不走 focused closure。round 5 reviewer `019fb85a-a5a2-7370-bb44-9be6d2e570ca` 已启动，本报告当前只是可恢复等待状态，不代表审查通过。
- Round 5 reviewer `019fb85a-a5a2-7370-bb44-9be6d2e570ca` 已完成并被本地核验消费；返回 2 个 blocking、2 个 important。已修复 partial workflow 隐藏风险、release/install gate 只看 ref 的过弱判定、CMD-005 状态和显式 matrix path 绕过 parent acceptance 的歧义。修订影响 projection schema、doctor/docs render 契约和 supported gate，需启动完整 round 6 复审，不走 focused closure。round 6 reviewer `019fb861-f326-73c0-bec6-6650eeaddb72` 已启动，本报告当前只是可恢复等待状态，不代表审查通过。
- Round 6 reviewer `019fb861-f326-73c0-bec6-6650eeaddb72` 已完成并被本地核验消费；返回 0 个 blocking、1 个 important 和 1 个 nit。已修复 release-surface supported gate 字段绑定和摘要条件漂移。修订影响 release-surface gate 可执行性，需启动完整 round 7 复审，不走 focused closure。round 7 reviewer `019fb867-fece-77e3-a65c-637998ea8ff7` 已启动，本报告当前只是可恢复等待状态，不代表审查通过。
- Round 7 reviewer `019fb867-fece-77e3-a65c-637998ea8ff7` 已完成并被本地核验消费；返回 0 个 blocking、1 个 important。已修复 current feature docs/doctor artifacts 只看 `ok=true` 的过弱判定，要求 artifact 绑定当前 projection ref/hash 且 tier 一致。修订影响 supported gate 可执行性，需启动完整 round 8 复审，不走 focused closure。round 8 reviewer `019fb86c-5f41-7bf1-a199-6da278fe2a17` 已启动，本报告当前只是可恢复等待状态，不代表审查通过。
- Round 8 reviewer `019fb86c-5f41-7bf1-a199-6da278fe2a17` 已完成并被本地核验消费；返回 0 个 blocking、1 个 important、1 个 nit 和 1 个 suggestion。已修复 projection identity/hash 算法与 docs/doctor 两阶段固定点，且将 docs/doctor artifacts 加入 `schema_version=1`。修订影响 supported gate 可执行性，需启动完整 round 9 复审，不走 focused closure。round 9 reviewer `019fb874-b585-71a0-a096-b12e669f656c` 已启动，本报告当前只是可恢复等待状态，不代表审查通过。
- Round 9 reviewer `019fb874-b585-71a0-a096-b12e669f656c` 已完成并被本地核验消费；返回 0 个 blocking、1 个 important。已修复 final downgrade 后 `projection_hash` 必须重算的 identity 语义；修订影响 projection identity，需启动完整 round 10 复审，不走 focused closure。round 10 reviewer `019fb879-ec2a-7f63-b52c-74e9b9dd8aff` 已启动，本报告当前只是可恢复等待状态，不代表审查通过。
- Round 10 reviewer `019fb879-ec2a-7f63-b52c-74e9b9dd8aff` 已完成并被本地核验消费；返回 0 个 blocking、0 个 important、0 个 nit。保留 residual risk：当前 `docs/ccbd-diagnostics-contract.md` 仍存在未标 deprecated/unsupported 的 `doctor --bundle` 公开口径，docs guard 当前会命中第 22、662、726 行；design 第 194 行与 checklist CMD-004 已覆盖，属于 implementation 必修红灯，不是 design blocker。
- Round 13 reviewer `019fb96c-d2d2-7380-9daf-608b602688b1` 已完成并被本地核验消费；返回 0 个 blocking、0 个 important、0 个 nit、0 个 suggestion。round 12 的 `non_pass_workflows` key namespace 和 doctor/docs sorted render 缺口已关闭到可实现、可验收层面。保留 implementation residual risk：sorted render 必须覆盖 doctor/docs 所有 `non_pass_workflows` 用户可见输出，不应只覆盖 snapshot。
- Implementation residual risk：`docs-consistency.json` / `doctor-render.json` freshness 规则和 fixtures 必须覆盖旧 hash、旧 tier、错误 payload key、错误 render key；否则 supported gate 的 stale 降级不可证伪。

## 7. Verdict

- Status: passed
- Next: 回到 `cs-epic` child batch loop；该 child design 保持 `draft`，等待所有 child design-review passed 后由 epic 统一确认。

## 8. Focused Closure

- Closed findings: round 12 important：`non_pass_workflows` key namespace 缺少稳定公开 key 契约与 sorted render 要求。
- Attributed delta: 修改 design/checklist，使 `non_pass_workflows` key 固定为 `workflow:<workflow>` 与 `provider:<provider>:<workflow>`，provider id 绑定 current provider catalog / parent freeze，并要求 doctor/docs render 按 key 字典序输出；不改变实现范围，不进入代码实现，不宣称 supported。
- Verification: `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-31-herdr-supportability-projection/herdr-supportability-projection-design.md"` passed；`python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-31-herdr-supportability-projection/herdr-supportability-projection-checklist.yaml" --yaml-only` passed；`python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-31-herdr-supportability-projection/herdr-supportability-projection-design-review.md"` passed；scoped `git diff --check -- ".codestable/features/2026-07-31-herdr-supportability-projection"` passed；CMD-004 docs guard 当前命中既有 `doctor --bundle` baseline，作为实现期目标红灯保留。
- Classification: round 12 修订改变 projection/render 可比性，已完成完整独立 round 13 复审；最终复审无 blocking/important/nit/suggestion。
