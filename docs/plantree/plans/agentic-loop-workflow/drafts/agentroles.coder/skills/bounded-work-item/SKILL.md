---
name: bounded-work-item
description: Execute one scoped implementation or investigation item and return evidence without changing workflow authority.
---

# Bounded Work Item

Use this skill when the orchestrator assigns a single work item with explicit
scope, non-goals, acceptance criteria, and verification expectations.

## Workflow

1. Read the task packet, execution contract, and assigned scope.
2. Inspect relevant files before editing. Detect repository metadata once; if
   the assigned workspace is not a Git checkout, do not keep trying Git
   commands. Use the assigned paths, direct file inspection, focused tests,
   and runner-provided promotion evidence instead.
3. Make the smallest change that satisfies the scoped item.
4. Run focused verification when possible.
5. After the final required verification command completes, stop tool use and
   send the final answer immediately.
6. Return files changed, evidence, blockers, and the result:
   `done`, `blocked`, or `needs_rework`.

## Boundaries

- Do not lower acceptance criteria.
- Do not silently substitute fallback behavior.
- Do not claim whole-round success.
- Do not directly edit authoritative CCB state or runtime files.
- Do not run CCB commands or workflow wrappers; the supervisor/runner owns
  task authority and runtime transitions.
