---
doc_type: roadmap
slug: windows-rmux-ux-parity-hardening
status: active
created: 2026-07-25
last_reviewed: 2026-07-25
tags: [windows, rmux, wezterm, ux-parity, hardening, terminal-runtime]
related_requirements: []
related_architecture:
  - .codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-roadmap.md
  - .codestable/brainstorms/windows-rmux-ux-parity-hardening/brainstorm.md
---

# Windows Rmux UX Parity Hardening

## 1. 背景

`windows-rmux-native-backend` 已把 native Windows + WezTerm + rmux 路线推进到 `ccb -> ccbd -> rmux` 基本可跑通，并用 validation matrix / full-chain smoke 证明核心链路。下一阶段的问题不再是“能不能起”，而是 Windows/rmux/WezTerm 是否能达到 Linux/macOS tmux 路线的日用体验：前台交互、输出回看、pane 身份、视觉状态、重连恢复、诊断安装都要可验证。

近期真实使用已经暴露多类体验缺口：Git Bash 弹窗、鼠标滚轮无法回看、右键粘贴被 rmux buffer 劫持、pane 点击需要双击、文本选区错位、pane id target alias 导致 layout 绑定错误等。这些不是单个 bug 的同类重复，而是“tmux-like 语义迁移到 Windows/rmux/WezTerm GUI”时需要统一管理的 parity hardening 工作。

本 roadmap 的目标是把 `.codestable/brainstorms/windows-rmux-ux-parity-hardening/brainstorm.md` 中的 6 个讨论点升级为统一规划层：每个维度成为可独立推进、可验收、可回写的子 feature，并共享同一套 UX parity evidence contract。

## 2. 范围与明确不做

### 本 roadmap 覆盖

- 前台交互 parity：鼠标、键盘、剪贴板、滚轮、pane focus、sidebar 交互。
- 历史与输出 parity：scrollback、capture、provider completion capture、ANSI / wrapping / 宽字符保真。
- pane identity / layout parity：pane id、pane index、split 后 canonicalization、layout 重建和 agent 绑定恢复。
- 视觉与无干扰 parity：状态栏、标题、边框、动态状态、无 Git Bash / console 弹窗。
- 生命周期 parity：attach/reconnect、关闭 WezTerm 后继续存活、kill/recovery、pane/provider/rmux daemon crash 后恢复或 degraded diagnostics。
- 可支持性 parity：doctor/diagnostics、install.ps1、npm win32、support tier、runbook、错误分类。

### 明确不做

- 不替代 `windows-rmux-native-backend` 的 mux/backend/control-plane 基础路线；本 roadmap 建立在其已完成或进行中的能力之上。
- 不把 Rmux 设为 Linux/macOS 默认后端。
- 不恢复旧 WezTerm backend，不把 WezTerm 当 mux authority；WezTerm 仍是 GUI 宿主终端。
- 不把真实 provider auth / quota / credential failure 归为 Windows/rmux parity failure。
- 不发布 npm、不 push/tag/release；support tier 只能由后续 evidence gate 推导。
- 不在本 roadmap 中一次性实现所有模式开关；交互 feature 第一版已选择 GUI-native 默认，不加 `transparent | tmux_like | hybrid` 配置。
- 不重复定义 `rmux-packaging-docs-contracts` 已经承担的 base support projection、npm gate 或 `install.ps1` gate；本 roadmap 的 supportability 只消费/扩展其最终投影，增加 UX parity overlay。

### Granularity Gate

| 判断项 | 结论 |
|---|---|
| 为什么不是 single feature | 6 个 parity 维度横跨 UI mouse binding、backend capture、pane identity、theme/status hooks、supervision/recovery、doctor/install/docs，多条可独立设计和验收。 |
| 为什么不是 brainstorm | 已经明确目标：把“基本跑通”升级为“日用体验可验证 parity”；6 个维度和优先级已在 brainstorm 中收敛。 |
| roadmap 边界 | 只管理 Windows/rmux/WezTerm UX parity hardening，不重做底层 mux backend，不改 Linux/macOS 默认路径。 |
| 最小闭环 | `windows-rmux-wezterm-native-interaction-parity` 完成后，普通 pane 不再被 CCB/rmux 鼠标绑定劫持，sidebar 仍可用，用户能在 WezTerm 前台获得第一条日用体验闭环。 |

### Design 前置 Brainstorm Gate

每一项子 feature 在创建或实质更新 design 之前，必须先使用 `$cs-brainstorm` 与 owner 完成针对该 item 的充分深入讨论，并获得 owner 对 brainstorm 结论和进入 design 的明确批准/通过。roadmap 总体 brainstorm 只能作为规划输入，不能替代子 feature 自身的 design admission。

准入要求：

- brainstorm 必须围绕该 item 的真实用户问题、候选方向、明显不做、baseline reuse / delta、最大未知和 design admission 展开；不能只复制 roadmap 条目。
- brainstorm 记录必须体现 AI 质疑、替代方案、owner 回答和最终收敛结论。
- confirmed feature brainstorm 落点为 `.codestable/features/YYYY-MM-DD-{feature-slug}/{feature-slug}-brainstorm.md`，frontmatter 必须包含 `doc_type: feature-brainstorm` 与 `status: confirmed`。
- design frontmatter 或 design 正文必须引用该 brainstorm 路径，并记录 owner 已批准/通过进入 design。
- `.codestable/roadmap/windows-rmux-ux-parity-hardening/windows-rmux-ux-parity-hardening-items.yaml` 中对应 item 必须回填 `brainstorm_required: true`、`brainstorm`、`brainstorm_status` 与 `design_admission`；`brainstorm_status` 非 `confirmed` 时不得启动 design。
- 已经先行进入 design 的 item 不得绕过本 gate；若缺少 confirmed brainstorm 或 design 未引用该 brainstorm，继续实现前必须补齐确认记录和引用。

状态枚举：

- `brainstorm_status` 只允许 `pending | confirmed`。
- `design_admission` 只允许 `blocked_until_owner_brainstorm_approval | admitted`。
- `design_admission: admitted` 必须同时满足：`brainstorm_required: true`、`brainstorm_status: confirmed`、`brainstorm` 指向存在的 feature brainstorm、该 brainstorm frontmatter 为 `doc_type: feature-brainstorm` / `status: confirmed`，且 design frontmatter 或正文引用该 brainstorm 并记录 owner 已批准/通过进入 design。
- `$cs-brainstorm` 完成后，只有 owner 明确批准/通过进入 design，才能把对应 item 从 `brainstorm_status: pending` / `design_admission: blocked_until_owner_brainstorm_approval` 更新为 `brainstorm_status: confirmed` / `design_admission: admitted`。

## 3. 模块拆分（概设）

```
windows-rmux-ux-parity-hardening
├── Foreground Interaction：普通 pane GUI-native，sidebar 全接管
├── Output And Capture：用户可见历史与机器 capture 分层保真
├── Pane Identity And Layout：pane 身份、target canonicalization、layout 恢复
├── Visual No-Popup Surface：状态栏、边框、标题、无弹窗动态状态
├── Lifecycle And Recovery UX：attach/reconnect、kill、crash recovery、degraded diagnostics
└── Supportability Contract：doctor/install/support tier/docs consistency
```

### Foreground Interaction · 前台交互

- **职责**：定义 Windows/rmux/WezTerm 下普通 pane 的 GUI-native 行为和 sidebar 的 CCB-owned mouse/key 行为。
- **承载的子 feature**：`windows-rmux-wezterm-native-interaction-parity`
- **触碰的现有代码 / 模块**：`lib/cli/services/tmux_ui_runtime/service.py`、`test/test_v2_tmux_ui.py`、`tools/ccb-agent-sidebar/src/tui.rs`
- **Depth 判断**：deep。它把多层 mouse event 兼容复杂度集中在 project UI binding owner，而不是散到 rmux backend、ccbd namespace 和 sidebar TUI。

### Output And Capture · 历史与输出

- **职责**：验证用户可见历史、后端 capture、provider completion parser 之间的边界；覆盖 ANSI、宽字符、wrapping、尾部空白和 scrollback/capture 差异。
- **承载的子 feature**：`windows-rmux-output-capture-parity`
- **触碰的现有代码 / 模块**：`lib/terminal_runtime/rmux_backend_runtime/*`、provider completion fixtures、capture/logging tests、validation artifacts。
- **Depth 判断**：deep。provider completion 和人工回看都依赖输出保真，但它们不应复用用户滚轮路径。

### Pane Identity And Layout · pane 身份与布局

- **职责**：系统性收口 pane id、pane index、split 返回值、target canonicalization、agent 与 pane 绑定、layout 重建和重启恢复。
- **承载的子 feature**：`windows-rmux-pane-identity-layout-parity`
- **触碰的现有代码 / 模块**：`lib/terminal_runtime/rmux_backend_runtime/targets.py`、`panes.py`、`lib/ccbd/services/project_namespace_runtime/backend.py`、layout/materialize tests。
- **Depth 判断**：deep。身份错误会污染交互、capture、recovery 和 diagnostics，必须集中在 canonicalization / namespace adapter 层。

### Visual No-Popup Surface · 视觉与无干扰表面

- **职责**：恢复或替代 Windows/rmux 下被禁用的动态状态，同时保证无 Git Bash / console popup；覆盖状态栏、标题、边框、Git 分支、ccbd health 和 resize/border hook。
- **承载的子 feature**：`windows-rmux-visual-no-popup-parity`
- **触碰的现有代码 / 模块**：`lib/cli/services/tmux_ui_runtime/service.py`、theme renderer、status/border scripts、Windows-safe hidden execution / diagnostics。
- **Depth 判断**：medium/deep。动态状态是用户可见 polish，但不能把 shell popup 风险散到每个 status hook。

### Lifecycle And Recovery UX · 生命周期体验

- **职责**：验证关闭 WezTerm 后 namespace/provider 继续存活、重新 `ccb` attach、`ccb kill` 清理、pane/provider/rmux daemon crash 后恢复或明确 degraded。
- **承载的子 feature**：`windows-rmux-lifecycle-recovery-ux-parity`
- **触碰的现有代码 / 模块**：`lib/ccbd/*`、rmux daemon ownership、project namespace lifecycle、validation runbook、diagnostics bundle。
- **Depth 判断**：deep。它跨 authority、process/job evidence、rmux daemon evidence 和 UI attach，是日用可靠性的核心。

### Supportability Contract · 可支持性契约

- **职责**：把 parity evidence 转化为 doctor/diagnostics/install/support tier/docs 的一致承诺；明确 beta/supported/blocked 和 fallback 指引。
- **承载的子 feature**：`windows-rmux-supportability-parity-contract`
- **触碰的现有代码 / 模块**：`doctor` / diagnostics bundle、`install.ps1`、`package.json` / npm gate、README / docs、support projection。
- **Depth 判断**：deep。它是用户遇到问题时系统能否自证的入口，不能由 README、installer、doctor 各自发明状态。

## 4. 模块间接口契约 / 共享协议（架构层详设）

### 4.1 UX parity evidence record

**方向**：各 parity feature → roadmap acceptance / diagnostics / supportability
**形式**：QA/acceptance artifact schema。每个子 feature 必须在自身 feature 目录下产出 JSON 证据文件：

```text
.codestable/features/YYYY-MM-DD-{feature-slug}/evidence/windows-rmux-ux-parity-evidence.json
```

QA/acceptance 正文可以摘要该 JSON，但不能用自由 Markdown 表格替代机器可读证据。子 feature checklist 必须包含 JSON 校验步骤：至少解析 JSON，校验 required fields、enum 值、`schema_version=1`、`parity_dimension` 与 item 对应；当 `evidence_status=partial|blocked|failed` 时，`residual_risks` 或 failure detail 必须非空。

**契约**：

```python
class WindowsRmuxUxParityEvidence(TypedDict):
    schema_version: Literal[1]
    host_kind: Literal["native_windows"]
    terminal_host: Literal["wezterm"]
    backend_impl: Literal["rmux"]
    control_plane: Literal["ccbd"]
    parity_dimension: Literal[
        "foreground_interaction",
        "output_capture",
        "pane_identity_layout",
        "visual_no_popup",
        "lifecycle_recovery",
        "supportability",
    ]
    evidence_status: Literal["pass", "partial", "blocked", "failed"]
    failure_class: Literal[
        "none",
        "rmux_unavailable",
        "wezterm_gui_unavailable",
        "provider_failure",
        "system_failure",
        "test_design_failure",
        "unsupported_capability",
    ]
    artifacts: dict[str, str]
    residual_risks: list[str]
```

**约束**：

- `host_kind=native_windows` 不能用 WSL / MSYS / Linux/macOS 证据替代。
- `terminal_host=wezterm` 是本 roadmap core；Windows Terminal 或 headless transcript 只能作为 supporting evidence。
- `provider_failure` 不得降级为 rmux/system failure；真实 provider auth/quota 只影响 provider lane。
- `partial` 必须写 residual risk；`blocked` 必须写具体 failure_class。
- supportability item 只能消费上述 JSON evidence；缺失某个 core dimension 的 JSON 时，该维度投影为 `missing`，不得凭口头 QA 摘要推导支持档。

**Interface 设计检查**：

- Module / interface：各 feature 的 QA/acceptance 输出必须能投影成上述 evidence record。
- Seam placement：seam 放在 feature QA/acceptance artifact，不强迫生产代码引入新 schema。
- Depth / locality：共同字段让 supportability feature 能消费所有维度证据，避免每个 feature 自定义通过口径。
- Dependency strategy：local-substitutable；单元测试可用 fixture records。
- Adapter：无 production adapter；这是证据协议。

**Baseline reuse / delta**：

- 本 evidence record 不重做 `windows-rmux-native-backend` 已验收的 base backend evidence；它记录 UX parity 维度的增量证据和差异归因。
- 旧 feature acceptance、validation matrix、capture fixtures 可作为 baseline ref 写入 `artifacts`，但不能替代本 roadmap 要求的 native Windows + WezTerm + rmux UX evidence。

### 4.2 Foreground interaction policy

**方向**：Foreground Interaction → Visual / Capture / Lifecycle features
**形式**：稳定 UX policy

**契约**：

```text
ordinary_pane.mouse_policy = gui_native
ordinary_pane.left_click = focus_only
ordinary_pane.right_click = host_clipboard
ordinary_pane.wheel = host_or_app_scroll
ordinary_pane.history_entry = none_in_v1
sidebar.mouse_policy = ccb_owned
sidebar.close_action = KillProject
```

**约束**：

- 普通 pane 不应被后续 feature 重新绑定到 `copy-mode -e`、`paste-buffer -p` 或裸 `send-keys -M`，除非先更新本 roadmap / ADR。
- sidebar 是唯一默认 mouse passthrough 例外。
- backend capture / provider completion 不依赖用户滚轮行为。

### 4.3 Output/capture parity contract

**方向**：Output And Capture → Provider Runtime / Validation / Supportability
**形式**：capture fixture + semantic report

**契约**：

```python
class RmuxCaptureParityCase(TypedDict):
    case_id: str
    input_kind: Literal["plain_text", "ansi", "wide_char", "wrapped_line", "provider_completion"]
    expected_text_sha256: str
    capture_command: str
    normalized_output_sha256: str
    raw_artifact: str
    verdict: Literal["pass", "partial", "failed"]
```

**约束**：

- 原始输出和 normalized 输出都要保留 artifact ref。
- provider completion case 必须证明 parser 看到的文本与 Linux/macOS tmux baseline 等价或明确记录差异。
- 用户 scrollback 手工体验是 supporting evidence，不能替代 capture fixture。

**Baseline reuse / delta**：

- 复用 `rmux-send-capture-logging` 已 accepted 的 Rmux `capture_pane`、raw bytes、ANSI mode、trim policy 和 provider completion fixture 结论作为 baseline。
- 本 item 的增量只覆盖 UX parity 需要的 scrollback/capture 分层、跨平台 baseline 刷新、宽字符/wrapping/尾部空白差异归因；发现生产缺口时再在 feature design 中转为实现任务，不默认重写 Rmux IO 层。

### 4.4 Pane identity/layout parity contract

**方向**：Pane Identity And Layout → Foreground Interaction / Lifecycle / Diagnostics
**形式**：canonical pane ref + layout snapshot

**契约**：

```python
class WindowsRmuxPaneIdentitySnapshot(TypedDict):
    backend_impl: Literal["rmux"]
    session_name: str
    window_name: str
    pane_id: str
    pane_index: int
    ccb_role: str
    ccb_agent_id: str | None
    canonicalization_source: Literal["exact_pane_id", "index_alias", "layout_state", "runtime_authority"]
```

**约束**：

- exact pane id 优先；index alias 只能作为 fallback，且必须记录 source。
- split / respawn / reattach 后 snapshot 必须能重新关联 agent 与 pane。
- diagnostics 中如果存在 identity conflict，必须 fail closed，不得把同一 agent 绑定到多个 active pane。

**Baseline reuse / delta**：

- 复用 `rmux-backend-core`、`ccbd-rmux-namespace-lifecycle` 和现有 `targets.py` / `panes.py` 中的 canonicalization、split alias、layout materialize 基础能力。
- 本 item 的增量是把 pane identity/layout 作为 UX parity contract 统一验收：记录 canonicalization source、agent-pane binding 恢复、identity conflict diagnostics；不默认重做基础 split/list/move/swap 实现。

### 4.5 Visual/no-popup execution contract

**方向**：Visual No-Popup Surface → Foreground Interaction / Supportability
**形式**：Windows-safe status execution policy

**契约**：

```python
class WindowsRmuxVisualCommandPolicy(TypedDict):
    dynamic_status_enabled: bool
    execution_kind: Literal["disabled", "rmux_native_hidden", "windows_hidden_process", "static_only"]
    popup_probe_status: Literal["pass", "failed", "not-run"]
    disabled_reason: str | None
```

**约束**：

- Windows/rmux 不允许通过 visible Git Bash / git-cmd / shell popup 执行 status/border hooks。
- 动态状态恢复前必须有 popup probe evidence。
- 如果只能 static fallback，doctor/diagnostics 应说明状态来源和 disabled reason。

**Baseline reuse / delta**：

- 复用当前 Windows/rmux static fallback 和禁用 shell hook 的止血策略作为 baseline。
- 本 item 的增量是证明动态状态恢复或替代路径不会产生可见 popup，并把 disabled reason 投影给 diagnostics；不把 shell popup 风险分散到每个 status hook。

### 4.6 Lifecycle/recovery UX contract

**方向**：Lifecycle And Recovery UX → Supportability / Validation
**形式**：lifecycle transcript + residue report

**契约**：

```python
class WindowsRmuxLifecycleUxReport(TypedDict):
    scenario: Literal["reattach", "terminal_closed", "kill_cleanup", "pane_crash", "provider_crash", "rmux_daemon_crash"]
    start_state: str
    action: str
    expected_observable: str
    verdict: Literal["pass", "partial", "failed", "blocked"]
    cleanup_residue: dict[str, object]
    diagnostics_ref: str
```

**约束**：

- `ccb kill` 验收必须同时看 ccbd endpoint、rmux namespace/session、provider/job/process residue。
- crash 场景允许 degraded，但必须有用户可见诊断和下一步建议。
- 关闭 WezTerm 不得等同 kill project。

**Baseline reuse / delta**：

- 复用 `rmux-supervision-recovery`、`ccbd-windows-full-chain-smoke`、`rmux-windows-validation-matrix` 的 accepted evidence 作为 backend/control-plane baseline。
- 本 item 的增量是日用 UX 场景：关闭 WezTerm 后重新 attach、用户触发 kill、pane/provider/rmux daemon crash 后的可见恢复路径、residue 报告和 degraded diagnostics；不默认重做 native backend supervision。

### 4.7 Supportability projection contract

**方向**：Supportability Contract ← 所有 parity evidence
**形式**：support tier projection

**契约**：

```python
class WindowsRmuxUxSupportProjection(TypedDict):
    support_tier: Literal["experimental", "beta", "supported", "blocked"]
    parity_dimensions: dict[str, Literal["pass", "partial", "blocked", "failed", "missing"]]
    validation_ref: str
    install_entry: Literal["source", "install_ps1", "npm", "diagnostic_only"]
    fallback_guidance: str
```

**约束**：

- 任一 core parity dimension 为 `failed` / `blocked` 时不得宣称 `supported`。
- `partial` 可以进入 beta，但 docs/doctor 必须列 residual risks。
- npm win32 仍受 `rmux-packaging-docs-contracts` / package gate 约束；本 roadmap 不单独授权发布。
- `rmux-packaging-docs-contracts` 是 base support projection、npm gate、`install.ps1` gate 和 release guard 的单一 owner；本 item 只能消费其最终 projection，再叠加 UX parity dimensions。
- 如果 `rmux-packaging-docs-contracts` 仍未 accepted，本 item 可以设计/实现 UX overlay classifier，但不得把 `support_tier` 推高到 `supported`，也不得修改 npm/install gate 的 owner 规则。

**Baseline reuse / delta**：

- 复用 `rmux-packaging-docs-contracts` 的 base projection、diagnostics/docs/install/package gate 作为下游输入。
- 本 item 的增量是把 6 个 UX parity JSON evidence 投影到 doctor/diagnostics/docs 的用户可见承诺；不重复定义 base installer/package/release 规则。

## 5. 子 feature 清单

1. **windows-rmux-wezterm-native-interaction-parity** — 普通 pane GUI-native，sidebar 全接管，滚轮/剪贴板不被 CCB/rmux 劫持。
   - 所属模块：Foreground Interaction
   - 依赖：无
   - 状态：in-progress
   - 对应 feature：`2026-07-25-windows-rmux-wezterm-native-interaction-parity`
   - Design 前置 brainstorm：已确认 `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-brainstorm.md`
   - 备注：已先行进入 feature design；本 roadmap 采用该 feature 作为最小闭环。继续实现前仍必须保证 design 引用上述 brainstorm，并记录 owner 已批准/通过进入 design。

2. **windows-rmux-output-capture-parity** — 验证 rmux capture 与 Linux/macOS tmux baseline 在 provider completion、ANSI、宽字符、wrapping 上的保真边界。
   - 所属模块：Output And Capture
   - 依赖：`windows-rmux-wezterm-native-interaction-parity`
   - 状态：planned
   - 对应 feature：未启动
   - Design 前置 brainstorm：pending；owner 用 `$cs-brainstorm` 明确通过前不得启动 design。
   - 备注：不得把用户滚轮当作 capture 证据；复用 `rmux-send-capture-logging` acceptance 作为 baseline，只补 UX parity delta、跨平台 baseline 刷新和差异归因。

3. **windows-rmux-pane-identity-layout-parity** — 收口 pane id/index/canonicalization、layout 重建和 agent-pane 绑定恢复。
   - 所属模块：Pane Identity And Layout
   - 依赖：`windows-rmux-wezterm-native-interaction-parity`
   - 状态：planned
   - 对应 feature：未启动
   - Design 前置 brainstorm：pending；owner 用 `$cs-brainstorm` 明确通过前不得启动 design。
   - 备注：吸收 `%N` exact/index alias 既有问题，复用既有 canonicalization 基础，只补 identity/layout UX contract、binding 恢复和 conflict diagnostics。

4. **windows-rmux-visual-no-popup-parity** — 恢复或替代动态状态栏/边框/标题，同时保证无 Git Bash / console popup。
   - 所属模块：Visual No-Popup Surface
   - 依赖：`windows-rmux-wezterm-native-interaction-parity`
   - 状态：planned
   - 对应 feature：未启动
   - Design 前置 brainstorm：pending；owner 用 `$cs-brainstorm` 明确通过前不得启动 design。
   - 备注：当前 static fallback 是止血 baseline；本 item 只恢复或替代动态状态的 no-popup UX evidence，不分散修改 base support projection。

5. **windows-rmux-lifecycle-recovery-ux-parity** — 覆盖 reattach、关闭 WezTerm、kill cleanup、pane/provider/rmux daemon crash 后恢复或 degraded diagnostics。
   - 所属模块：Lifecycle And Recovery UX
   - 依赖：`windows-rmux-pane-identity-layout-parity`, `windows-rmux-output-capture-parity`
   - 状态：planned
   - 对应 feature：未启动
   - Design 前置 brainstorm：pending；owner 用 `$cs-brainstorm` 明确通过前不得启动 design。
   - 备注：身份与 capture 稳定后再验证 recovery；复用旧 supervision/full-chain/validation baseline，只补 attach/reconnect/kill/crash 的用户可见恢复与 degraded diagnostics。

6. **windows-rmux-supportability-parity-contract** — 汇总 parity evidence 到 doctor/install/support tier/docs，一致表达 beta/supported/blocked 和 fallback。
   - 所属模块：Supportability Contract
   - 依赖：`windows-rmux-output-capture-parity`, `windows-rmux-pane-identity-layout-parity`, `windows-rmux-visual-no-popup-parity`, `windows-rmux-lifecycle-recovery-ux-parity`
   - 状态：planned
   - 对应 feature：未启动
   - Design 前置 brainstorm：pending；owner 用 `$cs-brainstorm` 明确通过前不得启动 design。
   - 备注：消费 `rmux-packaging-docs-contracts` 最终 support projection，作为 UX parity overlay；不重复定义 npm、install.ps1、release guard，不单独授权 npm 发布。

**最小闭环**：第 1 条 `windows-rmux-wezterm-native-interaction-parity` 完成后，Windows/rmux/WezTerm 前台普通 pane 不再被 CCB/rmux 鼠标绑定劫持，sidebar 仍可用，用户获得第一条可日用 GUI 体验闭环。

### Goal Coverage Matrix

| Goal / completion signal | Covered by item(s) | Verification entry | Evidence type | Core? |
|---|---|---|---|---|
| 普通 pane 在 WezTerm 前台不被 CCB/rmux 劫持滚轮、右键粘贴、左键选择/聚焦 | `windows-rmux-wezterm-native-interaction-parity` | `test/test_v2_tmux_ui.py` + rmux live binding snapshot + manual WezTerm runbook | pytest / command transcript / manual report | yes |
| provider completion 和后端 capture 在 rmux 下保持格式保真或明确记录差异 | `windows-rmux-output-capture-parity` | capture parity fixtures + provider completion golden fixtures | pytest / artifact report | yes |
| pane identity/layout 在 split、respawn、reattach 后能稳定关联 agent 与 pane | `windows-rmux-pane-identity-layout-parity` | layout/materialize tests + live identity snapshot | pytest / command transcript | yes |
| 状态栏/边框/标题动态信息不再产生 Git Bash / console popup | `windows-rmux-visual-no-popup-parity` | popup probe + live status snapshot | command transcript / manual report | yes |
| WezTerm 关闭/重开、kill、pane/provider/daemon crash 后有恢复或明确 degraded diagnostics | `windows-rmux-lifecycle-recovery-ux-parity` | lifecycle transcript + residue report | command transcript / diagnostics bundle | yes |
| doctor/install/docs/support tier 与 parity evidence 一致 | `windows-rmux-supportability-parity-contract` | support projection tests + docs consistency gate | pytest / docs guard / diagnostics snapshot | yes |

## 6. 排期思路

先做前台交互，因为它已经有用户确认的 UX 决策和 draft design，且能最快形成日用闭环。随后并行倾向是 output/capture 与 pane identity/layout：前者保护 `ccb ask` 和 provider completion，后者保护所有 target / layout / recovery 的身份基础。视觉无弹窗可以在前台交互后启动，但若需要依赖 identity 或 diagnostics 字段，应在 design 阶段显式补依赖。生命周期 recovery 放在 identity/capture 之后，避免把底层 target 或 capture 问题误归因。supportability 最后收口，把各维度 evidence 投影到 doctor/install/docs/support tier。

技术依赖优先于产品排序：interaction → output/capture + identity/layout + visual/no-popup → lifecycle/recovery → supportability。若 owner 后续认为视觉无弹窗更影响日用，可以在不破坏 DAG 的前提下提前 `windows-rmux-visual-no-popup-parity`。

### 深度规划底稿

目标完成信号：

- native Windows + WezTerm + rmux 的普通 pane 前台交互不被 CCB/rmux 劫持。
- rmux capture 与 provider completion 有可重复保真证据。
- pane identity/layout 绑定不会因 id/index alias、split、reattach 漂移。
- 状态栏/边框/标题动态信息无可见 shell popup。
- reattach/kill/crash recovery 有 transcript、residue 和 diagnostics evidence。
- doctor/install/docs 能基于 parity evidence 一致声明支持状态。

Top 3 风险与缓解：

1. **GUI 体验无法完全由自动测试证明**：每个 core UX item 都必须有 native Windows + WezTerm 手工或 live transcript evidence，skip 不能算 pass。
2. **parity 维度互相污染归因**：统一 `WindowsRmuxUxParityEvidence`，区分 provider failure、system failure、test design failure 和环境 blocked。
3. **过早宣称 supported**：supportability 最后执行，且必须消费所有 core parity dimensions；partial 只能进入 beta 或 residual risk。

非显然依赖：

- 需要 native Windows + WezTerm 前台环境。
- 需要 rmux 可用且 version / capability 可记录。
- 需要现有 `windows-rmux-native-backend` 的 backend resolver、rmux backend、validation matrix、diagnostics 基础继续可用。
- 真实 provider auth/quota 失败需要与系统 parity 失败分离。

关键假设：

- WezTerm 是当前 native Windows GUI 宿主的目标终端；其他终端只作 supporting evidence。
- 不以 tmux-like mouse parity 为默认目标；普通 pane 采用 GUI-native。
- support tier 不由单条 feature 决定，而由所有 core parity dimensions 汇总。

基线与验证入口：

- `python -m pytest -q test/test_v2_tmux_ui.py`
- `python -m pytest -q -rs test/test_v2_tmux_ui.py -k rmux_accepts_mouse_context_project_ui_bindings`
- rmux live `list-keys` / capture / list-panes / lifecycle transcripts。
- sidebar Rust tests：`cargo test --manifest-path "tools/ccb-agent-sidebar/Cargo.toml" --quiet`
- diagnostics / doctor / docs consistency tests 由 supportability feature 定义。
- 每个子 feature 的 UX parity JSON evidence 校验：解析 `.codestable/features/YYYY-MM-DD-{feature-slug}/evidence/windows-rmux-ux-parity-evidence.json`，检查 `schema_version`、dimension/status/failure_class enum、artifact refs 和 partial/blocked/failed 的 residual risk。

交付物落点：

- 子 feature spec：`.codestable/features/YYYY-MM-DD-{slug}/`
- evidence artifacts：各子 feature 的 `evidence/` 或 QA 同名小节。
- 机器可读 UX parity evidence：各子 feature 的 `evidence/windows-rmux-ux-parity-evidence.json`。
- support projection / docs：由最后 supportability item 决定。

知识回写点：

- GUI-native vs tmux-like mouse parity 是 ADR 候选。
- Windows-safe status execution / no-popup 规则若验证稳定，应沉淀到 ADR 或 compound。
- parity evidence schema 若稳定，应在 supportability acceptance 后沉淀为项目约定。

## 7. 观察项

- `windows-rmux-wezterm-native-interaction-parity` 已经先于本 roadmap 进入 feature design；本 roadmap 确认后、进入实现前，应把该 design frontmatter 持久化为 `roadmap: windows-rmux-ux-parity-hardening` / `roadmap_item: windows-rmux-wezterm-native-interaction-parity`，并在后续 epic child batch 中明确复用既有 passed design-review 作为该 item 的 design-review evidence。
- `windows-rmux-native-backend` 中 `rmux-packaging-docs-contracts` 仍在进行。它是 base support projection、npm gate、`install.ps1` gate 和 release guard 的单一 owner；最终 supportability item 只能消费/扩展其 projection，不能互相矛盾或重复定义发布入口。
- 后续每个 child design 启动前都必须先有该 item 自身的 confirmed `$cs-brainstorm` 和 owner 进入 design 批准；roadmap 级 brainstorm 只能作输入材料，不是 design admission evidence。
- 后续每个 child design 都必须包含 “baseline reuse / delta” 小节，列出复用的 `windows-rmux-native-backend` acceptance evidence 和本 item 的 UX parity 增量，避免重做已验收的 base backend 工作。
- “Windows/rmux 选择 GUI-native parity，而不是 tmux-like mouse parity”符合 ADR 三判据（难回退 + 非显然 + 真实权衡），建议走 `cs-domain` 记录。
- 现有 `%SystemDrive%/` 未跟踪目录和 `bin/ccb-agent-sidebar.exe` dirty 文件不是本 roadmap 输入，后续实现不要误纳入本工作范围。

## 8. 变更日志

- 2026-07-25：从 `.codestable/brainstorms/windows-rmux-ux-parity-hardening/brainstorm.md` 升级为 draft roadmap；纳入 6 个 parity 维度，并将已启动的 `windows-rmux-wezterm-native-interaction-parity` 作为最小闭环 item。
- 2026-07-25：根据独立 roadmap review 收紧 supportability owner 边界、UX parity JSON evidence 落点、与 `windows-rmux-native-backend` accepted evidence 的 baseline/delta 规则，以及先行 feature 的 roadmap 绑定恢复规则。
- 2026-07-25：按 owner 要求新增每个子 feature 的 design 前置 `$cs-brainstorm` gate；所有 child design 启动前必须先完成针对该 item 的深入讨论，并获得 owner 明确批准/通过。
