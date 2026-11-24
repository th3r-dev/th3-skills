# Agentic build: hand steps 5–6 to a loop

Once the brief locks (step 3, the person said "build it") and the engine runs (step 4), the build
is the same move over and over — name a feature, build it, run it, look at it, commit it. That
repeats cleanly across agents, so it can run as an agentic loop instead of by hand. Design (steps
1–3) and the cut (step 7) stay with the person; the loop owns 5–6 and hands each milestone back.

The loop itself is [`agent-kit/team`](../../agent-kit/team/SKILL.md) — a lead loop in the main
session, role agents each on their own GitHub issue in their own worktree, all state on GitHub.
Don't re-build any of that here. This file is only the game-dev binding: what the issues are, which
roles play them, and the rule that every agent keeps the flow's gates.

## From brief to issues

The brief's "features in build order" become one issue each, smallest first:

- Title is the feature. Its "Done when" checklist is the brief's line for that feature **plus run
  and looked at** — a browser screenshot, or a Studio playtest's capture. A parse is not a run.
- `Depends on #N` for anything the feature builds on; milestones named `M1 …`, `M2 …` set the order.
- A feature with a screen gets its UI brief approved first ([`../design-ui/SKILL.md`](../design-ui/SKILL.md)).
  That approval is its own issue, and a dependency of the feature.

Scope is already locked, so no issue adds a system the brief cut. A new idea is a new issue for
later, never stacked on the build.

## Roles

| Role | Does | Finish line |
|---|---|---|
| `builder` | takes one feature issue, writes the engine code in files, runs it, captures it | draft PR "Closes #N", code runs, capture attached |
| `playtester` (Roblox) | plays the PR in Studio through the MCP server | PASS/FAIL table with screenshots — [`../roblox/references/agentic-playtest.md`](../roblox/references/agentic-playtest.md) |
| `reviewer` | reads the PR against its "Done when" and the gates below | ready-for-owner, or changes-requested with the reason |

The handoff between them is [`agent-kit/team`'s protocol](../../agent-kit/team/SKILL.md) — labels
and PR comments, nothing in chat. The owner merges and plays the milestone; no agent merges.

## Every agent carries the instructions

The loop is only safe if each agent runs the flow, not its own idea of the game. So each agent's
brief:

1. **Preloads this skill in full** (`skills: [game-dev]` in the role's `.claude/agents/<role>.md`) —
   the flow, the rules and the gates are in the agent's context before it writes a line.
2. **Ends with the feature's "Done when."** That is the finish line; an agent with no finish line
   loops (`agent-kit/cost` rule 3).
3. **Is stopped at the gate, not after it.** The reviewer blocks a PR that skipped one:
   - a change the player sees with no capture across the
     [viewport matrix](../design-ui/references/layout.md#viewport-matrix) — `OWNER EYE` is not a
     pass, and a dropped NOT ASSESSED row fails the review;
   - a visible defect against the brief written up as a "known limit";
   - a fourth fix round on one problem instead of a redesign (three rounds, then change the approach);
   - work stacked on an unmerged PR, or a removed system whose users weren't listed first.

A gate the agent couldn't run is NOT ASSESSED by name — never a silent pass. It is the same rule
the person's own build keeps; the loop doesn't get a looser one.

## Stop and hand back

The lead stops the loop when nothing is ready, in review, or running, and lists what needs the
person: a milestone to play, a UI brief to approve, an issue that's blocked. The person plays the
milestone — join → first goal → a failure → the recovery → the sale — and each thing they report
becomes its own issue, back into the loop.

## Check

`agent-kit/team`'s trail: every handoff shows as a label change or a PR comment, with no step that
lives only in chat. The build itself is checked the flow's way — the game was run and looked at, per
issue.
