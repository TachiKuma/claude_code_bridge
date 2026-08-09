---
status: observed
scope: Native Windows / Herdr / CCB 一键启动 / agent dispatch 触发条件
date: 2026-08-10
---
规则：Herdr 的 agent dispatch 只能由交互式终端输入触发，不能由 programmatic child-process invocation（如 `Start-Process`、`subprocess.Popen` 的非交互子进程）触发。在 Herdr 支持结构化 agent dispatch API 之前，将 agent 放入 Herdr pane 后触发其 dispatch 的唯一可靠方式是让 herdr 进程本身运行在交互式终端中——无论是用户手动键入命令、还是通过 wezterm cli send-text 注入模拟键盘输入。

适用 / 不适用：适用于所有需要 Herdr 在 agent pane 中识别并启动 coding agent 的场景（CCB 一键启动、pane 恢复、agent restart）；不适用于已在 Herdr TUI 内部手动操作的用户交互场景（dispatch 自然触发）。

后果：
- ccb8.ps1 的 `wezterm cli send-text --no-paste` 是满足此约束的唯一已知 workaround，被接受为 bootstrap shim，不是优雅终态。
- 任何试图用 `Start-Process`、`subprocess.Popen(detached)` 替代 send-text 的方案都必然失败——dispatch 不会触发，agent pane 中有 shell 但 agent 未被识别。
- 优雅终态需要 Herdr 侧提供程序化 dispatch 触发机制（如 `herdr agent start` 在 shell pane 中显式启动 agent 并触发 detection），或 CCB 侧新增对应的结构化原语。
- 在 Herdr 未提供此能力之前，`send-text` 键盘注入是唯一正确的实现路径；不应被当作 bug。

证据：
- ccb8.ps1:1110-1115（注释明确说明此约束）
- docs/native-windows-herdr-managed-launch.md（形态 1 / 形态 2 均围绕此约束设计）
- .codestable/features/2026-07-31-herdr-backend-client/herdr-backend-client-acceptance.md（send_text → pane run 已接受为适配决策）
- .codestable/compound/2026-08-10-ccb8-bootstrap-shim-analysis.md（综合分析 + 优化方案 P2-A / P2-B）

候选归宿：project-doc（项目级经验规则，影响所有 Herdr 相关的一键启动和 restore 设计）
