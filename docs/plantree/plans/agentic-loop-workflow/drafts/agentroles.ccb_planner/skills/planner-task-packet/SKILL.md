---
name: planner-task-packet
description: Draft CCB workflow task packets, readiness recommendations, and candidate clarification questions without mutating authoritative state.
---

# Planner Task Packet

Use this skill when converting macro user intent or a frontdesk request into a
plan artifact for review.

## Inputs

- macro task request
- relevant plan-tree/source references
- explicit scope and non-goals
- current phase or prior round result if any

## Outputs

Produce these exact reply-visible sections. Do not replace them with prose,
tables, alternate headings, or "equivalent" sections.

- `task-packet.md`
- `readiness.json`
- `candidate-questions.jsonl` when user input may be needed

Use fenced blocks with these exact labels:

````markdown
**task-packet.md**
```markdown
# Task: <title>
Route: <direct_execution|needs_detail|macro_adjustment_request|blocked|partial_completion>
Allowed paths:
- <relative path, or leave empty when route is needs_detail/blocked>
Verification:
- <command or evidence review>
```

**readiness.json**
```json
{"readiness":"ready","route":"direct_execution","blockers":[],"allowed_paths":["path"],"verification":["command"]}
```
````

Readiness values are exactly:

- `ready`
- `needs_clarification`
- `blocked`
- `not_ready`

For `route: needs_detail`, use `readiness: needs_clarification`, include
specific `blockers`, include `verification` for the detail packet, and set
`allowed_paths` to an empty list. Do not authorize implementation paths until
detail is resolved.

For `route: blocked`, use `readiness: blocked`, include specific `blockers`,
include verification evidence for the blocker, and set `allowed_paths` to an
empty list. Do not authorize implementation paths for blocked prerequisites.

## Rules

- Do not mark task state directly.
- Do not start execution.
- Do not call workers, checkers, or orchestrator.
- Do not reduce acceptance criteria to make the task executable.
- Questions must be current-phase questions; defer later-phase questions.
