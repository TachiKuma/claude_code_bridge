# WezTerm settings-only channel audit

## 结论

- WezTerm 版本：`wezterm 20251201-075747-d3b0fdad`
- `mouse_reporting_assignment_precise`: `false`
- `accepted_as_settings_only_channel`: `false`
- 本 feature 不接入 WezTerm terminal-layer route。

WezTerm 支持 `mouse_bindings`，也支持 `mouse_reporting=true` 的绑定；但该绑定的匹配维度是 mouse event、modifier、`mouse_reporting`、`alt_screen`，没有 settings cell / terminal grid coordinate / CCB sidebar role 这类区域谓词。把单击左键绑定到 `SendString("c")` 或 `action_callback` 只能成为 pane-wide 或 terminal-wide shortcut，无法证明只命中 settings。

## 文档事实

官方文档审计时间：2026-07-27。

- Mouse binding 文档说明：当应用启用 mouse event tracking 时，mouse events 默认不会匹配 WezTerm mouse assignments，而是传给应用。通过 `SHIFT` 或 `bypass_mouse_reporting_modifiers` 可以绕过应用 mouse reporting。
  - URL: `https://wezterm.org/config/mouse.html`
  - Relevant lines: 783-789
- Mouse binding entry 的字段只有 `event`、`mods`、`action`、`mouse_reporting`、`alt_screen`。
  - URL: `https://wezterm.org/config/mouse.html`
  - Relevant lines: 863-870
- `mouse_reporting=true` entry 会在 pane 当前 mouse reporting 状态匹配时才考虑，但文档也警告它会阻止 pane 内应用收到该 mouse event。
  - URL: `https://wezterm.org/config/mouse.html`
  - Relevant lines: 867-868
- `window:current_event()` 目前只实现给 mouse event 使用，文档示例暴露的是当前 wheel delta；没有提供可用于声明 settings cell hit-test 的配置级匹配字段。
  - URL: `https://wezterm.org/config/lua/window/current_event.html`
  - Relevant lines: 772-791
- `bypass_mouse_reporting_modifiers` 默认是 `SHIFT`，语义是阻止事件传给应用并让它进入 mouse assignment matching；这不是无修饰 settings-only click。
  - URL: `https://wezterm.org/config/lua/config/bypass_mouse_reporting_modifiers.html`
  - Relevant lines: 772-781

## Local probe

```text
> wezterm --version
wezterm 20251201-075747-d3b0fdad

> wezterm show-keys --lua
有效默认 key/mouse assignment 可枚举；未发现内置按 terminal cell 区域匹配的 mouse binding 条目。
```

## Route analysis

候选 1：`mouse_reporting=true` + `Down Left` + `SendString("c")`

- 可触发：可能。
- settings-only：否。匹配范围是当前 pane 的所有左键，不知道用户点的是 settings、`x` 还是普通 sidebar 区域。
- 反向风险：会拦截应用 mouse event；可能改变普通 pane/普通 sidebar 行为。

候选 2：`action_callback(function(window, pane) ... end)` + `window:current_event()`

- 可触发：可能。
- settings-only：否。`current_event()` 文档只提供当前 mouse event 的结构，不提供 CCB sidebar settings cell 的稳定 pane-local坐标契约；即使运行时能拿到某些 mouse event 细节，也没有 CCB pane role / hit-test 信息，不能区分 settings 和 `x`。
- 反向风险：需要外部 WezTerm config 参与，不属于当前默认安全通道；误配会形成 broad fallback。

候选 3：`SHIFT`/`bypass_mouse_reporting_modifiers`

- 可触发：可能。
- settings-only：否。它改变用户手势，从普通左键变成带修饰绕过 mouse reporting 的点击；不满足本 feature 的“真实 settings 单击”目标。
- 反向风险：不是 CCB 默认 UX parity，且会改变用户已有 WezTerm mouse assignment 行为。

## Capability matrix

```json
{
  "wezterm_capability": {
    "version": "wezterm 20251201-075747-d3b0fdad",
    "mouse_reporting_assignment_supported": true,
    "mouse_reporting_assignment_precise": false,
    "coordinate_or_region_predicate_supported": false,
    "accepted_as_settings_only_channel": false,
    "rejection_reason": "WezTerm mouse binding schema cannot express CCB sidebar settings-only hit-test; mouse_reporting=true would intercept pane-wide mouse events."
  }
}
```

## TDD exception

本 step 是外部 terminal 能力审计，不改 runtime 行为。自动化测试无法证明 WezTerm 前台 config route 的安全范围；替代证据为官方文档、`wezterm --version` 与 `show-keys` 本地探针。
