# Environments: a scene built from a kit

Read before building a level, a room or a tile of world. A scene is a few meshes placed many
times, so it has rules a single asset does not. Each rule names its source (read 2026-11-16);
"checked in Blender 5.3" means the fact comes from running the worked example,
`examples/wizard-glade/build_wizard_glade.py`, on Blender 5.3.0. The look of the pieces is in
[`art-theme.md`](art-theme.md).

## Sources

| Source | Licence | What it gives |
|---|---|---|
| [ai-skills-blender: blender-create-environment](https://github.com/SamuelAsherRivello/ai-skills-blender/tree/main/skills/blender-create-environment) | MIT (Rivello Multimedia Consulting) | the order of work: units and reference heights before layout, one representative area checked through its camera before the scene grows, a kit with the same origin and snap sizes, a recorded seed, a check from the real camera. Its `agents/openai.yaml` is a display name only |
| [blender-skills](https://github.com/arjun988/blender-skills/blob/main/SKILLS_GUIDE.md): `environment-artist` (with `modular-kits.md`, `composition.md`), `scene-assembly`, `set-dressing`, `lighting`, `lowpoly-style`, `stylized-style`, `vegetation-artist`, `references/polycount-budgets.md` | MIT (blender-skills contributors) | grid and kit rules, the smallest useful kit, density by zone, composition layers, triangle targets, key/fill/rim lighting. Its sizes are metres for a 1.7 m person and its budgets are for realistic games: the ratios are used here, the numbers are not |
| [Roblox: improve performance](https://create.roblox.com/docs/performance-optimization/improve), the [environmental art curriculum](https://create.roblox.com/docs/tutorials/curriculums/environmental-art) (greybox, develop polished assets, assemble an asset library), [global lighting](https://create.roblox.com/docs/environment/lighting), [atmosphere](https://create.roblox.com/docs/environment/atmosphere), `Humanoid` reference | CC-BY-4.0 (read from the `Roblox/creator-docs` repository) | what the engine does with the result: draw calls and instancing, one MeshPart per mesh, grid sizes in studs, and where the light comes from in the game |

Nothing is quoted from any of them: the rules below are restated. Not read: the first source's
companion skill `blender-create-visual-target-2d` and its render-style gallery (it generates a 2D
target image first; this skill uses a reference board instead, SKILL.md section 2).

## Order of work

Each step ends with something to look at. Do not start a step while the one before it is wrong.

1. **Brief.** The engine, the camera the game uses, the size of the playable area in studs, the
   character that walks it, the budget per view, the mood in one line. *(create-environment:
   scale and camera needs come first, and a small representative area before the whole)*
2. **Reference board.** As SKILL.md section 2, plus one thing an asset board lacks: references for
   the *layout* (where the landmark sits, how the path reaches it), kept apart from references
   for the look. *(create-environment: tell a quality reference from a layout to reproduce)*
3. **Blockout at true scale.** Boxes only, 1 Blender unit = 1 stud, the character standing in it.
   Fix these numbers before any piece is modelled:

   | What | Rule | Source |
   |---|---|---|
   | Character | the game's own character, in the scene from the first render | blender-skills: a scale figure is always present |
   | Door | opening about 1.25 × the character's height, a little over one character wide | blender-skills gives 2.1 × 0.9 m for a 1.7 m person; the ratio is what carries over |
   | Path, corridor | wide enough for two characters to pass | Roblox's sample keeps doors and halls at least 10 studs wide for two default avatars; blender-skills gives 1.5 m |
   | Wall that must stop a jump | taller than the jump | Roblox's greybox page says 10-stud walls against a "default jump height of 5 studs"; the `Humanoid` reference gives `JumpHeight` 7.2 and `WalkSpeed` 16 studs a second. The two pages disagree, and jump *distance* is on neither: measure both in Studio with the game's character before fixing a gap |
   | Grid | one snap size for the whole kit, and every piece a multiple of the smallest | Roblox's sample kit snaps at 5 studs and 90°; blender-skills: never mix grid sizes in a kit |

4. **Kit pieces on the grid.** List the unique pieces the blockout needs and build each once, at
   the origin. Structural pieces (walls, floors, tiles) snap to the grid and keep their origin at
   the same corner; props (trees, rocks) keep their origin where they touch the ground and turn
   freely. *(Roblox: a consistent pivot is what lets pieces meet; props only need a logical one.
   create-environment: the same origin and snap sizes across the kit)* Build the smallest kit that
   closes the blockout before any hero piece. *(blender-skills)*
5. **Set dressing.** Place copies from a table in the script, never by hand: the table is the
   layout, and a recorded seed stands in for one when pieces are scattered. *(create-environment)*
   Dress in clusters around a reason (mushrooms by the wizard's door), keep the path clear, leave
   the background sparse, and stop before every surface is covered. *(blender-skills: set-dressing)*
   Break repetition with a turn or a small scale, which costs no new mesh. *(blender-skills:
   modular-kits)*
6. **Lighting and atmosphere.** Last in Blender, and only for the preview: see
   [Lighting](#lighting-blender-against-roblox). Broad light must not hide a layout problem.
   *(create-environment)*
7. **The game's camera.** Render from where the player's camera will be, at its height, along the
   path, as well as the four orthographic views. One landmark per view, tall pieces behind it and
   low ones in front, the brightest surface where the player should go. *(blender-skills:
   composition; create-environment: inspect from the actual camera)*

## Budgets: a scene against one asset

An asset has one number, its triangles. A scene has three.

| Budget | Rule | Source |
|---|---|---|
| Per piece | 20,000 triangles per mesh is Roblox's limit; the house budgets per class are in `art-theme.md` | Roblox specifications |
| Per view | count every *placed copy* the camera can see, not the unique meshes. The glade: 354 triangles of unique mesh, 942 placed | `mesh_check.py` multiplies each mesh by its instances |
| Draw calls | fewer unique mesh-and-texture pairs. In Roblox they cost more than triangles do | Roblox: improve performance |

**How copies reach Roblox.** Every placed copy is its own MeshPart. Roblox draws MeshParts in one
call when they share the same mesh asset and the same texture (or the same SurfaceAppearance), so
ten copies of one tree cost one draw call. Importing a whole scene as one file can give each copy
its own asset id, and then nothing is shared. *(Roblox: improve performance, "missed instancing
opportunities")* So:

- Export each unique piece **once**, on its own, at the origin; upload it once; copy it in Studio.
- Ship a layout (kit name, position, turn, scale per copy) so the scene can be rebuilt from the
  kit. Blender is Z-up and Roblox Y-up: (x, y, z) in Blender is (x, z, −y) there.
- Keep the whole kit on **one palette texture and one material**. A second texture on some trees
  splits their batch.
- Not stated by Roblox's page, so not claimed here: whether a copy resized in Studio stays in the
  same batch as the others.

In Blender the same thing is a linked copy: `bpy.data.objects.new(name, mesh)` on a shared mesh.
The GLB then holds each mesh once with a node per copy (the glade: 10 meshes, 35 placed nodes),
and `mesh_check.py` prints `instances=`. *(checked in Blender 5.3)*

Roblox sets no triangle limit per scene. The per-view number is a house budget: agree it in the
brief, and for a Roblox world check it on a phone, with instance streaming on for anything large.
*(Roblox: improve performance)*

## Separate meshes or one

| Export separately | Merge into one mesh |
|---|---|
| anything placed more than once: it is how the engine instances it | parts that never move apart and are always seen together: a trunk and its crown, a frame and its gable (`join`) |
| anything that moves, opens or is picked up, with its origin at the hinge or the hand | detail that would otherwise be its own MeshPart for no reason: Roblox makes one MeshPart per mesh in the file |
| anything that needs its own collision setting (`CollisionFidelity`: Box is the cheapest and safe for a small anchored part) | |
| the ground, apart from what stands on it | |
| anything over 20,000 triangles, split by area | |

Never merge the scene. One mesh for the whole glade would draw once, but it loses instancing
across tiles, the engine can no longer skip the pieces outside the camera, and one tree cannot be
changed without re-uploading everything. *(Roblox: improve performance; blender-skills: instance
every repeat)*

The glade's door does not open, so its leaf is merged into the landmark. A door the player opens
is a separate piece.

## Lighting: Blender against Roblox

A Blender light setup does not reach the game. The kit FBXs are written with meshes only, and the
glTF exporter leaves lights and cameras out by default: a scene with a sun and a camera exports
with neither. *(checked in Blender 5.3)* The world colour and the view transform never export.

| In Blender (preview only) | In Roblox (the real look) |
|---|---|
| one sun and a pale world, the same for every asset, so renders can be compared (`build_cat.py`'s `render`) | `Lighting`: `Ambient`, `OutdoorAmbient`, `Brightness`, `ColorShift_Top` and `ColorShift_Bottom`, `ClockTime`, `GeographicLatitude`, shadows |
| key, fill and rim for a beauty shot *(blender-skills: lighting)* | `Atmosphere` under `Lighting`: `Density`, `Offset`, `Haze`, `Color`, `Glare`, `Decay` for depth and mood |
| the Standard view transform, so colours render as picked | lights placed in Studio; shadows are costly, so few of them cast *(Roblox: improve performance)* |

What does cross over is **colour in the texture**. Shade that must always be there goes into the
palette as a darker cell on the faces that point down (the underside of a tree's crown), which
costs no triangles and looks the same under any light. Mood (time of day, fog, warmth) belongs to
`Lighting` and `Atmosphere`, set in Studio and judged there. A scene that only looks right under
its Blender light is not finished.

## Checked in Blender 5.3

Found by running the worked example, not from a source:

- **Blender exits 0 after a script error.** A build that hits an assertion still returns 0 unless
  the script catches it and calls `sys.exit(1)` (or Blender runs with `--python-exit-code 1`).
- **`build_cat.py`'s `render` is sized for a character.** Its orthographic camera stands 8 units
  from the centre, which is inside a 24-stud scene, and geometry behind the camera is not drawn.
  The glade parents every piece to one empty, scales it to 0.25 for the four views and puts it
  back; an orthographic view looks the same at any scale.
- **`bound_box` overstates a turned object.** Its world-space corners are the corners of a turned
  box. To test "inside the tile", use the mesh's vertices.
- **Triangulate in the script.** Then the `.blend`, the GLB and the FBX report the same count.
- **A kit FBX round-trips.** Re-imported into an empty Blender each piece is one mesh with one
  material, scale 1, the same triangles, closed (vertices welded by position first, as
  `bench_model.py` does), and the 16 px palette embedded.

## Worked example

`examples/wizard-glade/`: a 24 × 24 stud glade for the wizard cat.

```bash
blender -b --factory-startup --python examples/wizard-glade/build_wizard_glade.py -- --out examples/wizard-glade
blender -b --factory-startup --python examples/wizard-glade/build_wizard_glade.py -- --out examples/wizard-glade --verify examples/wizard-glade/kit/TreePine.fbx
python scripts/bench_model.py benchmarks/wizard-glade.toon examples/wizard-glade/wizard-glade.glb
```

| Piece | Triangles | Copies | Height above ground, studs |
|---|---|---|---|
| `Ground` | 12 | 1 | 0 (a slab 1 stud thick) |
| `Path` | 52 | 1 | 0.08 |
| `WizardDoor` (landmark) | 72 | 1 | 5.65 |
| `TreeRound` | 56 | 3 | 7.0 |
| `TreePine` | 46 | 3 | 7.9 |
| `TreeYoung` | 48 | 3 | 3.6 |
| `RockLarge` | 20 | 3 | 1.2 |
| `RockSmall` | 20 | 4 | 0.55 |
| `Mushroom` | 16 | 6 | 0.74 |
| `GrassTuft` | 12 | 10 | 0.7 |
| **Scene** | **942** placed, 354 unique | 35 | |

It writes the scene (`wizard-glade.blend`, `.glb`), `kit/<Piece>.fbx` once per piece,
`layout.json`, the four views and `wide.png` with the wizard cat on the path. The script asserts
its own rules and fails the build when one breaks: every piece closed, 3,000 triangles at most,
every copy inside the tile with its base on the ground, nothing on the path, accents under a tenth
of the visible surface. Not checked: the import into Roblox Studio, collisions, and how the glade
looks under `Lighting` and `Atmosphere`.
