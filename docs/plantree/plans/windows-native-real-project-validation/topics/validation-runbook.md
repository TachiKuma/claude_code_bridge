# Windows 原生外部项目验收 Runbook

日期：2026-08-25

## 约定

以下命令在 Windows 原生 PowerShell 中执行。除明确说明外，当前目录必须是外部项目
根，不是 CCB 仓库根。

```powershell
$Ccb = "E:\GitHub开源项目\TachiKuma\claude_code_bridge\ccb.cmd"
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$SmokeRoot = Join-Path $env:USERPROFILE "Desktop\ccb-smoke-$Stamp"
```

证据目录建议放在计划目录下：

```powershell
$EvidenceRoot = "E:\GitHub开源项目\TachiKuma\claude_code_bridge\docs\plantree\plans\windows-native-real-project-validation\evidence\$Stamp"
```

## 阶段 0：环境确认

记录：

```powershell
$PSVersionTable
Get-Command codex
Get-Command claude
& $Ccb --help
& $Ccb doctor
```

判断：

- `codex` 和 `claude` 必须来自已有用户环境；
- provider 登录态不在计划中重配；
- `ccb doctor` 的失败项必须先分类，不直接进入 smoke。

## 阶段 A：创建 smoke 项目

创建项目与最小配置：

```powershell
New-Item -ItemType Directory -Force -Path $SmokeRoot
New-Item -ItemType Directory -Force -Path (Join-Path $SmokeRoot ".ccb")
Set-Location $SmokeRoot

@'
version = 2
entry_window = "main"

[windows]
main = "win_codex:codex, win_claude:claude"

[ui.sidebar]
mode = "off"
'@ | Set-Content -Encoding UTF8 -Path ".ccb\ccb.config"
```

基础诊断：

```powershell
& $Ccb doctor
& $Ccb --diagnose
```

`ccb --diagnose` 当前未在 `ccb --help` 的公开命令列表中出现。实测时仍执行一次，
用于验证兼容入口是否存在；如果只打印 help 或返回非诊断结果，记录为兼容差异。

启动与观测：

```powershell
& $Ccb
& $Ccb doctor ps
& $Ccb ping ccbd
& $Ccb ping win_codex
& $Ccb ping win_claude
```

关闭：

```powershell
& $Ccb kill
& $Ccb doctor ps
```

只有当普通 `kill` 后仍能证明存在当前 smoke 项目拥有的 runtime 残留时，才执行：

```powershell
& $Ccb kill -f
```

## 阶段 B：真实项目准备

在真实项目根执行：

```powershell
$RealRoot = "替换为真实项目绝对路径"
Set-Location $RealRoot
git status --short
```

如果真实项目不是 Git 仓库，先记录允许写入范围：

```text
允许写入：.ccb/、CCB 管理的 provider home、CCB 日志、运行时状态。
禁止写入：业务源码、依赖锁文件、数据库、生产配置、用户全局 provider 配置。
```

创建或复用 `.ccb/ccb.config`。若项目已有配置，先备份到证据目录，不直接覆盖。

## 阶段 B：真实项目启动和关闭

```powershell
Set-Location $RealRoot
& $Ccb doctor
& $Ccb
& $Ccb doctor ps
& $Ccb doctor storage
& $Ccb kill
& $Ccb doctor ps
git status --short
```

验收重点：

- CCB 的 project root 必须是 `$RealRoot`；
- provider pane 的工作目录必须是 `$RealRoot` 或 CCB 记录的该项目 agent
  workspace；
- `git status --short` 不应出现业务源码的非预期变化。

## 阶段 C：跨 agent ask

在 smoke 项目和真实项目中至少各跑一次业务 ask。任务应要求读取或判断项目内容，
避免把 provider 空响应误判为协作成功。

示例：

```powershell
Set-Location $SmokeRoot
& $Ccb ask win_claude -- "读取当前目录结构，判断这个项目是不是 CCB 仓库源码目录。只返回结论和依据。"
& $Ccb ask win_codex -- "读取 .ccb/ccb.config，判断当前配置声明了哪些 agent 和 provider。只返回结论和依据。"
```

真实项目示例：

```powershell
Set-Location $RealRoot
& $Ccb ask win_claude -- "根据当前项目根的文件，判断项目类型和主要入口。不要修改文件。"
& $Ccb ask win_codex -- "根据当前项目根的文件，列出最可能的测试命令。不要运行测试，不要修改文件。"
```

每个 ask 记录：

- 提交命令；
- job id；
- `ccb pend <job_id>` 或 `ccb trace <job_id>` 输出；
- provider 最终回答摘要；
- 是否满足业务任务；
- 失败分类。

## 阶段 D：韧性场景

第二阶段执行，建议每个场景使用新的 smoke 项目或先 `ccb kill` 后重启，避免证据混杂。

中断：

```powershell
& $Ccb ask win_claude -- "执行一个需要 60 秒内持续推理的只读分析任务。"
& $Ccb ask cancel <job_id>
& $Ccb trace <job_id>
```

重启：

```powershell
& $Ccb restart win_claude
& $Ccb doctor ps
```

恢复或重建：

```powershell
& $Ccb
& $Ccb -n
& $Ccb doctor ps
```

上下文命令：

```powershell
& $Ccb clear win_claude
& $Ccb compact win_codex
```

followup：

```powershell
& $Ccb ask win_claude -- "等待我的 followup 后再给出最终结论。"
& $Ccb followup <job_id> --message "补充条件：只检查 README 和 package 文件。"
& $Ccb trace <job_id>
```

followup 只在 job 仍活跃且 provider/runtime 支持 active-turn 注入时作为通过证据；
若返回 `rejected`、`too_late` 或 `terminal`，按预期边界记录，不重试伪造通过。

## 清理

每轮结束：

```powershell
& $Ccb kill
& $Ccb doctor ps
```

smoke 项目可删除；真实项目只按允许范围清理 CCB 运行时文件。删除前必须确认目标路径
是本轮创建的 smoke 目录或明确授权的运行时目录。
