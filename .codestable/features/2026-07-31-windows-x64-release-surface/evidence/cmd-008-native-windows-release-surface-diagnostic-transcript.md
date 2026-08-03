# CMD-008 Native Windows release-surface diagnostic transcript

## 结论

本机 Native Windows x64 可观察到同一 Windows x64 release-surface projection；当前真实发布面仍按设计 fail closed：

- `surface_state=blocked`
- `failure_reason=release-artifact-missing`
- `release_install_entry=diagnostic_only`
- `source_install_allowed=True`
- `source_install_entry=install_ps1`
- `update_entry=diagnostic_only`

本证据不执行真实 install/uninstall，不修改用户 PATH / skills，不下载 release artifact，不执行 publish/promotion。

## code-level npm route

命令：

```powershell
node -e "const adapter=require('./bin/ccb-npm-install.js'); try { adapter.artifactForWindowsX64ReleaseSurface(process.cwd(), {os_platform:'win32', cpu_arch:'x64', process_arch:'x64', wow64:false, installer_entrypoint:'npm'}); console.log('unexpected route opened'); process.exit(1); } catch (error) { console.log(String(error.message).split('\n').slice(0,2).join('\n')); }"
```

结果：exit 0，输出：

```text
Windows x64 release route is blocked by the current release-surface projection. release_install_entry=diagnostic_only
Next action: Use install.ps1 for source/dev checkout installs and keep release/npm routes diagnostic-only.
```

## install.ps1 projection diagnostic

命令只在内存中加载 `install.ps1` 函数定义并调用 `Show-WindowsX64ReleaseSurfaceProjection`；不调用 `Install-Native` / `Uninstall-Native`。

结果：exit 0，输出：

```text
Windows x64 release surface: state=blocked release_install_entry=diagnostic_only source_install_allowed=True source_install_entry=install_ps1
Windows x64 release surface diagnostic: Windows x64 release route is blocked by the current release-surface projection.
Windows x64 release surface next_action: Use install.ps1 for source/dev checkout installs and keep release/npm routes diagnostic-only.
```

## ccb update diagnostic-only route

命令通过 `cmd_update()` 直接进入 Windows release-surface update branch，设置 `PYTHONUTF8=1` 避免 Windows GBK 输出问题。

结果：exit 0，业务返回码为预期 `1`，输出：

```text
Windows x64 update route is diagnostic_only: Windows x64 release route is blocked by the current release-surface projection.
failure_reason=release-artifact-missing
next_action=Use install.ps1 for source/dev checkout installs and keep release/npm routes diagnostic-only.
exit_code 1
```

## ccb doctor live smoke

命令在隔离 `%TEMP%\ccb-release-surface-qa-doctor-*` 目录运行，避免当前仓库 `.ccb/ccb.config` 干扰。

结果：exit 0，输出包含：

```text
windows_x64_release_surface: surface_state=blocked failure_reason=release-artifact-missing release_install_entry=diagnostic_only source_install_allowed=True source_install_entry=install_ps1 update_entry=diagnostic_only managed_python_status=unknown native_helper_status=unknown
windows_x64_release_surface_detail: implementation_admission=admitted baseline_version_status=v8.5.2 upstream_gate_status=blocked upstream_failure_ref=None upstream_detail_reason=release-artifact-missing beta_gaps=none
windows_x64_release_surface_next_action: diagnostic=Windows x64 release route is blocked by the current release-surface projection. next_action=Use install.ps1 for source/dev checkout installs and keep release/npm routes diagnostic-only.
```

## ccb doctor --output bundle smoke

命令在隔离 `%TEMP%\ccb-release-surface-qa-doctor-output-*` 目录运行并写入临时 bundle。

结果：exit 0，`doctor_bundle_status=ok`。gzip 解压后包含：

```text
"windows_x64_release_surface": {
"failure_reason": "release-artifact-missing",
"release_install_entry": "diagnostic_only",
"update_entry": "diagnostic_only",
"upstream_detail_reason": "release-artifact-missing",
```

## 未执行动作

- 未执行真实 `install.ps1 install`：该路径会复制安装目录、写 wrapper，并可能修改用户级 PATH / provider skill 文件。当前 feature 的 source/dev preservation 已由静态 contract、PowerShell projection diagnostic 与 focused tests 覆盖。
- 未执行真实 `install.ps1 uninstall`、PATH cleanup 或 skills cleanup：见 CMD-011 blocked evidence。
