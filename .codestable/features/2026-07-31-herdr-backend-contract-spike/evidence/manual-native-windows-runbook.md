---
doc_type: feature-evidence-runbook
feature: 2026-07-31-herdr-backend-contract-spike
status: active
---

# herdr-backend-contract-spike Native Windows Runbook

## Purpose

Run the Herdr contract spike on a dedicated Native Windows x64 host and write machine-readable evidence for downstream Herdr adapter decisions.

## Command

```powershell
cmd /c "set PATH=C:/Users/Administrator/AppData/Local/Programs/Herdr;%PATH% && C:/Users/Administrator/AppData/Local/Programs/Python/Python314/python.exe .codestable/roadmap/windows-native-herdr-ccb/drafts/herdr-backend-contract-spike/run_spike.py --platform-gate-ref .codestable/features/2026-07-31-windows-x64-v852-baseline-gate/evidence/platform-gate-summary.json --session ccb-herdr-spike --isolated-server --isolation-created-by-spike --isolated-socket-ref ccb-herdr-spike --herdr-socket-arg=--session --out .codestable/features/2026-07-31-herdr-backend-contract-spike/evidence/herdr-contract-spike-evidence.json"
```

## Safety Rules

- Use only a dedicated spike session named `ccb-herdr-spike`.
- For Herdr 0.7.5 preview, use `--herdr-socket-arg="--session"` because the CLI does not accept a global `--socket` option.
- Do not stop or restart a global Herdr server unless the runner has isolated session/socket/config evidence.
- Provider CLI dry run must not use credentials or claim CCB completion authority.
- If platform gate, Herdr executable, schema, provider dry run, or restart isolation is missing, keep the result fail-closed.

## Current Run Notes

- The checked platform gate artifact currently reports `supported=true`: v8.5.2 source admission, 64-bit Python, x64 Herdr, and x64 helper PE evidence are satisfied.
- The current runner reaches Herdr CLI schema/status/workspace/pane commands. `pane run` plus `pane wait-output` observes the sentinel, while detach/reattach remains unexercised from the non-Herdr harness and server restart restore is only partial: workspace/pane identity returns, but marker output history does not. Blocked evidence is valid spike output for this feature; it prevents downstream adapter work from treating partial Herdr behavior as supported.
