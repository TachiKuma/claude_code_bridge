# sidebar settings foreground retest

Recorded: 2026-07-27

## Environment

- Host: native Windows
- Terminal: WezTerm foreground session
- Backend: rmux
- Session: `ccb-claude_code_bridge-b72b0116`
- Sidebar pane: `%0`
- Helper binary: `D:\Python\GitHub\claude_code_bridge\bin\ccb-agent-sidebar.exe`
- Helper fingerprint after rebuild: `sha256:41850a3b765275660291d842a6392149fe2f32bac339803083cba951e128bb98`
- Launch args identity: `sha256:1947d9580a65b89f9204d4f7965617454f921cb300f98b915878702e7ffd7603`

## Findings During Retest

1. The original refreshed pane had a current helper fingerprint but no running `ccb-agent-sidebar.exe`; `_refresh_running_sidebar_helpers()` was using an incomplete topology plan and a tmux backend against a live rmux namespace.
2. After fixing refresh, helper process `14272` was running with:
   `--ccbd-socket D:\Python\GitHub\claude_code_bridge\.ccb\ccbd\ccbd.sock --project-root D:\Python\GitHub\claude_code_bridge --pane-window main`.
3. A temporary rmux root binding probe changed `@ccb_mouse_binding_probe` from `reset` to `hit` after a real foreground click, proving WezTerm -> rmux root mouse binding was active.
4. A coordinate probe recorded `,,41,0,0,sidebar`: rmux resolved the mouse target pane and role but did not populate `mouse_x` or `mouse_y`.
5. `send-keys -t = -M` did not reach the Rust TUI mouse event probe. Direct `send-keys -t %0 c` opened config UI, proving the Rust settings action and config UI launch path were healthy.
6. Direct `send-keys -t %0 c` set `settings_action_observed=true` and showed `config ui: http://127.0.0.1:<port>/?token=...` in the sidebar, proving the Rust settings shortcut and config UI path are healthy.
7. A broad Windows/rmux fallback that mapped any sidebar left-click to `c` was tested and then rejected by the owner because it changes ordinary sidebar and `x` KillProject click semantics. The accepted current state is blocked until rmux provides coordinates/passthrough or a dedicated settings-only channel is implemented.

## Final Probe

`sidebar-mouse-probe.json` records the persisted click-probe state captured for the failed mouse route. It is intentionally not used as proof that direct `c` is a mouse click pass.

Observed diagnostic state from the foreground direct `c` transcript:

- `event_observed=false`
- `settings_action_observed=true`
- `mouse_event_count=0`
- `config_ui=config ui: http://127.0.0.1:<port>/?token=...`

The persisted `sidebar-mouse-probe.json` may remain at the failed click-probe state (`settings_action_observed=false`, `config_ui=null`) after retest cleanup or a later probe refresh. The direct `c` result above is diagnostic transcript evidence only, not accepted settings-click parity.

`event_observed=false` is retained intentionally. Current rmux does not expose coordinates and does not forward `send-keys -M` into the pane in this environment.
