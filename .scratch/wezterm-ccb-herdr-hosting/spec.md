# Spec：WezTerm + CCB + Herdr 运行时宿主优化（v2）

- 分类标签：`ready-for-agent`
- 日期：2026-08-23
- 关联方案：`plans/architecture-optimization/herdr-runtime-hosting-optimization-plan.v2.zh-CN.md`
- 关联基线：`plans/architecture-optimization/herdr-runtime-hosting-optimization-plan.zh-CN.md`
- 关联决策：`docs/adr/0001-三层运行时权威边界.md`
- 关联术语：仓库根 `CONTEXT.md`
- 语言约束：本 spec 及其派生工单/代码注释一律简体中文（见 `AGENTS.md`）

---

## Implementation Status（实现状态，2026-08-24）

实现提交：`3b4f75b4 实现 WezTerm CCB Herdr 宿主优化 v2`。

本轮已经完成 CCB 侧的前台启动 runner seam、Runtime Binding `frontend` 段、WezTerm mux 探活与可观测
回退、`project_view` 前台三态、no-window 兜底、import-time Herdr gate 移除、runtime manifest、
`ensure_runtime(manifest)` 兼容层，以及 Herdr runtime event/model/projector 与读模型映射基础。

仍未完全关闭的范围：

- 运行时事件目前是 CCB 侧模型与 projector 基础；真正的上游事件订阅、snapshot polling 循环、断线
  重连后自动重读 snapshot 仍需后续实现。
- 通用 pane readiness/liveness/restart/backoff/workspace cleanup 尚未真正下放给 Herdr；当前仍是
  CCB 兼容层承接，需等待或接入 Herdr 上游原生 `runtime.ensure/event/agent_id` 能力。
- 旧路径删除只完成了正常启动路径的 capability 文件治理；宽 CLI 白名单、backend capability 组合
  gate、tmux_runtime 主动补 agent 身份等收口仍需逐项 characterization test 与 Windows live validation。
- 尚未执行无预启动 WezTerm GUI/有 mux/多项目 attach/mobile gateway 的 Windows live validation。

已记录的验证：

- `python -m compileall ...` 通过。
- `git diff --check` 通过。
- 聚焦回归：`434 passed`。
- 追加回归：`266 passed`。
- 全量 `pytest -q` 在 Windows 收集阶段因既有 Unix-only `fcntl` 导入失败，未完成全量验证；该失败不由
  本轮改动引入。

---

## Problem Statement（问题陈述）

在 Native Windows 上，用户通过 WezTerm 启动 CCB 项目、观察多个 agent（如 codex、claude）的
运行。当前有三类用户可见的痛点：

1. **前台会「静默失败」**：当用户没有预先运行 WezTerm GUI 时，CCB 仍尝试把 agent 界面塞进一个
   并不存在的窗口，失败被悄悄吞掉，用户既看不到界面，也得不到任何解释——只感觉「启动了但什么
   都没出现」。
2. **状态不可信**：Agents 面板/侧栏有时把「运行时完成」当成「任务成功」，或把「无法分类」显示成
   「空闲」，用户据此做的判断是错的。
3. **偶发的控制台闪窗**：个别代码路径可能在每条底层命令时闪一下黑窗，破坏原生桌面体感。

这些痛点的共同根因是：CCB 同时充当运行时宿主、业务控制面与状态投影层，职责边界过宽，把
「运行时/前台事实」误当成「业务判定」，缺陷因此以「静默降级」的形式外泄给用户。

## Solution（解决方案）

按 `docs/adr/0001` 确立的三层权威边界重整配合关系，并让所有失败**可观测**而非静默降级：

- **Frontend Surface（WezTerm）** 只提供前台可见性事实。启动前先探活 WezTerm mux；探活或
  spawn 失败时**明确回退**到 Herdr 独立窗口，并把回退原因暴露给用户，绝不静默。
- **Host Runtime（Herdr）** 提供运行时事实（`idle/working/blocked/done/unknown`），但不决定
  业务成败。
- **Collaboration Control Plane（CCB）** 消费并校验前两层事实，是唯一的业务完成权威。前台事实
  以可选 `frontend` 段记入 Runtime Binding，供读模型呈现前台三态。

用户由此得到：启动要么进入可见界面、要么得到清晰的「已回退/前台未就绪」提示；面板状态如实
区分运行时状态与业务状态；桌面无意外闪窗。

## User Stories（用户故事）

1. 作为 Windows 用户，我希望在**已运行 WezTerm GUI** 时启动项目能直接在其中开出 agent tab，
   以便立即看到并操作 agent。
2. 作为 Windows 用户，我希望在**未运行 WezTerm GUI** 时启动项目**不会静默失败**，而是可观测地
   回退到 Herdr 独立窗口，以便我仍能看到 agent。
3. 作为 Windows 用户，我希望当**根本没装 WezTerm** 时得到明确提示或回退，而不是「什么都没
   发生」。
4. 作为 Windows 用户，我希望前台启动失败时能看到**回退原因**，以便判断是环境问题还是 bug。
5. 作为用户，我希望 Agents 面板把 Herdr 的 `done` 显示为「运行时已完成、业务未确认」，而不是
   直接把 job 关闭，以免误以为任务成功。
6. 作为用户，我希望 Herdr 的 `unknown` 在面板上显示为「不确定/重连中」，而**不是**「空闲」，以免
   我误判 agent 可输入。
7. 作为用户，我希望 `blocked` 状态被呈现为「等待用户输入/审批」，以便我知道该去操作哪个 agent。
8. 作为用户，我希望面板能**同时**显示运行时状态与 job/ask 状态两条信息，而不把二者混成一个
   权威。
9. 作为用户，我希望 pane 重启、pane 迁移、重新 attach、断线重连后，面板**不会残留旧状态**。
10. 作为用户，我希望事件乱序或重复到达时，面板显示的状态仍然正确。
11. 作为用户，我希望在过期 runtime generation 的事件到来时，它被丢弃而不污染当前状态。
12. 作为 Windows 用户，我希望日常启动路径**不产生任何意外控制台闪窗**。
13. 作为运行 `ccb --help` / `ccb version` 的用户，我希望在 Herdr 缺失时命令仍然成功，因为这些
    命令与运行时无关。
14. 作为明确选择 Herdr 后端的用户，我希望在 Herdr 不可用时得到**fail-closed** 的清晰错误，而不是
    含糊行为。
15. 作为用户，我希望启动、恢复、attach、teardown 时不会因重复的运行时握手而变慢。
16. 作为用户，我希望重连后系统先读取运行时快照再消费增量事件，从而得到一致视图。
17. 作为用户，我希望我的 API key、OAuth token、prompt、reply **绝不**出现在 manifest、面板或
    mobile gateway 中。
18. 作为用户，我希望我打开多个项目时的窗口行为是可预期的（本轮维持「同窗堆 tab」，不引入
    混乱的新窗口）。
19. 作为未来的用户，我希望（升级后）多项目能按项目稳定地落到各自的逻辑工作区，且重连后回到
    同一位置。
20. 作为开发者，我希望有一个**可注入命令 runner** 的前台启动 seam，以便无需真起 WezTerm 即可
    测试探活/spawn/回退逻辑。
21. 作为开发者，我希望前台事实以可选 `frontend` 段进入 Runtime Binding，以便读模型可靠判断该
    spawn tab 还是回退。
22. 作为开发者，我希望默认构造的运行时命令适配器也带 no-window 标志，避免未来退化出闪窗。
23. 作为维护者，我希望删除任何旧路径前都有等价的 characterization test 与 Windows live
    validation 兜底。
24. 作为维护者，我希望 `runtime_status` 缓存按 project id / agent name / runtime generation /
    pane id 复合键失效，避免跨实例串状态。
25. 作为维护者，我希望 CCB 只声明运行时拓扑（manifest），由 Herdr 或兼容层收敛实际 runtime。
26. 作为维护者，我希望运行时握手收敛为一次性对象，而不是每个操作都重复 `server_info()`。
27. 作为维护者，我希望前台三态在 `project_view` 中可被下游（面板、mobile gateway）一致消费。
28. 作为维护者，我希望 WezTermBackend（WezTerm 作为 mux 后端）明确 out-of-scope，避免范围
    蔓延。

## Implementation Decisions（实现决策）

**边界与权威（遵循 ADR 0001）**

- 三层职责：Frontend Surface（WezTerm，前台事实源）/ Host Runtime（Herdr，运行时事实源）/
  Collaboration Control Plane（CCB，业务完成权威）。运行时/前台事实不得替代业务判定。
- 所有失败模式（缺 mux、断线、过期 generation、事件缺口、`unknown`）必须**显式暴露**，禁止
  静默降级。

**前台层（本轮核心，Phase 1/3 织入）**

- 引入**可注入命令 runner** 的前台启动抽象（复刻现有 `run_fn` 依赖注入模式），承载：
  WezTerm mux 探活（`wezterm cli list` 或等价）→ tab spawn 且**判定返回码** → 探活/ spawn 失败
  （非仅二进制缺失）即**触发可观测回退**到 Herdr 独立窗口，并记录回退原因。
- 前台事实以**可选 `frontend` 段**写入 Runtime Binding；本轮只需可靠填 `mux_available`。段结构
  （来自 v2 契约草案，编码「重连锚点用 workspace 名而非 window_id」这一决策）：

  ```json
  {
    "kind": "wezterm",
    "mux_available": true,
    "window_id": null,
    "spawn_target": "ccb-proj-abc12345"
  }
  ```

  `window_id` 仅诊断、不作重连锚点；`spawn_target`（WezTerm workspace 名）在 (B) 升级时才成为
  寻址主键。

**契约模型（Phase 0/2）**

- 新增 `HerdrRuntimeManifest`、`HerdrRuntimeBinding`（含可选 `frontend`）、`HerdrRuntimeEvent`
  数据模型；manifest 只描述现有拓扑与策略，**不含原始凭据**，只允许 `env_refs`。
- Runtime Binding 持久化为 CCB 重连/ teardown / 投影 / 事件去重的唯一运行时锚点；绑定
  project / namespace / pane / agent slot / provider kind / session / runtime generation。
- 不为 WezTerm 新增独立 manifest / event 流。

**运行时客户端收敛（Phase 1）**

- 运行时握手收敛为一次性对象：缓存 server info / capabilities / socket ref / identity；仅在首次
  握手、连接恢复或 generation 改变时刷新，停止每操作无条件重复握手。
- `ccb --help` / `version` / 配置检查等 introspection 命令**完全不触碰** Herdr；需要运行时的命令在
  operation-time 调用适配器，并返回结构化错误。

**声明式 manifest 与兼容层（Phase 2）**

- CCB start path 生成 manifest；先由 CCB 内 `ensure_runtime(manifest, restore_token)` 兼容层收敛，
  内部仍可调用既有 create/ensure/pane 操作；上游 Herdr 原生 `runtime.ensure` 成熟后再切换。
- bootstrap 降级为兼容层：只负责解析 Herdr 可执行文件与启动初始 server；capability 证据来自
  握手/ binding，不再写临时 capability 文件。

**事件投影与读模型（Phase 3）**

- 增加运行时事件订阅；无上游事件时先用 snapshot polling 兼容实现，对外保持事件语义。
- `project_view` 的 runtime_status resolver 合并：Herdr 运行时状态、Provider hook 状态、
  pane/status-line 状态、CCB job/callback 元数据、lifecycle guard，以及**前台三态**（已 attach
  WezTerm tab / 已回退 detached / 前台未就绪）。
- Herdr→CCB 状态映射（遵循 v1）：`working→working`；`blocked→waiting_for_user`；
  `idle→idle`；`done→idle + unseen_done=true`；`unknown→unknown`（不得降级为 idle）。
- `runtime_status` 缓存按 project id / agent name / runtime generation / pane id 复合键失效。

**加固（Phase 1 子任务）**

- 运行时命令适配器**默认构造**也携带 `CREATE_NO_WINDOW`，不再仅依赖注入的 runner；加防回归
  断言。
- 降低 `ccb.cmd` 对 `%TEMP%` 验证脚本的依赖噪声。

**记名升级（Phase 3，不在首个 tracer bullet）**

- (B) 单一权威 mux + 按每项目 WezTerm workspace 名寻址 tab；进入前需 `/prototype` 验证寻址在
  重连/ mux 重启/多项目并发下的稳定性。

## Testing Decisions（测试决策）

**什么是好测试**：只测外部可观测行为（用户可见的启动结果、面板呈现的状态、binding 的对外
字段、命令是否 fail-closed），不测实现细节。前台测试通过注入命令 runner 断言「探活→ spawn→
回退」的决策，而非真起 WezTerm 进程。

**被测模块与 seam（尽量复用现有、取最高位）**：

1. `test/test_v2_start_foreground.py`（复用，最高位）：WezTerm mux 探活、spawn 返回码判定、
   **缺 mux 也回退**（终结静默降级）、回退原因记录；经可注入 runner 覆盖「有 mux / 无 mux /
   无二进制」三态。
2. `test/test_ccbd_start_binding.py`（复用）：`HerdrRuntimeBinding.frontend` 序列化/回读、
   generation 校验、`mux_available` 三态取值。
3. `test/test_v2_project_namespace_state.py`（复用）：`project_view.runtime_status` 反映前台三态与
   Herdr→CCB 状态映射；pane 重启/迁移/重连/事件乱序/重复/过期 generation 下不残留旧状态。
4. HerdrCliRequestAdapter 构造点窄单元（可入 `test/test_herdr_bootstrap.py`）：默认构造携带
   no-window 标志（闪窗防回归）。

**prior art（现有同类测试）**：`test_v2_runtime_launch.py`、`test_v2_cli_watch_reconnect.py`、
`test_ccbd_start_binding.py`、`test_windows_bootstrap_script.py`、`test_v2_project_namespace_backend.py`
提供了运行时启动、重连、binding、bootstrap、backend 的既有测试范式，可直接沿用其夹具与断言
风格。

**验证矩阵增量**（在 v1 基础上追加）：缺 mux 可观测回退且原因被记录；spawn 失败被正确判定不
丢弃；`frontend.mux_available` 三态正确；`project_view` 区分前台三态；默认构造适配器不闪窗。

**Windows live validation**：在**无预启动 WezTerm GUI** 的干净环境验证回退可观测；有 mux 时多
项目 attach 符合「同窗堆 tab」预期；面板与 mobile gateway 不解析原始 transcript、不泄漏 prompt/
reply/API key/OAuth token。

## Out of Scope（范围外）

- **WezTermBackend**：让 WezTerm 成为第二 mux 后端替代 psmux/tmux——deferred，见
  `docs/plantree/plans/windows-wezterm-native/`；如激活需独立 ADR + 原型。
- **(B) 单一权威 mux + workspace 寻址**：本轮仅记名与定向设计，实现留待 Phase 3 且需 `/prototype`
  验证后进行；不在首个 tracer bullet。
- 改动 Herdr 源码：本方案只在 CCB 侧配合 WezTerm/Herdr。
- 承诺把 Herdr/WezTerm 自身窗口改成无 UI：前台展示是其职责；本轮只治理 CCB 触发的 transient
  window。
- 引入新的窗口寻址复杂度（`--window-id`/`--new-window` 等）——本轮维持现有窗口模型。

## Further Notes（补充说明）

- 首个 tracer bullet 应是 v2 的最小可交付切片：`binding.frontend`（仅 `mux_available`）→ 前台
  探活 + 返回码判定 + 缺 mux 回退 → `project_view` 前台三态 → `_run_command_once` no-window
  兜底 + 防回归。它直接修掉「前台静默降级」这一与主干同源的正确性缺陷，并为后续 Phase 预留
  binding 锚点。
- 阶段顺序沿用 v1 Phase 0–5；闪窗降级为 Phase 1 加固子任务；前台契约贯穿 Phase 1/3。
- 每个删除旧路径的动作（Phase 5）必须先有等价 characterization test 与 Windows live validation。
- `/to-tickets` 拆分时按 blocking edges 组织：契约模型（Phase 0）为多数工单的 blocker；前台切片
  可较早并行；事件投影依赖 binding 与握手先行。
