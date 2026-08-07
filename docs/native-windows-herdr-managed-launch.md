# Native Windows Herdr Managed Startup（`ccb herdr open`）

> 对应 Epic `windows-native-herdr-ccb` ITEM-7。C2 非对称联邦下的一键启动路径：
> WezTerm（唯一入口）→ Herdr（物理 pane owner）→ CCB（provider/编排/recovery authority）。

## 目标体验

预先配置好 WezTerm、Herdr、CCB 三份配置后，日常只运行 WezTerm，即进入
Herdr 双 pane（例如 `claude` + `codex`）多 agent 协作环境。用户看到的是 Herdr
双 pane，但 provider 生命周期、凭证、completion、ask/pend/recovery 仍由 CCB 持有。

关键边界：**不让 Herdr 配置直接长期启动 claude/codex**——那会退化成 attached 模式，
CCB 只能“观察/绑定”已有 pane。正确分层是 CCB 创建并标识 pane（managed 模式）。

## 前置条件

- 已安装并运行 Herdr（`herdr status server` 显示 `running`）。
- CCB 的 `.ccb/ccb.config` 声明期望 agent 拓扑（如 `main = "Main_Code:claude, code_reviewer:codex"`）。
- 使用的 provider 必须在 herdr 显式启动 allow-list 内（当前 `codex`、`claude`；
  见 `lib/cli/services/runtime_launch_runtime/ensure.py::_HERDR_NATIVE_VERIFIED_PROVIDERS`）。

## 形态 1（推荐）：WezTerm 打开 Herdr，Herdr 触发 CCB

- WezTerm 配置 `~/.wezterm.lua`：`config.default_prog = { '<herdr.exe>' }`，
  使运行 WezTerm 即 launch/attach Herdr persistent session。
  （配套 `launch_menu` 保留普通 PowerShell 入口。）
- 进入 Herdr 后，通过 Herdr 快捷键或 Herdr 插件（B-lite）触发 `ccb herdr open`。
- `ccb herdr open` 完成：
  1. 定位 `herdr.exe`（`--herdr-exe` 或自动检测）；
  2. 校验 Herdr server 运行且协议兼容，只读探测核心能力；
  3. 注入 `CCB_HERDR_EXE` / `CCB_HERDR_SESSION` / `CCB_HERDR_CAPABILITY_REPORT` env；
  4. 复用 CCB 启动流，在 Herdr 中创建 pane 并启动 `.ccb/ccb.config` 声明的 agent；
  5. 前台 attach（默认）或后台返回。

## 形态 2（备选）：`ccb herdr open` 编排整个启动链

若希望 WezTerm 直接以 `ccb herdr open` 为 `default_prog`、由命令编排“确保 Herdr + 创建 pane”，
可将 WezTerm 配置改为：

```lua
config.default_prog = { 'ccb', 'herdr', 'open', '--no-attach' }
```

该形态让 bootstrap 同时负责 Herdr 环境就绪与 CCB 启动，职责更重；当前默认不采用，
保留为备选。使用前确认 `ccb` 可执行文件在 PATH 中。

## 前台 / 后台切换

`ccb herdr open` 默认**前台 attach**（类似 `ccb start` 的交互驻留）。两种方式切换：

| 模式 | 命令 | 行为 |
|---|---|---|
| 前台（默认） | `ccb herdr open` | 启动后在 namespace 前台 attach，驻留控制面 |
| 后台 | `ccb herdr open --no-attach` | 启动 daemon 与 agent 后返回 CLI，不前台 attach |

## 故障排查

- **`Herdr project namespace backend selection failed`**：
  CCB daemon 已以非 Herdr backend 运行（旧 keeper 复用时 env 不含 herdr）。
  先 `ccb kill` 停止现有会话，再重试 `ccb herdr open`。
- **`Herdr server is not running`**：
  先运行 `herdr` 启动/attach persistent session，再执行 `ccb herdr open`。
- **`provider ... does not support herdr-native launch`**：
  provider 不在显式 herdr allow-list。改用 `codex`/`claude`，或移除
  `[runtime.mux] backend = "herdr"` 配置走 tmux。
