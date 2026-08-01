---
doc_type: feature-design-review
feature: 2026-07-20-rmux-packaging-docs-contracts
status: passed
review_state: passed
review_reason: ""
reviewer_id: "019f7cd6-7e7d-7781-b9c9-b2f0db317481"
reviewed: 2026-07-20
round: 1
---

# rmux-packaging-docs-contracts feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-20-rmux-packaging-docs-contracts/rmux-packaging-docs-contracts-design.md`
- Checklist: `.codestable/features/2026-07-20-rmux-packaging-docs-contracts/rmux-packaging-docs-contracts-checklist.yaml`
- Intent / brainstorm: none
- Roadmap: `.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-roadmap.md`、`.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml`
- Related docs: `rmux-windows-validation-matrix` child design、README/install/diagnostics/package facts
- Code facts checked:
  - `package.json`
  - `install.ps1`
  - `install.sh`
  - `README.md`
  - `docs/ccbd-diagnostics-contract.md`
  - `bin/ccb-npm-install.js` facts from reviewer

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: `019f7cd6-7e7d-7781-b9c9-b2f0db317481`
- Raw output: 首轮 `changes-requested`，提出 6 个 important、1 个 nit、1 个 suggestion；focused closure 后 verdict `passed`
- Merge policy: 主 agent 已核验 design/checklist 和 reviewer findings，修订后由同一 reviewer 做 focused closure
- Gate effect: 独立 reviewer completed + closure verified；允许定稿 `passed`

## 2. Design Summary

- Goal: 将 Windows Rmux 后端的安装、打包、诊断和文档契约收口为明确 `blocked/experimental/beta/supported` 支持档，并区分 npm 与 `install.ps1` 入口。
- Key contracts: support projection 单一 owner；supported 必须消费 validation matrix 机器字段 `selection_scope=full`、`full_matrix_status=pass`、true-host/manual core rows observed；Windows npm gate 需 `artifactForHost` win32、artifact/checksum、postinstall、package files/docs strategy。
- Steps: 8 个步骤，覆盖 support projection/classifier、diagnostics projection、install.ps1 contract、npm packaging gate、README/docs sync、troubleshooting、release guard、acceptance evidence pack。
- Checks: 10 项检查，覆盖 support tier、validation gate、installer behavior、npm gate、diagnostics fields、docs consistency、troubleshooting、release safety。
- Baseline / validation: YAML 校验、support projection tests、installer snapshots、diagnostics snapshots、conditional npm pack check、release guard、docs parser/snapshot consistency gate。

## 3. Findings

### blocking

none

### important

none

### nit

none

### suggestion

none

### learning

- 此类收口 feature 的关键是把 support tier 做成证据投影对象；README、installer、doctor、package 都只是消费者，不能各自发明承诺。

### praise

- design 没有过早承诺 Windows npm 或 supported，且将 `win32` 与 postinstall/artifact/checksum/package files/docs strategy 绑定。
- 发布动作边界清楚：明确不做 npm publish、push、tag、release upload。
- `install.ps1` 与 npm 路线分开建模，`install.sh` 保持 Linux/macOS/WSL tmux 路线，不混入 native Windows Rmux。

## 4. User Review Focus

- 用户需要重点拍板：最终 support tier 取决于 route/capability/validation/package evidence；本 design 不授权发布或默认启用 Rmux。
- implement 需要重点遵守：support projection 必须是单一 owner；subset validation 不能打开 supported；Windows npm 不能只改 `package.json.os`。
- code review / QA / acceptance 需要重点复核：docs parser gate、package no-change rationale 或 npm gate evidence、install.ps1 不自动下载 rmux、release guard。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | design §3.1 / §3.3 覆盖 AC-001 至 AC-009 | none |
| DoD Contract | pass | E | design §3.4 覆盖 Design / Implementation / Review / QA / Acceptance DoD 与 validation commands | none |
| Steps and checks traceability | pass | E | checklist steps/checks 对应 design §2.4、§3.1、§3.4；YAML 校验通过 | none |
| Roadmap contract compliance | pass | E | roadmap item `rmux-packaging-docs-contracts` 要求 installer/package/docs/contracts 收口并区分 npm 与 install.ps1 | none |
| Module interface design | pass | C | reviewer 核验 package/install/docs facts；design 已补 support projection owner 和 consumer contract | implementation 需按现有模块边界选择落点 |
| Validation and artifacts | pass | E | checklist `dod.commands` 覆盖 support projection、installer、diagnostics、docs parser、release guard、conditional npm gate | none |

Summary: E=5, C=1, H=0, H-only core checks=none。

## 6. Residual Risk

- 前序 `rmux-windows-validation-matrix`、route approval、supervision/recovery 仍处于 draft/in-progress；本 feature 只能 fail-closed 消费这些证据，不能替代它们。
- `docs/ccbd-diagnostics-contract.md` 仍偏 tmux-heavy；实现时若 diagnostics 字段改动超过本 design 预期，需在 implementation/review 阶段收紧 contract diff。

## 7. Verdict

- Status: passed
- Next: 返回 `cs-epic` child design batch loop；本 child design 保持 `draft`，等待所有 child design-review 通过后由 epic 统一确认。

## 8. Focused Closure

- Closed findings: FDR-I01、FDR-I02、FDR-I03、FDR-I04、FDR-I05、FDR-I06、FDR-N01、FDR-S01
- Attributed delta: `.codestable/features/2026-07-20-rmux-packaging-docs-contracts/rmux-packaging-docs-contracts-design.md`、`.codestable/features/2026-07-20-rmux-packaging-docs-contracts/rmux-packaging-docs-contracts-checklist.yaml`
- Verification: reviewer `019f7cd6-7e7d-7781-b9c9-b2f0db317481` focused closure verdict `passed`；checklist YAML 与 roadmap items YAML 校验通过
- Classification: 修订只关闭 reviewer 提出的 validation machine fields、support tier enum、projection owner、npm gate、docs consistency gate、packaging smoke、install enum 和 evidence pack 机器索引问题；未修改生产代码、未改变 feature 范围、未授权发布动作
