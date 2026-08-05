---
doc_type: audit-finding
audit: herdr-ccb-recent-changes
finding_id: "01"
nature: bug
severity: P0
confidence: high
recommended_action: cs-issue
---

# Finding 01：`run_spike.ps1` pane capture 在 session 歧义场景使用错误的 Herdr session

## 位置

`run_spike.ps1:887-898`

## 证据

```powershell
# 行 890 — capture 命令使用了 $effectiveHerdrSession，而非 $ccbHerdrSession
$captureResult = Invoke-CapturedCommand `
    -Name ('ccb-herdr-pane-capture-' + ...) `
    -Command (Add-HerdrSessionArgs -Command @($resolvedHerdr, 'pane', 'read', $paneId, '--lines', '3', '--format', 'text') -Session $effectiveHerdrSession) `
    ...
```

## 问题

前面行 823 已正确将 snapshot 来源切换到 CCB namespace session：

```powershell
$preferredSnapshotName = if ($ccbHerdrSession -and $ccbHerdrSession -ne $effectiveHerdrSession) { 'herdr-api-snapshot-ccb-namespace' } else { 'herdr-api-snapshot-after' }
```

但行 890 的 pane capture 调用仍**硬编码 `$effectiveHerdrSession`**，而非跟随 snapshot 切换逻辑。

当 `$ccbHerdrSession` != `$effectiveHerdrSession`（即 CCB 实际使用的 session 与 wrapper 默认 session 不同时），snapshot 从 `ccbHerdrSession` 提取 pane 列表，但 pane read 命令却打到 `$effectiveHerdrSession`——此时该 session 下**不存在这些 pane_id**，全部 capture 返回空文本或错误。

## 影响

pane verification report 中的 "Pane content capture" 节数据不可信——当 session 存在分歧时，所有 capture 结果均为空/failure，无法验证 CCB pane 是否真正有内容输出。

## 修复方向

将行 890 的 `-Session $effectiveHerdrSession` 改为使用与 snapshot 来源一致的 session：

```powershell
$captureSession = if ($ccbHerdrSession -and $ccbHerdrSession -ne $effectiveHerdrSession) { $ccbHerdrSession } else { $effectiveHerdrSession }
```
