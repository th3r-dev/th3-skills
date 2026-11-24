# Dungeon key: references

Collected on 2026-11-19, after the key was built, which broke the skill's "references first" rule
(section 2); the comparison below is the check it should have started from. Sketchfab figures come
from its public API (`api.sketchfab.com/v3/search` and `/v3/models/<uid>`, no login). Links only:
no reference image is committed.

## The game's own look (first)

| Reference | What it gives |
|---|---|
| Craghold's key art: [`design/thumbnail-keyart/examples/craghold`](../../../../design/thumbnail-keyart/examples/craghold/README.md) (the gold key in the gate, and the shop's key) | the key players were promised: gold, a ring bow, a straight shaft, two teeth, readable at thumbnail size |

## Outside references (measured)

| Model | Author | Licence | Faces | What it gives |
|---|---|---|---|---|
| [Stylized Fantasy Key](https://sketchfab.com/3d-models/b5431c53a2ed48db9fde3ebfc59cd56a) | Wooff | CC Attribution | 956 | **closest in style**: a gold ring bow, bands that break the long shaft, three teeth, an emissive glow that reads as a reward |
| [Low-poly Key](https://sketchfab.com/3d-models/86feedcb9a25455a913a690e22ef10d7) | beasty-pro | CC Attribution | 144 | **the budget floor**: an octagonal bow and a flat extruded profile read as a key at 144 faces |
| [Old Key](https://sketchfab.com/3d-models/dcf61f79745b47778ad10aa28199df50) | meerschaumdigital | CC Attribution | 1,556 | the classic warded silhouette: a long shaft, an oval bow, a stepped bit; bow-to-shaft proportion |
| [Dungeon Key](https://sketchfab.com/3d-models/53c5ca8be6c145949d07c06d9a8ec8f8) | JackMaddigan | CC Attribution | 988 | a different bow (a diamond) that still reads as a key: the bow is where a key gets its identity |
| [Stylized key lp](https://sketchfab.com/3d-models/cdd4e4a34a1c4752b081ffa125f983eb) | ForevereQ | CC Attribution | 520 | a chunky, hand-made ring and blocky bit; worn colour instead of extra geometry |
| [The dungeon key](https://sketchfab.com/3d-models/50d982bc1bef4240a57e44414bb67470) | ultimatech | CC Attribution | 300 | a voxel key for a blocky world (Craghold's characters are blocky): mood only, a different style from the thumbnail's |
| [Door Key](https://sketchfab.com/3d-models/6538a6a21f5545e0b1dcf22bee5741a1) | Guibel | CC Attribution | 694 | wrong genre (a modern pin-tumbler key); kept as the budget lesson: engraving and wear live in the texture, not the mesh |
| [Low Poly Key (Blank)](https://sketchfab.com/3d-models/7f09464495134d3ab6d5599830966cb9) | Guibel | CC Attribution | 332 | the same key blank at 332 faces: the cut adds 362 faces, so a bit's detail is where triangles go |

## Ours next to them

The key (648 tris after modifiers) set beside the eight thumbnails:

- **Matches the game's look**: gold, a ring bow, two teeth, as in Craghold's thumbnail and shop.
- **Budget**: mid-range of the set (144 to 1,556). The 144-face key shows a flat extruded profile
  would roughly halve it; for a single held prop on Roblox, 648 is well inside the 20,000 limit, so it
  stays, but a pickup scattered in dozens should take the flat route.
- **Silhouette**: the shaft is plain where the closest reference breaks it with bands, and the bit
  has two teeth where most have three or a stepped ward. Open: one band near the collar and a third
  tooth would add identity for about 60 tris.
