# Herdr Runtime Hosting 架构优化方案 v2：WezTerm 前台层叠加与优先级重排

日期：2026-08-23

> 本文在 v1（`herdr-runtime-hosting-optimization-plan.zh-CN.md`）基础上叠加 **WezTerm 前台层**，
> 并结合代码事实**重排优先级**。v1 仍是权威基线（archi 分数、Phase 定义、契约草案挂在其上）；
> 本文只做增量与修正，不替代 v1。阅读顺序：先 v1，再本文。
>
> 关联决策：`docs/adr/0001-三层运行时权威边界.md`
> 关联术语：仓库根 `CONTEXT.md`
> 关联规划（deferred）：`docs/plantree/plans/windows-wezterm-native/`

## 0. 为什么需要 v2

v1 通篇只谈 CCB ↔ Herdr 边界，**完全没有 WezTerm 维度**。但在 Native Windows 上，真实
分层链条是：

```text
WezTerm（唯一 GUI 入口 / 前台事实源）
    → Herdr（physical pane owner / 运行时事实源）
        → CCB（provider / 编排 / 恢复 / 业务完成权威）
```

证据：

- `platforms/windows/docs/herdr-managed-launch.md` 明确 WezTerm 是唯一入口，用户经
  `~/.wezterm.lua` 的 `config.default_prog` 启动 Herdr。
- `lib/cli/services/start_foreground.py:239-249` 中 CCB 亲自
  `wezterm cli spawn --cwd <cwd> -- <herdr> session attach <session>` 拉起可见 UI。
- `platforms/windows/packaging/build_release.py:230` 将 `wezterm: required` 列为强制前置。

因此 v1 的「运行时事实源」其实是**两级**：Herdr 提供 agent 运行时事实，WezTerm 提供**前台
可见性事实**（mux 是否在、attach 落到哪个窗口）。v1 的契约模型缺这一级，导致 attach 首屏
不可靠、缺 mux 时静默降级。v2 补齐这一级，并据此重排优先级。

## 1. 结合代码事实的关键结论

### 1.1 闪窗其实基本已被设计性消除（据此降级为加固子任务）

- 后台进程一律 `CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS | CREATE_NO_WINDOW`
  （`lib/process_background.py:9-18`）。
- `background_spawn()` 刻意绕过 Windows venvlauncher 重定向器，以防真解释器弹控制台
  （`lib/process_background.py:32-37`）。
- 每个 Herdr CLI 调用、server 启动、UI 控制进程均带 no-window
  （`lib/terminal_runtime/api.py:73-77`、`lib/platforms/windows/herdr/runtime/cli.py:1346`、
  `lib/cli/services/start_foreground.py:596-600`）。
- 最终可见前台是 WezTerm GUI 窗口本身（预期 UI，非闪窗）。

**仅存两个真实残留风险（非大面积闪窗）**：

1. **潜在脆弱点**：`HerdrCliRequestAdapter._run_command_once`
   （`lib/platforms/windows/herdr/runtime/cli.py:1301-1330`）自身不加 `CREATE_NO_WINDOW`，
   全靠注入的 `run_fn`；构造器默认是裸 `subprocess.run`（`cli.py:29`）。一旦有人直接用默认
   构造，就会**每条 Herdr 命令闪一次控制台**。
2. `ccb.cmd:27-37` 为验证 Python 写/删一个 `%TEMP%` 脚本——是临时文件依赖，不是窗口。

**结论**：闪窗不再占主线预算，降级为 Phase 1 的加固子任务（见 §3）。

### 1.2 WezTerm mux 现状：无确保、静默失败、无寻址（本轮核心修正点）

- **CCB 从不确保 WezTerm mux 存在**：`_launch_herdr_ui()` 直接 `wezterm cli spawn` 进「当前
  活动窗口」，spawn 前无 `wezterm cli list` / 健康探测（`start_foreground.py:239-244`）。
- **缺 mux 时静默失败**：`try/except` 只捕获 `OSError/SubprocessError`；`Popen` 不 wait、不查
  返回码；若 mux 未起导致 spawn 失败，**错误被静默丢弃**。回退（detached herdr 窗口）**只在
  wezterm 二进制完全缺失时触发**（`start_foreground.py:242-264`）。
- **多项目 = 挤进同一活动窗口的 tab**：`cli spawn` 无 `--window-id / --workspace /
  --new-window`，靠 WezTerm 隐式「活动窗口」行为堆 tab，**无按项目寻址、无窗口隔离**
  （`start_foreground.py:244`）。

这与 v1 的核心约束「`unknown`、断线、事件缺口必须显式暴露，不能静默降级」**同源**：前台缺
mux 的静默降级，是运行时静默降级的前台镜像。本轮据此落地 (A) 最小加固（见 §4）。

## 2. WezTerm 角色边界（本轮范围）

- 本轮把 WezTerm 当作**可调优的前台窗口 + spawn 入口层**，不越界替代 Herdr 的 agent runtime
  语义。
- **不激活** `WezTermBackend`（让 WezTerm 成为第二 mux 后端）——该方向明确 **out-of-scope /
  deferred**，其可行性与搁置理由已由 `docs/plantree/plans/windows-wezterm-native/` 记录，
  本文仅交叉链接，不重复立 ADR。

## 3. 阶段安排：沿用 v1 Phase 0–5，三处修正

沿用 v1 的 Phase 0（契约冻结）→ 1（持久 Runtime Client）→ 2（声明式 Manifest + ensure_runtime
兼容层）→ 3（事件投影 + 面板读模型）→ 4（生命周期下放 Herdr）→ 5（旧路径删除）主骨架，叠加：

### 修正一：闪窗治理降级为 Phase 1 加固子任务

并入 Phase 1��具体动作：

- 给 `HerdrCliRequestAdapter._run_command_once` 兜底 `CREATE_NO_WINDOW`（不再仅依赖注入的
  `run_fn`），并把构造器默认 `run_fn` 收敛为带 no-window 的实现或移除默认。
- 给 `ccb.cmd` 的 `%TEMP%` Python 验证脚本依赖降噪（尽量减少临时文件写删，或改为内联探测）。
- 增加防回归测试：断言任一 Herdr 命令路径均携带 no-window creationflags。

验收：以默认构造直接调用 `HerdrCliRequestAdapter` 也不闪控制台；防回归测试可捕获未来退化。

### 修正二：新增贯穿式关切「WezTerm 前台契约」

不新增独立 Phase，而是织入现有 Phase：

- **织入 Phase 1**：`HerdrSocketClient.handshake()` 完成时，一并解析并绑定**前台事实**
  （WezTerm mux 是否可用、spawn 目标），写入 runtime binding 的 `frontend` 段（见 §5）。
- **织入 Phase 3**：把「attach 首屏可靠性」作为读模型的一部分——binding.frontend 缺 mux 时，
  `project_view` 必须显式反映「前台未就绪 / 已回退到 detached 窗口」，不得伪装成已 attach。

### 修正三：Phase 4 的 WezTermBackend 明确 deferred

Phase 4 只做 v1 既定的「通用 pane 生命周期下放 Herdr」。`WezTermBackend`（WezTerm 作为 mux
后端）**不在本轮范围**，交叉链接 `docs/plantree/plans/windows-wezterm-native/`；如未来激活，
需独立 ADR + 原型验证。

## 4. WezTerm mux 策略

### 4.1 本轮落地：(A) 最小加固——终结静默降级

在 `_launch_herdr_ui()` 及其调用链引入：

1. **spawn 前探活**：`wezterm cli list`（或等价 `wezterm cli list-clients`）确认存在可用的
   GUI mux；结果决定后续路径。
2. **检查 spawn 结果**：`wezterm cli spawn` 改为可判定成功/失败（检查返回码，不再 fire-and-forget
   丢弃错误）。
3. **缺 mux 也回退**：当探活失败或 spawn 失败（而非仅二进制缺失）时，触发既有的 detached
   `herdr session attach` 回退路径，并**显式记录回退原因**。
4. **事实入 binding**：探活与 spawn 结果写入 `binding.frontend.mux_available` 等字段，供
   `project_view` 消费（见 §5、§3 修正二）。

验收：

- 无 WezTerm GUI mux 运行时，attach 不再静默失败，而是**可观测地**回退到 detached 窗口。
- `project_view` 能区分「已 attach 到 WezTerm tab」「已回退 detached 窗口」「前台未就绪」。
- 不引入新的窗口寻址复杂度（窗口模型本轮不变）。

### 4.2 记名升级：(B) 单一权威 mux + 寻址 tab（Phase 3）

目标终态（本轮**不实现**，仅记名定向）：

- CCB 确保**恰好一个**长驻 WezTerm gui-mux（无则起一个），避免多窗口散落。
- 每项目/agent 以**确定目标**寻址 spawn tab，寻址主键为**每项目一个 WezTerm workspace 名**
  （Q9 定向；window-id 是易变句柄，进程重启即失效，不作 binding 锚点）。
- 重连时按 workspace 名回到同一逻辑窗口，binding.frontend 持久化该 workspace 名 /
  `spawn_target`。

进入 (B) 前的门控：需**原型验证** WezTerm workspace 寻址在重连、mux 重启、多项目并发下的稳定性
（可复用 `docs/plantree/plans/windows-wezterm-native/demos/` 的探针方法）。

## 5. 契约模型增量：`HerdrRuntimeBinding.frontend`

在 v1 的 `HerdrRuntimeBinding`（`.ccb/runtime/herdr-binding.json`）中新增**可选** `frontend` 段，
只记录 attach 首屏可靠性所需的**最小前台事实**：

```json
{
  "schema": "herdr.runtime-binding.v1",
  "server_id": "server-...",
  "session_name": "ccb-project-abc12345",
  "workspace_id": "w1",
  "runtime_generation": 12,
  "frontend": {
    "kind": "wezterm",
    "mux_available": true,
    "window_id": null,
    "spawn_target": "ccb-proj-abc12345"
  }
}
```

约束：

- `frontend` 为**可选**；缺失或 `kind != "wezterm"` 时按无前台事实处理。
- **不**为 WezTerm 新增独立 manifest / event 流（否则重蹈「CCB 理解低层 capability」的覆辙）。
- `window_id` 仅作诊断记录，**不作重连锚点**；重连锚点为 `spawn_target`（workspace 名）。
- 本轮 (A) 只需可靠填 `mux_available`；`spawn_target` 在 (B) 落地时才成为寻址主键。

## 6. 验证矩阵增量（在 v1 验证矩阵基础上追加）

新增测试应覆盖：

- 缺 WezTerm GUI mux 时，attach **可观测回退**到 detached 窗口，且回退原因被记录（不静默）。
- `wezterm cli spawn` 失败（返回码非 0）被正确判定，不再被丢弃。
- `binding.frontend.mux_available` 在「有 mux / 无 mux / 无 wezterm 二进制」三态下取值正确。
- `project_view` 能区分「WezTerm tab attach」「detached 回退」「前台未就绪」三种前台状态。
- 以默认构造直接使用 `HerdrCliRequestAdapter` 不产生控制台闪现（防回归）。

Windows live validation 增量：

- 在**无预启动 WezTerm GUI** 的干净环境启动 `ccb`，验证回退路径可观测、无静默失败。
- 有 WezTerm GUI 时，多项目 attach 行为符合当前「同窗堆 tab」预期（(A) 不改窗口模型）。

## 7. 最小可交付切片（v2）

```text
binding.frontend 可选段（仅 mux_available）
    → _launch_herdr_ui 探活 + 返回码判定 + 缺 mux 回退（终结静默降级）
    → project_view 反映前台三态
    → _run_command_once no-window 兜底 + 防回归测试
```

这个切片直接修掉「前台静默降级」这一与主干目标同源的正确性缺陷，改动面小、可验证，且为 (B)
的 workspace 寻址预留了 binding 锚点，不返工。

## 8. 与 v1 优先级的对照

| 关切 | v1 定位 | v2 调整 |
|---|---|---|
| 边界收敛 | 主干 | 不变（主干） |
| 闪窗治理 | 独立主线 | 降级为 Phase 1 加固子任务（因已基本消除） |
| WezTerm 前台契约 | 缺失 | 新增贯穿式关切（织入 Phase 1 / 3） |
| WezTerm mux 复用 | 未涉及 | (A) 本轮落地；(B) 记名 Phase 3 升级 |
| WezTermBackend | Phase 4 隐含 | 明确 deferred / out-of-scope |
| 契约模型 | 三模型无前台维度 | binding 增可选 `frontend` 段 |
