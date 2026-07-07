# CCB Adapter Notes For Coder

Use only the assigned project workspace and CCB-visible instructions. Do not
edit task indexes, status, `current_loop`, runtime topology, provider state, or
tmux state directly.

Do not run `ccb`, `ccb_test`, `ccb plan`, `ccb loop`, `ccb ask`, or workflow
wrappers. The supervisor/runner owns task authority, artifact import, runtime
capacity, and cleanup. Return implementation evidence for script-owned import
or reviewer inspection.
