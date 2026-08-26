# MewUI 前台 UI 根因复测

执行时间：2026-08-26 18:20-19:05 +08:00

真实项目目录：

```text
E:\GitHub开源项目\TachiKuma\MewUI
```

用户复现命令：

```powershell
E:\GitHub开源项目\TachiKuma\NativeWin_CCB_Herdr\ccb.cmd
```

用户现象：PowerShell 提示符返回，但没有出现 Herdr UI 界面。

## 最小反馈回路

无 WezTerm 的 Windows fallback harness 在修复前失败：

```text
frontend: {'kind': 'wezterm', 'status': 'detached_fallback', 'launch_mode': 'detached_fallback', 'fallback': True, 'fallback_reason': 'wezterm_cli_unavailable'}
popen kwargs: {'stdout': -3, 'stderr': -3, 'creationflags': 134217728}
AssertionError
```

含义：

- `creationflags=134217728` 是 `CREATE_NO_WINDOW`；
- `stdout=-3`、`stderr=-3` 是 `subprocess.DEVNULL`；
- 裸 `herdr session attach` 被当成隐藏进程启动，TUI 没有可见控制台和输出目标。

修复后同一 harness 通过：

```text
frontend: {'kind': 'wezterm', 'status': 'detached_fallback', 'launch_mode': 'detached_fallback', 'fallback': True, 'fallback_reason': 'wezterm_cli_unavailable'}
popen kwargs: {'creationflags': 16}
```

含义：`creationflags=16` 是 `CREATE_NEW_CONSOLE`，且不再重定向 stdout/stderr。

## 根因

本机没有 `wezterm` 可执行文件在 PATH 中，因此 CCB 进入 Herdr frontend fallback 路径：

```text
fallback_reason=wezterm_cli_unavailable
```

直接根因：

1. `_launch_detached_herdr_ui()` 在 Windows fallback 中使用 `CREATE_NO_WINDOW`。
2. 同一路径把 `stdout` 和 `stderr` 指向 `DEVNULL`。
3. 因此 `herdr session attach <session>` 虽然被启动，但作为隐藏 TUI 进程运行，用户看不到 Herdr UI。

联动发现：

1. manifest 提交流程只判断 `CCB_HERDR_SESSION` 和 `CCB_HERDR_SOCKET_REF` 是否存在，没有校验它们是否匹配当前项目 session，导致 MewUI 曾持久化旧 smoke session 的 `namespace_ipc_ref`。
2. `HerdrSocketClient.runtime_snapshot()` 只接受 `{snapshot: ...}` 包装形状，不接受 `HerdrCliRequestAdapter` 返回的原始 snapshot 形状，导致 polling 读到空 snapshot。
3. `get_backend_for_namespace_teardown()` 依赖 ambient `CCB_HERDR_SESSION` 构建 adapter，没有直接绑定持久化 namespace 的 `session_name`，在诊断进程或无 env 进程中会读错 session。

这些联动问题不直接导致“窗口不显示”，但会导致 `doctor ps` 把真实存在的 Herdr pane 误判为 `missing`，影响验收观测。

## 修复

代码修复：

- `lib/cli/services/start_foreground.py`
  - 拆分 Herdr frontend subprocess 参数；
  - WezTerm 控制面命令继续使用 `CREATE_NO_WINDOW`；
  - 裸 Herdr fallback 使用 `CREATE_NEW_CONSOLE`，且不再重定向 stdout/stderr。
- `lib/cli/phase2_runtime/handlers_start.py`
  - 只有 Herdr env 与当前 manifest session 完全匹配时才跳过 `ensure_runtime`；
  - 否则重新 ensure，并显式传入当前项目 session。
- `lib/platforms/windows/herdr/runtime/client.py`
  - `runtime_snapshot()` 同时接受 `{snapshot: ...}` 包装形状和原始 snapshot 形状。
- `lib/terminal_runtime/api.py`
  - persisted namespace backend 直接按 `namespace_ref.session_name` 绑定 Herdr adapter。

新增回归覆盖：

- `test_launch_herdr_ui_fallback_uses_visible_windows_console`
- `test_start_resubmits_when_runtime_env_points_to_other_herdr_session`
- `test_start_resubmits_when_runtime_env_has_stale_herdr_socket_ref`
- `test_herdr_backend_exposes_raw_adapter_runtime_snapshot`
- `test_get_backend_for_namespace_teardown_binds_persisted_session`

## 真实项目复测

重启闭环：

```text
kill_status: ok
state: unmounted

start_status: ok
project: E:\GitHub开源项目\TachiKuma\MewUI
ccbd_started: true
agents: agent1, agent2
layout_agent: name=agent1 ... pane=w7:p1 ... runtime_state=idle
layout_agent: name=agent2 ... pane=w7:p2 ... runtime_state=idle
```

持久化 namespace 已修正：

```text
namespace_session_name: ccb-mewui-1aa66360
namespace_ipc_ref: herdr://ccb-mewui-1aa66360
namespace_id: w7
```

`doctor ps` 已收敛：

```text
agent1 pane=w7:p1 pane_state=alive
agent2 pane=w7:p2 pane_state=alive
```

`ccb ping all` 已收敛：

```text
agent1 mount_state=mounted runtime_state=idle health=restored
agent2 mount_state=mounted runtime_state=idle health=restored
```

无 pytest 环境限制仍存在：

```text
.venv\Scripts\python.exe: No module named pytest
```

已执行并通过的替代验证：

- `py_compile` 覆盖所有本次修改的 Python 文件；
- 无 WezTerm fallback harness；
- stale Herdr env manifest harness；
- persisted namespace reattach snapshot harness。

## 残留事项

当前工具执行环境不是交互式 TTY，因此直接运行 `ccb.cmd` 会走摘要输出路径，不能替代人工视觉确认。基于修复后的 fallback 参数，用户在交互式 PowerShell 中再次运行同一命令时，裸 Herdr fallback 应打开新的可见控制台。

Claude provider 仍可能停在 trust/login 交互界面；这是 provider 前置条件，不属于 Herdr UI 不显示根因。

## 后续修正：WezTerm CLI 不再强依赖 PATH

2026-08-26 追加修复：`_launch_herdr_ui()` 不再只依赖 PATH 查找 `wezterm`。当用户已在 WezTerm 内运行
`ccb.cmd` 时，CCB 会从 `WEZTERM_EXECUTABLE`、`WEZTERM_EXECUTABLE_DIR` 和当前 WezTerm 环境变量派生
可用 CLI；如果 `WEZTERM_EXECUTABLE` 指向 `wezterm-gui.exe`，优先使用同目录 `wezterm.exe`。

因此，当前问题不应通过“必须把 WezTerm 加入全局 PATH”来解决；PATH 是优先路径，但不是必要条件。详见
`mewui-wezterm-env-fallback.md`。
