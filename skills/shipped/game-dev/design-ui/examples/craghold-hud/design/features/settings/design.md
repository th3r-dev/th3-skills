# Settings

Status: draft

## Job
Let the player turn the music, the sounds and the motion down (or up) without leaving the game.
It serves no loop beat; it keeps players who would otherwise leave.

## Content, in order of importance
1. Effects: Full / Reduced / Off. Starts on "Auto", shown as the level the device asked for:
   "Reduced (your Roblox setting)" when Roblox's Reduce Motion is on, else "Full".
2. Music: a slider 0–100 (default 60).
3. Sound effects: a slider 0–100 (default 80); dragging it plays the coin sound at that volume.
4. Hints: on / off (default on).

Follows the style contract. Roblox's own menu already has the camera, graphics quality, master
volume and text size, so they aren't repeated here.

## Reserved zones
Same as the key shop: a centred modal over the HUD, inside the safe insets, on its own ScreenGui
with the `Modal` attribute and a full-bleed dim behind it.

## Layout
| Device | Placement | Notes |
|---|---|---|
| Phone (667×375 and 844×390) | a centred dialog, 80% of the height, four rows | each row a label left and its control right; controls at least 44 px tall |
| Tablet (1024×768) | the same dialog, capped at 520 px wide | |
| Desktop (1270×557 and 1920×1080) | the same, capped at 520 px wide | close with the X, the backdrop or the gear; not Esc (Roblox keeps it) |

## States
| State | What shows | Trigger |
|---|---|---|
| Default | the rows with the saved values | the server's copy arrived |
| Loading | the rows at the defaults, greyed, not interactive | before the server's copy arrives |
| Saving | nothing visible; a change applies at once and saves quietly | any change |
| Error | under the rows: "Couldn't save. Your settings work this session." in Muted | the server refused or timed out |
| Reduced by the device | Effects reads "Reduced (your Roblox setting)" | Auto, and Reduce Motion is on |

## Interactions
Open from the HUD's gear; close with the X, the backdrop, or the gear again. Every change applies
at once: the effects level goes to `Juice.set`, volumes to the Music and Effects SoundGroups. The
client sends the whole table through `SaveSettings` (a RemoteEvent, at most once a second); the
server runs `Settings.validate` on it and keeps the clean copy for the session (this example has
no DataStore; a real game saves it with the player's data). Opening pops the dialog (Full only);
the sliders give no motion, only the sound sample.

## Copy
"Settings", "Effects", "Full", "Reduced", "Off", "Reduced (your Roblox setting)", "Music",
"Sound effects", "Hints", "On", "Off", "Couldn't save. Your settings work this session.",
"Close" (accessible name of the X).
