---
doc_type: issue-fix-note
issue: ccb-src-missing-drive-candidate-path
status: fixed
root_cause_type: powershell-path-resolution
tags:
  - windows
  - ccb-src
  - launcher
---

# ccb-src 缺失盘符候选路径修复记录

## 根因

`ccb-src.ps1` 在 `Resolve-CcbScript` 中用 `Join-Path "E:/" ...` 构造候选源码目录。PowerShell 会在 `Join-Path` 阶段解析盘符，当前机器不存在 E 盘时直接抛出 `Cannot find drive`，导致脚本还没进入 `Test-Path` 探测就中断。

同一段逻辑里，`Join-Path $expandedRoot "ccb.py"` 也可能在环境变量或候选路径指向缺失盘符时提前失败。

## 改动

- 将固定候选源码根从 `Join-Path` 构造改为普通路径字符串，避免构造阶段依赖盘符存在。
- 将候选 `ccb.py` 路径拼接改为 `[System.IO.Path]::Combine(...)`，只做文本级路径组合。
- 对 `Test-Path` 增加 `-ErrorAction SilentlyContinue`，缺失盘符或不可访问候选路径只视为未命中，继续检查下一个候选。
- 保留前一轮已加入的 `Push-Location $ProjectRoot` / `Pop-Location`，启动执行目录仍固定为项目自身并在退出时恢复。

## 验证

- PowerShell AST 解析通过：`Parser.ParseFile("ccb-src.ps1", ...)` 返回 `OK`。
- 用 `--project D:/tmp/should-not-run` 触发脚本初始化与快速退出，结果为预期的 `ccb-src is bound to D:\Python\GitHub\claude_code_bridge and does not accept --project overrides.`，不再出现 E 盘缺失错误。

## 遗留风险

未运行完整 `& "./ccb-src.ps1" kill -f; ...` 启动链路，因为该命令会停止/启动本项目 CCB 运行时并可能改写 `.ccb` 状态；当前验证已覆盖本次报错所在的路径解析阶段。
