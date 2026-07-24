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
