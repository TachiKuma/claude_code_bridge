---
doc_type: feature-evidence
feature: 2026-07-31-native-windows-public-workflow-validation-matrix
artifact: native-windows-transcript
status: blocked
---

# Native Windows Public Workflow Transcript

## Host Identity

- Host class: Native Windows x64 project host.
- OS platform required by matrix: `win32`.
- CPU architecture required by matrix: `x64`.
- Backend implementation required by matrix: `herdr`.
- Evidence class for current artifact: `blocked-evidence`.

## Transcript Status

This feature defines the transcript shape and archives a fail-closed matrix.
It does not claim pass evidence for the full public workflow set because every
required workflow has not been re-captured on the current Native Windows x64
host in one complete matrix run.

## Required Manual Capture List

The complete manual pass transcript must capture these commands or user
surfaces and then update
`.codestable/features/2026-07-31-native-windows-public-workflow-validation-matrix/evidence/windows-herdr-public-workflow-matrix.json`:

- `ccb`
- `ccb ask <target>`
- `ccb pend <target>`
- `ccb pend --watch <target>`
- `ccb ping`
- `ccb ping all`
- `ccb kill`
- `ccb restart`
- `ccb reload`
- foreground attach through `ccb`
- Mobile terminal history/message/websocket
- Config UI readonly terminal status
- `ccb doctor --output`
- `ccb update`
- support projection consumer smoke over the matrix JSON

## Current Result

- Verdict: blocked.
- Reason: Native Windows public workflow transcripts are not fully captured for
  every required workflow and public provider.
- Matrix status: all required workflow rows are `blocked`.
- Support candidate: `support_projection_allowed=false`.

