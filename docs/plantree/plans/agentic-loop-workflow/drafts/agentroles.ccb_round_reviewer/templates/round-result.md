round result: pass|partial|replan_required|blocked
task id: <task-id>
loop id: <loop-id>
round id: <round-id>

The `round result:` line above must be the first non-empty line of the reply.
Do not put any preamble before it. Do not wrap it in a Markdown fence, bullet,
quote, or backticks.
Do not run tests, tools, shell commands, CCB commands, or workflow wrappers
before this line. Judge only supplied evidence. If evidence is insufficient,
use `round result: blocked` as the first line.

## Evidence Reviewed

- planner verification contract: <ref>
- orchestrator summary: <ref>
- node reports: <refs>

## Integrated Verification

- <check and result>

## Next Recommendation

- <done, rework node, replan, escalate, or pause>
