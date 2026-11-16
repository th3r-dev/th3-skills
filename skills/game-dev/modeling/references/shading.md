# Shading for game assets

Read before building a material that has to leave Blender. Each rule names its source (read
2026-11-16). **"Checked in Blender 5.3"** means it was run headless on Blender 5.3.0 for this
file, not taken from a page. Texture budgets are in [`texturing.md`](texturing.md). The worked
case is `examples/crystal-ground/build_crystal_ground.py`: three procedural materials baked to a
256 px colour map and a 128 px emission map, exported as one material.

## Sources

| Source | Reached | What it gives |
|---|---|---|
| [CG Cookie: Beginners guide to materials and shading in Blender](https://blog.cgcookie.com/posts/beginners-guide-to-materials-and-shading/) (Ewa Wierbik-Ziąbka, 2024-09-16) | the live page answers HTTP 403 to two clients; read from the Wayback Machine copy of 2026-10-30 | start from one Principled BSDF; metallic up and roughness down for a shiny surface; lighting changes how a material reads; look at the rendered preview. Nothing on export or baking |
| [Blender Studio: Shading Theory](https://studio.blender.org/training/blender-fundamentals-45-lts/blender_4-5_lts_shading-theory/) (Beau Gerbrands, Blender Fundamentals 4.5 LTS, a free lesson) | yes, the lesson text; the videos were not watched | what each Principled BSDF input means |
| [Scribd: Blender 04](https://www.scribd.com/doc/282838414/Blender-04) | **no** | only the page summary shows without signing in ("Blender Shading & Lighting Techniques", 38 pages on Cycles lamps and materials). Nothing here comes from it |
| [ra100/blender-claude-plugin](https://github.com/ra100/blender-claude-plugin) (MIT), `skills/blender-shader-nodes` and its `references/python_api.md` | yes | bpy node type strings and material recipes. Three things in it did not hold on 5.3: see [bpy on 5.3](#bpy-on-53) |
| Blender manual: [glTF 2.0](https://docs.blender.org/manual/en/latest/addons/scene_gltf2.html), [Render Baking](https://docs.blender.org/manual/en/latest/render/cycles/baking.html), [Color Spaces](https://docs.blender.org/manual/en/latest/render/color_management/color_spaces.html), [Displays and Views](https://docs.blender.org/manual/en/latest/render/color_management/displays_views.html) | yes | what the exporter reads, the bake types, colour management |
| Roblox: [Surface Appearance](https://create.roblox.com/docs/art/modeling/surface-appearance), [texture specifications](https://create.roblox.com/docs/art/modeling/texture-specifications), [Importer](https://create.roblox.com/docs/studio/importer) | yes | what Studio reads |

## What survives export

The glTF exporter "will construct a glTF material based on the nodes it recognizes": a Principled
BSDF, with plain values or Image Texture nodes on its inputs. *(Blender manual, glTF)*

| Principled BSDF input | In the GLB | In Roblox (SurfaceAppearance) |
|---|---|---|
| Base Color: a value or an Image Texture | base colour factor or texture | `ColorMap` |
| Metallic, Roughness | two factors, or one image with roughness in green and metallic in blue, set to Non-Color | `MetalnessMap`, `RoughnessMap`: one greyscale image each |
| Normal: Image Texture → Normal Map node | tangent space, the only kind glTF takes | `NormalMap`: OpenGL, tangent space only |
| Emission Color, Emission Strength | emissive texture and factor; a strength over 1 needs the `KHR_materials_emissive_strength` extension | a greyscale `EmissiveMaskContent` plus `EmissiveTint` and `EmissiveStrength` |
| Alpha | alpha mode (opaque, mask, blend) read from the nodes on the socket | the alpha of `ColorMap`, used as `AlphaMode` says |
| Vertex colour (colour attribute) | `COLOR_0`, a multiplier on base colour | read by the importer, multiplied by the part's colour |

*(Blender manual, glTF; Roblox Surface Appearance, texture specifications, Importer)*

What does not survive:

- **Procedural node trees.** Checked in Blender 5.3: a cube with Noise Texture → Color Ramp →
  Base Color exports a material with no texture and no base colour at all. The model arrives
  white and nothing warns.
- **Every other shader node**: Diffuse, Glossy, Shader to RGB (EEVEE only, *ra100*), Light Path
  and Layer Weight tricks (*CG Cookie* suggests them for look development; they stay in Blender).
- **Transmission, subsurface, volume.** Costly and noisy even in Blender *(Blender Studio)*, and
  Roblox has no map for them.
- **Lights and the world.** Area lights and world lighting are ignored on export. *(Blender
  manual, glTF)*

Roblox also wants one material per mesh, one UV set, all UVs inside 0–1, and PBR maps of at most
1024 px. *(Roblox texture specifications)*

## The route: procedural in Blender, baked for the engine

Build the look with nodes, then bake it into images and export a material that holds only those
images. "Cycles shaders and lighting can be baked to image textures", for "export to game
engines". *(Blender manual, Render Baking)*

```python
scene.render.engine = "CYCLES"          # baking is a Cycles feature
scene.cycles.samples = 1                # colour and emission are not lit: one sample is exact
img = bpy.data.images.new("prop", 256, 256, alpha=False)
for mat in materials_on_the_selected_objects:
    node = mat.node_tree.nodes.new("ShaderNodeTexImage")   # linked to nothing
    node.image = img
    mat.node_tree.nodes.active = node   # the active Image Texture node is the bake target
bpy.ops.object.bake(type="DIFFUSE", pass_filter={"COLOR"}, margin=3, margin_type="EXTEND")
img.filepath_raw, img.file_format = "/abs/path/prop.png", "PNG"
img.save()
```

- **A UV map and a target.** The mesh needs a UV map, and each material an active Image Texture
  node holding the image. A material without one bakes nothing. *(Blender manual)*
- **Pick the bake type by the map.** *(Blender manual; the identifiers are checked in Blender 5.3)*

  | Map | `type` | Notes |
  |---|---|---|
  | Base colour | `DIFFUSE` with `pass_filter={"COLOR"}` | "If only Color is selected you get the pass color": no light, no shadow |
  | Emission | `EMIT` | colour times strength; keep the strength at 1 or under, an 8-bit PNG holds no more |
  | Roughness | `ROUGHNESS` | save as Non-Color |
  | Normal | `NORMAL` | keep Tangent and +X, +Y, +Z: that is the OpenGL layout glTF and Roblox take |
  | Contact shadow | `AO` | glTF can carry it; Roblox has no slot, so multiply it into the colour |
  | Lit, for an unlit look | `COMBINED` | bakes the lighting in; the asset then ignores the engine's lights |

- **Power of two, small.** 256 px for a prop about 5 studs wide, 512 the ceiling.
  *([`texturing.md`](texturing.md): ZEPETO, Roblox)* The emission map can be half the colour
  map's size: it is a soft gradient.
- **One call bakes every selected object** into its materials' targets, and the image is cleared
  once. Checked in Blender 5.3: three objects sharing one image all land in it.
- **The margin has to fit the gap.** The margin fills past each UV island so filtering does not
  pull in the background *(Blender manual)*. Checked in Blender 5.3: objects are baked one after
  another and none sees the others' islands, so a 3 px margin across a 2.5 px gap painted
  crystal glow onto the ground's rim. Pack with `uv.pack_islands(margin=GAP,
  margin_method="FRACTION")` and bake with a margin of at most `GAP * size / 2` pixels.
- **Bake the kit, not the scatter.** Checked in Blender 5.3: UVs ride through Instance on Points
  and Realize Instances. Unwrap and bake the one crystal cluster, and all six copies share its
  texels. Unwrapping after the scatter would cut each copy's share to a sixth.
- **Spend texels where the player looks.** Before packing, the example scales the UVs of faces
  that point straight down to a quarter, and the small pieces seen close to 2.5 times.
  *([`texturing.md`](texturing.md), even texel density, ZEPETO)*
- **Then swap the material.** The exported objects get one material: Image Texture → Base Color,
  Image Texture → Emission Color, plain values for the rest. The procedural materials stay in
  the `.blend` behind a fake user and are on no exported object.
- **Baked colour is deterministic.** Checked in Blender 5.3: two runs with the same seed wrote
  byte-identical PNG and GLB files.

### Palette or bake

| | Palette texture (`examples/lowpoly-cat`) | Baked texture (`examples/crystal-ground`) |
|---|---|---|
| Use when | every face is one flat colour | colour changes inside a face: a gradient, noise, a glow that fades |
| Texture | 16 px, shared by any number of models | 256 px + 128 px, for this model only |
| UVs | every face on one point of its cell | a real unwrap with gaps |
| Cost of a change | repaint a cell | rerun the bake |

The crystal ground bakes because its three looks cannot be a palette cell: moss noise across a
flat top, a violet-to-cyan gradient up each crystal, and a glow that grows toward the tip.

## Stylised low-poly shading

- **Flat colour:** the palette texture, with Closest filtering. *([`texturing.md`](texturing.md))*
- **Faceted normals:** flat shading is a property of the mesh, not of the material, and needs no
  normal map. Checked in Blender 5.3: meshes from `from_pydata` and the primitives are flat by
  default, and the GLB keeps the facets by splitting vertices (the 58-triangle ground has 31
  positions and 105 exported vertices).
- **Gradients and ramps:** a Color Ramp on a coordinate (the Z of Generated for height), then
  bake. Constant interpolation on the ramp gives toon bands that survive the bake. *(ra100 for
  the recipe)*
- **Toon shading with Shader to RGB** works in EEVEE only *(ra100)*, so Cycles cannot bake it.
  Use it for renders, not for the export.
- **Vertex colour:** Roblox's importer reads vertex colours from `.fbx` and `.gltf` (its "Ignore
  Vertex Colors" setting is off by default) *(Roblox Importer)*, and a
  [staff post](https://devforum.roblox.com/t/vertex-colored-meshes-using-blender-and-studio/3050119)
  says they multiply the MeshPart's colour. No texture at all, but one colour per vertex and no detail
  inside a face. Not checked in Studio. `bake(target="VERTEX_COLORS")` writes a bake into the
  active colour attribute *(Blender manual; identifier checked in Blender 5.3)*.
- **A stray colour attribute tints the model.** Checked in Blender 5.3: with the exporter's
  defaults, a colour attribute no material uses still went out as `COLOR_0`. Delete it or pass
  `export_vertex_color="NONE"`.

## Theory that changes a choice

- **Start from one Principled BSDF.** It covers most materials, and it is the node exporters
  read. *(CG Cookie; Blender Studio; Blender manual, glTF)*
- **Metallic** switches to the metal model and uses the base colour as the reflection colour
  *(Blender Studio)*. Roblox says its values are usually 0 or 100% *(Surface Appearance)*: paint
  it black or white, not grey.
- **Roughness** is how much the surface scatters light: 0 is a mirror, 1 fully rough, and in a
  texture white is rough *(Blender Studio)*. Low-poly work holds one high value (the examples
  use 0.85 to 0.9) so facets do not flash.
- **Emission** makes the surface a light in a Blender render *(Blender Studio)*. Judge the glow
  in the engine, under its own lighting and bloom: "even the best materials can look flat
  without the right lighting" *(CG Cookie)*.
- **Colour maps are sRGB, data maps are Non-Color.** Blender works in scene linear and converts
  each image by its colour space. Normal and displacement maps "do not actually store colors,
  just data encoded as colors" and are marked Non-Color *(Blender manual, Color Spaces)*; so are
  roughness and metallic *(Blender manual, glTF; ra100)*. A data map left on sRGB gets a curve
  it should not have.
- **The view transform touches renders, not textures.** Only renders are saved with the view
  applied *(Blender manual, Displays and Views)*, so a bake comes out the same under any of them.
  For the check renders use **Standard**: "no extra conversion", "often used for
  non-photorealistic results", so a palette colour renders as picked. **AgX** is the default
  (checked in Blender 5.3) and desaturates bright colours like film. **Filmic** is deprecated in
  favour of AgX. **Khronos PBR Neutral** is made to keep sRGB base colours faithful under
  neutral light. *(Blender manual)*

## bpy on 5.3

All checked in Blender 5.3.

- A new material already has a Principled BSDF and a Material Output. `material.use_nodes = True`
  prints a DeprecationWarning ("expected to be removed in Blender 6.0").
- Emission is two inputs: `Emission Color` and `Emission Strength`.
- Noise Texture's output and Color Ramp's input are named `Factor` (`Fac` still resolves).
- `ShaderNodeTexMusgrave` is gone ("Node type undefined"): use Noise. *ra100* lists it as
  deprecated.
- `Material.shadow_method`, which *ra100* sets, does not exist; `blend_method`,
  `surface_render_method` and `use_backface_culling` do. Backface culling on makes the GLB
  material single-sided.
- `ShaderNodeMix` keeps a set of `A`, `B` and `Result` sockets per data type. Set `data_type`
  first, then take the socket whose `enabled` is true instead of an index.
- Blender exits 0 after a Python traceback. Catch it and `sys.exit(1)`, or pass
  `--python-exit-code 1`, or CI passes a build that wrote nothing.

## Check before export

1. Every exported mesh has one material, and that material is a Principled BSDF fed by Image
   Texture nodes and plain values only.
2. Every image is a power of two, at most 512 px, saved as PNG, with sRGB for colour and
   Non-Color for data.
3. One UV map per mesh, all of it inside 0–1.
4. No colour attribute you did not mean to ship.
5. Normal maps are OpenGL, tangent space.
6. `python scripts/bench_model.py benchmarks/<case>.toon model.glb` passes its `materials` and
   `textures` rows.
7. Open the GLB in a fresh Blender: one material, its image textures, the same triangle count.
8. Look at it in the engine. Not checked in Roblox Studio for the worked case: whether the 3D
   Importer wires the emission map into a SurfaceAppearance by itself. The file carries an RGB
   emission texture; Roblox's own format is a greyscale mask plus `EmissiveTint`.
