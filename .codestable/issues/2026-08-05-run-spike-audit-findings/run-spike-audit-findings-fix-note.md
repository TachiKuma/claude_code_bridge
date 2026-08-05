---
doc_type: issue-fix-note
issue: run-spike-audit-findings
status: fixed
source_audit: 2026-08-05-herdr-ccb-recent-changes
fixed_findings:
  - "01"
  - "06"
  - "07"
not_fixed_findings:
  - "05"
---

# run_spike.ps1 审计问题修复记录

## 根因

`run_spike.ps1` 的 pane verification 先按 CCB namespace session 采集 snapshot，但 pane read 仍使用 wrapper 默认 session，导致 session 分歧时对不存在的 pane id 读取内容，pane content capture 证据不可信。

同一代码段还存在明显缩进漂移，后续维护者容易误判 `snapshotPayload`、`snapshot` 和 capture 循环的实际作用域。

采集脚本此前只能全量运行，调试单个维度时仍要启动完整链路，采集循环过重；pane capture 默认只读 3 行，深度偏浅。

## 改动

- 在 `run_spike.ps1` 增加 `-OnlyDimension`、`-SkipDimension` 和 `-PaneCaptureLines`，默认仍启用全部采集维度。
- 为 pane/backend 等维度保留必要隐式依赖，并在 `collection-dimensions.json`、`summary.json`、`report.md` 中记录 enabled/executed/skipped 维度。
- 部分采集时只为实际生成的证据写 summary ref，避免未采集维度留下误导性路径。
- 部分采集分类改为 `partial-dimension-complete` / `partial-dimension-failed`，并写出 `classification_scope`、`command_failure_count` 和 `failed_commands`。
- pane snapshot 候选必须命令成功、未 timeout、stdout 非空、JSON 可解析且包含 snapshot；CCB namespace snapshot 不可用时 fallback 到 wrapper session snapshot，并记录 fallback 原因。
- pane capture 命令结果纳入 `$commands` 和失败统计，避免 pane read 全失败时误报局部采集完成。
- `ccb8-ping-all` 总是生成 canonical 结果；失败统计忽略中间 retry attempt，只按最终 canonical 结果判断。
- 将 pane capture session 改为跟随实际 snapshot source：CCB namespace snapshot 使用 `$ccbHerdrSession`，fallback snapshot 使用 `$effectiveHerdrSession`。
- 重排 pane verification 段缩进，保持 JSON parse、snapshot 选择和 pane capture 的作用域一致。
- 将 pane capture 默认深度从 3 行提升到 20 行，并允许调用方通过 `-PaneCaptureLines` 调整。

## 验证

- `powershell -NoProfile -ExecutionPolicy Bypass -File ".../run_spike.ps1" -SelfTest` 通过。
- PowerShell AST parse 检查通过：`parse: ok`。
- `-OnlyDimension wrapper-file-check -AllowNonHerdrUi` 冒烟通过，仅执行 `ccb8-wrapper-file-check`，summary 为 `partial-dimension-complete`，`process_samples_ref` 为空，`executed_dimensions=wrapper-file-check`，`command_failure_count=0`。
- 构造缺失 `ccb8.ps1` 的 wrapper-only 失败路径通过，summary 为 `partial-dimension-failed`，`command_failure_count=1`，`failed_commands[0].name=ccb8-wrapper-file-check`。
- SelfTest 覆盖 ping retry canonical 失败统计规则，以及单个失败命令的数组计数语义。

## 遗留风险

- 未执行真实 Herdr UI 全链路采集；需要在 Herdr UI 环境中用默认全量维度跑一次确认 pane capture 真实内容。
- finding 05 需要跨 `run_spike.ps1` 与 `ccb8.ps1` 抽共享模块；本轮按用户要求只处理 `run_spike.ps1`，未改 `ccb8.ps1`。
