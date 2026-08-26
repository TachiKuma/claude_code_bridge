# Spec：Windows 原生 all-agent ready time 优化

- Status: ready-for-agent
- 日期：2026-08-26
- 关联 ADR：`docs/adr/0001-三层运行时权威边界.md`、`docs/adr/0002-观测聚合协作模型.md`、`docs/adr/0003-windows-native-all-agent-ready-time-optimization.md`
- 关联术语：仓库根 `CONTEXT.md`

---

## Problem Statement

Windows 原生环境下，用户启动一个包含多个 agent 的 CCB 项目时，首要痛点不是“命令是否很快返回”，而是**全部目标 agent 真正达到 `Agent Ready` 的总时间过长**。老机器上，冷启动链容易把总 ready 时间推高到接近或超过默认预算，用户最终看到的是超时、部分 ready，或长时间等待却不清楚时间花在了哪里。

当前问题还伴随几个可见后果：

- 启动前的只读解析、启动计划构建、运行时写入和 ready gate 的顺序不够收敛。
- 某些可重复写入的 provider home / settings 动作没有基于一致指纹充分跳过。
- 单个 agent 的配置变化可能被扩大成不必要的全量重建或全量重启。
- Config UI 保存后对 `restart-required` 的语义不够显式，容易让用户误以为 live provider 已采用新配置。
- 失败与部分完成的边界不够清楚，用户难以区分”已就绪的 agent””待重启的 agent””仍在收敛的 agent”。

此外，还存在一个跨层干扰问题：CCB 通过 `HerdrAgentLifecycleBridge.sync()` 持续把自身业务队列状态
（`AgentState.BUSY`、`AgentState.IDLE`）映射写入 Herdr UI Agents 面板，覆盖了 Herdr 作为 Host Runtime
原生观测到的 `working`、`idle` 等运行时状态。这导致 Herdr 面板的工作状态失真，用户无法从面板读到真实的
运行时观测。同时，CCB 管理的 provider home 中 Herdr 原生状态 hook（如 `herdr-agent-state`、
`pane.report_agent_session`）因旧版 CCB monotonic seq 状态抢占策略面临被删除的风险，进一步破坏了
Herdr 的工作状态观测链路。用户对 Restart-Bound Provider Config 的 deferred intent 也难以区分”已记录待
重启”和”provider 已经重启并达到 Agent Ready”。

## Solution

把 **all-agent ready time** 作为这项优化的主指标，并围绕这一目标收敛 CCB 的启动路径：

- 先对所有目标 agent 并行做只读解析和启动计划构建，再进入运行时动作。
- 对启动计划引入项目级缓存，按输入指纹失效，局部失效只重建受影响的 agent。
- 允许有限并发启动，但保留上限，避免老机器上的 IO / CPU 争用放大。
- 缓存命中时允许跳过重复的 provider home / settings 写入，只要 hash / receipt 一致就不重复做。
- `Agent Ready` 保持严格门槛：绑定已写入、可接收任务、且至少一次 health/ping 成功。
- Config UI 保存 provider 启动相关配置时只更新 desired 状态并记录 `restart-required`，不热改正在运行的 provider。
- 重启或 provider replacement 只作用于受影响的 agent，不把单一变化扩散到全体 agent。

用户最终得到的是：启动更快、更可预测、可观测的部分完成，以及明确区分 desired/live 的配置语义。

同时，在跨层状态边界上实现以下收敛：

- CCB 不再通过 `HerdrAgentLifecycleBridge.sync()` 向 Herdr 持续同步 `AgentState.BUSY`、`AgentState.IDLE` 等普通工作状态；该桥只保留启动或绑定阶段的身份注册职责。
- CCB 对自身管理 pane 的身份注册优先使用 `set_pane_identity` 或等价 metadata token 表达
  project/slot/provider/generation/session，不再通过 `report_pane_agent` 携带状态字段或递增 seq
  长期覆盖 Herdr 观测。
- CCB 管理的 provider home 中必须保留 Herdr 原生状态 hook（`herdr-agent-state`、
  `pane.report_agent_session` 或等价 hook），这些 hook 是 Herdr 工作状态链路的一部分，不得因旧版
  CCB monotonic seq 状态抢占策略被删除或屏蔽。
- `restart-required` / deferred intent 严格区分于 provider 已完成重启。Herdr 记录 deferred 或重启
  意图只能表示动作被延后或待处理，不能被当作 provider 已经采用新配置或达到 Agent Ready。
- 既有 Herdr UI 的精确复用先以 `Runtime Binding.frontend` 为锚，再通过 Herdr/WezTerm 轻量探测
  确认可达性，不得仅靠 tab 标题或 tab 数做推断。

## User Stories

1. 作为 Windows 用户，我希望多个目标 agent 的启动准备能先并行完成只读解析，以便缩短总 ready 时间。
2. 作为 Windows 用户，我希望系统优化的是“全部目标 agent 真正 ready”的总耗时，而不是只优化表面返回速度。
3. 作为 Windows 用户，我希望在老机器上启动多个 agent 时不会因为过度并发而把磁盘和 CPU 打满。
4. 作为用户，我希望缓存命中时能复用已验证的启动计划结果，以便减少重复工作。
5. 作为用户，我希望当某个 agent 的输入变化时，只重建这个 agent，而不是重新构建全部 agent。
6. 作为用户，我希望当某个 agent 已经 ready 时，它不会因为无关 agent 的变化而被回滚或重置。
7. 作为用户，我希望 provider home / settings 的重复写入在内容一致时被跳过，以便减少冷启动开销。
8. 作为用户，我希望 `Agent Ready` 只有在绑定、接收能力和 health/ping 都满足时才成立，以便状态可信。
9. 作为用户，我希望“部分 ready”被如实记录，而不是被伪装成“全部成功”或“全部失败”。
10. 作为用户，我希望失败原因能区分在解析、计划构建、写入、启动、还是 ready gate 阶段，以便定位瓶颈。
11. 作为用户，我希望 Config UI 保存 API、model、startup_args 或 env 后明确看到 `restart-required`，以便知道 live provider 还没变更。
12. 作为用户，我希望配置保存不会自动重启正在运行的 provider，以免打断当前任务。
13. 作为用户，我希望只替换受影响的 agent，以便降低重启成本和任务扰动。
14. 作为用户，我希望在发生配置漂移时能清楚看到 desired 和 live 的差异，而不是被误导为已生效。
15. 作为用户，我希望启动路径中的缓存失效是局部的，以便单点变化不会拖慢整个项目。
16. 作为用户，我希望项目级缓存按输入指纹失效，以便旧结果不会污染新启动。
17. 作为用户，我希望系统在缓存命中时尽量少做重复 I/O，以便提升 Windows 原生冷启动表现。
18. 作为用户，我希望受限并发能在提速和稳定之间取得平衡，而不是不加控制地并行。
19. 作为维护者，我希望所有 ready 相关状态都能被外部行为测试覆盖，以便后续优化不会破坏语义。
20. 作为维护者，我希望启动计划、缓存、配置漂移和 ready gate 之间的职责边界清晰，以便减少交叉耦合。
21. 作为维护者，我希望 launch plan 的缓存键来自稳定输入指纹，以便失效规则可预测。
22. 作为维护者，我希望重复写入跳过只依赖可验证的 hash / receipt 一致性，而不是隐式状态，以便可审计。
23. 作为维护者，我希望配置 UI 的保存路径和重启路径分离，以便 desired/live 语义不混淆。
24. 作为维护者，我希望现有的 `start` 路径仍然是最高位 seam，以便测试集中验证外部行为。
25. 作为维护者，我希望在 Windows 原生环境下的优化不破坏失败可观测性，以便超时和 partial ready 仍然能解释。
26. 作为维护者，我希望运行时握手和 ready 采集不被重复触发到不必要的次数，以便减少启动成本。
27. 作为维护者，我希望配置变化只影响指纹匹配到的 affected agent，以便实现最小重启面。
28. 作为维护者，我希望该优化遵循 ADR 0001 和 ADR 0002 的权威边界，以便不把运行时事实误当业务判定。
29. 作为用户，我希望 Herdr UI Agents 面板显示真正来自 Herdr 观测的运行时状态，而不是 CCB 业务队列状态的映射，以便面板如实反映运行事实。
30. 作为用户，我希望 CCB 不再持续把 `AgentState.BUSY`、`AgentState.IDLE` 覆盖到 Herdr 面板，以便我可以看到 agent 在 Herdr 层面的真实观测状态。
31. 作为用户，我希望 CCB 保留 provider home 中的 Herdr 原生状态 hook，以便 Herdr 工作状态观测链路不被中断。
32. 作为用户，我希望 Herdr `deferred` / `restart-intent` 只被展示为"待重启"，而不是显示为"provider 已重启"，以便我知道何时可以开始使用新配置。
33. 作为用户，我希望通过 `Runtime Binding.frontend` 记录的标识来精确复用既有 Herdr UI，而不是靠窗口标题或 tab 数判断，以免错误的窗口操作。
34. 作为用户，我希望 CCB 的身份注册优先使用 metadata token 而非携带状态的 `report_pane_agent`，以便状态展示与身份归属解耦。
35. 作为维护者，我希望 `HerdrAgentLifecycleBridge.sync()` 对普通工作状态（BUSY/IDLE）的转发被停用，以便 Herdr 面板状态不再被 CCB 覆盖。
36. 作为维护者，我希望 `filter_herdr_agent_hooks` 等 hook 管理代码只做诊断记录，不清除运行时所需 hook，以便 Herdr 原生观测链路保持完整。
37. 作为维护者，我希望 `restart-required` 与 `agent-ready` 的语义区分被测试覆盖，以便 desired/live 差异始终可观测。
38. 作为维护者，我希望 WezTerm 内启动优先交接当前前台 pane，不额外创建 UI tab，以便启动形态收敛为"当前 pane 直接进入 Herdr UI"。

## Implementation Decisions

- 以 `ccb start` 的全量启动流程作为主实现面，围绕启动准备、运行时动作、ready gate 和结果汇总做优化。
- 启动前先完成所有目标 agent 的只读解析与启动计划构建，再进入实际运行时收敛。
- 引入项目级 launch plan cache，缓存失效基于输入指纹，不做全量失效。
- 缓存命中时允许跳过重复的 provider home / settings 写入，但前提是 hash / receipt 一致。
- 启动并发维持小上限，优先避免老机器上的资源争用，而不是追求无限并行。
- `Agent Ready` 仍然保持严格门槛，不允许用运行时完成、部分写入或单次探活替代。
- Config UI 保存 provider 启动相关字段后，只更新 desired 状态并记录 `restart-required`，不直接改写 live provider。
- provider replacement 只面向受影响 agent，按配置指纹定位，不扩散到未受影响 agent。
- 结果模型需要保留 partial ready 和 failure reason，以便用户判断哪些 agent 已可用、哪些仍在收敛。
- 该优化不改变三层权威边界：CCB 仍然是业务完成权威，Herdr 只提供运行时事实，WezTerm 只提供前台事实。
- CCB 不得通过 `HerdrAgentLifecycleBridge.sync()` 继续把 `AgentState.BUSY`、`AgentState.IDLE` 等普通工作状态映射成 Herdr `working`、`idle` 写入 `source=ccb`。该桥只保留启动或绑定阶段的身份注册职责。
- CCB 身份注册优先使用 `set_pane_identity` 或等价 metadata token 表达 project/slot/provider/generation/session。仅当 Herdr 必须知道 provider kind 时，才允许一次性注册 agent kind；若当前 Herdr CLI 强制要求 `state`，该注册只能使用不争抢后续观测的初始状态，并避免通过递增 seq 长期压过 Herdr 自身观测。
- CCB 管理的 provider home 必须保留 `herdr-agent-state`、`pane.report_agent_session` 或等价 Herdr 原生观测 hook；`filter_herdr_agent_hooks` 等 hook 管理代码只做诊断记录，不得删除运行时所需 hook。
- Herdr 记录 deferred 或重启意图只能表示动作被延后或待处理，不能被当作 provider 已经采用新配置或达到 Agent Ready。desired/live 差异必须始终对用户可见。
- WezTerm 内启动优先交接当前前台 pane 给 `herdr session attach <session>`，避免通过 `wezterm cli spawn` 额外创建 UI tab。

## Testing Decisions

- 好测试应只验证外部可观测行为：总 ready 时间变化、启动结果、partial ready 记录、缓存命中/失效效果、`restart-required` 语义，以及受影响 agent 的最小重启面。
- 主要测试 seam 放在现有的 `start` 高层流程和其返回读模型上，尽量不下钻到实现细节。
- 计划重点覆盖启动流程、启动准备、binding、配置保存与重启意图、以及 ready 相关投影。
- 可复用的现有测试范式包括性能启动测试、start 流程测试、binding 测试、配置重启意图测试和 project_view 状态测试。
- 需要补充的关键断言是：缓存命中不重复写入、局部失效只影响单个 agent、并发上限生效、`Agent Ready` 不被降格、`restart-required` 对外可见、`sync()` 不转发 BUSY/IDLE、provider home hook 保留不删除、deferred intent 不冒充 agent-ready。

## Out of Scope

- 不把“更快返回首屏”作为主目标。
- 不修改 Herdr 的职责边界或把 agent 身份、重启/backoff 下放给 Herdr。
- 不引入新的前台 mux 方案或 WezTerm backend 升级。
- 不把 Config UI 保存改成自动重启流程。
- 不追求把所有失败都回滚成全量一致状态；部分完成是允许且需要可观测的。
- 不在本 spec 内改动与 Windows 原生 all-agent ready time 无直接关系的其它性能路径。
- 不恢复 CCB 向 Herdr 持续同步普通工作状态的旧行为。
- 不删除可以诊断保留的 Herdr 原生状态 hook（herdr-agent-state 等）。
- 不把 Herdr deferred / restart-intent 提升为 "已采用新配置" 或 "Agent Ready" 语义。
- 不把 Herdr 的观测试图代替 CCB 的业务完成权威，或把 CCB 的闲置/忙碌状态映射到 Herdr 面板。

## Further Notes

- 该 spec 的核心验收标准是：在 Windows 原生环境下，多个 agent 的总 ready 时间显著收敛，同时保留严格的 ready gate 和清晰的 desired/live 语义。
- 相关实现应继续沿用仓库中既有的启动、binding、runtime projection 和配置漂移术语，避免引入新的权威层。
- 如果后续需要进一步拆分，可把”launch plan 预计算””缓存””并发控制””restart-required 语义”拆成独立工单，但主目标仍应保持为一个。
- CCB 状态上报收窄部分（`lifecycle_bridge.sync()` 停用 BUSY/IDLE 转发、provider home hook 保留诊断不删除）已有第一版实现（`lib/platforms/windows/herdr/lifecycle_bridge.py` 已 return False、`test/test_herdr_lifecycle_bridge.py` 已覆盖），spec 补充阶段不再重新要求实现，但 `restart-required` vs agent-ready 的测试覆盖仍需补充。
