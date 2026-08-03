# CMD-011 Windows cleanup / rollback blocked evidence

## 结论

本机是 Native Windows，可运行 PowerShell，但本轮没有执行真实 `install.ps1 uninstall`、PATH 清理或 skills cleanup。

原因：`install.ps1 uninstall` 会删除安装目录并可能修改用户级 PATH / provider skill 文件，属于 AGENTS.md 定义的高风险文件系统与系统配置操作。当前会话没有收到针对真实卸载 / PATH 修改的明确二次确认，因此按协议只落 blocked evidence，不做破坏性动作。

## 非破坏性 host probe

- 命令：`powershell -NoProfile -Command "$PSVersionTable.PSVersion.ToString(); Test-Path '.\install.ps1'; Test-Path '.\lib\terminal_runtime\windows_x64_release_surface_projection.json'"`
- 结果：
  - PowerShell：`5.1.19041.6157`
  - `install.ps1`：`True`
  - `lib/terminal_runtime/windows_x64_release_surface_projection.json`：`True`

## rollback 单测证据

- 命令：`python -m pytest -q test/test_windows_x64_release_surface_update_rollback.py`
- 结果：`2 passed`
- 覆盖：
  - `update_entry="diagnostic_only"` 不下载、不写 install prefix。
  - fake staged `install.ps1` failure 返回非零时 restore prior install prefix。
  - Windows update branch 不调用 `run_staged_unix_installer()`。

## 后续可执行的真实验证

如 owner 明确确认可修改临时 install prefix 和用户 PATH / skills，可用隔离的 `CODEX_INSTALL_PREFIX`、`CODEX_BIN_DIR` 与临时 HOME 重新捕获真实 `install.ps1 uninstall` transcript。没有该确认前，继续以本 blocked evidence 和 S9 rollback unit 作为 S12 acceptance 证据。
