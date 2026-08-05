---
doc_type: audit-finding
audit: herdr-ccb-recent-changes
finding_id: "07"
nature: maintainability
severity: P2
confidence: medium
recommended_action: cs-refactor
---

# Finding 07：`run_spike.ps1` 采集维度无法选择性启用，启动命令过长

## 位置

`run_spike.ps1` 主流程（行 678-1098）

## 证据

当前采集脚本的启动命令是：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "run_spike.ps1" \
  -ProjectRoot "C:\ccb8v" \
  -RepoRoot "E:\GitHub开源项目\TachiKuma\claude_code_bridge" \
  -HerdrExe "C:\Users\Administrator\AppData\Local\Programs\Herdr\herdr.exe" \
  -HerdrSession "ccb-herdr-avaprintdesigner-source-dev" \
  -ExpectedAgents 2
```

所有采集维度（wrapper file check、baseline、CCB start、ping、ps、layout、pane verification、backend route）**全或无**——没有按维度选择性开关的参数。

用户描述中提到"采集脚本的启动命令仍然过长"——虽然当前命令长度主要来自路径长度，但缺少维度选择开关加剧了调试和增量采集的成本。例如：只想重新采集 pane verification 时仍必须跑完整流程，等待 120 秒 timeout。

## 影响

中等——采集脚本的调试效率受限于无法跳过维度，每次调试改动都需全量重跑。

## 修复方向

加 `-SkipDimension` / `-OnlyDimension` 参数，允许选择性禁用/启用采集维度，加速调试循环。
