---
doc_type: issue-fix
issue: 2026-07-24-rmux-pane-id-exact-target
status: confirmed
path: fast-track
fix_date: 2026-07-24
tags: [rmux, layout, pane-binding]
---

# rmux pane id exact target 修复记录

## 1. 问题描述

源码版 `ccb` 使用 rmux 启动后，配置里的 2x agent 布局没有稳定呈现。运行态证据显示多个 agent 被记录到同一个 pane，现场 `rmux list-panes` 中部分 pane 没有 CCB 身份。

## 2. 根因

rmux 的 `%N` 既可能是稳定 pane id，也可能在部分命令输出中表现为 pane index alias。

问题有两层：

1. 后续 target 解析路径在扫描 `list-panes` 输出时，遇到 `pane_index == N` 就提前返回，导致 exact `pane_id == %N` 如果位于后续行，会被错误忽略。
2. `split_pane()` 处理 `split-window` 返回值时缺少 split 前 pane 集合。递归 materialize 2x 布局时，`split-window` 返回的 `%N` 可能是 exact 新 pane，也可能是已存在 pane id 对应的 index alias。缺少 split 前快照会把 `agent1` 的新 pane `%3` 解析成已有 `%2`，随后 Claude 继续绑定 `%2`，最终表现为 `agent1` 的 Codex CLI 不在可见的 agent1 pane。

## 3. 修复方案

修复采用两条最小改动：

- 后续 target canonicalization 扫描完整 `list-panes` 结果，优先返回 exact `pane_id == %N`，没有 exact match 时才回退到 `pane_index == N`。
- `split_pane()` 在执行 split 前记录当前窗口 pane id 集合。若 `split-window` 返回值已经存在于 split 前集合，按 index alias 解析；否则走 exact-first canonicalization，确认 split 后该 id 是否真实存在。

这样同时保留 rmux split 返回 index alias 的兼容性，并避免把 exact 新 pane 错当旧 pane。

## 4. 改动文件清单

- `lib/terminal_runtime/rmux_backend_runtime/targets.py`
  - `_pane_id_from_window_index` 和 `_pane_id_from_session_index` 改为 exact 优先，index match 延后作为 fallback。
- `lib/terminal_runtime/rmux_backend_runtime/panes.py`
  - `split_pane()` 增加 split 前 pane 快照，根据返回 id 是否已存在决定 index alias 还是 exact-first canonicalization。
- `lib/ccbd/services/project_namespace_runtime/backend.py`
  - `_canonical_mux_pane_id` 的 rmux target canonicalization 同步改为 exact 优先。
- `test/test_rmux_backend_core.py`
  - 增加 rmux presentation target exact 优先回归。
- `test/test_v2_project_namespace_backend.py`
  - 增加 project namespace mux adapter exact 优先回归。

## 5. 验证结果

- `python -m pytest "test/test_rmux_backend_core.py::test_split_pane_canonicalizes_returned_percent_index_alias_before_respawn" "test/test_rmux_backend_core.py::test_split_pane_prefers_returned_percent_index_over_existing_percent_id" "test/test_rmux_backend_core.py::test_split_pane_uses_exact_returned_percent_id_when_new_at_split_time" "test/test_rmux_backend_core.py::test_split_pane_treats_existing_returned_percent_id_as_index_alias" "test/test_rmux_backend_core.py::test_presentation_identity_prefers_exact_percent_pane_id_over_window_index" -q`
  - 结果：5 passed。
- `python -m pytest "test/test_v2_project_namespace_backend.py::test_mux_percent_pane_adapter_prefers_exact_pane_id_over_window_index" -q`
  - 结果：1 passed。
- `python -m pytest "test/test_v2_project_namespace_backend.py" -q`
  - 结果：26 passed。
- `git diff --check -- ...`
  - 结果：通过。
- 早前执行 `python -m pytest "test/test_rmux_backend_core.py" "test/test_v2_project_namespace_backend.py" -q`
  - 结果：`test_v2_project_namespace_backend.py` 相关用例通过；`test_rmux_backend_core.py::test_pane_core_uses_backend_local_refs_without_tmux_percent_requirement` 失败，失败原因是当前环境下 respawn 命令为普通 `"codex"`，测试按 Windows PowerShell base64 包装解码，和本次 canonicalization 改动无关。

## 6. 遗留事项

- 严格 CodeStable 独立 review gate 尚未通过：当前环境没有可同步返回的 Task agent review；`ocr llm test` 返回 403。
- 需要重启 / 重建当前 rmux namespace 后，才能让已存在的错误 pane 运行态按新逻辑重新 materialize；本轮未主动 kill 当前 CCB namespace，避免影响正在运行的会话。
