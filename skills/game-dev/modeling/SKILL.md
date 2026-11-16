---
name: game-dev-modeling
description: >-
  Make 3D models for a game with any coding agent, and get them into the engine within its limits.
  Builds in Blender from a Python script (the durable source), driven through the Blender Lab MCP
  server, the Blender Agent Studio plugin, or plain `blender --background`; cleans up and exports
  (FBX for Roblox, GLB for the web); and checks the file against the engine's limits with
  `mesh_check.py` before import. Meshy AI generation is an opt-in route, off unless the user says
  they have the Meshy CLI. Use WHENEVER the work is "3D model", "make a prop / asset / character
  model", "Blender", "bpy", "low poly", "polycount", "triangle budget", "environment", "level", "modular kit",
  "set dressing", "art style", "shading", "bake", "geometry nodes", "export FBX / GLB / glTF",
  "import a mesh into Roblox", "MeshPart", "too many triangles", "texture size", "Meshy",
  "text to 3D", "image to 3D", "โมเดล 3D", "ปั้นโมเดล".
---

# Modeling for games

Adapted from three MIT projects: [meshy-3d-agent](https://github.com/meshy-dev/meshy-3d-agent)
(AI generation through the Meshy CLI), [Blender Agent Studio](https://github.com/ifBars/blender-agent-studio)
(scripted Blender work with checked renders), and [blender-claude-plugin](https://github.com/ra100/blender-claude-plugin)
(bpy references and the Blender Lab MCP setup). Install either Blender plugin for its deeper
per-topic references; this file is the route and the game-engine handoff.

## 0. Decide the route (ask once)

| Route | When | Cost | Default |
|---|---|---|---|
| **Blender, scripted** | props, buildings, modular kits, stylised or low-poly assets | free, local | **yes** |
| **Meshy** (AI generation) | an organic shape or a character from a picture or a line of text | paid credits, cloud | **off** |
| **Existing file** | the user has a model already | free | when a file is given |

**Meshy is off by default.** Before the first model, ask once: "Do you have the Meshy CLI set up
(a Meshy account and `meshy` installed)? If not, I'll build it in Blender." Then:

- **No, or no answer:** do not use Meshy, and do not install `meshy-cli` or suggest signing up.
  Do not ask again in this project. Go back to Meshy only when the user brings it up.
- **Yes:** run `meshy --version` and `meshy auth status --format json --no-update-check`. Only a
  verified session counts. Then follow [Meshy rules](#meshy-only-when-opted-in) below. Meshy's own
  skill installs its CLI without asking; that step does not apply here.

## 1. Know what the model is for

Before building, write down: the engine (Roblox, web, other), what it is (prop, building,
character to rig), its size in the game (Roblox studs, metres), the triangle budget, and the
style. For Roblox the hard limits are in [section 5](#5-engine-limits). A character to rig needs a
T- or A-pose and clean topology; a prop does not.

## 2. References first

Before building, collect 6 to 12 references and write them down in `references.md` beside the
build script: link, author, licence, polygon count, and **what each one gives** (a proportion, a
budget, a way to do fur or colour).

- **Sketchfab** is measurable: `https://api.sketchfab.com/v3/search?type=models&q=<terms>&max_face_count=<n>`
  and `.../v3/models/<uid>` return face counts, licences and thumbnails without a login.
- **Pinterest and image boards** are mood only: rights unknown, nothing copied, no image committed.
- **Not a copy:** no existing game's or brand's character, even when it shows up in the search.
- Put your renders next to the closest references before calling the model done.

## 3. Blender (default route)

**Check Blender first:** `blender --version` (macOS: `/Applications/Blender.app/Contents/MacOS/Blender`).
Not installed: say so (blender.org/download, free) and stop the Blender steps.

Three ways to drive it; use the first that is available:

1. **Blender Agent Studio plugin** (Claude Code, Codex): bounded inspection and render tools, and
   a `blender_check_setup` doctor. Install: `claude plugin marketplace add ifBars/blender-agent-studio`.
2. **Blender Lab MCP server** (official, Blender 5.1+; v1.0.3, 2026-09-11): a Blender add-on on
   `localhost:9876`, plus the `blender-mcp` server for any stdio MCP client. It runs model-written
   Python in the live Blender session **with no sandbox**: say so and ask before wiring it up.
   Setup checked on Blender 5.3.0, from the v1.0.3 release files
   (projects.blender.org/lab/blender_mcp/releases):
   - Add-on: `blender --command extension install-file -r user_default -e mcp-1.0.3.zip`, then
     enable it and turn on Preferences → System → Allow Online Access. It auto-starts on port
     9876 when Blender opens with a window.
   - Server: unzip `blender-1.0.3.mcpb` and register `uv run --directory <unzipped> blender-mcp`
     (stdio) with the agent. `BLENDER_PATH` names Blender for the background tools.
   - Two modes. The `*_for_cli` tools open a `.blend` in background Blender and need no window or
     add-on; `execute_blender_code_for_cli` edits a temporary copy, so save with
     `save_as_mainfile(copy=True)` to keep a result. The live tools (`execute_blender_code`,
     `get_objects_summary`, `get_screenshot_of_window_as_image`) drive the open Blender. Code
     returns data by assigning a dict to `result`; `print` output is not returned.
3. **Plain Blender:** write the script, then `blender -b --python build_<asset>.py`. Works for any
   agent with a shell.

Rules, whichever way:

- **The Python script is the source.** Save `art/<asset>/build_<asset>.py` that builds the model
  from an empty scene, plus the `.blend` it saves. A change is an edit to the script and a rerun.
- **Work in stages:** blockout at true scale → primary forms → secondary detail → materials →
  cleanup → export. Check proportions at the blockout, not at the end.
- **Look at it.** Render front, side, three-quarter and top views and open them before calling the
  model done. A render shows the look, not the topology: section 4's checks cover that.
- **Colour and textures:** read [`references/texturing.md`](references/texturing.md) first. Low-poly
  work uses one material over a small palette texture (power of two), not a material per colour.
- **Materials that must leave Blender:** read [`references/shading.md`](references/shading.md) first. No engine reads a procedural node tree: build the look with nodes, bake it to a power-of-two image, export one Principled material over that image.
- **Scatter, repeats, variants from a seed:** read [`references/geometry-nodes.md`](references/geometry-nodes.md) first. Realize Instances, apply the modifier, cap the count, and count triangles after realizing. `examples/crystal-ground/build_crystal_ground.py` is the worked case for both.
- **Bones and animation:** read [`references/rigging.md`](references/rigging.md) first. A segmented low-poly model is joined into one mesh and weighted part by part; `examples/wizard-cat/rig_wizard_cat.py` is the worked case.
- **Scenes and levels:** read [`references/environment.md`](references/environment.md) first. A scene is a kit: each unique piece is built once, exported once (`kit/<Piece>.fbx`) and placed from a layout table, so Roblox uploads it once and instances the copies. `examples/wizard-glade/build_wizard_glade.py` is the worked case.
- **The house look:** read [`references/art-theme.md`](references/art-theme.md) before modelling anything that stands next to the wizard cat: the palette cells, the value and saturation rules, the size ladder in studs, and the triangle budget per asset class.
- **Modifiers, then apply.** Mirror, bevel, subdivision and weld are fine while working; apply
  them before export so the engine gets the real mesh. Booleans leave n-gons: clean them up.

## 4. Export

```bash
blender -b art/rock/rock.blend --python scripts/blender_export.py -- --target roblox --out build/rock.fbx --dry-run
blender -b art/rock/rock.blend --python scripts/blender_export.py -- --target roblox --out build/rock.fbx
```

`--target roblox` applies scale and rotation, then writes FBX with Roblox's documented settings
(Path Mode Copy, Embed Textures, FBX Unit Scale, no leaf bones, no baked animation unless
`--animation`). `--target web` writes a GLB. `--dry-run` prints triangles, n-gons and whether
transforms were applied, and writes nothing. Checked on Blender 5.3.0: the cat example's FBX
re-imports with every scale 1 and the same triangle count.

## 5. Engine limits

Check the file before importing it:

```bash
python scripts/mesh_check.py build/rock.glb --target roblox      # exit 1 = over a limit
python scripts/mesh_check.py build/level.glb --target web --max-total 150000
```

It reads GLB, glTF and OBJ. For an FBX, export a GLB beside it and check that.

**Roblox** (create.roblox.com/docs/art/modeling, read 2026-11-16):

| Rule | Value |
|---|---|
| Triangles | at most **20,000 per mesh**; split a bigger model into parts |
| Geometry | watertight, no exposed backfaces, quads where possible (no n-gons), no zero-thickness faces |
| Import formats | `.fbx` (meshes, hierarchy, PBR textures, rigs, animation), `.gltf`, `.obj` (single simple mesh) |
| Textures | `.png`, `.jpg`, `.tga`, `.bmp`; about 256 px for a 5-stud object, 512 for 10, 1024 for 20. The page also states 4096 px support but 1024 for PBR maps: stay at 1024 unless checked |
| Normal maps | OpenGL, tangent space |
| Rigs | bones with scale 1 and rotation 0, root at the origin, at most 4 bone influences per vertex, no influence on the root |
| Avatar items | their own specs (character bodies, accessories): read those pages instead |

**Web (three.js and friends):** GLB. No fixed limit; agree a budget for the whole scene with the
user and pass it as `--max-total`.

Then import (Roblox: Studio → 3D Importer), and look at it in the engine. With Studio's MCP server
connected, `screen_capture` after `insert_asset` or the import shows it in place.

## 6. Bench

A case in `benchmarks/*.toon` holds the prompt as typed, the budget and a rubric;
`scripts/bench_model.py` scores a built model against it (exit code = failed checks):

```bash
blender -b --factory-startup --python examples/lowpoly-cat/build_cat.py -- --out examples/lowpoly-cat
python scripts/bench_model.py benchmarks/lowpoly-furry-cat.toon examples/lowpoly-cat/cat.glb
```

Checks: triangle budget, the engine's limits, every mesh closed (edges welded by position, each
shared by two triangles), named parts, modelled fur, the build script beside the model, and four
renders. Whether it *looks* like the prompt is the `manual` `look` row: score it with
[`references/visual-review.md`](references/visual-review.md), a fresh reviewer on a fixed 0–10
scale with evidence per view, never the builder's own eye.

Worked case, "Create an cat furry charactor which lowest polygon" (`examples/lowpoly-cat/`):
**128 triangles** in 19 closed parts, one material, 9/9. How it got there:

| Build | Triangles | What changed |
|---|---|---|
| v1 | 168 | first pass from the prompt alone |
| v1.1 | 148 | renders showed a belly hidden inside the body (20 triangles for nothing) and a floating chest tuft |
| v3 | 128 | after the reference board (`references.md`): character proportions, muzzle and belly as face colours instead of shapes, bigger eyes |
| v4 | 128 | after `references/texturing.md`: one material over a 16 px palette texture instead of four materials |
| wizard | 200 | the follow-up "output is need wizard cat": `examples/wizard-cat/` dresses the same cat (hat, cape, crystal), 9/9 on its own case |

A second case, `benchmarks/crystal-ground.toon` (`examples/crystal-ground/`): a tile for the cat to
stand on, crystals and rocks scattered by Geometry Nodes from a seed, procedural materials baked
to a 256 px colour map and a 128 px emission map. **498 triangles** in 3 closed parts, one
material, 8/8.

| Build | Triangles | What changed |
|---|---|---|
| first render | 458 | the 128 px emission map showed crystal glow on the ground's rim: the bake margin was wider than the gap between UV islands |
| final | 498 | margin tied to the gap; small pieces given 2.5 times the texel density; the ring widened so the count reaches its cap more often |

The script never caught any of these: the renders and the references did.

Scene case (`examples/wizard-glade/`, `benchmarks/wizard-glade.toon`): a 24 × 24 stud glade, **942
triangles** placed from 354 unique in 10 kit pieces (35 copies), one material, 8/8.

## 7. Asset records

Every model gets a line in `assets/provenance.yaml`: where it came from (script path, Meshy task
id, or the source and its license), the date, and the asset id once uploaded. Never use a model
whose license is unknown; Poly Haven (CC0) is safe for textures and HDRIs.

## Meshy (only when opted in)

Only after the user said yes in section 0 and `auth status` reports verified. Rules from
meshy-3d-agent's skill that matter here:

- **Every create costs credits.** Run `meshy balance` first, give the user the plan and the
  estimate the CLI reports, and get a yes before the first paid create. A rerun, a variant or an
  extra stage is a new yes.
- **Ask what the model is for** (game asset, character to rig, render): it picks the route. A
  game asset or a triangle budget means **smart topology** (`--model-type smart-topology
  --target-polycount N`), not a standard model reduced afterwards. For Roblox, N stays under
  20,000 per mesh.
- Submit once with `create --async`, keep the task id, `wait` on it; a timeout is not a reason to
  create again. Use `--format json --no-update-check` on every command.
- **An LOD is a remesh of the existing task**, never a new generation.
- Download the GLB, run `mesh_check.py` on it, then fix or export in Blender (sections 3–5). A
  preview image is not proof of topology.
- Login is the CLI's device flow, approved by the user in a browser. Credentials never go in chat
  or in files the agent writes.
