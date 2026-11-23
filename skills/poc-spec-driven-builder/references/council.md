# Council review of the SRS

Five advisors attack the draft SRS from opposed angles, review each other blind, and a chairman turns
that into edits to the spec. It runs once, between Step 2 (SRS) and Step 2.5 (ticket), because a flaw
found here costs one edit; found after the tests are written, it costs the tests too.

Method after Karpathy's LLM Council (different models answer, then rank each other anonymously),
in the form popularised by `aiwithremy/claude-skills-llm-council`: one model, five thinking lenses
instead of five models. Text here is our own; that repo carries no license.

## The five lenses

Picked to pull against each other: Contrarian vs Expansionist, First Principles vs Executor, the
Outsider between them.

| Lens | Asks of the SRS |
|---|---|
| **Contrarian** | Where does this PoC fail or prove nothing? Which FR could pass while the idea is still wrong? Assume a fatal flaw and find it. |
| **First Principles** | Is §1 the real uncertainty, or a proxy for it? Would a different, smaller experiment answer the question better? |
| **Expansionist** | What is the bigger version of this idea, and does the scope accidentally close the door on it? Risk is not this lens's job. |
| **Outsider** | No context on the user, the domain, or the repo. Which terms are undefined, which assumptions only make sense to an insider? |
| **Executor** | Can this be built and tested with the chosen stack in a day or two? What is the first file written, and which test is hardest to make real? |

## Step A: convene (parallel)

Spawn five subagents in one turn, one per lens, on the cheapest tier that reasons well (`sonnet` on
Claude Code; see `agent-kit/cost`). Every brief shares the same prefix so the prompt cache holds:

```
You are one advisor on a council reviewing a PoC spec. Your lens: <LENS NAME>: <lens row above>.
Stay in your lens; another advisor covers each other angle.

<full SRS.md>
<Step 1 research bullets>

Write 150-300 words. No preamble, no hedging. Name the FR/NFR/section ids you are talking about.
End with at most three concrete edits to the SRS, each one line.
Done = the response is in range and every edit names a section or requirement id.
```

## Step B: blind peer review (parallel)

Shuffle the five responses and label them A-E (shuffle so no lens always sits first). Spawn five
reviewers, each seeing all five labelled responses and the SRS:

```
Five anonymous advisors reviewed this PoC spec. <SRS> <A..E>
Answer in under 200 words:
1. Which response is strongest, and why?
2. Which has the biggest blind spot, and what is it?
3. What did all five miss?
Done = all three questions answered, each citing a letter or a section id.
```

Reviewers may run one tier lower (`haiku`) when the SRS is short; escalate if their answers come back
generic.

## Step C: chairman (inline)

The orchestrator is the chairman; no sixth agent. Un-blind the letters, read all ten outputs, and
decide. The chairman may side with one dissenter over four who agree if the reasoning is stronger.
Majority is not a reason.

Then **apply** the verdict: edit FRs, NFRs, scope or success criteria in `SRS.md`, move anything the
council pushed out to §2 Out of scope, and log each accepted or rejected edit in §6 Assumptions with
the lens that raised it. Append the verdict to the SRS as §8:

```markdown
## 8. Council Review
- **Agrees:** points most advisors made independently (high confidence)
- **Clashes:** both sides of each real disagreement, and which side the spec took
- **Blind spots:** what only the peer review surfaced
- **Verdict:** the change to the spec in one or two sentences, never "it depends"
- **First move:** the one test or file to write first
```

## Rules

- Never ask the user anything here. The council replaces the clarifying question; its verdict goes
  into §6 like any other assumption.
- If the council concludes the PoC proves nothing (the Contrarian's fatal flaw holds up in review),
  rewrite §1 and §7 before going on. Don't build a PoC the council has shown can't fail.
- No subagents available (or the host can't run them in parallel): run the five lenses one after
  another inline, each written before reading the next, and skip Step B. Note the shortcut in §8.
- Cost: 10 subagent calls per PoC. That's the price of catching a bad spec before the tests exist; it
  runs once, not per iteration.
