---
name: oask
description: Delegate a task to OpenCode via the existing `oask` command (stdin-safe). Use only when the user explicitly asks to delegate to OpenCode (ask/@opencode/let opencode/review); NOT for questions about OpenCode itself.
---

# Delegate to OpenCode (oask)

This skill lets Codex delegate work to OpenCode by running the existing `oask` command.

## Trigger Conditions

Use this skill ONLY when the user explicitly delegates to OpenCode, e.g.:
- "@opencode …", "ask opencode …", "let opencode …"
- "use opencode to review/analyze/debug …"

DO NOT use this skill when:
- The user asks questions *about* OpenCode itself (how it works, install, config, etc.)
- The user mentions OpenCode without delegation intent

## Prerequisites / Troubleshooting

- OpenCode backend must be running: `ccb up opencode`
- If unsure, check status: `ccb status opencode`

## Execution

Run `oask` and pass the full user request via stdin (prevents shell backtick command substitution):

```sh
oask <<'EOF'
<paste the user’s delegation request verbatim>
EOF
```

Then relay OpenCode’s reply back to the user.
