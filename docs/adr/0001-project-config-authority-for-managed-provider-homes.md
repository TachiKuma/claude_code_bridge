# Project Config Is the Authority for Managed Provider Homes

CCB-managed provider homes are generated runtime state, not a user configuration surface. For Codex agents such as `codex_aspai`, the project config is the authority for provider credentials, API base URL, model, and model catalog; when recorded provider state drifts from the current project config, startup must reject reuse of the old pane and relaunch with regenerated provider home state. Diagnostics should report the drift reason and redacted field-level differences without exposing secret values.
