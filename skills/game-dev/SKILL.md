---
name: game-dev
description: >-
  Game development, one skill with sub-skills, for any coding agent (Claude Code, Codex, Cursor,
  Gemini CLI). Runs one flow from idea to shipped game: a motivation-first design pass, a one-page
  brief, an engine, a first playable build that is run and looked at, then one feature a sitting
  until it is cut and shipped. (1) design-lens: design from player motivation (MDA read through
  Octalysis's core drives), with a white-hat / black-hat audit. (2) roblox: Roblox Studio with Luau
  in files (Rojo, Rokit, Selene, StyLua, Lune) and Studio's built-in MCP server wired to the agent
  for playtests. Use WHENEVER the work is "make a game", "game idea", "game design", "core loop",
  "why is this game not fun", "MDA", "Octalysis", "player motivation", "game brief", "GDD",
  "prototype a mechanic", "Roblox", "Roblox Studio", "Luau", "Rojo", "obby", "tycoon",
  "simulator", "Studio MCP", "ทำเกม", "ออกแบบเกม", "เกม Roblox". Read the sub-skill's SKILL.md
  before acting.
---

# game-dev: sub-skills

| When the work is… | Read | Scripts |
|---|---|---|
| an idea, a brief, "is this fun", a loop, rewards, player types, monetization ethics | [`design-lens/SKILL.md`](design-lens/SKILL.md) | none |
| Roblox Studio: set it up, wire the agent to Studio, build, test, playtest | [`roblox/SKILL.md`](roblox/SKILL.md) | `roblox/scripts/roblox_setup.py` (stdlib, `--dry-run`, `--selftest`) |

## The flow

The order comes from [th3 Game Studio](https://github.com/th3r-dev/th3-game-studio), a fork of
[Claude Code Game Studios](https://github.com/Donchitos/Claude-Code-Game-Studios) that adds the
Roblox route. **If the project is a copy of that template** (its `CLAUDE.md` names the studio and
`.claude/skills/prototype/` exists), use its own commands at each step (`/start`, `/prototype`,
`/setup-engine`, `/dev-story`, `/cut`) and treat this file as the map. Otherwise run the steps here.

| # | Step | Done when |
|---|---|---|
| 1 | **Where are we.** No idea, an idea, a brief, or a game already. Skip to the step that fits | the person agrees on the starting step |
| 2 | **Design pass** (`design-lens`): who plays, which motivation the game serves, the loop that delivers it | the motivation, the loop and the first minute are written in one paragraph each |
| 3 | **One-page brief** at `design/game-brief.md`: the person's words kept, pitch, motivation, core loop, first minute, challenge, the features in build order, what is left for later | the person says "build it" |
| 4 | **Engine.** Web (any browser, nothing to install) unless the brief needs more. Roblox (`roblox`) when the players are on Roblox or the game is multiplayer and social. Godot, Unity or Unreal for big 3D, consoles or stores | the engine is set up and an empty project runs |
| 5 | **First build**: the core loop only, every value in one config file | it was **run and looked at**: a browser screenshot, or a Studio playtest's output and capture |
| 6 | **Grow**: one feature a sitting. Name it, build it, run it, look at it, commit it. Check it against the brief's "keep" and "avoid" | the feature is in a commit, with what was checked |
| 7 | **Cut and ship**: list what to cut, a polish list, the date it ships | the person signs off the list |

## Rules every step keeps

- **Playable before paperwork.** One page of brief, then a build. More documents only when the
  person asks or a team needs them.
- **A check is a run, not a parse.** A step that changes what the player sees is not done until the
  game was started and looked at. A check that could not run is NOT ASSESSED, never a pass.
- **Ask before writing or installing.** Show the file list first; installs, downloads, account
  sign-ins and publishing are the person's yes.
- **No copies of existing games.** Genres and mechanics are free to use; another game's name,
  characters, art, music or levels are not.
- **The engine's docs over memory.** Engines change after any model's training; read the engine's
  current docs (or the reference the project pins) before writing API calls.

## Agents other than Claude

Every file here is plain Markdown plus stdlib Python, so any agent that can read files and run a
shell can follow it.

| Agent | How it loads the skill |
|---|---|
| Claude Code | `/plugin install th3-skills --marketplace th3r-dev/th3-skills`, or `npx skills@latest add th3r-dev/th3-skills --skill game-dev` |
| Codex CLI, Cursor, Gemini CLI, others | `npx skills@latest add th3r-dev/th3-skills --skill game-dev` installs it for the agents `skills` supports; otherwise point `AGENTS.md` / `.cursor/rules` / `GEMINI.md` at this file |
| Studio MCP (Roblox) | `roblox/scripts/roblox_setup.py mcp --client <claude|codex|cursor|gemini|vscode>` |

## Tests

```bash
cd skills/game-dev && uv venv && uv pip install --no-build pytest==9.2.0
uv run --no-project python -m pytest -q
uv run --no-project python roblox/scripts/roblox_setup.py --selftest
```
