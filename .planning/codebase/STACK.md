# Technology Stack

**Analysis Date:** 2026-03-28

## Languages

**Primary:**
- Python 3.10+ - Main application logic, CLI tools, daemon services
- Bash - Installation and configuration scripts for Unix/Linux/macOS
- PowerShell - Installation and configuration scripts for Windows

**Secondary:**
- TOML - Configuration files (`.codex/config.toml`)
- JSON - Configuration and data serialization (`.claude/package.json`, `.gemini/package.json`)

## Runtime

**Environment:**
- Python 3.10+ (required minimum version)
- Bash shell (Unix/Linux/macOS)
- PowerShell 5.1+ (Windows)
- WSL support (Windows Subsystem for Linux)

**Package Manager:**
- pip (Python package manager)
- No lockfile detected (dependencies managed via pip)

## Frameworks & Core Libraries

**Core Application:**
- Custom daemon architecture (`askd` - Ask Daemon)
- Multi-provider support: Claude, Codex, Gemini, Droid, OpenAI
- Terminal backends: tmux, WezTerm

**Terminal Integration:**
- TmuxBackend - tmux session management
- WeztermBackend - WezTerm terminal support
- Multi-window routing support

**Communication:**
- Custom RPC protocol (`askd_rpc.py`)
- Socket-based inter-process communication
- Session-based message routing

## Key Dependencies

**Critical:**
- watchdog - File system event monitoring (optional, falls back to polling)
- Standard library modules: json, subprocess, threading, pathlib, argparse

**Infrastructure:**
- Terminal multiplexers: tmux, WezTerm
- Shell environments: bash, zsh, PowerShell

## Configuration

**Environment:**
- Environment variables for installation paths:
  - `CODEX_INSTALL_PREFIX` - Installation directory (default: `~/.local/share/codex-dual`)
  - `CODEX_BIN_DIR` - Binary directory (default: `~/.local/bin`)
  - `CCB_LANG` - Language preference (zh/en, auto-detect)
  - `CCB_PARENT_PID` - Parent process tracking

**Build:**
- `install.sh` - Unix/Linux/macOS installation
- `install.ps1` - Windows PowerShell installation
- `install.cmd` - Windows batch wrapper

**Configuration Files:**
- `.codex/config.toml` - Codex agent configuration
- `.claude/package.json` - Claude provider config
- `.gemini/package.json` - Gemini provider config
- `.clinerules` - CLI rules configuration

## Platform Requirements

**Development:**
- Python 3.10+
- Bash or PowerShell (depending on OS)
- Terminal multiplexer (tmux or WezTerm)
- Git (for version control)

**Production:**
- Linux/macOS/Windows (WSL recommended for Windows)
- Python 3.10+ runtime
- Terminal environment (tmux or WezTerm)
- Network connectivity for AI provider APIs

## Core Modules

**Main Entry Point:**
- `ccb` - Python executable script (main CLI launcher)

**Daemon System:**
- `lib/askd/daemon.py` - Daemon process management
- `lib/askd_server.py` - RPC server implementation
- `lib/askd_client.py` - RPC client implementation
- `lib/askd_runtime.py` - Runtime state management

**Provider Communication:**
- `lib/claude_comm.py` - Claude API communication
- `lib/codex_comm.py` - Codex provider communication
- `lib/codebuddy_comm.py` - CodeBuddy integration
- `lib/caskd_session.py` - Codex session management
- `lib/baskd_session.py` - Bask session management

**Terminal Management:**
- `lib/terminal.py` - Terminal backend abstraction
- `lib/compat.py` - Cross-platform compatibility

**Session & Project Management:**
- `lib/session_utils.py` - Session file operations
- `lib/pane_registry.py` - Pane registry management
- `lib/project_id.py` - Project identification
- `lib/claude_session_resolver.py` - Session resolution

**Utilities:**
- `lib/i18n.py` - Internationalization (Chinese/English)
- `lib/process_lock.py` - Process locking mechanism
- `lib/cli_output.py` - CLI output formatting

## Total Python Modules

- 98 Python files in `lib/` directory
- Modular architecture with clear separation of concerns

---

*Stack analysis: 2026-03-28*
