# HUD

Status: approved

## Job
Show where the player is in the loop (level up on the farm, earn gold, buy the dungeon key) and the
next goal, without covering the play area.

## Content, in order of importance
1. The objective: "Buy the dungeon key" with the price, or "Reach LVL 10" before the key unlocks.
2. Gold: a coin and the count ("9,340"); from 100,000 up a suffix, rounded down: "100K", "9.9M",
   "1B", then T, Qa, Qi. The "+250" delta uses the suffix from 1,000 ("+8.3K").
3. Level: the badge ("LVL 5") and the XP bar to the next level.
4. A Shop button (the key icon) that opens the key shop.

## Layout
Positions are fractions of the safe area (below Roblox's top bar, `CoreUISafeInsets`), so on a
screenshot of the whole window they sit lower than the number says.

| Device | Placement | Notes |
|---|---|---|
| Phone (844×390) | a left-middle stack (AnchorPoint 0, 0.5 at 50% height): level and XP, gold below; the objective as a pill top-centre; the Shop button on the right edge at 45% height, above the jump button | the bottom corners stay empty |
| Tablet (1024×768) | same, the Shop button at 55% height so the right thumb reaches it | |
| Desktop (1920×1080) | same anchors; a UISizeConstraint caps the stack's width at 360 px | the B key also opens the shop |

Revised after the first playtest: the brief first put the stack top-left, under Roblox's chat
window, which covered the level and gold plates. Approved again with the stack at left-middle, clear of
the chat above and the thumbstick below; centred at 50% once the second playtest showed chat's input
bar reaching about a third of the way down.

## States
| State | What shows | Trigger |
|---|---|---|
| Default | level, XP, gold, the objective | the server's values arrived |
| Empty | gold "0", XP bar empty, objective "Reach LVL 10" | a new player |
| Loading | the numbers as "…" on their plates | before the server's first values |
| Error | a small "Reconnecting…" chip under the stack | the values stopped arriving for 10 s |
| Locked | the objective reads "Reach LVL 10" with a lock icon; the Shop button shows a lock | level below 10 |

## Interactions
Gold counts up with a short tween and a coin sound when it rises, with a "+250" delta for 1.5 s.
Levelling up flashes the badge and shows the new level for 1.5 s. The Shop button opens the shop
(and the "E" prompt at the gate does too). The HUD only shows values; the server sends them.

## Copy
"LVL 5", "9,340", "Buy the dungeon key · 12,500", "Reach LVL 10", "Enter the dungeon" (once the key is
owned), "Reconnecting…", "Shop" (accessible name).
