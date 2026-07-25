# Windows Rmux User Install Runbook

## Native Windows Beta Opt-In

Native Windows Rmux is a beta opt-in route. It is intended for users who explicitly want to run
CCB, ccbd, and rmux in the same native Windows environment.

Install from a checkout:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 install
```

The installer runs an rmux prerequisite check in `warn` mode by default. It reports whether
`rmux` or `psmux` is present, but it does not download rmux and it does not make Rmux the default
backend.

Available check modes:

- `detect_only`: report the prerequisite status only.
- `warn`: report missing or partial rmux and continue installation.
- `fail_fast`: stop installation if rmux or psmux cannot be probed.

## npm Entry

Native Windows Rmux is not installed through npm yet. `npm install -g @seemseam/ccb` remains the
Linux/macOS package route until the Windows npm artifact/checksum/postinstall gate passes.

## Diagnostics

Run:

```powershell
ccb doctor
```

Check these fields:

- `rmux_support_tier`
- `rmux_version`
- `rmux_capability_status`
- `rmux_validation_ref`
- `windows_install_entry`
- `windows_npm_enabled`
- `windows_install_ps1_rmux_check`
- `rmux_fallback_guidance`

`ccb doctor --output` includes the same projection under `generated/doctor.json`.

## Troubleshooting

- Route approval missing or rejected: stay on the Linux/macOS/WSL tmux route and inspect `rmux_support_tier`.
- Capability partial or blocking: install or update rmux/psmux, then rerun `ccb doctor`.
- Rmux missing: install rmux/psmux manually; CCB does not auto-download it.
- Provider auth failure: log in to the provider CLI in the same native Windows environment; this does not downgrade the rmux support tier.
- Validation incomplete: treat the route as beta or experimental until full Windows validation evidence is refreshed.

## Fallback

Use Linux/macOS/WSL tmux if native Windows Rmux is blocked, incomplete, or not needed for the
current project.
