---
name: agent-kit
description: >-
  Agent toolkit, one skill with sub-skills for running Claude Code agents cheaply. (1) cost: route each
  agent to the cheapest model tier that can finish it, give it a checkable finish line, skip agents the
  task doesn't need, with a PreToolUse hook that nudges Agent calls that set no model; (2) prompt-cache:
  keep agent prompt prefixes byte-identical so the prompt cache hits, with a uv-run script that builds a
  fingerprinted project outline, writes agent briefs and reports per-agent hit rate. Use WHENEVER you
  are about to spawn subagents, forks, parallel agents or a Workflow, run /loop or ScheduleWakeup, pick
  a model for an agent, or the user says "save tokens", "agent cost", "which model", "prompt caching",
  "cache hit", "token usage", "ลด token". Read the sub-skill's SKILL.md before acting.
---

# agent-kit: sub-skills

| When the work is… | Read | Scripts |
|---|---|---|
| spawning agents, "which model for this agent", "too many agents", "agent cost" | [`cost/SKILL.md`](cost/SKILL.md) | `cost/scripts/agent_guard.py` (PreToolUse hook, `--selftest`) |
| fanning out agents that share context, /loop, "cache hit rate", "prompt caching" | [`prompt-cache/SKILL.md`](prompt-cache/SKILL.md) | `prompt-cache/scripts/pcache.py` (`build` · `brief` · `stats` · `--self-test`) |

They chain: `cost` decides whether to spawn and on which tier; `prompt-cache` makes the briefs those
agents get share one cached prefix, then measures it.

## Rules every sub-skill keeps

- **No agent is free.** Count the brief, the re-read and the summary against doing it inline.
- **Measure, don't estimate.** Report hit rates and token counts from the session logs (`pcache.py stats`).
- **Never block the user's work.** The hook nudges; it doesn't refuse a call.

## Tests

```bash
cd skills/agent-kit
python cost/scripts/agent_guard.py --selftest
python prompt-cache/scripts/pcache.py --self-test
```
