# Production layout

A prototype that runs is not a production game. Production layout is the structure that lets the next
sitting — or another agent — pick the project up, ship it, and keep it from leaking memory or
dropping frames. A real build reached its owner as a folder with no git, no brief, and the hero
object sitting on grass; the layout below is what would have carried it.

## The project

| Holds | Is | Why |
|---|---|---|
| a git repo | `git init` from the first commit, with a `.gitignore` | the handoff and the trail — another agent gets commits, not your chat |
| `design/` | `game-brief.md`, `idea-grill.md`, `DESIGN.md`, committed | the locked scope, loop and milestones; the build's source of truth |
| `src/` | the engine's layout (`client` / `server` / `shared` for Roblox) | the server owns state; pure `shared` modules stay Lune-testable |
| one config file | every tuned value in one place (speeds, prices, odds) | the flow's rule — a designer tunes without reading code |
| `tests/` | Lune (or the engine's) tests on the pure modules | the headless gate: necessary, never sufficient |
| pinned toolchain + CI | `rokit.toml` (or a lockfile) and a CI that runs lint + tests | the same build on every machine; green before merge |
| `build/`, `assets/provenance` | the place file; where each asset came from | reproducible, and no stolen art |

## Memory — don't leak

Already the house rule, so follow it, don't restate it: **what a class creates, it cleans up** — a
class that makes Instances or connections holds them in fields, and its `destroy()` disconnects and
destroys them all, and someone calls it. Clear per-player state on `PlayerRemoving`. Full rule and
checklist: [`roblox/references/luau.md`](../roblox/references/luau.md) ("be tidy").

## Optimization — measure the placed result

Also already covered: time a hot-path change **before and after** (one "fix" made a tool eight times
slower and was reverted); keep effects under the fill-rate budget
([`roblox-vfx`](../roblox-vfx/SKILL.md)); and the Luau performance rules in
[`luau.md`](../roblox/references/luau.md) (typed `Vector3` for native code, no
`getfenv`/`loadstring`, measure with the Script Profiler). Budget first, measure in the engine, never
guess from the design.

## The gate

A game is laid out for production when: git is initialised and the brief + design are committed;
tuned values sit in one file; pure logic is Lune-tested; the toolchain is pinned and CI is green;
every class cleans up on removing; and the placed result has a **capture**, not just a headless pass.
