---
doc_type: issue-fix
issue: 2026-07-24-rmux-pane-scroll-history
status: confirmed
path: fast-track
fix_date: 2026-07-24
tags:
  - windows
  - rmux
  - tmux
  - mouse
  - scroll
  - sidebar
---

# rmux 鼠标交互修复记录

## 问题描述

用户反馈 CCB 源码版在 Windows + WezTerm + rmux 前台交互链路中存在两类鼠标异常：

- agent / CLI pane 不能用鼠标滚轮翻看前面的聊天内容；sidebar 仍能选中 pane，但 chat 输出无法滚动回看。
- sidebar 左上角 `⚙` / `×` 鼠标点击无响应。

补充运行时事实：sidebar 聚焦时按 `c`，Comms 中出现 config UI 启动提示，浏览器也成功打开配置面板。由此确认 config UI 功能本身可用，问题集中在 rmux 鼠标事件绑定 / 透传链路。

## 根因

- 旧的 root wheel 绑定把 `alternate_on` 也当成“交给应用处理”的条件。对 AI CLI pane 来说，这会把滚轮事件继续送回 pane 本身，而不是进入 tmux copy-mode，因此看不到历史聊天输出。
- 非 sidebar pane 的 wheel 动作没有显式指定鼠标所在 pane，可能作用到当前焦点 pane，而不是用户滚轮所在 pane。
- sidebar header 的 `⚙` / `×` 点击依赖 `send-keys -M` 把鼠标事件透传给 Rust sidebar TUI；在 rmux + WezTerm attach 场景下，header 鼠标事件透传不可靠。键盘 `c` 可用说明应在绑定层把 header 点击直接转换为等价按键。

## 修复方案

- 保持 sidebar pane 的 wheel 走鼠标透传，继续支持 sidebar 自己的内部滚动。
- 对其他 pane 的 wheel 绑定改成只在鼠标所在 pane 的 `pane_in_mode` 为真时透传；其余情况直接对鼠标所在 pane 执行 `copy-mode -e -t =`，再用 `send-keys -t = -X -N 2 scroll-up/down` 滚动历史。
- 在 `MouseDown1Pane` / `MouseDown1Border` 绑定层识别 sidebar header 的 `⚙` / `×` 坐标：
  - `⚙` 直接发 `c` 到鼠标所在 sidebar pane，打开 config UI。
  - `×` 直接发 `Q` 到鼠标所在 sidebar pane，沿用 Rust sidebar 现有 `KillProject` 语义。
- 所有 sidebar/header/wheel 分流条件均使用 `if-shell -F -t =`，避免条件按当前焦点 pane 求值。
- 其他 sidebar 鼠标点击仍走原有透传路径，非 sidebar top border 点击仍保留 `select-pane -M` 行为。
- 同步更新测试断言，覆盖 header 两个按钮和非 sidebar wheel 的 `-t =` 目标。

## 改动文件

- `lib/cli/services/tmux_ui_runtime/service.py`
- `test/test_v2_tmux_ui.py`

## 验证结果

- `python -m py_compile "lib/cli/services/tmux_ui_runtime/service.py" "test/test_v2_tmux_ui.py"`：通过。
- `python -m pytest -q "test/test_v2_tmux_ui.py" -k "apply_project_tmux_ui_sets_session_theme_and_hook_from_current_install_root or windows_rmux_project_ui_avoids_shell_status_commands"`：通过。
- `python -m pytest -q "test/test_v2_tmux_ui.py"`：`12 passed, 2 skipped`。
- 已将新绑定应用到当前 `.ccb/ccbd/state.json` 指向的 rmux session。
- `rmux -L <session> if-shell -F -t %1 "#{pane_id}" "display-message ok" "display-message no"`：通过，确认 rmux 0.9.0 接受 `if-shell -F -t <pane>`。
- `rmux -L <session> list-keys -T root` 已确认 `MouseDown1Pane`、`MouseDown1Border`、`WheelUpPane`、`WheelDownPane` 包含 `if-shell -F -t =`，并包含 `send-keys -t = Q`、`copy-mode -e -t =`、`send-keys -t = -X -N 2 scroll-up/down`。
- 对 agent pane 手动执行 `copy-mode -e -t %1` 后，`pane_in_mode` 变为 `1`；随后 `send-keys -t %1 -X -N 2 scroll-up/down` 返回正常，`send-keys -t %1 q` 后退出 copy-mode。
- 对 sidebar pane 手动执行 `send-keys -t %0 c`，capture 显示 `ccb -a`，说明键盘路径能触发 config UI 启动命令。

## 遗留风险

- `×` 的代码语义是 `KillProject`，不是单纯关闭 sidebar；如果需要“关闭 sidebar 但不 kill project”，应另开 feature / UX 调整，不并入本 bug。
- 本轮已刷新当前 rmux session 绑定，但真实鼠标点击和滚轮仍需要用户在 WezTerm 前台 TUI 里做最终手工确认。
- 这次修复优先保证 CCB 的聊天 pane 能滚回历史输出；如果某些非 sidebar 交互式 TUI 依赖 wheel 自身处理鼠标事件，行为会和以前不同。

## 追加修复：Windows + WezTerm + rmux 鼠标目标与 Shift+Q

> 说明：上文首次修复记录里的 `-t =` 方案已被本节追加修复取代；最终实现以显式 `#{mouse_pane}` 为准。

用户复测反馈：`×` 的既有语义虽然是 `KillProject`，但 sidebar 焦点下按 `Q` 只关闭了 sidebar，其他 pane 仍然显示；滚轮历史回看也没有改善。

本轮进一步定位到两个 v8 原生 Windows/rmux 特有兼容点：

1. Rust sidebar 原先只把 `KeyCode::Char('Q')` 识别为 `KillProject`。在 Windows/WezTerm/crossterm 链路中，Shift+Q 可能被表示成 `KeyCode::Char('q') + KeyModifiers::SHIFT`，旧匹配会先落入普通 `q` 的 `SidebarOnly` 分支，因此只退出 sidebar。
2. Python tmux/rmux mouse 绑定依赖特殊 target `=` 表示“鼠标所在 pane”。rmux 0.9.0 在 Windows attach 场景下对 `=` 的 mouse target 行为与 tmux 不完全一致，sidebar 有焦点时容易按焦点 pane 求值/送键，导致滚轮仍作用不到鼠标所在 agent pane。

追加改动：

- `tools/ccb-agent-sidebar/src/tui.rs`
  - 新增 `exit_action_for_key()`，把 `Char('Q')` 和 `Char('q') + SHIFT` 都映射为 `KillProject`，普通 `q` / Esc 仍只关闭 sidebar。
- `lib/cli/services/tmux_ui_runtime/service.py`
  - root mouse/header/wheel 绑定从 `-t =` 改为显式 `-t "#{mouse_pane}"`。
  - sidebar header 的 `⚙` / `×`、sidebar mouse passthrough、非 sidebar wheel copy-mode 都统一使用 mouse pane 目标。
- `test/test_v2_tmux_ui.py`
  - 更新绑定断言，覆盖 `#{mouse_pane}` 目标。

追加验证：

- `python -m py_compile "lib/cli/services/tmux_ui_runtime/service.py" "test/test_v2_tmux_ui.py"`：通过。
- `python -m pytest -q "test/test_v2_tmux_ui.py"`：`12 passed, 2 skipped`。
- `cargo fmt --manifest-path "tools/ccb-agent-sidebar/Cargo.toml" --check`：通过。
- `cargo test --manifest-path "tools/ccb-agent-sidebar/Cargo.toml" shifted_q_is_project_kill_across_terminal_key_encodings --quiet`：通过。
- `cargo test --manifest-path "tools/ccb-agent-sidebar/Cargo.toml" --quiet`：`54 passed`。
- 已将当前 rmux session `ccb-claude_code_bridge-b72b0116` 的 root mouse 绑定刷新为 `#{mouse_pane}`，`rmux list-keys -T root` 已确认 `MouseDown1Pane`、`MouseDown1Border`、`WheelUpPane`、`WheelDownPane`、`MouseDown3Pane` 均使用 `-t "#{mouse_pane}"`。
- `cargo build --release --manifest-path "tools/ccb-agent-sidebar/Cargo.toml"`：失败，原因是当前运行中的 `ccb-agent-sidebar.exe` 锁住默认 release exe，Windows 返回 `os error 5`。
- `cargo build --release --manifest-path "tools/ccb-agent-sidebar/Cargo.toml" --target-dir "tools/ccb-agent-sidebar/target/codex-build"`：通过，确认源码可 release 构建。

追加遗留风险：

- 当前正在运行的 sidebar 进程仍使用旧 release exe；`Q` / `×` 的 Rust 侧修复需要退出/重启 sidebar 或重启项目后才能替换默认 `target/release/ccb-agent-sidebar.exe` 并生效。
- 本轮已刷新 live rmux key bindings，因此滚轮目标修复可在当前 session 直接复测；若仍失败，下一轮应采集真实 mouse event 下 `#{mouse_pane}` 是否为空或错误 pane。

## 追加修复：Windows rmux fallback 的左键选择与文本选区错位

用户再次复测反馈：当前代码状态下 pane 交互仍严重异常：

- 需要双击才能定位到对应 pane。
- 在 pane 中选择文档时，鼠标实际位置与被选中的文本错开一行。

本轮重新核对当前代码和 rmux 0.9.0 现场默认绑定后，确认上一轮实际落入了 Windows + rmux fallback 分支：

1. `_mouse_pane_format_supported()` 在 Windows + rmux 下返回 false，因此不会使用 `#{mouse_pane}` 绑定。
2. fallback 把 `MouseDown1Pane` / `MouseDown1Border` / `WheelUpPane` / `WheelDownPane` 直接绑定为裸 `send-keys -M`。
3. rmux 0.9.0 默认的 `MouseDown1Pane` 是 `select-pane -t = ; send-keys -M`；当前 fallback 去掉了 `select-pane -t =`，导致首次点击没有可靠选中鼠标所在 pane。
4. 普通 pane 左键被无条件透传到应用 mouse event 链路，也会干扰文本选择路径；这与“定位需要双击”和“选中文本错行”的现象一致。
5. 复审指出不能只用 `list-keys` 证明 `=` target 在真实 mouse event 下可靠，因此最终 fallback 不再显式依赖 `=` target，而是使用 rmux/tmux mouse binding 的事件上下文。

追加改动：

- `lib/cli/services/tmux_ui_runtime/service.py`
  - 将 Windows + rmux fallback 从裸 `send-keys -M` 改为 mouse event context 绑定。
  - 普通 pane 的 `MouseDown1Pane` 默认只执行 `select-pane -M`，避免把左键点击继续转发到非 sidebar pane。
  - sidebar pane 仍保留 `select-pane -M ; send-keys -M`，不破坏 sidebar 自己的鼠标交互。
  - wheel fallback 先 `select-pane -M` 选中鼠标事件 pane，再按该 pane 的 `pane_in_mode` 决定透传或进入 `copy-mode -e` 后执行 `scroll-up/down`。
  - `MouseDown3Pane` fallback 补回 sidebar 分流：sidebar 透传，非 sidebar 先选中目标 pane 再 paste。
- `test/test_v2_tmux_ui.py`
  - Windows + rmux 分支断言不再允许 `MouseDown1Pane` 退回裸 `send-keys -M`。
  - rmux live binding 测试改为验证 fallback 不包含 `#{mouse_pane}` 或显式 `-t =`，并包含 `select-pane -M` 与 `copy-mode -e`。

追加验证：

- `python -m py_compile "lib/cli/services/tmux_ui_runtime/service.py" "test/test_v2_tmux_ui.py"`：通过。
- `python -m pytest -q "test/test_v2_tmux_ui.py" -k "windows_rmux_project_ui_avoids_shell_status_commands or rmux_accepts_equals_target_project_ui_bindings"`：`2 passed, 13 deselected`。
- `python -m pytest -q "test/test_v2_tmux_ui.py"`：`13 passed, 2 skipped`。
- 已刷新当前 live rmux session `ccb-claude_code_bridge-b72b0116` 的 root mouse 绑定。
- `rmux -L "ccb-claude_code_bridge-b72b0116" list-keys -T root` 已确认：
  - `MouseDown1Pane` 使用 `select-pane -M`，不再是裸 `send-keys -M`，也不显式使用 `-t =`。
  - `WheelUpPane` / `WheelDownPane` 使用 `select-pane -M ; if-shell -F "#{pane_in_mode}" ... copy-mode -e ; send-keys -X -N 2 scroll-up/down`。
  - `MouseDown3Pane` 对 sidebar 走 `select-pane -M ; send-keys -M`，对非 sidebar 走 `select-pane -M ; paste-buffer -p`。

追加遗留风险：

- 真实 WezTerm 前台鼠标选择是否完全消除一行错位仍需用户在当前 TUI 中复测；本轮已修正最直接的 rmux fallback 绑定错误并刷新 live session。
- 普通非 sidebar TUI pane 的左键 mouse event 不再默认透传；这是为恢复 pane 定位和文本选择优先级做的 Windows + rmux scoped 行为调整。
