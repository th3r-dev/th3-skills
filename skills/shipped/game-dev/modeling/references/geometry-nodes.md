# Geometry Nodes for game assets

Read before scattering, repeating or generating variants of a model with Geometry Nodes (GN).
Each rule names its source (read 2026-11-16). **"Checked in Blender 5.3"** means it was run
headless on Blender 5.3.0 for this file. The worked case is
`examples/crystal-ground/build_crystal_ground.py`: one node group scatters crystal clusters and
rocks over a tile from a seed, and what is exported is three plain meshes, 498 triangles.

## Sources

| Source | Reached | What it gives |
|---|---|---|
| [Blender Studio: Geometry Nodes chapter](https://studio.blender.org/training/blender-fundamentals-45-lts/chapter/blender_4-5_lts_geometry-nodes/) and its Geometry Nodes Theory lesson (Beau Gerbrands, Blender Fundamentals 4.5 LTS, free) | yes, the lesson text; the videos were not watched | the vocabulary: attributes and their domains, fields, Group Input and Group Output, Join Geometry, Instance on Points, the Spreadsheet. Nothing on realizing or performance |
| [ra100/blender-claude-plugin](https://github.com/ra100/blender-claude-plugin) (MIT), `skills/blender-geometry-nodes` and its `references/python_api.md` | yes | node type strings, the interface API, the scatter pattern, the performance list. One call in it fails on 5.3: see [modifier inputs](#build-a-group-from-python) |
| [SupaSkills: Blender Geometry Nodes Expert](https://www.supaskills.ai/skills/blender-geometry-nodes-expert) | the listing only | the prompt is cut off partway and the footer says it is "protected by copyright", redistribution prohibited. No wording or structure is taken. Its topic list (scatter, seeds, instancing against realized geometry) matches the other sources |
| [composio-community/opencode-skills: blender-geometry-nodes](https://github.com/composio-community/opencode-skills/blob/master/skills/blender-geometry-nodes/SKILL.md) | yes | a workflow in seven steps. The README says MIT, but there is no LICENSE file (404) and GitHub reports no licence, so ideas only: expose parameters instead of hard-coding them, and test a setup by changing its parameters and its seed |
| Blender manual: [Instances](https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/instances.html), [Realize Instances](https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/instances/realize_instances.html), [Distribute Points on Faces](https://docs.blender.org/manual/en/latest/modeling/geometry_nodes/point/distribute_points_on_faces.html), [glTF 2.0](https://docs.blender.org/manual/en/latest/addons/scene_gltf2.html) | yes | what an instance is, what realizing costs, the scatter node's inputs, the exporter's options |

## What it is good for here

| Use | Nodes | Status |
|---|---|---|
| **Scatter** props over a surface | Distribute Points on Faces → Instance on Points, Random Value for size and turn | the worked case |
| **Variants from one seed**: the same kit, a new layout per number | one `Seed` input wired to every random source | the worked case; `--seed 3` and `--seed 11` |
| **Building from a kit**: a few hand-made closed pieces, placed by rules | Object Info → Instance on Points | the worked case: Ground, a cluster, a rock |
| **Arrays and repeats**: fence posts, steps, a ring of pillars | Mesh Line → Instance on Points; a Repeat zone for steps that build on each other | type strings checked in Blender 5.3 (`GeometryNodeMeshLine`, `GeometryNodeRepeatInput`, `GeometryNodeRepeatOutput`); not built here. *(ra100)* |

A kit piece is an ordinary mesh: closed, unwrapped, textured. GN only decides where the copies
go, so everything in [`shading.md`](shading.md) and [`texturing.md`](texturing.md) applies to the
piece once.

## Build a group from Python

Type strings, socket names and calls below are checked in Blender 5.3; the patterns start from
*ra100*'s `python_api.md`.

```python
g = bpy.data.node_groups.new("Scatter", "GeometryNodeTree")
seed = g.interface.new_socket(name="Seed", in_out="INPUT", socket_type="NodeSocketInt")
g.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
gi, go = g.nodes.new("NodeGroupInput"), g.nodes.new("NodeGroupOutput")
points = g.nodes.new("GeometryNodeDistributePointsOnFaces")
points.distribute_method = "POISSON"
points.inputs["Distance Min"].default_value = 0.5
g.links.new(gi.outputs["Seed"], points.inputs["Seed"])
...
mod = obj.modifiers.new("Scatter", "NODES")
mod.node_group = g
getattr(mod.properties.inputs, seed.identifier).value = 3     # Blender 5.3
```

- **Interface first.** `interface.new_socket` adds the group's inputs and outputs; each returns
  an item whose `identifier` is `Socket_0`, `Socket_1`, … in creation order. A group used as a
  modifier needs a geometry output. It works without a geometry input: the worked case reads
  its ground through an Object input. *(ra100; checked)*
- **Three prefixes for type strings.** `GeometryNode…` for geometry, `ShaderNode…` for the maths
  shared with materials (`ShaderNodeMath`, `ShaderNodeVectorMath`, `ShaderNodeMapRange`,
  `ShaderNodeSeparateXYZ`, `ShaderNodeCombineXYZ`), `FunctionNode…` for `Compare`,
  `RandomValue`, `BooleanMath`, `IntegerMath`, `EulerToRotation`. Group ends are
  `NodeGroupInput` and `NodeGroupOutput`. *(ra100; checked)*
- **Sockets by name, and the live one.** Compare, Random Value, Map Range and Mix keep one set
  of sockets per data type under the same names. Set `data_type` first, then take the socket
  with that name whose `enabled` is true. Math nodes name both inputs `Value`: use the index.
  *(checked)*
- **Modifier inputs changed.** *ra100* gives `modifier["Socket_2"] = 5.0`. On Blender 5.3 that
  raises `TypeError: id properties not supported for this type`; the value is at
  `modifier.properties.inputs.<identifier>.value`. *(checked)*
- **Objects come in through Object Info.** An Object input on the group feeds
  `GeometryNodeObjectInfo`; `transform_space="ORIGINAL"` gives the piece in its own space,
  `"RELATIVE"` gives the ground where it stands relative to the modifier's object. *(checked)*

### Seeds and counts

- **One seed input, wired to every random source.** Distribute Points on Faces and Random Value
  both take a `Seed`. The scatter node also writes a stable `id` per point, which Random Value
  and Instance on Points use, so a point keeps its values when others are deleted. *(Blender
  manual, Distribute Points on Faces)*
- **The same seed is the same file.** Checked in Blender 5.3: two runs of the worked case with
  seed 3 wrote byte-identical GLB files.
- **Two Random Value nodes with the same seed give the same numbers.** Checked in Blender 5.3 on
  42 points. Sizes then follow rotations, or whatever else shares the seed. Take one random
  vector and split it (x orders, y sizes, z turns), or give each node its own seed offset.
- **Poisson Disk for spacing.** Random mode has no minimum distance; Poisson Disk takes
  `Distance Min` into account. *(Blender manual)* Clusters and rocks come from
  one distribution here, so no rock sits inside a cluster.
- **Cap the count, or a seed breaks the budget.** Checked in Blender 5.3: the ring in the worked
  case held 11 to 21 points over seeds 0 to 11. The group sorts the points by a random weight
  (`GeometryNodeSortElements`), then deletes every index outside `First … First + Count - 1`.
  Crystals take indices 0–5 and rocks 6–13, so the worst case is fixed: 58 + 6 × 50 + 8 × 20 =
  518 triangles. Seed 3 gives 498 because only 13 points fit.
- **Keep bases in the ground.** The pieces' bases sit 0.06 under their origin and the instances
  turn about Z only, so no copy floats. Add tilt and the sink has to grow with it.

### The graph in the worked case

| Step | Node (type string) | What it does |
|---|---|---|
| 1 | `NodeGroupInput` | Ground, Piece (objects), Seed, First, Count, Scale Min, Scale Max |
| 2 | `GeometryNodeObjectInfo` (RELATIVE) | the ground's mesh |
| 3 | `GeometryNodeInputNormal` → `ShaderNodeSeparateXYZ` → `FunctionNodeCompare` (FLOAT, GREATER_THAN 0.9) | selects the faces that point up |
| 4 | `GeometryNodeDistributePointsOnFaces` (POISSON) | points on those faces, 0.48 apart, from the seed |
| 5 | `GeometryNodeInputPosition` → `ShaderNodeVectorMath` (LENGTH) → `ShaderNodeMath` (SUBTRACT, ABSOLUTE) → `FunctionNodeCompare` → `GeometryNodeDeleteGeometry` (POINT) | keeps a ring between radius 0.95 and 1.7: the centre stays clear for the character |
| 6 | `FunctionNodeRandomValue` (FLOAT_VECTOR) → `ShaderNodeSeparateXYZ` | one random vector per point |
| 7 | `GeometryNodeSortElements` (POINT, weight = x) | a random order |
| 8 | `GeometryNodeInputIndex` → `FunctionNodeIntegerMath` (SUBTRACT First) → two `FunctionNodeCompare` (INT) → `FunctionNodeBooleanMath` (OR) → `GeometryNodeDeleteGeometry` | the cap: keeps `Count` points starting at `First` |
| 9 | `GeometryNodeObjectInfo` (ORIGINAL) | the piece to copy |
| 10 | `ShaderNodeMapRange` (y → Scale Min … Scale Max); `ShaderNodeMath` (z × 2π) → `ShaderNodeCombineXYZ` → `FunctionNodeEulerToRotation` | size and turn per copy |
| 11 | `GeometryNodeInstanceOnPoints` | a copy on every point |
| 12 | `GeometryNodeRealizeInstances` → `NodeGroupOutput` | real geometry out |

The group is used twice: `Crystals` (Piece = the cluster, First 0, Count 6) and `Rocks`
(Piece = the rock, First 6, Count 8).

## The export rule: the engine gets a plain mesh

An instance is a reference to geometry plus a transform, kept that way so Blender does not
duplicate the data *(Blender manual, Instances)*. A game file has no such thing.

1. **Realize Instances, last in the tree.** It turns instances into real geometry *(Blender
   manual)*. Keep it at the end: every node before it works once per piece, every node after it
   works on every copy *(Blender manual, Instance Processing; ra100)*.
2. **Apply the modifier.** `bpy.ops.object.modifier_apply` leaves a mesh with no modifier.
3. **Check what is left.** Checked in Blender 5.3, on a plane with 32 instanced cones and no
   Realize Instances:
   - the evaluated mesh held 0 triangles from the instances;
   - the GLB export with default settings wrote the plane and nothing else, with no warning;
   - `modifier_apply` raised "Evaluated geometry from modifier does not contain a mesh" when the
     output was instances only. It raises the same when a scatter ends with no points.
4. **Do not lean on the exporter.** Its "Geometry Nodes Instances" option is marked experimental
   *(Blender manual, glTF)*, and `export_apply` is off by default (checked in Blender 5.3).
5. **Count triangles after realizing.** Instances multiply: one 50-triangle cluster is 300 in
   the file. Roblox's 20,000 per mesh is 400 such clusters. *(SKILL.md section 5 for the limit)*
6. **Keep each piece closed.** A copy of a closed piece is closed, and pieces that pass through
   each other are still closed one by one. Two pieces that share an edge exactly are not:
   `bench_model.py` welds by position and counts four faces on that edge. Offset them, or join,
   `GeometryNodeMergeByDistance`, and delete the faces left inside.
7. **UVs and the material come along.** Checked in Blender 5.3: the piece's UV map and material
   slot are on the realized, applied mesh. Named attributes are carried through realizing
   *(Blender manual, Realize Instances)*; anonymous ones from Capture Attribute are not
   *(ra100, not checked here)*.
8. **One object per part the game needs.** Realized copies from one modifier are one mesh, so one
   MeshPart in Roblox (expected, not checked in Studio). Separate modifiers on separate objects give named parts (`Crystals`,
   `Rocks`).

Then the usual checks: `mesh_check.py`, the bench case, and a re-import of the GLB into a fresh
Blender (no Geometry Nodes modifier, no node group, the same triangle count).

## Limits

Performance, most costly first *(ra100, except where marked)*:

1. Realize Instances early in the tree. "Performance can become much worse when the input
   contains many instances of complex geometry." *(Blender manual)*
2. Dense point distributions.
3. Mesh Boolean on anything complex. It also leaves n-gons to clean up. *(SKILL.md section 3)*
4. Nested Repeat zones, and Simulation zones carrying more geometry than changes.

Nested instances render eight levels deep at most; deeper trees must be realized. *(Blender
manual, Instances)*

Do not use GN for:

- **A mesh that will be rigged or seen up close.** It needs chosen topology and weights. Build
  it by script or by hand *(SKILL.md section 1)*. GN placed the crystals here; it did not shape
  the tile or the cluster.
- **Many copies the engine can instance itself.** A forest realized into one mesh pays for every
  triangle and cannot be culled per tree. Export the kit piece once and place it in the engine.
  Realize in Blender when the copies are few and belong to one prop, as here. (Reasoning from
  the triangle limit, not a measurement.)
- **Simulation zones.** Their state depends on the frame; an export is one frame.
- **A layout nobody capped.** A density with no count limit is a triangle budget with no limit.

Not done here: per-copy colour. All six clusters share one bake. A named attribute per instance
could drive it, but it would have to become vertex colour or more texels to leave Blender. And
with seed 11 two clusters overlap: `Distance Min` (0.48) is smaller than a cluster is wide.
