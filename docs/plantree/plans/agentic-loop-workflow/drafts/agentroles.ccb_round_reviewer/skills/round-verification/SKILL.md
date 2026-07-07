---
name: round-verification
description: Verify integrated round evidence and return a machine-readable round result for script import.
---

# Round Verification

Use this skill after a bounded execution round has produced orchestrator,
coder, and code-reviewer evidence.

## Workflow

1. Read the task packet, execution contract, orchestrator summary, coder
   results, and code-reviewer results.
2. Check whether acceptance criteria were satisfied without hidden fallback,
   scope shrinkage, or missing evidence.
3. Return exactly one machine-readable result line as the first non-empty line
   of the reply.

```text
round result: pass|partial|replan_required|blocked
```

Do not write any preamble, heading, Markdown fence, bullet, quote, or backtick
before or around that first line. Put evidence and audit details after it.
Do not run tests, tools, shell commands, CCB commands, or workflow wrappers
before producing the first line; verify from the evidence already supplied. If
the evidence is insufficient, start with `round result: blocked`.
A later `round result: pass` after prose is invalid and will be blocked by the
runner.

## Boundaries

- Do not fix code.
- Do not run tests or tools.
- Do not change product scope.
- Do not infer pass without evidence.
- Do not directly edit authoritative CCB state or runtime files.
