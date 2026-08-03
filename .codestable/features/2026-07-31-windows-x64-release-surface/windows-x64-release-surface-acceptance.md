---
doc_type: feature-acceptance
feature: 2026-07-31-windows-x64-release-surface
status: passed
audit_state: not-started
audit_reason: ""
auditor_id: ""
acceptance_authorization_ref: "approval-report.md#goal-acceptance"
accepted: 2026-08-03
round: 1
---

# windows-x64-release-surface 验收报告

> 阶段：阶段 3（验收闭环）  
> 验收日期：2026-08-03  
> 关联方案 doc：`.codestable/features/2026-07-31-windows-x64-release-surface/windows-x64-release-surface-design.md`

## 1. 接口契约核对

- [x] `WindowsX64ReleaseSurfaceProjection`：`lib/terminal_runtime/windows_x64_release_surface.py` 与 packaged JSON 暴露 schema、host_gate、artifact/checksum、install/update/doctor 字段；strict loader 对 malformed/stale payload fail closed。
- [x] cross-language seam：`bin/ccb-npm-install.js`、`install.ps1`、`cmd_update()`、doctor 都消费同一 projection；Node/PowerShell 只执行通用 host_gate rule，不复制 release route 矩阵。
- [x] artifact / executable contract：projection 包含 `archive_name`、`extract_dir`、`checksum_entry`、`windows_executable_entry`、`windows_bin_entries`；npm runner tests 覆盖 `ccb/ask/autonew/ctx-transfer`。
- [x] source/dev install boundary：`source_install_allowed=True` 与 `source_install_entry=install_ps1` 保留 source/dev 入口；release/npm/update route 当前仍 diagnostic-only。

## 2. 行为与决策核对

- [x] 单一 projection owner 已落地，Python/Node/PowerShell/doctor 不各自解释 Windows x64、WOW64、artifact 或 helper route。
- [x] `package.json.os` 加入 `win32`，`package.json.cpu` 保持 envelope `["x64","arm64"]`，Windows x64-only 由 projection host gate fail closed 控制。
- [x] Windows update 不再落到 Unix installer；`update_entry=diagnostic_only` 不下载、不写 install prefix；`install_ps1` 分支有 zip/tar 解压、`SHA256SUMS` 校验、rollback 和 no-Unix-installer tests。
- [x] doctor/docs 输出 `windows_x64_release_surface` rows，旧 `doctor --bundle` 只保留 deprecated/unsupported 语境。
- [x] 明确不做已核对：未 publish、push、tag、promotion；未声明 Windows x64 final supported；未改 provider completion / recovery owner。

## 3. 验收场景核对

- [x] AC-001/002/010：projection available/blocked、Windows arm64/WOW64/ia32 fail closed、dependency/baseline admission 由 CMD-003/CMD-009/CMD-010 覆盖。
- [x] AC-003：npm package metadata/payload、code-level Windows route、all bin mapping 由 CMD-003/CMD-006 与 CMD-008 transcript 覆盖。
- [x] AC-004：Windows update projection route、diagnostic-only、checksum mismatch、rollback 和 no Unix installer 由 CMD-004/CMD-012 覆盖。
- [x] AC-005/006：managed Python/native helper/status rows 和 doctor/docs contract 由 CMD-004/CMD-013、live `ccb doctor` 与 `doctor --output` transcript 覆盖。
- [x] AC-007：Rmux / non-Windows regression 由 CMD-005 覆盖。
- [x] AC-008：scope guard CMD-007 覆盖，无 publish/promotion/support/completion 越界。
- [x] AC-009：CMD-008 以 Native Windows diagnostic/blocked transcript 覆盖；不等同真实 install transcript。
- [x] AC-011：CMD-011 以 blocked evidence + fake rollback unit 覆盖；不等同真实 uninstall/PATH/skills cleanup transcript。
- [x] AC-012：source/dev install preservation 由 tests、PowerShell projection diagnostic 和 docs 口径覆盖。
- [x] Review/QA focus：subagent review findings 已关闭；QA runner 的 live doctor blocker 已通过隔离临时目录 smoke 关闭；OCR timeout 与 destructive cleanup 保留为 residual risk。

## 4. 术语一致性

- `release-surface projection` / `windows_x64_release_surface` / `host_gate` / `release_install_entry` / `source_install_allowed` / `update_entry` 在代码、tests、doctor/docs 和报告中一致。
- 防冲突：`win32` 仅作为 Windows OS 名称；未把 Windows x64 发布面声明为 supported。

## 5. 领域影响盘点

- 新术语候选：`WindowsX64ReleaseSurfaceProjection`、`windows_x64_release_surface`、`package.json.cpu envelope`。建议后续用 `cs-domain` 或 `cs-keep` 沉淀；本 acceptance 不直接写 ADR/CONTEXT。
- 结构性选择候选：单一 packaged JSON projection 作为 Python/Node/PowerShell seam。长期保留时建议沉淀 ADR。
- 流程级约束候选：Goal release surface 只允许 diagnostic/blocked evidence，不能提升为 support tier。

## 6. requirement delta / clarification 回写

- Requirement: `native-windows-ccb-via-herdr`。
- 本 feature 只实现 roadmap 中既有 release-surface child 的发布面 gate 与 diagnostic 路由，不改变 owner-level capability boundary；无需 requirement delta。
- 当前 blocked/default projection 不新增 supported 能力声明。

## 7. roadmap 回写

- [x] `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml` 中 `windows-x64-release-surface` 已从 `in-progress` 改为 `done`。
- [x] `.codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-roadmap.md` 子 feature 清单中对应状态已改为 `accepted`。
- [x] `python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml"`：passed。

## 8. attention.md 候选盘点

- 候选 1：Windows 下 CodeStable/DoD runner 需设置 `PYTHONDONTWRITEBYTECODE=1` 与 `PYTHONUTF8=1`；前者已在 attention.md，后者可追加。
- 候选 2：Windows Node/npm 验证应通过 `cmd /d /s /c npm.cmd ...` 或平台安全 wrapper；避免直接 `execFileSync("npm")`。
- 不在 acceptance 内直接写 attention；后续可用 `cs-note` 归档。

## 9. 遗留

- CMD-008 不是真实 `install.ps1 install` transcript；它是 Native Windows diagnostic/blocked transcript。
- CMD-011 不是真实 uninstall/PATH/skills cleanup transcript；真实动作需要单独危险操作确认。
- OCR scoped rerun timeout；review/QA 已保留 residual risk。
- 当前 projection `failure_reason=release-artifact-missing`，后续 feature 仍不得声明 release route ready 或 final supported。

## 10. 最终审计

- 验证证据来源：`.codestable/features/2026-07-31-windows-x64-release-surface/windows-x64-release-surface-qa.md`。
- Evidence sources：evidence pack、gate results、DoD results、CMD-008/CMD-011 evidence files。
- 聚合命令：
  - checklist YAML：passed。
  - roadmap items YAML：passed。
  - CMD-003：21 passed。
  - CMD-004：64 passed。
  - CMD-005：5 passed。
  - CMD-009/CMD-010/CMD-012 grouped：7 passed。
  - CMD-006/CMD-007/CMD-013：passed。
  - `git diff --check` scoped feature files：passed with CRLF warnings only。
- 场景复核：re-verified 12 / trust-prior-verify 2（真实 install/uninstall cleanup 仅 blocked evidence）。
- 交付物复核：代码、projection JSON、Node/PowerShell adapters、update branch、doctor/docs、README、tests、evidence、review、QA、roadmap writeback 均存在。
- 完整工作区复核：feature 相关 tracked/untracked 文件已纳入；无 staged diff。`.codestable/gates/roadmap-goal-gates.yaml`、`.codestable/reference/agent-conventions.md`、`笔记.md` 属本轮外 baseline。
- diff 清洁度：scope guard、docs guard、`git diff --check` 通过；无 publish/promotion/support claim。
- 知识沉淀出口：attention 候选已登记；projection seam 建议后续沉淀到 domain/ADR。
- 结论：通过。Goal driver 可进入 feature accepted 状态回写与 scoped commit 授权核验。
