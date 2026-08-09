---
doc_type: compound
slug: ccb8-bootstrap-shim-analysis
status: accepted
created: 2026-08-10
summary: CCB 一键启动链路分析——ccb8.ps1 与 Python 侧的职责重叠、wezterm send-text 键盘注入的根因、以及把 dispatch 语义归位到 CCB/Herdr 结构化边界的优化方案
related_requirements:
  - .codestable/requirements/native-windows-ccb-via-herdr.md
related_epics:
  - .codestable/epics/windows-native-herdr-ccb.md
related_roadmap:
  - .codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-roadmap.md
related_compound:
  - .codestable/compound/2026-08-07-wezterm-herdr-ccb-cli-milestone.md
related_lessons:
  - .codestable/lessons/2026-08-10-herdr-dispatch-interactive-terminal.md
evidence:
  - ccb8.ps1 (lines 935-1137, 一键启动完整链路)
  - lib/cli/services/herdr_bootstrap.py (ensure_herdr_bootstrap_env)
  - lib/terminal_runtime/herdr_backend_runtime/cli.py (HerdrCliRequestAdapter._start_server + _command retry loop)
  - lib/cli/phase2_runtime/handlers_start.py (handle_herdr_open)
  - docs/native-windows-herdr-managed-launch.md (形态 1 / 形态 2)
  - .codestable/features/2026-07-31-herdr-backend-client/herdr-backend-client-acceptance.md
  - .codestable/features/2026-07-31-ccbd-herdr-namespace-lifecycle/evidence/cmd-013-herdr-cli-contract-verification.md
tags:
  - ccb8
  - bootstrap
  - herdr
  - wezterm
  - one-click
  - dispatch
  - architecture
---

# CCB 一键启动链路分析 — Bootstrap Shim 与优雅化路径

## 1. 现状：ccb8.ps1 一键启动的四阶段架构

`ccb8.cmd` 裸调（无参数）触发一键模式，`ccb8.ps1:935-1137` 完整编排了 4 个阶段：

```
Phase 0  参数检测         bare ccb8.cmd → isOneClick = true
Phase 1  预启动清理        杀旧 ccbd 进程、重置 state 文件、等 keeper stopped
Phase 2  Herdr server 预启动  herdr --session <name> server (Process.Start, CreateNoWindow)
Phase 3  Python 调用       ccb.py herdr open --no-attach
Phase 4  后启动 UI         wezterm cli spawn → send-text 键盘注入 → 等 15s
```

### 1.1 关键代码位置

| 阶段 | 行号 | 操作 |
|---|---|---|
| 参数检测 | 939-948 | `$CcbArgs = @('herdr', 'open', '--no-attach')` |
| 预启动清理 | 960-991 | `Invoke-PrestartCleanup` + keeper.json 轮询 |
| Herdr server 预启动 | 1007-1059 | `Process.Start` herdr server + `session list --json` 探活 |
| Python 调用 | 1061 | `& $env:CCB_PYTHON ccb.py @finalArgs` |
| lifecycle.json 轮询 | 1087-1103 | 90s 等 `phase == "mounted"` |
| WezTerm send-text | 1117-1122 | `wezterm cli spawn` → `send-text --no-paste` |

## 2. 问题诊断：PowerShell 与 Python 的职责重叠

### 2.1 四重重复

| 能力 | Python 已有实现 | PowerShell 重复 | 重复代码量 |
|---|---|---|---|
| Herdr server 启动 | `HerdrCliRequestAdapter._start_server()` (`cli.py:1211-1266`) + 20 次轮询确认 | `Process.Start` + `sleep 500ms` | ~50 行 |
| Session 探活 | `_discover_running_ccb_sessions()` (`herdr_bootstrap.py:152-192`) | `herdr session list --json` JSON 解析 | ~30 行 |
| NotFound 自动恢复 | `_command()` retry loop (`cli.py:1159-1178`)，最多 10 次重试 | 无（不知道 Python 有这个能力） | — |
| ccbd 就绪等待 | CCB 内部 startup polling | `lifecycle.json` 轮询 90s | ~20 行 |

**根因**：PowerShell 在调用 Python 之前做了 Python 能自动处理的事。Python 侧 `HerdrCliRequestAdapter._command()` 已经实现了"遇 NotFound → 自动起 server → 重试"的完整闭环，PowerShell 的预启动是冗余的。

### 2.2 wezterm send-text 键盘注入

`ccb8.ps1:1110-1126` 是当前链路中最 hacky 的部分：

```powershell
# ccb8.ps1:1110-1115
# Agent dispatch only fires when herdr runs via interactive
# terminal input, not programmatic child-process invocation.
# Spawn a new WezTerm tab, then send the herdr command as
# simulated keystrokes via wezterm cli send-text.
$paneId = (& $weztermCli cli spawn --cwd $env:CCB_PROJECT_ROOT 2>&1).Trim()
Start-Sleep -Seconds 2
$herdrCmd = "& `"$herdrExe`" --session $ccbSession`r`n"
& $weztermCli cli send-text --pane-id $paneId --no-paste $herdrCmd
```

**为什么必须这样做**：Herdr 的 agent dispatch 机制依赖交互式终端输入触发。通过 `Start-Process`（programmatic child-process invocation）启动的 herdr 无法触发 dispatch。这是 Herdr 当前的运行约束，不是 CCB 的设计缺陷。

`herdr-backend-client-acceptance.md` 已明确将 `send_text → pane run` 记录为已接受的适配决策，`stdin-style input` 约定另开协议。

### 2.3 已有文档化的替代路径

`docs/native-windows-herdr-managed-launch.md` 列出了两种形态：

| 形态 | 方式 | 当前状态 |
|---|---|---|
| 形态 1（推荐） | WezTerm 打开 Herdr，Herdr 触发 CCB | ccb8.ps1 实际执行的链路 |
| 形态 2（备选） | `config.default_prog = { 'ccb', 'herdr', 'open', '--no-attach' }` | 已文档化，未作为默认 |

## 3. 优雅化方案

### 3.1 核心原则

> **优雅不是把 PowerShell 字符串写得更漂亮，而是让 PowerShell 不再需要拼那些字符串。**

当前 ccb8.ps1 是 **bootstrap shim**——它在 Python/CCB 和 Herdr/WezTerm 之间的缝隙里做胶水。优雅终态是把 dispatch 语义归位到正确的架构层：

```
当前（bootstrap shim）：
  PowerShell 拼命令 → wezterm send-text 键盘注入 → Herdr dispatch

优雅终态：
  ccb herdr open（结构化命令）→ Herdr/CCB 内部 dispatch → agent 就绪
  ↑ PowerShell 只做 env 设置 + 单次调用
```

### 3.2 优先级排序

#### P0 · 消除重复逻辑（立即可做）

删除 `ccb8.ps1` 中与 Python `HerdrCliRequestAdapter` 重复的 server 启动和 session 探活代码。

**依据**：`cli.py:1211-1266` 的 `_start_server()` 启动后 20 次轮询确认；`cli.py:1159-1178` 的 `_command()` 在遇 NotFound 时自动起 server + 最多 10 次重试。PowerShell 的预启动既冗余又不同步（只 sleep 500ms，不等 confirm）。

**预期变化**：ccb8.ps1 删 ~80 行（server 预启动 + session 探活）。`ccb herdr open --no-attach` 的 Python 侧自动接管 server 生命周期。

#### P1 · ccbd 就绪等待进入 Python

给 `ccb herdr open` 加 `--wait-ready` flag，让 Python 侧 `handle_herdr_open()` 在 `handle_start()` 返回后阻塞等待 ccbd mounted，而不是由 PowerShell 轮询 `lifecycle.json`。

**依据**：CCB 内部已有 startup polling 机制，`--no-attach` 模式不应让 caller 自己轮询状态文件。

**预期变化**：
- Python：`handle_herdr_open()` 中加 ccbd 就绪轮询（复用已有 lifecycle state reader）
- PowerShell：删 lifecycle.json 轮询 ~20 行

#### P2 · 消除 wezterm send-text 键盘注入

将 Herdr UI attach 从键盘模拟迁移为结构化 Herdr 命令。两条平行路线：

**路线 A · `herdr agent start` 替代键盘注入**

```powershell
# 当前（hack）
& $weztermCli cli send-text --pane-id $paneId --no-paste $herdrCmd

# 优化后（结构化命令）
herdr agent start archi --kind claude --pane w1:p3
herdr agent start code_reviewer --kind codex --pane w1:p4
```

前提：Pane 已由 CCB 创建完成（`ccb herdr open` 已产出 pane ID），agent start 只需绑定 agent 到已有 shell pane。

**路线 B · `herdr session attach` 直接调用**

`HerdrCliRequestAdapter._attach_namespace()` (`cli.py:833-878`) 已实现 `herdr session attach`，当前受限于"非交互终端调用可能失败"。如果 `ccb herdr open` 本身在交互终端中运行（形态 2），此调用可自然成功。

**预期变化**：
- 路线 A：在 `handle_herdr_open` 或 ccb8.ps1 的 Phase 4 中，用 `herdr agent start` 替代 `wezterm send-text`
- 路线 B：配置 WezTerm `default_prog` 为 `ccb herdr open`，Python 进程在交互终端中，`herdr session attach` 自然成功

#### P3 · WezTerm default_prog 统一入口

将 ccb8.ps1 一键模式与文档化的"形态 2"对齐：

```lua
-- wezterm.lua
config.default_prog = { 'ccb', 'herdr', 'open' }
```

**预期变化**：
- 用户打开 WezTerm → 自动进入 CCB + Herdr 编程环境
- ccb8.ps1 从复杂编排退化为纯 env 引导
- 不再依赖 WezTerm CLI（`wezterm cli spawn` / `send-text`）

#### 长期 · `ccb herdr dispatch` 结构化原语

在 CCB 内部新增一个显式的 dispatch 原语，将"在 Herdr 交互 pane 中触发 agent 启动"固化为 CCB/Herdr 边界上的结构化语义：

```python
# 概念：不是 wrapper 拼命令，而是 CCB 调用 Herdr 的结构化能力
def dispatch_agents(
    session_name: str,
    agents: list[AgentSpec],  # name, kind, pane_id
) -> DispatchResult:
    for agent in agents:
        herdr.agent.start(agent.name, kind=agent.kind, pane=agent.pane_id)
        herdr.agent.wait(agent.name, until="idle", timeout=30000)
```

**预期变化**：PowerShell wrapper 退化为最薄的 env 引导层（~50 行），所有 dispatch 语义完全归位到 Python CCB 侧。

## 4. 方案可行性矩阵

| 优先级 | 方案 | Python 改动量 | PowerShell 改动量 | 依赖 | 风险 |
|---|---|---|---|---|---|
| P0 | 删 server/session 重复 | 0（已有能力） | -80 行 | 无 | 低·Python 自动恢复已验收 |
| P1 | `--wait-ready` | ~30 行（新 flag + 轮询） | -20 行 | 无 | 低·复用已有 state reader |
| P2-A | `herdr agent start` 替代 send-text | ~40 行 | -15 行 | Herdr CLI `agent start` 可用 | 中·需验证 agent start 后 dispatch 触发条件 |
| P2-B | `herdr session attach` 直接调用 | 0（已有实现） | -25 行 | 交互终端 | 中·`_attach_namespace` 有 5s timeout，非交互终端可能失败 |
| P3 | WezTerm default_prog | 0 | -20 行 | WezTerm 配置变更 | 低·已文档化备选方案 |
| 长期 | `ccb herdr dispatch` 原语 | ~200 行（新模块） | -30 行 | Herdr agent start API 稳定 | 中·新模块需要设计+测试 |

## 5. 不推荐的方向

1. **把 PowerShell 字符串拼接写得更复杂**——问题不在字符串本身，在于架构层错位
2. **在 PowerShell 中重写 Python 已有逻辑**——如更精细的 server 状态轮询、更复杂的 session 探活
3. **把 dispatch 降级为 `Start-Process` 式后台子进程**——与 Herdr 的交互终端约束矛盾，必然失败
4. **把 ccb8.ps1 从 PowerShell 改写为其他语言**——语言不是问题，架构才是

## 6. 决策记录

| 编号 | 决策 | 依据 |
|---|---|---|
| DEC-1 | ccb8.ps1 当前定位为 **bootstrap shim**，不是终态 | 4 处与 Python 的职责重叠 + send-text 键盘注入 |
| DEC-2 | 优雅化的方向是**架构归位**，不是**字符串美化** | Python 侧已有 server 生命周期、session 探活、NotFound 自动恢复能力 |
| DEC-3 | dispatch 语义的最终归属是 **CCB/Herdr 结构化边界**（长期 `ccb herdr dispatch`），短中期用 P0-P3 渐进 | code_reviewer agent 独立分析与本文分析一致 |
| DEC-4 | `send-text` 键盘注入在当前 Herdr 约束下是**有效的 workaround**，不应在 Herdr 支持 agent start API dispatch 之前被当作 bug 修复 | herdr-backend-client-acceptance 已接受此适配决策 |
