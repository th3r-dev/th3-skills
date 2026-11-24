# Visual language: hierarchy, conventions, type, icons, references

design-core's composition and taste rules apply as written
([visual-principles.md](../../../design/core/references/visual-principles.md),
[taste.md](../../../design/core/references/taste.md)). This file holds what Roblox players already
expect, from Roblox's [UI/UX design guide](https://create.roblox.com/docs/production/game-design/ui-ux-design)
and DevForum practice, plus the reference catalogue.

## Hierarchy of information

Ask, for each surface: what is the player doing now, what do they need to know, which choices do
they face, how often. Then:

- **Show only what applies now.** Without the ball: Sprint and Tackle. With it: Deke and Pass.
- **Small screens get a minimal HUD.** Survival-critical things (health, the tool in hand, the map)
  are one tap away; the rest folds into a menu that opens on demand.
- **Attention is spent, not sprayed**: a bright hue for the one crucial thing, muted for the rest;
  bigger means more important; space around what matters; related things grouped. Movement
  (a wiggle, an animated arrow) only in onboarding, and rarely.
- **The best offer looks it**: a gold stripe on the premium tier, a bigger tile with more padding
  for the best-value bundle. Honestly: the visual weight matches the real value.

## Conventions players already know

| Convention | Rule |
|---|---|
| Close | a square red button with a white X at the dialog's top right |
| Unusable | greyed out, still visible, with the reason when tapped |
| Not unlocked yet | a lock over it, with what unlocks it ("Reach LVL 10") |
| Can't afford | the price in red |
| One stat, one colour | health green in the bar, the icon and the text, everywhere |
| Interact | the "E" proximity prompt; number keys for a hotbar |
| Items in dialogue | bold when an NPC names them |
| Big numbers | exact with separators below 100,000 ("12,500"); a suffix from there, one decimal, rounded down so it never overstates: "100K", "9.9M", "1B", then T, Qa, Qi (simulators reach them). A delta beside a count goes compact sooner ("+8.3K") because its box is narrow |

Study the genre's top games before departing from these: a player's habit beats a clever layout.

## Type

- **Two fonts.** A display font for headers, big numbers and buttons, read in a glance; a body font
  for anything read in full (descriptions, tooltips). Wide fonts like Gotham tire as body text.
- Headers larger and bolder than body; text on a contrasting plate, not over a busy scene.
- Roblox can't upload font files: pick from its library (`Font.fromName`), and set the families as
  tokens so they change in one place.

## Icons

- One family per set: shared palette, stroke and shape language (all stat icons alike).
- Make icons **white** and tint them with `ImageColor3`, so one image serves every colour and theme.
- Free sources with their own terms: Kenney (CC0) and Icons8 (attribution unless licensed). Export
  PNG at 2× the largest size used; SVG doesn't upload.

## Look and feel

- Buttons sit in a contrasting container with a highlight or shadow for depth; chunky, outlined,
  rounded buttons read as tappable at phone size.
- Light themes suit cartoony and playful games; don't default to dark. A HUD that is all one dark
  fill reads as a tool panel on a sunny world.
- Gradients, glows and drop shadows are finishing touches on the one thing that matters (the
  "Go VIP" glow), not on every panel. design-core calls decoration everywhere an AI tell.
- **Match the game's thumbnail.** The thumbnail promised a look; the UI keeps it (palette, outline
  weight, type). Craghold's UI takes its navy plates, gold accent and cream type from its key art.

## Style contract

One owner had to ask for "playful" again on every new surface, because the first playful HUD
never became a rule. Write the contract into `design/DESIGN.md` once, and have every surface brief
cite it in one line ("Follows the style contract"). If a surface breaks the contract, its brief
says where and why.

| Part | The contract says |
|---|---|
| Roles of colour | which hue means numbers, which means words and goals, which means *press me* (one example: navy for numbers, cream for words, colour for anything pressable) |
| Buttons | the shape (radius, outline), the lip under the face, one role colour per action, an icon in a coloured disc |
| Icons | one family: filled, rounded, white on a colour disc; each role colour has its own icon shape, so colour is never the only signal |
| Counters | always X / Y when there is a cap ("Bag 7 / 10"); a counter with a goal gets a bar |
| Size | the HUD's share of the screen (cap it; a phone HUD over about 20% of the screen buries the game), the text floor, the icon share of its button (60% or more) |
| Motion | which effects from [juice.md](juice.md) this game uses, and at which Settings level |

Check it from a capture in one second: can a new player tell what to press, what they have, and
what to do next?

## Reference catalogue

Collected for this skill; take grammar (layout, density, shape, palette logic), never assets.

| Style | Seen in | Grammar to take |
|---|---|---|
| Cozy cartoon / pixel farm | the user's Pinterest board "roblox ui designs" (12 pins: jungle and forest GUI packs, cartoon game buttons, farming and pixel-farm interfaces, a hotbar, Stardew-style panels) | earthy palette (terracotta #BC5846, olive #5E6A3C, cream #FFEEB4, peach #F2A689, sage #D2E077); wood and leaf frames; chunky rounded buttons; a bottom-centre hotbar |
| Simulator / tycoon | the genre's front-page games | huge currency counters top-left, a right-side button stack, loud reward popups with a delta |
| Paid UI packs | BuiltByBit's [graphics-ui](https://builtbybit.com/resources/roblox/graphics-ui/) listings | NOT ASSESSED: the listing blocks automated reading. Packs are licensed per buyer; study what sells (themes, which surfaces a pack covers), never reuse their art |

Workflow from the [Ultimate UI Design Guide](https://devforum.roblox.com/t/the-ultimate-ui-design-guide/1236916):
sketch with limits (no detail), then a Figma prototype (layout boxes, then colour, then icons, then
text, then finishing touches), then rebuild in Studio by typing the Figma values into Properties.
design's flow sub-skill can hold the Figma side.
