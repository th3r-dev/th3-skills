# Craghold: UI system

Status: approved

## Look
From Craghold's key art (design's thumbnail-keyart example): navy plates, a gold accent for the goal
and the currency, cream type, chunky outlined shapes. The UI keeps the promise the thumbnail made.

## Tokens
| Token | Value | Use | Contrast |
|---|---|---|---|
| Panel | #14213D | plates behind every text | |
| OnPanel | #FFF6E2 | text on Panel | 14.9:1 |
| Muted | #A9B4CC | secondary text on Panel ("You have …") | 7.7:1 |
| Accent | #FFB23F | the goal, gold, the primary button | 8.9:1 on Panel |
| OnAccent | #14213D | text on an Accent button | 8.9:1 |
| PriceShort | #FF6B5E | an unaffordable price | 5.7:1 on Panel |
| Danger | #C8302A | the close button's fill (white X, 5.4:1) | not for text on Panel (3.0:1) |
| Level | #5BD15B | level and XP, in the bar and the badge | |
| Disabled | #3A4560 / #C5CBD8 | a disabled button and its text | 5.9:1 |
| Outline | #0B1220 | the 3 px stroke on plates and buttons | |

## Type
Display: Montserrat Heavy (900): the level number, gold, prices, button labels.
Body: Builder Sans Medium: descriptions and secondary lines.

## Shape and spacing
Radius 12 on plates, 10 on buttons. A 3 px Outline stroke. Gaps in Scale: 1% of the screen
between items in a group, 2% between groups. Tap targets never below 44 px (a UISizeConstraint floor).

## Style contract
Every surface brief cites this; a surface that departs says where and why.

| Part | Craghold |
|---|---|
| Roles of colour | navy Panel for plates and numbers, cream OnPanel for words, gold Accent only for the goal and the one thing to press; Level green wherever level or XP shows |
| Buttons | radius 10, the 3 px Outline, a press scale to 0.94 and a click; the primary action in Accent, a disabled one in Disabled with its reason |
| Icons | drawn shapes (the coin) or a single glyph on a plate; no emoji that some platforms can't draw |
| Counters | gold as a number with the coin; level as "LVL n" with its bar to the next level |
| Size | the HUD stack at most 26% of the screen's width and 360 px; text never under 14 px; the Shop button at least 44 px |
| Motion | from juice.md: gold ticks up, the level badge flashes on a level up, the key bounces when bought; all of it follows the Settings effects level, and at Off only colour changes remain |

## Conventions
Roblox's: a red square X at a dialog's top right, greyed disabled buttons, a lock with its unlock
condition, a red price when short, Level always green. The interact key at the gate is the "E"
proximity prompt ("Open shop").
