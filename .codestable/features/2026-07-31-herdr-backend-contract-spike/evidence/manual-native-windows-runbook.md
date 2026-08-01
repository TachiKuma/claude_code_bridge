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
python ".codestable/roadmap/windows-native-herdr-ccb/drafts/herdr-backend-contract-spike/run_spike.py" --platform-gate-ref ".codestable/features/2026-07-31-windows-x64-v852-baseline-gate/evidence/platform-gate-summary.json" --session ccb-herdr-spike --isolated-server --isolation-created-by-spike --isolated-socket-ref ".codestable/features/2026-07-31-herdr-backend-contract-spike/evidence/isolated-herdr.sock" --out ".codestable/features/2026-07-31-herdr-backend-contract-spike/evidence/herdr-contract-spike-evidence.json"
```

## Safety Rules

- Use only a dedicated spike session named `ccb-herdr-spike`.
- Do not stop or restart a global Herdr server unless the runner has isolated socket/config evidence.
- Provider CLI dry run must not use credentials or claim CCB completion authority.
- If platform gate, Herdr executable, schema, provider dry run, or restart isolation is missing, keep the result fail-closed.

## Current Run Notes

- The checked platform gate artifact currently reports `supported=false`, so the runner is expected to write blocked evidence and skip Herdr operations.
- Blocked evidence is valid spike output for this feature; it prevents downstream adapter work from treating unknown Herdr behavior as supported.
