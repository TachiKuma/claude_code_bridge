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
---

# rmux pane 滚动聊天历史修复记录

## 问题描述

用户反馈 CCB 的 CLI pane 不能用鼠标滚轮翻看前面的聊天内容；sidebar 仍能选中 pane，但 chat 输出无法滚动回看。

## 根因

`lib/cli/services/tmux_ui_runtime/service.py` 里的 root wheel 绑定把 `alternate_on` 也当成“交给应用处理”的条件。对 AI CLI pane 来说，这会把轮滚事件继续送回 pane 本身，而不是进入 tmux copy-mode，因此看不到历史聊天输出。

## 修复方案

- 保持 sidebar pane 的 wheel 走鼠标透传，继续支持 sidebar 自己的内部滚动。
- 对其他 pane 的 wheel 绑定改成只在 `pane_in_mode` 时透传，其余情况直接 `copy-mode -e` 并滚动历史。
- 同步更新测试断言，避免回归到旧的 `alternate_on` 分流。

## 改动文件

- `lib/cli/services/tmux_ui_runtime/service.py`
- `test/test_v2_tmux_ui.py`

## 验证结果

- `python -m pytest -q test/test_v2_tmux_ui.py -k "apply_project_tmux_ui_sets_session_theme_and_hook_from_current_install_root or windows_rmux_project_ui_avoids_shell_status_commands"`：通过。
- `python -m py_compile lib/cli/services/tmux_ui_runtime/service.py test/test_v2_tmux_ui.py`：通过。
- 当前 rmux 会话已重新绑定 root 的 `WheelUpPane` / `WheelDownPane` / `MouseDown3Pane`。

## 遗留风险

- 这次修复优先保证 CCB 的聊天 pane 能滚回历史输出；如果某些交互式 TUI 依赖 wheel 自身处理鼠标事件，行为会和以前不同。
