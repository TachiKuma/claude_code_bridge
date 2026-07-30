---
doc_type: feature-evidence
feature: 2026-07-30-ordinary-pane-drag-selection-native
status: blocked
---

# ordinary-pane-drag-selection-native 诊断

## 结论

当前 Windows + WezTerm + rmux 默认路径不能把普通 pane 拖拽选区声明为 GUI-native mouse parity pass。该 child 的正确投影是诊断闭环完成，但前台能力仍为 `blocked/unsupported_capability`。

## 证据

- 父 QA 已记录 owner 在 2026-07-27 的 native Windows + WezTerm + rmux 前台复测：普通 pane 拖拽无法选中任何字符串。
- root-cause review 指出，`mouse on` 下 mouse event 进入 terminal application mouse reporting 路径；删除 `copy-mode` / `paste-buffer` / `scroll` 绑定只能证明 CCB 没有执行这些命令，不能证明 WezTerm GUI-native selection 已接管。
- CCB 默认配置与运行时策略多处启用 `mouse on`：
  - `config/tmux-ccb.conf` 默认 `set -g mouse on`，并只提供手动 `m` / `M` toggle。
  - `lib/terminal_runtime/rmux_backend_runtime/namespace.py` 的 rmux server policy 设置 `mouse=on`。
  - `lib/terminal_runtime/tmux_mux_backend.py` 的 tmux-family policy 设置 `mouse=on`。
  - `lib/cli/services/runtime_launch_runtime/tmux_panes.py` 的 detached tmux prepare 设置 `mouse on`。
- Windows/rmux fallback 中 `_apply_sidebar_mouse_controls_without_mouse_pane_format()` 会 `unbind-key -T root MouseDrag1Pane`，并且普通 pane `MouseDown1Pane` 只执行 `select-pane -t =`。这是避免错误 copy-mode / paste / scroll 接管的必要保护，但不是前台 native selection pass。

## 策略边界

候选方向仍存在，但都需要 feature 级设计和验收：

- 关闭普通 pane mouse reporting 或提供可切换策略：会改变全局 mouse contract，可能影响 pane focus、sidebar route、wheel、copy-mode 等行为。
- `Shift` bypass：必须把修饰键写入用户动作和验收脚本；它不是默认 GUI-native drag pass。
- tmux/rmux copy-mode selection：可以成为替代交互，但语义不再是 WezTerm GUI-native selection。

本 goal 未选择以上生产策略，也未修改运行时代码。

## 复核边界

- 不把 “未出现 `MouseDrag1Pane` / `copy-mode -M` 绑定” 作为 native selection pass。
- 不把 `Shift` 拖拽作为默认无修饰键 native selection pass。
- 不把 tmux/rmux copy-mode selection 伪装成 WezTerm GUI-native selection。
- 不影响 sidebar settings / `x` KillProject / ordinary right-click / wheel 的既有结论。
