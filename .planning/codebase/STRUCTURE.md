# Codebase Structure

**Analysis Date:** 2026-03-28

## Directory Layout

```
claude_code_bridge/
├── bin/                    # CLI command entry points
├── lib/                    # Core Python modules
├── config/                 # Configuration templates
├── docs/                   # Documentation
├── claude_skills/          # Claude-specific skill definitions
├── codex_skills/           # Codex-specific skill definitions
├── droid_skills/           # Droid-specific skill definitions
├── .claude/                # Claude workspace config
├── .codex/                 # Codex workspace config
├── .gemini/                # Gemini workspace config
├── .ccb/                   # Project-local CCB state
├── .planning/              # Planning and analysis docs
├── assets/                 # Documentation assets
├── install.sh              # Unix installation script
├── install.ps1             # Windows installation script
├── ccb                     # Main executable binary
└── README.md               # Project documentation
```

## Directory Purposes

**bin/:**
- Purpose: Executable CLI commands for user interaction
- Contains: Shell scripts wrapping Python modules
- Key files: `ask`, `cask`, `dask`, `gask`, `lask`, `oask`, `hask`, `bask`, `qask` (provider commands), `askd` (daemon), `*pend` (wait commands), `ccb-*` (utilities)

**lib/:**
- Purpose: Core Python implementation
- Contains: Daemon servers, communication modules, session management, terminal abstraction
- Key files: `askd_server.py`, `*_comm.py`, `terminal.py`, `providers.py`, `session_utils.py`

**config/:**
- Purpose: Configuration templates and defaults
- Contains: Provider configuration examples, environment setup
- Key files: Configuration YAML/JSON templates

**docs/:**
- Purpose: User and developer documentation
- Contains: Guides, API references, troubleshooting
- Key files: Markdown documentation files

**claude_skills/, codex_skills/, droid_skills/:**
- Purpose: Provider-specific skill definitions for multi-model workflows
- Contains: Skill metadata, templates, command definitions
- Key files: `all-plan/` subdirectories with skill implementations

**.claude/, .codex/, .gemini/:**
- Purpose: Provider-specific workspace configurations
- Contains: Agent definitions, command hooks, GSD (Get Shit Done) workflow templates
- Key files: `agents/`, `commands/`, `get-shit-done/` subdirectories

**.ccb/:**
- Purpose: Project-local CCB state and history
- Contains: Pane registry, session history, daemon state
- Key files: `pane-registry.json`, `history/` (auto-exported context)

**.planning/:**
- Purpose: Codebase analysis and planning documents
- Contains: Architecture, structure, conventions, testing patterns, concerns
- Key files: `codebase/ARCHITECTURE.md`, `codebase/STRUCTURE.md`, etc.

**assets/:**
- Purpose: Documentation media
- Contains: Screenshots, demo GIFs, badges
- Key files: `show.png`, `readme_previews/`

## Key File Locations

**Entry Points:**
- `bin/ask`: Main unified command for sending messages to any provider
- `bin/askd`: Daemon server launcher
- `bin/ccb`: Main executable binary (compiled or wrapper)
- `bin/lpend`: Wait for Claude reply (legacy)
- `bin/cpend`, `bin/dpend`, `bin/gpend`: Wait for provider-specific replies

**Configuration:**
- `config/`: Provider configuration templates
- `.clinerules`: CLI behavior rules
- `.gitignore`: Git exclusion patterns

**Core Logic:**
- `lib/askd_server.py`: Generic daemon server implementation
- `lib/askd_client.py`: Client for submitting requests to daemon
- `lib/providers.py`: Provider specifications and utilities
- `lib/terminal.py`: Terminal backend abstraction
- `lib/session_utils.py`: Session file I/O and discovery

**Communication:**
- `lib/claude_comm.py`: Claude-specific protocol
- `lib/codex_comm.py`: Codex-specific protocol
- `lib/gemini_comm.py`: Gemini-specific protocol
- `lib/droid_comm.py`: Droid-specific protocol
- `lib/opencode_comm.py`: OpenCode-specific protocol
- `lib/copilot_comm.py`: GitHub Copilot-specific protocol
- `lib/codebuddy_comm.py`: Tencent CodeBuddy-specific protocol
- `lib/qwen_comm.py`: Alibaba Qwen-specific protocol

**Session Management:**
- `lib/claude_session_resolver.py`: Claude session discovery
- `lib/laskd_registry.py`: Claude daemon registry
- `lib/pane_registry.py`: Pane-to-provider mapping
- `lib/session_utils.py`: Generic session utilities

**Daemon Protocols:**
- `lib/*askd_protocol.py`: Protocol definitions per provider (caskd, gaskd, oaskd, laskd, daskd, haskd, baskd, qaskd)
- `lib/*askd_session.py`: Session handling per provider

**Testing:**
- No dedicated test directory; tests likely in CI/CD workflows

## Naming Conventions

**Files:**
- `*_comm.py`: Provider communication modules
- `*askd_*.py`: Daemon-related modules (protocol, session, etc.)
- `*_utils.py`: Utility modules
- `bin/*`: Executable scripts (no extension on Unix)

**Directories:**
- `*_skills/`: Provider-specific skill collections
- `.*/`: Hidden configuration directories
- `lib/`: Core implementation modules

**Commands:**
- `ask <provider>`: Send message to provider
- `<provider>ask`: Legacy provider-specific command (e.g., `cask`, `dask`)
- `<provider>pend`: Wait for provider reply (e.g., `cpend`, `dpend`)
- `<provider>ping`: Check provider daemon status (e.g., `cping`, `dping`)

## Where to Add New Code

**New Provider Support:**
- Communication: Create `lib/<provider>_comm.py` with `send_prompt()`, `read_reply()` functions
- Protocol: Create `lib/<provider>askd_protocol.py` with request/reply format
- Session: Create `lib/<provider>askd_session.py` with session handling
- Provider Spec: Add `<PROVIDER>_SPEC` and `<PROVIDER>_CLIENT_SPEC` to `lib/providers.py`
- CLI: Create `bin/<provider>ask` wrapper script
- Wait Command: Create `bin/<provider>pend` wrapper script

**New Utility Function:**
- Location: `lib/session_utils.py` (session-related) or create new `lib/<domain>_utils.py`

**New Skill:**
- Location: `<provider>_skills/all-plan/` for multi-model workflows
- Structure: Subdirectory with skill metadata and implementation

**New Daemon Feature:**
- Location: `lib/askd_server.py` for core logic, `lib/askd_*.py` for protocol/session specifics

## Special Directories

**lib/askd/:**
- Purpose: Daemon subprocess management
- Generated: No
- Committed: Yes

**lib/mail/:**
- Purpose: Email integration for context transfer
- Generated: No
- Committed: Yes

**lib/mail_tui/:**
- Purpose: Terminal UI for mail operations
- Generated: No
- Committed: Yes

**lib/memory/:**
- Purpose: Memory/context persistence
- Generated: No
- Committed: Yes

**lib/web/:**
- Purpose: Web server integration
- Generated: No
- Committed: Yes

**.ccb/history/:**
- Purpose: Auto-exported context history per project
- Generated: Yes (by `ctx-transfer` command)
- Committed: No (in .gitignore)

**logs/:**
- Purpose: Runtime logs
- Generated: Yes
- Committed: No
