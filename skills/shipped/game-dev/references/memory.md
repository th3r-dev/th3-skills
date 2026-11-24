# Project memory: an Obsidian vault for the game

A game build runs for weeks, across many sittings and several agents. What was decided, what a
playtest found, what got cut and why — none of it should live only in a chat that ends. Keep it in a
local, Obsidian-compatible vault and feed it to each agent after the cached prefix, so the memory is
cheap to carry.

The vault and its tool are [`agent-kit/rag`](../../agent-kit/rag/SKILL.md) (claude-obsidian layout,
stdlib BM25, local-only); the briefs are [`agent-kit/prompt-cache`](../../agent-kit/prompt-cache/SKILL.md).
Don't rebuild either. This file is the game-dev mapping: what a game remembers, as what, and when.

## What a game remembers, and as which note

| Note type | Holds, for a game |
|---|---|
| `decisions/` | why this core loop, why the scope was cut, the council verdict, the monetization call (white-hat), each "three rounds, then redesign" turn |
| `sessions/` | one per build sitting and per playtest: the feature, what was run and looked at, PASS/FAIL, the NOT ASSESSED rows, the owner's milestone report |
| `concepts/` | the motivation, the loop, the first minute — the design-lens read, stable across the build |
| `sources/` | the engine docs read (dated — engines change weekly) and the references the project pins |

`design/game-brief.md` and the council verdict stay in the repo, committed (see
[`production-layout`](production-layout.md)); the vault is the working memory around them, kept local.

## In the build loop

The [agentic build loop](agentic-build.md) already briefs each role agent with
`pcache brief "<task>" --rag <vault>` (an [`agent-kit/team`](../../agent-kit/team/SKILL.md) rule), so
wiring memory in is four habits, not new code:

1. **The lead sets it up once** — `vault.py init`, and `migrate` an existing `progress.md` if there
   is one. The vault goes in `.git/info/exclude`, never committed.
2. **A playtest files its findings as a session note** before the loop moves on — the PASS/FAIL, the
   defects (which also become issues), the NOT ASSESSED rows. A design change files a decision note.
3. **`hot.md` holds the current milestone** — what is being built now. It is the same for every agent
   of a pass, so it rides inside the cached prefix; only the retrieved notes and the task differ.
4. **Re-index after writing** (`index` is milliseconds on unchanged files), so the next feature's
   agent retrieves the new notes in its brief.

One writer: the lead. Worktree agents never see the ignored vault — they get its knowledge through
the brief and report back, and the lead files it ([`agent-kit/rag`](../../agent-kit/rag/SKILL.md)
rule 2).

## Why it earns its place

The agent building feature N gets, after a byte-stable cached prefix, the playtest findings and
decisions from features 1..N-1 — so it doesn't re-break what a past sitting already fixed. A removed
farm that left day-one quests pointing at mobs that no longer existed is exactly the kind of thing a
decision note carries forward and a fresh agent, briefed only on the current task, would miss.

## Check

`agent-kit/rag` and `prompt-cache` carry the self-tests. For a game, the trail is the proof: every
playtest and design turn is a note, and `pcache stats` after a loop pass shows the briefs stayed warm.
