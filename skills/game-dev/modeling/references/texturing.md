# Texturing for game assets

Read before giving a model colour or textures. Each rule names its source (read 2026-11-16).
`mesh_check.py` measures texture sizes; `bench_model.py`'s `materials` and `textures` rows hold a
case to the budget.

## Sources

| Source | What it gives |
|---|---|
| [ZEPETO: 3D texture optimization guide by category](https://docs.zepeto.me/studio-guide/3d-texture-optimization-guide-by-category) | the budget rules: power-of-two sizes, texel density, 512 px, one material, channel packing, per-category limits, and why they matter in a multiplayer world |
| [Roblox: texture specifications](https://create.roblox.com/docs/art/modeling/texture-specifications) and [specifications](https://create.roblox.com/docs/art/modeling/specifications) | formats, size per object size, OpenGL normal maps |
| [Blender Guru: Texturing](https://www.blenderguru.com/posts/category/Texturing) | technique: [baking](https://www.blenderguru.com/posts/introduction-baking-cycles), [map types](https://www.blenderguru.com/posts/the-secrets-of-realistic-texturing), [variation](https://www.blenderguru.com/posts/basics-realistic-texturing), [grunge masks](https://www.blenderguru.com/posts/how-to-grunge) |
| [Angle 3D: 3D modeling and textures 101](https://www.angle3d.co/resource-library/3d-modeling-and-textures) | the basics: a texture is a 2D image wrapped on the mesh through its UV map |

## Pick the approach by style

| Style | Approach | Cost |
|---|---|---|
| **Low poly, flat colour** | one **palette texture** (8–64 px, a cell per colour), every face UV'd into its colour's cell | 1 material, 1 tiny texture; a new colour is a new cell |
| **Stylised, hand-painted** | one unwrap, one painted base-colour map at the budget size | 1 material, 1 map |
| **PBR (realistic)** | base colour, normal, and a packed roughness/metal/AO map, often **baked** from a high-poly model | 1 material, 2–3 maps |

The palette is the default for low-poly work: it is how `examples/lowpoly-cat` gets four colours
with one material. Per-face materials look the same in a render but cost a draw call each per
part.

## Budget rules

- **Power of two on both sides** (64, 128, 256, 512). The GPU pads other sizes up to the next
  power of two, which can double the memory. *(ZEPETO)*
- **512 px is the default ceiling.** 1024 × 1024 is four times the pixels and memory of 512, not
  two. Go up only for a large object seen close. *(ZEPETO)*
- **Roblox sizes by object size:** about 256 px for a 5-stud object, 512 for 10, 1024 for 20.
  Formats `.png`, `.jpg`, `.tga`, `.bmp`. *(Roblox)*
- **One material per asset**; more only where a property really differs (transparency, a special
  shader), never one per colour or per material type. *(ZEPETO)*
- **Pack masks into channels** instead of separate images. ZEPETO's layout: R metallic, G ambient
  occlusion, A smoothness. Check the target engine's own layout before packing: engines differ.
- **Even texel density.** Every part of the surface gets about the same pixels per unit, so no
  area is blurry next to a sharp one. Then shrink UV space for what is never seen (undersides,
  insides) and give it to what is (face, logo). *(ZEPETO)*
- **Count the whole scene, not one asset.** One over-budget item becomes a problem when every
  player in a world wears one: memory runs out on phones, and the OS closes the app. *(ZEPETO)*

## Technique

- **Normal maps** must be OpenGL, tangent space, for Roblox; DirectX-style maps look lit from the
  wrong side. *(Roblox)*
- **Bake** detail and lighting from a high-poly model onto the low-poly model's texture: unwrap,
  make an empty image, bake. That is how a low-poly game asset carries high-poly detail. Several
  objects can bake at once. *(Blender Guru)*
- **Map types:** diffuse/base colour (colour only, no lighting), normal (surface direction),
  specular or roughness (how sharp reflections are), displacement (real height; rarely in games),
  ambient occlusion (contact shadow). *(Blender Guru)*
- **Variation makes realism.** A uniform roughness or colour reads as plastic; varied roughness
  from the same texture sells the material. Grunge masks give dirt and wear without new
  geometry. *(Blender Guru)*
- **Closest (nearest) filtering** for palette textures, so neighbouring cells don't bleed into
  each other.

## Checks

```bash
python scripts/mesh_check.py model.glb --target roblox --max-texture 512
python scripts/bench_model.py benchmarks/<case>.toon model.glb    # materials and textures rows
```

Then look at the model in the engine at its game distance. A texture that passes every number can
still be blurry where the player looks.
