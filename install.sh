#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_PREFIX="${CODEX_INSTALL_PREFIX:-$HOME/.local/share/codex-dual}"
BIN_DIR="${CODEX_BIN_DIR:-$HOME/.local/bin}"
readonly REPO_ROOT INSTALL_PREFIX BIN_DIR

# i18n support
detect_lang() {
  local lang="${CCB_LANG:-auto}"
  case "$lang" in
    zh|cn|chinese) echo "zh" ;;
    en|english) echo "en" ;;
    *)
      local sys_lang="${LANG:-${LC_ALL:-${LC_MESSAGES:-}}}"
      if [[ "$sys_lang" == zh* ]] || [[ "$sys_lang" == *chinese* ]]; then
        echo "zh"
      else
        echo "en"
      fi
      ;;
  esac
}

CCB_LANG_DETECTED="$(detect_lang)"

localized_skill_template() {
  local skill_dir="$1"
  if [[ "$CCB_LANG_DETECTED" == "zh" ]] && [[ -f "$skill_dir/SKILL.zh.md" ]]; then
    echo "$skill_dir/SKILL.zh.md"
    return
  fi
  if [[ -f "$skill_dir/SKILL.md.bash" ]]; then
    echo "$skill_dir/SKILL.md.bash"
    return
  fi
  if [[ -f "$skill_dir/SKILL.md" ]]; then
    echo "$skill_dir/SKILL.md"
    return
  fi
}

localized_config_template() {
  local base_name="$1"
  local zh_candidate="$INSTALL_PREFIX/config/${base_name}.zh"
  local default_candidate="$INSTALL_PREFIX/config/${base_name}"

  if [[ "$CCB_LANG_DETECTED" == "zh" ]]; then
    case "$base_name" in
      *.md)
        zh_candidate="$INSTALL_PREFIX/config/${base_name%.md}.zh.md"
        ;;
      *.conf)
        zh_candidate="$INSTALL_PREFIX/config/${base_name%.conf}.zh.conf"
        ;;
    esac
    if [[ -f "$zh_candidate" ]]; then
      echo "$zh_candidate"
      return
    fi
  fi

  echo "$default_candidate"
}

# Message function
msg() {
  local key="$1"
  shift
  local en_msg zh_msg
  case "$key" in
    install_complete) key="install.complete" ;;
    uninstall_complete) key="install.uninstall.complete" ;;
    python_version_old) key="install.python.version_old" ;;
    requires_python) key="install.python.requires" ;;
    missing_dep) key="install.dependency.missing" ;;
    detected_env) key="install.environment.detected" ;;
    confirm_wsl) key="install.backend.confirm_wsl_prompt" ;;
    cancelled) key="install.backend.cancelled" ;;
    wsl_warning) key="install.backend.wsl_warning" ;;
    same_env_required) key="install.backend.same_env_required" ;;
    confirm_wsl_native) key="install.backend.confirm_wsl_native" ;;
    wezterm_recommended) key="install.wezterm.recommended" ;;
    watchdog_installing) key="install.watchdog.installing" ;;
    watchdog_installed) key="install.watchdog.installed" ;;
    watchdog_failed) key="install.watchdog.failed" ;;
    pip_missing) key="install.pip.missing" ;;
    root_error) key="install.error.root" ;;
  esac
  case "$key" in
    "install.complete")
      en_msg="Installation complete"
      zh_msg="安装完成" ;;
    "install.uninstall.complete")
      en_msg="Uninstall complete"
      zh_msg="卸载完成" ;;
    "install.error.root")
      en_msg="ERROR: Do not run as root/sudo. Please run as normal user."
      zh_msg="错误：请勿以 root/sudo 身份运行。请使用普通用户执行。" ;;
    "install.ui.separator")
      en_msg="================================================================"
      zh_msg="================================================================" ;;
    "install.usage.title")
      en_msg="Usage:"
      zh_msg="用法：" ;;
    "install.usage.install")
      en_msg="  ./install.sh install    # Install or update Codex dual-window tools"
      zh_msg="  ./install.sh install    # 安装或更新 Codex 双窗工具" ;;
    "install.usage.uninstall")
      en_msg="  ./install.sh uninstall  # Uninstall installed content"
      zh_msg="  ./install.sh uninstall  # 卸载已安装内容" ;;
    "install.usage.env_title")
      en_msg="Optional environment variables:"
      zh_msg="可选环境变量：" ;;
    "install.usage.install_prefix")
      en_msg="  CODEX_INSTALL_PREFIX     Install directory (default: ~/.local/share/codex-dual)"
      zh_msg="  CODEX_INSTALL_PREFIX     安装目录（默认：~/.local/share/codex-dual）" ;;
    "install.usage.bin_dir")
      en_msg="  CODEX_BIN_DIR            Executable directory (default: ~/.local/bin)"
      zh_msg="  CODEX_BIN_DIR            可执行目录（默认：~/.local/bin）" ;;
    "install.usage.claude_dir")
      en_msg="  CODEX_CLAUDE_COMMAND_DIR Custom Claude commands directory (default: auto-detect)"
      zh_msg="  CODEX_CLAUDE_COMMAND_DIR 自定义 Claude commands 目录（默认：自动检测）" ;;
    "install.usage.droid_autoinstall")
      en_msg="  CCB_DROID_AUTOINSTALL    Auto-register Droid MCP tools if droid exists (default: 1)"
      zh_msg="  CCB_DROID_AUTOINSTALL    若存在 droid，则自动注册 Droid MCP 工具（默认：1）" ;;
    "install.usage.droid_force")
      en_msg="  CCB_DROID_AUTOINSTALL_FORCE Re-register Droid MCP tools (default: 0)"
      zh_msg="  CCB_DROID_AUTOINSTALL_FORCE 重新注册 Droid MCP 工具（默认：0）" ;;
    "install.usage.claude_md_mode")
      en_msg="  CCB_CLAUDE_MD_MODE       CLAUDE.md injection mode: \"inline\" (default) or \"route\""
      zh_msg="  CCB_CLAUDE_MD_MODE       CLAUDE.md 注入模式：`inline`（默认）或 `route`" ;;
    "install.usage.claude_md_mode_inline")
      en_msg="                           inline = full config in CLAUDE.md (~57 lines)"
      zh_msg="                           inline = 在 CLAUDE.md 中写入完整配置（约 57 行）" ;;
    "install.usage.claude_md_mode_route")
      en_msg="                           route  = minimal pointer in CLAUDE.md, full config in ~/.claude/rules/ccb-config.md"
      zh_msg="                           route  = CLAUDE.md 中保留指针，完整配置写入 ~/.claude/rules/ccb-config.md" ;;
    "install.dependency.missing")
      en_msg="ERROR: Missing dependency: $1"
      zh_msg="错误：缺少依赖：$1" ;;
    "install.dependency.install_first")
      en_msg="   Please install $1 first, then re-run install.sh"
      zh_msg="   请先安装 $1，然后重新执行 install.sh" ;;
    "install.python.missing")
      en_msg="ERROR: Missing dependency: python (3.10+ required)"
      zh_msg="错误：缺少依赖：python（需要 3.10+）" ;;
    "install.python.install_hint")
      en_msg="   Please install Python 3.10+ and ensure it is on PATH, then re-run install.sh"
      zh_msg="   请安装 Python 3.10+ 并确保其在 PATH 中，然后重新执行 install.sh" ;;
    "install.python.version_old")
      en_msg="Python version too old: $1"
      zh_msg="Python 版本过旧：$1" ;;
    "install.python.requires")
      en_msg="Requires Python 3.10+"
      zh_msg="需要 Python 3.10+" ;;
    "install.python.upgrade_hint")
      en_msg="   Requires Python 3.10+, please upgrade and retry"
      zh_msg="   需要 Python 3.10+，请升级后重试" ;;
    "install.python.ok")
      en_msg="OK: Python $1 ($2)"
      zh_msg="OK：Python $1 ($2)" ;;
    "install.environment.detected")
      en_msg="Detected $1 environment"
      zh_msg="检测到 $1 环境" ;;
    "install.watchdog.installing")
      en_msg="Installing Python dependency: watchdog"
      zh_msg="正在安装 Python 依赖：watchdog" ;;
    "install.watchdog.installed")
      en_msg="OK: watchdog installed"
      zh_msg="OK：watchdog 已安装" ;;
    "install.watchdog.failed")
      en_msg="WARN: watchdog install failed (will fall back to polling)"
      zh_msg="警告：watchdog 安装失败（将退回轮询）" ;;
    "install.pip.missing")
      en_msg="WARN: pip not available; please install watchdog manually"
      zh_msg="警告：未找到 pip，请手动安装 watchdog" ;;
    "install.backend.non_interactive")
      en_msg="ERROR: Installing in WSL but detected non-interactive terminal; aborted to avoid env mismatch."
      zh_msg="错误：在 WSL 中安装时检测到非交互终端；为避免环境错配已中止。" ;;
    "install.backend.non_interactive_hint")
      en_msg="   If you confirm codex/gemini will be installed and run in WSL:"
      zh_msg="   如果你确认 codex/gemini 将在 WSL 中安装并运行：" ;;
    "install.backend.non_interactive_retry")
      en_msg="   Re-run: CCB_INSTALL_ASSUME_YES=1 ./install.sh install"
      zh_msg="   请重新执行：CCB_INSTALL_ASSUME_YES=1 ./install.sh install" ;;
    "install.backend.wsl_warning")
      en_msg="WARN: Detected WSL environment"
      zh_msg="警告：检测到 WSL 环境" ;;
    "install.backend.same_env_required")
      en_msg="ccb/ask/ping/pend must run in the same environment as codex/gemini."
      zh_msg="ccb/ask/ping/pend 必须与 codex/gemini 在同一环境运行。" ;;
    "install.backend.confirm_wsl_native")
      en_msg="Please confirm: you will install and run codex/gemini in WSL (not Windows native)."
      zh_msg="请确认：你将在 WSL 中安装并运行 codex/gemini（不是 Windows 原生）。" ;;
    "install.backend.windows_hint")
      en_msg="If you plan to run codex/gemini in Windows native, exit and run on Windows side:"
      zh_msg="如果你打算在 Windows 原生环境运行 codex/gemini，请退出并在 Windows 侧执行：" ;;
    "install.backend.windows_command")
      en_msg="   powershell -ExecutionPolicy Bypass -File .\\install.ps1 install"
      zh_msg="   powershell -ExecutionPolicy Bypass -File .\\install.ps1 install" ;;
    "install.backend.confirm_wsl_prompt")
      en_msg="Confirm continue installing in WSL? (y/N)"
      zh_msg="确认继续在 WSL 中安装？(y/N)" ;;
    "install.backend.cancelled")
      en_msg="Installation cancelled"
      zh_msg="安装已取消" ;;
    "install.tmux.macos_brew")
      en_msg="   macOS: Run 'brew install tmux'"
      zh_msg="   macOS：执行 `brew install tmux`" ;;
    "install.tmux.macos_no_brew")
      en_msg="   macOS: Homebrew not detected, install from https://brew.sh then run 'brew install tmux'"
      zh_msg="   macOS：未检测到 Homebrew，请先安装 https://brew.sh 然后执行 `brew install tmux`" ;;
    "install.tmux.debian")
      en_msg="   Debian/Ubuntu: sudo apt-get update && sudo apt-get install -y tmux"
      zh_msg="   Debian/Ubuntu：sudo apt-get update && sudo apt-get install -y tmux" ;;
    "install.tmux.dnf")
      en_msg="   Fedora/CentOS/RHEL: sudo dnf install -y tmux"
      zh_msg="   Fedora/CentOS/RHEL：sudo dnf install -y tmux" ;;
    "install.tmux.yum")
      en_msg="   CentOS/RHEL: sudo yum install -y tmux"
      zh_msg="   CentOS/RHEL：sudo yum install -y tmux" ;;
    "install.tmux.pacman")
      en_msg="   Arch/Manjaro: sudo pacman -S tmux"
      zh_msg="   Arch/Manjaro：sudo pacman -S tmux" ;;
    "install.tmux.apk")
      en_msg="   Alpine: sudo apk add tmux"
      zh_msg="   Alpine：sudo apk add tmux" ;;
    "install.tmux.zypper")
      en_msg="   openSUSE: sudo zypper install -y tmux"
      zh_msg="   openSUSE：sudo zypper install -y tmux" ;;
    "install.tmux.generic")
      en_msg="   Linux: Please use your distro's package manager to install tmux"
      zh_msg="   Linux：请使用你的发行版包管理器安装 tmux" ;;
    "install.tmux.docs")
      en_msg="   See https://github.com/tmux/tmux/wiki/Installing for tmux installation"
      zh_msg="   参考 https://github.com/tmux/tmux/wiki/Installing 安装 tmux" ;;
    "install.backend.wezterm_env_override")
      en_msg="OK: Detected WezTerm environment ($1)"
      zh_msg="OK：检测到 WezTerm 环境（$1）" ;;
    "install.backend.wezterm_env")
      en_msg="OK: Detected WezTerm environment"
      zh_msg="OK：检测到 WezTerm 环境" ;;
    "install.backend.tmux_env")
      en_msg="OK: Detected tmux environment"
      zh_msg="OK：检测到 tmux 环境" ;;
    "install.backend.wezterm_override")
      en_msg="OK: Detected WezTerm ($1)"
      zh_msg="OK：检测到 WezTerm（$1）" ;;
    "install.backend.wezterm")
      en_msg="OK: Detected WezTerm"
      zh_msg="OK：检测到 WezTerm" ;;
    "install.backend.wezterm_program_files")
      en_msg="OK: Detected WezTerm (/mnt/c/Program Files/WezTerm/wezterm.exe)"
      zh_msg="OK：检测到 WezTerm（/mnt/c/Program Files/WezTerm/wezterm.exe）" ;;
    "install.backend.wezterm_program_files_x86")
      en_msg="OK: Detected WezTerm (/mnt/c/Program Files (x86)/WezTerm/wezterm.exe)"
      zh_msg="OK：检测到 WezTerm（/mnt/c/Program Files (x86)/WezTerm/wezterm.exe）" ;;
    "install.backend.tmux_recommended")
      en_msg="OK: Detected tmux (recommend also installing WezTerm for better experience)"
      zh_msg="OK：检测到 tmux（建议同时安装 WezTerm 以获得更好体验）" ;;
    "install.backend.missing")
      en_msg="ERROR: Missing dependency: WezTerm or tmux (at least one required)"
      zh_msg="错误：缺少依赖：WezTerm 或 tmux（至少需要一个）" ;;
    "install.backend.website")
      en_msg="   WezTerm website: https://wezfurlong.org/wezterm/"
      zh_msg="   WezTerm 网站：https://wezfurlong.org/wezterm/" ;;
    "install.backend.macos_note")
      en_msg="NOTE: macOS user recommended options:"
      zh_msg="提示：macOS 用户推荐方案：" ;;
    "install.backend.macos_tmux")
      en_msg="   - Install tmux: brew install tmux"
      zh_msg="   - 安装 tmux：brew install tmux" ;;
    "install.wezterm.recommended")
      en_msg="Recommend installing WezTerm as terminal frontend"
      zh_msg="推荐安装 WezTerm 作为终端前端" ;;
    "install.wezterm.cached")
      en_msg="OK: WezTerm path cached: $1"
      zh_msg="OK：已缓存 WezTerm 路径：$1" ;;
    "install.link.script_missing")
      en_msg="WARN: Script not found $1, skipping link creation"
      zh_msg="警告：未找到脚本 $1，跳过创建链接" ;;
    "install.link.created")
      en_msg="Created executable links in $1"
      zh_msg="已在 $1 创建可执行链接" ;;
    "install.path.already_configured")
      en_msg="PATH already configured in $1 (restart terminal to apply)"
      zh_msg="PATH 已在 $1 中配置（重启终端后生效）" ;;
    "install.path.added")
      en_msg="OK: Added $1 to PATH in $2"
      zh_msg="OK：已将 $1 添加到 $2 的 PATH" ;;
    "install.path.reload_hint")
      en_msg="   Run: source $1  (or restart terminal)"
      zh_msg="   执行：source $1（或重启终端）" ;;
    "install.commands.removed")
      en_msg="  Removed obsolete command: $1"
      zh_msg="  已移除废弃命令：$1" ;;
    "install.commands.updated_dir")
      en_msg="Updated Claude commands directory: $1"
      zh_msg="已更新 Claude commands 目录：$1" ;;
    "install.skill.removed")
      en_msg="  Removed obsolete skill: $1"
      zh_msg="  已移除废弃 skill：$1" ;;
    "install.skill.installing_claude")
      en_msg="Installing Claude skills (bash SKILL.md templates)..."
      zh_msg="正在安装 Claude skills（bash SKILL.md 模板）..." ;;
    "install.skill.installing_codex")
      en_msg="Installing Codex skills (bash SKILL.md templates)..."
      zh_msg="正在安装 Codex skills（bash SKILL.md 模板）..." ;;
    "install.skill.installing_droid")
      en_msg="Installing Droid/Factory skills..."
      zh_msg="正在安装 Droid/Factory skills..." ;;
    "install.skill.updated")
      en_msg="  Updated skill: $1"
      zh_msg="  已更新 skill：$1" ;;
    "install.skill.updated_codex")
      en_msg="  Updated Codex skill: $1"
      zh_msg="  已更新 Codex skill：$1" ;;
    "install.skill.updated_factory")
      en_msg="  Updated Factory skill: $1"
      zh_msg="  已更新 Factory skill：$1" ;;
    "install.skill.docs_installed")
      en_msg="  Installed skills docs: docs/"
      zh_msg="  已安装 skills 文档：docs/" ;;
    "install.skill.updated_dir")
      en_msg="Updated Claude skills directory: $1"
      zh_msg="已更新 Claude skills 目录：$1" ;;
    "install.skill.updated_codex_dir")
      en_msg="Updated Codex skills directory: $1"
      zh_msg="已更新 Codex skills 目录：$1" ;;
    "install.skill.updated_factory_dir")
      en_msg="Updated Factory skills directory: $1"
      zh_msg="已更新 Factory skills 目录：$1" ;;
    "install.droid.python_missing")
      en_msg="WARN: python required for Droid MCP setup; skipping"
      zh_msg="警告：Droid MCP 配置需要 python，已跳过" ;;
    "install.droid.server_missing")
      en_msg="WARN: Droid MCP server not found at $1; skipping"
      zh_msg="警告：未找到 Droid MCP server：$1，已跳过" ;;
    "install.droid.registered")
      en_msg="OK: Droid MCP delegation registered"
      zh_msg="OK：Droid MCP delegation 已注册" ;;
    "install.droid.register_failed")
      en_msg="WARN: Failed to register Droid MCP delegation (already registered or droid config unavailable)"
      zh_msg="警告：注册 Droid MCP delegation 失败（可能已注册或 droid 配置不可用）" ;;
    "install.mcp.python_required")
      en_msg="WARN: python required to detect MCP configuration"
      zh_msg="警告：检测 MCP 配置需要 python" ;;
    "install.mcp.detected_conflict")
      en_msg="WARN: Detected codex-related MCP configuration, removing to avoid conflicts..."
      zh_msg="警告：检测到与 codex 相关的 MCP 配置，正在移除以避免冲突..." ;;
    "install.mcp.cleaned")
      en_msg="OK: Codex MCP configuration cleaned"
      zh_msg="OK：已清理 Codex MCP 配置" ;;
    "install.claude_md.python_required")
      en_msg="ERROR: python required to update CLAUDE.md"
      zh_msg="错误：更新 CLAUDE.md 需要 python" ;;
    "install.claude_md.template_missing")
      en_msg="WARN: Template not found: $1; skipping CLAUDE.md injection"
      zh_msg="警告：未找到模板：$1，跳过 CLAUDE.md 注入" ;;
    "install.claude_md.external_written")
      en_msg="Wrote full CCB config to $1"
      zh_msg="已将完整 CCB 配置写入 $1" ;;
    "install.claude_md.updating")
      en_msg="Updating existing CCB config block (mode: $1)..."
      zh_msg="正在更新现有 CCB 配置块（模式：$1）..." ;;
    "install.claude_md.removing_legacy")
      en_msg="Removing legacy rules and adding new CCB config block..."
      zh_msg="正在移除旧规则并添加新的 CCB 配置块..." ;;
    "install.claude_md.updated")
      en_msg="Updated AI collaboration rules in $1 (mode: $2)"
      zh_msg="已更新 $1 中的 AI 协作规则（模式：$2）" ;;
    "install.agents.python_required")
      en_msg="WARN: python required to update AGENTS.md; skipping"
      zh_msg="警告：更新 AGENTS.md 需要 python，已跳过" ;;
    "install.agents.template_missing")
      en_msg="WARN: Template not found: $1; skipping AGENTS.md injection"
      zh_msg="警告：未找到模板：$1，跳过 AGENTS.md 注入" ;;
    "install.agents.updating")
      en_msg="Updating existing CCB blocks in AGENTS.md..."
      zh_msg="正在更新 AGENTS.md 中现有的 CCB 配置块..." ;;
    "install.agents.updated")
      en_msg="Updated AGENTS.md: $1"
      zh_msg="已更新 AGENTS.md：$1" ;;
    "install.clinerules.python_required")
      en_msg="WARN: python required to update .clinerules; skipping"
      zh_msg="警告：更新 .clinerules 需要 python，已跳过" ;;
    "install.clinerules.template_missing")
      en_msg="WARN: Template not found: $1; skipping .clinerules injection"
      zh_msg="警告：未找到模板：$1，跳过 .clinerules 注入" ;;
    "install.clinerules.updating")
      en_msg="Updating existing CCB roles block in .clinerules..."
      zh_msg="正在更新 .clinerules 中现有的 CCB 角色块..." ;;
    "install.clinerules.updated")
      en_msg="Updated .clinerules: $1"
      zh_msg="已更新 .clinerules：$1" ;;
    "install.settings.created")
      en_msg="Created $1 with permissions"
      zh_msg="已创建带权限配置的 $1" ;;
    "install.settings.updated")
      en_msg="Updated $1 permissions"
      zh_msg="已更新 $1 的权限配置" ;;
    "install.tmux.updated")
      en_msg="Updated tmux configuration: $1"
      zh_msg="已更新 tmux 配置：$1" ;;
    "install.tmux.reloaded")
      en_msg="Reloaded tmux configuration in running server."
      zh_msg="已在运行中的 tmux server 中重新加载配置。" ;;
    "install.tmux.reload_failed")
      en_msg="WARN: Failed to reload tmux configuration automatically; run: tmux source $1"
      zh_msg="警告：自动重载 tmux 配置失败；请执行：tmux source $1" ;;
    "install.tmux.removing")
      en_msg="Removing CCB tmux configuration from $1..."
      zh_msg="正在从 $1 移除 CCB tmux 配置..." ;;
    "install.tmux.removed")
      en_msg="Removed CCB tmux configuration from $1"
      zh_msg="已从 $1 移除 CCB tmux 配置" ;;
    "install.wezterm.note")
      en_msg="NOTE: Recommend installing WezTerm as terminal frontend (better experience, recommended for WSL2/Windows)"
      zh_msg="提示：推荐安装 WezTerm 作为终端前端（体验更好，尤其推荐 WSL2/Windows）" ;;
    "install.wezterm.site")
      en_msg="   - Website: https://wezfurlong.org/wezterm/"
      zh_msg="   - 网站：https://wezfurlong.org/wezterm/" ;;
    "install.wezterm.benefit")
      en_msg="   - Benefits: Smoother split/scroll/font rendering, more stable bridging in WezTerm mode"
      zh_msg="   - 优势：分屏/滚动/字体渲染更顺滑，WezTerm 模式下桥接更稳定" ;;
    "install.uninstall.remove_claude_md")
      en_msg="Removing CCB config block from CLAUDE.md..."
      zh_msg="正在从 CLAUDE.md 移除 CCB 配置块..." ;;
    "install.uninstall.removed_claude_md")
      en_msg="Removed CCB config from CLAUDE.md"
      zh_msg="已从 CLAUDE.md 移除 CCB 配置" ;;
    "install.uninstall.python_required_claude_md")
      en_msg="WARN: python required to clean CLAUDE.md, please manually remove CCB_CONFIG block"
      zh_msg="警告：清理 CLAUDE.md 需要 python，请手动移除 CCB_CONFIG 配置块" ;;
    "install.uninstall.remove_legacy_rules")
      en_msg="Removing legacy collaboration rules from CLAUDE.md..."
      zh_msg="正在从 CLAUDE.md 移除旧版协作规则..." ;;
    "install.uninstall.removed_legacy_rules")
      en_msg="Removed collaboration rules from CLAUDE.md"
      zh_msg="已从 CLAUDE.md 移除协作规则" ;;
    "install.uninstall.python_required_legacy_rules")
      en_msg="WARN: python required to clean CLAUDE.md, please manually remove collaboration rules"
      zh_msg="警告：清理 CLAUDE.md 需要 python，请手动移除协作规则" ;;
    "install.uninstall.removed_external_config")
      en_msg="Removed external CCB config: $1"
      zh_msg="已移除外部 CCB 配置：$1" ;;
    "install.uninstall.removed_permissions")
      en_msg="Removed permission configuration from settings.json"
      zh_msg="已从 settings.json 移除权限配置" ;;
    "install.uninstall.python_required_permissions")
      en_msg="WARN: python required to clean settings.json, please manually remove related permissions"
      zh_msg="警告：清理 settings.json 需要 python，请手动移除相关权限" ;;
    "install.uninstall.remove_claude_skills")
      en_msg="Removing CCB Claude skills..."
      zh_msg="正在移除 CCB Claude skills..." ;;
    "install.uninstall.remove_codex_skills")
      en_msg="Removing CCB Codex skills..."
      zh_msg="正在移除 CCB Codex skills..." ;;
    "install.uninstall.remove_droid_skills")
      en_msg="Removing CCB Droid skills..."
      zh_msg="正在移除 CCB Droid skills..." ;;
    "install.uninstall.remove_droid_commands")
      en_msg="Removing CCB Droid commands..."
      zh_msg="正在移除 CCB Droid commands..." ;;
    "install.cleanup.start")
      en_msg="Cleaning up legacy files..."
      zh_msg="正在清理遗留文件..." ;;
    "install.cleanup.removed_daemon")
      en_msg="  Removed legacy daemon script: $1"
      zh_msg="  已移除遗留守护进程脚本：$1" ;;
    "install.cleanup.removed_state")
      en_msg="  Removed legacy state file: $1"
      zh_msg="  已移除遗留状态文件：$1" ;;
    "install.cleanup.removed_module")
      en_msg="  Removed legacy module: $1"
      zh_msg="  已移除遗留模块：$1" ;;
    "install.cleanup.none")
      en_msg="  No legacy files found"
      zh_msg="  未发现遗留文件" ;;
    "install.cleanup.done")
      en_msg="  Cleaned up $1 legacy file(s)"
      zh_msg="  已清理 $1 个遗留文件" ;;
    "install.summary.ok")
      en_msg="OK: Installation complete"
      zh_msg="OK：安装完成" ;;
    "install.summary.project_dir")
      en_msg="   Project dir    : $1"
      zh_msg="   项目目录       : $1" ;;
    "install.summary.bin_dir")
      en_msg="   Executable dir : $1"
      zh_msg="   可执行目录     : $1" ;;
    "install.summary.commands")
      en_msg="   Claude commands updated"
      zh_msg="   Claude commands 已更新" ;;
    "install.summary.claude_route")
      en_msg="   Global CLAUDE.md configured with CCB route pointer (full config in ~/.claude/rules/ccb-config.md)"
      zh_msg="   已为全局 CLAUDE.md 配置 CCB route 指针（完整配置在 ~/.claude/rules/ccb-config.md）" ;;
    "install.summary.claude_inline")
      en_msg="   Global CLAUDE.md configured with CCB collaboration rules (inline)"
      zh_msg="   已为全局 CLAUDE.md 配置 CCB 协作规则（inline）" ;;
    "install.summary.agents")
      en_msg="   AGENTS.md configured with review rubrics"
      zh_msg="   已配置 AGENTS.md 的 review rubrics" ;;
    "install.summary.clinerules")
      en_msg="   .clinerules configured with role assignments"
      zh_msg="   已配置 .clinerules 的角色分配" ;;
    "install.summary.settings")
      en_msg="   Global settings.json permissions added"
      zh_msg="   已添加全局 settings.json 权限" ;;
    "install.uninstall.start")
      en_msg="INFO: Starting ccb uninstall..."
      zh_msg="信息：开始卸载 ccb..." ;;
    "install.uninstall.project_removed")
      en_msg="Removed project directory: $1"
      zh_msg="已移除项目目录：$1" ;;
    "install.uninstall.bin_removed")
      en_msg="Removed bin links: $1"
      zh_msg="已移除 bin 链接：$1" ;;
    "install.uninstall.commands_cleaned")
      en_msg="Cleaned commands directory: $1"
      zh_msg="已清理 commands 目录：$1" ;;
    "install.uninstall.ok")
      en_msg="OK: Uninstall complete"
      zh_msg="OK：卸载完成" ;;
    "install.uninstall.note")
      en_msg="   NOTE: Dependencies (python, tmux, wezterm) were not removed"
      zh_msg="   注意：依赖（python、tmux、wezterm）不会被自动移除" ;;
    *)
      en_msg="$key"
      zh_msg="$key" ;;
  esac
  if [[ "$CCB_LANG_DETECTED" == "zh" ]]; then
    echo "$zh_msg"
  else
    echo "$en_msg"
  fi
}

# Check for root/sudo - refuse to run as root
if [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
  msg "install.error.root" >&2
  exit 1
fi

SCRIPTS_TO_LINK=(
  bin/cask
  bin/cpend
  bin/cping
  bin/gask
  bin/gpend
  bin/gping
  bin/oask
  bin/opend
  bin/oping
  bin/lask
  bin/lpend
  bin/lping
  bin/dask
  bin/dpend
  bin/dping
  bin/hask
  bin/hpend
  bin/hping
  bin/bask
  bin/bpend
  bin/bping
  bin/qask
  bin/qpend
  bin/qping
  bin/ask
  bin/ccb-ping
  bin/pend
  bin/autonew
  bin/ccb-completion-hook
  bin/maild
  bin/ctx-transfer
  ccb
)

CLAUDE_MARKDOWN=(
  # Old CCB commands removed - replaced by unified ask/ping/pend skills
)

LEGACY_SCRIPTS=(
  ping
  cast
  cast-w
  codex-ask
  codex-pending
  codex-ping
  claude-codex-dual
  claude_codex
  claude_ai
  claude_bridge
  caskd
  gaskd
  oaskd
  laskd
  daskd
)

usage() {
  msg "install.usage.title"
  msg "install.usage.install"
  msg "install.usage.uninstall"
  printf '\n'
  msg "install.usage.env_title"
  msg "install.usage.install_prefix"
  msg "install.usage.bin_dir"
  msg "install.usage.claude_dir"
  msg "install.usage.droid_autoinstall"
  msg "install.usage.droid_force"
  msg "install.usage.claude_md_mode"
  msg "install.usage.claude_md_mode_inline"
  msg "install.usage.claude_md_mode_route"
}

detect_claude_dir() {
  if [[ -n "${CODEX_CLAUDE_COMMAND_DIR:-}" ]]; then
    echo "$CODEX_CLAUDE_COMMAND_DIR"
    return
  fi

  local candidates=(
    "$HOME/.claude/commands"
    "$HOME/.config/claude/commands"
    "$HOME/.local/share/claude/commands"
  )

  for dir in "${candidates[@]}"; do
    if [[ -d "$dir" ]]; then
      echo "$dir"
      return
    fi
  done

  local fallback="$HOME/.claude/commands"
  mkdir -p "$fallback"
  echo "$fallback"
}

require_command() {
  local cmd="$1"
  local pkg="${2:-$1}"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    msg "install.dependency.missing" "$cmd"
    msg "install.dependency.install_first" "$pkg"
    exit 1
  fi
}

PYTHON_BIN="${CCB_PYTHON_BIN:-}"

_python_check_310() {
  local cmd="$1"
  command -v "$cmd" >/dev/null 2>&1 || return 1
  "$cmd" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1
}

pick_python_bin() {
  if [[ -n "${PYTHON_BIN}" ]] && _python_check_310 "${PYTHON_BIN}"; then
    return 0
  fi
  for cmd in python3 python; do
    if _python_check_310 "$cmd"; then
      PYTHON_BIN="$cmd"
      return 0
    fi
  done
  return 1
}

pick_any_python_bin() {
  if [[ -n "${PYTHON_BIN}" ]] && command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
    return 0
  fi
  for cmd in python3 python; do
    if command -v "$cmd" >/dev/null 2>&1; then
      PYTHON_BIN="$cmd"
      return 0
    fi
  done
  return 1
}

require_python_version() {
  # ccb requires Python 3.10+ (PEP 604 type unions: `str | None`, etc.)
  if ! pick_python_bin; then
    msg "install.python.missing"
    msg "install.python.install_hint"
    exit 1
  fi
  local version
  version="$("$PYTHON_BIN" -c 'import sys; print("{}.{}.{}".format(sys.version_info[0], sys.version_info[1], sys.version_info[2]))' 2>/dev/null || echo unknown)"
  if ! _python_check_310 "$PYTHON_BIN"; then
    msg "install.dependency.missing" "python"
    msg "install.python.version_old" "$version"
    msg "install.python.upgrade_hint"
    exit 1
  fi
  msg "install.python.ok" "$version" "$PYTHON_BIN"
}

python_has_module() {
  local module="$1"
  if ! pick_any_python_bin; then
    return 1
  fi
  "$PYTHON_BIN" - <<PY >/dev/null 2>&1
import importlib.util
import sys
sys.exit(0 if importlib.util.find_spec("${module}") else 1)
PY
}

install_watchdog() {
  if python_has_module "watchdog"; then
    msg watchdog_installed
    return 0
  fi
  msg watchdog_installing

  # 1. Try uv (fast, no PEP 668 issues)
  if command -v uv >/dev/null 2>&1; then
    if uv pip install --system "watchdog>=2.1.0" >/dev/null 2>&1 || \
       uv pip install "watchdog>=2.1.0" >/dev/null 2>&1; then
      if python_has_module "watchdog"; then
        msg watchdog_installed
        return 0
      fi
    fi
  fi

  if ! "$PYTHON_BIN" -m pip --version >/dev/null 2>&1; then
    msg pip_missing
    return 1
  fi

  # 2. Try standard pip install --user
  if "$PYTHON_BIN" -m pip install --user "watchdog>=2.1.0" >/dev/null 2>&1; then
    if python_has_module "watchdog"; then
      msg watchdog_installed
      return 0
    fi
  fi

  # 3. PEP 668 fallback: --break-system-packages (Homebrew Python, Debian 12+, etc.)
  if "$PYTHON_BIN" -m pip install --user --break-system-packages "watchdog>=2.1.0" >/dev/null 2>&1; then
    if python_has_module "watchdog"; then
      msg watchdog_installed
      return 0
    fi
  fi

  # 4. Try pipx inject into a shared venv as last resort
  if command -v pipx >/dev/null 2>&1; then
    if pipx install watchdog >/dev/null 2>&1; then
      if python_has_module "watchdog"; then
        msg watchdog_installed
        return 0
      fi
    fi
  fi

  msg watchdog_failed
  return 1
}

# Return linux / macos / unknown based on uname
detect_platform() {
  local name
  name="$(uname -s 2>/dev/null || echo unknown)"
  case "$name" in
    Linux) echo "linux" ;;
    Darwin) echo "macos" ;;
    *) echo "unknown" ;;
  esac
}


is_wsl() {
  [[ -f /proc/version ]] && grep -qi microsoft /proc/version 2>/dev/null
}

get_wsl_version() {
  if [[ -n "${WSL_INTEROP:-}" ]]; then
    echo 2
  else
    echo 1
  fi
}

check_wsl_compatibility() {
  if is_wsl; then
    local ver
    ver="$(get_wsl_version)"
    msg "install.environment.detected" "WSL $ver"
  fi
}

confirm_backend_env_wsl() {
  if ! is_wsl; then
    return
  fi

  if [[ "${CCB_INSTALL_ASSUME_YES:-}" == "1" ]]; then
    return
  fi

  if [[ ! -t 0 ]]; then
    msg "install.backend.non_interactive"
    msg "install.backend.non_interactive_hint"
    msg "install.backend.non_interactive_retry"
    exit 1
  fi

  printf '\n'
  msg "install.ui.separator"
  msg "install.backend.wsl_warning"
  msg "install.ui.separator"
  msg "install.backend.same_env_required"
  printf '\n'
  msg "install.backend.confirm_wsl_native"
  msg "install.backend.windows_hint"
  msg "install.backend.windows_command"
  msg "install.ui.separator"
  printf '\n'
  read -r -p "$(msg "install.backend.confirm_wsl_prompt"): " reply
  case "$reply" in
    y|Y|yes|YES) ;;
    *) msg "install.backend.cancelled"; exit 1 ;;
  esac
}

print_tmux_install_hint() {
  local platform
  platform="$(detect_platform)"
  case "$platform" in
    macos)
      if command -v brew >/dev/null 2>&1; then
        msg "install.tmux.macos_brew"
      else
        msg "install.tmux.macos_no_brew"
      fi
      ;;
    linux)
      if command -v apt-get >/dev/null 2>&1; then
        msg "install.tmux.debian"
      elif command -v dnf >/dev/null 2>&1; then
        msg "install.tmux.dnf"
      elif command -v yum >/dev/null 2>&1; then
        msg "install.tmux.yum"
      elif command -v pacman >/dev/null 2>&1; then
        msg "install.tmux.pacman"
      elif command -v apk >/dev/null 2>&1; then
        msg "install.tmux.apk"
      elif command -v zypper >/dev/null 2>&1; then
        msg "install.tmux.zypper"
      else
        msg "install.tmux.generic"
      fi
      ;;
    *)
      msg "install.tmux.docs"
      ;;
  esac
}

require_terminal_backend() {
  local wezterm_override="${CODEX_WEZTERM_BIN:-${WEZTERM_BIN:-}}"

  # ============================================
  # Prioritize detecting current environment
  # ============================================

  # 1. If running in WezTerm environment
  if [[ -n "${WEZTERM_PANE:-}" ]]; then
    if [[ -n "${wezterm_override}" ]] && { command -v "${wezterm_override}" >/dev/null 2>&1 || [[ -f "${wezterm_override}" ]]; }; then
      msg "install.backend.wezterm_env_override" "${wezterm_override}"
      return
    fi
    if command -v wezterm >/dev/null 2>&1 || command -v wezterm.exe >/dev/null 2>&1; then
      msg "install.backend.wezterm_env"
      return
    fi
  fi

  # 2. If running in tmux environment
  if [[ -n "${TMUX:-}" ]]; then
    msg "install.backend.tmux_env"
    return
  fi

  # ============================================
  # Not in specific environment, detect by availability
  # ============================================

  # 3. Check WezTerm environment variable override
  if [[ -n "${wezterm_override}" ]]; then
    if command -v "${wezterm_override}" >/dev/null 2>&1 || [[ -f "${wezterm_override}" ]]; then
      msg "install.backend.wezterm_override" "${wezterm_override}"
      return
    fi
  fi

  # 4. Check WezTerm command
  if command -v wezterm >/dev/null 2>&1 || command -v wezterm.exe >/dev/null 2>&1; then
    msg "install.backend.wezterm"
    return
  fi

  # WSL: Windows PATH may not be injected, try common install paths
  if [[ -f "/proc/version" ]] && grep -qi microsoft /proc/version 2>/dev/null; then
    if [[ -x "/mnt/c/Program Files/WezTerm/wezterm.exe" ]] || [[ -f "/mnt/c/Program Files/WezTerm/wezterm.exe" ]]; then
      msg "install.backend.wezterm_program_files"
      return
    fi
    if [[ -x "/mnt/c/Program Files (x86)/WezTerm/wezterm.exe" ]] || [[ -f "/mnt/c/Program Files (x86)/WezTerm/wezterm.exe" ]]; then
      msg "install.backend.wezterm_program_files_x86"
      return
    fi
  fi

  # 5. Check tmux
  if command -v tmux >/dev/null 2>&1; then
    msg "install.backend.tmux_recommended"
    return
  fi

  # 6. No terminal multiplexer found
  msg "install.backend.missing"
  msg "install.backend.website"

  if [[ "$(uname)" == "Darwin" ]]; then
    printf '\n'
    msg "install.backend.macos_note"
    msg "install.backend.macos_tmux"
  fi

  print_tmux_install_hint
  exit 1
}

has_wezterm() {
  local wezterm_override="${CODEX_WEZTERM_BIN:-${WEZTERM_BIN:-}}"
  if [[ -n "${wezterm_override}" ]]; then
    command -v "${wezterm_override}" >/dev/null 2>&1 || [[ -f "${wezterm_override}" ]] && return 0
  fi
  command -v wezterm >/dev/null 2>&1 && return 0
  command -v wezterm.exe >/dev/null 2>&1 && return 0
  if [[ -f "/proc/version" ]] && grep -qi microsoft /proc/version 2>/dev/null; then
    [[ -f "/mnt/c/Program Files/WezTerm/wezterm.exe" ]] && return 0
    [[ -f "/mnt/c/Program Files (x86)/WezTerm/wezterm.exe" ]] && return 0
  fi
  return 1
}

detect_wezterm_path() {
  local wezterm_override="${CODEX_WEZTERM_BIN:-${WEZTERM_BIN:-}}"
  if [[ -n "${wezterm_override}" ]] && [[ -f "${wezterm_override}" ]]; then
    echo "${wezterm_override}"
    return
  fi
  local found
  found="$(command -v wezterm 2>/dev/null)" && [[ -n "$found" ]] && echo "$found" && return
  found="$(command -v wezterm.exe 2>/dev/null)" && [[ -n "$found" ]] && echo "$found" && return
  if is_wsl; then
    for drive in c d e f; do
      for path in "/mnt/${drive}/Program Files/WezTerm/wezterm.exe" \
                  "/mnt/${drive}/Program Files (x86)/WezTerm/wezterm.exe"; do
        if [[ -f "$path" ]]; then
          echo "$path"
          return
        fi
      done
    done
  fi
}

save_wezterm_config() {
  local wezterm_path
  wezterm_path="$(detect_wezterm_path)"
  if [[ -n "$wezterm_path" ]]; then
    local cfg_root="${XDG_CONFIG_HOME:-$HOME/.config}"
    mkdir -p "$cfg_root/ccb"
    echo "CODEX_WEZTERM_BIN=${wezterm_path}" > "$cfg_root/ccb/env"
    msg "install.wezterm.cached" "$wezterm_path"
  fi
}

copy_project() {
  local staging
  staging="$(mktemp -d)"
  trap 'rm -rf "$staging"' EXIT

  if command -v rsync >/dev/null 2>&1; then
    rsync -a \
      --exclude '.git/' \
      --exclude '__pycache__/' \
      --exclude '.pytest_cache/' \
      --exclude '.mypy_cache/' \
      --exclude '.venv/' \
      --exclude 'lib/web/' \
      --exclude 'bin/ccb-web' \
      "$REPO_ROOT"/ "$staging"/
  else
    tar -C "$REPO_ROOT" \
      --exclude '.git' \
      --exclude '__pycache__' \
      --exclude '.pytest_cache' \
      --exclude '.mypy_cache' \
      --exclude '.venv' \
      --exclude 'lib/web' \
      --exclude 'bin/ccb-web' \
      -cf - . | tar -C "$staging" -xf -
  fi

  rm -rf "$INSTALL_PREFIX"
  mkdir -p "$(dirname "$INSTALL_PREFIX")"
  mv "$staging" "$INSTALL_PREFIX"
  trap - EXIT

  # Update GIT_COMMIT and GIT_DATE in ccb file
  local git_commit="" git_date=""

  # Method 1: From git repo
  if command -v git >/dev/null 2>&1 && [[ -d "$REPO_ROOT/.git" ]]; then
    git_commit=$(git -C "$REPO_ROOT" log -1 --format='%h' 2>/dev/null || echo "")
    git_date=$(git -C "$REPO_ROOT" log -1 --format='%cs' 2>/dev/null || echo "")
  fi

  # Method 2: From environment variables (set by ccb update)
  if [[ -z "$git_commit" && -n "${CCB_GIT_COMMIT:-}" ]]; then
    git_commit="$CCB_GIT_COMMIT"
    git_date="${CCB_GIT_DATE:-}"
  fi

  # Method 3: From GitHub API (fallback)
  if [[ -z "$git_commit" ]] && command -v curl >/dev/null 2>&1; then
    local api_response
    api_response=$(curl -fsSL "https://api.github.com/repos/bfly123/claude_code_bridge/commits/main" 2>/dev/null || echo "")
    if [[ -n "$api_response" ]]; then
      git_commit=$(echo "$api_response" | grep -o '"sha": "[^"]*"' | head -1 | cut -d'"' -f4 | cut -c1-7)
      git_date=$(echo "$api_response" | grep -o '"date": "[^"]*"' | head -1 | cut -d'"' -f4 | cut -c1-10)
    fi
  fi

  if [[ -n "$git_commit" && -f "$INSTALL_PREFIX/ccb" ]]; then
    sed -i.bak "s/^GIT_COMMIT = .*/GIT_COMMIT = \"$git_commit\"/" "$INSTALL_PREFIX/ccb"
    sed -i.bak "s/^GIT_DATE = .*/GIT_DATE = \"$git_date\"/" "$INSTALL_PREFIX/ccb"
    rm -f "$INSTALL_PREFIX/ccb.bak"
  fi
}

install_bin_links() {
  mkdir -p "$BIN_DIR"

  for path in "${SCRIPTS_TO_LINK[@]}"; do
    local name
    name="$(basename "$path")"
    if [[ ! -f "$INSTALL_PREFIX/$path" ]]; then
      msg "install.link.script_missing" "$INSTALL_PREFIX/$path"
      continue
    fi
    chmod +x "$INSTALL_PREFIX/$path"
    if ln -sf "$INSTALL_PREFIX/$path" "$BIN_DIR/$name" 2>/dev/null; then
      :
    else
      # Windows (Git Bash) / restricted environments may not allow symlinks. Fall back to copying.
      cp -f "$INSTALL_PREFIX/$path" "$BIN_DIR/$name"
      chmod +x "$BIN_DIR/$name" 2>/dev/null || true
    fi
  done

  for legacy in "${LEGACY_SCRIPTS[@]}"; do
    rm -f "$BIN_DIR/$legacy"
  done

  msg "install.link.created" "$BIN_DIR"
}

ensure_path_configured() {
  # Check if BIN_DIR is already in PATH
  if [[ ":$PATH:" == *":$BIN_DIR:"* ]]; then
    return
  fi

  local shell_rc=""
  local current_shell
  current_shell="$(basename "${SHELL:-/bin/bash}")"

  case "$current_shell" in
    zsh)  shell_rc="$HOME/.zshrc" ;;
    bash)
      if [[ -f "$HOME/.bash_profile" ]]; then
        shell_rc="$HOME/.bash_profile"
      else
        shell_rc="$HOME/.bashrc"
      fi
      ;;
    *)    shell_rc="$HOME/.profile" ;;
  esac

  local path_line="export PATH=\"${BIN_DIR}:\$PATH\""

  # Check if already configured in shell rc
  if [[ -f "$shell_rc" ]] && grep -qF "$BIN_DIR" "$shell_rc" 2>/dev/null; then
    msg "install.path.already_configured" "$shell_rc"
    return
  fi

  # Add to shell rc
  echo "" >> "$shell_rc"
  echo "# Added by ccb installer" >> "$shell_rc"
  echo "$path_line" >> "$shell_rc"
  msg "install.path.added" "$BIN_DIR" "$shell_rc"
  msg "install.path.reload_hint" "$shell_rc"
}

install_claude_commands() {
  local claude_dir
  claude_dir="$(detect_claude_dir)"
  mkdir -p "$claude_dir"

  # Clean up obsolete CCB commands (replaced by unified ask/ping/pend)
  local obsolete_cmds="cask.md gask.md oask.md dask.md lask.md cpend.md gpend.md opend.md dpend.md lpend.md cping.md gping.md oping.md dping.md lping.md"
  for obs_cmd in $obsolete_cmds; do
    if [[ -f "$claude_dir/$obs_cmd" ]]; then
      rm -f "$claude_dir/$obs_cmd"
      msg "install.commands.removed" "$obs_cmd"
    fi
  done

  for doc in "${CLAUDE_MARKDOWN[@]+"${CLAUDE_MARKDOWN[@]}"}"; do
    cp -f "$REPO_ROOT/commands/$doc" "$claude_dir/$doc"
    chmod 0644 "$claude_dir/$doc" 2>/dev/null || true
  done

  msg "install.commands.updated_dir" "$claude_dir"
}

install_claude_skills() {
  local skills_src="$REPO_ROOT/claude_skills"
  local skills_dst="$HOME/.claude/skills"

  if [[ ! -d "$skills_src" ]]; then
    return
  fi

  mkdir -p "$skills_dst"

  # Clean up obsolete CCB skills (replaced by unified ask/cping/pend)
  local obsolete_skills="cask gask oask dask lask cpend gpend opend dpend lpend cping gping oping dping lping ping auto"
  for obs_skill in $obsolete_skills; do
    if [[ -d "$skills_dst/$obs_skill" ]]; then
      rm -rf "$skills_dst/$obs_skill"
      msg "install.skill.removed" "$obs_skill"
    fi
  done

  msg "install.skill.installing_claude"
  for skill_dir in "$skills_src"/*/; do
    [[ -d "$skill_dir" ]] || continue
    local skill_name
    skill_name=$(basename "$skill_dir")
    [[ "$skill_name" == "docs" ]] && continue

    local src_skill_md=""
    src_skill_md="$(localized_skill_template "$skill_dir")"
    if [[ -z "$src_skill_md" ]]; then
      continue
    fi

    local dst_dir="$skills_dst/$skill_name"
    local dst_skill_md="$dst_dir/SKILL.md"
    mkdir -p "$dst_dir"
    cp -f "$src_skill_md" "$dst_skill_md"

    # Copy additional subdirectories (e.g., references/) if they exist
    for subdir in "$skill_dir"*/; do
      if [[ -d "$subdir" ]]; then
        local subdir_name
        subdir_name=$(basename "$subdir")
        cp -rf "$subdir" "$dst_dir/$subdir_name"
      fi
    done

    msg "install.skill.updated" "$skill_name"
  done

  # Shared docs live at skills/docs but are not a "skill directory". Install them as well.
  if [[ -d "$skills_src/docs" ]]; then
    rm -rf "$skills_dst/docs"
    cp -r "$skills_src/docs" "$skills_dst/docs"
    msg "install.skill.docs_installed"
  fi

  # Make autoloop scripts executable
  local autoloop_sh="$skills_dst/tr/scripts/autoloop.sh"
  local autoloop_py="$skills_dst/tr/scripts/autoloop.py"
  [[ -f "$autoloop_sh" ]] && chmod +x "$autoloop_sh"
  [[ -f "$autoloop_py" ]] && chmod +x "$autoloop_py"

  msg "install.skill.updated_dir" "$skills_dst"
}

install_codex_skills() {
  local skills_src="$REPO_ROOT/codex_skills"
  local skills_dst="${CODEX_HOME:-$HOME/.codex}/skills"

  if [[ ! -d "$skills_src" ]]; then
    return
  fi

  mkdir -p "$skills_dst"

  # Clean up obsolete CCB skills (replaced by unified ask/ping/pend)
  local obsolete_skills="cask gask oask dask lask cpend gpend opend dpend lpend cping gping oping dping lping"
  for obs_skill in $obsolete_skills; do
    if [[ -d "$skills_dst/$obs_skill" ]]; then
      rm -rf "$skills_dst/$obs_skill"
      msg "install.skill.removed" "$obs_skill"
    fi
  done

  msg "install.skill.installing_codex"
  for skill_dir in "$skills_src"/*/; do
    [[ -d "$skill_dir" ]] || continue
    local skill_name
    skill_name=$(basename "$skill_dir")

    local src_skill_md=""
    src_skill_md="$(localized_skill_template "$skill_dir")"
    if [[ -z "$src_skill_md" ]]; then
      continue
    fi

    local dst_dir="$skills_dst/$skill_name"
    local dst_skill_md="$dst_dir/SKILL.md"
    mkdir -p "$dst_dir"
    cp -f "$src_skill_md" "$dst_skill_md"

    # Copy additional subdirectories (e.g., references/) if they exist
    for subdir in "$skill_dir"*/; do
      if [[ -d "$subdir" ]]; then
        local subdir_name
        subdir_name=$(basename "$subdir")
        cp -rf "$subdir" "$dst_dir/$subdir_name"
      fi
    done

    msg "install.skill.updated_codex" "$skill_name"
  done
  msg "install.skill.updated_codex_dir" "$skills_dst"
}

install_droid_skills() {
  local skills_src="$REPO_ROOT/droid_skills"
  local skills_dst="${FACTORY_HOME:-$HOME/.factory}/skills"

  if [[ ! -d "$skills_src" ]]; then
    return
  fi

  if ! command -v droid >/dev/null 2>&1; then
    return
  fi

  mkdir -p "$skills_dst"

  # Clean up obsolete CCB skills (replaced by unified ask/ping/pend)
  local obsolete_skills="cask gask oask dask lask cpend gpend opend dpend lpend cping gping oping dping lping"
  for obs_skill in $obsolete_skills; do
    if [[ -d "$skills_dst/$obs_skill" ]]; then
      rm -rf "$skills_dst/$obs_skill"
      msg "install.skill.removed" "$obs_skill"
    fi
  done

  msg "install.skill.installing_droid"
  for skill_dir in "$skills_src"/*/; do
    [[ -d "$skill_dir" ]] || continue
    local skill_name
    skill_name=$(basename "$skill_dir")

    local src_skill_md=""
    src_skill_md="$(localized_skill_template "$skill_dir")"
    if [[ -z "$src_skill_md" ]]; then
      continue
    fi

    local dst_dir="$skills_dst/$skill_name"
    local dst_skill_md="$dst_dir/SKILL.md"
    mkdir -p "$dst_dir"
    cp -f "$src_skill_md" "$dst_skill_md"

    # Copy additional subdirectories (e.g., references/) if they exist
    for subdir in "$skill_dir"*/; do
      if [[ -d "$subdir" ]]; then
        local subdir_name
        subdir_name=$(basename "$subdir")
        cp -rf "$subdir" "$dst_dir/$subdir_name"
      fi
    done

    msg "install.skill.updated_factory" "$skill_name"
  done
  msg "install.skill.updated_factory_dir" "$skills_dst"
}

install_droid_delegation() {
  if [[ "${CCB_DROID_AUTOINSTALL:-1}" == "0" ]]; then
    return
  fi
  if ! command -v droid >/dev/null 2>&1; then
    return
  fi
  local py
  py="$(command -v python3 2>/dev/null || command -v python 2>/dev/null || true)"
  if [[ -z "$py" ]]; then
    msg "install.droid.python_missing"
    return
  fi
  local server="$INSTALL_PREFIX/mcp/ccb-delegation/server.py"
  if [[ ! -f "$server" ]]; then
    msg "install.droid.server_missing" "$server"
    return
  fi
  if [[ "${CCB_DROID_AUTOINSTALL_FORCE:-0}" == "1" ]]; then
    droid mcp remove ccb-delegation >/dev/null 2>&1 || true
  fi
  if droid mcp add ccb-delegation --type stdio "$py" "$server" >/dev/null 2>&1; then
    msg "install.droid.registered"
  else
    msg "install.droid.register_failed"
  fi
}

CCB_START_MARKER="<!-- CCB_CONFIG_START -->"
CCB_END_MARKER="<!-- CCB_CONFIG_END -->"
LEGACY_RULE_MARKER="## Codex 协作规则"

remove_codex_mcp() {
  local claude_config="$HOME/.claude.json"

  if [[ ! -f "$claude_config" ]]; then
    return
  fi

  if ! pick_python_bin; then
    msg "install.mcp.python_required"
    return
  fi

  local has_codex_mcp
  has_codex_mcp=$("$PYTHON_BIN" -c "
import json

try:
    with open('$claude_config', 'r', encoding='utf-8') as f:
        data = json.load(f)
    projects = data.get('projects', {}) if isinstance(data, dict) else {}
    found = False
    if isinstance(projects, dict):
        for _proj, cfg in projects.items():
            if not isinstance(cfg, dict):
                continue
            servers = cfg.get('mcpServers', {})
            if not isinstance(servers, dict):
                continue
            for name in list(servers.keys()):
                if 'codex' in str(name).lower():
                    found = True
                    break
            if found:
                break
    print('yes' if found else 'no')
except Exception:
    print('no')
" 2>/dev/null)

  if [[ "$has_codex_mcp" == "yes" ]]; then
    msg "install.mcp.detected_conflict"
    "$PYTHON_BIN" -c "
import json
import sys

try:
    with open('$claude_config', 'r', encoding='utf-8') as f:
        data = json.load(f)
    removed = []
    projects = data.get('projects', {}) if isinstance(data, dict) else {}
    if isinstance(projects, dict):
        for proj, cfg in projects.items():
            if not isinstance(cfg, dict):
                continue
            servers = cfg.get('mcpServers')
            if not isinstance(servers, dict):
                continue
            for name in list(servers.keys()):
                if 'codex' in str(name).lower():
                    del servers[name]
                    removed.append(f'{proj}: {name}')
    with open('$claude_config', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    if removed:
        print('Removed the following MCP configurations:')
        for r in removed:
            print(f'  - {r}')
except Exception as e:
    sys.stderr.write(f'WARN: failed cleaning MCP config: {e}\\n')
    sys.exit(0)
"
    msg "install.mcp.cleaned"
  fi
}

install_claude_md_config() {
  local claude_md="$HOME/.claude/CLAUDE.md"
  local md_mode="${CCB_CLAUDE_MD_MODE:-inline}"
  local full_template
  local route_template
  full_template="$(localized_config_template "claude-md-ccb.md")"
  route_template="$(localized_config_template "claude-md-ccb-route.md")"
  local external_config="$HOME/.claude/rules/ccb-config.md"

  # Select template based on mode
  local template
  if [[ "$md_mode" == "route" ]]; then
    template="$route_template"
  else
    template="$full_template"
  fi

  mkdir -p "$HOME/.claude"
  if ! pick_python_bin; then
    msg "install.claude_md.python_required"
    return 1
  fi

  if [[ ! -f "$template" ]]; then
    msg "install.claude_md.template_missing" "$template"
    return 1
  fi

  # In route mode, write full config to external file
  if [[ "$md_mode" == "route" ]]; then
    mkdir -p "$HOME/.claude/rules"
    cp "$full_template" "$external_config"
    msg "install.claude_md.external_written" "$external_config"
  fi

  local ccb_content
  ccb_content="$(cat "$template")"

  if [[ -f "$claude_md" ]]; then
    if grep -q "$CCB_START_MARKER" "$claude_md" 2>/dev/null; then
      msg "install.claude_md.updating" "$md_mode"
      "$PYTHON_BIN" -c "
import re, sys

with open(sys.argv[1], 'r', encoding='utf-8') as f:
    content = f.read()
with open(sys.argv[2], 'r', encoding='utf-8') as f:
    new_block = f.read().strip()
pattern = r'<!-- CCB_CONFIG_START -->.*?<!-- CCB_CONFIG_END -->'
content = re.sub(pattern, new_block, content, flags=re.DOTALL)
with open(sys.argv[1], 'w', encoding='utf-8') as f:
    f.write(content)
" "$claude_md" "$template"
    elif grep -qE "$LEGACY_RULE_MARKER|## Codex Collaboration Rules|## Gemini|## OpenCode" "$claude_md" 2>/dev/null; then
      msg "install.claude_md.removing_legacy"
      "$PYTHON_BIN" -c "
import re, sys

with open(sys.argv[1], 'r', encoding='utf-8') as f:
    content = f.read()
patterns = [
    r'## Codex Collaboration Rules.*?(?=\n## (?!Gemini)|\Z)',
    r'## Codex 协作规则.*?(?=\n## |\Z)',
    r'## Gemini Collaboration Rules.*?(?=\n## |\Z)',
    r'## Gemini 协作规则.*?(?=\n## |\Z)',
    r'## OpenCode Collaboration Rules.*?(?=\n## |\Z)',
    r'## OpenCode 协作规则.*?(?=\n## |\Z)',
]
for p in patterns:
    content = re.sub(p, '', content, flags=re.DOTALL)
content = content.rstrip() + '\n'
with open(sys.argv[1], 'w', encoding='utf-8') as f:
    f.write(content)
" "$claude_md"
      cat "$template" >> "$claude_md"
    else
      echo "" >> "$claude_md"
      cat "$template" >> "$claude_md"
    fi
  else
    cat "$template" > "$claude_md"
  fi

  msg "install.claude_md.updated" "$claude_md" "$md_mode"
}

CCB_ROLES_START_MARKER="<!-- CCB_ROLES_START -->"
CCB_ROLES_END_MARKER="<!-- CCB_ROLES_END -->"
CCB_RUBRICS_START_MARKER="<!-- REVIEW_RUBRICS_START -->"
CCB_RUBRICS_END_MARKER="<!-- REVIEW_RUBRICS_END -->"

install_agents_md_config() {
  local agents_md="$INSTALL_PREFIX/AGENTS.md"
  local template
  template="$(localized_config_template "agents-md-ccb.md")"

  if ! pick_python_bin; then
    msg "install.agents.python_required"
    return 1
  fi
  if [[ ! -f "$template" ]]; then
    msg "install.agents.template_missing" "$template"
    return 1
  fi

  if [[ -f "$agents_md" ]]; then
    # Replace existing CCB blocks if present
    local updated=false
    if grep -q "$CCB_ROLES_START_MARKER" "$agents_md" 2>/dev/null || \
       grep -q "$CCB_RUBRICS_START_MARKER" "$agents_md" 2>/dev/null; then
      msg "install.agents.updating"
      "$PYTHON_BIN" -c "
import re, sys

with open(sys.argv[1], 'r', encoding='utf-8') as f:
    content = f.read()
with open(sys.argv[2], 'r', encoding='utf-8') as f:
    new_block = f.read().strip()

# Remove old roles block
content = re.sub(
    r'<!-- CCB_ROLES_START -->.*?<!-- CCB_ROLES_END -->',
    '', content, flags=re.DOTALL)
# Remove old rubrics block
content = re.sub(
    r'<!-- REVIEW_RUBRICS_START -->.*?<!-- REVIEW_RUBRICS_END -->',
    '', content, flags=re.DOTALL)
content = content.rstrip() + '\n\n' + new_block + '\n'
with open(sys.argv[1], 'w', encoding='utf-8') as f:
    f.write(content)
" "$agents_md" "$template"
      updated=true
    fi
    if ! $updated; then
      echo "" >> "$agents_md"
      cat "$template" >> "$agents_md"
    fi
  else
    cat "$template" > "$agents_md"
  fi

  msg "install.agents.updated" "$agents_md"
}

install_clinerules_config() {
  local clinerules="$INSTALL_PREFIX/.clinerules"
  local template
  template="$(localized_config_template "clinerules-ccb.md")"

  if ! pick_python_bin; then
    msg "install.clinerules.python_required"
    return 1
  fi
  if [[ ! -f "$template" ]]; then
    msg "install.clinerules.template_missing" "$template"
    return 1
  fi

  if [[ -f "$clinerules" ]]; then
    if grep -q "$CCB_ROLES_START_MARKER" "$clinerules" 2>/dev/null; then
      msg "install.clinerules.updating"
      "$PYTHON_BIN" -c "
import re, sys

with open(sys.argv[1], 'r', encoding='utf-8') as f:
    content = f.read()
with open(sys.argv[2], 'r', encoding='utf-8') as f:
    new_block = f.read().strip()

content = re.sub(
    r'<!-- CCB_ROLES_START -->.*?<!-- CCB_ROLES_END -->',
    new_block, content, flags=re.DOTALL)
with open(sys.argv[1], 'w', encoding='utf-8') as f:
    f.write(content)
" "$clinerules" "$template"
    else
      echo "" >> "$clinerules"
      cat "$template" >> "$clinerules"
    fi
  else
    cat "$template" > "$clinerules"
  fi

  msg "install.clinerules.updated" "$clinerules"
}

install_settings_permissions() {
  local settings_file="$HOME/.claude/settings.json"
  mkdir -p "$HOME/.claude"

  local perms_to_add=(
    'Bash(ask *)'
    'Bash(ccb-ping *)'
    'Bash(pend *)'
  )

  if [[ ! -f "$settings_file" ]]; then
    cat > "$settings_file" << 'SETTINGS'
{
	  "permissions": {
	    "allow": [
	      "Bash(ask *)",
	      "Bash(ccb-ping *)",
	      "Bash(pend *)"
	    ],
    "deny": []
  }
}
SETTINGS
    msg "install.settings.created" "$settings_file"
    return
  fi

  # Remove legacy permissions from previous versions
  local perms_to_remove=(
    'Bash(ping *)'
  )
  for old_perm in "${perms_to_remove[@]}"; do
    if grep -q "$old_perm" "$settings_file" 2>/dev/null; then
      if pick_python_bin; then
        "$PYTHON_BIN" -c "
import json, sys
path = '$settings_file'
old_perm = '$old_perm'
try:
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    allow = data.get('permissions', {}).get('allow', [])
    if old_perm in allow:
        allow.remove(old_perm)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
except Exception as e:
    sys.stderr.write(f'WARN: failed cleaning {path}: {e}\n')
"
        echo "  Removed legacy permission: $old_perm"
      fi
    fi
  done

  local added=0
  for perm in "${perms_to_add[@]}"; do
    if ! grep -q "$perm" "$settings_file" 2>/dev/null; then
      if pick_python_bin; then
        "$PYTHON_BIN" -c "
import json
import sys

path = '$settings_file'
perm = '$perm'
try:
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if not isinstance(data, dict):
        data = {}
    perms = data.get('permissions')
    if not isinstance(perms, dict):
        perms = {'allow': [], 'deny': []}
        data['permissions'] = perms
    allow = perms.get('allow')
    if not isinstance(allow, list):
        allow = []
        perms['allow'] = allow
    if perm not in allow:
        allow.append(perm)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
except Exception as e:
    sys.stderr.write(f'WARN: failed updating {path}: {e}\\n')
    sys.exit(0)
"
        added=1
      fi
    fi
  done

  if [[ $added -eq 1 ]]; then
    msg "install.settings.updated" "$settings_file"
  else
    echo "Permissions already exist in $settings_file"
  fi
}

CCB_TMUX_MARKER="# CCB (Claude Code Bridge) tmux configuration"
CCB_TMUX_MARKER_LEGACY="# CCB tmux configuration"

remove_ccb_tmux_block_from_file() {
  local target_conf="$1"

  if [[ ! -f "$target_conf" ]]; then
    return 0
  fi

  if ! grep -q "$CCB_TMUX_MARKER" "$target_conf" 2>/dev/null && \
     ! grep -q "$CCB_TMUX_MARKER_LEGACY" "$target_conf" 2>/dev/null; then
    return 0
  fi

  if ! pick_any_python_bin; then
    return 1
  fi

  "$PYTHON_BIN" -c "
import re
path = '$target_conf'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()
# Remove CCB tmux config block (both new and legacy markers)
pattern = r'\n*# =+\n# CCB \(Claude Code Bridge\) tmux configuration.*?# =+\n# End of CCB tmux configuration\n# =+'
content = re.sub(pattern, '', content, flags=re.DOTALL)
pattern = r'\n*# CCB tmux configuration.*'
content = re.sub(pattern, '', content, flags=re.DOTALL)
with open(path, 'w', encoding='utf-8') as f:
    f.write(content.strip() + '\n' if content.strip() else '')
"
}

install_tmux_config() {
  local tmux_conf_main="$HOME/.tmux.conf"
  local tmux_conf_local="$HOME/.tmux.conf.local"
  local tmux_conf="$tmux_conf_main"
  local reload_conf="$tmux_conf_main"
  local ccb_tmux_conf
  ccb_tmux_conf="$(localized_config_template "tmux-ccb.conf")"
  local ccb_status_script="$REPO_ROOT/config/ccb-status.sh"
  local status_install_path="$BIN_DIR/ccb-status.sh"

  if [[ ! -f "$ccb_tmux_conf" ]]; then
    return
  fi

  mkdir -p "$BIN_DIR"

  # Install ccb-status.sh script
  if [[ -f "$ccb_status_script" ]]; then
    cp "$ccb_status_script" "$status_install_path"
    chmod +x "$status_install_path"
    echo "Installed: $status_install_path"
  fi

  # Install ccb-border.sh script (dynamic pane border colors)
  local ccb_border_script="$REPO_ROOT/config/ccb-border.sh"
  local border_install_path="$BIN_DIR/ccb-border.sh"
  if [[ -f "$ccb_border_script" ]]; then
    cp "$ccb_border_script" "$border_install_path"
    chmod +x "$border_install_path"
    echo "Installed: $border_install_path"
  fi

  # Install ccb-git.sh script (cached git status for tmux status line)
  local ccb_git_script="$REPO_ROOT/config/ccb-git.sh"
  local git_install_path="$BIN_DIR/ccb-git.sh"
  if [[ -f "$ccb_git_script" ]]; then
    cp "$ccb_git_script" "$git_install_path"
    chmod +x "$git_install_path"
    echo "Installed: $git_install_path"
  fi

  # Install tmux UI toggle scripts (enable/disable CCB theming per-session)
  local ccb_tmux_on_script="$REPO_ROOT/config/ccb-tmux-on.sh"
  local ccb_tmux_off_script="$REPO_ROOT/config/ccb-tmux-off.sh"
  if [[ -f "$ccb_tmux_on_script" ]]; then
    cp "$ccb_tmux_on_script" "$BIN_DIR/ccb-tmux-on.sh"
    chmod +x "$BIN_DIR/ccb-tmux-on.sh"
    echo "Installed: $BIN_DIR/ccb-tmux-on.sh"
  fi
  if [[ -f "$ccb_tmux_off_script" ]]; then
    cp "$ccb_tmux_off_script" "$BIN_DIR/ccb-tmux-off.sh"
    chmod +x "$BIN_DIR/ccb-tmux-off.sh"
    echo "Installed: $BIN_DIR/ccb-tmux-off.sh"
  fi

  # Oh-My-Tmux keeps user customizations in ~/.tmux.conf.local.
  # Appending to ~/.tmux.conf can break its internal _apply_configuration script.
  if [[ -f "$tmux_conf_main" ]] && grep -q 'TMUX_CONF_LOCAL' "$tmux_conf_main" 2>/dev/null; then
    tmux_conf="$tmux_conf_local"
    reload_conf="$tmux_conf_main"
    if [[ ! -f "$tmux_conf_local" ]]; then
      touch "$tmux_conf_local"
    fi
  else
    reload_conf="$tmux_conf"
  fi

  # Check if already configured (new or legacy marker) in either main/local config.
  local already_configured=false
  for conf in "$tmux_conf_main" "$tmux_conf_local"; do
    if [[ -f "$conf" ]] && \
      (grep -q "$CCB_TMUX_MARKER" "$conf" 2>/dev/null || \
       grep -q "$CCB_TMUX_MARKER_LEGACY" "$conf" 2>/dev/null); then
      already_configured=true
      break
    fi
  done

  if $already_configured; then
    # Update existing config: remove old CCB block(s) and re-add at target location.
    echo "Updating CCB tmux configuration..."
    remove_ccb_tmux_block_from_file "$tmux_conf_main" || true
    remove_ccb_tmux_block_from_file "$tmux_conf_local" || true
  else
    # Backup existing config if present
    if [[ -f "$tmux_conf" ]]; then
      cp "$tmux_conf" "$tmux_conf.bak.$(date +%Y%m%d%H%M%S)"
    fi
  fi

  # Append CCB tmux config (fill in BIN_DIR placeholders)
  {
    echo ""
    if pick_any_python_bin; then
      "$PYTHON_BIN" -c "
import sys

path = '$ccb_tmux_conf'
bin_dir = '$BIN_DIR'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()
sys.stdout.write(content.replace('@CCB_BIN_DIR@', bin_dir))
" 2>/dev/null || cat "$ccb_tmux_conf"
    else
      cat "$ccb_tmux_conf"
    fi
  } >> "$tmux_conf"

  msg "install.tmux.updated" "$tmux_conf"
  echo "   - CCB tmux integration (copy mode, mouse, pane management)"
  echo "   - CCB theme is enabled only while CCB is running (auto restore on exit)"
  echo "   - Vi-style pane management with h/j/k/l"
  echo "   - Mouse support and better copy mode"
  echo "   - Run 'tmux source $reload_conf' to apply (or restart tmux)"

  # Best-effort: if a tmux server is already running, reload config automatically.
  # (Avoid spawning a new server when tmux isn't running.)
  if command -v tmux >/dev/null 2>&1; then
    if tmux list-sessions >/dev/null 2>&1; then
      if tmux source-file "$reload_conf" >/dev/null 2>&1; then
        msg "install.tmux.reloaded"
      else
        msg "install.tmux.reload_failed" "$reload_conf"
      fi
    fi
  fi
}

uninstall_tmux_config() {
  local tmux_conf_main="$HOME/.tmux.conf"
  local tmux_conf_local="$HOME/.tmux.conf.local"
  local status_script="$BIN_DIR/ccb-status.sh"
  local border_script="$BIN_DIR/ccb-border.sh"
  local tmux_on_script="$BIN_DIR/ccb-tmux-on.sh"
  local tmux_off_script="$BIN_DIR/ccb-tmux-off.sh"

  # Remove ccb-status.sh script
  if [[ -f "$status_script" ]]; then
    rm -f "$status_script"
    echo "Removed: $status_script"
  fi

  # Remove ccb-border.sh script
  if [[ -f "$border_script" ]]; then
    rm -f "$border_script"
    echo "Removed: $border_script"
  fi

  # Remove tmux UI toggle scripts
  if [[ -f "$tmux_on_script" ]]; then
    rm -f "$tmux_on_script"
    echo "Removed: $tmux_on_script"
  fi
  if [[ -f "$tmux_off_script" ]]; then
    rm -f "$tmux_off_script"
    echo "Removed: $tmux_off_script"
  fi

  local removed_any=false
  for conf in "$tmux_conf_main" "$tmux_conf_local"; do
    if [[ -f "$conf" ]] && \
      (grep -q "$CCB_TMUX_MARKER" "$conf" 2>/dev/null || \
       grep -q "$CCB_TMUX_MARKER_LEGACY" "$conf" 2>/dev/null); then
      msg "install.tmux.removing" "$conf"
      if remove_ccb_tmux_block_from_file "$conf"; then
        msg "install.tmux.removed" "$conf"
        removed_any=true
      fi
    fi
  done

  if ! $removed_any; then
    return
  fi
}

install_requirements() {
  check_wsl_compatibility
  confirm_backend_env_wsl
  require_python_version
  install_watchdog || true
  require_terminal_backend
  if ! has_wezterm; then
    printf '\n'
    msg "install.ui.separator"
    msg "install.wezterm.note"
    msg "install.wezterm.site"
    msg "install.wezterm.benefit"
    msg "install.ui.separator"
    printf '\n'
  fi
}

# Clean up legacy daemon files (replaced by unified askd)
cleanup_legacy_files() {
  msg "install.cleanup.start"
  local cleaned=0

  # Legacy daemon scripts in bin/
  local legacy_daemons="caskd gaskd oaskd laskd daskd"
  for daemon in $legacy_daemons; do
    if [[ -f "$BIN_DIR/$daemon" ]]; then
      rm -f "$BIN_DIR/$daemon"
      msg "install.cleanup.removed_daemon" "$BIN_DIR/$daemon"
      cleaned=$((cleaned + 1))
    fi
    # Also check install prefix bin
    if [[ -f "$INSTALL_PREFIX/bin/$daemon" ]]; then
      rm -f "$INSTALL_PREFIX/bin/$daemon"
      msg "install.cleanup.removed_daemon" "$INSTALL_PREFIX/bin/$daemon"
      cleaned=$((cleaned + 1))
    fi
  done

  # Legacy daemon state files in ~/.cache/ccb/
  local cache_dir="${XDG_CACHE_HOME:-$HOME/.cache}/ccb"
  local legacy_states="caskd.json gaskd.json oaskd.json laskd.json daskd.json"
  for state in $legacy_states; do
    if [[ -f "$cache_dir/$state" ]]; then
      rm -f "$cache_dir/$state"
      msg "install.cleanup.removed_state" "$cache_dir/$state"
      cleaned=$((cleaned + 1))
    fi
  done

  # Legacy daemon module files in lib/
  local legacy_modules="caskd_daemon.py gaskd_daemon.py oaskd_daemon.py laskd_daemon.py daskd_daemon.py"
  for module in $legacy_modules; do
    if [[ -f "$INSTALL_PREFIX/lib/$module" ]]; then
      rm -f "$INSTALL_PREFIX/lib/$module"
      msg "install.cleanup.removed_module" "$INSTALL_PREFIX/lib/$module"
      cleaned=$((cleaned + 1))
    fi
  done

  if [[ $cleaned -eq 0 ]]; then
    msg "install.cleanup.none"
  else
    msg "install.cleanup.done" "$cleaned"
  fi
}

install_all() {
  install_requirements
  remove_codex_mcp
  cleanup_legacy_files
  save_wezterm_config
  copy_project
  install_bin_links
  ensure_path_configured
  install_claude_commands
  install_claude_skills
  install_codex_skills
  install_droid_skills
  install_droid_delegation
  install_claude_md_config
  install_agents_md_config
  install_clinerules_config
  install_settings_permissions
  install_tmux_config
  msg "install.summary.ok"
  msg "install.summary.project_dir" "$INSTALL_PREFIX"
  msg "install.summary.bin_dir" "$BIN_DIR"
  msg "install.summary.commands"
  local md_mode="${CCB_CLAUDE_MD_MODE:-inline}"
  if [[ "$md_mode" == "route" ]]; then
    msg "install.summary.claude_route"
  else
    msg "install.summary.claude_inline"
  fi
  msg "install.summary.agents"
  msg "install.summary.clinerules"
  msg "install.summary.settings"
}

uninstall_claude_md_config() {
  local claude_md="$HOME/.claude/CLAUDE.md"

  if [[ ! -f "$claude_md" ]]; then
    return
  fi

  if grep -q "$CCB_START_MARKER" "$claude_md" 2>/dev/null; then
    msg "install.uninstall.remove_claude_md"
    if pick_any_python_bin; then
      "$PYTHON_BIN" -c "
import re

with open('$claude_md', 'r', encoding='utf-8') as f:
    content = f.read()
pattern = r'\\n?<!-- CCB_CONFIG_START -->.*?<!-- CCB_CONFIG_END -->\\n?'
content = re.sub(pattern, '\\n', content, flags=re.DOTALL)
content = content.strip() + '\\n'
with open('$claude_md', 'w', encoding='utf-8') as f:
    f.write(content)
"
      msg "install.uninstall.removed_claude_md"
    else
      msg "install.uninstall.python_required_claude_md"
    fi
  elif grep -qE "$LEGACY_RULE_MARKER|## Codex Collaboration Rules|## Gemini|## OpenCode" "$claude_md" 2>/dev/null; then
    msg "install.uninstall.remove_legacy_rules"
    if pick_any_python_bin; then
      "$PYTHON_BIN" -c "
import re

with open('$claude_md', 'r', encoding='utf-8') as f:
    content = f.read()
patterns = [
    r'## Codex Collaboration Rules.*?(?=\\n## (?!Gemini)|\\Z)',
    r'## Codex 协作规则.*?(?=\\n## |\\Z)',
    r'## Gemini Collaboration Rules.*?(?=\\n## |\\Z)',
    r'## Gemini 协作规则.*?(?=\\n## |\\Z)',
    r'## OpenCode Collaboration Rules.*?(?=\\n## |\\Z)',
    r'## OpenCode 协作规则.*?(?=\\n## |\\Z)',
]
for p in patterns:
    content = re.sub(p, '', content, flags=re.DOTALL)
content = content.rstrip() + '\\n'
with open('$claude_md', 'w', encoding='utf-8') as f:
    f.write(content)
"
      msg "install.uninstall.removed_legacy_rules"
    else
      msg "install.uninstall.python_required_legacy_rules"
    fi
  fi

  # Clean up external config file if it exists (route mode)
  local external_config="$HOME/.claude/rules/ccb-config.md"
  if [[ -f "$external_config" ]]; then
    rm -f "$external_config"
    msg "install.uninstall.removed_external_config" "$external_config"
  fi
}

uninstall_settings_permissions() {
  local settings_file="$HOME/.claude/settings.json"

  if [[ ! -f "$settings_file" ]]; then
    return
  fi

  local perms_to_remove=(
    'Bash(ask *)'
    'Bash(ping *)'
    'Bash(ccb-ping *)'
    'Bash(pend *)'
    'Bash(cask:*)'
    'Bash(cpend)'
    'Bash(cping)'
    'Bash(gask:*)'
    'Bash(gpend)'
    'Bash(gping)'
    'Bash(oask:*)'
    'Bash(opend)'
    'Bash(oping)'
  )

  if pick_any_python_bin; then
    local has_perms=0
    for perm in "${perms_to_remove[@]}"; do
      if grep -q "$perm" "$settings_file" 2>/dev/null; then
        has_perms=1
        break
      fi
    done

    if [[ $has_perms -eq 1 ]]; then
      echo "Removing permission configuration from settings.json..."
      "$PYTHON_BIN" -c "
import json
import sys

path = '$settings_file'
perms_to_remove = [
    'Bash(ask *)',
    'Bash(ping *)',
    'Bash(ccb-ping *)',
    'Bash(pend *)',
    'Bash(cask:*)',
    'Bash(cpend)',
    'Bash(cping)',
    'Bash(gask:*)',
    'Bash(gpend)',
    'Bash(gping)',
    'Bash(oask:*)',
    'Bash(opend)',
    'Bash(oping)',
]
try:
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if not isinstance(data, dict):
        sys.exit(0)
    perms = data.get('permissions')
    if not isinstance(perms, dict):
        sys.exit(0)
    allow = perms.get('allow')
    if not isinstance(allow, list):
        sys.exit(0)
    perms['allow'] = [p for p in allow if p not in perms_to_remove]
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
except Exception:
    sys.exit(0)
"
      msg "install.uninstall.removed_permissions"
    fi
  else
    msg "install.uninstall.python_required_permissions"
  fi
}

uninstall_claude_skills() {
  local skills_dst="$HOME/.claude/skills"
  local ccb_skills="ask cping ping pend autonew mounted all-plan docs tp tr file-op review"

  if [[ ! -d "$skills_dst" ]]; then
    return
  fi

  msg "install.uninstall.remove_claude_skills"
  for skill in $ccb_skills; do
    if [[ -d "$skills_dst/$skill" ]]; then
      rm -rf "$skills_dst/$skill"
      echo "  Removed skill: $skill"
    fi
  done
}

uninstall_codex_skills() {
  local skills_dst="${CODEX_HOME:-$HOME/.codex}/skills"
  local ccb_skills="ask ping pend autonew mounted all-plan file-op"

  if [[ ! -d "$skills_dst" ]]; then
    return
  fi

  msg "install.uninstall.remove_codex_skills"
  for skill in $ccb_skills; do
    if [[ -d "$skills_dst/$skill" ]]; then
      rm -rf "$skills_dst/$skill"
      echo "  Removed skill: $skill"
    fi
  done
}

uninstall_droid_skills() {
  local skills_dst="${FACTORY_HOME:-$HOME/.factory}/skills"
  local ccb_skills="ask ping pend autonew mounted all-plan"

  if [[ ! -d "$skills_dst" ]]; then
    return
  fi

  msg "install.uninstall.remove_droid_skills"
  for skill in $ccb_skills; do
    if [[ -d "$skills_dst/$skill" ]]; then
      rm -rf "$skills_dst/$skill"
      echo "  Removed skill: $skill"
    fi
  done
}

uninstall_droid_delegation() {
  if ! command -v droid >/dev/null 2>&1; then
    return
  fi

  echo "Removing Droid MCP delegation..."
  if droid mcp remove ccb-delegation >/dev/null 2>&1; then
    echo "  Removed ccb-delegation MCP"
  fi
}

uninstall_droid_commands() {
  local cmds_dst="${FACTORY_HOME:-$HOME/.factory}/commands"
  local ccb_cmds="ask.md ping.md pend.md"

  if [[ ! -d "$cmds_dst" ]]; then
    return
  fi

  msg "install.uninstall.remove_droid_commands"
  for cmd in $ccb_cmds; do
    if [[ -f "$cmds_dst/$cmd" ]]; then
      rm -f "$cmds_dst/$cmd"
      echo "  Removed command: $cmd"
    fi
  done
}

uninstall_all() {
  msg "install.uninstall.start"

  # 1. Remove project directory
  if [[ -d "$INSTALL_PREFIX" ]]; then
    rm -rf "$INSTALL_PREFIX"
    msg "install.uninstall.project_removed" "$INSTALL_PREFIX"
  fi

  # 2. Remove bin links
  for path in "${SCRIPTS_TO_LINK[@]}"; do
    local name
    name="$(basename "$path")"
    if [[ -L "$BIN_DIR/$name" || -f "$BIN_DIR/$name" ]]; then
      rm -f "$BIN_DIR/$name"
    fi
  done
  for legacy in "${LEGACY_SCRIPTS[@]}"; do
    rm -f "$BIN_DIR/$legacy"
  done
  msg "install.uninstall.bin_removed" "$BIN_DIR"

  # 3. Remove Claude command files (clean all possible locations)
  local cmd_dirs=(
    "$HOME/.claude/commands"
    "$HOME/.config/claude/commands"
    "$HOME/.local/share/claude/commands"
  )
  for dir in "${cmd_dirs[@]}"; do
    if [[ -d "$dir" ]]; then
      for doc in "${CLAUDE_MARKDOWN[@]+"${CLAUDE_MARKDOWN[@]}"}"; do
        rm -f "$dir/$doc"
      done
      msg "install.uninstall.commands_cleaned" "$dir"
    fi
  done

  # 4. Remove collaboration rules from CLAUDE.md
  uninstall_claude_md_config

  # 5. Remove permission configuration from settings.json
  uninstall_settings_permissions

  # 6. Remove tmux configuration
  uninstall_tmux_config

  # 7. Remove Claude skills
  uninstall_claude_skills

  # 8. Remove Codex skills
  uninstall_codex_skills

  # 9. Remove Droid skills
  uninstall_droid_skills

  # 10. Remove Droid MCP delegation
  uninstall_droid_delegation

  # 11. Remove Droid commands
  uninstall_droid_commands

  msg "install.uninstall.ok"
  msg "install.uninstall.note"
}

main() {
  if [[ $# -ne 1 ]]; then
    usage
    exit 1
  fi

  case "$1" in
    install)
      install_all
      ;;
    uninstall)
      uninstall_all
      ;;
    *)
      usage
      exit 1
      ;;
  esac
}

main "$@"
