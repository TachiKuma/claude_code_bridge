---
doc_type: feature-design-review
feature: 2026-07-31-windows-x64-release-surface
status: passed
review_state: passed
review_reason: ""
reviewer_id: 019fb943-43ce-7462-8744-c7df598f339c
reviewed: 2026-08-01
round: 12
---

# windows-x64-release-surface feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-31-windows-x64-release-surface/windows-x64-release-surface-design.md`
- Checklist: `.codestable/features/2026-07-31-windows-x64-release-surface/windows-x64-release-surface-checklist.yaml`
- Intent / brainstorm: none
- Roadmap: `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-roadmap.md`
- Related docs: `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml`
- Code facts checked: `package.json`, `bin/ccb.js`, `bin/ask.js`, `bin/autonew.js`, `bin/ctx-transfer.js`, `bin/ccb-npm-runner.js`, `bin/ccb-npm-install.js`, `README.md`, `docs/ccbd-diagnostics-contract.md`, `install.ps1`, `lib/cli/management_runtime/commands_runtime/update.py`, `lib/release_artifacts.py`, `lib/terminal_runtime/rmux_packaging_support.py`, `lib/terminal_runtime/rmux_packaging_support_projection.json`, doctor 相关文件

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: `019fb943-43ce-7462-8744-c7df598f339c`
- Raw output: round 12 返回 1 个 blocking：CMD-007 scope guard 未扫描 `README/*.md`，无法覆盖包内 README 子文档里的 Windows x64 final supported 文案。
- Merge policy: 已本地核验；该 finding 属于 guard 覆盖缺口，已用 focused closure 修订 design/checklist 的 CMD-007 roots。
- Gate effect: focused closure verified; final verdict passed.

## 2. Design Summary

- Goal: 建立 Windows x64 release-surface gate，让 npm/install/update/native helper/managed Python/doctor/docs 消费同一 JSON projection。
- Key contracts: Python builder + packaged JSON projection + Node/PowerShell/Python adapter；artifact route、package payload、public npm runner executable entry、upstream failure detail 和 Windows update 分支均进入 projection 契约。
- Steps: 13 个步骤，风险热点是跨语言 projection、npm payload、Node postinstall gate、PowerShell source install、Windows update 分支和 upstream dependency admission。
- Checks: checklist 当前 YAML 合法，steps/checks 均为 pending。
- Baseline / validation: 已包含 YAML 校验、projection/package/update/doctor pytest、npm pack dry-run、scope guard、manual Windows transcript、all npm bin runner mapping、docs guard 和 upstream dependency admission。

## 3. Findings

### blocking

- none

### important

- none

### nit

- none

### suggestion

- 可在实现中将 release-surface doctor payload key 命名为独立字段，例如 `windows_x64_release_surface`，避免与既有 `rmux_packaging_support` rows 混淆；该建议不阻塞 design。

### learning

- Round 8 independent reviewer 返回 3 个 important 与 1 个 nit；主 agent 已本地核验并修订 design/checklist：收紧 S5/AC-003 的 fake admitted upstream / blocked-default 边界，明确 roadmap contract refinement 需 epic owner 统一确认承接，补列 `bin/ccb.js` / `bin/ccb-npm-runner.js` public npm bin 挂载点，并将 unknown field fail closed 收窄为 required/schema/rule 层 fail closed。
- Round 9 independent reviewer 返回 2 个 important 与 1 个 nit；主 agent 已本地核验并修订 design/checklist：补齐 `failure_reason` canonical machine reason 映射，增强 CMD-007 对单/双引号 `support_tier=supported` 与 Windows x64 final supported 文案的 scope guard 覆盖。S5 暂不继续拆分，因 checklist checks/CMD covers 已能逐项回填 package envelope、postinstall host gate 与 runner executable contract。
- Round 10 independent reviewer 返回 1 个 blocking、2 个 important、1 个 nit 和 2 个 suggestion；主 agent 已本地核验并修订 design/checklist：用 `release_install_entry` / `source_install_allowed` / `source_install_entry` 拆清 release artifact gate 与 source/dev `install.ps1` 路径，保证 upstream 未 admitted 时不回归既有 source install；将 S5/S6 拆成 package metadata/payload、Node host gate、runner executable、PowerShell source adapter、Windows update rollback 等独立步骤；新增 DOD-IMPL-008/009 承接 source install preservation 与 `package.json.cpu` roadmap refinement 的 epic owner 确认；S10 显式包含旧 `doctor --bundle` 文案清理。两个 suggestion 作为实现复核重点保留，不强制扩范围。
- Round 11 independent reviewer 返回 2 个 important；主 agent 已本地核验并用 focused closure 修订 design/checklist：S7/CMD-003 覆盖 `package.json.bin` 的全部 key（`ccb`、`ask`、`autonew`、`ctx-transfer`），新增 CMD-013 focused docs guard 确保 `doctor --bundle` 只在 deprecated/unsupported 语境出现；frontmatter `requirement` 改为 `null`；补充 `terminal_runtime` owner 放置理由。
- Round 12 independent reviewer 返回 1 个 blocking；主 agent 已本地核验并用 focused closure 修订 design/checklist：CMD-007 roots 同时覆盖 `README.md` 与 `README` 目录，从而扫描 `README/*.md` 中的 Windows x64 final supported / full support / stable support 越界文案。

### praise

- 单一 JSON projection seam、strict host gate、canonical failure reason、source/dev install preservation 和 upstream dependency admission 均已形成可证伪契约。

## 4. User Review Focus

- 用户需要重点拍板：`package.json.cpu` envelope refinement 是否在 epic 统一确认中承接；该确认前不得沉淀为 roadmap/ADR 最终事实。
- implement 需要重点遵守：当前 upstream 未 admitted 且版本仍为 `8.2.1` 时只能 blocked/default projection；release route gate 不得阻断既有 `install.ps1` source/dev checkout install。
- code review / QA / acceptance 需要重点复核：all npm bin runner mapping、CMD-013 docs guard、source/dev preservation、Windows update rollback、native transcript 或 blocked evidence。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | design/checklist 覆盖 blocked-default、admitted-fixture、source/dev install preservation、all npm bin runner 和 docs guard | none |
| DoD Contract | pass | E | DOD-IMPL-001..009 覆盖 projection、admission、source preservation、owner refinement evidence 与 scope guard | owner 统一确认时复核 refinement |
| Steps and checks traceability | pass | E | checklist 可解析，13 个 steps/checks 均为 pending 且可追踪到 AC/CMD | none |
| Roadmap contract compliance | warn | E | roadmap 依赖与 `os=win32,cpu=x64` refinement 已显式写入 design/checklist，但仍需 epic owner 统一确认承接 | owner checkpoint |
| Module interface design | pass | E | JSON seam、artifact/executable fields、canonical machine reason、release/source install split 和 adapter 边界已写入 | none |
| Validation and artifacts | pass | E | YAML 校验通过，future validation commands 覆盖 projection/package/update/doctor/docs/transcript/scope | implementation 阶段执行 |

Summary: E=6, C=0, H=0, H-only core checks=none。

## 6. Residual Risk

- `package.json.cpu` 对 roadmap `os=win32,cpu=x64` 的解释是合理 refinement，但仍需要 epic owner 在所有 child design 统一确认 checkpoint 承接；design-review passed 不是最终 roadmap/ADR 批准。
- 当前 `VERSION` / `package.json` 仍是 `8.2.1`，roadmap 依赖项仍是 `in-progress`；implementation/QA/acceptance 必须预期 blocked/default projection。
- Native Windows transcript、cleanup/rollback transcript 和 Herdr/upstream evidence 仍是外部依赖；缺 host 时只能提供 blocked evidence，不能用 WSL/Linux 替代。
- Windows helper/package artifact 的真实命名与 checksum contract 仍需 implementation/code review 核对 `release_artifacts.py` 与 packaged JSON freshness gate 是否为唯一事实源。

## 7. Verdict

- Status: passed
- Next: 回到 `cs-epic` child design batch；不要在单个 child 停下请求用户确认，等待所有 child design-review passed 后统一确认。

## 8. Focused Closure

- Closed findings: round 11 FDR-I01、FDR-I02、FDR-N01、round 12 FDR-B01。
- Attributed delta: 仅修改 `.codestable/features/2026-07-31-windows-x64-release-surface/windows-x64-release-surface-design.md` 与 checklist 的验收映射、future validation command、frontmatter 空值、owner 放置说明，以及 CMD-007 的 `README` 目录扫描 roots；不改变行为范围、公开支持范围或架构 ownership。
- Verification: `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-31-windows-x64-release-surface/windows-x64-release-surface-design.md"` passed；`python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-31-windows-x64-release-surface/windows-x64-release-surface-checklist.yaml" --yaml-only` passed；`python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml"` passed；CMD-007 scope guard passed；`git diff --check -- ".codestable/features/2026-07-31-windows-x64-release-surface"` passed；本地核验 `package.json.bin`、`doctor --bundle` 代码/文档事实与 `README/*.md` guard 覆盖。
- Classification: round 12 修订只把已有 support-claim guard 扩展到同一发布文档集合下的 README 子文档，不改变行为、公开契约、架构边界、验收语义或范围，因此不启动 round 13。
