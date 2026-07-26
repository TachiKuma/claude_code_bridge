---
doc_type: feature-brainstorm
feature: 2026-07-26-windows-rmux-supportability-parity-contract
status: confirmed
summary: Windows/rmux supportability 采用 evidence aggregation first，把 UX parity evidence 聚合为 fail-closed support projection
tags: [windows, rmux, supportability, diagnostics, doctor, docs, support-tier, parity, evidence]
---

# Windows Rmux Supportability Parity Contract Brainstorm

> Stage 0 | 2026-07-26 | 下一步：cs-feat（由主入口选择 lane）

## 想做什么、为什么

当前 `windows-rmux-ux-parity-hardening` epic 已把前台交互、output/capture、pane identity/layout、visual/no-popup、lifecycle/recovery 五个 UX parity 维度推进到 draft design + passed design-review。最后一个 item `windows-rmux-supportability-parity-contract` 的问题不是继续实现某条 UX 能力，而是把这些维度的机器证据转成用户遇到问题时能看懂、系统能自证的 supportability projection。

roadmap 已经给出两个硬边界：

- 每个 child feature 必须产出 `evidence/windows-rmux-ux-parity-evidence.json`；supportability item 缺少某个 core dimension JSON 时必须投影为 `missing`，不能凭口头 QA 摘要推导支持档。
- `rmux-packaging-docs-contracts` 是 base support projection、npm gate、`install.ps1` gate 和 release guard 的单一 owner；本 item 只能消费其最终 projection，再叠加 UX parity overlay。

现有 baseline 显示 `rmux-packaging-docs-contracts` 已 accepted/done：support projection、`install.ps1` rmux check、doctor/diagnostics 字段、README/docs contract、release guard 与 evidence pack 已交付；当前支持档为 beta，Windows npm 未启用，native Windows 入口为 `install.ps1` / source opt-in。这个 feature 要做的是在该 base projection 上增加 UX parity overlay，而不是重新授权 npm、发布或 installer 策略。

## 考虑过的方向

### 方向 A：Evidence aggregation first

- 先建立 support projection aggregator：读取前 5 个 upstream parity feature 的 `windows-rmux-ux-parity-evidence.json`，校验 schema、dimension、status/failure/residual risk、artifact refs 和 native Windows / WezTerm / rmux / ccbd 固定字段；本 feature 再输出第 6 个 supportability evidence。
- 再消费 `rmux-packaging-docs-contracts` 的 base projection，叠加 UX parity dimensions，产出 support tier、doctor/diagnostics summary、docs consistency gate 和 fallback guidance。
- 缺失 evidence 投影为 `missing`；任一 core dimension `failed|blocked` 不得宣称 `supported`；`partial` 只能进入 beta 并列 residual risks；Windows npm 仍按 base projection 保持未启用，除非 base owner 已改变。
- 价值：support tier 由机器证据推导，能 fail closed，避免 README、doctor、installer 各自发明支持状态。
- 代价：如果前置 child feature 还没有 acceptance evidence，本 item 可能只能产出 overlay classifier 和 missing/partial projection，不能把整体支持档推高。
- 结论：选定。owner 已回复 `1`，批准采用该方向进入 design。

### 方向 B：Doctor/docs first

- 先改善用户可见 doctor、diagnostics 和文档说明，把 Windows/rmux 当前状态解释清楚。
- 价值：用户感知改善最快，能减少误用和支持成本。
- 代价：若没有 evidence aggregator，doctor/docs 很容易绕过 roadmap §4.1 的 JSON gate，自行声明 beta/supported/blocked，导致后续验收不可证伪。
- 结论：否决第一版默认方向；doctor/docs 是方向 A 的投影输出，不是事实源。

### 方向 C：Installer/npm first

- 直接推进 Windows npm entry、install.ps1 或 package metadata。
- 价值：对外入口最明显。
- 代价：roadmap 明确 `rmux-packaging-docs-contracts` 拥有 npm、`install.ps1`、release guard；本 item 若直接改这些入口，会重复 owner 边界并绕过 base support projection。
- 结论：否决。本 item 不发布 npm、不改 release guard、不单独授权 Windows npm。

## 已敲定的设计点

- 已确认：本 item 采用 **Evidence aggregation first**。
- 已确认：supportability projection 的输入是 6 个 child feature 的 `evidence/windows-rmux-ux-parity-evidence.json`，不是自由 Markdown QA 摘要。
- 已确认：缺失 core dimension 投影为 `missing`，不能靠 headless、docs 或口头结果推断为 pass。
- 已确认：任一 core dimension `failed|blocked` 时不得宣称 `supported`；`partial` 可以进入 beta，但 doctor/docs 必须列 residual risks。
- 已确认：`rmux-packaging-docs-contracts` 的 base projection 是下游输入；本 item 不重复定义 npm、`install.ps1`、release guard 或 publish gate。
- 已确认：Windows npm 当前仍未启用；本 item 不单独改变该状态。
- 已确认：最终应产出机器可读 UX support projection，并让 doctor/diagnostics/docs consistency gate 从该 projection 读取状态。
- 已确认：owner 已批准本 brainstorm 结论，并允许进入 feature design。

## 选定方向与遗留问题

选定方向是 `windows-rmux-supportability-parity-contract`：建立 Windows/rmux UX supportability overlay，把 6 个 parity dimensions 的 evidence JSON 与 base packaging/docs support projection 聚合成 fail-closed support projection，并把结果投影到 doctor、diagnostics、docs consistency 和 fallback guidance。

核心行为：

- 读取并校验前 5 个 upstream UX parity evidence JSON，缺失维度显式标记 `missing`；supportability 自己的 `parity_dimension=supportability` evidence 是本 feature 的输出，不作为输入。
- 读取 `rmux-packaging-docs-contracts` 的 base support projection / acceptance evidence，继承 beta、Windows npm 未启用、`install.ps1` / source opt-in 等 base 事实。
- 生成 `windows-rmux-ux-support-projection.json` 或等价机器可读 artifact，包含 support tier、parity dimensions、validation refs、install entry、fallback guidance 和 residual risks。
- 给 doctor/diagnostics/docs consistency 提供单一 projection 输入，避免各处重复实现支持状态判断。

明显不做：

- 不发布 npm、不 push/tag/release、不做生产环境动作。
- 不修改 release guard owner，不单独授权 Windows npm。
- 不重做 `rmux-packaging-docs-contracts` 已 accepted 的 base installer/package/docs contract。
- 不把真实 provider auth、quota、credential failure 归为 Windows/rmux UX parity failure。
- 不用自由 Markdown 替代机器 evidence projection。

遗留给 design 的问题：

- support projection artifact 的确切 schema 是否扩展 roadmap §4.7 `WindowsRmuxUxSupportProjection`，还是另建 wrapper 保留 base projection refs。
- 6 个 parity dimensions 的缺失、partial、blocked、failed 如何汇总成 `experimental|beta|supported|blocked` 的 deterministic rule。
- doctor/diagnostics/docs 是否在第一版直接修改 production 投影，还是先生成 feature-local projection + consistency tests，只有 broken/missing wiring 被证实时最小接入。
- 当前前置 child feature 只有 design-review passed、尚未 acceptance 时，supportability implementation 应如何 fail closed 为 `missing|partial`，同时允许 overlay classifier 先落地。
