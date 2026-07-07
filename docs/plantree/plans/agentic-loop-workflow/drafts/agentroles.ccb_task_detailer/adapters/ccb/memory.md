# CCB Adapter Notes For Task Detailer

Use reply-visible artifacts as the durable boundary. Prefer producing
`task-detail-design.md`, `brief-update-summary.md`, and `detail-packet.md`
sections for the supervisor/runner to import or review.

Never run `ccb plan task-artifact`, `ccb plan task-status`, `ccb plan
task-create`, `ccb loop`, `ccb ask`, `ccb_test`, or wrapper commands from the
provider session. Those commands mutate or route authority and are owned by the
supervisor/runner script, not task_detailer.

Never edit `.ccb/runtime`, `.ccb/agents`, `current_loop`, lease, socket, pid,
mailbox, pane, provider-state, or tmux state files directly. Do not write
supervisor import files into the project tree for later self-import.

If detail needs macro plan changes, produce a macro-adjustment request as an
artifact; scripts and planner decide whether to apply it.
