# Council review of the game brief

Five advisors attack `design/game-brief.md` from opposed angles, review each other blind, and a
chairman turns that into edits to the brief. It runs once, between step 3 (the brief) and step 4
(the engine) — a flaw found here costs one edit; found after a feature is built, it costs the build.

Method after Karpathy's LLM Council (different models answer, then rank each other anonymously), in
the one-model-five-lenses form the repo already uses for specs
([`poc-spec-driven-builder/references/council.md`](../../poc-spec-driven-builder/references/council.md)).
Text here is our own.

## The five lenses

Picked to pull against each other: fun vs scope, first-principles vs executor, the outsider between.

| Lens | Asks of the brief |
|---|---|
| **Contrarian (is it fun)** | Where does the loop become a chore? Assume a player is bored by minute five — what makes them quit? Which reward is noise, not a pull? |
| **First Principles** | Is the stated motivation the real draw, or a proxy for it? Would a smaller or different loop deliver that motivation better? |
| **Expansionist** | What is the bigger version of this game, and does the scope cap accidentally wall it off? (Keeping scope is the skill's job; this lens only names the door being closed.) |
| **Outsider (first 30s)** | A player who has never seen it: in the first minute, do they know what to do, what the goal is, how they win? Which term or mechanic only makes sense to the designer? |
| **Executor (buildable + ethics)** | Can the core loop be built, run and looked at in one sitting? What is the first file, which playtest is hardest to make real? Is any mechanic black-hat (`design-lens`'s audit)? |

## Step A: convene (parallel)

Spawn five subagents in one turn, one per lens, on the cheapest tier that reasons well (`sonnet`; see
[`agent-kit/cost`](../../agent-kit/cost/SKILL.md)). Every brief shares the same prefix so the cache holds:

```
You are one advisor on a council reviewing a game brief. Your lens: <LENS>: <row above>.
Stay in your lens; another advisor covers each other angle.

<full game-brief.md>
<the design-lens motivation / core loop / first-minute paragraphs>

Write 150-300 words. No preamble, no hedging. Name the section or feature you mean.
End with at most three concrete edits to the brief, each one line.
Done = the response is in range and every edit names a section or a feature.
```

## Step B: blind peer review (parallel)

Shuffle the five responses, label them A-E (shuffle so no lens always sits first). Spawn five
reviewers, each seeing all five labelled responses and the brief:

```
Five anonymous advisors reviewed this game brief. <brief> <A..E>
Answer in under 200 words:
1. Which response is strongest, and why?
2. Which has the biggest blind spot, and what is it?
3. What did all five miss about whether this game is fun or shippable?
Done = all three answered, each citing a letter or a section.
```

Reviewers may run one tier lower (`haiku`) when the brief is short; escalate if answers come back generic.

## Step C: chairman (inline)

The orchestrator is the chairman; no sixth agent. Un-blind the letters, read all ten outputs, and
decide — the stronger reasoning wins, not the majority. Then **apply** the verdict: edit the loop,
scope, milestones or success lines in `design/game-brief.md`, move anything the council cut to the
brief's "what is left for later", and append:

```markdown
## Council Review
- **Agrees:** what most advisors raised independently (high confidence)
- **Clashes:** both sides of each real disagreement, and which side the brief took
- **Blind spots:** what only the peer review surfaced
- **Verdict:** the change to the brief in one or two sentences, never "it depends"
- **First build:** the one feature to prototype first
```

## Rules

- The council replaces the clarifying question here; its verdict goes into the brief like any other
  assumption. Don't stop to ask the person mid-council.
- If the Contrarian's "this loop is a chore" holds up in review, fix the loop before the engine.
  Don't build a game the council has shown isn't fun.
- No subagents available (or no parallel): run the five lenses one after another inline, each written
  before reading the next, and skip Step B. Note the shortcut in the Council Review.
- Cost: ~10 subagent calls, once, before any build. That's the price of catching a bad loop before a
  feature is built on it.
