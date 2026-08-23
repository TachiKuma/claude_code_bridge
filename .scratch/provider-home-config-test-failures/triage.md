# Triage：CCB provider-home / config 既有测试失败（12 个）

- 日期：2026-08-23
- 基点：上游 `9805c2cd`（实测 HEAD `aa0641c3`），Python 3.14.2 on Win11
- 性质：**上游既有失败，与「WezTerm + CCB + Herdr 运行时宿主优化（v2）」无关**
- 关联：`.scratch/wezterm-ccb-herdr-hosting/spec.md`（v2，**不含**本文件内容）
- 语言：简体中文（见 `AGENTS.md`）

## 一句话结论

这 12 个失败全部落在 **CCB 层的 provider-home 物化 / project-config 权威 / 凭据所有权 / shell-path
子域**，**没有一个**触及 WezTerm（Frontend Surface）或 Herdr（Host Runtime）运行时托管边界。
它们**对 v2 spec 零影响**（代码不重叠、无 blocking edge），**不并入 v2 范围**。

其中 **10 个是仅本机环境导致**（Windows / Py3.14 下测试的 posix 假设失配），**2 个是疑似真·跨平台
bug**（#4、#5）。

## 分类表

| # | 测试短名 | CCB 子域 | 判定 | 根因 |
|---|---|---|---|---|
| 1 | shell_path_prefers_project_command_shims | shell-path | 环境 | Windows `os.pathsep=';'`，源策略冒号路径不被拆 |
| 2 | shell_path_supports_missing_user_policy | shell-path | 环境 | 同 #1 |
| 3 | codex…disables_external_migration_without_toml_reader | provider-home 物化 | 环境 | Windows 反斜杠 TOML 转义 vs 断言单反斜杠 |
| 4 | **codex…refreshes_plugin_projection_without_sha_marker** | provider-home 物化 | **真 bug** | 插件 bundle 内容寻址不一致：`plugins.sha` 与目录名用了两个不同指纹 |
| 5 | **claude…owned_credentials_symlink_during_keychain_refresh** | 凭据所有权 | **真 bug（边界/低危）** | `_relative_to_home` 未 posix 归一，反斜杠 vs manifest `/` → keychain `-U` 刷新被跳过 |
| 6 | claude…removes_only_source_owned_auth_after_logout | 凭据所有权 | 环境 | Windows 无 POSIX 权限位，`chmod(0o600)` 不生效 |
| 7 | gemini…removes_only_source_owned_auth_after_logout | 凭据所有权 | 环境 | 同 #6 |
| 8 | v2…resolves_role_store_from_account_home | project-config 权威 | 环境 | Windows 无 `pwd` 模块，回落真实 USERPROFILE |
| 9 | v2…role_missing_reports_resolved_store | project-config 权威 | 环境 | 同 #8 |
| 10 | v2…uses_user_default_when_project_config_missing | project-config 权威 | 环境 | Windows `Path.home()` 取 USERPROFILE 而非 monkeypatch 的 `HOME` |
| 11 | v2…reports_invalid_user_default_path | project-config 权威 | 环境 | 同 #10 |
| 12 | v2…supports_workspace_path_and_group_fields | project-config 权威 | 环境 | Win tmp 路径未转义插进 TOML，Py3.14 tomllib 严格拒绝 |

## 处置

### known-env（10 个：#1-3、#6-12）

标记为**仅本机环境**，本轮不修。若要消除，需做的是「测试跨平台/Windows-native + Py3.14 适配」
——这是**独立目标（测试可移植性）**，应单独立项（先 grill），**不得**塞进 v2 运行时托管。

### 真 bug（2 个）→ `/diagnosing-bugs`

- **#4（较确定，复现稳、与 OS 无关）**：codex 插件 bundle 目录命名与写入 `plugins.sha` 的指纹来源
  不一致，产生「marker 存在但 bundle 目录不存在」。
  - 入手 seam：`lib/provider_profiles/codex_home_config.py` 的 `_codex_plugin_bundle_sha` 与插件
    投影例程（约 1721–1786 行）——让**目录命名与 `plugins.sha` 用同一指纹**（一次计算、同值复用）。
- **#5（边界、低危）**：auth-projection manifest 相对路径未 posix 归一，连带 keychain `-U` 刷新被
  跳过。
  - 入手 seam：claude launcher 的 `_relative_to_home`——manifest key 统一 `Path.as_posix()`，读写
    两侧都归一化。

## 对 v2 的影响

**无。** v2 工单动的模块（前台启动 / binding / project_view / 握手 / runtime manifest / 事件投影 /
生命周期）与本文件涉及的模块互不相交。唯一 caveat：v2 的 Windows live validation 会因这 10 个
环境类失败而出现「测试红」噪音，需知其为既有、无关。
