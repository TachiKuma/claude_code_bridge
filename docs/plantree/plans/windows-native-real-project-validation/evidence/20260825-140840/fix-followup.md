# 修复跟进：Herdr `create_session` capability blocker

执行时间：2026-08-25 14:23-14:42 +08:00

## 用户复现

用户在 WezTerm 中从真实项目执行：

```powershell
PS E:\GitHub开源项目\TachiKuma\MewUI> E:/GitHub开源项目/TachiKuma/claude_code_bridge/ccb.cmd
```

实际输出：

```text
command_status: failed
error: mux backend capability unsupported for create_session
```

该输出与前一轮 smoke 项目中的 A4 blocker 一致。

## 最小反馈环

命令：

```powershell
python -m pytest test/test_herdr_backend_client.py -k "uses_socket_runtime_env_without_capability_file"
```

新增断言前该测试只能证明 backend 创建成功；新增 `backend._capability_gate.require_supported("create_session")`
后稳定失败，错误为：

```text
Herdr capability gate is missing supported capabilities for create_session
```

失败能力：

```text
pane_metadata
workspace_create
workspace_metadata
```

## 根因

`ensure_herdr_bootstrap_env()` 成功路径会设置：

- `CCB_HERDR_EXE`
- `CCB_HERDR_SESSION`
- `CCB_HERDR_SOCKET_REF`

但旧实现会清除 `CCB_HERDR_CAPABILITY_REPORT`。后续 Herdr backend 在只有 socket runtime env
的情况下使用 persisted-session fallback；随后又与 `server_info` 生成的 compat mux 能力相交。

旧的 `HerdrCapabilityGate.from_server_info()` compat mux 能力只声明 5 个核心项：

- `session_attach`
- `pane_spawn`
- `send_input`
- `read_output`
- `kill_pane`

而当前 `create_session` 门槛要求：

- `session_attach`
- `workspace_create`
- `workspace_metadata`
- `pane_metadata`

因此能力相交后，`workspace_create`、`workspace_metadata`、`pane_metadata` 被误降级为
`unsupported`，导致裸 `ccb.cmd` 在 Native Windows/WezTerm/Herdr 路径启动失败。

## 修复

变更文件：

- `lib/platforms/windows/herdr/bootstrap.py`
- `lib/platforms/windows/herdr/runtime/capabilities.py`
- `test/test_herdr_backend_client.py`
- `test/test_herdr_bootstrap.py`

修复点：

- bootstrap 成功后执行只读能力 probe；
- 生成并写入 Herdr capability report；
- 设置 `CCB_HERDR_CAPABILITY_REPORT`，让后续 daemon/runtime 能继承完整 facade 能力；
- 扩展 `from_server_info()` 的 compat mux 能力集，使其覆盖当前 backend 操作门槛；
- 新增/更新测试，确保 socket runtime env 路径允许 `create_session`。

## 验证

命令：

```powershell
python -m pytest test/test_herdr_backend_client.py -k "uses_socket_runtime_env_without_capability_file or from_server_info_supports_native_runtime_contract"
```

结果：

```text
2 passed, 201 deselected
```

命令：

```powershell
python -m pytest test/test_herdr_bootstrap.py
```

结果：

```text
50 passed
```

命令：

```powershell
python -m pytest test/test_herdr_backend_client.py test/test_herdr_bootstrap.py
```

结果：

```text
253 passed
```

命令：

```powershell
python -m pytest test/test_v2_project_namespace_state.py -k herdr
```

结果：

```text
19 passed, 31 deselected
```

## 修复后 smoke

新建 smoke 项目：

```text
C:\Users\Administrator\Desktop\ccb-smoke-20260825-143734
```

配置：

```toml
version = 2
entry_window = "main"

[windows]
main = "win_codex:codex, win_claude:claude"

[ui.sidebar]
mode = "off"
```

启动命令：

```powershell
Get-ChildItem Env:CCB*,Env:CODEX* -ErrorAction SilentlyContinue | Remove-Item
$env:CCB_SOURCE_HOME = $env:USERPROFILE
& "E:\GitHub开源项目\TachiKuma\claude_code_bridge\ccb.cmd"
```

结果：

```text
start_status: ok
ccbd_started: true
agents: win_codex, win_claude
layout_summary_status: ok
layout_agent: name=win_codex runtime_state=idle
layout_agent: name=win_claude runtime_state=idle
```

状态命令：

```powershell
& "E:\GitHub开源项目\TachiKuma\claude_code_bridge\ccb.cmd" doctor ps
& "E:\GitHub开源项目\TachiKuma\claude_code_bridge\ccb.cmd" ping ccbd
& "E:\GitHub开源项目\TachiKuma\claude_code_bridge\ccb.cmd" ping win_codex
& "E:\GitHub开源项目\TachiKuma\claude_code_bridge\ccb.cmd" ping win_claude
```

结果摘要：

```text
ccbd_state: mounted
agent: name=win_codex state=idle provider=codex
agent: name=win_claude state=idle provider=claude
ping ccbd: health=healthy
ping win_codex: runtime_state=idle health=restored
ping win_claude: runtime_state=idle health=restored
```

清理命令：

```powershell
& "E:\GitHub开源项目\TachiKuma\claude_code_bridge\ccb.cmd" kill
& "E:\GitHub开源项目\TachiKuma\claude_code_bridge\ccb.cmd" doctor ps
```

结果：

```text
kill_status: ok
state: unmounted
ccbd_state: unmounted
agent: name=win_codex state=stopped
agent: name=win_claude state=stopped
```

## 剩余风险

- 本次修复解除 A4 的 `create_session` blocker，并完成 smoke 启动/观测/清理闭环。
- 真实项目 B 阶段与跨 agent ask 的 C 阶段尚未重新执行。
- `doctor ps` 中 `herdr_namespace_ref.ipc_ref` 仍显示为既有 `herdr://ccb-claude_code_bridge-823aff28`，
  而 `namespace_session_name` 是 smoke 项目的 session；后续真实项目验收应继续观察该字段是否只是显示/引用
  复用差异，还是 session 路由残留。
