<p align="center"><img src="assets/hero.svg" width="100%" alt="agent-kit: Cheaper agent runs. The right tier, a finish line, one cached prefix."></p>

# agent-kit

Agent toolkit, one skill with sub-skills for running Claude Code agents cheaply.

| Sub-skill | What it does |
|---|---|
| [`cost`](cost/SKILL.md) | Routes each agent to the cheapest model tier that can finish it, gives it a checkable finish line, and skips agents the task doesn't need. A PreToolUse hook nudges every Agent call that sets no model |
| [`prompt-cache`](prompt-cache/SKILL.md) | Keeps agent prompt prefixes byte-identical so the prompt cache hits: a fingerprinted project outline, briefs that put it first and the task last, and per-agent hit rate from the session logs |
| [`rag`](rag/SKILL.md) | Project memory without breaking the cache: a local Obsidian-compatible vault (claude-obsidian layout) kept out of git, stdlib BM25 retrieval, briefs with retrieved notes after the cached prefix, and migration of a single progress file into notes |
| [`team`](team/SKILL.md) | Runs role agents as a team on a loop: the main session is the lead (`/team-tick`), workers take GitHub issues in their own worktrees and open draft PRs, a reviewer (and for games a playtester) hands on to the owner, every step a label or comment. `team.py` reads the board |

The agent's instructions are in [SKILL.md](SKILL.md).

```
npx skills@latest add th3r-dev/th3-skills --skill agent-kit
```
