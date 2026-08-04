---
doc_type: issue-fix-note
issue: 2026-08-04-codex-bootstrap-windows-inbox
status: confirmed
fix_path: standard
tags: [windows, codex, bridge, fifo, inbox]
---

# Codex bridge 在 Windows inbox 端点下误判 FIFO 缺失

## 根因

`provider_backends.codex.launcher_runtime.bridge.validate_bridge_bootstrap()` 直接把 `input.fifo` / `output.fifo` 当成必须存在的文件。
但 `provider_backends.codex.launcher_runtime.runtime_state.prepare_runtime()` 在 Windows 上走的是 `SpoolDirTransport` 兼容路径，只会创建 `inbox/` 目录，不会创建 FIFO 文件。

同样，`provider_backends.codex.comm_runtime.session_runtime_runtime.health.check_tmux_runtime_health()` 也直接检查 `input.fifo.exists()`，导致 Windows 下即使 inbox 端点已经就绪，健康检查仍返回失败。

## 改动

- `lib/provider_backends/codex/launcher_runtime/bridge.py`
  - bootstrap 校验改为检查 `endpoint_for_fifo_path(input_fifo)` / `endpoint_for_fifo_path(output_fifo)`。
  - POSIX 仍按 FIFO 文件校验，Windows 按 inbox 目录校验。
- `lib/provider_backends/codex/comm_runtime/session_runtime_runtime/health.py`
  - 健康检查改为检查平台映射后的通信端点，而不是硬看 `input.fifo` 本体。
- `test/test_codex_bridge_runtime.py`
  - 增加平台端点回归。
- `test/test_codex_comm_session_runtime.py`
  - 增加平台端点回归。

## 验证

- `python -m pytest test/test_codex_bridge_runtime.py test/test_codex_comm_session_runtime.py -q`
- 结果：`8 passed`
- `python -m pytest test/test_v2_ccbd_start_flow.py -k "herdr and provider" -q`
- 结果：`2 passed, 37 deselected`
- `python -m pytest test/test_v2_runtime_launch.py -k "codex and bridge" -q`
- 结果：`1 passed, 115 deselected`
- `python -m py_compile lib/provider_backends/codex/launcher_runtime/bridge.py lib/provider_backends/codex/comm_runtime/session_runtime_runtime/health.py test/test_codex_bridge_runtime.py test/test_codex_comm_session_runtime.py`

## 遗留风险

- 仅修正 Windows inbox / POSIX FIFO 的平台契约，不扩大处理 provider 其它启动分支。
