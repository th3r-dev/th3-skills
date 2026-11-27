---
name: plan-tick
description: One pass of the project's lead loop: read the GitHub board, send PRs to the reviewer, send changes back to workers, claim ready issues, update the state file, report. Use for "/plan-tick", "/loop /plan-tick", "run the team", "next issue".
---

# plan-tick

You are the lead (the main session; subagents can't spawn subagents). All state is on GitHub and in
the project's state file, so any session can run a pass. `T` = `uv run --script <agent-kit>/team/scripts/team.py`.

1. Board: `T board`. First pass of a session: also `T doctor`; keep its NEED rows for the report.
2. Review: each `status:needs-review` PR → spawn `reviewer` "PR #<n>".
3. Changes: each `status:changes-requested` PR with no new commit since the last review → SendMessage
   the worker if alive, else spawn its `agent:<role>`: "Fix PR #<n>: address the latest review comment".
4. New work, while fewer than 2 workers run: `T next --limit 1` → `T claim <n> <role>` → spawn `<role>`
   with a brief from `pcache.py brief "Issue #<n>: <title>" --role <role>`.
5. Update the state file (who is on what, what waits for the owner).
6. Report in one paragraph: spawned, finished, blocked, what needs the owner.

Rules: never merge, close or force-push. A role that fails its finish line twice →
`T release <n> "<why>" --blocked`. Under `/loop`: wake about every 1200 s, never more than 3600 s;
stop when nothing is ready, nothing to review and nothing running, and list what needs the owner.
