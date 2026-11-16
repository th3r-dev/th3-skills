# Art theme: what makes an asset one of ours

Read before modelling anything that will stand next to the wizard cat. The theme is taken from
what the cat already does (`examples/lowpoly-cat/build_cat.py`,
`examples/wizard-cat/build_wizard_cat.py`), measured on Blender 5.3.0 on 2026-11-16. A rule marked
**new** is not in the cat: it was set while building `examples/wizard-glade/` so that scenery
matches it. Where an outside rule is used it names its source, as listed in
[`environment.md`](environment.md).

## Palette

One material, `Palette`, over one 16 px texture: a 4 × 4 grid of 4 px cells, sampled with Closest
filtering, roughness 0.9. Every face's UVs sit on the centre of its colour's cell (`paint`). A
colour patch is a repaint of some faces (`patch`) and costs no triangles.

| Cell | Name | sRGB | Hue | Sat | Value | Used for |
|---|---|---|---|---|---|---|
| 0 | `fur` | 0.95, 0.50, 0.15 | 26° | 0.84 | 0.95 | the cat's body |
| 1 | `cream` | 0.98, 0.88, 0.70 | 39° | 0.29 | 0.98 | muzzle, belly, chest ruff; mushroom stems |
| 2 | `pink` | 0.95, 0.55, 0.62 | 350° | 0.42 | 0.95 | nose, inner ears |
| 3 | `dark` | 0.08, 0.07, 0.07 | | 0.12 | 0.08 | eyes only |
| 4 | `purple` | 0.45, 0.22, 0.68 | 270° | 0.68 | 0.68 | hat; the door, mushroom caps |
| 5 | `gold` | 0.96, 0.78, 0.25 | 45° | 0.74 | 0.96 | hat band and tip; the door knob |
| 6 | `cyan` | 0.35, 0.92, 0.96 | 184° | 0.64 | 0.96 | crystals, sparks |
| 7 | `plum` | 0.28, 0.12, 0.42 | 272° | 0.71 | 0.42 | cape |
| 8 | `wood` | 0.45, 0.28, 0.14 | 27° | 0.69 | 0.45 | staff; tree trunks |
| 9 | `grass` | 0.42, 0.66, 0.30 | 100° | 0.55 | 0.66 | **new**: ground, moss on rocks |
| 10 | `leaf` | 0.30, 0.56, 0.28 | 116° | 0.50 | 0.56 | **new**: crowns, grass blades |
| 11 | `pine` | 0.16, 0.40, 0.30 | 155° | 0.60 | 0.40 | **new**: pines, the shaded underside of crowns |
| 12 | `sand` | 0.80, 0.66, 0.44 | 37° | 0.45 | 0.80 | **new**: paths |
| 13 | `stone` | 0.62, 0.62, 0.66 | 240° | 0.06 | 0.66 | **new**: rocks, pillars |
| 14 | `slate` | 0.40, 0.40, 0.47 | 240° | 0.15 | 0.47 | **new**: the shaded side of stone, steps, roofs |
| 15 | | | | | | spare (magenta in the texture, so a stray face shows) |

Cells 9 to 14 live in `build_wizard_glade.py`'s copy of the palette; `build_cat.py` still holds
only the first nine.

**Adding a colour.** Append it to `PALETTE`: the dict's order is the cell order. Never reorder or
remove a cell, because every UV already built points at a cell's position. One cell is left. When
the grid is full the next size is 8 × 8 cells on 32 px, which moves every cell: rebuild every
asset from its script in the same change (**new**). Before adding, try an existing cell: a new
colour has to earn its cell on more than one asset.

**Value and saturation.**

- The character is the brightest thing on screen: its body colours have value 0.95 to 0.98. *(what
  the cat does)*
- Its clothes are darker than its body (purple 0.68, plum 0.42), so the face stays the brightest
  part. Black is for the eyes. *(what the cat does)*
- Scenery sits under the character: value at most 0.80 and saturation at most 0.60 (**new**;
  blender-skills `stylized-style`: backgrounds desaturated, the subject saturated).
- The path is the brightest surface in a scene, because the eye goes to the brightest area
  (**new**; blender-skills `composition`).
- Shade is a darker cell on the faces that point down, never a light or a gradient (**new**; why
  is in `environment.md`, Lighting).

**Accents.** Purple, plum, gold, cyan and pink are the wizard's colours. In a scene they cover at
most a tenth of the visible surface, on the landmark and on things the player uses (**new**;
blender-skills `palette-examples`: 70 % dominant, 20 % secondary, 10 % accent). The glade
measures 83 % greens, 15 % sand, wood and stone, and 1.8 % accent; its build script prints the
shares and fails over 10 %.

## Shapes

All of this is what the cat does.

- **Faceted.** Flat shading on every face. No smooth shading, no subdivision, no bevels.
- **Few-sided primitives.** An icosahedron (20 triangles) for a head or a crown, a three-sided
  prism (8) for a tail or a staff, a five- or six-sided cone for a hat or a pine tier, a lofted
  ring of cross-sections for a body or a path.
- **Tapered spikes for anything soft.** Fur is tetrahedra (4 triangles each) in fans of two or
  three, pointing along the way it would hang. Foliage and grass use the same spike in green.
- **Chunky silhouette.** The head is as wide as the body is long and takes 53 % of the height to
  the ear tips. Ears, hat and tail are big enough to read at 512 px from every view.
- **Colour before geometry.** The muzzle, the belly and the hat band are painted facets. A new
  shape is added only when it changes the outline.
- **Nothing hidden, nothing floating.** A part covered by another is deleted (the crown tuft under
  the hat). A part that sits on a surface is seated on it by a ray cast, its base just under the
  surface (`seated`). The one exception is magic: a spark hangs in the air by the crystal.
- **Closed parts.** Every part is a closed solid, and parts that never move apart are joined.
- **Symmetry where a face is.** The head is turned so it mirrors across x = 0; the hat and its tip
  lean off-axis on purpose.

## Proportions

1 Blender unit = 1 stud. The cat faces −Y.

| What | Studs | Against the cat |
|---|---|---|
| Wizard cat to the ear tips | 1.93 | |
| Wizard cat to the hat tip | 2.54 | 1 |
| Wizard cat's width (cheek fur) and length | 1.56, 1.91 | |
| Roblox's default avatar | about 5 | 2 |
| Door opening | 2.1 wide, 3.35 tall | 1.3 tall (**new**) |
| Landmark, whole | 5.65 | 2.2 (**new**) |
| Path | 3.0 wide | two cats pass (**new**) |
| Sapling | 3.6 | 1.4 (**new**) |
| Broadleaf tree | 7.0 | 2.75 (**new**) |
| Pine | 7.9 | 3.1 (**new**) |
| Large rock | 1.2 tall, 2.4 wide | half (**new**) |
| Small rock, mushroom, grass tuft | 0.55 to 0.75 | a quarter: below the cat's chin (**new**) |

The world is sized to the cat, which is half the height of Roblox's default avatar. A door at
1.3 cats is too low for a default avatar: if one also walks this world, doors and paths take
their size from it instead (**new**).

## Triangle budgets

**New**, set from what the two examples measure. They sit under the low-poly targets in
blender-skills `lowpoly-style` (character 500 to 3,000, prop 50 to 500, environment module 100 to
800, tree 200 to 800), which is the point of the prompt the cat was built from.

| Class | Budget | Measured |
|---|---|---|
| Hero character | 300 | wizard cat 292, in 22 parts |
| Prop (rock, mushroom, tuft) | 100 | 12 to 20 |
| Kit piece (tree, landmark, wall) | 150 | trees 46 to 56, the door 72 |
| Environment tile, 24 × 24 studs, every copy counted | 3,000 | the glade 942 |

Roblox's own limit is 20,000 per mesh. A budget is checked by `bench_model.py`'s `budget` row.

## Preview renders

What `build_cat.py`'s `render` does, and every asset uses it so renders can be compared:

- EEVEE, 512 px square, an orthographic camera framed on the model's bounds with a 1.3 margin.
- Front, side, three-quarter and top.
- One sun, turned 50° about X and 30° about Z, strength 1.6. No fill, no rim.
- A flat pale world (0.90, 0.90, 0.93 at strength 0.35), opaque, which renders as mid grey.
- The Standard view transform, so a colour renders as it was picked.

A scene adds one shot from the game's camera with the character in it (`wide.png`; **new**).
None of this light reaches the game: `environment.md`, Lighting.

## Do and don't

| Do | Why |
|---|---|
| Take colours from the palette | one material and one texture for the whole game, so copies batch into one draw call |
| Paint a facet before adding a shape | a patch costs no triangles |
| Use spikes for fur, leaves and grass | one way of saying "soft" across characters and scenery |
| Keep scenery duller and darker than the character | the cat has to read first in every view |
| Put a piece's origin where it meets the ground, its base 0.1 under | it stands on the ground without a gap |
| Put the character in the scene before judging a size | a door is only right against who walks through it |

| Don't | Why |
|---|---|
| Smooth-shade, subdivide or bevel | the facets are the style, and each costs triangles |
| Add a material for a colour | a draw call per part for the same picture |
| Reorder palette cells | every UV already built points at the old position |
| Use an accent colour on scenery | it stops meaning "the wizard was here" |
| Keep geometry nobody sees | the first cat spent 20 triangles on a belly inside its body |
| Float a part near a surface | it reads as a mistake in the side view |
| Copy an existing game's character or kit | the reference board is for proportion and budget only |

## Check an asset against the theme

For the reviewer in [`visual-review.md`](visual-review.md): add these to the brief as measured
facts or as things to look for. They sharpen criteria 5 (proportions), 6 (low-poly craft) and 7
(colour).

1. One material named `Palette`, one 16 px texture (`bench_model.py`: `materials`, `textures`).
2. Every colour is a palette cell. A magenta face is a face nobody painted.
3. Triangles within the class budget above (`budget`).
4. Every face flat-shaded. No smooth gradient across an edge in any render.
5. Soft things are tapered spikes. No hair cards, no round blobs.
6. Scenery: no colour brighter than 0.80 or more saturated than 0.60; accents under a tenth.
7. The asset stands next to the wizard cat in one render, and its size matches the table.
8. Nothing floats and nothing pokes through, checked in the side and top views.
9. Every part closed (`closed`), and no part hidden inside another.
10. The silhouette reads in all four views with the colours ignored.
