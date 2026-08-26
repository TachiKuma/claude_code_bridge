# ADR 0003：Windows 原生 all-agent ready time 优化

- 状态：已接受
- 日期：2026-08-26
- 关联术语：仓库根 `CONTEXT.md`
- 关联决策：`docs/adr/0001-三层运行时权威边界.md`、`docs/adr/0002-观测聚合协作模型.md`

## 背景

Windows 原生环境下，`ccb.cmd` 的首次冷启动在老机器上容易接近或超过默认启动预算，最终表现为 `timed out`。
实测显示，真正拖慢总 ready 时间的主要热区在 CCB 的 `start` 冷启动链，而不是 `ccb.cmd` 外层入口。

本次优化目标不是“更快返回首屏”，而是**缩短全部目标 agent 真正 ready 的总时间**。

## 决策

1. **以 all-agent ready time 为主指标。** 只把单个 agent 达到 `Agent Ready`，且全部目标 agent 都 ready 的时刻视为完成。
2. **先并行预计算启动计划。** 对所有目标 agent 先做只读解析与启动计划构建，再进入运行时动作。
3. **小并发启动。** 允许 agent 间并发，但限制并发上限，避免老机器 IO / CPU 争用放大。
4. **launch plan 项目级缓存。** 启动计划缓存放在 `.ccb/launch-plan-cache/`，按输入指纹失效。
5. **失效只重建局部。** 某个 agent 的缓存失效时，只重建该 agent，不做全量重建。
6. **缓存命中允许跳过重复写入。** 只要 hash / receipt 一致，就跳过重复的 provider home / settings 写入。
7. **部分失败不自动回滚。** 允许记录 partial ready + failure reason，但不为一致性自动撤销已 ready agent。
8. **ready gate 保持严格。** `Agent Ready` 必须同时满足绑定已写入、可接收任务、且至少一次 health/ping 成功。
9. **provider 启动配置保持 restart-bound。** Config UI 保存 API、model、startup_args 或 env 后，只更新 desired 配置并记录待重启意图；不对已运行的 provider 进程做热修改。
10. **只替换受影响的 agent。** 执行重启或 provider replacement 时，根据配置指纹定位 affected agent，不因单个 agent 的配置变化而重启全部 agent。
11. **Config UI 不自动重启 agent。** 保存动作只负责校验、持久化和展示 desired/live 差异；用户或明确的 `start` / `replace-agent` 流程负责触发替换。
12. **Herdr deferred 不等于 restarted。** Herdr 记录 deferred/restart intent 只能表示动作被延后或待处理，不能被当作 provider 已经采用新配置。

## 影响

正面：

- 更容易压缩 Windows 原生老机器上的首次冷启动总耗时。
- 便于观测时间花费究竟在解析、写入、启动还是 ready gate。
- 缓存收益能跨多次启动持续复用。
- 单个 provider 配置变更不会无故重启全部 agent。
- 用户可以区分“配置已保存”和“live provider 已采用新配置”。

代价：

- 缓存失效和并发边界更复杂，需要更严格的输入指纹和可观测性。
- 部分失败不回滚，会让用户看到 partial ready，而不是“要么全成要么全撤”。
- Config UI 保存后必须明确提示 `restart-required`，并展示仍在运行的 live 配置。
- Herdr 的 deferred 文案必须严格表达“已延后/待重启”，不能暗示 provider 已重启。

## 备选方案

1. **只调大 timeout。** 被否。只能掩盖问题，不会降低总 ready 时间。
2. **全量串行启动。** 被否。不能解决老机器冷启动抖动。
3. **失败自动回滚。** 被否。会增加总 ready 时间，也让已 ready 的 agent 失去可用性。
4. **Config UI 保存后自动重启 provider。** 被否。会把编辑动作变成有副作用的运行时操作，并可能打断当前任务；采用显式 restart/replace 流程。
5. **把 Herdr restart 视为 provider restart。** 被否。Herdr 可能只延后或记录重启意图，不能替代 provider 进程重新物化和 Ready Gate。
