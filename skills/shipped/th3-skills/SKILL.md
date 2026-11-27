---
name: th3-skills
description: >-
  The front door to the th3-skills toolkit: read what the user is actually trying to do and route it
  to the one skill that owns it, instead of guessing or hand-rolling. This is the default way to start
  any job in a project that has th3-skills installed. Use WHENEVER a request opens new work and the
  right skill isn't already obvious — "let's build this", "where do I start", "set up the workflow",
  "run the th3 workflow", "/th3-skills", "help me ship this", "วางแผนงาน", "เริ่มงานนี้ยังไง", "ใช้ th3-skills" —
  or any task that plausibly belongs to one of the toolkit's skills (plan/build, design, test, infra,
  games, marketing, docs, agents, dependencies, containers, mock data, cross-agent). Routes; it does
  not do the work itself — it hands off to the owning skill, defaulting to plans for anything that gets
  built. Read the chosen skill's SKILL.md before acting.
---

# th3-skills: the front door

One command for "I have a job, which skill does it?". Read the request, pick the row below, open that
skill's SKILL.md, and work from there. When a job spans phases — plan, design, test, ship — start at
[`plans`](../plans/SKILL.md); it already chains the others.

| When the work is… | Route to |
|---|---|
| Build / prove an idea, plan then build, "is this feasible", a PoC, spec-driven work (the default for anything that ships) | [`plans`](../plans/SKILL.md) |
| A screen, page, component, flow, UI copy, a banner, a game thumbnail or key art | [`design`](../design/SKILL.md) |
| Test evidence, a QA report, test-case design for an import, a pre-meeting answer review | [`qa`](../qa/SKILL.md) |
| ssh / infra change, a root cause, what's in a release, a system or network diagram | [`devops`](../devops/SKILL.md) |
| A game — idea to playable, Roblox, VFX, engine MCP, game UI, 3D models | [`game-dev`](../game-dev/SKILL.md) |
| Pricing, a marketplace listing, a blog post or its cover | [`marketing`](../marketing/SKILL.md) |
| Document or report something, a house-style PDF/DOCX, PDF page ops | [`documentation`](../documentation/SKILL.md) |
| The release report for the PM / BA / QA | [`software-engineer`](../software-engineer/SKILL.md) |
| Spawning agents, picking a model, prompt caching, an agent team, project RAG | [`agent-kit`](../agent-kit/SKILL.md) |
| A Dependabot alert, a CVE/GHSA, "does this vuln reach us" | [`dependency-vuln-explainer`](../dependency-vuln-explainer/SKILL.md) |
| Podman disk too big, prune / shrink container storage | [`containers`](../containers/SKILL.md) |
| Fake-but-realistic Thai test data | [`thai-mock-naming`](../thai-mock-naming/SKILL.md) |
| Making a skill or project work on Codex / Cursor / Gemini, handing off between agents | [`cross-agent-skills`](../cross-agent-skills/SKILL.md) |

## How to route

1. **Name the job in one line.** What outcome does the user actually want?
2. **Match the clearest row.** If two fit, pick the one that owns the *end* artifact (a tested build → `plans`, even if it also needs design).
3. **Default to `plans`** whenever something is getting built or proven and no single row is obviously it — `plans` sets up the team (via `agent-kit`), cleans the requirement (with `design`), builds cheap and fast (`qa` + `devops`), and ships.
4. **Open that skill's SKILL.md and follow it.** This front door only routes; the owning skill does the work.
5. If nothing fits, say so and proceed without a skill — don't force one.
