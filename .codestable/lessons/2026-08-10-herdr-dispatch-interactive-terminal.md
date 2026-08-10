---
status: observed
scope: Native Windows / Herdr / CCB 一键启动 / agent dispatch 触发条件
date: 2026-08-10
---
规则：Herdr 的 agent dispatch 只能由交互式终端输入触发，不能由 programmatic child-process invocation（如 `Start-Process`、`subprocess.Popen` 的非交互子进程）触发。在 Herdr 支持结构化 agent dispatch API 之前，将 agent 放入 Herdr pane 后触发其 dispatch 的唯一可靠方式是让 herdr 进程本身运行在交互式终端中——无论是用户手动键入命令、还是通过 wezterm cli send-text 注入模拟键盘输入。后续 `ccb herdr dispatch` 只能表达 Herdr terminal agent activation primitive，不能成为第二套 CCB job dispatcher、不能持有 job / queue / completion / cancel 权威，也不能复活 legacy topology dispatch / communication DSL。

适用 / 不适用：适用于所有需要 Herdr 在 agent pane 中识别并启动 coding agent 的场景（CCB 一键启动、pane 恢复、agent restart、未来 `ccb herdr dispatch`）；不适用于 CCB job 分发、completion 判定、cancel/followup、queue 调度、topology loop 编排，或已在 Herdr TUI 内部手动操作的用户交互场景（dispatch 自然触发）。

后果：
- ccb8.ps1 的 `wezterm cli send-text --no-paste` 是满足此约束的唯一已知 workaround，被接受为 bootstrap shim，不是优雅终态。
- 任何试图用 `Start-Process`、`subprocess.Popen(detached)` 替代 send-text 的方案都必然失败——dispatch 不会触发，agent pane 中有 shell 但 agent 未被识别。
- 优雅终态需要 Herdr 侧提供程序化 dispatch 触发机制（如 `herdr agent start` 在 shell pane 中显式启动 agent 并触发 detection），或 CCB 侧新增 capability-gated 的结构化原语；能力不存在时必须返回 structured blocked，不得静默退回后台子进程。
- 在 Herdr 未提供此能力之前，`send-text` 键盘注入是唯一正确的实现路径；不应被当作 bug。

当前代码状态标记（2026-08-10）：
- `ccb herdr open` 的 P0/P1/P2/P3 启动链路瘦身已落地：Python 侧负责 Herdr server 生命周期、`--wait-ready` 等 ccbd mounted，UI attach 走结构化 `session attach` 路线并保留 fallback。
- CLI parser 当前只支持 `ccb herdr open`；不存在 `ccb herdr dispatch` 子命令、模型或 handler。
- Herdr capability 当前没有 `agent_dispatch` / `agent_start` 逻辑能力；已有能力是 `pane_run`、`send_input`、`attach_namespace` 等 terminal primitive。未来实现必须先加 capability gate 与 blocked 语义，再接真实 Herdr 原生能力。

证据：
- .codestable/compound/2026-08-10-ccb8-bootstrap-shim-analysis.md（综合分析 + 优化方案 P0-P3 + 长期 dispatch follow-up）
- lib/cli/phase2_runtime/handlers_start.py 与 lib/cli/parser_runtime/commands.py（`ccb herdr open` 当前入口与 parser 状态）
- lib/terminal_runtime/herdr_backend_runtime/capabilities.py 与 lib/terminal_runtime/herdr_backend_runtime/cli.py（Herdr primitive capability 与 adapter 状态）

候选归宿：project-doc（项目级经验规则，影响所有 Herdr 相关的一键启动和 restore 设计）
