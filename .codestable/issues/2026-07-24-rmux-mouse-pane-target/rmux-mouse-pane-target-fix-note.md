# rmux 鼠标 pane target 字面量错误修复记录

## 问题

在 Windows rmux 后端中，点击或滚动 CCB sidebar 时，rmux 状态栏提示：

```text
invalid target '#{mouse_pane}': can't find pane: #{mouse_pane}
```

## 根因

`lib/cli/services/tmux_ui_runtime/service.py` 生成的 sidebar 鼠标绑定使用了 tmux 格式 target：

```text
-t #{mouse_pane}
```

tmux 会在鼠标绑定执行时展开该格式；Windows rmux 当前不会在 target 参数位置展开它，于是把
`#{mouse_pane}` 当成字面 pane id 解析，触发 invalid target。

## 修复

- 保持 tmux 路径原有绑定不变。
- 对 `is_windows() && backend_impl == "rmux"` 增加独立鼠标绑定分支，不再生成任何
  `#{mouse_pane}` target。
- rmux 分支使用最小可用绑定：
  - 左键 pane/border 与滚轮：`send-keys -M`
  - 右键 pane：`paste-buffer -p`

该修复遵循 KISS/YAGNI：不模拟 tmux 的完整 mouse target 条件系统，只移除 rmux 不支持的 target
格式依赖，避免继续触发状态栏错误。

## 验证

```text
python -m pytest "test/test_v2_tmux_ui.py"
13 passed, 2 skipped

python -m pytest "test/test_rmux_backend_core.py"
25 passed
```

## 遗留风险

Windows rmux 分支的鼠标绑定比 tmux 分支更保守：不再依赖 target 条件判断 sidebar role，因此只保证
点击/滚轮事件不会因 `#{mouse_pane}` 字面 target 报错，并保留基础事件转发。若后续 rmux 支持完整 tmux
格式 target 展开，可再恢复 tmux 等价绑定。
