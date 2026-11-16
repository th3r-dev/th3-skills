---
name: game-dev-modeling
description: >-
  Make 3D models for a game with any coding agent, and get them into the engine within its limits.
  Builds in Blender from a Python script (the durable source), driven through the Blender Lab MCP
  server, the Blender Agent Studio plugin, or plain `blender --background`; cleans up and exports
  (FBX for Roblox, GLB for the web); and checks the file against the engine's limits with
  `mesh_check.py` before import. Meshy AI generation is an opt-in route, off unless the user says
  they have the Meshy CLI. Use WHENEVER the work is "3D model", "make a prop / asset / character
  model", "Blender", "bpy", "low poly", "polycount", "triangle budget", "export FBX / GLB / glTF",
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
style. For Roblox the hard limits are in [section 4](#4-engine-limits). A character to rig needs a
T- or A-pose and clean topology; a prop does not.

## 2. Blender (default route)

**Check Blender first:** `blender --version` (macOS: `/Applications/Blender.app/Contents/MacOS/Blender`).
Not installed: say so (blender.org/download, free) and stop the Blender steps.

Three ways to drive it; use the first that is available:

1. **Blender Agent Studio plugin** (Claude Code, Codex): bounded inspection and render tools, and
   a `blender_check_setup` doctor. Install: `claude plugin marketplace add ifBars/blender-agent-studio`.
2. **Blender Lab MCP server** (official, Blender 5.1+; v1.0.3, 2026-09-11): a Blender add-on on
   `localhost:9876`, plus the `blender-mcp` server for any stdio MCP client. It runs model-written
   Python in the live Blender session **with no sandbox**: say so and ask before wiring it up.
   Setup: projects.blender.org/lab/blender_mcp.
3. **Plain Blender:** write the script, then `blender -b --python build_<asset>.py`. Works for any
   agent with a shell.

Rules, whichever way:

- **The Python script is the source.** Save `art/<asset>/build_<asset>.py` that builds the model
  from an empty scene, plus the `.blend` it saves. A change is an edit to the script and a rerun.
- **Work in stages:** blockout at true scale → primary forms → secondary detail → materials →
  cleanup → export. Check proportions at the blockout, not at the end.
- **Look at it.** Render front, side, three-quarter and top views and open them before calling the
  model done. A render shows the look, not the topology: section 4's checks cover that.
- **Modifiers, then apply.** Mirror, bevel, subdivision and weld are fine while working; apply
  them before export so the engine gets the real mesh. Booleans leave n-gons: clean them up.

## 3. Export

```bash
blender -b art/rock/rock.blend --python scripts/blender_export.py -- --target roblox --out build/rock.fbx --dry-run
blender -b art/rock/rock.blend --python scripts/blender_export.py -- --target roblox --out build/rock.fbx
```

`--target roblox` applies scale and rotation, then writes FBX with Roblox's documented settings
(Path Mode Copy, Embed Textures, FBX Unit Scale, no leaf bones, no baked animation unless
`--animation`). `--target web` writes a GLB. `--dry-run` prints triangles, n-gons and whether
transforms were applied, and writes nothing. *This script has not yet been run in Blender in this
repo; check its first export by hand.*

## 4. Engine limits

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

## 5. Asset records

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
- Download the GLB, run `mesh_check.py` on it, then fix or export in Blender (sections 2–4). A
  preview image is not proof of topology.
- Login is the CLI's device flow, approved by the user in a browser. Credentials never go in chat
  or in files the agent writes.
