# Reference board: low-poly furry cat

Gathered 2026-11-16, before v2 of `build_cat.py`. Links only: no reference image is stored here.
Sketchfab face counts and licences come from its public API (`api.sketchfab.com/v3/models/<uid>`).

## Sketchfab (3D, measurable)

| Model | Faces | Licence | What it gives |
|---|---|---|---|
| [Low Poly Cat](https://sketchfab.com/3d-models/low-poly-cat-1e7143dfafd04ff4891efcb06949a0b4) (volkanongun) | 384 | CC BY | the user's pick: a realistic, slim cat, long legs, faceted |
| [Wizard Cat](https://sketchfab.com/3d-models/42cc473a1c17467c8f96e47e2a4439de) (ndiecity) | 146 | CC BY | the lowest-poly *character*: a big head, big ears, the face as flat colour |
| [Wo the Cat](https://sketchfab.com/3d-models/1224899d82d947909076ee8b4ac49d44) (ani3d) | 1,440 | CC BY | chibi proportions: head as big as the body, short legs, colour patches |
| [Black Cat PSX](https://sketchfab.com/3d-models/62416ff46cef45599c51dc9bc0b83b43) (Bonvikt) | 466 | CC BY | PS1 style: the silhouette carries it |
| [Low Poly Cat Walk](https://sketchfab.com/3d-models/13674c3dbb074f73b6563a75c28b0fe0) (volkanongun) | 520 | CC BY | the same author's cat, animated |
| [Lowpoly Cat Rig + Run Animation](https://sketchfab.com/3d-models/c36df576c9ae4ed28e89069b1a2f427a) (dailyfree3d) | 794 | CC BY | a rigged budget for a running cat |
| [Gnarpy sily cat](https://sketchfab.com/3d-models/31ae2d49d5b94531bb36337e4de6de5b) (myoshi_ua) | 650 | CC BY | fur as spiky geometry |
| [objects for drawing reference](https://sketchfab.com/mastershokhan1/collections/objects-for-drawing-reference-e4a38dc176bb4a92a49b8ba30d2ef026) (collection, 89 models) | — | mixed | weapons and props, no cats: a model of how to keep a reference set, not a cat reference |

## Pinterest (mood only)

[Low poly cat ideas](https://www.pinterest.com/ideas/low-poly-cat/908541234841/): PS1-style and chibi
cats, calico patches, faces painted on rather than modelled. Rights unknown: used for direction
only. Several pins show an existing commercial character (a white cat in the style of Sony's Toro):
its design is not to be copied.

## What changed in the model

| Seen in the references | v1 (before) | v3 (after) |
|---|---|---|
| A cat *character* has a head about as big as the body | realistic proportions, small head | head 1.15× body width, short legs |
| The lowest-poly models colour faces, not extra shapes | a 20-triangle muzzle object | muzzle and belly as face colours on the head and body: 0 extra triangles |
| Big eyes carry the character | small eyes | eyes twice the size |
| Fur at low poly is spikes (Gnarpy) | kept | kept: cheeks, chest, crown, tail tip |
| One material per asset, power-of-two textures (ZEPETO, `references/texturing.md`) | 4 materials | **1 material** over a 16 px palette texture |
| — | 148 triangles | **128 triangles**, 9/9 on the bench |

## Wizard cat (`../wizard-cat/`)

The follow-up "output is need wizard cat" dresses the same cat. [Wizard Cat](https://sketchfab.com/3d-models/42cc473a1c17467c8f96e47e2a4439de)
on this board gave the idea only. Its look (a black cat, a blue robe, a yellow hat with a red band,
blue flames) was kept out: this one is the orange cat with a purple pointed hat, the ears through
its brim, a purple cape with a gold clasp, and a floating cyan crystal. 200 triangles, one
material, 9/9 on `benchmarks/lowpoly-wizard-cat.toon`.
