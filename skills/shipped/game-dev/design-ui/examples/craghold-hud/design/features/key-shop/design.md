# Key shop

Status: approved

## Job
Turn the gold the loop earns into the goal: buy the dungeon key. One item, one decision.

## Content, in order of importance
1. The key: its icon and name, "Dungeon key".
2. The price, "12,500", red when short.
3. The Buy button.
4. "You have 9,340": what the player has, in Muted.
5. Close.

## Layout
| Device | Placement | Notes |
|---|---|---|
| Phone (844×390) | a centred dialog, 60% of the height, aspect 4:3; the Buy button full width at the bottom of the dialog | the dialog sits above the HUD (higher DisplayOrder), a dimmed backdrop behind |
| Tablet (1024×768) | the same, 50% of the height | |
| Desktop (1920×1080) | the same, capped at 520 px wide | B toggles it (Esc is Roblox's menu) |

## States
| State | What shows | Trigger |
|---|---|---|
| Affordable | the price in Accent; "Buy key" enabled (Accent button) | gold ≥ 12,500 |
| Unaffordable | the price in PriceShort; the button disabled: "Need 3,160 more" | gold < 12,500 |
| Loading | the button reads "Buying…", disabled, a spinner | the request is with the server |
| Owned | a check over the key; the button disabled: "Owned"; a line "The gate is open" | the server confirmed |
| Error | "Couldn't buy. Try again." under the button, which is enabled again | the server refused or timed out (10 s) |
| Locked | a lock over the key; the button disabled: "Reach LVL 10" | level below 10 |
| Empty | not used: the shop always has the key |

## Interactions
Buy asks the server (`BuyKey`). The server checks the level, the gold and that the key isn't owned,
takes the gold and answers. The dialog shows Loading until it answers; on success, a short
celebration (a key sound and a bounce) and Owned. Close: the X, the backdrop, or the B key again. Not Esc: Roblox keeps Escape for its own menu, and
the game receives it already processed (found in the playtest).

## Copy
"Dungeon key", "12,500", "Buy key", "Need 3,160 more", "Buying…", "Owned", "The gate is open",
"Couldn't buy. Try again.", "Reach LVL 10", "You have 9,340", the close button's name "Close".
