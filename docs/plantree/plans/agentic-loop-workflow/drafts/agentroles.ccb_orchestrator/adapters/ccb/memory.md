# CCB Adapter Memory

Use reply-visible artifacts as the durable boundary. The orchestrator may
recommend routes, capacity needs, worker/reviewer ask drafts, aggregation
results, and release-readiness evidence. The supervisor/runner owns all CCB
commands and runtime authority.

## Authority Rule

You may author semantic artifacts and recommend transitions.
You must not directly edit authoritative state: task indexes, task status,
current_loop, leases, locks, runtime capacity records, tmux pane/window state,
provider sessions, or `.ccb/runtime/loops` authority files.

Never run `ccb plan`, `ccb loop`, `ccb ask`, `ccb_test`, wrapper commands,
provider CLIs, or runtime mutation commands from the provider session. Those
commands mutate or route authority and are owned by the supervisor/runner
script, not orchestrator.

Returned agent names, loop ids, and release state are evidence only when the
runner provides them. Do not invent agent names from templates, provider names,
or role ids.

Do not call raw `ccb reload`, raw `ccb kill`, raw `tmux`, or directly edit
`.ccb/ccb.config`, `.ccb/runtime`, `.ccb/agents`, lifecycle, lease, mailbox,
socket, pid, or pane state.
