# Design briefs: the gate before building

Adapted from AshExplained/roblox-skills' design gate
([roblox-game-ux@a3a7b94](https://github.com/AshExplained/roblox-skills/tree/a3a7b94/roblox-game-ux), MIT).
It is design-core's "show the plan as text before building" step, written down where the next agent
finds it. Roblox UI is built in Studio, so the brief is Markdown (with sketches or screenshots), not
an HTML mock.

Two files in the game's repo:

- `design/DESIGN.md`: the game's visual system, written once and kept current.
- `design/features/<surface>/design.md`: one per surface (hud, shop, inventory, reward, settings…).
  Settings has its own content list in [settings.md](settings.md).

A surface is built only when its brief says `Status: approved`, set by the person, not the agent.
A change to an approved brief sets it back to `draft` until approved again.

## `design/DESIGN.md`

```markdown
# <Game>: UI system

Status: draft | approved

## Look
Where it comes from (the thumbnail, key art) and the one-line mood.

## Tokens
| Token | Value | Use |
|---|---|---|
| Panel | #… | plates behind text |
| OnPanel | #… | text on Panel (contrast ≥ 4.5:1) |
| Accent | #… | the one thing to look at: goal, currency, primary button |
| Danger / Price short | #… | close X, unaffordable price |
| <Stat> | #… | one colour per stat, everywhere |

## Type
Display: <font, weight> — headers, numbers, buttons. Body: <font, weight> — descriptions.

## Shape and spacing
Radius, outline width, the gap scale, the minimum tap target.

## Style contract
Roles of colour, buttons, icons, counters, size caps, motion: see visual.md's style contract.

## Conventions
Close, disabled, locked, unaffordable, the interact key; anything this game does differently and why.
```

## `design/features/<surface>/design.md`

```markdown
# <Surface>

Status: draft | approved

## Job
What the player does here, in one sentence; which loop beat it serves.

## Content, in order of importance
1. …

Follows the style contract (or: where it departs, and why).

## Reserved zones
What this surface keeps clear: chat, the People list, the top bar, the thumbstick, the jump button,
and the game's own permanent panels.

## Layout
| Device | Placement | Notes |
|---|---|---|
| Phone (667×375 and 844×390) | … | thumb zone, clear corners |
| Tablet (1024×768) | … | |
| Desktop (1270×557 and 1920×1080) | … | |

## States
| State | What shows | Trigger |
|---|---|---|
| Default | | |
| Empty | | |
| Loading | | waiting for the server |
| Error | | the server refused or timed out; how to retry |
| Locked | | not unlocked yet; what unlocks it |
(a shop adds Affordable, Unaffordable, Owned)

## Interactions
Open, close, the primary action, feedback (which juice.md effects, and what each does with Effects
at Off), the sound, what the server decides.

## Copy
Every visible string, verb-first on buttons (design-core's writing rules).
```
