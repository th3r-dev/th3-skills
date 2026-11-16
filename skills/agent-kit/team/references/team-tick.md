# team-tick template (the lead's pass)

Copy to `.claude/skills/team-tick/SKILL.md` in the project and edit the role names.

```markdown
---
name: team-tick
description: One pass of the project's lead loop: read the GitHub board, send PRs to the playtester or reviewer, send changes back to workers, claim ready issues for role agents, update the state file, report. Use for "/team-tick", "/loop /team-tick", "run the team", "next issue".
---

# team-tick

You are the lead (the main session; subagents can't spawn subagents). All state is on GitHub and in
<state file>, so any session can run a pass. `T` = `uv run --script <agent-kit>/team/scripts/team.py`.

1. Board: `T board`. First pass of a session: also `T doctor`; keep its NEED rows for the report.
2. Playtest (if the project has one): no PR `status:playtesting` → the oldest `status:needs-playtest` → spawn `playtester` "PR #<n>".
3. Review: each `status:needs-review` PR → spawn `reviewer` "PR #<n>".
4. Changes: each `status:changes-requested` PR with no commit since the last review → SendMessage
   the worker if alive, else spawn its `agent:<role>`: "Fix PR #<n>: address the latest review comment".
5. New work, while fewer than 2 workers run: `T next --limit 1` → `T claim <n> <role>` → spawn `<role>`
   with `pcache.py brief "Issue #<n>: <title>" --role <role>` (or just "Issue #<n>: <title>").
6. Update <state file> (who is on what, what waits for the owner).
7. Report in one paragraph: spawned, finished, blocked, what needs the owner.

Rules: never merge, close or force-push. A role that fails its finish line twice →
`T release <n> "<why>" --blocked`. Under /loop: wake about every 1200 s, never more than 3600 s; stop
when nothing is ready, nothing to review and nothing running, and list what needs the owner.
```
