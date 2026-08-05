---
doc_type: audit-finding
audit: herdr-ccb-recent-changes
finding_id: "05"
nature: maintainability
severity: P1
confidence: high
recommended_action: cs-refactor
---

# Finding 05：`run_spike.ps1` 与 `ccb8.ps1` 重复了约 70 行参数引用函数

## 位置

`run_spike.ps1:83-117`，`ccb8.ps1:553-589`

## 证据

两个文件各自独立定义了以下函数（实现完全相同）：

```powershell
# 两个文件中完全相同的函数
function Quote-WindowsProcessArgument { ... }   # run_spike.ps1:83-112, ccb8.ps1:554-583
function Join-WindowsProcessArguments { ... }   # run_spike.ps1:114-117, ccb8.ps1:586-589
```

此外 `Test-Utf8Bom`、`Write-Utf8NoBom`、`Redact-Text` 也在两个文件中各自定义。

## 问题

1. 任一文件的 bug 修复需同步到另一文件——当前的 fix-note 显示了这种跨文件同步的维护成本
2. 两个文件各行约 1,100 行，重复逻辑约占 6-7%
3. `run_spike.ps1` 是采集/验证脚本，`ccb8.ps1` 是运行时 wrapper，职责不同但共享了通用工具函数——抽象到共享模块是最自然的解耦方式

## 修复方向

将共享工具函数提取到独立 `.psm1` 模块（如 `ccb8-shared.psm1`），两个脚本都 `Import-Module` 引入。短期可用 dot-source 引入共享 `.ps1`。
