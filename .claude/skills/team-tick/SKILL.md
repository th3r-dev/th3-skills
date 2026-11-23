---
name: team-tick
description: One pass of th3-skills' lead loop: read the GitHub board, send PRs to the reviewer, send changes back to skill-dev, claim ready issues, report. Use for "/team-tick", "/loop /team-tick", "run the team", "next issue".
---

# team-tick

You are the lead (the main session; subagents can't spawn subagents). All state is on GitHub, so
any session can run a pass. `T` = `uv run --script skills/shipped/agent-kit/team/scripts/team.py`.

1. Board: `T board`. First pass of a session: also `T doctor`; keep its NEED rows for the report.
2. Review: each `status:needs-review` PR → spawn `reviewer` "PR #<n>".
3. Changes: each `status:changes-requested` PR with no commit since the last review → SendMessage
   the worker if alive, else spawn `skill-dev`: "Fix PR #<n>: address the latest review comment".
4. New work, while fewer than 2 `skill-dev` run: `T next --limit 1` → `T claim <n> skill-dev` →
   spawn `skill-dev` with the brief from
   `uv run --script skills/shipped/agent-kit/prompt-cache/scripts/pcache.py brief "Issue #<n>: <title>" --role skill-dev`.
5. Report in one paragraph: spawned, finished, blocked, and what waits for the owner
   (`status:ready-for-owner` PRs to merge, NEED rows, `blocked` issues).

Rules: never merge, close or force-push. A role that fails its finish line twice →
`T release <n> "<why>" --blocked`. Spawn only `skill-dev` and `reviewer`; their model is in their
definition. Under /loop: wake about every 1200 s, never more than 3600 s; stop the loop when
nothing is ready, nothing is in review and nothing is running, and list what needs the owner.
