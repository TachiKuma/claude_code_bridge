---
status: observed
scope: Native Windows / ccb8.ps1 / wezterm spawn / Herdr 数据目录解析
date: 2026-08-10
---
规则：`ccb8.ps1` 通过 `wezterm cli spawn -- <herdr> session attach <session>` 打开 Herdr UI 时，spawn 出的 herdr 进程会继承 ccb8.ps1 重定向的 `XDG_CONFIG_HOME / XDG_CACHE_HOME / XDG_STATE_HOME`；Herdr 用 `XDG_CONFIG_HOME` 定位数据目录，于是 attach 到 `.ccb-source-dev/state/xdg-config/herdr` 下的空 server，而不是真实 server（`AppData\Roaming\herdr`，含 CCB 创建的 agent pane），表现为"herdr UI 打开了但看不到 agent cli"。Python 侧 `herdr_command_env()`（`lib/cli/services/herdr_common.py`）在 Windows 上会清除 XDG_* 并显式指向真实 `HERDR_CONFIG_PATH`，ccb8.ps1 的 spawn 路径必须做同样的清理，否则 UI attach 落空。

补充：wezterm spawn 的 env 继承规则是——带 `--` 参数直接指定程序时，进程 env 来自调用进程（此处即 ccb8.ps1，含 XDG 重定向）；不带 `--` 参数走 default_prog 时，进程 env 来自 GUI 实例（干净）。因此旧版 `wezterm cli spawn`（空 pane）+ `send-text` 注入 `herdr --session` 不受 XDG 重定向影响，P2 改为直接 spawn 后才暴露。

适用 / 不适用：适用于 native Windows 下 ccb8.ps1 一键启动经 wezterm spawn 直接拉起 herdr 的场景；不适用于 Python 侧（`ccb herdr open` / ccbd / herdr_bootstrap）调用 herdr（`herdr_command_env` 已处理），也不适用于 wezterm spawn 无 `--` 参数（default_prog，env 来自 GUI 实例）的场景。

证据：
- ccb8.ps1（`wezterm cli spawn -- $herdrExe session attach $ccbSession`，已加 XDG guard）
- lib/cli/services/herdr_common.py（`herdr_command_env` 清除 XDG_* + 设 HERDR_CONFIG_PATH）
- `.ccb-source-dev/state/xdg-config/herdr/sessions/ccb-claude_code_bridge-823aff28/herdr-server.log`（devState 空 server 记录了 ccb8 spawn 的 attach client 连接，而真实 server 无记录）
- 修复验证（2026-08-10）：模拟 ccb8 env 重定向后应用 guard（清除 XDG_* + 设 HERDR_CONFIG_PATH）再 `wezterm cli spawn -- herdr session attach`，真实 server `herdr-client.log` 新增 `handshake succeeded`，UI 显示 main_claude/reviewer 双 agent；修复前同环境 spawn 0 行连接记录、UI 仅显示空 PowerShell。
候选归宿：project-doc
