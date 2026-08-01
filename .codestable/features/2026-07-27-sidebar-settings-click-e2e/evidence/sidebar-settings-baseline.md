# sidebar settings click e2e baseline

Recorded: 2026-07-27

## Environment probes

- `Get-Command rmux`: `C:\Users\Administrator\AppData\Local\Microsoft\WinGet\Packages\Helvesec.RMUX_Microsoft.Winget.Source_8wekyb3d8bbwe\rmux-0.9.0-windows-x86_64\rmux.exe`
- `Get-Command ccb`: `C:\Users\Administrator\AppData\Local\codex-dual\bin\ccb.bat`
- `sidebar_helper_fingerprint()`: `sha256:eb5a12e5f9acd0c0ad62802098d3c9fd49f34235271e44ca4cf850e693371bd8`

## Live rmux probes

- `rmux list-sessions`: failed with `no server running on \\.\pipe\rmux-S-1-5-21-1509734132-243468015-1433946896-500-il-high-default`
- `rmux list-panes -a -F ...`: failed with the same no-server result.
- `rmux list-keys -T root`: returned default root mouse bindings, but this is supporting evidence only because there is no live project sidebar pane.

## S1 result

S1 is complete as a blocked baseline: the run recorded the expected helper fingerprint and root binding availability, but no live rmux server/sidebar pane existed, so `@ccb_role=sidebar` and `@ccb_sidebar_helper_id` could not be observed from a real pane.
