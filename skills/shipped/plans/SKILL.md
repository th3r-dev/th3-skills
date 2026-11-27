---
name: plans
description: >-
  Plan-then-build toolkit: one orchestrator that turns a loose idea into a working, evidence-backed
  result by running a fixed pipeline over the other th3-skills — (0) agent-kit sets up the model routing,
  a team and the work templates, (1) design plus a councilled SRS cleans the requirement, (2) qa and
  devops build it cheap and fast with a test matrix and a --selftest on every script, (3) ship it as a
  ticket and a PR. The engine is the plans-poc-spec-driven-builder sub-skill; this skill is the router.
  Use WHENEVER the work is "plan then build", "design then build", "prove this works", "is this feasible",
  "build a PoC", "prototype", "spec-driven", "set up the team and build it", "วางแผนแล้วทำ", "ทำ PoC",
  "พิสูจน์ว่าไอเดียนี้เวิร์ค". Read the sub-skill's SKILL.md before acting.
---

# plans: orchestrated spec-driven build

One idea in, a tested PR out. `plans` is the router; the step-by-step engine is
[`poc-spec-driven-builder/SKILL.md`](poc-spec-driven-builder/SKILL.md). Each phase hands off to the
th3-skill that already owns that job, so nothing here re-implements what another skill does.

| Phase | Read + route to | Engine step | Output |
|---|---|---|---|
| 0 · Prereqs & team | [`agent-kit`](../agent-kit/SKILL.md): [`cost`](../agent-kit/cost/SKILL.md) routes every agent to the cheapest tier, [`team`](../agent-kit/team/SKILL.md) stands up the board, [`prompt-cache`](../agent-kit/prompt-cache/SKILL.md) shares the cached brief prefix. Run `poc-spec-driven-builder/scripts/check_prereqs.sh`; copy the [`templates/`](templates/) into the target repo's `.claude/`. | 0–0.5 | tiers chosen, tracker picked, team board + role rule + command + MCP config in place |
| 1 · Clean the requirement | [`design`](../design/SKILL.md) when there are real screens or flows; the engine writes the SRS and a five-advisor council pressure-tests it | 1–2.2 | `SRS.md`, council verdict |
| 2 · Build cheap & fast | [`qa`](../qa/SKILL.md) for the test matrix (and a `--selftest` on anything stateful), [`devops`](../devops/SKILL.md) for infra and release-scope, agent-kit `cost` for the routing | 3–4 | test matrix green, every script self-checks |
| 3 · Ship | the engine files the ticket, writes the report, opens the PR | 2.5, 5, 6 | ticket, report, PR into `dev` |

The engine runs autonomously — an unspecified choice is logged as an SRS assumption, never a question
(see the sub-skill). `plans` adds only the routing: which skill owns each phase, and the work templates
Phase 0 drops into the project.

## Rules every phase keeps

- **The spec is the source of truth.** Build to the SRS and the test matrix, not to a running guess.
- **Reuse before building.** Each phase calls the skill that owns it; don't re-implement design, qa or devops here.
- **Cheap and fast is the default.** Any fan-out (the step-2.2 council, parallel workers) follows
  agent-kit `cost` + `prompt-cache`: the cheapest tier that finishes, a checkable finish line, a shared cached prefix.
- **A `--selftest` on anything stateful**, so a phase can prove itself without a full run.
- **No PR without a green build.** Phase 3 runs only after Phase 2's tests pass.

Background and the skills this pipeline is built on: [`references/best-practices.md`](references/best-practices.md).
