---
doc_type: feature-brainstorm
feature: 2026-07-25-windows-rmux-supportability-parity-contract
status: confirmed
summary: Windows/rmux supportability parity 采用 UX parity overlay first，只消费 base support projection 与 5 个上游 UX parity evidence JSON，并输出第 6 维 supportability evidence
tags: [windows, rmux, wezterm, supportability, doctor, diagnostics, docs, parity, evidence]
---

# Windows Rmux Supportability Parity Contract Brainstorm

> Stage 0 | 2026-07-27 | 下一步：cs-feat（由主入口选择 lane）

## 想做什么、为什么

当前 roadmap 要求 `windows-rmux-supportability-parity-contract` 在 design 前单独完成 `$cs-brainstorm`。这个 item 的真实问题不是“再做一套 packaging/install 支持系统”，而是当用户运行 `ccb doctor`、导出 diagnostics bundle、阅读 install/docs/support 状态时，系统能否基于 Windows/rmux/WezTerm UX parity evidence 一致说明：当前是 `beta`、`supported`、`blocked` 还是只能 fallback。

已有 baseline 已经存在：

- `lib/terminal_runtime/rmux_packaging_support.py` 定义 `RmuxPackagingSupport` 和 `rmux_packaging_support_summary()`，负责 base support projection。
- `lib/terminal_runtime/rmux_packaging_support_projection.json` 存放 packaged fallback projection。
- `lib/cli/services/doctor.py` 把 `rmux_packaging_support_summary()` 纳入 doctor payload。
- `lib/cli/render_runtime/ops_views_doctor.py` 已展示 `rmux_support_tier`、`rmux_version`、`rmux_capability_status`、`rmux_validation_ref`、`windows_install_entry`、`windows_npm_enabled`、`windows_install_ps1_rmux_check`、`rmux_fallback_guidance`。
- `test/test_rmux_packaging_docs_contracts.py`、`test/test_cli_doctor_rmux_packaging.py`、`test/test_ccbd_diagnostics_bundle_rmux.py`、`test/test_rmux_docs_consistency_gate.py`、`test/test_install_windows_rmux_contract.py` 已覆盖 base tier、doctor、diagnostic bundle、docs consistency 和 `install.ps1` rmux prerequisite check。

因此本 item 的增量应放在 UX parity overlay：只消费 5 个上游 child feature 的 `evidence/windows-rmux-ux-parity-evidence.json`，将 `foreground_interaction`、`output_capture`、`pane_identity_layout`、`visual_no_popup`、`lifecycle_recovery` 投影为一致的 supportability contract，并由本 item 输出第 6 维 `supportability` evidence，明确缺失、partial、blocked、failed 如何影响用户可见承诺。

## 考虑过的方向

### 方向 A：UX parity overlay first

- 描述：在现有 base support projection 上叠加 UX parity evidence，生成 supportability projection 和 doctor/diagnostics/docs 一致表达。base projection 负责 packaging/install/npm/docs gate；overlay 负责 UX parity dimensions 和 residual risks。
- 价值：单一职责清楚，避免 README、installer、doctor、support tier 各自发明状态；缺失 core dimension 可 fail closed。
- 代价：不能绕过 base projection 直接把 Windows/rmux 宣称为 supported；如果 UX evidence 全绿但 local install 或 docs gate 缺失，最终支持档仍受 base projection 限制。
- 结论：选定。

### 方向 B：support tier rewrite

- 描述：本 item 重新定义 support tier、install entry、npm win32、`install.ps1` check 和 docs/release gate。
- 价值：把所有用户可见支持承诺放在一个 feature 里，看起来更集中。
- 代价：与 `rmux-packaging-docs-contracts` 双 owner，容易让 package metadata、install.ps1、doctor 和 docs 漂移；还可能误授权 npm win32 发布。
- 结论：否决。

### 方向 C：docs-only consistency

- 描述：只更新 docs/runbook，把 UX parity 状态写进 Markdown。
- 价值：范围最小。
- 代价：doctor/diagnostics 和机器 gates 无法消费，缺失维度无法可靠投影为 `missing`。
- 结论：否决；docs 必须由 projection 驱动，不能反过来靠 docs 推导支持状态。

## 已敲定的设计点

- 已确认：本 item 采用 **UX parity overlay first**。
- 已确认：唯一公开消费接口是每个 child 的 `evidence/windows-rmux-ux-parity-evidence.json`；child 私有 report 只能作为 artifact ref。
- 已确认：必须消费 5 个上游 UX dimensions：`foreground_interaction`、`output_capture`、`pane_identity_layout`、`visual_no_popup`、`lifecycle_recovery`；本 feature 自身生成第 6 个 `supportability` evidence。
- 已确认：缺失 core dimension 投影为 `missing`；不得用 acceptance Markdown、design review 摘要或口头结论替代。
- 已确认：任一 core dimension 为 `failed|blocked|missing` 时不得宣称 `supported`。
- 已确认：`partial` 可以允许 `beta`，但 doctor/docs/diagnostics 必须列 residual risks 和 fallback guidance。
- 已确认：base projection 是上限约束；UX overlay 不得把 support tier 提升到 base projection 不允许的档位。
- 已确认：不重复定义 npm、`install.ps1`、release guard，不单独授权 npm 发布。
- 已确认：owner 已批准本 brainstorm 结论，并允许进入 feature design。

## 选定方向与遗留问题

选定方向是 `windows-rmux-supportability-parity-contract`：建立 Windows/rmux UX parity supportability overlay，读取 base support projection 和各 child UX evidence JSON，生成 supportability parity report，并把结果一致投影到 doctor/diagnostics/docs。

核心行为：

- 汇总 5 个上游 child 的 `windows-rmux-ux-parity-evidence.json`，并输出本 feature 的 supportability evidence。
- 对每个 dimension 计算 `pass|partial|blocked|failed|missing`。
- 用 base projection 和 UX overlay 共同推导最终 supportability result，且最终 tier 不能高于 base projection 允许值。
- doctor/diagnostics/docs 展示相同的 parity dimensions、residual risks、validation refs 和 fallback guidance。

明显不做：

- 不修改 npm win32 发布规则。
- 不重新定义 `install.ps1` prerequisite check。
- 不修改 release guard 或远端发布流程。
- 不读取 child 私有 report 作为公开 contract；只允许通过 UX evidence 的 `artifacts` 追溯。

遗留给 design 的问题：

- supportability 自身的 `parity_dimension=supportability` evidence 是否由本 feature acceptance 生成，并引用 overlay report。
- doctor 输出是否新增独立 `rmux_ux_parity_*` 字段，还是扩展 `rmux_packaging_support` payload。
- docs consistency gate 应覆盖 README、support contract、install runbook、diagnostics contract 中哪些字段。
