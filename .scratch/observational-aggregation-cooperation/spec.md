# Spec：观测聚合协作模型落地

- 分类标签：`ready-for-agent`
- 日期：2026-08-25
- 来源 ADR：`docs/adr/0002-观测聚合协作模型.md`
- 关联决策：`docs/adr/0001-三层运行时权威边界.md`
- 关联术语：仓库根 `CONTEXT.md`
- 语言约束：本 spec 及其派生工单/代码注释一律简体中文（见 `AGENTS.md`）

---

## Problem Statement

在 Native Windows 的 CCB 协作运行时中，WezTerm、Herdr、CCB 的职责边界已经由 ADR 0001 确立：
WezTerm 提供前台事实，Herdr 提供运行时事实，CCB 是业务完成权威。但旧 v2 方案仍残留一条错误叙事：
等待 Herdr 将来接管 `runtime.ensure`、agent 身份权威、restart/backoff，并把 CCB 当前的
`ensure_runtime` 与 `report_pane_agent` 视为临时兼容层。

2026-08-24/25 的 Herdr 0.8.2 实机与源码验证已经证明这条路线不可成立。Herdr 是观测式状态聚合器：
它通过进程与屏幕检测观察 pane，并从 CCB、agent 自带 hook 等对等来源接收状态；它不铸造 agent 实例
身份，也不拥有 agent 级 restart/backoff 策略。继续沿用“等待 Herdr 下放能力”的表述，会让后续 agent
误删 CCB 身份上报路径、错误采用 snapshot polling 作为主通道、或把 Herdr 的运行时状态误当成业务完成
判定。

用户需要的是一个可执行、可拆票的落地计划，把 ADR 0002 的锚点“CCB 权威 · Herdr 观测 · WezTerm 呈现”
转化为代码、契约、读模型和文档的一致行为。

## Solution

按 ADR 0002 落地观测聚合协作模型：

- CCB 继续拥有其管理 pane 的 agent 身份、provider 种类、业务完成判定与运行时收敛职责。
- Herdr 作为 Host Runtime 和观测式状态聚合器，提供运行时事实，并通过原生 events 作为主状态通道。
- WezTerm 继续作为 Frontend Surface，只承担可见窗口与 attach 落点，不与 Herdr 竞争 mux。
- CCB 与 Herdr 的状态通道从“snapshot polling 为主、事件待上游”调整为“原生 events 为主、polling 兜底”。
- 对 CCB 创建并管理的 pane，`source=ccb` 的 agent 身份/种类上报是权威来源，屏幕检测只作为非 CCB pane 的兜底。
- `ensure_runtime(manifest)` 明确定义为 CCB 的长期职责，而不是等待 Herdr 原生 `runtime.ensure` 的过渡层。
- CCB 不安装、不采纳 Herdr 原生 agent hook 作为其管理 pane 的权威来源；Herdr 更细的 `agent_status` 可以进入运行时读模型，但不得关闭 job 或替代 CCB 的业务判定。

## User Stories

1. 作为 CCB 用户，我希望 agent 面板的运行时状态来自低延迟事件通道，以便我能及时看到 pane 状态变化。
2. 作为 CCB 用户，我希望 Herdr events 不可用时系统显式回退到 snapshot polling，以便状态仍能更新且失败原因可见。
3. 作为 CCB 用户，我希望事件订阅断开、事件批次非法或能力缺失时都能看到明确回退原因，以便诊断运行时问题。
4. 作为 CCB 用户，我希望过期 runtime generation 的事件不会污染当前 agent 状态，以免重连后看到旧事实。
5. 作为 CCB 用户，我希望重复或乱序事件不会覆盖更新的状态，以免面板回跳。
6. 作为 CCB 用户，我希望来自其他 workspace、session 或 pane 的事件被忽略，以免多项目并发时串状态。
7. 作为 CCB 用户，我希望 Herdr 的 `working`、`blocked`、`idle`、`done`、`unknown` 都被保留为运行时事实，以便面板表达真实状态。
8. 作为 CCB 用户，我希望 Herdr 的 `done` 不会直接关闭 CCB job，以免把运行时完成误判成业务成功。
9. 作为 CCB 用户，我希望 Herdr 的 `unknown` 不会降级为空闲，以免误以为 agent 可用。
10. 作为 CCB 用户，我希望 `blocked` 能继续表达为等待用户输入或审批，以便我知道哪个 agent 需要处理。
11. 作为 CCB 用户，我希望 CCB 亲手启动的 pane 始终显示 CCB 声明的 provider 种类，以免被屏幕检测误覆盖。
12. 作为 CCB 用户，我希望 CCB 管理 pane 的具体 agent 归属由 CCB 上报，以便恢复、取消、continuation 和回复路由保持可信。
13. 作为 CCB 用户，我希望非 CCB 启动的 pane 仍可由 Herdr 屏幕检测兜底，以便观察外部 pane。
14. 作为 CCB 用户，我希望 CCB 启动时先清理旧的 pane agent authority，再以 `source=ccb` 抢占当前权威，以免 stale 身份残留。
15. 作为 CCB 用户，我希望 CCB 的 agent 状态上报使用单调 seq，以免旧状态覆盖新状态。
16. 作为 CCB 用户，我希望 Herdr agent hook 不会被安装到 CCB 管理的 provider home，以免 hook 的 `time_ns` seq 架空 CCB 权威。
17. 作为 CCB 用户，我希望如果环境中已经存在 Herdr 原生 hook 产物，CCB 能把它视为非业务权威的运行时事实，而不是采纳其业务判定。
18. 作为 CCB 用户，我希望更细粒度的 Herdr `agent_status` 能丰富读模型，以便看见 working/blocked/idle/done 等运行时层信息。
19. 作为 CCB 用户，我希望 `agent_status` 只影响运行时展示，不会影响 ask/job 的完成、失败、恢复或取消判定。
20. 作为 Windows 用户，我希望 WezTerm 仍是可见入口，以便 attach 行为与当前桌面体感一致。
21. 作为 Windows 用户，我希望 Herdr 继续拥有 pane 进程与真实 mux 生命周期，以便 pane 可长期存在。
22. 作为 Windows 用户，我希望 WezTerm 与 Herdr 不被设计成两个互相竞争的 mux，以免窗口行为不可预测。
23. 作为维护者，我希望 `ensure_runtime(manifest)` 的文档、契约和命名说明都表达为 CCB 长期职责，以免后来者继续等待不存在的 Herdr `runtime.ensure`。
24. 作为维护者，我希望旧 v2 spec 和相关工单中“兼容层/过渡/待上游”的残留被清理或注明已被 ADR 0002 取代，以免重复打开已证伪方向。
25. 作为维护者，我希望 Herdr 上游诉求只记录 source 优先级和只读 pane-agent 关联，而不要求 Herdr 成为 agent_id 权威。
26. 作为维护者，我希望实现 ticket 按 ADR 0002 优先级拆分，以便先完成事件主通道和身份权威，再做读模型增强。
27. 作为维护者，我希望每个 ticket 都能独立验证外部行为，以便 agent 可逐票实现并回归。
28. 作为维护者，我希望 spec 明确防止删除 `report_pane_agent` 正常路径，以免破坏 CCB 到 Herdr 的正规权威上报。
29. 作为维护者，我希望旧的 snapshot polling 测试继续覆盖兜底路径，以便事件通道失败时仍有稳定行为。
30. 作为维护者，我希望 runtime event projector 继续作为运行时事实投影边界，以便状态去重、generation 校验和读模型更新集中处理。

## Implementation Decisions

- 本 spec 以 ADR 0002 为权威来源，采用“CCB 权威 · Herdr 观测 · WezTerm 呈现”作为实现锚点。
- 状态通道采用 Herdr 原生 events 优先策略。订阅入口先以 snapshot 种子建立一致初始视图，再消费增量事件；能力缺失、订阅不可用、订阅失败或事件批次非法时，显式回退到 snapshot polling，并保留 `fallback_reason`。
- 运行时事件只接受白名单字段，并按 server、session、workspace、pane、agent、provider、runtime generation 和 seq 做归属校验。过期 generation、外部 workspace、旧 seq、非法状态和缺少必要身份字段的事件都必须被忽略。
- snapshot polling 保留为兜底通道，不再被描述为主状态通道。它仍负责在 events 不可用时提供运行时事实，并在失败时记录 `unknown` 和 failure reason。
- 对 CCB 管理的 pane，`source=ccb` 的 agent 种类和身份上报是权威事实。Herdr 的屏幕检测只能作为非 CCB pane 或缺少 CCB 上报时的兜底观测。
- CCB 保留并强化 `report_pane_agent` 与 `release_pane_agent` 正常路径。它们不是历史补丁，不得作为旧路径删除。
- CCB 管理 pane 的上报必须携带 provider kind、state、可选 session 信息和单调 seq，并通过 Herdr 支持的 source 机制声明为 CCB 来源。
- `ensure_runtime(manifest)` 定义为 Collaboration Control Plane 的长期运行时收敛职责。实现可以内部复用 Herdr bootstrap、session/pane 创建和 binding 逻辑，但文档与契约不得再把它称为过渡兼容层。
- manifest 与 binding 继续承担 CCB 的运行时声明和重连锚点职责。manifest 不包含原始凭据；binding 绑定 project、session、workspace、pane、agent slot、provider kind 和 runtime generation。
- Herdr 更细的 `agent_status` 可以进入 CCB 读模型，作为 Host Runtime 的运行时事实。它不得关闭 job，不得声明 ask 成功，不得改变 continuation、恢复、取消或 provider completion 的业务判定。
- WezTerm 与 Herdr 的关系保持“呈现 vs mux”。WezTerm 提供 OS 窗口宿主与 attach 落点；Herdr 是窗口内真实 mux 和 pane 存活所有者。
- 不安装 Herdr 原生 agent hook 到 CCB 管理的 provider home。若检测到相关 hook 竞争风险，必须优先保护 CCB 的 `source=ccb` 权威，不允许 hook 的 `time_ns` seq 架空 CCB 小整数 seq。
- Herdr 上游诉求只保留为协议增强：文档化多源仲裁的 source 优先级与 seq 语义，以及可选暴露稳定只读 pane-agent 关联。二者都不改变 CCB 的 agent identity authority。
- 旧 v2 工单中已判 `wontfix` 的 Herdr agent_id 权威、删除 CCB 主动补身份路径、restart/backoff 下放方向不得重新作为本 spec 的实现目标。

## Testing Decisions

- 好测试只验证外部可观测行为：状态源优先级、回退原因、事件归属过滤、读模型语义、上报 payload、文档契约文字和业务权威边界；不测试私有实现细节。
- 最高测试 seam 是 Herdr runtime event polling 入口。它应覆盖 events supported 时使用事件结果、events unsupported 时回退 snapshot polling、订阅失败时记录 failure 或 fallback、以及回退原因持久化。
- 事件投影 seam 应覆盖 generation 不匹配、workspace/session/server 不匹配、agent/provider 不匹配、旧 seq、非法状态、缺字段事件、`done`/`unknown` 映射和 `unseen_done` 语义。
- Herdr backend/client 合约 seam 应覆盖 `report_pane_agent` 与 `release_pane_agent` 的 payload：必须包含 pane、session、provider kind、state、seq、session 信息，并通过 CCB source 发送到底层 Herdr 命令。
- `ensure_runtime` seam 应覆盖成功提交 manifest、结构化失败、不会泄漏 restore token 或原始凭据，以及文档语义表达为 CCB 长期职责。
- 读模型 seam 应覆盖 runtime fact source 与 business completion authority 的分离：Herdr `done`、`idle`、`unknown`、`blocked` 只能改变运行时展示，不得关闭 job 或改变 provider completion。
- hook 风险 seam 应覆盖 CCB 管理 provider home 不安装 Herdr 原生 hook，或在已存在 hook 风险时暴露可诊断状态并保持 CCB source 权威。
- prior art 包括既有 Herdr backend/client 合约测试、Herdr runtime contracts 测试、snapshot polling 与 runtime events polling 测试、project view runtime refresh 测试、mobile gateway runtime status 契约测试。新测试应复用这些夹具风格，而不是新建低层重复 harness。
- 对文档/契约清理，使用文字级回归检查：不再把 `ensure_runtime` 称作临时兼容层、过渡层或等待 Herdr 原生 `runtime.ensure` 的桥；旧方向必须指向 ADR 0002 的取代结论。
- Windows live validation 只作为补充证据，不作为普通单元测试前置条件。涉及真实 Herdr/WezTerm 的行为应通过可注入 backend 或 fake client 优先覆盖。

## Out of Scope

- 不修改 Herdr 源码。
- 不要求 Herdr 铸造或回传稳定 agent_id。
- 不把 CCB 的 agent 身份权威、业务完成权威或 restart/backoff 策略下放给 Herdr。
- 不删除 CCB 的 `report_pane_agent` 正常路径。
- 不安装 Herdr 原生 agent hook 到 CCB 管理的 provider home。
- 不实现 WezTermBackend，也不把 WezTerm 设计成与 Herdr 竞争的 mux。
- 不激活“单一权威 mux + workspace 寻址”升级；该方向仍需独立 prototype。
- 不把 Herdr `done`、`idle`、`unknown` 映射为业务完成、业务失败或 job 可关闭判定。
- 不解决 Herdr 上游 source 优先级协议本身；本 spec 只在 CCB 侧消费、约束和记录诉求。

## Further Notes

- `/to-tickets` 拆分时按 ADR 0002 的优先级组织：事件主通道优先，其次是 `source=ccb` 权威契约，再清理 `ensure_runtime` 叙述，然后消费更细的 `agent_status`，最后处理 hook/seq 架空风险。
- 推荐阻塞关系：读模型增强依赖事件主通道；hook/seq 风险票依赖身份权威契约；文档叙述清理可较早并行，但不得先于 ADR 0002 的引用落点。
- 本 spec 的测试 seam 选择现有最高层边界：runtime events polling、runtime event projector、Herdr backend/client 合约、`ensure_runtime` 合约和 project view 读模型。暂不新增跨仓库测试 harness。
- 该 spec 是对旧 `.scratch/wezterm-ccb-herdr-hosting` v2 收尾后的下一层落地，不重开 12C/13A/13B 的下放方向。
