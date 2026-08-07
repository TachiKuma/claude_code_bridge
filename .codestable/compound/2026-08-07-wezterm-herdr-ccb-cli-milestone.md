# WezTerm + Herdr + CCB 联合启动：首次在原生 Windows 出现 CLI

## 背景

CCB v8.5.2 在 Native Windows x64 上缺少可用的 terminal multiplexer backend。前期工作完成了
C2 非对称联邦架构（CCB 拥有 agent/provider 权威，Herdr 拥有 workspace/pane/UI 权威）的
代码实现和 Epic 交付（2 个 accepted Epic，15+ commits，222+ tests）。

但直到 2026-08-07，用户仍报告"无法目视 CLI"——provider 进程在 Herdr pane 中确实运行并输出
内容（pane read 证实），但 Herdr UI 中看不到。根因是 Herdr viewport/rendering 层面的问题，
非 CCB 启动失败。

## 突破

2026-08-07 22:30 左右，在外部项目 `D:\C#Project\GitHub\AvaPrintDesigner` 中：

1. 在 WezTerm 中运行 `ccb8 herdr open --no-attach`，CCB 以 detached Herdr daemon 模式启动
2. 用 `herdr --session <session-name>` 将 Herdr UI 客户端 attach 到 CCB 创建的 session
3. **CLI 首次在 Herdr UI 中出现**——agent1/claude 和 agent2/codex 的 CLI 对话界面可见

## 完整启动序列

### 步骤 1：启动 CCB Herdr backend（WezTerm 中）

```powershell
D:\C#Project\GitHub\AvaPrintDesigner\ccb8.cmd herdr open --no-attach
```

这会在 Herdr 中创建 session `ccb-avaprintdesigner-575a971f`（`--no-attach` 表示不前台
attach，以 detached daemon 模式运行）。CCB 通过 Herdr socket API 创建 workspace 和 pane：
- w1X:p1 = sidebar（占位）
- w1X:p2 = cmd
- w1X:p3 = agent1（claude）
- w1X:p4 = agent2（codex）

### 步骤 2：Herdr UI attach 到 CCB session（终端中）

```powershell
herdr --session ccb-avaprintdesigner-575a971f
```

Herdr UI 客户端连接到已存在的 session server。左侧 session 面板出现
`ccb-avaprintdesigner-575a971f`，workspace 中的 pane 可见。**CLI 对话界面出现。**

## 为什么之前看不到 CLI

| 尝试 | 环境 | 问题 |
|---|---|---|
| Herdr UI 中直接 `ccb8.cmd` | `Herdr_Guides` workspace | workspace 已被占用，CCB 无法创建 agent pane，`runtime_panes=0` |
| WezTerm 中 `ccb8.cmd` | 无 Herdr 环境 | `HERDR_ENV` 缺失，CCB fallback 到非 Herdr backend |
| `ccb8 herdr open --no-attach` | detached daemon | session 创建成功、pane 创建成功，但 Herdr UI 看不到（未 attach） |
| **`herdr --session <name>`** | **UI attach** | ✅ **成功！UI 连接到已有 session，pane 可见** |

## 关键技术要点

1. **`ccb herdr open` 创建 detached session**：CCB 通过 Herdr socket API 在后台创建
   session/workspace/pane，不依赖 Herdr UI 客户端
2. **`herdr --session <name>` 连接已有 session**：这是让 UI 显示已存在的 detached session
   的关键命令
3. **session 名由 CCB 自动生成**：`ccb-{project-name}-{project-id前8位}`。对于
   AvaPrintDesigner，project_id 为 `575a971f...`，session 名为
   `ccb-avaprintdesigner-575a971f`
4. **WezTerm 作为启动入口**：WezTerm 打开 → 在 WezTerm 中运行 `ccb8 herdr open` →
   终端中 `herdr --session <name>` → Herdr UI 出现 CLI

## 证据

- Herdr session 验证：`ccb-avaprintdesigner-575a971f: running=True`，
  4 panes（sidebar/cmd/agent1/agent2）
- 采集证据：run-20260807-223227（`classification: ccb-mounted-not-proven`，
  `HERDR_ENV=1`，`cmd.exe=0`）
- 闪窗修复：`_ResolveCmdToPowerShell` 解析 `%~dp0` 后 cmd.exe 采样 = 0

## 下一步

简化到一键启动：WezTerm 打开 → 一条命令 → 预设编程环境就绪。
CCB sidebar 需要在实际使用中禁用（架构设计中其不工作，功能由 Herdr 侧边栏替代）。
