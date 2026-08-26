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

## 修订（2026-08-26，前台 attach 与 Herdr 观测约束）

ADR 0003 的 ready time 优化不得以牺牲 Herdr UI 自身可观测性为代价。后续实现必须同时满足：

1. **前台 attach 幂等。** 在同一项目、同一 Herdr session 已存在可见 Herdr UI 时，再次从同一项目启动
   CCB 不应创建重复的等价 Herdr UI。
2. **WezTerm 内启动优先交接当前前台。** 用户在 WezTerm tab 内运行 CCB 时，目标体验是当前 tab
   进入 Herdr UI，且 `ccb` 启动进程可以被前台 Herdr attach 接管，不要求返回原命令行。目标不是保留
   一个命令启动 tab 再额外创建 Herdr UI tab；如用户需要新的命令行，可由用户手动新建 tab。
   从普通 PowerShell/cmd 启动时没有可交接的 WezTerm 前台，可继续使用可观测 fallback：有可用
   WezTerm mux 时新建 Herdr UI tab，无 mux 时打开可见 Herdr 控制台。
3. **CCB 身份权威不覆盖 Herdr 工作状态观测。** CCB 对自身管理 pane 的权威范围是
   project/slot/provider/generation 与业务完成判定；Herdr UI Agents 面板中的
   `working`、`idle`、`blocked`、`done`、`unknown` 等工作状态仍应由 Herdr 作为 Host Runtime
   观测并展示。CCB 不得为了 ready time 或恢复路径把这些运行时工作状态压成失真的固定值。
4. **既有健康 runtime 启动退化为恢复前台。** 再次从同一项目运行 `ccb` 时，若 daemon、Herdr
   session 和 agent pane 已存在且健康，不应重新 create/respawn agent；该启动应只负责把前台交接或
   恢复到既有 Herdr session。
5. **既有 Herdr UI 判定以绑定为锚。** “同一项目、同一 Herdr session 已有 Herdr UI”先以
   `Runtime Binding.frontend` 为锚，再通过 Herdr/WezTerm 轻量探测确认可达性；不得只依赖
   WezTerm tab 数或窗口标题。
6. **第一阶段状态修复收窄 CCB 上报。** 为恢复 Herdr UI Agents 面板的工作状态监控，第一阶段只调整
   CCB 到 Herdr 的上报边界：保留 project/slot/provider/generation/session 等身份与绑定信息，不再持续用
   CCB 的 `idle`/`working` 等状态覆盖 Herdr 的观测状态。若后续需要合并两类状态，必须另行设计
   source 优先级与 seq 语义。
7. **lifecycle bridge 不再同步普通工作状态。** `AgentState.BUSY`、`AgentState.IDLE` 等 CCB
   业务队列状态不得持续映射成 Herdr `working`、`idle` 写入 `source=ccb`。该桥只保留启动或绑定阶段的
   身份注册职责。
8. **身份注册优先使用 pane metadata。** CCB 归属应优先通过 `set_pane_identity` 或等价 metadata token
   表达 project/slot/provider/generation/session。只有 Herdr 必须知道 provider kind 时，才允许一次性
   注册 agent kind；若当前 Herdr CLI 强制要求 `state`，该注册只能使用不争抢后续观测的初始状态，并避免
   通过递增 seq 长期压过 Herdr 自身观测。
9. **先修状态监控，再接当前前台。** Herdr UI Agents 面板状态失真直接破坏 Host Runtime 事实展示，
   优先级高于 WezTerm 当前 tab 交接体验；状态边界收窄后，WezTerm 内启动应由当前 pane 直接交接给
   `herdr session attach <session>`，避免再通过 `wezterm cli spawn` 额外创建 UI tab。
10. **第一版停掉持续 `report_pane_agent` 状态写入。** `HerdrAgentLifecycleBridge.sync()` 不再把
    `AgentState.BUSY`、`AgentState.IDLE` 等普通状态变化转成 Herdr `report-agent` 调用；如仍需要桥接，
    应重命名或收敛为 identity/binding bridge，避免接口名暗示其拥有工作状态权威。
11. **兼容兜底必须一次性且不争抢状态。** 若 Herdr 当前接口在少数 provider 上还无法只靠 metadata
    恢复 agent kind，可在启动或绑定阶段做一次最小兼容注册；该路径不得携带递增 `seq`，不得随 CCB
    队列状态变化重复发送，也不得把 `source=ccb` 变成 Herdr UI Agents 面板工作状态的长期胜出来源。
12. **验收同时覆盖单测与真实 UI。** 单测必须断言普通 BUSY/IDLE 同步不会再调用
    `report_pane_agent`；真实验证必须覆盖 WezTerm + Herdr 场景中 agent 可从 `working` 回到 `idle`，
    且同一项目重复启动不产生重复等价 Herdr UI。
13. **第一版只改 CCB 侧。** 本轮先在 CCB 停止错误状态上报，不要求 Herdr 同步新增
    identity-only API；若发现 Herdr API 表达力不足，另开后续设计。
14. **CCB 业务状态只留在 CCB 展示面。** CCB 仍可在自身日志、队列或项目视图中展示业务队列状态与
    business completion 判定，但不得把这些状态投射成 Herdr UI Agents 面板的 runtime 工作状态。
15. **讨论完成后进入实现。** 以上边界足以指导第一版修复；实现顺序为先恢复 Herdr Agents 面板状态监控，
    再让 WezTerm 内启动的 CCB 进程交接给当前 pane 中的 Herdr UI。
16. **不再过滤 Herdr 原生状态 hook。** CCB 管理的 provider home 应保留 `herdr-agent-state`、
    `pane.report_agent_session` 或等价 Herdr 原生观测 hook；这些 hook 是 Herdr 工作状态链路的一部分，
    不得再因旧的 CCB monotonic seq 状态抢占策略被删除。
17. **既有 UI 精确复用不得靠标题猜测。** 当前 pane 交接消除“命令 tab + 新 UI tab”的启动形态；
    若要在已有 Herdr UI 客户端存在时只聚焦旧 UI 并关闭启动 tab，需要 `Runtime Binding.frontend` 记录
    可验证的 frontend pane/window 标识，并通过 Herdr/WezTerm API 确认可达后执行。实现前不得仅凭
    tab 标题或 tab 数推断并杀掉用户 pane。
