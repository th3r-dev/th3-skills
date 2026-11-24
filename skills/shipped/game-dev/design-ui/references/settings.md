# Settings: a surface every game ships

A game with rich effects and sound needs a way to turn them down. Without one, a player whose
phone is slow, who plays in class with the sound off, or who gets sick from motion, leaves instead.
Settings is one of the five screens a first game gets (see
[idea-grill's scope budget](../../idea-grill/SKILL.md#4-scope-budget-few-systems-a-long-ladder)),
and it ships with v1.

## What it holds

Keep it to what this game actually has. Roblox's own menu already covers the camera, graphics
quality, master volume and text size, so don't copy those.

| Setting | Control | Default | Applies to |
|---|---|---|---|
| Music | slider 0–100 | 60 | a `SoundGroup` named Music |
| Sound effects | slider 0–100 | 80 | a `SoundGroup` named Effects; every UI and world sound sits in one of the two groups |
| Effects | Full / Reduced / Off | Full, or **Reduced** when `GuiService.ReducedMotionEnabled` is on | every UI tween loop, pop, shine and sparkle ([juice.md](juice.md)) and the world effects the game owns |
| Hints | on / off | on | tutorial arrows, key hints, "tap here" pulses |
| Key hints | on / off | on with a keyboard, off on touch | the keycaps on buttons |

`GuiService.ReducedMotionEnabled` mirrors the player's Roblox **Reduce Motion** setting
(create.roblox.com/docs/reference/engine/classes/GuiService, read 2026-11-24). Read it on join and
whenever it changes. If the player chose Full in the game, that choice wins.
`GuiService.PreferredTextSize` is the player's text size: let text grow with it
(`AutomaticSize`, `TextWrapped`) rather than adding a text-size setting of your own.

## Rules

- **Changes apply at once.** No Save button. A slider plays a sample sound while you drag it.
- **The server validates, then saves.** The client sends the whole settings table. The server
  runs it through one pure `validate(raw)` that clamps numbers, drops unknown keys and falls back
  to defaults for wrong types, then saves the clean result with the player's data. The same
  function runs on the client before it sends, so both sides agree.
- **One source of truth on the client.** Every system that animates or plays a sound asks one
  module for the current level (`Settings.effects(settings, reducedMotion)`). No system reads the
  raw table.
- **Effects Off really stops them.** No idle loop runs, nothing travels, and states change by colour
  and icon alone. The review row "Settings honoured" checks this in a capture with Off set.
- **Open it from the HUD**: a gear button in the dock or menu, never in the bottom corners. Close
  it with the X, the backdrop, or the key that opened it.

## States

| State | What shows |
|---|---|
| Default | the controls with the saved values |
| Loading | the controls at their defaults, disabled, until the saved values arrive |
| Saving | nothing visible; a save is silent |
| Error | the save failed: a small "Couldn't save. Your settings work this session." note, with no retry button (the next change tries again) |
| Reduced by the device | the Effects control shows "Reduced (your Roblox setting)" until the player picks another value |

## Brief

Use the surface template in [design-brief.md](design-brief.md). The Content list is the table
above, cut down to what the game has. The Copy section names every label ("Music", "Sound
effects", "Effects: Full / Reduced / Off").
