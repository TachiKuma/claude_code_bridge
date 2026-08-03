---
doc_type: feature-review
feature: 2026-07-31-windows-x64-release-surface
status: passed
reviewer: subagent
reviewed: 2026-08-03
round: 1
lane_a_state: completed
lane_a_ref: "019fc632-8d93-7b23-872e-b1c9a402ee98"
lane_a_reason: "独立 subagent review 已完成；结果经本地逐项核验并关闭，agent 已关闭。"
lane_b_state: unavailable
lane_b_ref: "a64a2552-666a-4edb-8c35-49cf53551031"
lane_b_reason: "OCR CLI 可用且 scoped preview 成功；但没有稳定 completed 结果可合并，历史 OCR 为 partial，当前 scoped rerun 被宿主 240s timeout 终止，因此不作为 reviewer 放行锚点。"
---

# windows-x64-release-surface 代码审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-31-windows-x64-release-surface/windows-x64-release-surface-design.md`
- Checklist: `.codestable/features/2026-07-31-windows-x64-release-surface/windows-x64-release-surface-checklist.yaml`
- Evidence pack: `.codestable/features/2026-07-31-windows-x64-release-surface/windows-x64-release-surface-evidence-pack.md`
- Gate results: `.codestable/features/2026-07-31-windows-x64-release-surface/windows-x64-release-surface-gate-results.json`
- DoD results: `.codestable/features/2026-07-31-windows-x64-release-surface/windows-x64-release-surface-dod-results.json`
- Implementation evidence: `.codestable/features/2026-07-31-windows-x64-release-surface/windows-x64-release-surface-implementation.md`
- Diff basis: 当前 unstaged/untracked feature diff；staged diff 为空。
- Review mode: initial，包含独立 reviewer findings 修复后的本地 closure 核验。
- Baseline dirty files: `.codestable/gates/roadmap-goal-gates.yaml`、`.codestable/reference/agent-conventions.md`、`笔记.md` 等为本轮外既有 dirty baseline，未纳入 verdict。

### Independent Review

- Detection: subagent 可用且已返回；`ocr` CLI 可用，`ocr review --preview` scoped 到 17 个本轮代码/测试文件成功。
- 环节 A 独立隔离 Task agent: independent-agent completed，ref `019fc632-8d93-7b23-872e-b1c9a402ee98`。
- 环节 B OCR CLI: unavailable completed result。历史 OCR 为 partial；当前 scoped rerun 使用 `.codestable/**` 与无关笔记排除后仍被宿主 240s timeout 终止。
- OCR severity mapping: High->blocking/important, Medium->nit/suggestion, Low->discarded。
- Merge policy: subagent findings 已逐条用当前代码、测试和 gate 结果核验；OCR 不作为 completed reviewer 合并。
- Gate effect: reviewer 放行锚点为 `subagent`；OCR 超时作为 residual risk 和 QA focus。

## 2. Diff Summary

- 新增：`lib/terminal_runtime/windows_x64_release_surface.py`、`lib/terminal_runtime/windows_x64_release_surface_projection.json`、8 个 focused test 文件、feature evidence/gate/implementation 产物。
- 修改：`bin/ccb-npm-install.js`、`install.ps1`、`lib/cli/management_runtime/commands_runtime/update.py`、doctor service/render、README/docs、`package.json`、checklist/design。
- 删除：none。
- 未跟踪 / staged：新增 feature 证据与新增测试文件未跟踪；staged diff 为空。
- 风险热点：跨 Python/Node/PowerShell 的 fail-closed schema/host gate、Windows release artifact checksum、update rollback、npm Windows executable entry、source/dev install 不阻断、doctor/docs 只展示 diagnostic。

## 3. Adversarial Pass

- 假设的生产 bug：Windows x64 route 一旦打开，会绕过 projection 契约安装错误 artifact，或把 blocked diagnostic 误展示为 supported。
- 主动攻击过的反例：schema 缺字段、host_gate comparison rule 缺 `value`、unknown/invalid PowerShell rule、WOW64 env、Windows update checksum mismatch、zip 路径穿越、fake staged `install.ps1` failure rollback、npm runner 多 bin 映射、docs/support claim scope guard、manual cleanup evidence 假阳性。
- 结果：原 subagent blocking 已修复并由 CMD-003/CMD-004/CMD-012/CMD-013 覆盖；真实 uninstall/PATH/skills cleanup 未执行，保留为 residual risk。

## 4. Findings

### blocking

- none

### important

- none

### nit

- none

### suggestion

- none

### learning

- `package.json.os=win32` 只允许 npm 进入 postinstall；Windows x64 是否可走 release route 仍必须由 projection、host_gate、artifact/checksum 和后续 supportability feature 决定。

### praise

- 单一 projection owner 让 Python、Node、PowerShell 的入口共享同一组机器字段，避免各入口复制 Windows x64 / WOW64 / artifact route 判断。

## 5. Test And QA Focus

- QA 必须重点复核：Native Windows x64 真机 `npm install` dry-run、`install.ps1 install/uninstall`、`ccb update` failure rollback、`ccb doctor --output` 是否显示同一 projection，且不声明 final supported / publish / promotion。
- Evidence pack residual risks / gate warnings：CMD-011 只有 blocked evidence 和 fake rollback unit；未执行真实 `install.ps1 uninstall`、用户 PATH cleanup 或 skills cleanup。
- 建议新增或加强的测试：如果后续打开 `release_install_entry="npm"` 或 `update_entry="install_ps1"` 的真实 artifact route，应补真实 fixture 覆盖 runtime Python entry 与 release `SHA256SUMS` ref。
- 不能靠 review 完全确认的点：OCR 未完成当前 scoped rerun；Markdown README/docs 被 OCR 标为 unsupported，但已有 docs contract guard 和 DoD command 覆盖。

## 6. Residual Risk

- CMD-011 缺真实 cleanup transcript。acceptance 不能把 blocked evidence 当成真实卸载/PATH/skills 清理通过，只能作为未获危险操作确认时的阻断证据。
- OCR 行级扫描未完成当前 scoped rerun；本报告已用 subagent + 本地核验覆盖主要风险，但 QA 仍应重点看 `update.py` 与 `bin/ccb-npm-install.js` 的 Windows route 错误路径。

## 7. Verdict

- Status: passed
- Next: 这是 Goal feature，通过后进入 QA 阶段；不要执行 publish、push、tag、真实 uninstall/PATH cleanup，除非 owner 另行明确确认。

## 8. Focused Closure（无则写 none）

- Closed findings: subagent blocking 1（Windows update 缺 checksum）已由 `update.py` 的 `SHA256SUMS` 下载/校验与 CMD-012 checksum mismatch test 关闭；blocking 2（npm Windows readiness 走 Unix entry）已由 projection `windows_bin_entries`、zip extraction helper 与 runner/readiness tests 关闭；blocking 3（packaged projection baseline mismatch 假阳性）已由当前 canonical default blocked projection `baseline_version_status=v8.5.2` / `failure_reason=release-artifact-missing` 与 freshness test 关闭。
- Attributed delta: `lib/cli/management_runtime/commands_runtime/update.py`、`bin/ccb-npm-install.js`、`lib/terminal_runtime/windows_x64_release_surface.py`、`install.ps1`、相关 focused tests 和 evidence pack residual risk。
- Targeted verification: CMD-001/CMD-002/CMD-003/CMD-004/CMD-005/CMD-006/CMD-007/CMD-009/CMD-010/CMD-012/CMD-013 全部通过；scope-gate 与 evidence-pack 重新通过。
- Classification: 该 closure 包含生产行为修复，因此不按窄义 focused-closure 跳过独立审查；本报告使用已完成 subagent reviewer 作为完整 review gate 锚点。
