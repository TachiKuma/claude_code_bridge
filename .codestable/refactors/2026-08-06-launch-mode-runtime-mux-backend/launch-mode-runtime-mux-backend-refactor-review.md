---
doc_type: refactor-review
refactor: 2026-08-06-launch-mode-runtime-mux-backend
status: changes-requested
reviewer: subagent+ocr
reviewed: 2026-08-06
round: 1
lane_a_state: completed
lane_a_ref: "aaa6b57a3673442f6"
lane_a_reason: ""
lane_b_state: completed
lane_b_ref: "ocr-review-20260806-H1..HEAD"
lane_b_reason: ""
---

# 2026-08-06-launch-mode-runtime-mux-backend 代码审查报告

## 1. Scope And Inputs

- Design: `.codestable/refactors/2026-08-06-launch-mode-runtime-mux-backend/launch-mode-runtime-mux-backend-refactor-design.md`
- Checklist: none（refactor 来源，非 feature 标准流程）
- Evidence pack: none
- Gate results: none
- DoD results: none
- Implementation evidence: commit `616e5a9b` — 5 files changed（agent_runtime.py, bridge.py, api.py, documents.py, .gitignore）
- Diff basis: `HEAD~1..HEAD`（`git diff 616e5a9b~1..616e5a9b`）
- Review mode: initial（首次独立审查）
- Baseline dirty files: none（工作区干净）

### Independent Review

- Detection: independent-agent（环节 A）可用；ocr CLI（环节 B）可用（`ocr llm test` ✓）
- 环节 A 独立隔离 Task agent: completed（ref `aaa6b57a3673442f6`）
- 环节 B OCR CLI: completed（3 findings，全部经本地事实核验）
- OCR severity mapping: High→blocking/important, Medium→nit/suggestion, Low→discarded
- Merge policy: 两环节结果已逐条本地核验后合并；OCR finding #3 核验为假阳性已丢弃

## 2. Findings

### BLOCKING

**B1 — `_copy_config` 覆盖时丢弃 `runtime_mux_backend`，导致 herdr 偏好静默丢失**
- 来源：lane A（subagent）
- 文件：`lib/agents/config_loader_runtime/loop_overlays.py:311-327` 和 `lib/agents/config_loader_runtime/dynamic_agent_overlays.py:412-428`
- 事实：两个 `_copy_config` 函数在构造 `ProjectConfig(...)` 时均**未传入** `runtime_mux_backend=config.runtime_mux_backend`。`ProjectConfig.runtime_mux_backend` 默认 `None`（`project.py:44`）。
- 触发条件：用户设置 `[runtime.mux] backend = "herdr"`，且存在活跃的 loop capacity state 或 dynamic agent state。
- 影响链路：
  1. `load_project_config()`（`documents.py:326-328`）调用 `apply_loop_capacity_overlays()` / `apply_dynamic_agent_overlays()`
  2. overlays 内部调用 `_copy_config(config, ...)` → `runtime_mux_backend` 字段丢失 → 新 config 此字段为 `None`
  3. `_propagate_runtime_mux_backend(config)`（`documents.py:329`）读到 `None` → `os.environ.pop('CCB_RUNTIME_MUX_BACKEND', None)`
  4. herdr 后端偏好被静默清除 → 违反设计 D5 "不静默回退"
- 测试假阳性：`test_config_runtime_mux_backend.py` 仅测试 `validate_project_config` 直出，未覆盖 overlays 流水线。
- 修复边界：
  - `loop_overlays.py:_copy_config` 增加参数 `runtime_mux_backend: str | None = None`，`ProjectConfig(...)` 调用中传入 `runtime_mux_backend=config.runtime_mux_backend`
  - `dynamic_agent_overlays.py:_copy_config` 同上
  - 所有 `_copy_config(...)` 调用点无需修改（默认 `None` 已安全）

**B2 — 五处 `startswith('tmux:')` 硬编码检查未适配 `mux:` 前缀**
- 来源：lane A（subagent）
- 文件与行号：
  1. `lib/cli/services/runtime_launch_runtime/binding_state_runtime/liveness.py:13`
  2. `lib/cli/services/runtime_launch_runtime/binding_state_runtime/cleanup.py:10`
  3. `lib/cli/services/kill_runtime/agent_cleanup.py:103`
  4. `lib/ccbd/supervision/loop_runtime.py:227`
  5. `lib/ccbd/stop_flow_runtime/service.py:60`
- 事实：本次 diff 新增 `_runtime_ref_prefix` 在 herdr 时返回 `'mux'`（design I-2），但这些位置全部使用 `startswith('tmux:')` 过滤。`binding_runtime/common.py:3` 的 `_PANE_RUNTIME_BACKENDS` 已包含 `'mux'`，说明基础设施已预期 `mux:` 前缀，但业务层未更新。
- 影响评估：
  - `liveness.py:13`：`if not runtime_ref.startswith('tmux:'): return True` → herdr pane 永远返回 alive，不验证进程存活
  - `cleanup.py:10`：`if not runtime_ref.startswith('tmux:'): return` → stale herdr binding 不清理
  - `agent_cleanup.py:103`：herdr runtime 的 tmux socket 不被收集
  - `loop_runtime.py:227`：`if runtime_ref.startswith('tmux:%'): return runtime_ref[len('tmux:'):]` → herdr pane_id 提取失败，supervision 对 herdr pane 失效
  - `stop_flow_runtime/service.py:60`：herdr 的 tmux socket 在 stop flow 中不被收集
- 修复边界：这些位置大部分是 tmux 专属操作（tmux liveness、tmux cleanup、tmux socket 收集）。对 herdr 应**新增对应的 herdr 生命周期实现**（herdr liveness、herdr cleanup），而非简单扩展 `startswith`。短期可接受为"herdr 生命周期延后实现"，但必须记录为已知限制。

### IMPORTANT

**I1 — `get_backend()` 中 `_backend_config_preference` 持久化导致 env var 变更被忽略**
- 来源：lane B（OCR）
- 文件：`lib/terminal_runtime/api.py:156-159`
- 事实：
  ```python
  if terminal_type is None and not _backend_config_preference:
      env_pref = os.environ.get('CCB_RUNTIME_MUX_BACKEND', '').strip().lower()
      if env_pref in ('herdr', 'rmux'):
          _backend_config_preference = env_pref  # 永久缓存
  ```
  首次调用 `get_backend()` 将 env var 值写入模块全局 `_backend_config_preference`，后续调用不再读取 env var。若 env var 在首次调用后被清除/修改，`get_backend()` 仍使用旧值。
- 实际风险：低。config 加载在启动阶段一次性完成，env var 不会被修改。但若未来支持 config reload，此缓存会导致新 config 无效。
- 修复边界：不将 env var 持久化到模块全局，改用局部变量：
  ```python
  env_pref = None
  if terminal_type is None:
      candidate = os.environ.get('CCB_RUNTIME_MUX_BACKEND', '').strip().lower()
      if candidate in ('herdr', 'rmux'):
          env_pref = candidate
  if terminal_type is None:
      terminal_type = _backend_config_preference or env_pref
  ```

**I2 — `_propagate_runtime_mux_backend` 写入 `os.environ` 是进程全局副作用**
- 来源：lane B（OCR）+ lane A I3
- 文件：`lib/agents/config_loader_runtime/io_runtime/documents.py:355-365`
- 事实：`_propagate_runtime_mux_backend` 在每次 `load_project_config()` 调用时写入 `os.environ`。若在同一进程中多次加载不同项目的 config，后续项目的 config 会覆盖前一个项目的 env var。此外 default 路径执行 `os.environ.pop(key, None)` 会清除之前设置的 env var。
- 实际风险：中低。ccbd 进程单项目单次加载。但代码模式不够健壮。
- 修复边界：记录为已知限制。若后续支持多项目/热加载，改用 `set_backend_config_preference()` API 直接调用代替 env var 桥梁。

**I3 — `post_launch` 在 herdr 下无条件 spawn bridge + validate，可能阻断 agent 启动**
- 来源：lane A（subagent）
- 文件：`lib/provider_backends/codex/launcher_runtime/bridge.py:17-22`
- 事实：`post_launch` 调用链为 `write_pane_pid`（herdr 已安全跳过）→ `spawn_codex_bridge`（仍硬编码 `CODEX_TERMINAL='tmux'`）→ `validate_bridge_bootstrap`（无条件检查 bridge 产物）。若 bridge 因 tmux env vars 启动失败，`validate_bridge_bootstrap` 抛出 `RuntimeError` 阻断 `post_launch`，进而导致 agent 启动失败。
- 设计 D3 决策 A：bridge 降级为辅助。当前 `write_pane_pid` 正确回退，但 `spawn_codex_bridge` 和 `validate_bridge_bootstrap` 未做 herdr 条件分支。
- 修复边界：在 herdr backend 下检测并跳过 `spawn_codex_bridge` 和 `validate_bridge_bootstrap`，或将 `validate_bridge_bootstrap` 的异常降级为 warning。

### NIT

**N1 — `_propagate_runtime_mux_backend` 参数缺少类型注解**
- 来源：lane A（subagent）
- 文件：`lib/agents/config_loader_runtime/io_runtime/documents.py:355`
- 建议：`def _propagate_runtime_mux_backend(config: ProjectConfig | None) -> None:`

**N2 — TODO 注释未关联追踪 issue**
- 来源：lane A（subagent）
- 文件：`lib/provider_backends/codex/launcher_runtime/bridge.py:28-30`
- 建议：追加 refactor slug 或 issue 编号

### SUGGESTION

**S1 — `_runtime_ref_prefix` 返回值可用常量替代魔术字符串**
- 来源：lane A（subagent）
- 文件：`lib/ccbd/start_runtime/agent_runtime.py:47-61`
- 建议：定义为 `_RUNTIME_REF_PREFIX_MUX = 'mux'` / `_RUNTIME_REF_PREFIX_TMUX = 'tmux'`

**S2 — 缺少端到端集成测试覆盖**
- 来源：lane A（subagent）
- 缺失测试：
  - `load_project_config` + overlays → `runtime_mux_backend` 保留验证
  - `get_backend()` 读取 `CCB_RUNTIME_MUX_BACKEND` env var 的路径
  - `_runtime_ref_prefix` 单元测试
  - `write_pane_pid` 对 herdr backend 的无操作验证

### PRAISE

**P1 — `write_pane_pid` 的 herdr 回退设计优雅**
- 来源：lane A（subagent）
- 文件：`lib/provider_backends/codex/launcher_runtime/bridge.py:96-101`
- `getattr(backend, '_tmux_run', None)` + `callable()` 守卫模式，精确且无副作用。

**P2 — `_runtime_ref_prefix` 的 fallback 链设计合理**
- 来源：lane A（subagent）
- 文件：`lib/ccbd/start_runtime/agent_runtime.py:47-61`
- 优先级 `namespace_backend_impl → assigned_pane_ref.backend_impl → 默认 'tmux'` 清晰，与 design I-2 对齐。

**P3 — `set_backend_config_preference` 的 cache 失效正确**
- 来源：lane A（subagent）
- 文件：`lib/terminal_runtime/api.py:128-131`
- 偏好变更时同时清除 `_backend_cache` 和 `_backend_cache_key`，避免脏读。

### RESIDUAL-RISK

**R1 — `_runtime_ref_prefix` 依赖 `namespace_backend_impl` 被上游正确填充**
- 来源：lane A（subagent）
- `start_agent_runtime` 的 `namespace_backend_impl` 参数默认 `None`。若上游未正确填充 `'herdr'`，`_runtime_ref_prefix` 返回 `'tmux'`，runtime_ref 保持 `tmux:` 前缀，所有 `startswith('tmux:')` 检查继续工作 — 但这恰好**掩盖了 B2**，造成不一致行为。
- 建议：增加防御性日志，当检测到 herdr 环境但 `namespace_backend_impl` 为 None 时发出 warning。

**R2 — 非 Windows 环境的 fail-closed 依赖 `_resolve_backend` 内部 platform gate 逻辑**
- 来源：lane A（subagent）
- 设计 L-1：非 Windows + `runtime.mux.backend` → fail-closed。当前实现中 platform gate 校验仅在 `_resolve_backend` 内部进行，未在 config 加载阶段前置校验。若 `_resolve_backend` 的实现变更，fail-closed 语义可能丢失。
- 建议：在 `_propagate_runtime_mux_backend` 或 `set_backend_config_preference` 中增加平台前置检查。

**R3 — OCR finding #3（`terminal_backend` 默认 `'tmux'`）核验为假阳性**
- 来源：lane B（OCR）
- 文件：`lib/ccbd/start_runtime/agent_runtime.py:194-197`
- 核验：对于 herdr pane（如 `w2:p3`），`_namespace_assigned_pane_id()` 因 `not pane_id.startswith('%')` 返回 `None`。因此 `namespace_pane_id` 为 `None`，`('tmux' if None else None)` = `None`。`terminal_backend` 默认值正确为 `None`，不存在不一致。
- 处置：丢弃此 finding。

## 3. Test And QA Focus

### QA 必须重点复核的场景

1. **SC-1（B1 验证）**：herdr config + loop capacity overlays 活跃 → 验证 herdr backend 被选中（非静默 tmux 回退）
2. **SC-2（B1 验证）**：herdr config + dynamic agent overlays 活跃 → 同上
3. **SC-3（B2 验证）**：herdr runtime 的 liveness 检测 → kill herdr pane 进程，验证 liveness 正确报告 dead
4. **SC-4（B2 验证）**：herdr agent 的 stop/cleanup → stop agent，验证 stale binding 被清理
5. **SC-5（I3 验证）**：codex bridge 在 herdr 下 bootstrap 失败 → 验证 agent launch 不被错误阻断
6. **SC-6（R2 验证）**：非 Windows 环境 + `runtime.mux.backend=herdr` → fail-closed 报错明确

### 建议新增测试

1. `test_load_project_config_preserves_runtime_mux_backend_through_overlays`
2. `test_runtime_ref_prefix_herdr` / `test_runtime_ref_prefix_tmux_default`
3. `test_write_pane_pid_noop_for_herdr_backend`
4. `test_get_backend_reads_ccb_runtime_mux_backend_env`

## 4. Verdict

**changes-requested** — B1（overlays 丢弃 `runtime_mux_backend`）是真实阻断性 bug，需在 review-fix 中修复。B2（`startswith('tmux:')` 硬编码）是已知架构限制，短期可接受但必须记录。I1（env var 持久化）和 I3（bridge 在 herdr 下可能阻断）应修复。

下一步：回到 refactor 实施修复 B1 + I1 + I3，然后回到本审查做 focused closure 或完整复审。
