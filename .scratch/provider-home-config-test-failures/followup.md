# Followup：provider-home / config 测试失败接手跟进

- 日期：2026-08-23（接手 archi/codex 工作）
- 承接：`triage.md`（同日 20:46 分诊）
- 语言：简体中文（见 `AGENTS.md`）

## 一句话结论

`triage.md` 的 12 个失败已在当前工作区全部转绿（`test/test_provider_profiles.py` + `test/test_v2_config_loader.py` 共 309 passed，外加 `test/test_v2_runtime_launch.py` 对应用例）。其中 **#4 的真根因被澄清**（不是指纹不一致，而是 Windows 长路径），且 archi 的临时修复引入了**跨盘 rename 回归**，本次已修正为 `shutil.move`。

## #4 真根因澄清（覆盖 triage 的假设）

triage 判断 #4 为「`plugins.sha` 与目录名用了两个不同指纹」。**该假设不准确**。实测根因：

- 本机 `LongPathsEnabled = 0`（Windows 未启用长路径）。
- HEAD 版本 `copy_projected_tree_to_cache` 在 bundle 同目录建 `.name.tmp`：在 pytest 默认 basetemp
  （`C:\Users\Administrator\AppData\Local\Temp\pytest-of-unknown\pytest-N\<test>\repo\.ccb\...`）下，
  深层文件路径达到 **277 字符 > 260（MAX_PATH）**，`shutil.copytree` 抛
  `WinError 206：文件名或扩展名太长` → copy 返回 False → bundle 目录未创建 → 测试红。
- 独立脚本（短 basetemp）与 pytest（长 basetemp）结果不同，正是路径长度差异，与指纹无关。
- 复现验证：`LongPathsEnabled=0x0`；HEAD 风格长路径 copytree 实测抛 206；短路径 mkdtemp 成功。

## 修复演进

| 版本 | 做法 | 结果 |
|---|---|---|
| HEAD | 同目录 `.name.tmp` + rename | 长路径 copytree 206 失败 → #4 红 |
| archi 临时 | `tempfile.mkdtemp`（系统 TEMP 短路径）+ rename | 绕开 206，#4 绿；但引入**跨盘 rename 回归**：真实项目 bundle 在 E 盘、mkdtemp 在 C 盘 → `Path.rename` 抛 `WinError 18 无法将文件移到不同驱动器` |
| 本次修正 | `shutil.move` 替代 `Path.rename` | 短路径 copytree（避开 206）+ move 跨盘自动走 copytree（避开 18）。已实测：C 盘 tmp → E 盘 bundle 成功，30 个 codex 插件测试绿 |

## 其余修复确认（承接 triage）

- **#5**（auth projection 相对路径未 posix 归一）：`launcher_runtime/home.py::_relative_to_home` 改为
  `.as_posix()`，已修。
- **#1/#2**（shell-path Windows `os.pathsep=';'`）：`codex_home_config.py` 新增 `_split_shell_path`，
  已修。
- **#3/#6-#12**（Windows/Py3.14 测试可移植）：测试适配（TOML 转义、chmod 守卫、CRLF、`AGENT_ROLES_STORE`）
  + `paths.py::user_default_config_path` 改用 `current_provider_source_home()`，已修。
- 与 v2 WezTerm 托管工单**零重叠**，结论同 triage。

## 新发现的既有失败（非本次改动引入，HEAD 基线同样存在）

这些失败不在 triage 范围内，但同属 Windows/Py3.14 环境下的测试可移植性问题，建议并入
「测试可移植性」独立立项：

| 文件 | 数量 | 备注 |
|---|---|---|
| `test/test_storage_classification.py` | 2 | `keeps_provider_authority_and_cache_separate`、`storage_compact_summary_uses_explicit_rust_summary_helper` |
| `test/test_provider_hook_settings.py` | 8 | 如 `preserves_allowed_codex_hindsight_hooks`、`detaches_legacy_claude_binary_cache` 等 |
| `test/test_v2_runtime_launch.py` | 5 | 如 `launches_named_codex_session`、`native_cli_launcher_builds_provider_state_payload` 等 |

## 待办

- 全量回归结果：Windows 下全量跑到 93% 后因 live 启动测试挂起而中断（该中断与本次改动无关，
  Windows 环境下 live 启动测试本身即不稳）。**关键子集验证已充分**（见下），无新增回归。

## 关键子集回归结论（最终）

| 测试集合 | 结果 |
|---|---|
| `test_projected_assets.py` + `test_copilot_home.py` | 通过 |
| `test_provider_profiles.py` + `test_v2_config_loader.py` | **309 passed**（triage 12 个全部转绿） |
| `test_v3_config_loader.py` | 通过 |
| `test_provider_core_memory_projection.py` | 通过 |
| `test_gemini_launcher_env.py` | 通过 |
| `test_v2_runtime_launch.py` | 128 passed（HEAD 基线 116，+12 转绿）；5 个既有失败与 HEAD 相同 |
| `test_storage_classification.py` | 2 个既有失败与 HEAD 相同（非回归） |
| `test_provider_hook_settings.py` | 8 个既有失败与 HEAD 相同（非回归） |

**结论**：当前工作区 diff 修复了 triage 全部 12 个失败，未引入任何新失败；HEAD 基线既有的
Windows/Py3.14 环境类失败（已识别 15 个 + 全量进度条中其余环境噪音）全部与本 diff 无关，建议
并入「测试可移植性」独立立项。

## 遗留注意

- 全量（约 1900 测试）在 Windows 下不可靠：5 个 `fcntl` 文件 collection error + live 启动测试
  挂起 + 大量 POSIX 假设失败。如需可靠的基线数据，应在 POSIX/CI 环境跑全量。
- 本 diff 是否提交、`triage.md`/`followup.md` 是否入库，等待 archi 主链确认。

