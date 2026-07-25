---
doc_type: feature-design
feature: 2026-07-25-windows-rmux-wezterm-native-interaction-parity
roadmap: windows-rmux-ux-parity-hardening
roadmap_item: windows-rmux-wezterm-native-interaction-parity
brainstorm: .codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-brainstorm.md
requirement:
execution_lane: standard
status: draft
summary: Windows/rmux/WezTerm 前台交互采用 GUI-native parity，普通 pane 透明化，sidebar 专属接管
tags: [windows, rmux, wezterm, interaction, mouse, keyboard, clipboard, sidebar, parity]
---

# Windows Rmux WezTerm Native Interaction Parity Feature Design

## 0. 术语约定

| 术语 | 定义 | 防冲突结论 |
|---|---|---|
| GUI-native parity | Windows/rmux/WezTerm 下以宿主 GUI 终端的选择、复制、粘贴、滚轮和焦点直觉作为用户体验目标。 | 不等于 tmux mouse binding 逐条兼容；本 feature 明确选择 GUI-native。 |
| 普通 pane | agent / tool / cmd 等非 sidebar pane。 | 普通 pane 默认透明化，不承载 CCB 自有鼠标 UI。 |
| sidebar pane | `@ccb_role=sidebar` 的 CCB 自有 TUI pane。 | sidebar 允许 CCB/rmux 绑定全接管。 |
| 透明化 | CCB 不把普通 pane 的鼠标事件改写成 rmux copy-mode、rmux buffer paste 或 pane 应用 mouse event。 | 受 rmux mouse capture 限制时，第一版至少要做到不劫持到 CCB/rmux 行为。 |
| KillProject | sidebar 退出项目的既有高影响动作。 | sidebar `x` 保持 KillProject 语义，不改成仅隐藏 sidebar。 |

## 1. 决策与约束

### Design admission

本 design 的前置 brainstorm 为 `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-brainstorm.md`。该记录 frontmatter 为 `doc_type: feature-brainstorm` / `status: confirmed`，并已收敛到 Windows/rmux/WezTerm 前台交互采用 GUI-native parity；它是本 feature 进入 design 的 owner admission evidence。

本 design 绑定 roadmap `windows-rmux-ux-parity-hardening` / item `windows-rmux-wezterm-native-interaction-parity`。继续实现前必须保留上述 brainstorm 引用，并遵守 roadmap 的 Design 前置 Brainstorm Gate；后续对本 design 的实质更新也必须先确认 admission 仍有效。

### 需求摘要

在 native Windows + WezTerm + rmux 前台交互链路中，普通 agent pane 应尽量像普通 GUI 终端：单击可聚焦，拖选不被应用 mouse event 干扰，右键不被 CCB 改写成 rmux buffer paste，滚轮不强制进入 rmux copy-mode。sidebar 作为 CCB 自有 TUI 保留专属鼠标接管，包含滚动、agent 选择、配置入口和 `x` KillProject。

成功标准：

- Windows/rmux fallback 下，普通 pane 的左键路径只做 focus，不透传普通左键到 pane 应用。
- Windows/rmux fallback 下，普通 pane 的右键不被绑定为 `paste-buffer -p`。
- Windows/rmux fallback 下，普通 pane 的滚轮不进入 `copy-mode -e`，不触发空 scrollback `[0/0]`。
- sidebar pane 仍能通过鼠标滚轮、点击 agent、`⚙`、`x` 完成既有 CCB TUI 交互。
- `Q` 和 `Shift+Q` 在 Windows/WezTerm/crossterm 编码差异下仍映射到同一 KillProject 语义。
- Linux/macOS tmux 既有 project UI 行为不因本 feature 回退。

明确不做：

- 不实现完整 tmux-like mouse parity。
- 不新增 `transparent | tmux_like | hybrid` 交互配置开关。
- 不新增显式 history viewer、sidebar 历史入口或 copy-mode 快捷入口。
- 不改变 provider completion / backend capture 契约。
- 不改变 sidebar `x` 的 KillProject 语义。
- 不调整 install/support tier、full-chain smoke 或 packaging/docs 承诺。

复杂度档位：走现有 CLI/runtime UI feature 的默认档位；偏离点是“真实前台 GUI 手工验收”为 core evidence，因为鼠标/剪贴板行为无法只靠单元测试证明。

### 关键决策

1. **GUI-native 优先，而不是 tmux-like mouse parity。**  
   普通 pane 的默认体验以 WezTerm 和系统剪贴板直觉为目标；Windows/rmux 不继续为普通 pane 叠加 copy-mode 和 paste-buffer 鼠标工作流。

2. **普通 pane 透明，sidebar 全接管。**  
   绑定必须先按 `@ccb_role=sidebar` 分流；sidebar 可以 `send-keys -M`，普通 pane 不应继承 sidebar 的 mouse passthrough。

3. **第一版不加模式开关。**  
   交互行为尚未稳定前不扩大配置面；如后续需要 tmux-like 或 hover-focus，另开 feature。

4. **滚轮和后端 capture 解耦。**  
   用户滚轮不作为 `capture-pane` / provider completion 的可靠性证明；机器读取继续由后端 capture 测试覆盖。

### Top 3 风险与缓解

1. **风险：rmux mouse capture 使 WezTerm 原生滚轮/右键仍无法完全接管。**  
   缓解：验收目标先定为“不被 CCB/rmux 劫持到 copy-mode / paste-buffer /普通左键透传”，并要求真实 WezTerm 手工 runbook 记录残留。
2. **风险：sidebar 全接管改动误伤普通 pane。**  
   缓解：单元测试和 live binding snapshot 必须同时断言普通 pane fallback 不含 `copy-mode -e`、`paste-buffer -p` 和裸 `send-keys -M` 左键透传。
3. **风险：为了交互修复顺手改变 Linux/macOS tmux 行为。**  
   缓解：scope guard 只允许 Windows + `backend_impl=rmux` fallback 语义变化；现有 tmux UI 测试保持回归。

### 非显然依赖与关键假设

- 假设当前 WezTerm 前台环境可由用户手工复测；若缺少真实 GUI 前台，QA 只能给出 blocked 或 partial evidence。
- 假设 `@ccb_role=sidebar` 在 live rmux session 中仍是可靠的 sidebar 判定来源。
- 假设 `tools/ccb-agent-sidebar/src/tui.rs` 中既有 `Q` / `Shift+Q` 兼容测试可继续作为 KillProject 键盘语义证据。
- 假设本 feature 不需要改 rmux backend send/capture 实现；若实现发现 capture 语义缺口，应转出到 output/capture parity。

### 方案深度 pre-pass

候选：

- 完整版：引入可配置 mouse mode，分别实现 transparent / tmux-like / hybrid。
- 简化版：只固化 Windows/rmux 默认 GUI-native 行为，sidebar 例外。

本场景选择简化版，不是因为“更快”，而是因为当前风险来自过多 mouse binding 叠加；第一版应减少默认接管面，让用户可日用路径更稳定。转正条件：只有出现明确用户需求要求 tmux-like 普通 pane 鼠标流，且 WezTerm/rmux 有可靠证据支持时，再设计配置模式。

## 2. 名词与编排

### 2.1 名词层

#### 现状

- `lib/cli/services/tmux_ui_runtime/service.py` 的 `_apply_sidebar_mouse_controls()` 负责 root table mouse binding。非 Windows/rmux 路径使用 `#{mouse_pane}`，Windows/rmux 因 `_mouse_pane_format_supported()` 返回 false 进入 `_apply_sidebar_mouse_controls_without_mouse_pane_format()`。
- Windows/rmux fallback 目前已经避免绑定 `MouseDown3Pane`，防止普通右键被 `paste-buffer -p` 劫持；但普通 pane wheel 仍可能在 `history_size > 0` 时进入 `copy-mode -e`。
- `test/test_v2_tmux_ui.py` 已覆盖 Windows/rmux 不使用 `#{mouse_pane}` / `-t =`、不绑定右键 paste-buffer、以及 live rmux binding snapshot。
- `tools/ccb-agent-sidebar/src/tui.rs` 中 `exit_action_for_key()` 已把 `KeyCode::Char('Q')` 和 `KeyCode::Char('q') + SHIFT` 映射为 `KillProject`。

#### 变化

- 收紧 Windows/rmux fallback 的普通 pane wheel 语义：普通 pane 不进入 `copy-mode -e`，不执行 `send-keys -X scroll-up/down`。
- 保留普通 pane 左键 `select-pane -M` focus 行为，避免裸 `send-keys -M` 透传普通左键。
- 保留 sidebar `send-keys -M`、`c` 和 `Q` 语义；sidebar `x` 仍映射 KillProject。
- 将测试从“history_size/alternate_on 分流”更新为“普通 pane 不 copy-mode，sidebar 独占 wheel passthrough”。

##### Interface 设计检查

- Module：`tmux_ui_runtime.service` 的 project UI mouse binding 生成逻辑，改造现有模块。
- Interface：caller 只调用 `apply_project_tmux_ui()`；实现内部根据 backend/platform 产出 tmux/rmux key bindings。caller 不应知道具体 mouse binding 字符串。
- Seam：seam 保持在 `_apply_sidebar_mouse_controls()` / `_apply_sidebar_mouse_controls_without_mouse_pane_format()`；测试通过 fake backend calls 和 live `list-keys` 观察。
- Depth / locality：行为复杂度集中在 UI binding owner 内；若不在此处处理，会散到 ccbd namespace、sidebar TUI 或 rmux backend callers。
- Dependency strategy：local-substitutable。单元测试用 fake backend，live test 在 rmux 可用时作为补充。
- Adapter：无新 adapter；backend 已存在 tmux/rmux 兼容 interface。
- Test surface：`test_v2_tmux_ui.py` 的 fake call assertions、rmux live binding snapshot、sidebar Rust key tests、手工 WezTerm runbook。

### 2.2 编排层

主流程简单线性，不画图：

1. `apply_project_tmux_ui()` 解析 backend 与平台。
2. Windows + rmux 禁用 shell status/hook，避免额外 console 弹窗。
3. `_apply_sidebar_mouse_controls()` 先 unbind root mouse keys。
4. Windows/rmux 进入 fallback binding。
5. fallback 绑定普通 pane 左键 focus、sidebar 左键/滚轮/header 交互，并避免普通 pane right-click / wheel 劫持。
6. pane theme / active border 继续沿用现有流程。

#### 现状

当前 fallback 兼容了 rmux 不可靠的 `#{mouse_pane}` target，并修过右键 paste-buffer 劫持；但 wheel 仍保留普通 pane copy-mode 分支，和本轮“终端原生滚动优先”决策冲突。

#### 变化

- Windows/rmux fallback 的 `WheelUpPane` / `WheelDownPane`：sidebar 继续 `select-pane -M ; send-keys -M`，普通 pane 不执行 copy-mode scroll。
- `MouseDown1Pane` / `MouseDown1Border`：保留 sidebar header direct action；普通 pane 只 focus。
- `MouseDown3Pane` / `M-MouseDown3Pane`：Windows/rmux fallback 继续不绑定。

流程级约束：

- 幂等性：重复 apply UI 时先 unbind 再 bind，结果稳定。
- 错误语义：backend 命令失败沿用现有 `tmux_run` / backend error 行为；本 feature 不新增吞错策略。
- 可观测点：fake backend call list、live `rmux list-keys -T root`、手工 WezTerm 前台操作记录。
- 顺序约束：Windows/rmux shell command 禁用和 mouse fallback 应在 pane theme / active border 前后保持现有调用顺序，不改变主题应用。

### 2.3 挂载点清单

- 本 feature 不引入新的用户配置 key、CLI flag、daemon endpoint 或 public command。
- 挂载点为既有 project UI 注入点：`apply_project_tmux_ui()` 对 tmux/rmux root mouse bindings 的既有注册行为 — 修改 Windows/rmux fallback 规则。
- sidebar `x` / `Q` 的 public UX 语义保持现有 KillProject，不新增入口。
- 可卸载性：回退本 feature 等价于回退 Windows/rmux fallback binding 规则和对应测试，不涉及配置迁移、状态清理或用户数据转换。

### 2.4 推进策略

1. **编排骨架：收紧 Windows/rmux fallback 的普通 pane left-click、wheel 和 right-click 行为。**  
   退出信号：fake backend calls 中普通 pane left-click 只保留 focus，不裸透传 `send-keys -M`；普通 pane wheel/right-click 分支不再包含 `copy-mode -e`、`send-keys -X scroll-up/down`、`paste-buffer -p`。
2. **sidebar 交互保持：验证 header、滚轮、agent 点击和 KillProject 不回退。**  
   退出信号：sidebar 分支仍包含 `send-keys -M`、`send-keys c`、`send-keys Q`，Rust `Q` / `Shift+Q` 测试通过。
3. **live binding snapshot：在 rmux 可用时验证 root bindings。**  
   退出信号：`rmux list-keys -T root` 不包含普通 pane copy-mode / paste-buffer 劫持，且包含 sidebar 分流；证据写入 `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/evidence/live-binding-snapshot.txt` 或 QA 同名小节。
4. **前台手工 runbook：记录 WezTerm GUI 操作结果。**  
   退出信号：用户或 QA 记录单击聚焦、拖选、右键粘贴、滚轮、sidebar `⚙` / `x` 的实际结果；证据写入 `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/evidence/manual-wezterm-runbook.md` 或 QA 同名小节；缺 rmux 记 `blocked: rmux-unavailable`，缺 GUI 前台记 `partial: gui-unavailable`，不得把 skipped live test 记为 full pass。
5. **回归收口：跑 tmux UI 与 sidebar TUI 相关测试。**  
   退出信号：目标 pytest、cargo tests、compile/format checks 通过或记录既有非本 feature 红灯。

### 2.5 结构健康度与微重构

##### 评估

- compound 检索：未发现与本 feature 直接相关的目录/命名沉淀。
- 文件级 — `lib/cli/services/tmux_ui_runtime/service.py`：该文件承担 project UI theme、mouse binding、resize hook、border style 等多项 UI 编排职责；本 feature 只触碰已有 Windows/rmux fallback binding，不新增第 N+1 个独立职责。
- 文件级 — `test/test_v2_tmux_ui.py`：测试文件较长且覆盖多个 tmux UI 行为；本 feature 只更新已有 Windows/rmux 用例和 live binding 用例，不新增独立测试子系统。
- 文件级 — `tools/ccb-agent-sidebar/src/tui.rs`：已有 KillProject 键盘兼容逻辑和测试；本 feature 默认只回归验证，不改 Rust TUI，除非实现发现回退。
- 目录级 — `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/`：新 feature spec 目录，结构符合共享约定。

##### 结论：不做微重构

本 feature 的最小充分改动是收紧既有 Windows/rmux fallback 分支和对应测试。把 mouse binding 从 `service.py` 拆出独立文件有长期价值，但会扩大行为验证面；本轮不做只搬不改行为的微重构。

##### 超出范围的观察

- `tmux_ui_runtime/service.py` 长期看可以拆分 theme、mouse binding、resize hook、border style owner。建议后续若继续扩展 project UI，再走 `cs-refactor` 做只搬不改行为的拆分。

## 3. 验收契约

### 3.1 关键场景清单

| ID | 输入 / 触发 | 期望可观察结果 | 证据类型 |
|---|---|---|---|
| AC-001 | Windows + `backend_impl=rmux` apply project UI | 普通 pane wheel 分支不包含 `copy-mode -e` 或 `send-keys -X scroll-up/down` | unit |
| AC-002 | Windows + `backend_impl=rmux` apply project UI | 普通 pane right-click 不绑定 `MouseDown3Pane` / `M-MouseDown3Pane` 到 `paste-buffer -p` | unit |
| AC-003 | Windows + `backend_impl=rmux` 普通 pane 左键 | binding 只做 pane focus，不裸透传 `send-keys -M` 到普通 pane 应用 | unit / live |
| AC-004 | Windows + `backend_impl=rmux` sidebar wheel / click | sidebar 分支仍透传 mouse event，并保留 settings / KillProject header action | unit / live |
| AC-005 | Windows/WezTerm/crossterm `Q` / `Shift+Q` | 两种编码均映射到 KillProject，普通 `q` / Esc 不 kill project | cargo test |
| AC-006 | 非 Windows tmux 路径 | 既有 tmux project UI mouse/theme 行为不回退 | unit |
| AC-007 | WezTerm 手工前台 | 单击聚焦、拖选、右键粘贴、滚轮、sidebar `⚙` / `x` 结果被记录；残留限制明确分类 | manual |

测试更新要求：

- `test_windows_rmux_project_ui_avoids_shell_status_commands` 中 wheel 断言必须反转：普通 pane fallback 不再要求 `copy-mode -e`、`history_size`、`alternate_on`、`send-keys -X -N 2 scroll-up/down` 存在；应断言这些不出现在普通 pane fallback 分支。
- 同一测试或拆出的精准测试必须继续证明 sidebar 分支保留 `select-pane -M ; send-keys -M`，普通 pane left-click 不裸透传 `send-keys -M`。
- live rmux 用例运行时使用 `-rs` 或等价输出记录 skip reason；skip 只能作为环境事实，不能替代 live binding snapshot。

### 3.2 明确不做的反向核对项

- Windows/rmux fallback 不应新增交互模式配置 key。
- Windows/rmux fallback 不应在普通 pane 分支出现 `paste-buffer -p`。
- Windows/rmux fallback 不应在普通 pane wheel 分支出现 `copy-mode -e` 或 `send-keys -X scroll-up/down`。
- 本 feature 不应修改 provider capture / completion parser。
- 本 feature 不应修改 install/support tier、README support wording 或 packaging metadata。

### 3.3 Acceptance Coverage Matrix

| Scenario | Covered By Step | Evidence Type | Command / Action | Core? |
|---|---|---|---|---|
| AC-001 普通 pane wheel 不进 copy-mode | S1 | test | `python -m pytest -q test/test_v2_tmux_ui.py -k windows_rmux_project_ui_avoids_shell_status_commands` | yes |
| AC-002 右键不劫持 paste-buffer | S1 | test | `python -m pytest -q test/test_v2_tmux_ui.py -k windows_rmux_project_ui_avoids_shell_status_commands` | yes |
| AC-003 左键只 focus | S1,S3 | test / live | `python -m pytest -q -rs test/test_v2_tmux_ui.py -k rmux_accepts_mouse_context_project_ui_bindings` | yes |
| AC-004 sidebar 全接管 | S2,S3 | test / live | `python -m pytest -q test/test_v2_tmux_ui.py` | yes |
| AC-005 Q / Shift+Q KillProject | S2 | test | `cargo test --manifest-path tools/ccb-agent-sidebar/Cargo.toml shifted_q_is_project_kill_across_terminal_key_encodings --quiet` | yes |
| AC-006 tmux 路径回归 | S5 | test | `python -m pytest -q test/test_v2_tmux_ui.py` | yes |
| AC-007 WezTerm 前台手工 | S4 | manual | 在 native Windows + WezTerm + rmux 复测交互 runbook | yes |

### 3.4 DoD Contract

| ID | 要求 | 证据 | 阻塞级别 |
|---|---|---|---|
| DOD-DESIGN-001 | design/checklist/design-review 完整且通过 | design review | blocking |
| DOD-IMPL-001 | Windows/rmux fallback 普通 pane 不再劫持 wheel / right-click / left-click passthrough | unit/live evidence | blocking |
| DOD-IMPL-002 | sidebar mouse/header/KillProject 语义不回退 | unit/live/cargo evidence | blocking |
| DOD-IMPL-003 | Linux/macOS tmux project UI 测试不回退 | pytest | blocking |
| DOD-REVIEW-001 | code review passed 且无 unresolved blocking | review report | blocking |
| DOD-QA-001 | QA 包含 native Windows + WezTerm 手工记录，无法执行时明确 blocked/partial | QA report | blocking |
| DOD-ACCEPT-001 | acceptance 根据测试、live snapshot、手工记录裁决 | acceptance report | blocking |

Validation Commands:

| ID | 命令 | 目的 | 核心性 | 失败处理 |
|---|---|---|---|---|
| CMD-001 | `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-checklist.yaml" --yaml-only` | checklist YAML 合法性 | core | fix-or-block |
| CMD-002 | `python -m pytest -q test/test_v2_tmux_ui.py` | tmux UI mouse/theme 回归 | core | fix-or-block |
| CMD-003 | `cargo test --manifest-path "tools/ccb-agent-sidebar/Cargo.toml" shifted_q_is_project_kill_across_terminal_key_encodings --quiet` | sidebar KillProject 键盘编码回归 | core | fix-or-block |
| CMD-004 | `cargo test --manifest-path "tools/ccb-agent-sidebar/Cargo.toml" --quiet` | sidebar TUI 回归 | supporting | fix-or-block-if-touched |
| CMD-005 | `python -m py_compile "lib/cli/services/tmux_ui_runtime/service.py" "test/test_v2_tmux_ui.py"` | Python 编译检查 | core | fix-or-block |
| CMD-006 | `python -m pytest -q -rs test/test_v2_tmux_ui.py -k rmux_accepts_mouse_context_project_ui_bindings` | rmux live binding snapshot；skip reason 必须写入 QA | core-live | attach-transcript-or-block-pass |

Required Artifacts：design、checklist、design-review、实现 diff、pytest 输出、cargo test 输出、rmux live binding snapshot（`.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/evidence/live-binding-snapshot.txt` 或 QA 同名小节）、native Windows + WezTerm 手工交互记录（`.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/evidence/manual-wezterm-runbook.md` 或 QA 同名小节）、review、QA、acceptance。

### 3.5 自我批判结论

- 可证伪性：核心行为都落到绑定字符串缺失/存在、live snapshot 和手工操作结果。
- 步骤原子性：普通 pane 收紧、sidebar 保持、live snapshot、手工 runbook、回归收口分开。
- 最弱依赖：WezTerm 手工复测是最弱依赖；无法执行时不能伪装 full pass。
- 证据完整性：单元测试证明绑定生成，live snapshot 证明 rmux 接受，手工记录证明 GUI 体验。
- 基线可执行性：当前工作区已有非本轮改动，implement/QA 必须避免把既有 dirty binary 或 `%SystemDrive%/` 归入本 feature。
- 清洁度规则：不新增临时 TODO/FIXME、调试输出、注释掉代码、无用 import；不落 provider token 或本地敏感路径到手工记录。

## 4. 与项目级架构文档的关系

本 feature 形成一个稳定 UX 取舍：Windows/rmux 前台交互选择 GUI-native parity，而不是 tmux-like mouse parity。该决策难回退、非显然且有真实权衡，建议后续通过 `cs-domain` 写 ADR。

另外 5 个 UX parity 维度已记录在 `.codestable/brainstorms/windows-rmux-ux-parity-hardening/brainstorm.md`，本 feature 不替代后续 epic/roadmap。
