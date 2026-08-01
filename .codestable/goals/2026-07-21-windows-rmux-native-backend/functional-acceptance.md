---
doc_type: goal-functional-acceptance
goal: "windows-rmux-native-backend"
status: pass
reviewer_id: "019f844f-d803-7f22-bdb0-9a53cbda67ec"
final_iteration: "iterations/002.md"
---

# 功能验收

## Reviewer

可见 Task agent：`019f844f-d803-7f22-bdb0-9a53cbda67ec`（nickname: Curie）。

Task agent 先对 iteration 001 做只读验收并给出 fail，指出 `PsmuxBackend` 子进程环境仍可能继承 `CCB_TMUX_CONFIG`。修复后复验 verdict 为 pass。复验结果已被主流程消费；关闭结果另见交付记录。

## Scope

验收范围是 `windows-rmux-native-backend` 的仓库内首个实现切片：

- `terminal_runtime` 暴露 `PsmuxBackend`。
- 显式 backend 选择支持 `psmux` / `rmux`。
- psmux/rmux 命令使用 tmux-family namespace 语义。
- 不伪造 Windows 真机 capability gate、named pipe、Job Object 或完整 `ccbd` namespace lifecycle。

## Acceptance Checks

- `PsmuxBackend` 已由 `terminal_runtime.api` 和包入口导出。
- `TmuxBackend.backend_family/backend_impl` 为 `tmux/tmux`，`PsmuxBackend.backend_family/backend_impl` 为 `tmux/psmux`。
- `TerminalBackendSelection` 支持 `terminal_backend`、`terminal`、`backend_impl`、`mux_backend` 字段选择 `psmux` / `rmux`。
- `PsmuxBackend` 使用 `rmux -L <namespace>`，不传 tmux `-f` config 参数。
- `PsmuxBackend._command_env()` 移除 `CCB_TMUX_CONFIG`，避免 tmux 配置环境泄漏到 rmux 子进程。
- 测试覆盖 `terminal_backend`、`backend_impl`、`mux_backend` 字段选择和 `CCB_TMUX_CONFIG` 环境隔离。
- goal 产物明确记录当前环境无法执行 Windows 真机 psmux capability gate，没有把后续阶段伪造成完成。

## Functional Evidence

- Task agent 复验报告 verdict：pass。
- 本地主线程 fresh evidence：
  - `python -m pytest -q "test/test_terminal_runtime_backend_selection.py" "test/test_tmux_backend.py" "test/test_rmux_capability_probe.py"`：36 passed。
  - `python -m pytest -q "test/test_terminal_runtime_backend_env.py" "test/test_ccbd_runtime_attach.py" "test/test_ccbd_runtime_refresh.py"`：18 passed。
  - `python -m pytest -q "test/test_terminal_runtime_tmux.py" "test/test_terminal_runtime_tmux_panes.py" "test/test_terminal_runtime_tmux_send.py" "test/test_terminal_runtime_tmux_respawn.py" "test/test_terminal_runtime_tmux_respawn_service.py" "test/test_terminal_runtime_tmux_logs.py" "test/test_detect_terminal.py"`：36 passed。
  - `python -m py_compile "lib/terminal_runtime/tmux.py" "lib/terminal_runtime/tmux_backend.py" "lib/terminal_runtime/psmux_backend.py" "lib/terminal_runtime/backend_selection.py" "lib/terminal_runtime/api.py"`：通过。
  - `git diff --check`：通过。

## Verdict

pass。

本轮仓库内 rmux/psmux backend 实现切片满足 goal acceptance。完整 Windows native 产品能力仍依赖后续 Windows 真机 psmux capability gate、named pipe、Job Object 和 `ccbd` namespace lifecycle 接入。

## Residual Risks

- `lib/terminal_runtime/psmux_backend.py` 是新增文件，后续提交或打包时必须纳入版本控制。
- 未在当前环境完成 Windows 真机 capability gate。
- 未验收 Windows provider 进程树治理、ConPTY 行为和完整 namespace lifecycle。
- `test/test_ccbd_start_agent_runtime.py::test_real_runtime_service_warm_reuse_preserves_restored_without_store_write` 在本环境单独运行失败，当前证据显示不在本轮改动调用路径内。

## Delivery Record

- Final iteration：`iterations/002.md`。
- Task agent 结果已消费；agent 已成功关闭。
