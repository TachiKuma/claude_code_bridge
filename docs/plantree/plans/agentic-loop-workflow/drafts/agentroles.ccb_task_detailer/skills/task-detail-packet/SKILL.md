---
name: task-detail-packet
description: Draft task-scoped detail artifacts and a detail packet as reply content for script-owned workflow import.
---

# Task Detail Packet

Use this skill when a macro task packet needs task-local execution detail before
orchestrator dispatch.

## Workflow

1. Read macro task refs, plan-tree refs, accepted decisions, source files,
   tests, and prior evidence.
2. Draft task-scoped detail design and source-evidence map.
3. Produce detailed acceptance, verification, and worker handoff notes.
4. Return a detail packet suitable for supervisor/runner script import.
5. If detail is blocked, return clarification or macro-adjustment evidence.

## Boundaries

- Do not rewrite roadmap or accepted decisions directly.
- Do not lower acceptance criteria.
- Do not dispatch runtime agents.
- Do not directly edit authoritative CCB state or runtime files.
- Do not run `ccb plan`, `ccb loop`, `ccb ask`, `ccb_test`, or wrapper
  commands.
- Do not write detail artifacts into the project tree for later self-import;
  put artifact content in the reply.
