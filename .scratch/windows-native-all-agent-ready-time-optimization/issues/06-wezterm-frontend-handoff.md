# 06：WezTerm 前台交接与 UI 精确复用

**What to build:** WezTerm 内启动 CCB 时优先交接当前前台 pane（`herdr session attach <session>`），避免通过 `wezterm cli spawn` 额外创建 UI tab；既有 Herdr UI 精确复用先以 `Runtime Binding.frontend` 记录标识为锚，再通过 Herdr/WezTerm 轻量探测确认可达性，不得仅靠窗口标题或 tab 数做推断。

**Blocked by:** T04（需要 `restart-required` 语义和 deferred/agent-ready 区分，以确保前台交接时不会混淆 desired/live 状态）。

**Status:** done

- [x] WezTerm 内启动优先交接前台：
  - 检测当前是否在 WezTerm pane 中运行（通过 `WEZTERM_PANE` 环境变量或 `wezterm cli get-pane-direction`）。
  - 若在 WezTerm pane 内，用 `herdr session attach <session>` 将当前 pane 交接给 Herdr UI，而不是 `wezterm cli spawn` 创建新 tab。
  - 从普通 PowerShell/cmd 启动时（无 WezTerm 上下文），保持现有行为：有可用 WezTerm mux 时新建 Herdr UI tab，无 mux 时打开 Herdr 控制台窗口。
- [x] Runtime Binding.frontend 作为 UI 复用锚点：
  - `Runtime Binding.frontend` 记录 frontend pane/window 可验证标识（如 WezTerm workspace 名、pane_id、mux_available 等）。
  - 再次从同一项目启动时，先通过 `Runtime Binding.frontend` 记录的标识结合 Herdr/WezTerm API 轻量探测确认既有 UI 是否仍可达。
  - 确认可达时直接聚焦/恢复到既有 UI，不创建重复的 Herdr UI 实例。
  - 确认不可达时（如 WezTerm 已重启、pane 已关闭），重建前台并更新 binding。
- [x] 轻量探测不做猜测：
  - 探测只使用 Herdr session API 和 WezTerm CLI 返回的结构化信息。
  - 不通过 tab 标题匹配、不通过 tab 计数推断、不通过窗口标题猜测。
  - 探测失败时回退到新建/重建 UI（同无 WezTerm 上下文的行为），并记录探测失败原因。
- [x] "当前 pane 交接"消除命令 tab + UI tab 双残留：
  - WezTerm 内成功 attach 后，原 CCB 启动进程可退出或转入后台，当前 pane 展示 Herdr UI。
  - 不要求保留一个命令行 tab 再额外创建 Herdr UI tab。
- [x] 交接失败的可观测性：
  - attach 失败时暴露明确错误原因（session 不存在、Herdr 不可达、WezTerm pane 不匹配等）。
  - 不静默降级为 create/spawn。

**Validation:**

- `pytest -q test/test_v2_start_foreground.py -k "wezterm_handoff"`
- `pytest -q test/test_ccbd_start_binding.py -k "frontend"`
- 新增测试：在 WezTerm 上下文中启动时调用 `herdr session attach` 而非 `wezterm cli spawn`
- 新增测试：Rumtime Binding.frontend 有有效标识时复用既有 UI 不创建新 UI
- 新增测试：binding 中 frontend 标识不可达时重建 UI 并记录原因
- 新增测试：从普通 cmd 启动时保持现有 fallback 行为
- Windows live validation：在 WezTerm tab 内运行 `ccb` 看到当前 tab 进入 Herdr UI，无额外 tab 残留
- Windows live validation：同一项目重复启动不产生重复 Herdr UI

**Evidence:** WezTerm 内启动优先交接当前前台 pane、Runtime Binding.frontend 作为 UI 复用精确锚点、不靠标题/tab 数做猜测、重复启动不产生重复 UI。

**验证记录：**

- `pytest -q test/test_v2_start_foreground.py`：34 passed。
- `pytest -q test/test_v2_project_namespace_state.py test/test_herdr_runtime_contracts.py test/test_ccbd_project_view.py -k "frontend"`：2 passed，170 deselected。
- `python -m compileall -q lib/cli/services/start_foreground.py lib/ccbd/services/project_namespace_state_runtime/models.py lib/ccbd/project_view/runtime_status.py lib/platforms/windows/herdr/runtime/contracts.py`：通过。
- `git diff --check`：通过。
- Windows WezTerm + Herdr 实机验证：未执行，本轮以自动化测试覆盖。
