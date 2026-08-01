---
doc_type: feature-design
feature: 2026-07-27-sidebar-settings-click-e2e
status: approved
execution_lane: goal
summary: "验证并修复 Windows/rmux/WezTerm 下 sidebar settings 鼠标点击的端到端派发链路"
tags: [windows, rmux, wezterm, sidebar, mouse, diagnostics]
roadmap: windows-rmux-ux-parity-hardening
roadmap_item: sidebar-settings-click-e2e
split_parent: 2026-07-25-windows-rmux-wezterm-native-interaction-parity
split_child: sidebar-settings-click-e2e
brainstorm: .codestable/features/2026-07-27-sidebar-settings-click-e2e/sidebar-settings-click-e2e-brainstorm.md
design_admission: admitted
---

# sidebar-settings-click-e2e Feature Design

## 0. 需求摘要

Owner 在 2026-07-27 前台复测确认：普通 pane 单击聚焦已通过，但 sidebar settings 点击无反应。本 feature 只处理 `sidebar-settings-click-e2e`：证明真实 sidebar pane 的鼠标左键点击能从 WezTerm/rmux 经 CCB root binding 到达 `ccb-agent-sidebar` 的 crossterm `Event::Mouse`，并最终触发 config UI 打开或显示可诊断失败状态。

Design admission：本 feature 由 `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/evidence/root-cause-review-and-feature-split.md` 拆分而来；Owner 在 2026-07-27 明确要求“按拆分 feature”继续。自身 brainstorm 已确认，见 `.codestable/features/2026-07-27-sidebar-settings-click-e2e/sidebar-settings-click-e2e-brainstorm.md`。

Workflow ownership：本 split child 作为 `windows-rmux-ux-parity-hardening` 下的独立 roadmap item `sidebar-settings-click-e2e` 恢复；`split_parent` 仅用于追溯失败根因，不作为当前 feature 的执行 owner。

Roadmap trace：父 item `windows-rmux-wezterm-native-interaction-parity` 的 `split_children` 仅保留 trace-only 索引，不携带 `feature` / brainstorm / design admission 字段；canonical owner 只存在于顶层 `sidebar-settings-click-e2e` item 和 roadmap `goal-state.yaml` 的同名 feature row。

### 成功标准

- native Windows + WezTerm + rmux 前台点击 sidebar header settings 控件后，sidebar 能观察到 mouse event。
- 若 config UI 能启动，sidebar 显示 `config ui: <url>` 或等价可见 ready 状态。
- 若 config UI 启动失败，sidebar 显示 `config ui failed: <reason>`，不能静默无反应。
- 诊断证据必须包含真实 sidebar pane 的 `@ccb_role`、`@ccb_sidebar_helper_id`、期望 helper fingerprint、root mouse binding 摘要、mouse event 计数或等价 probe、config UI launch 结果。
- UX parity JSON 必须能拒绝无归因的 non-pass evidence：`partial|blocked|failed` 时必须有 `residual_risks` 或结构化 failure detail；`blocked|failed` 时 `failure_class` 不能是 `none`；`artifacts` 引用必须非空且指向存在文件。

### 明确不做

- 不处理 sidebar `x` KillProject；该路径使用同一 mouse passthrough 诊断结论，但由 `sidebar-kill-project-click-e2e` 独立验收。
- 不处理普通 pane 拖拽选区、右键粘贴、滚轮。
- 不把 `list-keys` 通过写成前台点击通过。
- 不新增长期默认 debug 噪音；若实现需要 probe，必须显式 opt-in 或只在测试/诊断命令中启用。
- 不改变 `ordinary_pane.mouse_policy`，不在本 feature 中关闭全局 `mouse on`。
- 不修改或判定非 Windows/rmux fallback 的 `#{mouse_pane}` 路径；该路径现有 `send-keys c` 坐标命令是否保留不在本 feature 范围内。

## 1. 决策与约束

### 1.1 现有事实

- `tools/ccb-agent-sidebar/src/tui.rs:62-69` 已启用 raw mode、alternate screen 和 crossterm `EnableMouseCapture`。
- `tools/ccb-agent-sidebar/src/tui.rs:89-120` 主循环读取 `Event::Mouse`，左键 down 会调用 `handle_mouse_down()`。
- `tools/ccb-agent-sidebar/src/tui.rs:503-539` `handle_mouse_down()` 命中 settings 后调用 `open_config_ui()`，失败时写入 sidebar error。
- `tools/ccb-agent-sidebar/src/tui.rs:853-858` 已有 config UI 子进程 opening / ready / failed 的状态行，但同步 spawn/launch 失败当前走 `last_error`，现有测试只断言内部错误前缀 `config ui launch failed:`，不足以证明用户可见的 `config ui failed:` 状态。
- `tools/ccb-agent-sidebar/src/tui.rs:1275-1291` `header_action_at()` 负责 settings / kill header hit-test。
- `lib/cli/services/tmux_ui_runtime/service.py:266-290` Windows/rmux fallback 当前通过 `@ccb_role=sidebar` 分流后执行 `select-pane -t = ; send-keys -t = -M`。
- `lib/ccbd/services/project_namespace_runtime/sidebar_helper.py:104-119` 已能计算 sidebar helper sha256 fingerprint。
- `lib/ccbd/services/project_namespace_runtime/materialize_topology.py:580-639` 已按 helper fingerprint respawn stale sidebar 并写回 `@ccb_sidebar_helper_id`。
- `lib/ccbd/services/project_namespace_pane.py:155-185` 和 `189-210` 已能读取 pane role、sidebar helper id 等 namespace pane 信息。

### 1.2 方案深度

候选方案：

- 只改测试断言：拒绝。当前失败来自真实 GUI 前台，负向断言已被证明不足。
- 在 Windows/rmux fallback / `without_mouse_pane_format` 中恢复 mux 层 `send-keys -t = c`：拒绝。它绕过 Rust TUI，无法证明 `send-keys -M` 到 crossterm 的根链路，且会把 settings 与 kill 再次绑在脆弱坐标表达式上。现有非 fallback `#{mouse_pane}` 路径的 `send-keys c` 坐标命令不在本 feature 范围内。
- 增加可观测 e2e probe 并按证据最小修复：采用。该路径先证明 event 是否到达 Rust，再根据证据决定修 binding、pane option、helper refresh 或 config UI launch。

本 feature 是用户直接依赖的前台交互，不能用 mock 代替核心链路；但 native GUI 鼠标动作无法由当前 agent 自动执行，所以设计中允许手工前台 transcript 作为 core evidence，自动化只承担前置与回归保护。

### 1.3 Top 3 风险

1. **事件未到达 Rust 却误判为 hit-test 问题**  
   缓解：先记录 pane option、helper fingerprint、root binding、mouse event probe，再看 `header_action_at()`。

2. **运行的是旧 sidebar binary**  
   缓解：验收必须对比 `@ccb_sidebar_helper_id` 与当前 `sidebar_helper_fingerprint()`；不匹配时先走 helper refresh/respawn 归因。

3. **config UI 启动失败被用户看成点击无反应**  
   缓解：settings 点击后必须显示 opening / ready / failed 状态；失败要有 compact reason。

### 1.4 关键假设

- Owner 的下一轮前台复测仍使用 native Windows + WezTerm + rmux。
- `send-keys -t = -M` 在 rmux 中若被触发，应能把 mouse event 送给已开启 mouse capture 的 sidebar 进程；如果证据否定该假设，本 feature 需要回 design 修订，而不是继续改 Rust hit-test。
- 当前 `ccb-agent-sidebar` 不需要新增常驻日志；若需要 probe，优先做 opt-in 诊断模式或测试专用计数输出。

### 1.5 Baseline reuse / delta

**复用基线**

- 复用 split parent 的根因审查结论：不能把 `list-keys` 或负向绑定断言当作前台 pass。
- 复用现有 Windows/rmux fallback binding 测试，继续保护 sidebar 分支为 `send-keys -t = -M`。
- 复用 Rust sidebar 单元测试中 `header_action_at()`、`handle_mouse_down()`、config UI status line 的本进程逻辑。
- 复用 sidebar helper fingerprint 与 topology refresh 机制，不重做 helper resolution。

**本 feature 增量**

- 新增 settings click 专用的 e2e 诊断证据与前台 transcript。
- 新增或复用 opt-in mouse event/action probe，证明 `send-keys -M` 到达 crossterm 后触发 settings action。
- 只修复 settings 点击链路中被证据证明的最小断点。

## 2. 设计

### 2.1 名词层：现状 → 变化

**现状**

- Sidebar TUI 内部已有 `HeaderMouseAction::Settings`、`ConfigUiLaunchStatus` 和可见 status line，但没有运行时证据说明前台 mouse event 到达了这些分支。
- Namespace pane record 已包含 `sidebar_helper_id`、`role`、`sidebar_instance` 等字段，但 settings 前台 QA 没把这些字段作为必备证据。
- Root mouse binding live test 只证明 `list-keys` 中存在 binding，未证明真实 sidebar pane 命中 `@ccb_role=sidebar` 分支。

**变化**

- 产出 roadmap 兼容的 `WindowsRmuxUxParityEvidence`，顶层字段遵守共享协议；settings 专用字段放入 `details.sidebar_settings_click` 或单独 artifact。
- 新增 opt-in sidebar mouse probe seam：由环境变量或 CLI 参数显式启用，默认关闭；启用时只记录最后一次 mouse event、settings action 是否命中、config UI status，不写无界日志。
- QA 不再接受单纯 `list-keys`、cargo hit-test 单测或 “没有报错” 作为 pass。

示例 evidence：

```json
{
  "schema_version": 1,
  "host_kind": "native_windows",
  "terminal_host": "wezterm",
  "backend_impl": "rmux",
  "control_plane": "ccbd",
  "parity_dimension": "foreground_interaction",
  "evidence_status": "pass",
  "failure_class": "none",
  "artifacts": {
    "settings_click_detail": "evidence/sidebar-settings-click-detail.json",
    "manual_transcript": "evidence/manual-sidebar-settings-click.md"
  },
  "residual_risks": [],
  "details": {
    "sidebar_settings_click": {
      "pane": {
        "role": "sidebar",
        "sidebar_helper_id": "sha256:...",
        "expected_helper_id": "sha256:..."
      },
      "mouse": {
        "binding": "if-shell -F -t = ... send-keys -t = -M ...",
        "event_observed": true,
        "settings_action_observed": true,
        "last_mouse_event": {"kind": "Down(Left)", "column": 12, "row": 0}
      },
      "config_ui": {
        "status": "ready",
        "detail": "http://127.0.0.1:..."
      },
      "failure_detail": null
    }
  }
}
```

### 2.1.1 Opt-in probe seam

Probe 入口必须满足：

- 默认关闭：未设置 probe 参数时，sidebar UI 与 stdout/stderr 不出现调试噪音。
- 显式启用：本 feature 选择单一环境变量入口 `CCB_AGENT_SIDEBAR_MOUSE_PROBE=<path>`，不新增 sidebar CLI 参数。原因是当前 `tools/ccb-agent-sidebar/src/args.rs:34-53` 未知参数会失败，`lib/ccbd/services/project_namespace_runtime/topology_plan.py:162-169` 生成固定 launch args；使用 env 可随 sidebar 进程继承，避免扩大 launch 参数契约。
- 传播方式：QA 需要在启动 `ccb` / `ccbd` / sidebar respawn 前设置 `CCB_AGENT_SIDEBAR_MOUSE_PROBE` 为 feature evidence 目录下的 JSON 路径；若 sidebar 已经运行，必须先触发 sidebar helper refresh/respawn 或重启当前 namespace，确保真实 sidebar pane 继承该 env。
- 父进程要求：若 `ccbd` 已经运行，不能只在当前 shell 设置 env 后假设 sidebar respawn 会继承；QA 必须在该 env 下重启 `ccbd` / namespace，或用进程环境/diagnostic transcript 证明 respawn 父进程已经持有该 env。
- 输出路径：推荐 `.codestable/features/2026-07-27-sidebar-settings-click-e2e/evidence/sidebar-mouse-probe.json`；artifact ref 写入 UX parity JSON 的 `artifacts.settings_click_detail`。
- 清理规则：probe 文件属于 feature evidence；实现不得把该 env 写入用户持久配置，QA 完成后清除当前 shell/session 中的 env。
- 有界输出：只覆盖写当前进程最后一次 mouse event、settings action 命中、config UI status、时间戳和计数，不追加无界日志。
- 可测试：cargo test 可用临时路径或内存替身验证 probe 不影响默认路径。
- 可删除：删掉 probe seam 后只失去诊断证据，不改变正常 settings 点击语义。

### 2.2 编排层：现状 → 变化

**现状**

当前前台路径是线性的，但缺少中间观测：

```text
WezTerm mouse -> rmux root binding -> @ccb_role=sidebar branch -> send-keys -M -> crossterm Event::Mouse -> header_action_at -> open_config_ui
```

失败时任何一段断裂都会表现为“没有反应”，现有测试不能区分断点。

**变化**

本 feature 的实现和 QA 按诊断优先顺序推进：

1. 读取真实 sidebar pane identity：`@ccb_role`、`@ccb_sidebar_helper_id`、window/pane id。
2. 读取 Windows/rmux fallback root mouse binding：确认 sidebar pane 走 `send-keys -t = -M`，不是 fallback mux 层 `send-keys c`。
3. 触发 settings 点击并观察 sidebar 进程内 event/action probe。
4. 若 event/action 到达但 config UI 失败，区分同步 spawn/launch 失败与子进程运行后失败；两者都必须在渲染层出现 `config ui failed: <reason>` 或等价失败状态，而不是只写内部 `last_error`。
5. 若 event 未到达，归因到 rmux binding/pane option/helper instance，不进入 config UI 修复。

该流程不需要复杂状态机，按证据顺序线性推进；每一步失败都能给出不同归因。

### 2.3 挂载点

- Sidebar runtime：`ccb-agent-sidebar` 主循环的 mouse event 观测点。删掉该观测点后，本 feature 无法证明前台点击到达 Rust。
- Sidebar settings action：`open_config_ui()` 的状态反馈。删掉该反馈后，用户仍可能看到“无反应”。
- Project namespace pane identity：真实 sidebar pane 的 role/helper id 证据。删掉后无法区分旧 helper 或 pane option 丢失。
- Sidebar probe env：`CCB_AGENT_SIDEBAR_MOUSE_PROBE` 的 opt-in 诊断入口。删掉后正常点击语义不变，但本 feature 无法在真实 pane 中产出 event/action 证据。
- Feature evidence：`sidebar-settings-click-e2e` 的 JSON/Markdown transcript。删掉后 acceptance 无法复核真实前台路径。

### 2.4 推进策略

1. **基线预检**：确认当前自动化仍绿或明确既有红灯；读取真实可用命令入口。
2. **证据 schema 与 runbook**：先定义 settings click e2e evidence，不让实现阶段临时发明 pass 口径。
3. **运行时最小观测点**：如缺少可观测点，加入 opt-in probe，不污染正常 UI。
4. **settings action 反馈闭环**：确保点击后 ready/failed 都有可见状态。
5. **前台 QA 与 UX parity evidence**：由 owner 或可观察前台环境记录真实 transcript，并生成 `windows-rmux-ux-parity-evidence.json`。

### 2.5 结构健康度与微重构

- 文件级 — `tools/ccb-agent-sidebar/src/tui.rs` 已较长，继续直接追加大段诊断逻辑会加剧职责混杂。实现阶段若需要新增 probe，应优先把纯数据格式化/写 evidence 的逻辑放到新模块或小函数，`tui.rs` 只保留事件钩子。
- 文件级 — `lib/cli/services/tmux_ui_runtime/service.py` 已集中 project UI binding，本 feature不应扩大普通 pane 策略；只允许必要的 sidebar binding 修正或测试保护。
- 目录级 — `tools/ccb-agent-sidebar/src/` 当前模块不多，新增一个窄职责诊断模块是可接受的。

结论：不做预置微重构；实现时遇到 probe 逻辑超过一屏或涉及文件 IO，必须新建窄模块，避免把 `tui.rs` 继续推成混合诊断/渲染/事件处理文件。

## 3. 验收契约

| ID | 触发 | 期望可观察结果 | 证据类型 | Core |
|---|---|---|---|---|
| AC-001 | native Windows + WezTerm + rmux 中读取真实 sidebar pane | `@ccb_role=sidebar`，`@ccb_sidebar_helper_id` 等于当前 `sidebar_helper_fingerprint()` | command transcript / JSON | yes |
| AC-002 | 读取 Windows/rmux fallback root mouse binding | sidebar 分支为 `send-keys -t = -M`，Windows/rmux fallback 不使用 mux 层 `send-keys c` 伪造 settings；非 Windows/rmux 路径不在本 feature 范围 | live rmux list-keys + unit | yes |
| AC-003 | 前台点击 sidebar settings | sidebar 进程观察到 mouse event，且 settings action 被触发 | manual transcript / probe evidence | yes |
| AC-004 | config UI 正常启动 | sidebar 显示 ready URL 或等价 ready 状态 | manual transcript / cargo unit | yes |
| AC-005 | config UI 同步 spawn/launch 失败或子进程运行后失败 | sidebar 渲染层显示 `config ui failed: <reason>` 或等价失败状态，不只是内部 `last_error`，也不是静默无反应 | cargo unit / manual if applicable | yes |
| AC-006 | 缺旧 helper 或 pane option 异常 | QA 归因为 helper/pane identity failure，不误报 Rust hit-test | unit / command transcript | yes |
| AC-007 | 非目标路径 | 不修改 KillProject、普通 pane drag/right/wheel 策略 | diff review / existing tests | yes |

### Acceptance Coverage Matrix

| 场景 | Checklist step | 证据 |
|---|---|---|
| pane identity/fingerprint | S1, S2 | transcript / JSON |
| pane target / role failure | S3 | unit / command transcript |
| binding 内容 | S1, S4 | pytest / live list-keys |
| mouse event/action 到 Rust | S5, S7 | probe/manual |
| settings action 到 config UI | S5, S6, S7 | cargo/manual |
| failure 可见 | S6, S7 | cargo/manual |
| helper stale / pane option 异常归因 | S2, S3 | unit / command transcript |
| scope guard | S8 | diff review / regression tests |

### DoD Contract

| ID | Contract | Evidence | Blocking |
|---|---|---|---|
| DOD-DESIGN-001 | design/checklist/review 均落盘并通过 review gate | files + design-review | yes |
| DOD-IMPL-001 | 真实前台路径至少能定位断点：pane identity、binding、event/action、config UI status | evidence JSON / transcript | yes |
| DOD-IMPL-002 | 正常 UI 不新增默认 debug 噪音 | diff review / tests | yes |
| DOD-QA-001 | native Windows + WezTerm + rmux 前台 settings click 重新验证 | manual transcript | yes |
| DOD-QA-002 | 产出 UX parity JSON，顶层符合 roadmap schema；`evidence_status` 非 pass 时必须写 failure/residual risk | schema validation | yes |
| DOD-GOAL-001 | Goal lane 执行包边界可恢复：feature-local goal package 或 epic goal package projection 指向 design/checklist/review/QA/acceptance/evidence | goal-plan / goal-state / goal-feature projection | yes |

### 必跑验证命令

- `python -m pytest -q -rs test/test_v2_tmux_ui.py`
- `python -m pytest -q -rs test/test_v2_tmux_ui.py -k rmux_accepts_mouse_context_project_ui_bindings`
- `cargo test --manifest-path tools/ccb-agent-sidebar/Cargo.toml --quiet`
- `python -m py_compile lib/cli/services/tmux_ui_runtime/service.py test/test_v2_tmux_ui.py`
- `python -c "import json, pathlib; p=pathlib.Path('.codestable/features/2026-07-27-sidebar-settings-click-e2e/evidence/windows-rmux-ux-parity-evidence.json'); d=json.loads(p.read_text(encoding='utf-8')); req={'schema_version','host_kind','terminal_host','backend_impl','control_plane','parity_dimension','evidence_status','failure_class','artifacts','residual_risks'}; assert req <= d.keys(); assert d['schema_version']==1; assert d['parity_dimension']=='foreground_interaction'; assert d['evidence_status'] in {'pass','partial','blocked','failed'}; assert d['failure_class'] in {'none','rmux_unavailable','wezterm_gui_unavailable','provider_failure','system_failure','test_design_failure','unsupported_capability'}; assert isinstance(d['artifacts'], dict) and d['artifacts']; base=p.parents[1]; assert all(isinstance(v,str) and v.strip() and ((pathlib.Path(v) if pathlib.Path(v).is_absolute() else base/pathlib.Path(v)).exists()) for v in d['artifacts'].values()); assert isinstance(d['residual_risks'], list); detail=d.get('failure_detail') or d.get('details',{}).get('failure_detail') or d.get('details',{}).get('sidebar_settings_click',{}).get('failure_detail'); assert d['evidence_status']=='pass' or d['residual_risks'] or detail; assert d['evidence_status'] not in {'blocked','failed'} or d['failure_class']!='none'"`

### Required artifacts / Goal lane projection

- Design/checklist/review：`sidebar-settings-click-e2e-design.md`、`sidebar-settings-click-e2e-checklist.yaml`、`sidebar-settings-click-e2e-design-review.md`。
- Epic goal projection：`.codestable/roadmap/windows-rmux-ux-parity-hardening/goal-features/sidebar-settings-click-e2e.md` 和 roadmap `goal-state.yaml` 中的同名 feature row。
- Implementation/review/QA/acceptance：`sidebar-settings-click-e2e-review.md`、`sidebar-settings-click-e2e-qa.md`、`sidebar-settings-click-e2e-acceptance.md`。
- Evidence：`evidence/sidebar-mouse-probe.json`、`evidence/manual-sidebar-settings-click.md`、`evidence/windows-rmux-ux-parity-evidence.json`。

### 清洁度规则

- 不新增无条件 debug print/log。
- 不新增临时 TODO/FIXME/XXX。
- 不提交注释掉的旧实现。
- 不把手工前台失败写成 residual pass。

## 4. 架构回写预判

如果本 feature 证明 `send-keys -M` 在 rmux/Windows 下不能稳定送达 crossterm，应回写 roadmap foreground interaction policy：sidebar mouse passthrough 不能继续作为默认假设，需要改为 mux 层命令或其它控制通道。若只是 helper stale 或 pane option 丢失，应沉淀为 supportability/doctor 诊断规则候选。

## 5. 自我批判

- 可证伪性：每条 AC 都是 yes/no；`无反应` 被拆成 identity、binding、event/action、config UI 四段。
- 步骤原子性：settings 与 kill 没合并；本 feature 只做 settings。
- 最弱依赖：真实 GUI 前台仍需 owner 操作，已作为 core evidence 写入，不用自动化替代。
- 证据完整性：自动化覆盖 binding/Rust 状态；前台 transcript 覆盖真实 mouse event。
- 清洁度：probe 必须 opt-in，防止把诊断噪音带入日常 sidebar。
