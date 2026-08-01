---
doc_type: feature-implementation
feature: 2026-07-25-windows-rmux-wezterm-native-interaction-parity
status: completed
implemented: 2026-07-27
---

# windows-rmux-wezterm-native-interaction-parity 实现完成汇报

## 动了哪些文件

- `lib/cli/services/tmux_ui_runtime/service.py`
- `test/test_v2_tmux_ui.py`
- `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-checklist.yaml`
- `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/evidence/live-binding-snapshot.txt`
- `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/evidence/manual-wezterm-runbook.md`
- `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/evidence/windows-rmux-ux-parity-evidence.json`
- `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-gate-results.json`
- `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-dod-results.json`
- `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-evidence-pack.md`
- `.codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-evidence-pack-results.json`
- `.codestable/roadmap/windows-rmux-ux-parity-hardening/goal-state.yaml`

## 改了哪些函数 / 类型

**步骤 1：普通 pane GUI-native wheel fallback**

- `lib/cli/services/tmux_ui_runtime/service.py:266` `_apply_sidebar_mouse_controls_without_mouse_pane_format`：删除普通 pane wheel 的 `copy-mode -e` / `send-keys -X scroll-*` fallback，改为普通 pane `select-pane -M`；sidebar 分支保持 `select-pane -M ; send-keys -M`。
- `test/test_v2_tmux_ui.py:342` `test_windows_rmux_project_ui_avoids_shell_status_commands`：反转 Windows/rmux 普通 pane wheel 断言，明确不含 `send-keys -M`、`copy-mode -e`、`history_size`、`alternate_on` 和 scroll command。
- `test/test_v2_tmux_ui.py:420` `test_rmux_accepts_mouse_context_project_ui_bindings`：live rmux root binding 断言同步为普通 pane no-copy-mode。

## 方案边界

- 方案外文件：否；除 goal-state 状态推进外，改动均属于本 feature 代码、测试或证据目录。
- 新概念 / 抽象：否；没有新增交互模式、配置 key、adapter、schema 或 provider capture 逻辑。
- 第一性原则 pre-pass：外部行为只改变 Windows/rmux 普通 pane wheel fallback；不可破约束是 sidebar 全接管、右键不 paste-buffer、左键不裸透传、非 Windows tmux 路径不回退；最小充分改动是复用现有 fallback 分流；必须不写的是模式开关、history viewer、provider capture 修改和 install/support 文案。

## Step 证据

| Step | 结果 | 证据 |
|---|---|---|
| S1 普通 pane fallback 收紧 | done | RED：更新 targeted 测试后旧实现失败；GREEN：`python -m pytest -q test/test_v2_tmux_ui.py -k windows_rmux_project_ui_avoids_shell_status_commands` 通过。 |
| S2 sidebar 交互保持 | done | fake binding 仍保留 sidebar `select-pane -M ; send-keys -M`、settings `c`、KillProject `Q`；cargo targeted test 1 passed。 |
| S3 live binding snapshot | done | `evidence/live-binding-snapshot.txt`；live rmux binding test 1 passed。 |
| S4 manual WezTerm runbook | done | `evidence/manual-wezterm-runbook.md` 记录为 partial；非交互 API 会话无法实际执行前台点击/剪贴板。 |
| S5 回归收口 | done | checklist YAML、pytest、py_compile、cargo targeted、cargo full、live rmux test 均通过。 |

## TDD 证据

- RED：`python -m pytest -q test/test_v2_tmux_ui.py -k windows_rmux_project_ui_avoids_shell_status_commands` 在旧实现下失败，失败点为普通 pane wheel 分支仍包含 `send-keys -M` / `copy-mode -e`。
- GREEN：删除普通 pane wheel copy-mode fallback 后同命令通过。
- VERIFY：全量 `test/test_v2_tmux_ui.py`、live rmux binding、py_compile 和 sidebar cargo tests 通过。

## 基线预检与清洁度

- 基线 checklist YAML：通过。
- 基线 targeted Python 测试：旧语义通过；随后按新契约制造 RED。
- `cargo` 初始不在 PATH；本机存在 `C:/Users/Administrator/.cargo/bin/cargo.exe`，DoD runner 通过显式 PATH 补入后执行成功。
- `git diff --check`：通过。
- 清洁度 grep：未发现本次新增 debug output、临时 TODO/FIXME/XXX、注释掉代码或无用 import。

## 验证命令

- `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-25-windows-rmux-wezterm-native-interaction-parity/windows-rmux-wezterm-native-interaction-parity-checklist.yaml" --yaml-only`：通过。
- `python -m pytest -q test/test_v2_tmux_ui.py`：13 passed, 2 skipped。
- `cargo test --manifest-path "tools/ccb-agent-sidebar/Cargo.toml" shifted_q_is_project_kill_across_terminal_key_encodings --quiet`：1 passed。
- `cargo test --manifest-path "tools/ccb-agent-sidebar/Cargo.toml" --quiet`：54 passed。
- `python -m py_compile "lib/cli/services/tmux_ui_runtime/service.py" "test/test_v2_tmux_ui.py"`：通过。
- `python -m pytest -q -rs test/test_v2_tmux_ui.py -k rmux_accepts_mouse_context_project_ui_bindings`：1 passed, 14 deselected。

## 验收场景自检

- AC-001 / AC-003 / AC-004：unit + live binding snapshot 覆盖。
- AC-002：unit 断言 Windows/rmux fallback 不绑定 `MouseDown3Pane` / `M-MouseDown3Pane` 到 `paste-buffer -p`。
- AC-005：sidebar cargo targeted test 覆盖。
- AC-006：全量 `test/test_v2_tmux_ui.py` 覆盖。
- AC-007：manual runbook 已记录 partial；真实前台 GUI 操作仍是 QA / acceptance residual risk。

## 知识回写候选

- Windows PowerShell 环境下 CodeStable Python 工具若触发自身 re-exec，需设置 `PYTHONDONTWRITEBYTECODE=1`。
- Windows 下 `codestable-dod-runner.py` 跑 cargo 输出时需 `PYTHONUTF8=1`，否则 Python 3.14 默认 GBK 解码可能失败。
- `cargo` 不在 PATH 时可使用本机已有 `C:/Users/Administrator/.cargo/bin/cargo.exe`。

## 下一步

Goal 模式继续进入 `cs-code-review`。QA 必须重点处理 manual WezTerm runbook 的 partial residual risk，不能把 live binding snapshot 当成完整 GUI UX 证明。
