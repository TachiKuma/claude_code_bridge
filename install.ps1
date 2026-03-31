param(
  [Parameter(Position = 0)]
  [ValidateSet("install", "uninstall", "help")]
  [string]$Command = "help",
  [string]$InstallPrefix = "$env:LOCALAPPDATA\codex-dual",
  [switch]$Yes
)

# --- UTF-8 / BOM compatibility (Windows PowerShell 5.1) ---
# Keep this near the top so Chinese/emoji output is rendered correctly.
try {
  $script:utf8NoBom = [System.Text.UTF8Encoding]::new($false)
} catch {
  $script:utf8NoBom = [System.Text.Encoding]::UTF8
}
try { $OutputEncoding = $script:utf8NoBom } catch {}
try { [Console]::OutputEncoding = $script:utf8NoBom } catch {}
try { [Console]::InputEncoding = $script:utf8NoBom } catch {}
try { chcp 65001 | Out-Null } catch {}

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

# Constants
$script:CCB_START_MARKER = "<!-- CCB_CONFIG_START -->"
$script:CCB_END_MARKER = "<!-- CCB_CONFIG_END -->"
$script:CCB_WEZTERM_START_MARKER = "-- CCB_WEZTERM_START"
$script:CCB_WEZTERM_END_MARKER = "-- CCB_WEZTERM_END"

$script:SCRIPTS_TO_LINK = @(
  "ccb",
  "cask", "cpend", "cping",
  "gask", "gpend", "gping",
  "oask", "opend", "oping",
  "lask", "lpend", "lping",
  "dask", "dpend", "dping",
  "ask", "ccb-ping", "pend", "autonew", "ccb-completion-hook", "maild"
)

$script:CLAUDE_MARKDOWN = @(
  # Old CCB commands removed - replaced by unified ask/ping/pend skills
)

$script:LEGACY_SCRIPTS = @(
  "cast", "cast-w", "codex-ask", "codex-pending", "codex-ping",
  "claude-codex-dual", "claude_codex", "claude_ai", "claude_bridge"
)

# i18n support
function Get-CCBLang {
  $lang = $env:CCB_LANG
  if ($lang -in @("zh", "cn", "chinese")) { return "zh" }
  if ($lang -in @("en", "english")) { return "en" }
  # Auto-detect from system
  try {
    $culture = (Get-Culture).Name
    if ($culture -like "zh*") { return "zh" }
  } catch {}
  return "en"
}

$script:CCBLang = Get-CCBLang

function Get-Msg {
  param([string]$Key, [string]$Arg1 = "", [string]$Arg2 = "")
  $legacyKeyMap = @{
    "install_complete" = "install.complete"
    "uninstall_complete" = "install.uninstall_complete"
    "python_old" = "install.python.version_old"
    "requires_python" = "install.python.requires"
    "confirm_windows" = "install.backend.confirm_windows"
    "cancelled" = "install.backend.cancelled"
    "windows_warning" = "install.backend.windows_warning"
    "same_env" = "install.backend.same_env"
  }
  if ($legacyKeyMap.ContainsKey($Key)) {
    $Key = $legacyKeyMap[$Key]
  }
  $msgs = @{
    "install.complete" = @{ en = "Installation complete!"; zh = "安装完成！" }
    "install.uninstall_complete" = @{ en = "Uninstall complete."; zh = "卸载完成。" }
    "install.common.separator" = @{ en = "================================================================"; zh = "================================================================" }
    "install.usage.title" = @{ en = "Usage:"; zh = "用法：" }
    "install.usage.install" = @{ en = "  .\\install.ps1 install    # Install or update"; zh = "  .\\install.ps1 install    # 安装或更新" }
    "install.usage.uninstall" = @{ en = "  .\\install.ps1 uninstall  # Uninstall"; zh = "  .\\install.ps1 uninstall  # 卸载" }
    "install.usage.options" = @{ en = "Options:"; zh = "选项：" }
    "install.usage.install_prefix" = @{ en = "  -InstallPrefix <path>    # Custom install location (default: $env:LOCALAPPDATA\\codex-dual)"; zh = "  -InstallPrefix <path>    # 自定义安装目录（默认：$env:LOCALAPPDATA\\codex-dual）" }
    "install.usage.requirements" = @{ en = "Requirements:"; zh = "依赖：" }
    "install.usage.python_requirement" = @{ en = "  - Python 3.10+"; zh = "  - Python 3.10+" }
    "install.python.not_found" = @{ en = "Python not found. Please install Python and add it to PATH."; zh = "未找到 Python，请先安装并加入 PATH。" }
    "install.python.download" = @{ en = "Download: https://www.python.org/downloads/"; zh = "下载地址：https://www.python.org/downloads/" }
    "install.python.version_old" = @{ en = "Python version too old: $Arg1"; zh = "Python 版本过旧：$Arg1" }
    "install.python.requires" = @{ en = "ccb requires Python 3.10+"; zh = "ccb 需要 Python 3.10+" }
    "install.python.detect_failed" = @{ en = "Failed to query Python version using: $Arg1"; zh = "无法查询 Python 版本：$Arg1" }
    "install.python.error_details" = @{ en = "   Error details: $Arg1"; zh = "   错误详情：$Arg1" }
    "install.python.ok" = @{ en = "[OK] Python $Arg1"; zh = "[OK] Python $Arg1" }
    "install.backend.windows_warning" = @{ en = "You are installing ccb in native Windows environment"; zh = "你正在原生 Windows 环境中安装 ccb" }
    "install.backend.same_env" = @{ en = "ccb/ask/ping/pend must run in the same environment as codex/gemini."; zh = "ccb/ask/ping/pend 必须与 codex/gemini 在同一环境运行。" }
    "install.backend.confirm_windows" = @{ en = "Continue installation in Windows? (y/N)"; zh = "确认安装到原生 Windows 环境中吗？(y/N)" }
    "install.backend.cancelled" = @{ en = "Installation cancelled"; zh = "安装已取消" }
    "install.backend.non_interactive_error" = @{ en = "Non-interactive environment detected, aborting to prevent Windows/WSL mismatch."; zh = "检测到非交互环境，为避免 Windows/WSL 环境错配，安装已中止。" }
    "install.backend.if_windows" = @{ en = "   If codex/gemini will run in native Windows:"; zh = "   如果 codex/gemini 将在原生 Windows 运行：" }
    "install.backend.re_run_windows" = @{ en = "Re-run: powershell -ExecutionPolicy Bypass -File .\\install.ps1 install -Yes"; zh = "请重新执行：powershell -ExecutionPolicy Bypass -File .\\install.ps1 install -Yes" }
    "install.backend.confirm_native" = @{ en = "Please confirm: You will install and run codex/gemini in native Windows (not WSL)."; zh = "请确认：你将在原生 Windows 中安装并运行 codex/gemini（非 WSL 环境）。" }
    "install.backend.if_wsl" = @{ en = "If you plan to run codex/gemini in WSL, exit and run in WSL:"; zh = "如果你计划在 WSL 中运行 codex/gemini，请退出并在 WSL 中执行：" }
    "install.backend.install_sh" = @{ en = "   ./install.sh install"; zh = "   ./install.sh install" }
    "install.starting" = @{ en = "Installing ccb to $Arg1 ..."; zh = "正在安装 ccb 到 $Arg1 ..." }
    "install.using_python" = @{ en = "Using Python: $Arg1"; zh = "使用 Python：$Arg1" }
    "install.path.added" = @{ en = "Added $Arg1 to user PATH"; zh = "已将 $Arg1 添加到用户 PATH" }
    "install.version.injected" = @{ en = "Injected version info: $Arg1 $Arg2"; zh = "已注入版本信息：$Arg1 $Arg2" }
    "install.version.inject_failed" = @{ en = "Failed to inject version info: $Arg1"; zh = "注入版本信息失败：$Arg1" }
    "install.skill.installing_claude" = @{ en = "Installing Claude skills (PowerShell SKILL.md templates)..."; zh = "正在安装 Claude skills（PowerShell SKILL.md 模板）..." }
    "install.skill.installing_codex" = @{ en = "Installing Codex skills (PowerShell SKILL.md templates)..."; zh = "正在安装 Codex skills（PowerShell SKILL.md 模板）..." }
    "install.skill.installing_factory" = @{ en = "Installing Droid/Factory skills..."; zh = "正在安装 Droid/Factory skills..." }
    "install.skill.updated" = @{ en = "  Updated skill: $Arg1"; zh = "  已更新 skill：$Arg1" }
    "install.skill.updated_codex" = @{ en = "  Updated Codex skill: $Arg1"; zh = "  已更新 Codex skill：$Arg1" }
    "install.skill.updated_factory" = @{ en = "  Updated Factory skill: $Arg1"; zh = "  已更新 Factory skill：$Arg1" }
    "install.skill.docs_installed" = @{ en = "  Installed skills docs: docs/"; zh = "  已安装 skills 文档：docs/" }
    "install.skill.updated_dir" = @{ en = "Updated skills directory: $Arg1"; zh = "已更新 skills 目录：$Arg1" }
    "install.codex.updated_dir" = @{ en = "Updated Codex skills directory: $Arg1"; zh = "已更新 Codex skills 目录：$Arg1" }
    "install.factory.updated_dir" = @{ en = "Updated Factory skills directory: $Arg1"; zh = "已更新 Factory skills 目录：$Arg1" }
    "install.droid.mcp.missing" = @{ en = "Droid MCP server not found at $Arg1; skipping"; zh = "未找到 Droid MCP server：$Arg1，已跳过" }
    "install.droid.mcp.registered" = @{ en = "OK: Droid MCP delegation registered"; zh = "OK：Droid MCP delegation 已注册" }
    "install.droid.mcp.failed" = @{ en = "Droid MCP delegation setup failed: $Arg1"; zh = "Droid MCP delegation 配置失败：$Arg1" }
    "install.claude.template_missing" = @{ en = "Template not found: $Arg1; skipping CLAUDE.md injection"; zh = "未找到模板：$Arg1，跳过 CLAUDE.md 注入" }
    "install.claude.updated" = @{ en = "Updated CLAUDE.md with CCB collaboration rules"; zh = "已更新 CLAUDE.md（CCB 协作规则）" }
    "install.claude.created" = @{ en = "Created CLAUDE.md with CCB collaboration rules"; zh = "已创建 CLAUDE.md（CCB 协作规则）" }
    "install.settings.updated" = @{ en = "Updated settings.json with permissions"; zh = "已更新 settings.json 权限配置" }
    "install.agents.updated" = @{ en = "Updated AGENTS.md with review rubrics"; zh = "已更新 AGENTS.md（评审 Rubrics）" }
    "install.clinerules.updated" = @{ en = "Updated .clinerules with role assignments"; zh = "已更新 .clinerules（角色分配）" }
    "install.wezterm.not_found" = @{ en = "WezTerm config not found; skipping default shell configuration."; zh = "未找到 WezTerm 配置，跳过默认 shell 配置。" }
    "install.wezterm.checked" = @{ en = "  Checked:"; zh = "  已检查：" }
    "install.wezterm.powershell_missing" = @{ en = "PowerShell not found; skipping WezTerm configuration."; zh = "未找到 PowerShell，跳过 WezTerm 配置。" }
    "install.wezterm.config_unrecognized" = @{ en = "WezTerm config doesn't appear to use a 'config' variable; skipping automatic edit."; zh = "WezTerm 配置似乎未使用 config 变量，跳过自动修改。" }
    "install.wezterm.suggested_snippet" = @{ en = "Suggested snippet to add before your return statement:"; zh = "建议在 return 语句前添加以下片段：" }
    "install.wezterm.configured" = @{ en = "✓ WezTerm configured to use $Arg1 ($Arg2)"; zh = "✓ WezTerm 已配置为使用 $Arg1（$Arg2）" }
    "install.wezterm.not_changed" = @{ en = "WezTerm default_prog not changed."; zh = "WezTerm default_prog 未变更。" }
    "install.wezterm.hint_added" = @{ en = "WezTerm default_prog not changed; added a comment hint to $Arg1"; zh = "WezTerm default_prog 未变更；已在 $Arg1 添加提示注释" }
    "install.cleanup.legacy.start" = @{ en = "Cleaning up legacy files..."; zh = "正在清理遗留文件..." }
    "install.cleanup.legacy.daemon_removed" = @{ en = "  Removed legacy daemon script: $Arg1"; zh = "  已删除遗留 daemon 脚本：$Arg1" }
    "install.cleanup.legacy.state_removed" = @{ en = "  Removed legacy state file: $Arg1"; zh = "  已删除遗留 state 文件：$Arg1" }
    "install.cleanup.legacy.module_removed" = @{ en = "  Removed legacy module: $Arg1"; zh = "  已删除遗留模块：$Arg1" }
    "install.cleanup.legacy.none" = @{ en = "  No legacy files found"; zh = "  未发现遗留文件" }
    "install.cleanup.legacy.done" = @{ en = "  Cleaned up $Arg1 legacy file(s)"; zh = "  已清理 $Arg1 个遗留文件" }
    "install.complete.restart_terminal" = @{ en = "Restart your terminal (WezTerm) for PATH changes to take effect."; zh = "请重启终端（WezTerm）以使 PATH 变更生效。" }
    "install.quickstart.title" = @{ en = "Quick start:"; zh = "快速开始：" }
    "install.quickstart.ccb" = @{ en = "  ccb             # Start providers from ccb.config (default: all four)"; zh = "  ccb             # 从 ccb.config 启动 providers（默认四个）" }
    "install.quickstart.codex" = @{ en = "  ccb codex       # Start with Codex backend"; zh = "  ccb codex       # 启动 Codex 后端" }
    "install.quickstart.gemini" = @{ en = "  ccb gemini      # Start with Gemini backend"; zh = "  ccb gemini      # 启动 Gemini 后端" }
    "install.quickstart.opencode" = @{ en = "  ccb opencode    # Start with OpenCode backend"; zh = "  ccb opencode    # 启动 OpenCode 后端" }
    "install.quickstart.claude" = @{ en = "  ccb claude      # Start with Claude backend"; zh = "  ccb claude      # 启动 Claude 后端" }
    "install.warn.wezterm_skipped" = @{ en = "WezTerm configuration skipped: $Arg1"; zh = "WezTerm 配置已跳过：$Arg1" }
    "install.warn.prefix" = @{ en = "[WARNING] $Arg1"; zh = "[WARNING] $Arg1" }
    "install.wezterm.checked_entry" = @{ en = "   - $Arg1"; zh = "   - $Arg1" }
    "install.wezterm.snippet_line" = @{ en = "  config.default_prog = { '$Arg1' }"; zh = "  config.default_prog = { '$Arg1' }" }
    "install.wezterm.already_configured" = @{ en = "WezTerm default_prog already configured for PowerShell."; zh = "WezTerm default_prog 已配置为 PowerShell。" }
    "install.wezterm.override_prompt" = @{ en = "WezTerm default_prog is already configured. Override to '$Arg1'? (y/N)"; zh = "WezTerm default_prog 已配置。是否覆盖为 '$Arg1'？(y/N)" }
    "install.uninstall.removed_prefix" = @{ en = "Removed $Arg1"; zh = "已删除 $Arg1" }
    "install.uninstall.removed_path" = @{ en = "Removed $Arg1 from user PATH"; zh = "已从用户 PATH 中删除 $Arg1" }
    "install.uninstall.removing_claude_skills" = @{ en = "Removing CCB Claude skills..."; zh = "正在移除 CCB Claude skills..." }
    "install.uninstall.removed_skill" = @{ en = "  Removed skill: $Arg1"; zh = "  已删除 skill：$Arg1" }
    "install.uninstall.removing_claude_block" = @{ en = "Removing CCB config from CLAUDE.md..."; zh = "正在从 CLAUDE.md 移除 CCB 配置..." }
    "install.uninstall.removed_claude_block" = @{ en = "  Removed CCB config block"; zh = "  已删除 CCB 配置块" }
    "install.uninstall.permissions_removed" = @{ en = "Removed CCB permissions from settings.json"; zh = "已从 settings.json 移除 CCB 权限" }
    "install.uninstall.settings_clean_failed" = @{ en = "Could not clean settings.json: $Arg1"; zh = "无法清理 settings.json：$Arg1" }
    "install.uninstall.removing_codex_skills" = @{ en = "Removing CCB Codex skills..."; zh = "正在移除 CCB Codex skills..." }
    "install.uninstall.removing_droid_skills" = @{ en = "Removing CCB Droid skills..."; zh = "正在移除 CCB Droid skills..." }
    "install.uninstall.removing_wezterm_block" = @{ en = "Removing CCB config from .wezterm.lua..."; zh = "正在从 .wezterm.lua 移除 CCB 配置..." }
    "install.uninstall.removed_wezterm_block" = @{ en = "  Removed CCB WezTerm config block"; zh = "  已删除 CCB WezTerm 配置块" }
  }
  if ($msgs.ContainsKey($Key)) {
    return $msgs[$Key][$script:CCBLang]
  }
  return $Key
}

function Show-Usage {
  Write-Host (Get-Msg "install.usage.title")
  Write-Host (Get-Msg "install.usage.install")
  Write-Host (Get-Msg "install.usage.uninstall")
  Write-Host
  Write-Host (Get-Msg "install.usage.options")
  Write-Host (Get-Msg "install.usage.install_prefix")
  Write-Host
  Write-Host (Get-Msg "install.usage.requirements")
  Write-Host (Get-Msg "install.usage.python_requirement")
}

function Find-Python {
  if (Get-Command py -ErrorAction SilentlyContinue) { return "py -3" }
  if (Get-Command python -ErrorAction SilentlyContinue) { return (Get-Command python).Source }
  if (Get-Command python3 -ErrorAction SilentlyContinue) { return (Get-Command python3).Source }
  return $null
}

function Require-Python310 {
  param([string]$PythonCmd)

  # Handle commands with arguments (e.g., "py -3")
  $cmdParts = $PythonCmd -split ' ', 2
  $fileName = $cmdParts[0]
  $baseArgs = if ($cmdParts.Length -gt 1) { $cmdParts[1] } else { "" }

  # Use ProcessStartInfo for reliable execution across different Python installations
  # (e.g., Miniconda, custom paths). The & operator can fail in some environments.
  try {
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $fileName
    # Combine base arguments with Python code arguments
    if ($baseArgs) {
      $psi.Arguments = "$baseArgs -c `"import sys; v=sys.version_info; print(f'{v.major}.{v.minor}.{v.micro} {v.major} {v.minor}')`""
    } else {
      $psi.Arguments = "-c `"import sys; v=sys.version_info; print(f'{v.major}.{v.minor}.{v.micro} {v.major} {v.minor}')`""
    }
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $psi
    $process.Start() | Out-Null
    $process.WaitForExit()

    $vinfo = $process.StandardOutput.ReadToEnd().Trim()
    if ($process.ExitCode -ne 0 -or [string]::IsNullOrEmpty($vinfo)) {
      throw $process.StandardError.ReadToEnd()
    }

    $vparts = $vinfo -split " "
    if ($vparts.Length -lt 3) {
      throw "Unexpected version output: $vinfo"
    }

    $version = $vparts[0]
    $major = [int]$vparts[1]
    $minor = [int]$vparts[2]
  } catch {
    Write-Host (Get-Msg "install.python.detect_failed" -Arg1 $PythonCmd)
    Write-Host (Get-Msg "install.python.error_details" -Arg1 "$_")
    exit 1
  }

  if (($major -ne 3) -or ($minor -lt 10)) {
    Write-Host (Get-Msg "install.python.version_old" -Arg1 $version)
    Write-Host (Get-Msg "install.python.requires")
    Write-Host (Get-Msg "install.python.download")
    exit 1
  }
  Write-Host (Get-Msg "install.python.ok" -Arg1 $version)
}

function Confirm-BackendEnv {
  if ($Yes -or $env:CCB_INSTALL_ASSUME_YES -eq "1") { return }

  if (-not [Environment]::UserInteractive) {
    Write-Host (Get-Msg "install.backend.non_interactive_error")
    Write-Host (Get-Msg "install.backend.if_windows")
    Write-Host (Get-Msg "install.backend.re_run_windows")
    exit 1
  }

  Write-Host
  Write-Host (Get-Msg "install.common.separator")
  Write-Host (Get-Msg "install.warn.prefix" -Arg1 (Get-Msg "install.backend.windows_warning"))
  Write-Host (Get-Msg "install.common.separator")
  Write-Host (Get-Msg "install.backend.same_env")
  Write-Host
  Write-Host (Get-Msg "install.backend.confirm_native")
  Write-Host (Get-Msg "install.backend.if_wsl")
  Write-Host (Get-Msg "install.backend.install_sh")
  Write-Host (Get-Msg "install.common.separator")
  $reply = Read-Host (Get-Msg "install.backend.confirm_windows")
  if ($reply.Trim().ToLower() -notin @("y", "yes")) {
    Write-Host (Get-Msg "install.backend.cancelled")
    exit 1
  }
}

function Install-Native {
  Confirm-BackendEnv

  $binDir = Join-Path $InstallPrefix "bin"
  $pythonCmd = Find-Python

  if (-not $pythonCmd) {
    Write-Host (Get-Msg "install.python.not_found")
    Write-Host (Get-Msg "install.python.download")
    exit 1
  }

  Require-Python310 -PythonCmd $pythonCmd

  Write-Host (Get-Msg "install.starting" -Arg1 $InstallPrefix)
  Write-Host (Get-Msg "install.using_python" -Arg1 $pythonCmd)

  $cleanInstall = $false
  $cleanEnv = ($env:CCB_CLEAN_INSTALL -as [string])
  if ($cleanEnv -and $cleanEnv.Trim() -notin @("0", "false", "no", "off")) {
    $cleanInstall = $true
  }
  if ($cleanInstall -and (Test-Path $InstallPrefix)) {
    $repoRootResolved = $repoRoot
    $installResolved = $InstallPrefix
    try { $repoRootResolved = (Resolve-Path $repoRoot).Path } catch {}
    try { $installResolved = (Resolve-Path $InstallPrefix).Path } catch {}
    if ($repoRootResolved -ne $installResolved) {
      Remove-Item -Recurse -Force $InstallPrefix
    }
  }

  if (-not (Test-Path $InstallPrefix)) {
    New-Item -ItemType Directory -Path $InstallPrefix -Force | Out-Null
  }
  if (-not (Test-Path $binDir)) {
    New-Item -ItemType Directory -Path $binDir -Force | Out-Null
  }

  $items = @("ccb", "lib", "bin", "commands", "mcp", "droid_skills")
  foreach ($item in $items) {
    $src = Join-Path $repoRoot $item
    $dst = Join-Path $InstallPrefix $item
    if (Test-Path $src) {
      if (Test-Path $dst) { Remove-Item -Recurse -Force $dst }
      Copy-Item -Recurse -Force $src $dst
    }
  }

  # Exclude web UI code from installation (CLI-only mail setup)
  $webDir = Join-Path $InstallPrefix "lib\\web"
  if (Test-Path $webDir) { Remove-Item -Recurse -Force $webDir }
  $ccbWeb = Join-Path $InstallPrefix "bin\\ccb-web"
  if (Test-Path $ccbWeb) { Remove-Item -Force $ccbWeb }

  function Fix-PythonShebang {
    param([string]$TargetPath)
    if (-not $TargetPath -or -not (Test-Path $TargetPath)) { return }
    try {
      $text = [System.IO.File]::ReadAllText($TargetPath, [System.Text.Encoding]::UTF8)
      if ($text -match '^\#\!/usr/bin/env python3') {
        $text = $text -replace '^\#\!/usr/bin/env python3', '#!/usr/bin/env python'
        [System.IO.File]::WriteAllText($TargetPath, $text, $script:utf8NoBom)
      }
    } catch {
      return
    }
  }

  $scripts = @(
    "ccb",
    "cask", "cping", "cpend",
    "gask", "gping", "gpend",
    "oask", "oping", "opend",
    "lask", "lping", "lpend",
    "dask", "dping", "dpend",
    "ask", "ccb-ping", "pend", "autonew", "ccb-completion-hook", "maild"
  )

  # In MSYS/Git-Bash, invoking the script file directly will honor the shebang.
  # Windows typically has `python` but not `python3`, so rewrite shebangs for compatibility.
  foreach ($script in $scripts) {
    if ($script -eq "ccb") {
      Fix-PythonShebang (Join-Path $InstallPrefix "ccb")
    } else {
      Fix-PythonShebang (Join-Path $InstallPrefix ("bin\\" + $script))
    }
  }

  foreach ($script in $scripts) {
    $batPath = Join-Path $binDir "$script.bat"
    $cmdPath = Join-Path $binDir "$script.cmd"
    if ($script -eq "ccb") {
      $relPath = "..\\ccb"
    } else {
      # Script is installed alongside the wrapper under $InstallPrefix\bin
      $relPath = $script
    }
    $wrapperContent = "@echo off`r`nset `"PYTHON=python`"`r`nwhere python >NUL 2>&1 || set `"PYTHON=py -3`"`r`n%PYTHON% `"%~dp0$relPath`" %*"
    [System.IO.File]::WriteAllText($batPath, $wrapperContent, $script:utf8NoBom)
    # .cmd wrapper for PowerShell/CMD users (and tools preferring .cmd over raw shebang scripts)
    [System.IO.File]::WriteAllText($cmdPath, $wrapperContent, $script:utf8NoBom)
  }

  $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
  $pathList = if ($userPath) { $userPath -split ";" | Where-Object { $_ } } else { @() }
  $binDirLower = $binDir.ToLower()
  $alreadyInPath = $pathList | Where-Object { $_.ToLower() -eq $binDirLower }
  if (-not $alreadyInPath) {
    $newPath = ($pathList + $binDir) -join ";"
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Host (Get-Msg "install.path.added" -Arg1 $binDir)
  }

  # Git version injection
  function Get-GitVersionInfo {
    param([string]$RepoRoot)

    $commit = ""
    $date = ""

    # 方法1: 本地 Git
    if (Get-Command git -ErrorAction SilentlyContinue) {
      if (Test-Path (Join-Path $RepoRoot ".git")) {
        try {
          $commit = (git -C $RepoRoot log -1 --format='%h' 2>$null)
          $date = (git -C $RepoRoot log -1 --format='%cs' 2>$null)
        } catch {}
      }
    }

    # 方法2: 环境变量
    if (-not $commit -and $env:CCB_GIT_COMMIT) {
      $commit = $env:CCB_GIT_COMMIT
      $date = $env:CCB_GIT_DATE
    }

    # 方法3: GitHub API
    if (-not $commit) {
      try {
        $api = "https://api.github.com/repos/bfly123/claude_code_bridge/commits/main"
        $response = Invoke-RestMethod -Uri $api -TimeoutSec 5 -ErrorAction Stop
        $commit = $response.sha.Substring(0,7)
        $date = $response.commit.committer.date.Substring(0,10)
      } catch {}
    }

    return @{Commit=$commit; Date=$date}
  }

  # 注入版本信息到 ccb 文件
  $verInfo = Get-GitVersionInfo -RepoRoot $repoRoot
  if ($verInfo.Commit) {
    $ccbPath = Join-Path $InstallPrefix "ccb"
    if (Test-Path $ccbPath) {
      try {
        $content = Get-Content $ccbPath -Raw -Encoding UTF8
        $content = $content -replace 'GIT_COMMIT = ""', "GIT_COMMIT = `"$($verInfo.Commit)`""
        $content = $content -replace 'GIT_DATE = ""', "GIT_DATE = `"$($verInfo.Date)`""
        [System.IO.File]::WriteAllText($ccbPath, $content, [System.Text.UTF8Encoding]::new($false))
        Write-Host (Get-Msg "install.version.injected" -Arg1 $verInfo.Commit -Arg2 $verInfo.Date)
      } catch {
        Write-Host (Get-Msg "install.warn.prefix" -Arg1 (Get-Msg "install.version.inject_failed" -Arg1 "$_"))
      }
    }
  }
  Install-CodexSkills
  Install-ClaudeConfig
  Install-DroidSkills
  Install-DroidDelegation -PythonCmd $pythonCmd -InstallPrefix $InstallPrefix
  Cleanup-LegacyFiles -InstallPrefix $InstallPrefix

  try {
    Set-WezTermDefaultShellToPowerShell
  } catch {
    Write-Host (Get-Msg "install.warn.prefix" -Arg1 (Get-Msg "install.warn.wezterm_skipped" -Arg1 "$_"))
  }

  Write-Host
  Write-Host (Get-Msg "install.complete")
  Write-Host (Get-Msg "install.complete.restart_terminal")
  Write-Host
  Write-Host (Get-Msg "install.quickstart.title")
  Write-Host (Get-Msg "install.quickstart.ccb")
  Write-Host (Get-Msg "install.quickstart.codex")
  Write-Host (Get-Msg "install.quickstart.gemini")
  Write-Host (Get-Msg "install.quickstart.opencode")
  Write-Host (Get-Msg "install.quickstart.claude")
}

# Clean up legacy daemon files (replaced by unified askd)
function Cleanup-LegacyFiles {
  param([string]$InstallPrefix)

  Write-Host (Get-Msg "install.cleanup.legacy.start")
  $cleaned = 0

  # Legacy daemon scripts in bin/
  $legacyDaemons = @("caskd", "gaskd", "oaskd", "laskd", "daskd")
  $binDir = Join-Path $InstallPrefix "bin"

  foreach ($daemon in $legacyDaemons) {
    $daemonPath = Join-Path $binDir $daemon
    if (Test-Path $daemonPath) {
      Remove-Item -Force $daemonPath
      Write-Host (Get-Msg "install.cleanup.legacy.daemon_removed" -Arg1 $daemonPath)
      $cleaned++
    }
  }

  # Legacy daemon state files in cache
  $cacheDir = Join-Path $env:LOCALAPPDATA "ccb"
  $legacyStates = @("caskd.json", "gaskd.json", "oaskd.json", "laskd.json", "daskd.json")

  foreach ($state in $legacyStates) {
    $statePath = Join-Path $cacheDir $state
    if (Test-Path $statePath) {
      Remove-Item -Force $statePath
      Write-Host (Get-Msg "install.cleanup.legacy.state_removed" -Arg1 $statePath)
      $cleaned++
    }
  }

  # Legacy daemon module files in lib/
  $libDir = Join-Path $InstallPrefix "lib"
  $legacyModules = @("caskd_daemon.py", "gaskd_daemon.py", "oaskd_daemon.py", "laskd_daemon.py", "daskd_daemon.py")

  foreach ($module in $legacyModules) {
    $modulePath = Join-Path $libDir $module
    if (Test-Path $modulePath) {
      Remove-Item -Force $modulePath
      Write-Host (Get-Msg "install.cleanup.legacy.module_removed" -Arg1 $modulePath)
      $cleaned++
    }
  }

  if ($cleaned -eq 0) {
    Write-Host (Get-Msg "install.cleanup.legacy.none")
  } else {
    Write-Host (Get-Msg "install.cleanup.legacy.done" -Arg1 "$cleaned")
  }
}

function Install-CodexSkills {
  $skillsSrc = Join-Path $repoRoot "codex_skills"
  $codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE ".codex" }
  $skillsDst = Join-Path $codexHome "skills"

  if (-not (Test-Path $skillsSrc)) {
    return
  }

  if (-not (Test-Path $skillsDst)) {
    New-Item -ItemType Directory -Path $skillsDst -Force | Out-Null
  }

  Write-Host (Get-Msg "install.skill.installing_codex")
  Get-ChildItem -Path $skillsSrc -Directory | ForEach-Object {
    $skillName = $_.Name
    $srcDir = $_.FullName
    $dstDir = Join-Path $skillsDst $skillName
    $dstSkillMd = Join-Path $dstDir "SKILL.md"

    if (-not (Test-Path $dstDir)) {
      New-Item -ItemType Directory -Path $dstDir -Force | Out-Null
    }

    $srcSkillMd = $null
    if ($script:CCBLang -eq "zh") {
      $srcSkillMd = Join-Path $srcDir "SKILL.zh.md"
    }
    if (-not $srcSkillMd -or -not (Test-Path $srcSkillMd)) {
      $srcSkillMd = Join-Path $srcDir "SKILL.md.powershell"
      if (-not (Test-Path $srcSkillMd)) {
        $srcSkillMd = Join-Path $srcDir "SKILL.md"
      }
    }
    if (-not (Test-Path $srcSkillMd)) {
      return
    }

    Copy-Item -Force $srcSkillMd $dstSkillMd

    # Copy additional subdirectories (e.g., references/) if they exist
    Get-ChildItem -Path $srcDir -Directory | ForEach-Object {
      $subDirName = $_.Name
      $srcSubDir = $_.FullName
      $dstSubDir = Join-Path $dstDir $subDirName
      Copy-Item -Recurse -Force $srcSubDir $dstSubDir
    }

    Write-Host (Get-Msg "install.skill.updated_codex" -Arg1 $skillName)
  }
  Write-Host (Get-Msg "install.codex.updated_dir" -Arg1 $skillsDst)
}

function Install-DroidSkills {
  $skillsSrc = Join-Path $repoRoot "droid_skills"
  $factoryHome = if ($env:FACTORY_HOME) { $env:FACTORY_HOME } else { Join-Path $env:USERPROFILE ".factory" }
  $skillsDst = Join-Path $factoryHome "skills"

  if (-not (Test-Path $skillsSrc)) {
    return
  }

  if (-not (Get-Command droid -ErrorAction SilentlyContinue)) {
    return
  }

  if (-not (Test-Path $skillsDst)) {
    New-Item -ItemType Directory -Path $skillsDst -Force | Out-Null
  }

  Write-Host (Get-Msg "install.skill.installing_factory")
  Get-ChildItem -Path $skillsSrc -Directory | ForEach-Object {
    $skillName = $_.Name
    $srcDir = $_.FullName
    $dstDir = Join-Path $skillsDst $skillName

    $srcSkillMd = $null
    if ($script:CCBLang -eq "zh") {
      $srcSkillMd = Join-Path $srcDir "SKILL.zh.md"
    }
    if (-not $srcSkillMd -or -not (Test-Path $srcSkillMd)) {
      $srcSkillMd = Join-Path $srcDir "SKILL.md.powershell"
      if (-not (Test-Path $srcSkillMd)) {
        $srcSkillMd = Join-Path $srcDir "SKILL.md"
      }
    }
    if (-not (Test-Path $srcSkillMd)) {
      return
    }

    if (-not (Test-Path $dstDir)) {
      New-Item -ItemType Directory -Path $dstDir -Force | Out-Null
    }

    Copy-Item -Force $srcSkillMd (Join-Path $dstDir "SKILL.md")

    # Copy additional subdirectories
    Get-ChildItem -Path $srcDir -Directory | ForEach-Object {
      Copy-Item -Recurse -Force $_.FullName (Join-Path $dstDir $_.Name)
    }

    Write-Host (Get-Msg "install.skill.updated_factory" -Arg1 $skillName)
  }
  Write-Host (Get-Msg "install.factory.updated_dir" -Arg1 $skillsDst)
}

function Install-DroidDelegation {
  param(
    [string]$PythonCmd,
    [string]$InstallPrefix
  )

  if ($env:CCB_DROID_AUTOINSTALL -eq "0") {
    return
  }
  $droidCmd = Get-Command droid -ErrorAction SilentlyContinue
  if (-not $droidCmd) {
    return
  }
  $serverPath = Join-Path $InstallPrefix "mcp\\ccb-delegation\\server.py"
  if (-not (Test-Path $serverPath)) {
    Write-Host (Get-Msg "install.warn.prefix" -Arg1 (Get-Msg "install.droid.mcp.missing" -Arg1 $serverPath))
    return
  }
  if ($env:CCB_DROID_AUTOINSTALL_FORCE -eq "1") {
    try { & $droidCmd.Source "mcp" "remove" "ccb-delegation" | Out-Null } catch {}
  }
  try {
    & $droidCmd.Source "mcp" "add" "ccb-delegation" "--type" "stdio" $PythonCmd $serverPath | Out-Null
    Write-Host (Get-Msg "install.droid.mcp.registered")
  } catch {
    Write-Host (Get-Msg "install.warn.prefix" -Arg1 (Get-Msg "install.droid.mcp.failed" -Arg1 "$_"))
  }
}

function Install-ClaudeConfig {
  $claudeDir = Join-Path $env:USERPROFILE ".claude"
  $commandsDir = Join-Path $claudeDir "commands"
  $claudeMd = Join-Path $claudeDir "CLAUDE.md"
  $settingsJson = Join-Path $claudeDir "settings.json"

  if (-not (Test-Path $claudeDir)) {
    New-Item -ItemType Directory -Path $claudeDir -Force | Out-Null
  }
  if (-not (Test-Path $commandsDir)) {
    New-Item -ItemType Directory -Path $commandsDir -Force | Out-Null
  }

  $srcCommands = Join-Path $repoRoot "commands"
  if (Test-Path $srcCommands) {
    Get-ChildItem -Path $srcCommands -Filter "*.md" | ForEach-Object {
      Copy-Item -Force $_.FullName (Join-Path $commandsDir $_.Name)
    }
  }

  # Install skills
  $skillsDir = Join-Path $claudeDir "skills"
  $srcSkills = Join-Path $repoRoot "claude_skills"
  if (Test-Path $srcSkills) {
    if (-not (Test-Path $skillsDir)) {
      New-Item -ItemType Directory -Path $skillsDir -Force | Out-Null
    }
    Write-Host (Get-Msg "install.skill.installing_claude")
    Get-ChildItem -Path $srcSkills -Directory | ForEach-Object {
      if ($_.Name -eq "docs") { return }

      $skillName = $_.Name
      $srcDir = $_.FullName
      $dstDir = Join-Path $skillsDir $skillName
      $dstSkillMd = Join-Path $dstDir "SKILL.md"

      if (-not (Test-Path $dstDir)) {
        New-Item -ItemType Directory -Path $dstDir -Force | Out-Null
      }

      $srcSkillMd = $null
      if ($script:CCBLang -eq "zh") {
        $srcSkillMd = Join-Path $srcDir "SKILL.zh.md"
      }
      if (-not $srcSkillMd -or -not (Test-Path $srcSkillMd)) {
        $srcSkillMd = Join-Path $srcDir "SKILL.md.powershell"
        if (-not (Test-Path $srcSkillMd)) {
          $srcSkillMd = Join-Path $srcDir "SKILL.md"
        }
      }
      if (-not (Test-Path $srcSkillMd)) {
        return
      }

      Copy-Item -Force $srcSkillMd $dstSkillMd

      # Copy additional subdirectories (e.g., references/) if they exist
      Get-ChildItem -Path $srcDir -Directory | ForEach-Object {
        $subDirName = $_.Name
        $srcSubDir = $_.FullName
        $dstSubDir = Join-Path $dstDir $subDirName
        Copy-Item -Recurse -Force $srcSubDir $dstSubDir
      }

      Write-Host (Get-Msg "install.skill.updated" -Arg1 $skillName)
    }

    $srcDocs = Join-Path $srcSkills "docs"
    if (Test-Path $srcDocs) {
      $dstDocs = Join-Path $skillsDir "docs"
      if (Test-Path $dstDocs) { Remove-Item -Recurse -Force $dstDocs }
      Copy-Item -Recurse -Force $srcDocs $dstDocs
      Write-Host (Get-Msg "install.skill.docs_installed")
    }
  }

  $templateSuffix = if ($script:CCBLang -eq "zh") { ".zh" } else { "" }
  $claudeMdTemplate = Join-Path $installPrefix "config\claude-md-ccb$templateSuffix.md"
  if (-not (Test-Path $claudeMdTemplate)) {
    $claudeMdTemplate = Join-Path $installPrefix "config\claude-md-ccb.md"
  }
  if (-not (Test-Path $claudeMdTemplate)) {
    Write-Host (Get-Msg "install.warn.prefix" -Arg1 (Get-Msg "install.claude.template_missing" -Arg1 $claudeMdTemplate))
  } else {
    $codexRules = Get-Content -Raw $claudeMdTemplate

  if (Test-Path $claudeMd) {
    $content = Get-Content -Raw $claudeMd

    if ($content -match [regex]::Escape($script:CCB_START_MARKER)) {
      $pattern = '(?s)<!-- CCB_CONFIG_START -->.*?<!-- CCB_CONFIG_END -->'
      $newContent = [regex]::Replace($content, $pattern, $codexRules.Trim())
      $newContent | Out-File -Encoding UTF8 -FilePath $claudeMd
      Write-Host (Get-Msg "install.claude.updated")
    } elseif ($content -match '##\s+(Codex|Gemini|OpenCode)\s+Collaboration Rules' -or $content -match '##\s+(Codex|Gemini|OpenCode)\s+协作规则') {
      $patterns = @(
        '(?s)## Codex Collaboration Rules.*?(?=\n## (?!Gemini)|\Z)',
        '(?s)## Codex 协作规则.*?(?=\n## |\Z)',
        '(?s)## Gemini Collaboration Rules.*?(?=\n## |\Z)',
        '(?s)## Gemini 协作规则.*?(?=\n## |\Z)',
        '(?s)## OpenCode Collaboration Rules.*?(?=\n## |\Z)',
        '(?s)## OpenCode 协作规则.*?(?=\n## |\Z)'
      )
      foreach ($p in $patterns) {
        $content = [regex]::Replace($content, $p, '')
      }
      $content = ($content.TrimEnd() + "`n")
      ($content + $codexRules + "`n") | Out-File -Encoding UTF8 -FilePath $claudeMd
      Write-Host (Get-Msg "install.claude.updated")
    } else {
      Add-Content -Path $claudeMd -Value $codexRules
      Write-Host (Get-Msg "install.claude.updated")
    }
  } else {
    $codexRules | Out-File -Encoding UTF8 -FilePath $claudeMd
    Write-Host (Get-Msg "install.claude.created")
  }
  } # end claudeMdTemplate check

  $allowList = @(
    "Bash(ask:*)", "Bash(ccb-ping:*)", "Bash(pend:*)"
  )

  if (Test-Path $settingsJson) {
    try {
      $settings = Get-Content -Raw $settingsJson | ConvertFrom-Json
    } catch {
      $settings = @{}
    }
  } else {
    $settings = @{}
  }

  if (-not $settings.permissions) {
    $settings | Add-Member -NotePropertyName "permissions" -NotePropertyValue @{} -Force
  }
  if (-not $settings.permissions.allow) {
    $settings.permissions | Add-Member -NotePropertyName "allow" -NotePropertyValue @() -Force
  }

  $currentAllow = [System.Collections.ArrayList]@($settings.permissions.allow)
  $updated = $false
  foreach ($item in $allowList) {
    if ($currentAllow -notcontains $item) {
      $currentAllow.Add($item) | Out-Null
      $updated = $true
    }
  }

  if ($updated) {
    $settings.permissions.allow = $currentAllow.ToArray()
    $settings | ConvertTo-Json -Depth 10 | Out-File -Encoding UTF8 -FilePath $settingsJson
    Write-Host (Get-Msg "install.settings.updated")
  }

  # --- AGENTS.md injection ---
  $agentsMdTemplate = Join-Path $installPrefix "config\agents-md-ccb$templateSuffix.md"
  if (-not (Test-Path $agentsMdTemplate)) {
    $agentsMdTemplate = Join-Path $installPrefix "config\agents-md-ccb.md"
  }
  $agentsMd = Join-Path $installPrefix "AGENTS.md"
  if (Test-Path $agentsMdTemplate) {
    $templateContent = Get-Content -Raw $agentsMdTemplate
    if (Test-Path $agentsMd) {
      $agentsContent = Get-Content -Raw $agentsMd
      if ($agentsContent -match '<!-- CCB_ROLES_START -->' -or $agentsContent -match '<!-- REVIEW_RUBRICS_START -->') {
        $agentsContent = [regex]::Replace($agentsContent, '(?s)<!-- CCB_ROLES_START -->.*?<!-- CCB_ROLES_END -->', '')
        $agentsContent = [regex]::Replace($agentsContent, '(?s)<!-- REVIEW_RUBRICS_START -->.*?<!-- REVIEW_RUBRICS_END -->', '')
        $agentsContent = $agentsContent.TrimEnd() + "`n`n" + $templateContent.Trim() + "`n"
        $agentsContent | Out-File -Encoding UTF8 -FilePath $agentsMd
      } else {
        Add-Content -Path $agentsMd -Value ("`n" + $templateContent)
      }
    } else {
      $templateContent | Out-File -Encoding UTF8 -FilePath $agentsMd
    }
    Write-Host (Get-Msg "install.agents.updated")
  }

  # --- .clinerules injection ---
  $clinerulesTpl = Join-Path $installPrefix "config\clinerules-ccb$templateSuffix.md"
  if (-not (Test-Path $clinerulesTpl)) {
    $clinerulesTpl = Join-Path $installPrefix "config\clinerules-ccb.md"
  }
  $clinerules = Join-Path $installPrefix ".clinerules"
  if (Test-Path $clinerulesTpl) {
    $tplContent = Get-Content -Raw $clinerulesTpl
    if (Test-Path $clinerules) {
      $crContent = Get-Content -Raw $clinerules
      if ($crContent -match '<!-- CCB_ROLES_START -->') {
        $crContent = [regex]::Replace($crContent, '(?s)<!-- CCB_ROLES_START -->.*?<!-- CCB_ROLES_END -->', $tplContent.Trim())
        $crContent | Out-File -Encoding UTF8 -FilePath $clinerules
      } else {
        Add-Content -Path $clinerules -Value ("`n" + $tplContent)
      }
    } else {
      $tplContent | Out-File -Encoding UTF8 -FilePath $clinerules
    }
    Write-Host (Get-Msg "install.clinerules.updated")
  }
}

function Set-WezTermDefaultShellToPowerShell {
  $weztermCandidates = @(
    (Join-Path $env:USERPROFILE ".wezterm.lua"),
    (Join-Path $env:USERPROFILE ".config\\wezterm\\wezterm.lua")
  )
  $weztermConfig = $weztermCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
  if (-not $weztermConfig) {
    Write-Host (Get-Msg "install.wezterm.not_found")
    Write-Host (Get-Msg "install.wezterm.checked")
    $weztermCandidates | ForEach-Object { Write-Host (Get-Msg "install.wezterm.checked_entry" -Arg1 $_) }
    return
  }

  $pwsh = Get-Command pwsh.exe -ErrorAction SilentlyContinue
  $powershell = Get-Command powershell.exe -ErrorAction SilentlyContinue
  if ($pwsh) {
    $shellExe = "pwsh.exe"
    $fallbackExe = "powershell.exe"
  } elseif ($powershell) {
    $shellExe = "powershell.exe"
    $fallbackExe = "pwsh.exe"
  } else {
    Write-Host (Get-Msg "install.warn.prefix" -Arg1 (Get-Msg "install.wezterm.powershell_missing"))
    return
  }

  $content = Get-Content -Raw -Path $weztermConfig
  $hasDefaultProg = $content -match "default_prog\\s*="
  if ($hasDefaultProg) {
    return
  }
  $hasConfigVar = ($content -match "(?m)^\\s*(local\\s+)?config\\s*=") -or ($content -match "(?m)^\\s*return\\s+config\\s*$")
  if (-not $hasConfigVar) {
    Write-Host (Get-Msg "install.warn.prefix" -Arg1 (Get-Msg "install.wezterm.config_unrecognized"))
    Write-Host (Get-Msg "install.wezterm.suggested_snippet")
    Write-Host (Get-Msg "install.wezterm.snippet_line" -Arg1 $shellExe)
    return
  }

  $block = @"
$($script:CCB_WEZTERM_START_MARKER)
-- Set default shell to PowerShell (installed by ccb)
config.default_prog = { '$shellExe' }
-- Fallback (if '$shellExe' is not available): config.default_prog = { '$fallbackExe' }
$($script:CCB_WEZTERM_END_MARKER)
"@

  $alreadyPowerShell = $content -match "default_prog\\s*=\\s*\\{\\s*'?(pwsh\\.exe|powershell\\.exe)'?\\s*\\}"

  $shouldApply = $false
  if ($content -match [regex]::Escape($script:CCB_WEZTERM_START_MARKER)) {
    $shouldApply = $true
  } elseif (-not $hasDefaultProg) {
    $shouldApply = $true
  } elseif ($alreadyPowerShell) {
    Write-Host (Get-Msg "install.wezterm.already_configured")
    return
  } else {
    if ($Yes -or $env:CCB_INSTALL_ASSUME_YES -eq "1") {
      $shouldApply = $true
    } elseif ([Environment]::UserInteractive) {
      $reply = Read-Host (Get-Msg "install.wezterm.override_prompt" -Arg1 $shellExe)
      if ($reply.Trim().ToLower() -in @("y", "yes")) {
        $shouldApply = $true
      }
    }
  }

  if ($shouldApply) {
    if ($content -match [regex]::Escape($script:CCB_WEZTERM_START_MARKER)) {
      $pattern = "(?s)\\Q$($script:CCB_WEZTERM_START_MARKER)\\E.*?\\Q$($script:CCB_WEZTERM_END_MARKER)\\E"
      $newContent = [regex]::Replace($content, $pattern, $block)
    } elseif ($content -match "(?m)^\\s*return\\s+config\\s*$") {
      $newContent = [regex]::Replace($content, "(?m)^\\s*return\\s+config\\s*$", ($block + "`r`nreturn config"))
    } else {
      $newContent = ($content.TrimEnd() + "`r`n`r`n" + $block + "`r`n")
    }

    [System.IO.File]::WriteAllText($weztermConfig, $newContent, $script:utf8NoBom)
    Write-Host (Get-Msg "install.wezterm.configured" -Arg1 $shellExe -Arg2 $weztermConfig)
  } else {
    if ($hasDefaultProg -and -not $alreadyPowerShell -and ($content -notmatch "(?m)^\\s*--\\s*ccb:\\s*To use PowerShell as default shell")) {
      $hint = @"
-- ccb: To use PowerShell as default shell, set:
-- config.default_prog = { '$shellExe' }
"@
      if ($content -match "(?m)^\\s*return\\s+config\\s*$") {
        $newContent = [regex]::Replace($content, "(?m)^\\s*return\\s+config\\s*$", ($hint + "`r`nreturn config"))
      } else {
        $newContent = ($content.TrimEnd() + "`r`n`r`n" + $hint + "`r`n")
      }
      [System.IO.File]::WriteAllText($weztermConfig, $newContent, $script:utf8NoBom)
      Write-Host (Get-Msg "install.wezterm.hint_added" -Arg1 $weztermConfig)
      return
    }
    Write-Host (Get-Msg "install.wezterm.not_changed")
  }
}

function Uninstall-Native {
  $binDir = Join-Path $InstallPrefix "bin"

  # 1. Remove project directory
  if (Test-Path $InstallPrefix) {
    Remove-Item -Recurse -Force $InstallPrefix
    Write-Host (Get-Msg "install.uninstall.removed_prefix" -Arg1 $InstallPrefix)
  }

  # 2. Remove from user PATH
  $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
  if ($userPath) {
    $pathList = $userPath -split ";" | Where-Object { $_ }
    $binDirLower = $binDir.ToLower()
    $newPathList = $pathList | Where-Object { $_.ToLower() -ne $binDirLower }
    if ($newPathList.Count -ne $pathList.Count) {
      $newPath = $newPathList -join ";"
      [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
      Write-Host (Get-Msg "install.uninstall.removed_path" -Arg1 $binDir)
    }
  }

  # 3. Remove Claude skills
  $claudeSkillsDir = Join-Path $env:USERPROFILE ".claude\skills"
  $ccbSkills = @("ask", "cping", "ping", "pend", "autonew", "mounted", "all-plan", "docs")
  if (Test-Path $claudeSkillsDir) {
    Write-Host (Get-Msg "install.uninstall.removing_claude_skills")
    foreach ($skill in $ccbSkills) {
      $skillPath = Join-Path $claudeSkillsDir $skill
      if (Test-Path $skillPath) {
        Remove-Item -Recurse -Force $skillPath
        Write-Host (Get-Msg "install.uninstall.removed_skill" -Arg1 $skill)
      }
    }
  }

  # 4. Remove CLAUDE.md CCB config block
  $claudeMd = Join-Path $env:USERPROFILE ".claude\CLAUDE.md"
  if (Test-Path $claudeMd) {
    $content = Get-Content $claudeMd -Raw -Encoding UTF8
    if ($content -match $script:CCB_START_MARKER) {
      Write-Host (Get-Msg "install.uninstall.removing_claude_block")
      $pattern = "(?s)$([regex]::Escape($script:CCB_START_MARKER)).*?$([regex]::Escape($script:CCB_END_MARKER))\r?\n?"
      $content = $content -replace $pattern, ""
      $content = $content.Trim() + "`n"
      [System.IO.File]::WriteAllText($claudeMd, $content, $script:utf8NoBom)
      Write-Host (Get-Msg "install.uninstall.removed_claude_block")
    }
  }

  # 5. Remove settings.json permissions
  $settingsFile = Join-Path $env:USERPROFILE ".claude\settings.json"
  if (Test-Path $settingsFile) {
    $permsToRemove = @("Bash(ask:*)", "Bash(ping:*)", "Bash(ccb-ping:*)", "Bash(pend:*)")
    try {
      $settings = Get-Content $settingsFile -Raw -Encoding UTF8 | ConvertFrom-Json
      if ($settings.permissions -and $settings.permissions.allow) {
        $originalCount = $settings.permissions.allow.Count
        $settings.permissions.allow = @($settings.permissions.allow | Where-Object { $_ -notin $permsToRemove })
        if ($settings.permissions.allow.Count -ne $originalCount) {
          $settings | ConvertTo-Json -Depth 10 | Set-Content $settingsFile -Encoding UTF8
          Write-Host (Get-Msg "install.uninstall.permissions_removed")
        }
      }
    } catch {
      Write-Host (Get-Msg "install.warn.prefix" -Arg1 (Get-Msg "install.uninstall.settings_clean_failed" -Arg1 "$_"))
    }
  }

  # 6. Remove Codex skills
  $codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE ".codex" }
  $codexSkillsDir = Join-Path $codexHome "skills"
  if (Test-Path $codexSkillsDir) {
    Write-Host (Get-Msg "install.uninstall.removing_codex_skills")
    foreach ($skill in $ccbSkills) {
      $skillPath = Join-Path $codexSkillsDir $skill
      if (Test-Path $skillPath) {
        Remove-Item -Recurse -Force $skillPath
        Write-Host (Get-Msg "install.uninstall.removed_skill" -Arg1 $skill)
      }
    }
  }

  # 7. Remove Droid skills
  $factoryHome = if ($env:FACTORY_HOME) { $env:FACTORY_HOME } else { Join-Path $env:USERPROFILE ".factory" }
  $droidSkillsDir = Join-Path $factoryHome "skills"
  if (Test-Path $droidSkillsDir) {
    Write-Host (Get-Msg "install.uninstall.removing_droid_skills")
    foreach ($skill in $ccbSkills) {
      $skillPath = Join-Path $droidSkillsDir $skill
      if (Test-Path $skillPath) {
        Remove-Item -Recurse -Force $skillPath
        Write-Host (Get-Msg "install.uninstall.removed_skill" -Arg1 $skill)
      }
    }
  }

  # 8. Remove WezTerm config block
  $weztermConfig = Join-Path $env:USERPROFILE ".wezterm.lua"
  if (Test-Path $weztermConfig) {
    $content = Get-Content $weztermConfig -Raw -Encoding UTF8
    if ($content -match $script:CCB_WEZTERM_START_MARKER) {
      Write-Host (Get-Msg "install.uninstall.removing_wezterm_block")
      $pattern = "(?s)\r?\n?$([regex]::Escape($script:CCB_WEZTERM_START_MARKER)).*?$([regex]::Escape($script:CCB_WEZTERM_END_MARKER))\r?\n?"
      $content = $content -replace $pattern, "`n"
      $content = $content.Trim() + "`n"
      [System.IO.File]::WriteAllText($weztermConfig, $content, $script:utf8NoBom)
      Write-Host (Get-Msg "install.uninstall.removed_wezterm_block")
    }
  }

  Write-Host (Get-Msg "install.uninstall_complete")
}

if ($Command -eq "help") {
  Show-Usage
  exit 0
}

if ($Command -eq "install") {
  Install-Native
  exit 0
}

if ($Command -eq "uninstall") {
  Uninstall-Native
  exit 0
}
