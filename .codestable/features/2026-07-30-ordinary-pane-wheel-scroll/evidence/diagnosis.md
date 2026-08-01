---
doc_type: feature-evidence
feature: 2026-07-30-ordinary-pane-wheel-scroll
status: blocked
---

# ordinary-pane-wheel-scroll 诊断

## 结论

当前 Windows + WezTerm + rmux 默认路径不能把普通 pane 滚轮声明为 GUI-native mouse parity pass。该 child 的正确投影是诊断闭环完成，但前台能力仍为 `blocked/unsupported_capability`。

## 证据

- 父 QA 已记录 owner 在 2026-07-27 的 native Windows + WezTerm + rmux 前台复测：普通 pane 滚轮行为失败，WezTerm 中未观察到任何滚动行为。
- root-cause review 指出，`mouse on` 下 mouse event 进入 terminal application mouse reporting 路径；删除 `copy-mode` / `paste-buffer` / `scroll` 绑定只能证明 CCB 没有执行这些命令，不能证明 WezTerm GUI-native scroll 已接管。
- CCB 默认配置与运行时策略多处启用 `mouse on`：
  - `config/tmux-ccb.conf` 默认 `set -g mouse on`，并只提供手动 `m` / `M` toggle。
  - `lib/terminal_runtime/rmux_backend_runtime/namespace.py` 的 rmux server policy 设置 `mouse=on`。
  - `lib/terminal_runtime/tmux_mux_backend.py` 的 tmux-family policy 设置 `mouse=on`。
  - `lib/cli/services/runtime_launch_runtime/tmux_panes.py` 的 detached tmux prepare 设置 `mouse on`。
- tmux-capable 路径中 `WheelUpPane` / `WheelDownPane` 可分 sidebar 与 ordinary：sidebar 透传，ordinary 可进入 `copy-mode -e` 并执行 `scroll-up` / `scroll-down`。Windows/rmux fallback 中 `_apply_sidebar_mouse_controls_without_mouse_pane_format()` 只绑定 `MouseDown1Pane` / `MouseDown1Border`，并且测试断言没有 `WheelUpPane`、`WheelDownPane`、`scroll-up`、`scroll-down` 或 `copy-mode -M -t =`。这是避免错误滚动模式的必要保护，但不是前台 wheel scroll pass。
- `config/tmux-ccb.conf` 的 `copy-mode-vi` wheel binding 只适用于 copy-mode，不等价于普通 pane 前台滚轮滚动。

## 策略边界

候选方向仍存在，但都需要 feature 级设计和验收：

- tmux/rmux-like copy-mode scroll：必须明确滚动的是 rmux copy-mode / scrollback，而不是 WezTerm GUI-native scroll。
- host terminal native scroll：需要关闭 mouse reporting 或明确 modifier bypass，并做真实前台验证。
- 应用内 wheel passthrough：前提是 pane app 自己支持 mouse wheel，不能作为通用 terminal scrollback 能力声明。

本 goal 未选择以上生产策略，也未修改运行时代码。

## 复核边界

- 不把 “未出现 `WheelUpPane` / `WheelDownPane` / `scroll-up` / `scroll-down` 绑定” 作为 wheel scroll pass。
- 不把 copy-mode wheel 或 tmux/rmux-like scroll 伪装成 WezTerm GUI-native scroll。
- 不把应用内 wheel passthrough 写成通用普通 pane scrollback 能力。
- 不影响 ordinary drag / right-click 或 sidebar settings / `x` KillProject 的既有结论。
