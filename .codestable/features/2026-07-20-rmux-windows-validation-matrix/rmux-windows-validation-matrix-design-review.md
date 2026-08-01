---
doc_type: feature-design-review
feature: 2026-07-20-rmux-windows-validation-matrix
status: passed
review_state: passed
review_reason: ""
reviewer_id: "019f7cca-986c-7ef2-888c-ef4ec0f09013"
reviewed: 2026-07-20
round: 1
---

# rmux-windows-validation-matrix feature design 审查报告

## 1. Scope And Inputs

- Design: `.codestable/features/2026-07-20-rmux-windows-validation-matrix/rmux-windows-validation-matrix-design.md`
- Checklist: `.codestable/features/2026-07-20-rmux-windows-validation-matrix/rmux-windows-validation-matrix-checklist.yaml`
- Intent / brainstorm: none
- Roadmap: `.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-roadmap.md`、`.codestable/roadmap/windows-rmux-native-backend/windows-rmux-native-backend-items.yaml`
- Related docs: roadmap item 15；`rmux-supervision-recovery` child design；existing CI / smoke scripts
- Code facts checked:
  - `.github/workflows/test.yml`
  - `.github/workflows/ccbd-real-platform.yml`
  - `pytest.ini`
  - `scripts/phase6_fake_matrix_smoke.py`
  - `scripts/single_lane_multi_workgroup_smoke.py`
  - `scripts/bootstrap-windows-test-env.ps1`
  - `package.json`

### Independent Review

- Status: completed
- Detection: independent-agent
- Provider / agent: `019f7cca-986c-7ef2-888c-ef4ec0f09013`
- Raw output: 首轮 `changes-requested`，提出 2 个 blocking、3 个 important、1 个 nit、1 个 suggestion；focused closure 后 verdict `passed`
- Merge policy: 主 agent 已核验 roadmap、design/checklist 和关键代码事实；修订后由同一 reviewer 做 focused closure
- Gate effect: 独立 reviewer completed + closure verified；允许定稿 `passed`

## 2. Design Summary

- Goal: 建立 Windows Rmux 自动化与真机验证矩阵、证据 schema 和可重复 runbook，覆盖多 agent、ask、kill、restart、多项目场景。
- Key contracts: matrix case schema 分离 fake / provider_blackbox / windows_true_host / manual_transcript；true-host 必须满足 `host_kind=native_windows`、`control_plane=ccbd`、`probe_bypass=false`；report 同时输出 `selection_scope`、`selected_cases_status`、`full_matrix_status`。
- Steps: 8 个步骤，覆盖 schema/manifest、report builder、fake lane、Windows true-host runbook runner、provider blackbox lane、CI integration、cleanup/residue evidence、scope guard。
- Checks: 11 项检查，覆盖核心 case、lane 隔离、true-host 防伪、transcript schema/redaction、provider/system failure 分类、upstream recovery gate、subset/full pass、scope guard。
- Baseline / validation: YAML 校验、manifest/report/transcript parser tests、fake lane runner、manual transcript import、existing lifecycle/provider blackbox baseline、PowerShell true-host runbook、scope guard。

## 3. Findings

### blocking

none

### important

none

### nit

none

### suggestion

none

### learning

- `phase6_fake_matrix_smoke.py` 可复用矩阵聚合思路，但不能直接扩展为 Rmux 矩阵；本 design 已选择新建专项脚本，避免 phase6 语义外泄。
- Windows true-host 证据必须显式记录 host/control-plane/probe-bypass/backend-selection，否则 WSL、probe、fake lane 很容易被误归类为 native Windows pass。

### praise

- design 对 lane 分层和证据边界处理清楚，明确 WSL/probe/fake 不能替代 native true-host。
- subset CI 与 full matrix status 已拆开，能让默认 CI 验证可自动化子集，同时不伪造完整交付可信度。

## 4. User Review Focus

- 用户需要重点拍板：full matrix pass 需要 native Windows true-host transcript；CI subset pass 不是完整 Windows Rmux 交付通过。
- implement 需要重点遵守：PowerShell runner 和 markdown runbook 必须共享 transcript sidecar schema；provider auth failure 与 Rmux/ccbd system failure 必须分开。
- code review / QA / acceptance 需要重点复核：true-host 防伪字段、scope guard forbidden path set、dirty transcript redaction fixture、upstream recovery pending gate 是否按契约实现。

## 5. Evidence Confidence Ledger

| Check | Verdict | Evidence Class | Basis | Follow-up |
|---|---|---|---|---|
| Acceptance Coverage Matrix | pass | E | design §3.1 / §3.3 覆盖 AC-001 至 AC-009 | none |
| DoD Contract | pass | E | design §3.4 覆盖 Design / Implementation / Review / QA / Acceptance DoD 与 validation commands | none |
| Steps and checks traceability | pass | E | checklist steps/checks 对应 design §2.4、§3.1、§3.4；YAML 校验通过 | none |
| Roadmap contract compliance | pass | E | roadmap item `rmux-windows-validation-matrix` 要求 Windows 原生验证矩阵和 runbook；design 明确 post-milestone 与 full-chain smoke 边界 | none |
| Module interface design | pass | C | existing CI、pytest markers、phase6 matrix script、multi-workgroup smoke、Windows bootstrap 与 package facts 已核对；design 新建专项 validation seam | implementation 需保持 fake/provider/true-host/manual lane 隔离 |
| Validation and artifacts | pass | E | checklist `dod.commands` 覆盖 new/new-or-existing tests、PowerShell runbook、manual transcript import、scope guard | none |

Summary: E=5, C=1, H=0, H-only core checks=none。

## 6. Residual Risk

- 本 design review 未运行 native Windows/Rmux 真机命令；true-host pass 仍必须由后续 implementation/QA/acceptance 的 transcript 证明。
- `rmux-supervision-recovery` 上游仍处于 draft design 阶段；本 design 已规定 recovery rows 在上游未 ready 时不得计 full pass。

## 7. Verdict

- Status: passed
- Next: 返回 `cs-epic` child design batch loop，继续下一个 epic child；本 child design 保持 `draft`，等待所有 child design-review 通过后由 epic 统一确认。

## 8. Focused Closure

- Closed findings: FDR-001、FDR-002、FDR-003、FDR-004、FDR-005、FDR-006、FDR-007
- Attributed delta: `.codestable/features/2026-07-20-rmux-windows-validation-matrix/rmux-windows-validation-matrix-design.md`、`.codestable/features/2026-07-20-rmux-windows-validation-matrix/rmux-windows-validation-matrix-checklist.yaml`
- Verification: reviewer `019f7cca-986c-7ef2-888c-ef4ec0f09013` focused closure verdict `passed`；checklist YAML 与 roadmap items YAML 校验通过
- Classification: 修订只关闭 reviewer 提出的 schema、runbook artifact、upstream gate、scope guard、subset/full status、classification wording 和 redaction fixture 契约问题；未修改生产代码，也未改变 feature 范围或 roadmap 边界
