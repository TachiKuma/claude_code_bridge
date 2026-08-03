---
doc_type: feature-implementation
feature: 2026-07-31-windows-x64-release-surface
status: implementing
implemented: 2026-08-03
---

# windows-x64-release-surface implementation report

## 第一性原则 pre-pass

- 外部行为：`npm install`、`install.ps1`、`ccb update`、`ccb doctor` 后续都将读取同一个 Windows x64 release-surface projection；当前 S1 先建立 Python loader 和 packaged JSON 的稳定 blocked/default 记录。
- 不可破约束：不把 Windows x64 发布面宣称为 supported；不执行 publish、push、tag、promotion；不把 Node/PowerShell/update/doctor 各自写成独立平台矩阵。
- 最小充分改动：新增 `lib/terminal_runtime/windows_x64_release_surface.py`、`windows_x64_release_surface_projection.json` 和 focused tests；真实仓库 projection 仍为 blocked/default。
- 必须不写：S1 不接入 `bin/ccb-npm-install.js`、`install.ps1`、`cmd_update()` 或 doctor render；这些挂载点按后续 S6/S8/S9/S10 顺序处理。

## 基线预检

- `python ".codestable/tools/validate-yaml.py" --file ".codestable/features/2026-07-31-windows-x64-release-surface/windows-x64-release-surface-checklist.yaml" --yaml-only`：passed。
- `python ".codestable/tools/validate-yaml.py" --file ".codestable/roadmap/windows-native-herdr-ccb/windows-native-herdr-ccb-items.yaml"`：passed。
- `codestable-workflow-next.py feature --feature ".codestable/features/2026-07-31-windows-x64-release-surface" --require-implementation-ready --json`：passed，两个 implementation dependencies 均为 `done`。

## 按步骤改动与证据

### S1 projection schema and strict loader

- 退出信号：fake baseline gate / user-surface parity / artifact / helper / python probe 下，`load_windows_x64_release_surface_projection(root, host_evidence)` 能稳定给出 `available | degraded | blocked`；缺 required field、非法 enum、stale/malformed JSON 都 fail closed。
- 改动：
  - `lib/terminal_runtime/windows_x64_release_surface.py`：新增 `WindowsX64ReleaseSurfaceProjection`、host evidence/gate TypedDict、strict schema 校验、default blocked projection、canonical JSON 输出与 `load_windows_x64_release_surface_projection()`。
  - `lib/terminal_runtime/windows_x64_release_surface_projection.json`：新增当前仓库 packaged projection；状态保持 `default_blocked`，`windows_npm_enabled=false`，`release_install_entry=diagnostic_only`，`source_install_allowed=true`。
  - `test/test_windows_x64_release_surface.py`：新增 focused tests，覆盖 missing packaged JSON、fake admitted packaged projection、host gate first failure、malformed JSON、stale schema。
- TDD 证据：
  - RED：`python -m pytest -q test/test_windows_x64_release_surface.py`，失败为 `ModuleNotFoundError: No module named 'terminal_runtime.windows_x64_release_surface'`。
  - GREEN/VERIFY：`python -m pytest -q test/test_windows_x64_release_surface.py`：5 passed。
- 边界：
  - 当前真实 packaged JSON 不打开 Windows npm/release route。
  - host gate evaluator 先以 Python loader 内部能力落地；Node/PowerShell adapter 仍留给 S2/S6/S8。
- 清洁度：
  - 本步未新增调试输出、临时 TODO/FIXME、注释掉代码或 dead import。

## 当前边界

### S2 host gate evaluator and cross-language seam

- 退出信号：Node 与 PowerShell fixture 能读取同一 JSON、只采集事实字段、只执行 `projection.host_gate.rules` 的 all-pass / first-failure 通用布尔求值，且不会复制 Windows x64 / WOW64 / helper / artifact 路由矩阵。
- 改动：
  - `bin/ccb-npm-install.js`：新增并导出 `readWindowsX64ReleaseSurfaceProjection()`、`collectWindowsX64ReleaseHostEvidence()`、`evaluateWindowsX64ReleaseHostGate()`；当前安装主流程未接入，避免 S2 越界改变 postinstall 行为。
  - `install.ps1`：新增 `Get-WindowsX64ReleaseSurfaceProjection`、`Test-WindowsX64ReleaseHostGate`、value present / normalize helpers；当前 `Install-Native` 未接入，保留给 S8。
  - `test/test_windows_x64_release_surface.py`：新增 Node adapter all-pass / first-failure tests 与 PowerShell helper 静态契约断言。
- TDD 证据：
  - RED：`python -m pytest -q test/test_windows_x64_release_surface.py`，S2 新增 3 个测试失败；Node 失败为 missing exported functions，PowerShell 失败为 helper 函数不存在。
  - GREEN/VERIFY：`python -m pytest -q test/test_windows_x64_release_surface.py`：8 passed。
- 边界：
  - Node / PowerShell 只读取 packaged JSON、采集事实字段并执行通用 op：`equals`、`in`、`not_equals`、`is_false`、`exists`。
  - 不在 S2 改 `artifactForHost()`，不引入 Windows artifact route，也不启用 npm Windows postinstall。
- 清洁度：
  - 本步未新增调试输出、临时 TODO/FIXME、注释掉代码或 dead import。

## 当前边界

### S3 canonical packaged JSON freshness

- 退出信号：提交/打包的 `windows_x64_release_surface_projection.json` 与 builder 在相同 repo/default-blocked 输入下的 canonical JSON 一致；`npm pack --dry-run` 只作为文件入包证明。
- 改动：
  - `lib/terminal_runtime/windows_x64_release_surface.py`：新增 `assert_windows_x64_release_surface_projection_fresh(root)`，按 canonical JSON 比较当前 packaged payload 与 default-blocked builder 输出。
  - `test/test_windows_x64_release_surface.py`：新增 freshness pass test 与 stale payload rejection test。
- TDD 证据：
  - RED：`python -m pytest -q test/test_windows_x64_release_surface.py`，失败为 `ImportError: cannot import name 'assert_windows_x64_release_surface_projection_fresh'`。
  - GREEN/VERIFY：`python -m pytest -q test/test_windows_x64_release_surface.py`：10 passed。
- 边界：
  - freshness gate 当前只证明 default-blocked builder 输出一致；后续 admitted repo-evidence builder 仍由 S4/S6 的 admission tests 扩展，不在 S3 预写。
- 清洁度：
  - 本步未新增调试输出、临时 TODO/FIXME、注释掉代码或 dead import。

## 当前边界

### S4 dependency and baseline admission

- 退出信号：parent items status 均为 done、parent acceptance frontmatter 均为 `doc_type=feature-acceptance` 且 `status=passed`、baseline/user-surface evidence refs 存在时才允许 available/degraded release route；当前 upstream 仍 in-progress 时最高只能生成 strict schema、host gate、blocked/default projection、diagnostics wiring 和回归保护。
- 改动：
  - `lib/terminal_runtime/windows_x64_release_surface.py`：新增 `windows_x64_release_surface_dependency_admission(root)` 与 `windows_x64_release_surface_baseline_version_admission(root)`。
  - `test/test_windows_x64_release_surface_dependency_admission.py`：新增 parent item/acceptance/evidence refs 机械核验与 missing acceptance blocked fixture。
  - `test/test_windows_x64_release_surface_baseline_version.py`：新增当前 `VERSION`/`package.json` strict 8.5.2 gate 与 mismatch blocked fixture。
- TDD 证据：
  - RED：`python -m pytest -q test/test_windows_x64_release_surface_dependency_admission.py test/test_windows_x64_release_surface_baseline_version.py`，失败为两个 admission 函数无法导入。
  - GREEN/VERIFY：`python -m pytest -q test/test_windows_x64_release_surface_dependency_admission.py test/test_windows_x64_release_surface_baseline_version.py`：4 passed。
- 当前事实：
  - `VERSION`：`8.5.2`。
  - `package.json.version`：`8.5.2`。
  - parent item `windows-x64-v852-baseline-gate`：`done`，acceptance passed，evidence ref `evidence/platform-gate-summary.json` 存在。
  - parent item `herdr-user-surfaces-parity`：`done`，acceptance passed，evidence ref `evidence/cmd-008-native-windows-surface-transcript.md` 存在。
- 清洁度：
  - 本步未新增调试输出、临时 TODO/FIXME、注释掉代码或 dead import。

## 当前边界

### S5 package metadata and payload

- 退出信号：npm 能进入 Windows postinstall；projection JSON 出现在 npm pack payload；`package.json.cpu` 未误伤 macOS arm64，且该 roadmap refinement 仍等待 epic owner 统一确认承接。
- 改动：
  - `package.json`：`os` 新增 `win32`，`cpu` 保持 `["x64", "arm64"]`，`files` 新增 `lib/terminal_runtime/windows_x64_release_surface_projection.json`。
  - `test/test_windows_x64_release_surface.py`：新增 package metadata focused test。
- TDD 证据：
  - RED：`python -m pytest -q test/test_windows_x64_release_surface.py -k package_metadata`，失败为 `win32` 不在 `package.json.os`。
  - GREEN/VERIFY：`python -m pytest -q test/test_windows_x64_release_surface.py -k package_metadata`：1 passed, 10 deselected。
- Package payload 证据：
  - approved CMD-006 原命令 `node -e "... execFileSync('npm', ...)"`：failed，当前 Windows/Node v24 环境报 `spawnSync npm ENOENT`。
  - 等价真实 runner：`npm.cmd pack --dry-run --json`：exit 0，输出 files 包含 `lib/terminal_runtime/windows_x64_release_surface_projection.json`。
- 边界：
  - `package.json.cpu` 未改成只含 `x64`，避免误伤 macOS arm64。
  - S5 未修改 `artifactForHost()` 或 postinstall 下载逻辑；Windows route 仍由 S6 host gate 接管。
- 清洁度：
  - 本步未新增调试输出、临时 TODO/FIXME、注释掉代码或 dead import。

## 当前边界

### S6 Node postinstall host gate

- 退出信号：fake admitted upstream + strict v8.5.2 fixture 下 native Windows x64 可通过 npm install dry-run release route；当前真实 repo/upstream 未 admitted 时只能进入 postinstall diagnostic 或 blocked/default projection；Windows arm64/WOW64 不能误装；Windows ia32 至少有 projection / adapter unit 的 blocked diagnostic。
- 改动：
  - `bin/ccb-npm-install.js`：`artifactForHost()` 在 `process.platform === "win32"` 时进入 projection route；新增 `artifactForWindowsX64ReleaseSurface()`，先读取 packaged JSON、执行 host gate，再根据 `windows_npm_enabled` 与 `release_install_entry` fail closed 或返回 artifact route。
  - `test/test_windows_x64_release_surface.py`：新增 fake admitted Windows x64 route test 和当前 default projection blocked diagnostic test。
- TDD 证据：
  - RED：`python -m pytest -q test/test_windows_x64_release_surface.py -k "postinstall"`，新增 S6 测试失败为 `artifactForWindowsX64ReleaseSurface is not a function`。
  - GREEN/VERIFY：`python -m pytest -q test/test_windows_x64_release_surface.py -k "postinstall"`：3 passed, 10 deselected。
- 回归证据：
  - `python -m pytest -q test/test_install_release_entrypoints.py`：2 failed，失败均为当前 Windows 环境找不到 `bash`，未进入本次 JS release-surface diff；记录为既有环境基线缺口。
- 边界：
  - Linux/macOS artifact matrix 保持原逻辑。
  - Windows current packaged projection 仍为 blocked/default；不会下载 release artifact。
- 清洁度：
  - 本步未新增调试输出、临时 TODO/FIXME、注释掉代码或 dead import。

## 当前边界

### S7 npm runner executable contract

- 退出信号：枚举 `package.json.bin` 的全部 key（当前为 `ccb`、`ask`、`autonew`、`ctx-transfer`），断言 `projection.windows_bin_entries` 覆盖每个 bin，并用 fake staged root / stub spawn 验证 runner 对每个 command 都使用 projection 映射；`node bin/ccb.js --print-version` 只是 smoke 的一个代表用例，不能替代其它 bin。
- 改动：
  - `bin/ccb-npm-install.js`：新增并导出 `executablePathForArtifact(info, command, base)`；Windows artifact 使用 `windows_bin_entries`，缺 command entry 直接 fail closed。
  - `test/test_windows_x64_release_surface.py`：新增 all public bin mapping test 与 missing entry blocked test。
- TDD 证据：
  - RED：`python -m pytest -q test/test_windows_x64_release_surface.py -k "runner"`，失败为 `executablePathForArtifact is not a function`。
  - GREEN/VERIFY：`python -m pytest -q test/test_windows_x64_release_surface.py -k "runner"`：2 passed, 13 deselected。
- 边界：
  - 非 Windows artifact path 保持旧的 `ccb` / `bin/<command>` 规则。
  - S7 只证明 runner path contract；不执行真实 release artifact。
- 清洁度：
  - 本步未新增调试输出、临时 TODO/FIXME、注释掉代码或 dead import。

## 当前边界

下一步是 S8：让 `install.ps1` 消费 projection，但继续保留 source/dev checkout install 路径。

## 当前边界

### S8 PowerShell source install adapter

- 退出信号：当前 upstream 未 admitted 时，release route 显示 blocked/default projection；既有 `install.ps1 install` source/dev 路径仍可按 `source_install_allowed=true` 继续执行并显示可行动诊断，除非存在单独 owner 决策要求阻断。
- 改动：
  - `install.ps1`：新增 `Show-WindowsX64ReleaseSurfaceProjection`，读取同一 packaged projection，执行通用 host gate 并输出 `surface_state`、`release_install_entry`、`source_install_allowed`、`source_install_entry` 与诊断。
  - `install.ps1`：在 `Install-Native` 开始处调用 projection report，但不以 release artifact admission 阻断 source/dev checkout 安装路径。
  - `test/test_windows_x64_release_surface.py`：新增 `install_ps1_reports_release_surface_without_blocking_source_install` 静态契约测试。
- TDD 证据：
  - RED：`python -m pytest -q test/test_windows_x64_release_surface.py -k "install_ps1_reports"`，失败为 `Show-WindowsX64ReleaseSurfaceProjection` 缺失。
  - GREEN/VERIFY：`python -m pytest -q test/test_windows_x64_release_surface.py -k "install_ps1_reports"`：1 passed, 15 deselected。
  - VERIFY：`python -m pytest -q test/test_windows_x64_release_surface.py`：16 passed。
- 边界：
  - PowerShell adapter 只消费 projection 和通用 host gate；不复制 Windows artifact 路由矩阵。
  - 当前 source/dev install 继续由既有 `Install-Native` 流程负责，release surface 只提供可行动诊断。
- 清洁度：
  - 本步未新增调试输出、临时 TODO/FIXME、注释掉代码或 dead import。

## 当前边界

下一步是 S9：让 Windows update 分支消费同一 projection，并证明失败 rollback 不调用 Unix installer。

## 当前边界

### S9 Windows update branch and rollback

- 退出信号：Windows x64 update 路由和 release-surface diagnostic 一致；fake staged root / fake `install.ps1` failure 单测证明 Windows update branch restore-or-retain backup 且不调用 Unix installer。
- 改动：
  - `lib/cli/management_runtime/commands_runtime/update.py`：`cmd_update()` 在普通 release update 上先分流 Windows，读取 `load_windows_x64_release_surface_projection()` 与 host evidence，再按 `update_entry` 分支处理。
  - `lib/cli/management_runtime/commands_runtime/update.py`：新增 Windows `diagnostic_only` / `npm` / `source` diagnostic 输出；三者不下载、不写 install prefix、不调用 Unix installer。
  - `lib/cli/management_runtime/commands_runtime/update.py`：新增 `_update_via_windows_release_surface()`、zip 安全解压、staged `install.ps1` 调用和 existing update identity / restore-or-retain backup / post-update 语义复用。
  - `test/test_windows_x64_release_surface_update_rollback.py`：新增 diagnostic-only 不变更测试，以及 fake staged `install.ps1` failure rollback + no Unix installer 测试。
  - `test/test_cli_management_update.py`：把旧 Windows 一律拒绝断言更新为 Windows release-surface diagnostic 断言。
- TDD 证据：
  - RED：`python -m pytest -q test/test_windows_x64_release_surface_update_rollback.py test/test_cli_management_update.py -k "windows_update or windows_uses_release_surface"`，失败为 `update_runtime` 缺 `load_windows_x64_release_surface_projection`，且 `cmd_update()` 仍输出 Linux/macOS/WSL only 拒绝。
  - GREEN/VERIFY：同一 focused 命令：2 passed, 57 deselected。
  - VERIFY：`python -m pytest -q test/test_windows_x64_release_surface_update_rollback.py`：2 passed。
  - VERIFY：`python -m pytest -q test/test_cli_management_update.py -k "windows or release_surface or install or update"`：57 passed。
  - VERIFY：`python -m pytest -q test/test_windows_bootstrap_script.py -k "windows or release_surface or install or update"`：4 passed。
  - VERIFY：`python -m pytest -q test/test_windows_x64_release_surface.py`：16 passed。
- CMD-004 当前状态：
  - 完整 CMD-004 暂未可运行：`test/test_cli_doctor_windows_x64_release_surface.py` 尚未存在，属于 S10 doctor step 的新增文件。
  - 已运行 CMD-004 中现存的 update/bootstrap 子集，结果通过；S10 补齐 doctor 测试后需重跑完整 CMD-004。
- 边界：
  - Linux/macOS 仍走既有 tarball + `run_staged_unix_installer()` 路径。
  - Windows `update_entry="npm"` 当前只输出 diagnostic / next_action，不由 Python updater 执行 `npm install`。
  - Windows `update_entry="source"` 当前只输出 source/dev 下一步，不当作 release tarball update。
- 清洁度：
  - 本步未新增调试输出、临时 TODO/FIXME、注释掉代码或 dead import。

## 当前边界

下一步是 S10：把 release-surface projection 输出到 doctor、doctor `--output` 和 README/docs，并清理旧 `doctor --bundle` 当前命令口径。

## 当前边界

### S10 doctor/docs projection

- 退出信号：doctor/render/docs 都能看到 `release_install_entry`、`source_install_allowed`、`source_install_entry`、`update_entry`、`managed_python_status`、`native_helper_status`、`failure_reason` 和 `next_action`；`docs/ccbd-diagnostics-contract.md` 不再把旧 `doctor --bundle` 作为当前公开命令。
- 改动：
  - `lib/cli/services/doctor.py`：`doctor_summary()` 新增顶层 `windows_x64_release_surface` payload，使用同一 `load_windows_x64_release_surface_projection()`，host evidence 只采集事实字段并标记 `installer_entrypoint=doctor`。
  - `lib/cli/render_runtime/ops_views_doctor.py`：新增 `windows_x64_release_surface`、detail、next_action 三类 line-oriented rows。
  - `test/test_cli_doctor_windows_x64_release_surface.py`：新增 payload、render 和 docs/README contract tests。
  - `docs/ccbd-diagnostics-contract.md`：新增 Windows x64 release-surface doctor contract；当前 support bundle 命令改为 `ccb doctor --output`，`ccb doctor --bundle` 只保留 deprecated compatibility alias。
  - `README.md` 与 `README/*.md`：补充 `windows_x64_release_surface` 字段说明和 source/dev `install.ps1` fallback vs blocked npm/release update 边界。
- TDD 证据：
  - RED：`python -m pytest -q test/test_cli_doctor_windows_x64_release_surface.py`，失败为 doctor service 缺 projection loader、render 缺 rows、docs/README 缺字段和 `doctor --bundle` 当前命令口径。
  - GREEN/VERIFY：`python -m pytest -q test/test_cli_doctor_windows_x64_release_surface.py`：3 passed。
  - VERIFY：README 覆盖检查：`README.md` 与 `README/*.md` 均包含 `windows_x64_release_surface`、`release_install_entry`、`next_action`。
  - VERIFY：CMD-013：通过，`doctor --bundle` 只出现在 deprecated 语境。
  - VERIFY：CMD-004 完整命令：`python -m pytest -q test/test_cli_doctor_windows_x64_release_surface.py test/test_windows_bootstrap_script.py test/test_cli_management_update.py -k "windows or release_surface or install or update or doctor"`：64 passed。
- 边界：
  - doctor 只展示 projection，不声明 Windows x64 final supported。
  - docs 明确这些 rows 是 diagnostics only，不授权 publish、tag 或 release promotion。
- 清洁度：
  - 本步未新增调试输出、临时 TODO/FIXME、注释掉代码或 dead import。

## 当前边界

下一步是 S11：运行非 Windows 更新安装回归与既有 Windows Rmux/diagnostics 回归，确认 release-surface 逻辑没有注入旧路径。

## 当前边界

### S11 non-Windows / Rmux regression

- 退出信号：非 Windows 更新安装回归与 Rmux packaging/diagnostics 回归通过，没有把 release-surface 逻辑注入旧路径。
- 改动：
  - `test/test_cli_doctor_rmux_packaging.py`：新增 doctor render contract，证明 legacy `terminal=rmux` binding 行保持，且缺 release-surface payload 时不会输出 `windows_x64_release_surface` rows。
  - `test/test_install_windows_rmux_contract.py`：新增 Windows install static contract，证明 `Confirm-BackendEnv` 仍在安装工作前执行，release-surface diagnostic block 不宣称 Rmux/support tier。
  - `test/test_rmux_packaging_docs_contracts.py`：新增 `rmux` 仍属 `tmux-family`，non-Windows auto 仍可选择 `legacy_default_backend="rmux"`。
- 验证证据：
  - 原 CMD-005 首次运行：失败，原因是指定的 `test/test_cli_doctor_rmux_packaging.py`、`test/test_install_windows_rmux_contract.py`、`test/test_rmux_packaging_docs_contracts.py` 在当前 filesystem 中不存在，且 `test/*rmux*` 为空。
  - 补齐当前仓库真实 Rmux/legacy contract tests 后，CMD-005：`python -m pytest -q test/test_cli_doctor_rmux_packaging.py test/test_install_windows_rmux_contract.py test/test_rmux_packaging_docs_contracts.py`：5 passed。
  - 非 Windows update focused 回归：`python -m pytest -q test/test_cli_management_update.py -k "linux or macos or wsl or release_artifact or update_via_tarball or unix_installer"`：6 passed, 51 deselected。
  - update 完整回归：`python -m pytest -q test/test_cli_management_update.py`：57 passed。
- 基线风险：
  - `python -m pytest -q test/test_install_release_entrypoints.py`：2 failed，当前 Windows host 缺 `bash`，失败为 `FileNotFoundError: [WinError 2]`，与本 feature diff 无关。
  - `python -m pytest -q test/test_cli_management_install.py test/test_install_source_dev_mode.py`：8 failed, 3 passed，失败同样集中在当前 Windows host 缺 `bash` 或测试未 monkeypatch Windows host 到 Unix installer 语义；记录为环境基线，不作为 S11 release-surface 回归。
- 清洁度：
  - 本步未新增调试输出、临时 TODO/FIXME、注释掉代码或 dead import。

## 当前边界

下一步是 S12：收集 Windows uninstall cleanup 与 update failure rollback 的真实 transcript 或 blocked evidence；rollback 语义已有 S9 fake staged failure 单测覆盖。

## 当前边界

### S12 Windows cleanup / rollback evidence

- 退出信号：Native Windows transcript 或 blocked evidence 存在；真实 Windows transcript 对齐 S8/S9 已由 fake rollback 单测覆盖的 rollback 语义。
- 证据：
  - 新增 `.codestable/features/2026-07-31-windows-x64-release-surface/evidence/cmd-011-windows-cleanup-rollback-blocked-evidence.md`。
  - 非破坏性 PowerShell host probe：PowerShell `5.1.19041.6157`，`install.ps1=True`，projection JSON `True`。
  - rollback unit：`python -m pytest -q test/test_windows_x64_release_surface_update_rollback.py`：2 passed。
- 阻断说明：
  - 未执行真实 `install.ps1 uninstall` / PATH cleanup / skills cleanup，因为该路径会删除安装目录并可能修改用户级 PATH / provider skill 文件，属于高风险文件系统与系统配置操作。
  - 当前会话未收到针对真实卸载 / PATH 修改的明确二次确认，因此按 S12 的 “transcript 或 blocked evidence” 出口记录 blocked evidence。
- 清洁度：
  - 本步未新增调试输出、临时 TODO/FIXME、注释掉代码或 dead import。

## 当前边界

### S13 scope guard and package cleanliness

- 退出信号：`npm pack --dry-run`、Windows `npm install` dry-run、scope guard 和清洁度检查全过，且没有 provider completion、recovery owner、final support claim、publish/promotion 越界。
- 验证证据：
  - `python -m pytest -q test/test_windows_x64_release_surface.py test/test_cli_doctor_windows_x64_release_surface.py test/test_windows_bootstrap_script.py test/test_cli_management_update.py -k "windows or release_surface or install or update or doctor"`：85 passed。
  - `python -m pytest -q test/test_cli_doctor_rmux_packaging.py test/test_install_windows_rmux_contract.py test/test_rmux_packaging_docs_contracts.py`：5 passed。
  - review-fix：Windows update 增加 `SHA256SUMS` 校验，npm Windows readiness/zip extraction 改用 projection entry，projection/schema 与 PowerShell fail-closed 约束补齐。
  - `node -e "const cp=require('child_process'); const out=process.platform==='win32'?cp.execFileSync('cmd',['/d','/s','/c','npm.cmd pack --dry-run --json'],{encoding:'utf8'}):cp.execFileSync('npm',['pack','--dry-run','--json'],{encoding:'utf8'}); const files=JSON.parse(out)[0].files.map(f=>f.path); if(!files.includes('lib/terminal_runtime/windows_x64_release_surface_projection.json')) throw new Error('projection JSON missing from npm pack payload'); console.log('ok')"`：projection JSON 进入包。
  - `python -c "import pathlib,re,subprocess; roots=('lib','test','docs','README','README.md','package.json','bin','install.ps1'); run=lambda a: subprocess.run(a,capture_output=True,text=True,encoding='utf-8',errors='ignore',check=True).stdout; tracked=run(['git','diff','--',*roots])+run(['git','diff','--cached','--',*roots]); others=[p for p in run(['git','ls-files','--others','--exclude-standard','--',*roots]).splitlines() if p]; extra=''.join(pathlib.Path(p).read_text(encoding='utf-8',errors='ignore') for p in others if pathlib.Path(p).is_file()); lower=(tracked+extra).lower(); q='['+chr(34)+chr(39)+']?'; patterns=('npm\\\\s+publish','git\\\\s+push','git\\\\s+tag','support_tier\\\\s*[:=]\\\\s*'+q+'supported'+q,'windows\\\\s+x64\\\\s+(is\\\\s+)?(fully\\\\s+|stable\\\\s+)?supported','full\\\\s+windows\\\\s+x64\\\\s+support','stable\\\\s+windows\\\\s+x64\\\\s+support','release[_ -]?promotion\\\\s*[:=]\\\\s*(true|enabled)','provider_completion','recovery_owner'); hits=[p for p in patterns if re.search(p,lower)]; assert not hits,hits; print('ok')"`：scope guard 通过。
- 清洁度：
  - 未引入 provider completion、recovery owner、final support claim、publish/promotion 文案；也未新增调试输出、临时 TODO/FIXME 或 dead import。

## 当前边界

实现阶段已收口。下一步转入 `cs-onboard` before_review gates：`scope-gate`、`dod-runner`、`evidence-pack`，然后进入独立 `cs-code-review`。
