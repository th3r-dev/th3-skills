# Why this pipeline, and what it is built on

`plans` is not a new method — it wires together a discipline the industry already agreed on: write
the spec before the code, derive tests from the spec, build in thin slices, and keep the cheapest
agent that can finish each step. The engine
([`../poc-spec-driven-builder/SKILL.md`](../poc-spec-driven-builder/SKILL.md)) is the worked example;
these reference skills are the source material, each mapped to the phase it informs.

| Reference skill | Phase it informs | What it gives the pipeline |
|---|---|---|
| `spec-driven-development` | 1 · Clean the requirement | Spec before code; a broad requirement decomposed into a capability map of independently testable modules; V1 scope vs a V2 backlog. The SRS in engine step 2 is this, kept to a page. |
| `planning-and-task-breakdown` | 1 → 2 | The spec broken into ordered, verifiable tasks with explicit acceptance criteria, and which tasks can run in parallel — the input the agent-kit team claims issues from. |
| `test-driven-development` | 2 · Build cheap & fast | Tests written from the requirement before the implementation. This is engine step 3 (the full test matrix) landing before step 4 (build to green). |
| `incremental-implementation` | 2 · Build cheap & fast | Each change a thin vertical slice that leaves the system working and testable, so a half-built PoC is never a broken one. |

In-repo skills each phase leans on: [`../agent-kit/SKILL.md`](../../agent-kit/SKILL.md) (routing, team,
prompt cache), [`../design/SKILL.md`](../../design/SKILL.md), [`../qa/SKILL.md`](../../qa/SKILL.md),
[`../devops/SKILL.md`](../../devops/SKILL.md).

The rule that holds it together: the spec and the tests are what the agent builds *to*, not decisions
made while typing code. A PoC only proves something if what it proves was written down first.
