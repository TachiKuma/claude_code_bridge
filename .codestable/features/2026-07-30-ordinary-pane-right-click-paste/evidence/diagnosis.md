---
doc_type: feature-evidence
feature: 2026-07-30-ordinary-pane-right-click-paste
status: blocked
---

# ordinary-pane-right-click-paste 诊断

## 结论

当前 Windows + WezTerm + rmux 默认路径不能把普通 pane 右键粘贴声明为 GUI-native mouse parity pass。该 child 的正确投影是诊断闭环完成，但前台能力仍为 `blocked/unsupported_capability`。

## 证据

- 父 QA 已记录 owner 在 2026-07-27 的 native Windows + WezTerm + rmux 前台复测：普通 pane 右键没有反应；即使先在其他软件复制，pane 中也无法粘贴。
- root-cause review 指出，`mouse on` 下 mouse event 进入 terminal application mouse reporting 路径；删除 `copy-mode` / `paste-buffer` / `scroll` 绑定只能证明 CCB 没有执行这些命令，不能证明 WezTerm GUI-native paste 已接管。
- CCB 默认配置与运行时策略多处启用 `mouse on`：
  - `config/tmux-ccb.conf` 默认 `set -g mouse on`，并只提供手动 `m` / `M` toggle。
  - `lib/terminal_runtime/rmux_backend_runtime/namespace.py` 的 rmux server policy 设置 `mouse=on`。
  - `lib/terminal_runtime/tmux_mux_backend.py` 的 tmux-family policy 设置 `mouse=on`。
  - `lib/cli/services/runtime_launch_runtime/tmux_panes.py` 的 detached tmux prepare 设置 `mouse on`。
- tmux-capable路径中 `MouseDown3Pane` 可分 sidebar 与 ordinary：sidebar 透传，ordinary 可执行 `paste-buffer -p`。Windows/rmux fallback 中 `_apply_sidebar_mouse_controls_without_mouse_pane_format()` 只绑定 `MouseDown1Pane` / `MouseDown1Border`，并且测试断言没有 `MouseDown3Pane`、`M-MouseDown3Pane` 或 `paste-buffer`。这是避免错误 clipboard / paste 行为的必要保护，但不是前台 right-click paste pass。
- `config/tmux-ccb.conf` 和 runtime detached prepare 存在 prefix paste / copy-mode clipboard 集成，但这些是键盘或 copy-mode 路径，不等价于普通 pane 前台右键粘贴。

## 策略边界

候选方向仍存在，但都需要 feature 级设计和验收：

- 显式 host clipboard paste bridge：必须定义从系统剪贴板读取、编码、换行、多行粘贴安全策略，以及失败时用户可见诊断。
- 恢复 rmux/tmux `paste-buffer`：必须先证明 buffer 来源正确，并明确系统剪贴板到 tmux/rmux buffer 的同步语义。
- WezTerm 配置层 mouse binding：可以作为用户配置方案，但不是 CCB 默认生产代码能力；也必须真实前台验证。

本 goal 未选择以上生产策略，也未修改运行时代码。

## 复核边界

- 不把 “未出现 `MouseDown3Pane` / `paste-buffer` 绑定” 作为 right-click paste pass。
- 不把 prefix paste、`prefix + p`、`prefix + ]` 或 copy-mode clipboard 通过作为普通 pane 右键粘贴 pass。
- 不把 WezTerm 配置层绑定写成 CCB 默认生产能力。
- 不影响 ordinary drag / wheel 或 sidebar settings / `x` KillProject 的既有结论。
