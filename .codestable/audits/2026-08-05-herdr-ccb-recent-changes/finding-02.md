---
doc_type: audit-finding
audit: herdr-ccb-recent-changes
finding_id: "02"
nature: bug
severity: P1
confidence: high
recommended_action: cs-issue
---

# Finding 02：`ccb8.cmd` 去掉了 `-WindowStyle Hidden`，非 Herdr 环境会闪窗

## 位置

`ccb8.cmd:8`

## 证据

```diff
-powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%CCB8_PS1%" %*
+powershell -NoProfile -ExecutionPolicy Bypass -File "%CCB8_PS1%" %*
```

## 问题

fix-note 中明确指出：

> 问题一：ccb8.cmd 闪窗
> `start "" /B` 在同一控制台窗口中启动进程（不创建新窗口）
> `-WindowStyle Hidden` 确保 PowerShell 窗口不可见

但当前仓库中的 `ccb8.cmd` 既没有 `start "" /B`（与 fix-note 记录的原始修复方案不同），也刚去掉了 `-WindowStyle Hidden`。

去掉 `-WindowStyle Hidden` 的理由可能是：fix-note 记录的"遗留风险"中提到 "在非 Herdr 环境的普通控制台中行为可能不同"。但这个改动方向有问题：

1. 如果目标是非 Herdr 普通控制台——此时无需隐藏窗口，但加上 `-WindowStyle Hidden` 也不会导致错误，只是 PowerShell 窗口瞬间隐藏然后恢复
2. 如果目标是 Herdr 环境——去掉该 flag 后 cmd.exe 作为控制台子系统进程被 Herdr 启动时仍会触发 Windows 自动分配控制台窗口，导致短暂闪窗

fix-note 中 `start "" /B` + `-WindowStyle Hidden` 的组合修复方案未能落地到当前仓库——取而代之的是直接删除 `-WindowStyle Hidden`，这实际上**回退**了闪窗修复。

## 影响

在 Herdr GUI 环境下启动 CCB 时，会出现短暂 cmd.exe 闪窗。

## 修复方向

恢复 `-WindowStyle Hidden`，或改用 fix-note 记录的原方案 `start "" /B powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%CCB8_PS1%" %*`。
