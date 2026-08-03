---
doc_type: feature-implementation
feature: 2026-07-31-native-windows-public-workflow-validation-matrix
status: done
stage: implementation
---

# native-windows-public-workflow-validation-matrix 实现报告

## 当前理解

本 feature 只建立 Native Windows x64 public workflow validation matrix 的
schema owner、fail-closed 规则和 acceptance 可消费证据。当前未宣称完整 pass；
缺少完整真机 workflow/provider transcript 时，matrix 必须保持 blocked candidate。

## 实现方式

- 新增 `lib/terminal_runtime/windows_herdr_public_workflow_matrix.py`，集中维护 required workflow key set、provider workflow key set、schema 校验、parent admission、blocked skeleton、provider freeze 和 canonical JSON。
- 新增 `test/test_windows_herdr_public_workflow_matrix.py`，覆盖 required key 漂移、非 pass reason、provider summary/detail 一致性、hard gate、blocked skeleton、parent admission、deterministic JSON。
- 归档 evidence artifacts：matrix JSON、public providers freeze、Native Windows transcript、provider transcript、blocked evidence。
- 更新 `docs/ccbd-diagnostics-contract.md`，只说明 matrix/artifact 读取方式，不发布最终支持声明。

## Step 证据

- S1 schema / required keys：`python -m pytest -q test/test_windows_herdr_public_workflow_matrix.py` -> 15 passed。
- S2 parent admission：`python -m pytest -q test/test_windows_herdr_public_workflow_matrix.py -k "parent_admission or blocked_skeleton"` -> 3 passed, 12 deselected。
- S3 workflow/provider rows：目标测试覆盖 required workflows、`mounted` -> `ccb ping all`、`watch` -> `ccb pend --watch <target>`、20 个 public provider x 4 workflow summary/detail 行。
- S4 support candidate rule：目标测试覆盖 all-pass supported candidate 与 Mobile/Config/npm/source/auto-restore/provider 非 pass fail closed。
- S5 transcript plan：已归档 `evidence/native-windows-transcript.md`、`evidence/provider-workflows-transcript.md`、`evidence/blocked-evidence.md` 和 matrix JSON。
- S6 docs contract：CMD-007 passed；`doctor --bundle` 只保留 deprecated/unsupported 语境。
- S7 scope guard：CMD-005 passed；未触碰 publish/push/tag、最终 support claim、provider runtime/recovery authority。

## Gate 证据

- `scope-gate`：passed。
- `dod-runner`：passed，CMD-001..CMD-007 全部 exit 0。
- `evidence-pack`：passed。

## Review-Fix 证据

- REV-001：workflow/provider `pass` 行现在都要求 `host_evidence_ref` 非空；新增对应负测。
- REV-002：`public_providers` 现在必须与 `build_default_provider_manifests(include_optional=True, include_test_doubles=False)` 的当前公开 provider set 完全一致；新增空集/漏项负测。
- REV-003：`support_tier_is_candidate` 必须为 `true`；新增 false 负测。
- REV-004：required field 校验改为显式 missing set，缺字段加 extra field 仍 fail。
- REV-005：`support_projection_allowed` 必须等于 hard gate 派生结果；all-pass 但 allowed=false 会 fail。
- REV-006：parent acceptance artifact refs 不再接受否定语境；新增 `No artifact refs` 负测。
- Nit：`blocked-evidence.md` 已说明 Windows npm install dry-run 顶层 gate 当前使用 `not-run`。
- 验证：`python -m pytest -q test/test_windows_herdr_public_workflow_matrix.py` -> 23 passed；`dod-runner` -> passed。

## Review-Fix Round 2 证据

- REV-007：parent artifact refs 只接受正向 evidence / CMD 语境，`unavailable`、`not available`、`not recorded`、`No CMD-*` 等否定语境均 blocked。
- REV-008：supported gate 现在要求 `baseline_ref`、`release_surface_ref`、`user_surfaces_ref` 非空；新增 root-aware artifact validator 验证 parent refs 和 pass row refs 存在。
- REV-009：provider pass detail row 要求 `pane_ref` 非空。
- REV-010：blocked matrix generator 不再允许 provider 子集，必须匹配当前 public provider catalog。
- 验证：`python -m pytest -q test/test_windows_herdr_public_workflow_matrix.py` -> 32 passed；`dod-runner` -> passed；root-aware matrix artifact validation -> passed。

## Review-Fix Round 3 证据

- OCR medium finding：补齐 root-aware workflow artifact 测试夹具，确保确实命中缺失 workflow artifact。
- OCR medium finding：root-aware refs 使用 `resolve()` 并拒绝脱离 repo root 的路径。
- OCR medium finding：parent artifact ref 负面语境增加 `not passed`、`failed`、`blocked`、`not found` 等 fail-closed 规则及测试。
- 验证：`python -m pytest -q test/test_windows_herdr_public_workflow_matrix.py` -> 36 passed；`dod-runner` -> passed；root-aware matrix artifact validation -> passed。

## Review-Fix Round 4 证据

- 独立复审 blocking：parent admission 改为必须匹配真实 repo evidence 路径或 `CMD-###`，并拒绝 `none`、`absent`、`omitted`、`TBD`、`pending`、`unrecorded` 等负面语境。
- 独立复审 important：root-aware artifact validator 现在校验顶层 `artifacts` map 以及所有 workflow/provider detail rows 的 `artifact_ref` / `host_evidence_ref`，不再只校验 pass rows。
- 独立复审 important：schema validator 现在拒绝未知顶层字段，避免证据契约静默漂移。
- 独立复审 nit：parent admission ready-path 单测改为 `tmp_path` fixture，不再依赖 live `Path.cwd()` 仓库状态。
- 验证：`python -m pytest -q test/test_windows_herdr_public_workflow_matrix.py` -> 49 passed；`python -m pytest -q test/test_windows_herdr_public_workflow_matrix.py -k "artifact or parent_admission or unknown_top_level or provider_catalog_freeze"` -> 26 passed, 23 deselected；root-aware matrix artifact validation -> passed。

## Review-Fix Round 5 证据

- OCR medium finding：root-aware artifact validator 现在对 blocked/beta matrix 中非空 `baseline_ref`、`release_surface_ref`、`user_surfaces_ref` 也做 repo-root 内存在性校验；只有 `support_projection_allowed=true` 时才要求三者全部非空。
- OCR medium finding：parent admission ready-path 单测同时覆盖 repo evidence path 与 `CMD-###` 两种正向 artifact ref 格式。
- 验证：`python -m pytest -q test/test_windows_herdr_public_workflow_matrix.py` -> 51 passed；`python -m pytest -q test/test_windows_herdr_public_workflow_matrix.py -k "artifact or parent_admission or unknown_top_level or provider_catalog_freeze"` -> 28 passed, 23 deselected；root-aware matrix artifact validation -> passed。

## Review-Fix Round 6 证据

- 独立复审 blocking：parent admission 现在对 acceptance 正文中的 repo `evidence/` 路径抽取后执行 repo-root 内存在性校验；不存在或 path escape 不会 admitted。
- `CMD-###` 仍作为 parent acceptance 可引用命令证据格式被接受；repo evidence path 只有文件真实存在才接受。
- 验证：`python -m pytest -q test/test_windows_herdr_public_workflow_matrix.py` -> 52 passed；`python -m pytest -q test/test_windows_herdr_public_workflow_matrix.py -k "parent_admission or artifact"` -> 27 passed, 25 deselected；当前真实 parent admission -> `ready`；root-aware matrix artifact validation -> passed。

## Review-Fix Round 7 证据

- OCR high finding：parent admission 现在一行内只要出现 repo `evidence/` 路径，就必须先校验这些路径全部真实存在；只有没有 repo path 的纯 `CMD-###` 行才按命令证据放行。
- 新增负测覆盖 `Artifact refs: CMD-001 .codestable/features/parent/evidence/missing.json`，防止 CMD token 绕过缺失 repo artifact。
- 验证：`python -m pytest -q test/test_windows_herdr_public_workflow_matrix.py` -> 53 passed；`python -m pytest -q test/test_windows_herdr_public_workflow_matrix.py -k "parent_admission or artifact"` -> 28 passed, 25 deselected；当前真实 parent admission -> `ready`；root-aware matrix artifact validation -> passed。

## Review-Fix Round 8 证据

- OCR medium finding：schema validator 现在校验 `herdr_version` 为非空字符串，并对 workflow/provider detail rows 执行 exact-field 校验，拒绝未知字段和缺失字段。
- OCR medium finding：workflow/provider detail rows 的 `command`、`reason`、`beta_gap`、`residual_risk`、`pane_ref` 等 nullable scalar 现在必须是 `str | None`。
- 新增负测覆盖 workflow row extra field、provider detail missing field、非 string scalar、非 string `herdr_version`。
- 验证：`python -m pytest -q test/test_windows_herdr_public_workflow_matrix.py` -> 57 passed；`python -m pytest -q test/test_windows_herdr_public_workflow_matrix.py -k "schema or unknown or missing_provider or scalar or parent_admission or artifact"` -> 32 passed, 25 deselected；当前真实 parent admission -> `ready`；root-aware matrix artifact validation -> passed。

## Review-Fix Round 9 证据

- OCR medium finding：`baseline_ref`、`release_surface_ref`、`user_surfaces_ref` 顶层字段现在必须是 `str | None`，blocked/beta matrix 不能用 list/dict 等非法类型静默绕过。
- 新增负测覆盖非法 parent ref scalar 类型。
- 验证：`python -m pytest -q test/test_windows_herdr_public_workflow_matrix.py` -> 58 passed；`python -m pytest -q test/test_windows_herdr_public_workflow_matrix.py -k "schema or unknown or scalar or parent_refs or parent_admission or artifact"` -> 33 passed, 25 deselected；当前真实 parent admission -> `ready`；root-aware matrix artifact validation -> passed。

## Review-Fix Round 10 证据

- OCR partial/high finding：root-aware refs 现在拒绝绝对路径，要求 repo-relative path。
- Parent admission 对 `CMD-###` 不再裸放行；只有能在 parent feature 同目录 `evidence/` 下解析到 `cmd-###*` evidence file 时才接受该 command ref。
- 新增负测覆盖 absolute repo ref、bare CMD blocked；新增正测覆盖 CMD ref + matching evidence file admitted。
- 验证：`python -m pytest -q test/test_windows_herdr_public_workflow_matrix.py` -> 60 passed；`python -m pytest -q test/test_windows_herdr_public_workflow_matrix.py -k "schema or unknown or scalar or parent_refs or parent_admission or artifact"` -> 35 passed, 25 deselected；当前真实 parent admission -> `ready`；root-aware matrix artifact validation -> passed。

## Review-Fix Round 11 证据

- OCR medium finding：parent admission 同一行上若同时包含 `CMD-###` 与 repo evidence path，则该行所有 CMD refs 都必须解析到 parent `evidence/cmd-###*` 文件，repo path 不能绕过 CMD evidence 校验。
- 新增负测覆盖有效 repo path + unresolved CMD ref 的混合行 blocked。
- 验证：`python -m pytest -q test/test_windows_herdr_public_workflow_matrix.py` -> 61 passed；`python -m pytest -q test/test_windows_herdr_public_workflow_matrix.py -k "parent_admission or artifact"` -> 31 passed, 30 deselected；当前真实 parent admission -> `ready`；root-aware matrix artifact validation -> passed。

## Review-Fix Round 12 证据

- OCR high finding：repo ref 校验现在显式拒绝 Windows drive absolute refs 与 UNC refs（`C:/...`、`C:\\...`、`//server/...`、`\\\\server\\...`），不依赖当前 host 的 `Path.is_absolute()` 语义。
- 新增参数化负测覆盖 Windows absolute / UNC repo refs。
- 验证：`python -m pytest -q test/test_windows_herdr_public_workflow_matrix.py` -> 65 passed；`python -m pytest -q test/test_windows_herdr_public_workflow_matrix.py -k "absolute or parent_admission or artifact"` -> 35 passed, 30 deselected；当前真实 parent admission -> `ready`；root-aware matrix artifact validation -> passed。

## Review-Fix Round 13 证据

- OCR high finding：repo ref 校验现在拒绝任何 rooted path（`/...`、`\\...`），覆盖 POSIX absolute 与 Windows current-drive-rooted refs。
- 新增参数化负测覆盖 `/tmp/evidence.md` 与 `\\Users\\me\\evidence.md`。
- 验证：`python -m pytest -q test/test_windows_herdr_public_workflow_matrix.py` -> 67 passed；`python -m pytest -q test/test_windows_herdr_public_workflow_matrix.py -k "absolute or parent_admission or artifact"` -> 37 passed, 30 deselected；当前真实 parent admission -> `ready`；root-aware matrix artifact validation -> passed。

## Review-Fix Round 14 证据

- OCR high finding：repo ref 校验现在拒绝任何 Windows drive-qualified 前缀（`^[A-Za-z]:`），包括 `C:tmp/evidence.md` 这类 drive-relative refs。
- 新增参数化负测覆盖 `C:tmp/evidence.md`。
- 验证：`python -m pytest -q test/test_windows_herdr_public_workflow_matrix.py` -> 68 passed；`python -m pytest -q test/test_windows_herdr_public_workflow_matrix.py -k "absolute or parent_admission or artifact"` -> 38 passed, 30 deselected；当前真实 parent admission -> `ready`；root-aware matrix artifact validation -> passed。

## 残留风险

- 当前 matrix 是 blocked candidate evidence，不是真实全量 Native Windows pass transcript。
- `support_projection_allowed=false`，后续 `herdr-supportability-projection` 必须重新校验 matrix，不得把 candidate 字段直接发布为最终支持结论。
