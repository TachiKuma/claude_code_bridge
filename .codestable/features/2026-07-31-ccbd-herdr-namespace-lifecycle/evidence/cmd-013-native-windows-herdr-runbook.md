---
doc_type: feature-evidence-runbook
feature: 2026-07-31-ccbd-herdr-namespace-lifecycle
command_id: CMD-013
status: blocked
updated_at: 2026-08-02
---

# CMD-013 Native Windows Herdr Transcript Runbook

## 目的

采集真实 Native Windows x64 + Herdr backend 下的前台/生命周期 transcript，用于证明 `ccbd-herdr-namespace-lifecycle` 的 S7 hard gate。

本文件不是 pass 证据。只有把实际运行输出保存为 `cmd-013-native-windows-herdr-transcript.md` 后，才能评估 S7 是否完成。

## 前置条件

- Native Windows，非 WSL。
- 64-bit Python。
- `herdr` CLI 可执行，或通过 `CCB_HERDR_EXE` 指向可执行文件。
- `CCB_HERDR_CAPABILITY_REPORT` 指向真实 Herdr capability report，且 report 包含 supported：`session_attach`、`pane_spawn`、`send_input`、`read_output`、`kill_pane`。
- `CCB_HERDR_SOCKET_REF` 指向真实 Herdr socket/ref。
- 测试目录不是当前开发仓库，避免污染工作树。

## 建议 PowerShell 采集脚本

在新的临时项目目录运行，保留完整 stdout/stderr。

```powershell
$ErrorActionPreference = "Continue"
$repo = "D:/Python/GitHub/claude_code_bridge"
$work = Join-Path $env:TEMP "ccb-herdr-cmd-013"
Remove-Item -LiteralPath $work -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $work | Out-Null
Set-Location $work

# 按真实主机替换：
$env:PYTHONPATH = Join-Path $repo "lib"
$env:CCB_SOURCE_RUNTIME_OK = "1"
$env:CCB_HERDR_EXE = "herdr"
$env:CCB_HERDR_SOCKET_REF = "herdr://local"
$env:CCB_HERDR_CAPABILITY_REPORT = "REPLACE_WITH_ABSOLUTE_CAPABILITY_REPORT_PATH"
$ccb = Join-Path $repo "ccb.py"

@"
version = 2
entry_window = "main"

[windows]
main = "agent1:codex"
"@ | Set-Content -LiteralPath ".ccb.config.tmp" -Encoding UTF8
New-Item -ItemType Directory -Force -Path ".ccb" | Out-Null
Move-Item -LiteralPath ".ccb.config.tmp" -Destination ".ccb/ccb.config" -Force

Write-Output "== platform =="
@'
import platform, sys
print({"sys_platform": sys.platform, "machine": platform.machine(), "python_bits": platform.architecture()[0]})
'@ | python -

Write-Output "== herdr availability =="
Get-Command $env:CCB_HERDR_EXE

Write-Output "== capability report =="
Get-Content -LiteralPath $env:CCB_HERDR_CAPABILITY_REPORT

Write-Output "== namespace create via ccb -n =="
python $ccb -n

Write-Output "== ccbd ping namespace payload =="
python $ccb ping ccbd

Write-Output "== foreground attach =="
python $ccb

Write-Output "== reload dry run =="
python $ccb reload --dry-run

Write-Output "== reload apply =="
python $ccb reload

Write-Output "== restart unsupported/deferred evidence =="
python $ccb restart agent1

Write-Output "== kill =="
python $ccb kill

Write-Output "== post-kill ping =="
python $ccb ping ccbd
```

如果使用已安装 release 命令替代源码入口，运行等价 `ccb` 命令即可，但 transcript 中必须记录实际入口。

## 必须保留的证据

- platform 输出显示 `win32`、`x64/AMD64`、`64bit`。
- Herdr capability report 的 source/path 和 supported capability 状态。
- `ccb -n` 或等价 start 输出能证明 Herdr project namespace 创建成功。
- `ping ccbd` / project payload 中包含 `namespace_backend_family=herdr-native`、`namespace_backend_impl=herdr`、`namespace_ipc_kind=herdr_socket`、`namespace_ipc_ref`、`namespace_restore_token_present`。
- foreground attach 路径显示 Herdr attach，不调用 tmux binary。
- reload apply 对 Herdr 走 V2 primitive，缺 primitive 时必须是 blocked/failed，不得 published/noop 成功。
- restart agent/panes 在 Herdr 下返回 unsupported/deferred evidence，不得 silent scheduled success。
- kill 只销毁当前 Herdr namespace。

## Redaction 检查

Transcript 不能包含 raw `restore_token` 值。允许出现：

- `namespace_restore_token_present: true`
- redacted namespace ref
- capability report path

如果输出中出现 raw token，先重采集并遮盖 token，再提交 transcript。

## 当前阻塞证据（2026-08-02 更新：blocker 已重归因）

早前「环境无 herdr」的前提**已被推翻**。真实复核：

- herdr 已安装于 `C:\Users\Administrator\AppData\Local\Programs\Herdr\herdr.exe`
  （`herdr 0.7.5-preview.2026-07-29`，protocol 18）；未进 PATH，但 runbook 支持用
  `CCB_HERDR_EXE` 指向绝对路径绕过。
- 对真实 herdr 做的 CLI 契约验证见
  `evidence/cmd-013-herdr-cli-contract-verification.md`：契约字段级几乎完全对齐，
  5 个必需 capability 真实可用。

新阻塞不再是「无 herdr」，而是首次真实端到端接触暴露的 **herdr socket client / adapter
对接缺陷**（server 生命周期缺失；split direction 词汇三方不对齐会污染 reload 布局），
全部落在已 accepted 的 `herdr-backend-client` scope，而当前 feature 明确
`herdr_socket_client_changes: forbidden`。需 owner 决策归属后先修对接，才能采到干净的
CMD-013 transcript。详见
`.codestable/roadmap/windows-native-herdr-ccb/approval-report.md` 的 Decision Needed。
