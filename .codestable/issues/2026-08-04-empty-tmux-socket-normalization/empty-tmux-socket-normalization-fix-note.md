---
doc_type: issue-fix-note
issue: 2026-08-04-empty-tmux-socket-normalization
status: confirmed
fix_path: standard
tags: [windows, herdr, tmux, start-flow, relaunch]
---

# 空字符串 tmux socket 被误当成有效 tmux 入口

## 根因

`ccbd` 当前在 Herdr / Windows 路径下拿到的 `tmux_socket_path` 为空字符串 `""`，但启动链路里多处仍按 `tmux_socket_path is not None` 判断是否存在 tmux。

这会把 `""` 当成“有 tmux”，导致：

- `prepare_start_agents()` 走 tmux 绑定过滤。
- 健康的 `mux:` / Herdr 绑定被判成 `runtime_not_tmux`。
- 启动流程触发不必要的 `relaunch_runtime`。
- 旧的 `provider_backends.codex.bridge` 进程不会被回收，重复累积。

## 改动

- `lib/ccbd/start_flow_runtime/service.py`
  - 入口统一把 `tmux_socket_path` 归一化为 `None`。
- `lib/ccbd/start_preparation.py`
  - 绑定过滤前先把空字符串归一化成 `None`。
  - 只有真实 tmux socket 才走 tmux filter。
- `test/test_ccbd_start_preparation.py`
  - 增加回归：`tmux_socket_path=''` 时必须当成缺失处理。
  - 空字符串场景下 `mux:` 绑定不得再被拒绝为 `runtime_not_tmux`。

## 验证

- `python -m pytest test/test_ccbd_start_preparation.py test/test_v2_ccbd_start_flow.py -k "empty_tmux or herdr or provider" -q`
- 结果：`11 passed, 38 deselected`
- `python -m py_compile lib/ccbd/start_flow_runtime/service.py lib/ccbd/start_preparation.py test/test_ccbd_start_preparation.py`

## 处置

- 已额外清理当前残留的 `provider_backends.codex.bridge` 进程，避免旧实例继续弹窗。
