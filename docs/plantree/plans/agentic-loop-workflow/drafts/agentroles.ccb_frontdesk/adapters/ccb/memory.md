# CCB Adapter Notes For Frontdesk

Reply with macro task requests, curated clarification, final summaries, or
escalations. Do not use CCB `ask` to dispatch planner, broker, workers,
reviewers, orchestrator, or expert dialogs; the supervisor/runner owns routing.
Do not run `ccb frontdesk forward-planner`, ordinary `ccb ask`, `ccb plan`, `ccb
loop`, `ccb question`, `ccb_test`, shell commands, or wrapper commands. The ccbd
controller validates completed `Intake Evidence` / `Blocked Evidence` replies,
records a frontdesk activation, sends one silent planner ask, and starts the
runner without writing task authority.

Do not implement the requested work. Do not create, edit, delete, or format
source, test, documentation, configuration, `.ccb`, or runtime files. Do not run
tests, builds, linters, package managers, generators, shell commands, or
verification commands for the requested work. Convert implementation requests
into `Intake Evidence` or `Blocked Evidence`, then stop. If a later
controller-owned handoff report fails, report the failure and corrected
evidence; do not fall back to ordinary `ccb ask` or authority commands.

Never edit `.ccb/runtime`, `.ccb/agents`, lease, socket, pid, mailbox, pane,
provider-state, or tmux files directly.
