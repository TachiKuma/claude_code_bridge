# Iteration 001 证据：Windows rmux 输入投递到 crossterm pane

只读诊断，未改任何生产文件。所有实验在本机 native Windows（Administrator）+ rmux 0.9.0
+ 已构建 `bin/ccb-agent-sidebar.exe`（Jul 27）上真跑，脚本见同目录 `probe_*.py`。

## 环境事实

- 仓库真实路径 `D:\Python\GitHub\claude_code_bridge`（`D:\Python\GitHub\claude_code_bridge`
  是 junction；这解释了 Read 工具对部分文件报 not-exist，改用 bash 读）。
- rmux `new-session` / `start-server` 在 Windows 必须用 **DEVNULL stdio**，否则挂起
  （对齐 `scripts/probe_rmux_capability.py` 的 `_rmux_probe_stdio_mode`）。

## 实验与结论

### E1 sidebar 能在 rmux pane 内独立运行（probe 机制可用）

`probe_sidebar_mouse_e2e.py`：`new-session` 起 pane 跑 `ccb-agent-sidebar.exe`
（bogus ccbd socket → set_error，仍渲染），`CCB_AGENT_SIDEBAR_MOUSE_PROBE` 生成 JSON。
结果：probe 文件创建、TUI 渲染（capture 见 Tips 面板）。**probe 机制可作为观测 crossterm
事件的自动化仪器。**

### E2 detached pane：send-keys 完全不投递（键盘+鼠标都不到）

`probe_sidebar_mouse_e2e.py` + `probe_control_shell.py`：对 detached（无 attached client）
pane 发键盘 echo / SGR mouse，`send-keys` 全部 rc=0，但：

- sidebar probe：`event_observed=false`、`mouse_event_count=0`、`updated_at` 不变。
- 普通 shell pane：`capture-pane` 无 echo marker，仅剩提示符。
- **权威 probe 独立印证**：`scripts/probe_rmux_capability.py` 的
  `artifacts/commands/capture-pane.json` 显示 `send-keys "echo ccb-rmux-probe"` 后
  capture 只有 `D:\...>` 提示符，echo 未回显；`attach-session` 被标 `unsupported`
  （"open terminal failed: not a terminal"）。

结论：**detached pane 上 send-keys 不泵入 ConPTY，输入不投递。**

### E3 attached（`-CC` control-mode）后 send-keys 投递恢复

`probe_attach_delivery.py`：后台 `rmux -CC attach-session`（无头可用），再对 shell pane
发 `echo CCB_ATT_MARKER_999`。`capture-pane` 出现 `CCB_ATT_MARKER_999`。
结论：**输入投递需要 attached client；`-CC` 无头 attach 能泵输入，使自动化注入可行。**

### E4 attached 下：键盘到达 crossterm，但 mouse 事件到不了 crossterm（核心根因）

`probe_sidebar_attached.py` + `probe_mouse_l_confirm.py`（均带 `-CC` attach）：

- 键盘 `c` → sidebar probe `settings_action_observed=true`、`config_ui="opening..."`
  （随后因 stub 非真 ccb 报 failed，符合预期）。**键盘链路通到 crossterm 并触发动作。**
- SGR mouse 序列 `\x1b[<0;col;row(M/m)`，`-H` 与 `-l` 两种发送方式、多列扫描：
  `event_observed=false`、`mouse_event_count=0`、`last_mouse_event=null`。
  **鼠标事件从不产生 `Event::Mouse`。**

结论：**native Windows 上 crossterm 走 console INPUT_RECORD 读鼠标；ConPTY 会把注入的键盘
字节转成 key record，但不会把注入的 VT SGR mouse 序列转成 mouse record。** 因此靠
`send-keys -M` 把鼠标事件送进 crossterm pane 的路径在 Windows 上不成立。

## 对 goal 的影响

1. **很可能是生产 sidebar 点击失败的真正根因**：现有 Windows/rmux fallback 用
   `select-pane -t = ; send-keys -t = -M`（service.py:270），依赖鼠标事件进 crossterm，
   而该投递在 Windows 不工作 → 与 owner 2026-07-27 前台 FAIL 一致。
2. **可行修复方向（sidebar，evidence-backed）**：在 Windows/rmux fallback binding 内做
   settings/kill 列命中测试（`_sidebar_settings_click_condition` /
   `_sidebar_kill_click_condition` 已存在，用 `#{mouse_x}`/`#{pane_left}`/`#{pane_width}`），
   命中后发**键盘**命令（settings→`c`，kill→`Q`）而非 `-M`，绕开鼠标注入。需先确认 rmux
   在 Windows 支持这些 `if-shell -F` 条件 format。
3. **对验收 C 的影响**：sidebar「无需 owner 手测的自动化 e2e」可覆盖两半——(a) binding 对
   settings/kill 列产出正确键盘翻译（单测），(b) 该键盘命令投递到真实 sidebar binary 后触发
   config UI / KillProject（`-CC` attach + probe 集成测试，本轮已验证仪器可用）。**唯一不可
   无头自动化的残留是「WezTerm 真实点击是否触发 rmux mouse binding」**（需 attached WezTerm，
   owner 前台确认）。这比旧的「只断言 list-keys」强得多，但并非 100% 无 owner 参与。
4. **对 ordinary 三项的影响**：同样无法无头注入鼠标；GUI-native drag/paste/wheel 依赖
   WezTerm 接管（mouse-off 策略），本质需 owner 前台确认（与验收 C 一致）。
