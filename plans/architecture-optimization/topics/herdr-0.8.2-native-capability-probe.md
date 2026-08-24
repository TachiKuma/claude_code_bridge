# Herdr 0.8.2 原生能力实机探针（12C/13A/13B/13C 阻塞判定）

日期：2026-08-24

探测对象：运行中的 Herdr `C:\Users\Administrator\AppData\Local\Programs\Herdr\herdr.exe`，版本 0.8.2，
protocol 20，socket `C:\Users\Administrator\AppData\Roaming\herdr\herdr.sock`。

方法：直接查询 Herdr **原生 API**（`herdr status server`、`herdr api schema --json`、
`herdr api snapshot`、`herdr agent list`），**不经 CCB 兼容层**——因为 CCB 的
`lib/platforms/windows/herdr/runtime/cli.py:131` 把 `agent_id_authority` 等能力位硬编码为
`supported`，会掩盖真实契约。

关联证据 artifact：`plans/architecture-optimization/live-validation/agent-id-authority.json`、
`archi-hotspot-baseline.json`（均 `passed:false`，附实机证据）。

## 关键发现

### 1. Herdr 没有 `agent_id`（阻塞 13A/13B）

- 全 API schema 中 `agent_id` 出现 **0 次**。
- agent 单体 `AgentInfo` 的身份字段为：`agent`（kind，如 `claude`）、`name`、`pane_id`、
  `terminal_id`、`agent_session`——**没有稳定的 Herdr 铸造 agent_id**。
- agent 归属的权威方向是 **CCB → Herdr**：`pane.report_agent`（参数含 `agent`/`pane_id`/
  `agent_session_id`/`state`）把身份 push 进 Herdr，配套 `pane.clear_agent_authority` 清除。
  不存在 Herdr → CCB 的 agent_id 回写通道。

结论：13A 的最低要求「Herdr 稳定回写 `agent_id`」在 Herdr 0.8.2 下**无法达成**。既然 Herdr
不是 agent_id 权威、`pane.report_agent` 又是它认可的**唯一 agent 归属 API**，13B「删除 CCB 主动补
身份路径」不仅不达标，删除还会**直接破坏 agent 状态归属**。

**实机 live-agent 复测（2026-08-24，补充）：** 用户手动在 Herdr 中启动 claude 与 codex CLI 后复测
`herdr agent list` / `agent get` / `agent explain`，坐实上述结论：

- 两个活 agent（`claude`@`w1:p1`、`codex`@`w1:p2`，`agent_status=idle`）完整字段中**仍无
  `agent_id`/`id`**，身份=`agent`(kind)+`pane_id`+`terminal_id`。
- **可寻址身份就是 `pane_id`**：`herdr agent get w1:p1` 成功，`herdr agent get claude` 报
  `agent_not_found`——agent 无法以名字/kind 寻址，只能以 `pane_id` 寻址。
- **检测机制是屏幕启发式**：`herdr agent explain w1:p1` 显示 Herdr 靠终端屏幕模式匹配识别
  （manifest 规则 `live_prompt_box`，evidence=`"❯\n"`），而非 agent 上报的身份令牌——这从根本上
  解释了为何没有稳定 `agent_id`。反过来印证 CCB 现有架构（CCB 报告身份、Herdr 观测）本就正确。

### 2. 无原生 restart/backoff，仅手动 close（阻塞 12C）

- 枚举全部 216 个 API method 常量：`restart` / `backoff` / `runtime.ensure` 均 **0 次**。
- 生命周期原语只有手动关闭：`workspace.close`、`pane.close`、`tab.close`、`worktree.remove`、
  `server.stop`。没有 Herdr 拥有的 restart/backoff 策略引擎。

结论：12C 的最低要求「把通用 pane restart/backoff 与 workspace cleanup 执行权下放 Herdr」
**无法达成**——Herdr 没有可下放的原生 restart/backoff 能力。

### 3. 有原生事件订阅（对 10B 是好消息）

- `events.subscribe` / `events.wait` 存在，且有 `pane.agent_status_changed`、
  `pane.agent_detected`、`pane.output_matched` 等细粒度事件；状态枚举
  `idle/working/blocked/done/unknown/attention` 与 CCB 的 Herdr→CCB 映射吻合。
- 这说明 10B 事件订阅适配器未来可切到 Herdr 原生 `events.subscribe`（当前仍走 snapshot polling
  兼容实现），不是本轮阻塞项。

## 对四个节点的判定

| 节点 | 最低要求 | Herdr 0.8.2 实机证据 | 达标 |
| --- | --- | --- | --- |
| 13A | Herdr 铸造/回传稳定 `agent_id` | 无 `agent_id` 字段；身份=pane_id+agent+name；权威 CCB→Herdr | 否 |
| 13B | 13A 通过后删 CCB 补身份路径 | `pane.report_agent` 是唯一 agent 归属 API，删除有害 | 否 |
| 12C | Herdr 原生 restart/backoff/cleanup | 无 restart/backoff/ensure，仅手动 close 原语 | 否 |
| 13C | live validation 覆盖 + 删除门禁 | 门禁已就位；前台回退/mux attach/脱敏可实机跑，但其门禁的 13A/13B 删除卡在 API 层 | 部分 |

## 结论

12C/13A/13B 的阻塞根因不是「缺实机环境」，而是 **Herdr 0.8.2 的 API 本身不提供这些能力**——
比缺环境更硬的上游阻塞。实机环境到位只解锁了 13C 验收矩阵里**与 agent_id 无关**的那几项
（前台回退可观测、mux 多项目 attach、mobile gateway 脱敏），但这些验收所门禁的删除动作仍因
13A 无法证明而保持 blocked。删除门禁 `scripts/phase5_deletion_gate.py` 已据上述负证据持续
fail-closed，符合预期。

后续可选路径（需用户决策，均超出「只在 CCB 侧配合」的现有范围）：
- 等 Herdr 上游在更高版本提供 `agent_id` 权威与原生 runtime.ensure/restart/backoff；
- 或据本发现更新 `docs/adr/0001-三层运行时权威边界.md`，把「CCB 报告 agent 身份、Herdr 不铸造
  agent_id」确立为长期契约，从而**关闭**（而非等待）13A/13B/12C 的下放设想。
