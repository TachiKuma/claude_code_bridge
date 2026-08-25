# Windows 原生外部项目验收测试计划

日期：2026-08-25

## 目标

设计并执行“Windows 原生外部项目验收测试”：在非仓库源码目录中，用
Windows 原生命令、终端、provider CLI 和 CCB 安装/源码入口，验证 CCB
的启动、运行时观测、跨 agent 协作和清理闭环。

本计划的测试对象是本仓库当前实现。测试时从外部项目目录运行绝对路径：

```powershell
& "E:\GitHub开源项目\TachiKuma\claude_code_bridge\ccb.cmd"
```

## 当前验收边界

本轮硬门槛是阶段 A 到阶段 C：

- 阶段 A：一次性 smoke 项目能完成环境、安装链路和基础诊断。
- 阶段 B：真实现有项目能在允许写入运行时文件的前提下启动并关闭。
- 阶段 C：Codex 与 Claude 两类 provider 能完成真实跨 agent `ask`，并拿到业务结果。

第二阶段覆盖韧性场景：

- 中断；
- 重启；
- 恢复；
- `clear`；
- `compact`；
- `followup`；
- 后续 provider 白名单扩展。

## 文件地图

- [roadmap.md](roadmap.md)：阶段路线、验收门槛和退出条件。
- [topics/validation-runbook.md](topics/validation-runbook.md)：Windows 原生实机执行步骤。
- [topics/test-matrix.md](topics/test-matrix.md)：场景矩阵、证据要求和失败分级。
- [evidence/README.md](evidence/README.md)：后续实测证据落盘约定。

## 关键约束

- 只测 `codex` 和 `claude` provider；保留 CCB provider 白名单的后续实现入口。
- CCB 可以安装到隔离 prefix。
- provider CLI、登录态、账号和本机认证材料必须使用已有用户环境。
- smoke 项目可自动创建和删除；真实项目只允许 CCB 写入 `.ccb/`、provider
  home、日志和其他运行时文件，不允许修改业务源码。
- `ccb --diagnose` 作为兼容入口验证；若当前 CLI 未暴露该入口，记录为差异，不用
  `ccb doctor` 的通过结果掩盖。

## 最小配置形态

外部测试项目使用 `version = 2` 的 `[windows]` 拓扑，只声明两个 agent：

```toml
version = 2
entry_window = "main"

[windows]
main = "win_codex:codex, win_claude:claude"

[ui.sidebar]
mode = "off"
```

如需开启可视化观测，可在实测记录中把 `ui.sidebar.mode` 改为当前 CCB 支持的
可视模式，但该变化必须作为证据记录。
