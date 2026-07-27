# rmux mouse capability audit

## 结论

- rmux 版本：`rmux 0.9.0`
- 源码快照：`9f007bf635a3904322737d90fc86dc7bf9224aa5`，提交时间 `2026-07-24 21:26:40 +0200`
- `=` / `{mouse}` target：支持。源码和测试显示 attached binding command queue 会保留 `mouse_target`，`if-shell -t {mouse}` 可解析并在无 live mouse target 时回退到 server fallback。
- `coordinates_or_equivalent_supported`: `false`
- `send_keys_dash_m_passthrough_supported`: `false`，针对当前 CCB sidebar 前台链路；rmux 源码存在 `send-keys -M` 协议字段和编码路径，但父 feature 前台 probe 已证明 sidebar helper 没收到 crossterm mouse event。
- settings-only route 判断：当前 rmux 能区分 mouse target pane，但不能在普通 pane root binding 中暴露 settings hit-test 所需的 cell 坐标或等价条件，因此不能实现 `rmux_precise_route`。

## Live probe

目标 namespace：`ccb-claude_code_bridge-b72b0116`

```text
> rmux -V
rmux 0.9.0

> rmux -L ccb-claude_code_bridge-b72b0116 display-message -p "#{session_name}|#{window_name}|#{pane_id}|#{@ccb_role}|#{mouse_x}|#{mouse_y}|#{mouse_pane}|#{pane_width}|#{pane_height}"
ccb-claude_code_bridge-b72b0116|main|%0|sidebar||||41|64

> rmux -L ccb-claude_code_bridge-b72b0116 display-message -a
mouse_all_flag=0
mouse_any_flag=0
mouse_button_flag=0
mouse_hyperlink=
mouse_line=
mouse_pane=
mouse_sgr_flag=0
mouse_standard_flag=0
mouse_status_line=
mouse_status_range=
mouse_utf8_flag=0
mouse_word=
mouse_x=
mouse_y=
pane_height=64
pane_id=%0
pane_left=0
pane_top=0
pane_width=41
session_name=ccb-claude_code_bridge-b72b0116
window_name=main
```

当前 root binding：

```text
MouseDown1Pane:
if-shell -F -t = "#{==:#{@ccb_role},sidebar}" "select-pane -t = ; send-keys -t = -M" "select-pane -t ="

MouseDown1Border:
if-shell -F -t = "#{==:#{@ccb_role},sidebar}" "select-pane -t = ; send-keys -t = -M" "select-pane -t ="

MouseDrag1Border:
resize-pane -M
```

解释：

- live `display-message` 能看到 `%0` pane、`@ccb_role=sidebar`、pane width/height。
- `mouse_x`、`mouse_y`、`mouse_pane` 在当前普通 command context 中为空。
- 这只能支撑“sidebar pane 二分”，不能支撑 settings / `x` / 普通 sidebar 区域三分。

## Source review

本地 rmux 源码临时审计目录：

```text
C:\Users\Administrator\AppData\Local\Temp\rmux-src-audit-413df37ca9b84bf982a7254422e7520e
```

关键源码事实：

- `src/cli/key_commands.rs`：`send-keys -M` 会把 `args.mouse` 写入 `SendKeysExtRequest.forward_mouse_event` 或 `SendKeysExt2Request.forward_mouse_event`。
- `crates/rmux-server/src/handler_pane/attached_key_dispatch/commands.rs`：attached binding command queue 带有 `mouse_target` 与 `mouse_event`，并通过 `QueueExecutionContext.with_mouse_target(...).with_mouse_event(...)` 传给后续命令。
- `crates/rmux-server/src/handler_scripting.rs`：`resize-pane -M` 直接消费 `AttachedMouseEvent` 的 `raw.x/raw.y/raw.lx/raw.ly` 计算 pane resize adjustment。
- `tests/windows_mouse_border_resize.rs`：`display-message dragged ; resize-pane -M` pipeline 测试证明 border drag command pipeline 会保留 `mouse_event`。
- `src/cli_args_tests/scripting_and_buffers.rs` 与 `tests/scripting.rs`：`if-shell -t {mouse}` 能解析；没有 live mouse target 时会使用 server fallback。
- `crates/rmux-core/src/formats/context.rs`：`mouse_x`、`mouse_y`、`mouse_pane` 在 token 列表中存在。
- `crates/rmux-server/src/handler_overlay/commands.rs`：`mouse_x`/`mouse_y` 的实际 `with_named_value` 注入发生在 overlay/display-menu 相关 runtime，普通 root binding 的 display-message/if-shell format runtime 未发现等价注入路径。

## Capability matrix

```json
{
  "rmux_capability": {
    "version": "rmux 0.9.0",
    "source_commit": "9f007bf635a3904322737d90fc86dc7bf9224aa5",
    "mouse_target_equals_supported": true,
    "coordinates_or_equivalent_supported": false,
    "send_keys_dash_m_passthrough_supported": false,
    "ordinary_mouse_event_pipeline_supported": true,
    "settings_only_route_supported": false
  }
}
```

## TDD exception

本 step 是能力审计和前台链路证据采集，不改变 runtime 行为。自动化单测无法模拟真实 Windows + WezTerm + rmux foreground mouse event 是否暴露坐标；替代证据为 live rmux command transcript、父 feature foreground probe 与 rmux 源码审计。
