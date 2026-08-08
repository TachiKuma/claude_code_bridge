# Herdr v0.8.0 Capability Probe

## Probe commands executed

- `herdr-v0.8-version`: exit=0, elapsed=29ms
- `herdr-v0.8-api-help`: exit=0, elapsed=31ms
- `herdr-v0.8-status-server`: exit=0, elapsed=28ms
- `herdr-v0.8-plugin-list`: exit=0, elapsed=33ms
- `herdr-v0.8-help`: exit=0, elapsed=28ms
- `herdr-v0.8-session-list`: exit=0, elapsed=32ms
- `herdr-v0.8-status`: exit=0, elapsed=27ms

## Integration Readiness Assessment

| Capability | v0.7.5 Status | v0.8.0 Probe Result | C2 Impact |
|---|---|---|---|
| Session reporting format | `herdr status server --json` | see `herdr-v0.8-status-server.stdout.txt` | CCB→Herdr evidence path |
| Plugin system | CLI-wrapped only | see `herdr-v0.8-plugin-list` | B-lite feasibility |
| API surface | `api snapshot`, `api workspace` | see `herdr-v0.8-api-help.stdout.txt` | C2 pane lifecycle |
| Lifecycle reporting | Kimi/Qoder/Cursor simplified | see `herdr-v0.8-status.stdout.txt` | C2 integration pattern |
| Session list/attach | `session list`/`attach`/`stop`/`delete` | see `herdr-v0.8-session-list.stdout.txt` | C2 session lifecycle |
| License | unknown | check `herdr-v0.8-version.stdout.txt` | Apache-2.0 confirmed? |

## Raw evidence

Full command outputs under `raw-command-refs/herdr-v0.8-*`.
