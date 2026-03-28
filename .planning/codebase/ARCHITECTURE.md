# Architecture

**Analysis Date:** 2026-03-28

## Pattern Overview

**Overall:** Multi-Model Async Messaging with Daemon-Based Provider Abstraction

**Key Characteristics:**
- Daemon-per-provider architecture with unified RPC protocol
- Async message passing via socket-based communication
- Terminal backend abstraction (WezTerm, tmux, etc.)
- Session-based state management per AI provider
- Lightweight prompt injection via pane control

## Layers

**CLI Layer:**
- Purpose: User-facing command interface
- Location: `bin/` (ask, cask, dask, gask, lask, oask, hask, bask, qask, etc.)
- Contains: Command wrappers that invoke daemon clients
- Depends on: askd_client, providers, session_utils
- Used by: End users via terminal

**Daemon Layer:**
- Purpose: Long-running provider-specific servers managing AI sessions
- Location: `lib/askd_server.py`, `lib/*askd_*.py` (protocol/session modules)
- Contains: Socket servers, request handlers, state management
- Depends on: providers, session_utils, terminal, process_lock
- Used by: CLI clients via RPC

**Communication Layer:**
- Purpose: Provider-specific protocol implementations
- Location: `lib/*_comm.py` (claude_comm.py, codex_comm.py, gemini_comm.py, etc.)
- Contains: Session resolution, prompt sending, reply parsing
- Depends on: terminal, pane_registry, session_utils, ccb_protocol
- Used by: Daemon request handlers

**Terminal Backend Layer:**
- Purpose: Abstract terminal multiplexer operations
- Location: `lib/terminal.py`
- Contains: Pane detection, text injection, log management
- Depends on: subprocess, platform-specific APIs
- Used by: Communication modules for prompt delivery

**Session Management Layer:**
- Purpose: Persist and resolve AI provider sessions
- Location: `lib/session_utils.py`, `lib/claude_session_resolver.py`, `lib/laskd_registry.py`
- Contains: Session file I/O, project ID computation, session discovery
- Depends on: Path operations, JSON serialization
- Used by: Communication and daemon layers

**Registry & State Layer:**
- Purpose: Track pane-to-provider mappings and daemon state
- Location: `lib/pane_registry.py`, `lib/process_lock.py`
- Contains: Pane registry persistence, provider locks
- Depends on: JSON, file I/O
- Used by: Daemon and CLI layers

## Data Flow

**Async Request Flow:**

1. User runs `ask claude "<message>"` (CLI)
2. `bin/ask` invokes `askd_client.submit_async_request()`
3. Client connects to daemon socket (or starts daemon if needed)
4. Request sent as JSON: `{req_id, provider, message, work_dir}`
5. Daemon receives, generates response file path
6. Returns immediately with `[CCB_ASYNC_SUBMITTED provider=xxx]`
7. User polls with `lpend` or waits for completion hook

**Sync Reply Retrieval:**

1. User runs `lpend` (wait for Claude reply)
2. Polls daemon state file or session log
3. Reads reply from provider's session file (`.claude/projects/...`)
4. Parses completion marker (`CCB_DONE`)
5. Returns reply text to user

**Prompt Delivery Flow:**

1. Daemon receives request from client
2. Resolves provider session (e.g., Claude project path)
3. Calls provider-specific `*_comm.send_prompt()`
4. Communication module:
   - Gets pane ID from session metadata
   - Injects prompt text via terminal backend
   - Monitors session log for reply
   - Parses and returns reply

**State Management:**

- Each provider maintains session files in provider-specific locations:
  - Claude: `~/.claude/projects/<project-key>/<session-id>.jsonl`
  - Codex: `~/.codex/sessions/<session-id>/`
  - Gemini: `~/.gemini/sessions/<session-id>/`
- Daemon state persisted in `~/.cache/ccb/askd/` (configurable)
- Pane registry stored in `.ccb/pane-registry.json` (project-local)

## Key Abstractions

**Provider Specification:**
- Purpose: Unified configuration for daemon and client specs
- Examples: `CASK_CLIENT_SPEC`, `GASK_CLIENT_SPEC`, `LASK_CLIENT_SPEC` in `lib/providers.py`
- Pattern: Dataclass with protocol prefix, env vars, session filename, daemon module

**Communication Protocol:**
- Purpose: Standardized request/reply format across providers
- Examples: `claude_comm.py`, `codex_comm.py`, `gemini_comm.py`
- Pattern: Each module implements `send_prompt()`, `read_reply()`, session resolution

**Terminal Backend:**
- Purpose: Abstract multiplexer differences (WezTerm, tmux, etc.)
- Examples: `get_pane_id_from_session()`, `get_backend_for_session()` in `lib/terminal.py`
- Pattern: Backend detection via environment, pane operations via subprocess

**Daemon Protocol:**
- Purpose: RPC between CLI and daemon
- Examples: `askd_rpc.py`, `*askd_protocol.py` modules
- Pattern: JSON-based socket communication with token authentication

## Entry Points

**CLI Commands:**
- Location: `bin/ask`, `bin/cask`, `bin/dask`, `bin/gask`, `bin/lask`, `bin/oask`, `bin/hask`, `bin/bask`, `bin/qask`
- Triggers: User invocation from terminal
- Responsibilities: Parse args, invoke daemon client, handle async submission

**Daemon Server:**
- Location: `lib/askd_server.py` (generic), spawned by `bin/askd`
- Triggers: Auto-started by client or manual invocation
- Responsibilities: Listen for RPC requests, dispatch to provider handlers, manage state

**Provider Handlers:**
- Location: `lib/*_comm.py` modules
- Triggers: Daemon receives request for specific provider
- Responsibilities: Session resolution, prompt injection, reply parsing

## Error Handling

**Strategy:** Graceful degradation with fallback mechanisms

**Patterns:**
- Session resolution: Try multiple paths (project-local, user-level, legacy formats)
- Daemon startup: Auto-start if not running, with timeout
- Reply parsing: Idle timeout detection (e.g., `CCB_GEMINI_IDLE_TIMEOUT`)
- Terminal injection: Fallback to alternative pane detection methods
- Async completion: Degraded mode accepts partial markers

## Cross-Cutting Concerns

**Logging:** File-based per-pane logs in `~/.cache/ccb/pane-logs/` with configurable rotation

**Validation:** Environment variable parsing with defaults, path normalization, session ID validation

**Authentication:** Token-based daemon RPC, provider-specific session tokens in session files

**Concurrency:** Process locks per provider (`lib/process_lock.py`), thread-safe daemon request handling
