# Craghold: a two-variant Roblox thumbnail

A mock game, made up for this example: a blocky adventure on a snow mountain where you fight up
from the farm, level up, earn gold and buy the dungeon key. The bench image it was measured
against was a painted "dungeon update" thumbnail: a hero mid-run, the first enemy with a level
bar, a guarded gate and a glowing key with its price.

| dungeon (mastery and reward) | summit (exploration) |
|---|---|
| <img src="keyart-dungeon-craghold-1920x1080.png" alt="Craghold Quest, dungeon update: title top-left; a big hooded blocky hero with gritted teeth swings his sword into a green enemy, a spark and gold coins flying, under a LVL 5 bar with a red arrow; behind them a gold key blazes in a dark stone gate, a red arrow from a plate reading KEY 12,500 GOLD; snow on the pines and the bridge"> | <img src="keyart-summit-craghold-1920x1080.png" alt="Craghold Quest, new summit: the same hero on the snowy bridge, a stepped trail climbing to a red flag on the peak, a red arrow from a plate reading SUMMIT 4,200 M"> |

**Art path: vector.** The image model (Gemini) answered 429, free tier, limit 0, so the scenes are
[build_art.py](build_art.py): blocky ranges snapped to a voxel grid, snow only above a snow line and
shaded on slopes facing away from the sun, haze with soft stops, and the sword placed from the arm's own
rotation. The brief's `prompt` and `negative` are ready for an AI render.

The brief, [craghold.keyart.toon](craghold.keyart.toon), holds the game read, the five anchors, the
palette, the callouts (each pinned to its prop with an arrow, and to its variant) and the two variants.
The summit variant has its own `goal` and `loop`, since it targets exploration.

```
python3 build_art.py
uv run ../../../banner-design/scripts/banner.py craghold.keyart.toon
for f in keyart-*-1920x1080.svg; do uv run ../../../banner-design/scripts/bench.py $f --bottom 120 --max-kb 3000; done
uv run ../../scripts/critic.py craghold.keyart.toon keyart-dungeon-craghold-1920x1080-400.png
```

## Bench

| Variant | Worst contrast | Smallest core text at 400 px | PNG 1× | Bottom band | Result |
|---|---|---|---|---|---|
| dungeon | 5.37:1 (ribbon) | 23.8 px | 875 KB | clear | pass |
| summit | 5.37:1 (ribbon) | 23.8 px | 737 KB | clear | pass |

## Critic: FAIL on both (deepseek-v4.1-flash via Tokenme, 400 px PNG, 3 runs each)

| Variant | Runs passing | is | loop | goal | Eye lands on |
|---|---|---|---|---|---|
| dungeon | 0/3 | 1, 1, 1 | 1, 2, 1 | 0, 1, 1 | title, title, the key and its price |
| summit | 0/3 | 1, 2, 1 | 1, 1, 1 | 2, 2, 2 | the title, all three |

The example stays in as a measured case, not a model answer. What is still wrong:

- **The title still wins the eye.** It survived three passes (centred at 100 px, moved top-left,
  capped at 76 px). By the skill's own rule that calls for a different approach, not new numbers:
  an AI-rendered scene with more light and texture, or a less saturated title.
- **The dungeon's goal reads as "get the key", not "buy the key and open the gate".** The price
  plate isn't enough; the gate opening isn't shown.
- **The summit has no stakes.** It was not rebuilt in this round (review tip 7).

## How it got here

1. First build: the title and ribbon sat on the hero's face, the sword floated beside the hand, and
   snow flooded the far range. Fixed with a smaller, lower hero, a hand computed from the arm, and a
   snow line. The summit's flag ran off the top edge; fixed with a lower peak and a stepped trail.
2. The first critic: the summit was scored against the dungeon's goal, so variants got their own
   `goal`. The snow line was raised.
3. A review against the bench (a Minecraft map's dungeon-update thumbnail and its video) and
   2025-2026 thumbnail trends. Applied:
   - a face that reacts: big eyes, angry brows, gritted teeth; the hero 1.4× larger
   - the title moved top-left and capped (`title_at`, `title_max`)
   - a near-black arch so the key is the brightest thing; warm light spilling down the bridge
   - snow on the pines, the lintel and the kerbs, shaded snow sides, falling flecks
   - the enemy between the hero and the gate, facing him, with a hit spark and coins
   - red arrows from each callout to its prop; callout text 42 px at 1920
   - the critic fails when the eye lands on the title
4. With those changes one critic run put the eye on the key, but the next three runs put it back
   on the title in two. One sample is noise, so the critic now runs three times and takes the majority,
   which is where both variants fail today.
