# Agentic playtest: an agent plays the PR in Studio

A `playtester` role agent (see agent-kit `team`) tests a feature by playing the real game in
Roblox Studio through Studio's MCP server, then reports PASS/FAIL per step with evidence.

## What Studio's MCP server gives the agent

From create.roblox.com/docs/studio/mcp (read 2026-11-16; Roblox changes weekly, so re-read it):

| Need | Tool |
|---|---|
| start / stop a playtest | `start_stop_play`, `get_studio_state` |
| move the character | `character_navigation` (to a position or an instance path) |
| click, press keys, use UI | `user_mouse_input`, `user_keyboard_input` (aimed at instances or coordinates) |
| read state from inside | `execute_luau` with data model **Server** or **Client**; `inspect_instance`, `search_game_tree` |
| evidence | `screen_capture`, `get_console_output` |
| which Studio | `list_roblox_studios`; every call names its `studio_id` |

## Three layers, cheapest first

| Layer | What | Runs |
|---|---|---|
| Rules | Lune tests on shared classes (curves, wallets, odds, trees) | headless, seconds, by the worker |
| **Scenarios** | `tests/scenarios/<feature>.md`, written from the issue's "Done when" | Studio playtest, by the playtester |
| Cloud | Open Cloud Luau execution against a published place: server checks, no players | later; check the API docs first |

## A scenario

```markdown
# Scenario: core loop (issue #2)
Setup: the player spawns at camp; Workspace.Zones.PigPen has 5 pigs. P = game.Players:GetPlayers()[1]

| # | Do (MCP tool) | Check (execute_luau, Server) | Pass when |
|---|---|---|---|
| 1 | start_stop_play | P.leaderstats.Level.Value | == 1 |
| 2 | character_navigation → nearest pig | | arrives within 8 studs |
| 3 | user_mouse_input click it until it dies | P.leaderstats.Gold.Value | == 10 |
| 4 | screen_capture | | the +gold pop is visible |
| 5 | get_console_output | | no line containing "error" |
| 6 | start_stop_play (stop) | | |

## Probes (the server decides)
| Probe | Fire from Client | Pass when |
| wrong target | hit request on workspace.Baseplate | Gold unchanged |
| out of range | hit request on a pig 100 studs away | its health unchanged |
| too fast | 20 requests in 1 s | at most the cooldown allows |

## Not assessed by the agent
Multiplayer, feel, phone performance.
```

Checks **read** state and never change it to make a step pass. Probes are the cheapest way to
catch a client-trusting remote, the classic Roblox exploit.

## The playtester's run

1. No Studio MCP (`list_roblox_studios` is empty) → comment "Playtest NOT ASSESSED: Studio MCP
   not connected", label `blocked`, stop. Never report a pass that didn't run.
2. Lock: `status:needs-playtest` → `status:playtesting` (one Studio, one playtest at a time).
3. Sync the PR: a fixed worktree (`../<game>-playtest`) checked out at the PR branch, `rojo serve`
   from it, Studio connected to Rojo (the owner connects it once per session). Confirm with
   `script_grep` that a string from the diff is in Studio.
4. Play each row, then the probes, then `get_console_output`. Stop play and stop `rojo serve`.
5. Evidence: screenshots committed to an orphan `evidence` branch (`evidence/pr-<n>/<step>.png`)
   and linked, so the main history stays small.
6. One PR comment: the step table (expected, observed, result), probes, console errors, and what
   wasn't assessed. Each FAIL → a `bug` issue (steps, expected, actual, screenshot, "Found in #<pr>").
7. Label: `status:needs-review` if everything passed, else `status:changes-requested`.

## Studio and capture limits

Each of these was found the hard way, one PR at a time, on a game built with this skill. Read
them before the first playtest, not after the third failure.

| Limit | What to do |
|---|---|
| Two agents driving one Studio made both runs fail and lag | one agent in Studio at a time: take the lock, check `pgrep` before launching it, never launch a second |
| Studio keeps an old ModuleScript after a sync; every driver crashed on a stale module | restart Studio every three playtests and whenever a shared module changed; a harness script loads its modules fresh |
| `screen_capture` doesn't draw `AlwaysOnTop` BillboardGuis | check those labels with `execute_luau` (Enabled, size, distance) and say so in the row |
| A capture taken in Edit mode shows terrain as thin shells | capture in Play |
| The cloud Luau tier has no baked terrain; a test there faked the cave floor and passed | a row that reads terrain, caves or placed props needs a Studio row; the cloud row covers server rules only |
| A geometry test passed on the design model and failed on real ground (563 planks, not 398) | measure the parts the engine placed, on the real ground |
| A config script near 200,000 characters would no longer sync into Studio | split config and data by domain early; fail the build at 150,000 |
| Screenshot links with tokens expired before the owner opened them | commit the image to the evidence branch and embed it inline (`?raw=true`) |
| A warning everyone called "known noise" stayed for eight days | a console warning that repeats becomes an issue in the same round |

## Agent definition

```markdown
---
name: playtester
description: Plays a PR in Roblox Studio through the Studio MCP server following tests/scenarios, reports PASS/FAIL per step with console output and screenshots, files a bug per failure. One at a time.
model: sonnet
skills:
  - th3-skills:game-dev
maxTurns: 80
---
<the run above, with the project's paths>
```
