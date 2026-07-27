---
doc_type: feature-design
feature: 2026-07-27-sidebar-settings-rmux-mouse-routing
status: approved
execution_lane: goal
summary: "研究并实现 Windows/rmux 下 sidebar settings-only 鼠标通道，或产出 unsupported capability evidence"
tags: [windows, rmux, wezterm, sidebar, mouse, capability]
roadmap: windows-rmux-ux-parity-hardening
roadmap_item: sidebar-settings-rmux-mouse-routing
split_parent: sidebar-settings-click-e2e
brainstorm: .codestable/features/2026-07-27-sidebar-settings-rmux-mouse-routing/sidebar-settings-rmux-mouse-routing-brainstorm.md
design_admission: admitted
---

# sidebar-settings-rmux-mouse-routing Feature Design

## 0. 需求摘要

本 feature 承接 `sidebar-settings-click-e2e` 的 blocked 结论：真实 Windows + WezTerm + rmux 前台点击能触发 rmux root binding，但 rmux 没有提供 `mouse_x/mouse_y`，`send-keys -t = -M` 没有进入 Rust/crossterm `Event::Mouse`。settings 键盘快捷键 `c` 和 config UI 路径健康，但 broad sidebar-left-click fallback 已被 owner 拒绝。

目标是在不影响 `x` KillProject、普通 sidebar click、普通 pane drag/right/wheel 的前提下，找到 settings-only 通道；如果当前 rmux/WezTerm 能力不支持，则产出可复现 capability evidence，并投影为 `unsupported_capability`。

Design admission：本 feature 自身 brainstorm 已确认，见 `sidebar-settings-rmux-mouse-routing-brainstorm.md`。Owner 明确选择“不接受 broad fallback”，并要求按拆分 feature 继续。

### 成功标准

- 可实现路径：真实前台点击 settings 只打开 config UI；点击 `x` 不打开 settings；点击普通 sidebar 区域不打开 settings；普通 pane drag/right/wheel 不被本 feature 改变。
- 不可实现路径：evidence 明确证明 rmux 无 settings-only 所需坐标/透传能力，且 WezTerm 也没有可接受的精确替代通道；UX parity JSON 为 `blocked`，`failure_class=unsupported_capability`。
- 两条路径都必须保留 direct `c` 作为诊断证据，不把它伪装成 mouse pass。

### 明确不做

- 不恢复“sidebar 任意左键打开 settings”。
- 不把 settings-only 问题和 `x` KillProject 修复合并。
- 不改变普通 pane GUI-native 策略，不修普通 pane 拖拽、右键、滚轮。
- 不把不可验证的 WezTerm 全局鼠标绑定写入默认配置。
- 不提交 token、完整 config UI URL secret 或无界 debug 日志。

## 1. 决策与约束

### 1.1 现状

- `lib/cli/services/tmux_ui_runtime/service.py` 的 tmux 路径依赖 `mouse_x/mouse_y` 判断 settings/x 坐标；Windows/rmux fallback 因 `_mouse_pane_format_supported()` 返回 false，只能在 `@ccb_role=sidebar` 时执行 `select-pane -t = ; send-keys -t = -M`。
- `tools/ccb-agent-sidebar/src/tui.rs` 已能处理 crossterm `Event::Mouse`，settings hit-test 和 `c` 快捷键都会打开 config UI。
- `tools/ccb-agent-sidebar/src/mouse_probe.rs` 已能区分 `event_observed`、`settings_action_observed` 和脱敏 config UI 状态。
- 父 feature 的前台 evidence 已记录：rmux root binding 命中；coordinate probe 为 `,,41,0,0,sidebar`；`send-keys -M` 未进入 Rust mouse event。

外部能力基线：

- tmux manual 定义 `send-keys -M` 用于把 mouse event 转发给 pane，这是当前设计想在 rmux 上复用的语义。
- WezTerm 文档说明应用启用 mouse reporting 后，mouse 事件会被发送给应用，普通 mouse assignment 只有在事件不被应用捕获时匹配；因此 WezTerm 替代路径必须经过真实前台验证，不能只看配置可写。

### 1.2 方案深度

本 feature 不能用 mock 或单测直接宣称 pass，因为失败发生在真实 terminal/mux 前台链路。采用 capability-first 深度：

1. 审计 rmux/tmux mouse 语义差异和 live capability。
2. 只在能表达 settings-only 的情况下接入行为。
3. 不能表达时产出 unsupported evidence，而不是写宽泛 fallback。

### 1.3 Top 3 风险

1. **误把全 sidebar fallback 当作 settings-only**  
   缓解：验收必须反向点击 `x` 和普通 sidebar 区域，证明不会打开 settings。

2. **WezTerm 绑定在 mouse reporting 开启时不生效或过宽**  
   缓解：WezTerm 方案必须有前台 transcript；无法限定 cell/区域时直接否决。

3. **unsupported evidence 不够可复现**  
   缓解：evidence 必须包含 rmux 版本/源码 ref、live `display-message/list-keys` 输出、`send-keys -M` probe、WezTerm 行为说明和最终 transcript。

### 1.4 关键假设

- 当前目标环境仍是 native Windows + WezTerm + rmux 前台。
- rmux 不兼容 tmux 的部分格式或 mouse passthrough 是能力边界，而不是 CCB helper stale；父 feature 已先排除 helper/settings action 健康问题。
- 如果 rmux 后续版本支持坐标或透传，本 feature 的 evidence schema 应能记录“当前版本 blocked / 新版本 pass”的差异。

### 1.5 Baseline reuse / delta

**复用基线**

- 复用 `sidebar-settings-click-e2e` 的 foreground retest：helper/settings action/config UI 健康，root binding 可命中 sidebar，当前 rmux 坐标为空且 `send-keys -M` 未进入 Rust。
- 复用父 feature 的 UX parity JSON 负向投影，作为本 feature 的 split-parent evidence。
- 复用 `tools/ccb-agent-sidebar/src/mouse_probe.rs` 的 opt-in probe，不重新定义 token 脱敏或 settings action 健康口径。
- 复用 `test/test_v2_tmux_ui.py` 中禁止 `send-keys -t = c` broad fallback 的回归保护。

**本 feature 增量**

- 只补 rmux/WezTerm capability matrix、`selected_route` 和当前 child 的 UX parity JSON projection。
- 若 rmux 提供坐标或等价 settings-only 条件，即使 `send-keys -M` 仍不透传，也允许采用“精确坐标命中后发送 `c`”的 settings-only mux route。
- `send-keys -M` passthrough 只作为 ordinary sidebar mouse passthrough 能力记录，不作为 settings-only route 的必要条件。
- 若没有精确坐标/等价条件，也没有 WezTerm 精确通道，则只更新 unsupported evidence，不改运行时点击行为。

## 2. 设计

### 2.1 名词层：现状 → 变化

**现状**

- `WindowsRmuxUxParityEvidence` 只有 settings click blocked 结果，缺少专门表达 rmux/WezTerm capability matrix 的字段。
- rmux fallback 只有 sidebar/non-sidebar 二分，无法区分 settings/x/普通 sidebar 坐标。
- direct `c` 只证明 Rust settings action 健康，不证明 mouse routing。

**变化**

新增 feature-local capability evidence：

```json
{
  "rmux_capability": {
    "version": "<recorded>",
    "mouse_target_equals_supported": true,
    "coordinates_or_equivalent_supported": false,
    "send_keys_dash_m_passthrough_supported": false,
    "source_refs": ["..."],
    "live_probe_refs": ["evidence/rmux-mouse-capability.md"]
  },
  "wezterm_capability": {
    "mouse_reporting_assignment_precise": false,
    "accepted_as_settings_only_channel": false,
    "evidence_ref": "evidence/wezterm-settings-only-channel.md"
  },
  "selected_route": "unsupported_capability"
}
```

`windows-rmux-ux-parity-evidence.json` 保持 roadmap 顶层 schema，把上述文件作为 artifact，并在 `details.sidebar_settings_routing` 中摘要最终结论。

### 2.2 编排层：现状 → 变化

**现状**

```text
WezTerm mouse -> rmux root binding -> sidebar branch -> send-keys -M -> no crossterm event
```

**变化**

```text
Capability audit
  -> rmux supports coordinates or equivalent settings-only condition?
      -> yes: use precise mux condition; settings sends c, x/ordinary sidebar never send settings
      -> no: WezTerm precise settings-only binding available?
          -> yes: add opt-in/default-safe settings-only terminal-layer channel
          -> no: emit unsupported_capability evidence
```

实现阶段只能选择其中一条终态路径：

- `rmux_precise_route`：必须证明 `mouse_x/mouse_y` 或等价字段能表达 settings 区域。settings 命中后可以发送 `c` 触发既有 settings action；`send-keys -M` 透传只作为 ordinary sidebar mouse passthrough 能力记录，不阻塞 settings-only route。接入后必须保留 x/ordinary sidebar 反向测试。
- `wezterm_precise_route`：必须证明绑定只在 settings cell/区域触发，不能覆盖 `x` 或普通 pane。若需要用户配置，必须显式记录启用方式和禁用方式。
- `unsupported_capability`：不改运行时行为，只补 evidence、supportability 投影和回归测试，避免未来误加 broad fallback。

### 2.3 挂载点

- Rmux mouse binding builder：仅当 `rmux_precise_route` 成立时修改；删掉后 settings-only mux 通道消失。
- WezTerm integration/runbook：仅当 `wezterm_precise_route` 成立时新增；删掉后 terminal-layer settings-only 通道消失。
- Capability evidence artifacts：无论实现或 blocked 都必须新增；删掉后 supportability 无法复核 blocked/pass。
- UX parity JSON projection：把本 feature 结论投影给后续 supportability。
- 回归测试：禁止 broad fallback，保护 x/ordinary sidebar 不被 settings 覆盖。

### 2.4 推进策略

1. **rmux capability audit**：记录 rmux 版本、相关 mouse binding/source 语义、`list-keys` / `display-message` / `send-keys -M` probe。
2. **WezTerm precise route audit**：只验证 settings-only 能力；不能精确到区域则否决。
3. **选择终态路线**：在 design contract 内只能选 `rmux_precise_route`、`wezterm_precise_route` 或 `unsupported_capability`。
4. **最小接入或 blocked 投影**：可实现才改 runtime；不可实现只补 evidence，不写退化。
5. **前台验证与反向验收**：真实点击 settings、`x`、普通 sidebar、普通 pane wheel/drag/right 的 scope guard。

### 2.5 结构健康度与微重构

- `lib/cli/services/tmux_ui_runtime/service.py` 已集中 session theme、mouse binding、pane theme 多职责。本 feature 若只补 guard/test，不做微重构；若新增 rmux capability 分支超过一个小函数，应提取窄职责 helper，避免继续扩大 `_apply_sidebar_mouse_controls_without_mouse_pane_format()`。
- `tools/ccb-agent-sidebar/src/tui.rs` 已很长。本 feature 不应在其中追加 WezTerm/rmux 研究逻辑；probe 和 evidence 继续放在独立模块或 feature evidence 文件。
- `.codestable/features/.../evidence/` 是 capability artifacts 的自然位置，不需要新增全局 schema 模块。

结论：不做预置微重构；实现阶段只允许为新增 capability helper 做小范围提取，且必须保持行为等价。

## 3. 验收契约

| ID | 触发 | 期望可观察结果 | 证据类型 | Core |
|---|---|---|---|---|
| AC-001 | 运行 rmux mouse capability probe | 记录 rmux 版本、`=` target、坐标/等价 settings-only 条件、`send-keys -M` 透传是否支持 | command transcript / source ref | yes |
| AC-002 | 审查 WezTerm precise route | 明确是否能在 mouse reporting 场景下精确触发 settings-only；不能则记录否决原因 | docs/source ref / manual probe | yes |
| AC-003 | 若选择实现路线，点击 settings | config UI 打开或显示 ready，且 evidence 标记 route | manual foreground transcript | yes |
| AC-004 | 点击 sidebar `x` 和普通 sidebar 区域 | 不打开 settings；`x` 仍留给 KillProject feature 验收，不被 settings 覆盖 | manual transcript / regression test | yes |
| AC-005 | 普通 pane drag/right/wheel smoke | 本 feature 没新增劫持；若仍失败，归属原拆分项，不归因到 settings routing | manual transcript / diff review | yes |
| AC-006 | 不可实现路径 | UX parity JSON 为 `blocked` 且 `failure_class=unsupported_capability`，residual risk 非空 | JSON validator | yes |
| AC-007 | 清洁度 | 无 token 泄露、无默认 debug 输出、无 broad fallback | rg / diff review | yes |

### Acceptance Coverage Matrix

| 场景 | Checklist step | 证据 |
|---|---|---|
| rmux 坐标/透传能力 | S1 | `evidence/rmux-mouse-capability.md` |
| WezTerm settings-only 可行性 | S2 | `evidence/wezterm-settings-only-channel.md` |
| 终态路线选择 | S3 | design/evidence route summary |
| runtime 接入或 blocked 投影 | S4 | code diff 或 evidence JSON |
| settings/x/ordinary 反向验证 | S5 | foreground transcript |
| schema/清洁度 | S6 | validators / rg |

### DoD Contract

| ID | Contract | Evidence | Blocking |
|---|---|---|---|
| DOD-001 | 不能存在 broad sidebar-left-click settings fallback | tests / diff review | yes |
| DOD-002 | 终态 route 必须三选一且有证据 | capability JSON / markdown | yes |
| DOD-003 | pass 只能来自真实前台 settings-only 点击 | manual transcript | yes |
| DOD-004 | blocked 必须投影 unsupported capability | UX parity JSON | yes |

### 必跑验证命令

- `$env:PYTHONDONTWRITEBYTECODE='1'; python "C:/Users/Administrator/.codex/plugins/cache/codestable/codestable/1.0.4/skills/cs-onboard/tools/validate-yaml.py" --file ".codestable/roadmap/windows-rmux-ux-parity-hardening/windows-rmux-ux-parity-hardening-items.yaml"`
- `$env:PYTHONDONTWRITEBYTECODE='1'; python "C:/Users/Administrator/.codex/plugins/cache/codestable/codestable/1.0.4/skills/cs-onboard/tools/validate-yaml.py" --file ".codestable/features/2026-07-27-sidebar-settings-rmux-mouse-routing/sidebar-settings-rmux-mouse-routing-checklist.yaml" --yaml-only`
- `$env:PYTHONPATH='lib'; python -m pytest -q -rs test/test_v2_tmux_ui.py`
- `cargo test --manifest-path tools/ccb-agent-sidebar/Cargo.toml --quiet`
- `python -c "import json, pathlib; p=pathlib.Path('.codestable/features/2026-07-27-sidebar-settings-rmux-mouse-routing/evidence/windows-rmux-ux-parity-evidence.json'); d=json.loads(p.read_text(encoding='utf-8')); req={'schema_version','host_kind','terminal_host','backend_impl','control_plane','parity_dimension','evidence_status','failure_class','artifacts','residual_risks'}; assert req <= d.keys(); assert d['schema_version']==1; assert d['host_kind']=='native_windows'; assert d['terminal_host']=='wezterm'; assert d['backend_impl']=='rmux'; assert d['control_plane']=='ccbd'; assert d['parity_dimension']=='foreground_interaction'; assert d['evidence_status'] in {'pass','partial','blocked','failed'}; assert d['failure_class'] in {'none','rmux_unavailable','wezterm_gui_unavailable','provider_failure','system_failure','test_design_failure','unsupported_capability'}; assert isinstance(d['artifacts'], dict) and d['artifacts']; base=p.parents[1]; assert all(isinstance(v,str) and v.strip() and ((pathlib.Path(v) if pathlib.Path(v).is_absolute() else base/pathlib.Path(v)).exists()) for v in d['artifacts'].values()); assert isinstance(d['residual_risks'], list); detail=d.get('failure_detail') or d.get('details',{}).get('failure_detail') or d.get('details',{}).get('sidebar_settings_routing',{}).get('failure_detail'); assert d['evidence_status']=='pass' or d['residual_risks'] or detail; assert d['evidence_status'] not in {'blocked','failed'} or d['failure_class']!='none'"`

## 4. 架构回写预判

如果最终是 `unsupported_capability`，supportability feature 必须把 Windows/rmux sidebar settings mouse click 标为 blocked 或 beta residual risk，不能宣称 foreground interaction full parity。若发现 rmux 新版本支持坐标/透传，需要把版本能力条件写入 diagnostics，而不是无条件启用。

## 5. 自我批判

- 可证伪性：每条路线都有正反证据；blocked 不是模糊结论。
- 步骤原子性：能力审计、路线选择、接入/投影、前台验证分离。
- 最弱依赖：真实前台 mouse 行为仍需 owner 环境；design 把它列为 core evidence，不用单测替代。
- 证据完整性：rmux、WezTerm、runtime、UX JSON 四类证据都可独立复核。
- 清洁度：明确禁止 broad fallback、token 泄露和默认 debug。
