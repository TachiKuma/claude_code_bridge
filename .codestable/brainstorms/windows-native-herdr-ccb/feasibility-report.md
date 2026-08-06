# CCB v8.5.2 + Herdr Native Windows 可行性报告

> 2026-07-30（2026-08-06 实现后回顾追加）| 输入：`.codestable/brainstorms/windows-native-herdr-ccb/brainstorm.md`

## 结论

可行，但不是低风险替换。推荐路线是把 Herdr 作为 Native Windows 的 terminal multiplexer/session backend，CCB 保持 control plane、provider runtime、completion、Mobile、Config UI、update、doctor/support tier 的权威边界。

不建议把目标表述为“Herdr 直接实现 CCB 全功能”。更准确的目标是：CCB v8.5.2 增加一个 Native Windows backend，底层 pane/session 能力由 Herdr 提供，最终达到 CCB public workflow parity。

## 基底事实

- `v8.5.2` tag 存在，`v8.5.2:package.json` 版本为 `8.5.2`。
- `v8.5.2` npm package metadata 的 `os` 仅包含 `linux` / `darwin`，说明官方 release surface 尚未把 `win32` 纳入支持目标。
- `v8.5.2` release 重点是 bounded pane recovery、managed communication 精简、Rich WezTerm detached launch，并非 Native Windows 发布。
- 当前工作区 `package.json` 显示 `8.2.1`，且有大量未提交 CodeStable 产物。后续实现必须先明确基线：从 `v8.5.2` tag 创建实现线，或把当前开发线同步到等价基线后再继续。

## Herdr 能力匹配

Herdr 对本目标有明显吸引力：

- Herdr 文档和仓库描述面向 agentic terminal multiplexer，提供 session/pane、agent detection、session restore、插件和 socket API。
- Windows beta 明确使用 ConPTY pane，是 Native Windows 终端 primitive，比在 Windows 上模拟 tmux/rmux 更贴近平台。
- socket API 适合作为 CCB backend adapter 的边界，避免 CCB 直接绑定 Herdr 内部 Rust/Swift/TypeScript 实现。

主要缺口也很明确：

- Windows beta 仍有不支持项，例如 native Windows 下 remote/live handoff/fd handoff/process group 相关能力不可用或受限。
- Herdr 的 agent state 与 CCB 的 provider runtime state 存在重叠。CCB 不能把 Herdr 的 agent detection 直接作为 completion/ping/health 权威，只能作为 evidence 输入。
- CCB v8.5.2 的 package/release surface 还不是 Windows-native：installer、postinstall、runtime dependency、Python managed env、path/permission、socket authority、support tier 都要补。

## 功能映射

| CCB 能力 | Herdr 映射 | 可行性 | 备注 |
|---|---|---:|---|
| `ccb` 启动项目 session | Herdr session create/restore | 高 | 需要 project identity -> Herdr session name 的稳定映射。 |
| provider pane 创建 | Herdr pane + ConPTY | 高 | CCB 仍负责 provider home/env/auth 隔离。 |
| split/layout/focus | Herdr pane/layout API | 中高 | 需验证 API 是否暴露足够的 resize/focus/pane id 稳定性。 |
| `ask` 输入投递 | pane input/send API | 中高 | 必须保留 request id、caller、cancellation、queue 语义。 |
| `pend`/completion 捕获 | pane output/read + provider native logs | 中 | CCB 不能只依赖 terminal capture；仍需 provider-specific completion contract。 |
| `ping`/mounted/project view | CCB ccbd + Herdr health evidence | 中高 | Herdr 是 runtime evidence，不是唯一 authority。 |
| pane crash recovery | CCB bounded recovery + Herdr pane respawn | 中 | 需避免 CCB 和 Herdr 同时自动恢复造成双重 respawn。 |
| attach/reattach | Herdr attach/session restore | 中 | Windows beta 限制会影响 parity 承诺。 |
| Mobile terminal | CCB relay + Herdr output stream | 中 | 需要 terminal snapshot/resize/wide-char 重新验收。 |
| Config UI/update/doctor | CCB 原体系 | 高 | 主要是 Windows packaging 和 support projection 工作。 |

## 推荐架构

新增一个边界清晰的 backend adapter：

```text
CCB CLI / ccbd / provider runtime
        |
        v
MuxBackend / PaneRuntime contract
        |
        v
HerdrBackendClient
        |
        v
Herdr socket API / Windows ConPTY panes
```

关键原则：

- CCB owns provider state：登录、私有 HOME、session binding、completion、cancellation、queue、bounded recovery 仍由 CCB 管。
- Herdr owns terminal primitive：session、pane、ConPTY、layout、attach、basic output stream 由 Herdr 管。
- 单向证据流：Herdr agent detection 可以进入 diagnostics，但不能直接覆盖 CCB runtime truth。
- fail closed：Herdr API 缺失或 Windows beta 不支持的能力必须投影为 `unsupported` / `beta` / `blocked`，不做静默 fallback。

## 主要风险

1. **API 稳定性风险**：Herdr socket API 如果仍在快速变化，CCB adapter 需要版本探测和 schema gate。
2. **双恢复风险**：Herdr session restore 和 CCB bounded recovery 都可能尝试恢复 pane，必须明确唯一恢复 owner。
3. **completion 误判风险**：Herdr 的 agent state 不等于 provider final-answer contract；Codex/Claude/Gemini/Pi/OMP 等仍需各自 native completion 证据。
4. **Windows release 风险**：`v8.5.2` 官方 metadata 未包含 `win32`，发布前要补 npm/install/update/doctor/support docs。
5. **UX parity 风险**：Windows beta 下 remote/live handoff 等限制意味着第一版只能承诺 CCB core workflow parity，不能承诺所有 Herdr/Unix 行为 parity。

## 建议拆解

1. `herdr-backend-contract-spike`：锁定 Herdr 版本和 socket schema，验证 create session、pane spawn、send input、read output、kill pane、restore。
2. `mux-backend-contract-v2`：把 CCB v8.5.2 的 tmux assumptions 抽到 backend contract，不把 Herdr 特例散落到业务层。
3. `herdr-native-windows-backend`：实现 Herdr backend client 和 Windows capability gate。
4. `provider-runtime-on-herdr`：让 Codex/Claude/Gemini/Opencode 等托管 provider 在 Herdr pane 中启动、投递、捕获。
5. `ccbd-windows-release-surface`：补 win32 package metadata、postinstall、managed Python、path/permission、loopback/socket authority。
6. `native-windows-validation-matrix`：覆盖 ask/pend/ping/mounted/kill/restart/reload/Mobile terminal/Config UI/update/doctor。
7. `supportability-projection`：将 Native Windows 标为 beta/experimental，只有矩阵通过后再升级 support tier。

## 最小 Spike 验收

进入正式 epic 前，建议先做一个很小的 spike：

- 在 Native Windows 上启动 Herdr server。
- 通过 socket API 创建一个 project-scoped session。
- 创建两个 pane，分别启动 `powershell` 和一个 provider CLI dry run。
- 从 Python 客户端发送输入并读取输出。
- 杀掉一个 pane，验证 CCB 侧能观察失败并由单一 owner 恢复。
- 重启 Herdr 或关闭前端窗口后，验证 session identity、pane id、输出捕获是否可恢复。

Spike 通过后再进入 `cs-epic`。Spike 未通过时，不应继续做全量 adapter；应先把失败点拆成 Herdr upstream issue、CCB contract 调整，或降低 Native Windows support scope。

## 外部资料

- Herdr GitHub: https://github.com/herdrdev/herdr
- Herdr docs: https://herdr.dev/docs/
- Herdr Windows beta: https://herdr.dev/docs/windows-beta/
- Herdr socket API: https://herdr.dev/docs/socket-api/
- Herdr session state: https://herdr.dev/docs/session-state/

## 2026-08-06 实现后回顾

> 本报告写于 2026-07-30 spike 之前。以下为 12 个 roadmap item 完成后的事实更新。

### 原始结论验证

原结论"可行，但不是低风险替换"——**已证实正确**。C2 非对称联邦架构在工程上可行，12 个 roadmap item 中 11 个已 acceptance passed（§12 supportability projection 仍在进行中）。主要风险项中的 API 稳定性、双恢复、completion 误判、Windows release、UX parity 均已通过 contract gate、recovery boundary、provider runtime 和 support projection 得到控制。

### 建议拆解完成情况

对照原报告 7 步拆解建议：

| 原建议 | 对应 roadmap item | 状态 |
|---|---|---|
| 1. herdr-backend-contract-spike | §2 | ✅ verdict=partial, failure_class=windows-beta-gap, adapter_recommendation=continue-with-gaps |
| 2. mux-backend-contract-v2 | §3 | ✅ backend-neutral refs/capabilities/errors, resolver v2 |
| 3. herdr-native-windows-backend | §4 | ✅ HerdrBackend + HerdrSocketClient + HerdrCapabilityGate |
| 4. provider-runtime-on-herdr | §7 | ✅ 全部 20 个 public provider 支持 Herdr assigned pane |
| 5. ccbd-windows-release-surface | §10 | ✅ npm install dry-run gate |
| 6. native-windows-validation-matrix | §11 | ✅ schema + rows 就绪，证据全部 blocked（待真实环境采集） |
| 7. supportability-projection | §12 | 🔄 进行中 |

### 功能映射回顾

对照原报告功能映射表，基于实际实现更新：

| CCB 能力 | 原评估 | 实际状态 | 备注 |
|---|---|---|---|
| `ccb` 启动项目 session | 高 | ✅ | namespace lifecycle CMD-013 passed |
| provider pane 创建 | 高 | ✅ | 19 个 provider 均适配 Herdr assigned pane |
| split/layout/focus | 中高 | ✅ | ensure_window + create_pane + split_pane + reflow_window |
| `ask` 输入投递 | 中高 | ✅ | send_text + respawn_pane |
| `pend`/completion 捕获 | 中 | ✅ | capture_pane + provider-specific completion contract |
| `ping`/mounted/project view | 中高 | ✅ | CMD-008 surface transcript passed |
| pane crash recovery | 中 | ✅ | bounded recovery + Herdr auto-restore disabled gate |
| attach/reattach | 中 | ✅ | foreground_attach CMD-008 passed（Herdr UI 中 timeout 降级处理） |
| Mobile terminal | 中 | ⚠️ | projection 到位，matrix 中 blocked（缺真实环境 transcript） |
| Config UI/update/doctor | 高 | ✅ | surface parity projection 到位 |

### 原始风险项当前状态

| 原风险 | 当前状态 |
|---|---|
| API 稳定性风险 | ✅ HerdrSocketClient 内置 `EXPECTED_HERDR_API_SCHEMA` version gate + `server_info` schema mismatch 检测 |
| 双恢复风险 | ✅ CCB 为唯一 recovery owner；Herdr auto-restore 仅 disabled 可进入 recovery-capable path |
| completion 误判风险 | ✅ Herdr agent state diagnostics-only，completion authority 仍归 CCB provider-specific contract |
| Windows release 风险 | ⚠️ release surface gate 已建立（npm install dry-run），但 `v8.5.2` 官方 metadata 仍未包含 `win32` |
| UX parity 风险 | ✅ CMD-008 覆盖 foreground/Mobile/Config UI/ping/project view/doctor/mounted |

### 距"全功能"还差什么

1. **真实环境 transcript 证据**：~~全部 blocked~~ → 11/14 partial, 3/14 blocked
   （run-20260807-004015: 19/19 维度, 0 failures, pane_state=alive 证实）
2. **support tier 正式化**：✅ §12 核心模块已完成（19 tests），doctor/docs consumer 端待后续
3. **A-lite / B-lite / bridge config**：✅ ITEM-4/5/6 已交付
4. **managed/attached/import 模式契约**：✅ 预期语义已写入 ADR-001，精确 contract 留给后续 feature
5. **Herdr per-pane auto-restore disable**：✅ 2026-08-07 双验证确认，`config.toml` 已写入 `resume_agents_on_restore = false` + `server reload-config applied`，mode=disabled。Herdr 默认 `[session] resume_agents_on_restore = true`，但 CCB agents 无官方 Herdr 集成，auto-restore 不会主动恢复 CCB agents

## 2026-08-07 19 维度验证 — 事后更新

### 关键证实

- **CCB 在 Herdr v0.8.0 中功能完全正常**（两次采集 run-002147 + run-004015 一致证实）
- **pane_state: unknown → alive**（Herdr liveness fix 在真实环境生效）
- **Kill/Restart 全周期通过**（kill=ok → unmounted → restart=mounted, gen 4→5）
- **Ask smoke 管道通畅**（job accepted for agent1）
- **Reload smoke 稳定**（noop on unchanged config）
- **采集脚本 13 → 19 维度**，全部执行通过

### 新发现

- **"无法目视 CLI" 根因确认**：Herdr viewport/rendering 问题，非 CCB 启动失败。Provider 在 pane 中持续输出内容（两次采集一致证实）。
- **Herdr workspace 累积**：6 个同名 workspace，每次 kill/restart 未清理旧 namespace。
- **herdr_auto_restore_mode=unknown**：config.toml 无此字段，需确认 Herdr 默认行为。
