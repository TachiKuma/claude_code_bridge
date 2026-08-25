# 真实项目验证

执行时间：2026-08-25 14:08-14:22 +08:00

预选真实项目：

```text
E:\GitHub开源项目\TachiKuma\MewUI
```

选择理由：

- 是相邻的真实 Git 仓库；
- 当前 `git status --short` 干净；
- 没有现成 `.ccb/ccb.config`，便于验证只写 CCB 运行时范围。

## 写入边界

计划允许写入：

- `.ccb/`
- CCB 管理的 provider home
- CCB 日志
- 运行时状态

计划禁止写入：

- 业务源码
- 依赖锁文件
- 数据库
- 生产配置
- 用户全局 provider 配置

## 执行情况

真实项目阶段 B 未执行启动。

原因：阶段 A 的 smoke runtime 启动未通过，失败点为：

```text
mux backend capability unsupported for create_session
```

按测试矩阵，A4 是 blocker；在 smoke 项目无法创建 runtime 和 agent pane 的情况下，继续在真实项目创建 `.ccb/` 或启动 provider 会污染真实项目证据，且无法形成有效 B/C 通过结论。

## 状态确认

命令：

```powershell
git -C "E:\GitHub开源项目\TachiKuma\MewUI" status --short
```

退出码：0

结果：无输出，真实项目仍为干净工作区。

## 修复后复测

执行时间：2026-08-25 16:46-16:52 +08:00

真实项目根：

```text
E:\GitHub开源项目\TachiKuma\MewUI
```

写入边界仍按计划执行：

- 允许写入：`.ccb/`、CCB 管理的 provider home、CCB 日志、运行时状态
- 禁止写入：业务源码、依赖锁文件、数据库、生产配置、用户全局 provider 配置

## 观测摘要

`ccb doctor`：

```text
project: E:\GitHub开源项目\TachiKuma\MewUI
ccbd_state: mounted
ccbd_health: healthy
ccbd_startup_last_status: ok
ccbd_startup_last_desired_agents: ['archi', 'claude_aspai', 'claude_ds', 'claude_yes']
ccbd_herdr_namespace_ref: backend_family=herdr-native,backend_impl=herdr,ipc_ref=herdr://ccb-ccb-smoke-20260825-143734-15830fa4,namespace_id=w3,session_name=ccb-mewui-bbc66c3f
agent: name=archi health=restored provider=codex completion=protocol_turn
agent: name=claude_ds health=restored provider=claude completion=session_boundary
agent: name=claude_yes health=restored provider=claude completion=session_boundary
agent: name=claude_aspai health=restored provider=claude completion=session_boundary
```

`ccb doctor storage`：

```text
storage_status: ok
storage_runtime_state_root: E:\GitHub开源项目\TachiKuma\MewUI\.ccb
storage_shared_cache_status: enabled
storage_user_provider_cache_root: C:\Users\Administrator\.cache\ccb\provider-cache
```

`git status --short`：

```text
?? .ccb/
```

## 结论

- 真实项目已成功绑定到项目根 `E:\GitHub开源项目\TachiKuma\MewUI`
- 运行时健康，agent 已恢复为 `idle/restored`
- 当前工作区仅有允许范围内的 `.ccb/` 变更
- `ccbd_namespace_ref.ipc_ref` 仍显示 smoke 会话引用，属于待继续观察项，不影响本轮 ask 成功
