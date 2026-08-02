---
doc_type: feature-evidence
feature: 2026-07-31-ccbd-herdr-namespace-lifecycle
command_id: CMD-013
kind: real-herdr-cli-contract-verification
status: blocker-reattributed
updated_at: 2026-08-02
---

# CMD-013 真实 Herdr CLI 契约验证

## 背景

此前 goal 三次 handoff 的理由是「环境无 herdr 可执行文件 / 不在 PATH / 无 CCB_HERDR*」。
该前提**部分错误**：herdr 一直安装在本机，只是未进 PATH。本文件记录用真实 herdr
对 ccbd `HerdrCliRequestAdapter` 契约做的实测结果，并对 CMD-013 blocker 重新归因。

## 环境事实（真实 Native Windows x64）

- herdr 可执行：`C:\Users\Administrator\AppData\Local\Programs\Herdr\herdr.exe`
- 版本：`herdr 0.7.5-preview.2026-07-29-44b3adb12552`，protocol `18`
- session socket：`C:\Users\Administrator\AppData\Roaming\herdr\sessions\<session>\herdr.sock`
  （herdr 自身 Rust 实现使用 Windows AF_UNIX；不受 CPython `AF_UNIX` 缺失影响）
- 未进 PATH、未配 `CCB_HERDR*`；runbook 支持用 `CCB_HERDR_EXE` 指向绝对路径绕过 PATH。
- server 模型：**socket API 命令不会自动拉起 server**。server 未运行时
  `workspace list/create` 立即 `Error: Os { code: 2, kind: NotFound }`。必须显式
  `herdr --session <name> server`（headless 阻塞进程）先起 server；停止用
  `herdr --session <name> server stop`。

## 契约对照（真跑证据，独立 Task agent 验证）

ccbd 经 `herdr --session <name> <args>` 驱动 herdr（见
`lib/terminal_runtime/herdr_backend_runtime/cli.py`）。逐条实测：

| adapter 操作 / 命令 | 成功 | 真实 JSON 关键路径 | 与 adapter 期望 |
|---|---|---|---|
| server_info: `status --json` | ✓(无需 server) | `client.version` | 匹配 |
| server_info: `api schema --json` | ✓(无需 server) | 顶层 `title="Herdr API"` | 匹配（`EXPECTED_HERDR_API_SCHEMA` 精确对上） |
| create_session: `workspace create --cwd --label --focus` | ✓ | `result.workspace.workspace_id` | 匹配 |
| create_pane: `pane list` | ✓ | `result.panes[].pane_id`/`.workspace_id` | 匹配 |
| create_pane: `pane split <id> --direction --ratio --focus` | ✓ | `result.pane.pane_id` | 匹配（direction 取值见缺陷 3） |
| create_pane/send_text: `pane run <id> <cmd>` | ✓ | 无 JSON 需求 | 见缺陷 2 |
| capture_pane: `pane read <id> --lines N --format text` | ✓ | 纯文本 stdout | 匹配 |
| kill_pane: `pane close <id>` | ✓ | `result.type="ok"` | 匹配 |
| attach_namespace: `workspace focus <id>` | ✓ | `result.workspace.workspace_id` | 匹配 |
| restore_session: `workspace list` | ✓ | `result.workspaces[].workspace_id` | 匹配 |

补充：herdr 成功响应**无 `status:"ok"` 字段**（用 `type`/`error` 表达），错误时 exit code
非零。adapter 靠 `check=True` 的非零退出捕获错误，`_require_ok_json_status` 实为空操作但
不会误判。字段名 / 嵌套层级**无差异**。

## 5 个必需 capability 真实可用性

server 运行时全部真跑通过：

| capability | 结论 | 证据 |
|---|---|---|
| session_attach | 可用 | `workspace focus` 返回 focused=true |
| pane_spawn | 可用 | `pane split` 产出新 pane |
| send_input | 可用 | `pane run` / `pane send-text` 送出 |
| read_output | 可用 | `pane read --format text` 拿到真实输出 |
| kill_pane | 可用 | `pane close` 后 `pane list` 确认移除 |

## 发现的对接缺陷（全部落在 herdr socket client / adapter 层）

1. **【高·根本 blocker】server 生命周期缺失**。socket 命令不自动拉起 server；
   `lib/terminal_runtime/herdr_backend_runtime/{cli,client,capabilities}.py` 与 ccbd 侧
   均无 spawn/启动 headless server 的逻辑（adapter「只连不启」）。第一个写操作
   （create_session→`workspace create`）即 `NotFound`。现有 11 个 roadmap feature **无一
   归属「启动 herdr server」**。

2. **【中·语义 bug，本 goal 不触发】`send_text`→`pane run`**。实测 `pane run <id> text` =
   把 text 当命令行执行并回车；herdr 另有 `pane send-text`（送字面文本、不回车）。
   adapter 把 `send_text` 也映射到 `pane run`。但 ccbd 无任何独立 `send_text`/`send_input`
   调用（`grep` 确认），create_pane 用 `pane run` 发 provider 启动命令是正确语义。
   → 潜在缺陷，**不阻塞 CMD-013**，记录待 herdr 用户输入面 feature 处理。

3. **【中·会污染 CMD-013】split direction 词汇三方不对齐**。herdr `pane split --direction`
   只接受 `right|down`；adapter `_split_direction` 只认 `left|right|up|down`，其他 fallback
   到 `right`；而 ccbd 传的是 `right`/`bottom`（`materialize_topology.py:805/809`、
   `additive_patch_windows.py:317`）。ccbd 的 `'bottom'`（垂直分割）不在 adapter 白名单 →
   被错误归一成 `'right'`（水平分割）。**多 agent 布局 / reload 拓扑会退化**，CMD-013 的
   reload 场景 transcript 会记录错误布局。

其他（低）：herdr `pane split`/`workspace create` 支持 `--env`，adapter 主动拒绝（能力缺口，
非 bug）。

## 对 CMD-013 的影响与归因

- CMD-013 需覆盖 namespace create / foreground attach / kill / reload / restart
  unsupported-deferred。其中 **create/reload 会触发缺陷 3**（split direction），即便
  operator 手动先起 server（绕过缺陷 1），reload transcript 仍会记录错误布局。
- 因此 **CMD-013 无法在不修 herdr socket client 的前提下产出干净证据**。
- 三个缺陷全部属 `herdr-backend-client`（index 3，**已 accepted**）的
  "Herdr socket client / adapter boundary" scope，而当前 feature
  `ccbd-herdr-namespace-lifecycle` checklist 明确 `herdr_socket_client_changes: forbidden`。
- 根因：`herdr-backend-client` 的实现只对 spike/fake 契约与 fixtures 验证过，从未对真实
  herdr 验证（彼时判定「环境无 herdr」）。真实 herdr 到位后首次端到端接触即暴露上述缺陷。

## 结论

- 好消息：真实 herdr 定位成功；契约**字段级几乎完全对齐**；5 capability 真实可用。
- 阻塞：需 owner 决策（见 `.codestable/roadmap/windows-native-herdr-ccb/approval-report.md`
  Decision Needed）——如何归属修复（重开 `herdr-backend-client` / 建 issue / 新 roadmap
  item 承接 server 生命周期），再回到本 feature 采 CMD-013 transcript。
- 本次为只读探查 + 真跑 herdr，未修改任何仓库代码；临时 workspace/server 已清理。
</content>
</invoke>
