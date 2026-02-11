<!-- CCB_CONFIG_START -->
## AI Collaboration
Use `/ask <provider>` to consult other AI assistants (codex/gemini/opencode/droid).
Use `/ping <provider>` to check connectivity.
Use `/pend <provider>` to view latest replies.

Providers: `codex`, `gemini`, `opencode`, `droid`, `claude`

<!-- CCB_ROLES_START -->
## Role Assignment

Abstract roles map to concrete AI providers. Skills reference roles, not providers directly.

| Role | Provider | Description |
|------|----------|-------------|
| `designer` | `claude` | Primary planner and architect — owns plans and designs |
| `inspiration` | `gemini` | Creative brainstorming — provides ideas as reference only (unreliable, never blindly follow) |
| `reviewer` | `codex` | Scored quality gate — evaluates plans/code using Rubrics |
| `executor` | `claude` | Code implementation — writes and modifies code |

To change a role assignment, edit the Provider column above.
When a skill references a role (e.g. `reviewer`), resolve it to the provider listed here (e.g. `/ask codex`).
<!-- CCB_ROLES_END -->

<!-- CODEX_REVIEW_START -->
## Peer Review Framework

The `designer` MUST send to `reviewer` (via `/ask`) at two checkpoints:
1. **Plan Review** — after finalizing a plan, BEFORE writing code. Tag: `[PLAN REVIEW REQUEST]`.
2. **Code Review** — after completing code changes, BEFORE reporting done. Tag: `[CODE REVIEW REQUEST]`.

Include the full plan or `git diff` between `--- PLAN START/END ---` or `--- CHANGES START/END ---` delimiters.
The `reviewer` scores using Rubrics defined in `AGENTS.md` and returns JSON.

**Pass criteria**: overall >= 7.0 AND no single dimension <= 3.
**On fail**: fix issues from response, re-submit (max 3 rounds). After 3 failures, present results to user.
**On pass**: display final scores as a summary table.
<!-- CODEX_REVIEW_END -->

<!-- GEMINI_INSPIRATION_START -->
## Inspiration Consultation

For creative tasks (UI/UX design, copywriting, naming, brainstorming), the `designer` SHOULD consult `inspiration` (via `/ask`) for reference ideas.
The `inspiration` provider is often unreliable — never blindly follow. Exercise independent judgment and present suggestions to the user for decision.
<!-- GEMINI_INSPIRATION_END -->

<!-- CCB_CONFIG_END -->
