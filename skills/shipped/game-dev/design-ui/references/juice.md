# Juice: UI that feels alive

A HUD can be readable and still look like a tool panel. A game's owner scored one 4.5/10 for
playfulness: ten navy boxes, flat buttons, nothing that looked pressable, nothing that moved. The
fix wasn't more decoration. Every action got an answer the player can feel. This file is the
catalogue, the budget and the gate.

## The style contract comes first

Playfulness has to be a rule in `design/DESIGN.md`, not a request repeated for every new surface
(the same owner asked again for the join banner, the event chips and the Go buttons). Write it
once ([visual.md, style contract](visual.md#style-contract)) and have each brief cite it.

## Catalogue

Each effect is a recipe on `TweenService`. "Level" means the lowest Settings effects level at
which the effect still plays ([settings.md](settings.md)).

| Effect | When | Recipe | Level |
|---|---|---|---|
| Press lip | every button | a darker "lip" frame 4 px under the face; on press the face drops 3 px onto it and a `UIScale` goes to 0.94 | Off (it is feedback, not motion) |
| Hover lift | buttons, desktop | `UIScale` 1.05, 0.12 s Quad Out | Reduced |
| Tick-up | any counter that rises | the number steps from old to new over 0.4 s (8 to 12 steps, the last one exactly the new value), a coin sound on the first step | Reduced; at Off the number just changes |
| Reward pop | a reward, a tier up, a purchase | the element scales 0 → 1.15 → 1 with `Enum.EasingStyle.Back`, 0.35 s, plus a sound | Reduced shows it at full size, without the scale |
| Shine sweep | the one thing to look at (the goal chip, the best-value tile) | a `UIGradient` with a white band; tween its `Offset` from (-1, 0) to (1, 0) once, then wait 4 s or more | Full |
| Gradient stroke | rare or top-tier items | a `UIGradient` on the `UIStroke`, `Rotation` tweened 0 → 360 over 3 s | Full |
| Sparkles | a big reward, a level up | 6 to 10 pooled `ImageLabel`s burst out from the element and fade over 0.6 s | Full |
| Pulse | a button that just became usable | its stroke thickens 3 → 6 → 3 once | Reduced |
| Idle bob | the goal chip only | `Position` ±2 px every 4 s, one loop for the whole HUD | Full |
| Edge flash | level up | a full-screen frame in the stat's colour, transparency 0.7 → 1 over 0.4 s | Full |
| Sound | every action | a short sound in the Effects `SoundGroup` | follows the sound sliders, not the effects level |

## Budget

- Tween `Position`, `Size`, `Rotation`, `Transparency` and gradient `Offset` only. No per-frame
  `RenderStepped` code for UI.
- At most **one idle loop** on screen at a time. Everything else plays once and stops.
- Pool sparkles: create them once and reuse them. A burst never creates instances.
- Nothing moves during the first action of a new player except the thing they should press.
- Motion supports a state, never replaces it. A locked button stays locked with its icon and
  colour even when Effects is Off.

## One module

The game has one client module (`Juice`) holding these recipes. Each recipe reads the current
effects level from Settings and falls back to an instant state change below its level. Surfaces
call `Juice.pop(frame)` or `Juice.tick(label, from, to)`; they never build tweens of their own,
so one Settings switch reaches every effect.

## The gate

In review ([review.md](review.md)):

- **Playfulness / feel**: captures show a press, a reward and a tier-up mid-animation. A fresh
  reviewer scores it, and 8 or more passes.
- **Settings honoured**: the same three captures with Effects at Off show no motion, and the
  states still read.

World effects (particles, beams, ability visuals) are in [roblox-vfx](../../roblox-vfx/SKILL.md).
