---
name: cross-agent-skills
description: >-
  Make a skill (or a whole project) usable by any coding agent, not just Claude — Codex, Cursor,
  Gemini CLI, an MCP client — and hand work off between them reliably. Use WHENEVER the work is
  "another agent", "not just Claude", "Codex built this", "cross-agent", "agent interop", "works with
  Cursor/Gemini", "hand off between agents", "why did the other agent skip the flow", a non-Claude
  agent will run these skills, a skill assumes a tool the agent doesn't have, or an engine/MCP server
  is connected but its tools aren't in the agent's tool list. Built from a real run: a Codex session
  built a Roblox game with the game-dev skill, then was interviewed about what it read, skipped and
  worked around. Pairs with [`agent-kit/team`](../agent-kit/team/SKILL.md) (the handoff
  protocol) and [`agent-kit/cost`](../agent-kit/cost/SKILL.md).
---

# Cross-agent skills

A skill that only works for Claude is half a skill. These rules come from watching a non-Claude
agent (Codex) use one: where it diverged is where the skill assumed Claude.

## 1. The reader opens the sub-skill, not your flow

A non-Claude agent loads the file it is pointed at and starts. Interviewed, Codex said it went
straight to `roblox/SKILL.md` and never opened the umbrella `game-dev/SKILL.md` — so it never met
the flow or the gates that lived there. **Put a load-bearing gate where the work happens, not one
level up.** If an umbrella holds the preconditions, each sub-skill either repeats the two or three
that matter or refuses to proceed without them. "Read the parent first" is not a mechanism; an agent
that was handed the child won't.

## 2. Check your tools before you claim a check

The skill said "wire the agent to Studio through its MCP server" and assumed those tools sit in the
agent's tool list — the way they do for Claude. They weren't exposed to Codex, even though Studio
showed "MCP Ready." So a cross-agent step reads:

1. **Look at your own tool list.** Use the engine/MCP tools if they're there.
2. **Authorized fallback if they're not.** Codex drove Studio through computer-use (screen control)
   and inspected screenshots — a real playtest by another route.
3. **Otherwise NOT ASSESSED.** A check the agent could not run is named, never claimed as a pass.

The failure this prevents: an agent with no playtest tool writing "tested, works."

## 3. Nothing Claude-only on the critical path

The core job must not require the Agent/subagent tool, a slash command, or a Claude Code hook. Name
tools generically ("the engine's MCP server", "a browser you control"), and always give the
file-based path beside the tool-based one. A skill may mention Claude as the default and still work
for everyone — Codex followed the Rojo file workflow untouched — as long as nothing Claude-only is
*required* to finish.

## 4. Conventions that travel

What worked across agents, unchanged: a file-based layout, plain Markdown, stdlib-only scripts,
pinned tool versions, and triggers in the description. Keep every script runnable as
`python3 <path>` with no Claude runtime, and let a skill be read as flat files from a filesystem
root — that is how a non-Claude agent ingests it.

## 5. Make referenced scripts resolvable

Codex couldn't run `roblox_setup.py` — it wasn't at the path the skill named in its environment, and
resolving the skill root was friction. A script a skill tells the agent to run must be findable from
a path the agent can resolve (relative to the skill file, or discoverable), or the instruction is
dead for anyone whose install layout differs from yours.

## 6. Self-look is biased — capture for an outside reader

Codex did look in Studio, caught the petals reading as dots, and fixed them — then signed off a HUD
that still read weak to the owner. The building agent's own "looks good" is the least reliable
review of its own work. So the artifact of a visual step is a **capture** (screenshot + console) that
a *different* reader judges — the owner, a reviewer agent, or a council — not the builder's verdict.

## 7. Hand off in artifacts, not in chat

Asked what a Claude agent would need to continue its work, Codex named: a **git branch with the
source committed**, **one canonical brief** for goals and decisions, and **reproducible steps with
screenshots and console output**. There was no git repo, so the only trail was the files and the
conversation — which the next agent doesn't have. The handoff is real only when it survives the
session that made it. (The label-and-PR protocol is [`agent-kit/team`](../agent-kit/team/SKILL.md).)

## 8. Interview the agent that did the work

After a non-Claude agent finishes real work, resume its session and ask what it read, what it
skipped and why, and what it had to work around. It is the fastest way to find where a skill assumed
Claude — every rule above came from one such interview. For Codex: `codex exec resume <session-id>
--skip-git-repo-check -c approval_policy="never" -c sandbox_mode="read-only" "<questions>"`.

## Check

There is no script here yet. The test is a real one: hand a skill to a non-Claude agent, let it do
the work, interview it, and see whether rules 1–7 held. Each place they didn't is the next edit.
