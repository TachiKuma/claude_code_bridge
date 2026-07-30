# sidebar-kill-project-click-e2e diagnosis

## 结论

当前 `sidebar-kill-project-click-e2e` 不应声明为前台点击通过。内部 Rust 路径已经有测试覆盖：header `x` hit-test 会返回 `ExitAction::KillProject`，`Q` / `Shift+Q` 会触发 KillProject，`run_ccb_kill_with_program` 会在项目目录下调用 `ccb kill`。但真实 Windows + WezTerm + rmux 前台点击链路仍没有证据证明 `x` click 到达 Rust/crossterm `Event::Mouse`。

因此本 child 的本轮终态是 `blocked/unsupported_capability` evidence，而不是 parity pass。

## 证据

- Root-cause split 把 `sidebar-kill-project-click-e2e` 标为 failed，并要求单独 design diagnostic feature。
- `sidebar-settings-click-e2e` 真实前台复测证明 rmux root binding 可触发，但 `send-keys -M` 未进入 Rust/crossterm mouse event。
- `sidebar-settings-rmux-mouse-routing` 能力审计证明当前 rmux 只能区分 sidebar pane，不能在普通 root binding 中暴露 settings / x 级坐标或等价谓词。
- `tools/ccb-agent-sidebar/src/tui.rs` 内部路径：
  - `header_action_at()` 能识别 controls 第三列为 `HeaderMouseAction::KillProject`。
  - `handle_mouse_down()` 对 `HeaderMouseAction::KillProject` 返回 `ExitAction::KillProject`。
  - `run()` 在收到 `ExitAction::KillProject` 后调用 `run_ccb_kill()`。
  - `run_ccb_kill_with_program()` 在 `project_root` 目录执行 `ccb kill`。

## 不接受的路线

- 不把任意 sidebar 左键映射为 KillProject。该 fallback 不能区分 settings、`x`、普通 sidebar 行、comms action，且具有破坏性。
- 不把键盘 `Q` / `Shift+Q` 通过当作 `x` mouse click pass。
- 不在当前工作区执行真实 `ccb kill`。

## 下一步

如果未来要把该 child 从 blocked 改为 pass，需要先有 x-only mouse route：rmux 暴露精确坐标 / 等价谓词，或其他可证明只命中 header `x` 的安全通道。实现后必须重新 review、QA，并做真实 foreground 验收。
