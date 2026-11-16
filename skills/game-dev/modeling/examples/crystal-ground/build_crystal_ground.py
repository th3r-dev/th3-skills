"""A low-poly ground tile with crystal clusters and rocks, for the wizard cat to stand on.

The source of the model: run it, never edit the .blend by hand.

  blender -b --factory-startup --python build_crystal_ground.py -- --out <folder> [--seed N]

The worked case for references/shading.md and references/geometry-nodes.md:

1. Three kit pieces are built as plain closed meshes: Ground, a crystal cluster, a rock.
2. Each gets a procedural material (noise, gradients, emission on the crystal tips).
3. The kit is unwrapped into one UV square and baked with Cycles to two small textures:
   base colour (256 px) and emission (128 px). The kit is baked, not the scatter, so every
   instance of a piece shares that piece's texels.
4. One Geometry Nodes group scatters the cluster and the rock over the ground's top face from
   one seeded Poisson distribution, with the count capped so no seed can pass the budget.
5. Realize Instances is in the tree and the modifier is applied: Ground, Crystals and Rocks
   are plain meshes with one material over the two baked images.

Writes crystal-ground.blend / .glb / .fbx, crystal-ground.png, crystal-ground-emit.png,
front / side / three-quarter / top .png, and three-quarter-seed-<M>.png for a second seed.
Blender is Z-up; the tile's top is z = 0 and its centre is kept clear. One unit is one stud.
"""
import argparse
import importlib.util
import math
import os
import random
import shutil
import sys
import tempfile

import bmesh
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("build_cat", os.path.join(HERE, "..", "lowpoly-cat", "build_cat.py"))
cat_kit = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cat_kit)  # for render(): the same four views as the cat

STEM = "crystal-ground"
MAX_TRIS = 600
TEX, EMIT_TEX = 256, 128  # powers of two; the object is 4 studs wide (Roblox: about 256 px at 5 studs)
CRYSTALS, ROCKS = 6, 8  # the caps: at most this many of each, whatever the seed
RADIUS = 2.0  # the tile's top
CLEAR, EDGE = 0.95, 1.7  # scatter only between these radii: the cat stands inside CLEAR
SPACING = 0.48  # Poisson minimum distance between any two pieces
GAP = 0.03  # between UV islands, as a fraction of the texture: 7 px at 256, 3 px at 128
SINK = 0.06  # how far a piece's base sits under z = 0, so nothing floats


def args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=3, help="layout seed: same seed, same layout")
    ap.add_argument("--variant", type=int, default=11, help="a second seed, rendered three-quarter only")
    ap.add_argument("--size", type=int, default=512, help="render size, px")
    return ap.parse_args(argv)


# ---------------------------------------------------------------- meshes

def ring(n, r, z, turn=0.0):
    return [(r * math.cos(turn + 2 * math.pi * k / n), r * math.sin(turn + 2 * math.pi * k / n), z) for k in range(n)]


def loft(sections):
    """Verts and faces of a closed solid through equal rings; a one-point section is an apex."""
    verts, faces, start = [], [], []
    for s in sections:
        start.append(len(verts))
        verts += s
    n = max(len(s) for s in sections)
    for a, b, sa, sb in zip(start, start[1:], sections, sections[1:]):
        for k in range(n):
            j = (k + 1) % n
            if len(sa) == 1:
                faces.append((a, b + k, b + j))
            elif len(sb) == 1:
                faces.append((a + k, a + j, b))
            else:
                faces.append((a + k, a + j, b + j, b + k))
    for a, s in ((start[0], sections[0]), (start[-1], sections[-1])):
        if len(s) > 1:
            faces.append(tuple(range(a, a + n)))  # a ring at an end is capped
    return verts, faces


def mesh_obj(name, verts, faces, parent=None):
    """A triangulated mesh object with outward normals (Roblox wants no n-gons)."""
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.parent = parent
    return obj


def shard(sides, r, h, lean, toward, at):
    """One crystal: a tapered shaft and a point, leaning `lean` degrees toward `toward`."""
    m = (Matrix.Translation(at) @ Matrix.Rotation(math.radians(toward), 4, "Z")
         @ Matrix.Rotation(math.radians(lean), 4, "X"))
    verts, faces = loft([ring(sides, 0.6 * r, -SINK), ring(sides, r, 0.66 * h), [(0, 0, h)]])
    return [tuple(m @ Vector(v)) for v in verts], faces


def merged(parts):
    verts, faces = [], []
    for v, f in parts:
        faces += [tuple(i + len(verts) for i in face) for face in f]
        verts += v
    return verts, faces


def kit(root):
    """The three pieces Geometry Nodes works with. Triangles: 58, 50, 20."""
    ground = mesh_obj("Ground", *loft([
        [(0, 0, 0)], ring(10, RADIUS, 0), ring(10, RADIUS + 0.12, -0.16), ring(10, RADIUS - 0.25, -0.5)]), root)
    cluster = mesh_obj("KitCluster", *merged([
        shard(5, 0.13, 0.78, 4, 0, (0, 0.02, 0)),
        shard(5, 0.10, 0.50, 22, 130, (0.13, -0.08, 0)),
        shard(4, 0.08, 0.34, 28, 250, (-0.14, -0.06, 0)),
    ]))
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.17)
    rock = bpy.context.active_object
    rock.name = rock.data.name = "KitRock"
    rnd = random.Random(1)  # the rock's own shape: fixed, not the layout seed
    for v in rock.data.vertices:
        v.co = Vector((v.co.x * 1.25, v.co.y * 0.95, v.co.z * 0.6)) * rnd.uniform(0.82, 1.12) + Vector((0, 0, 0.035))
    return ground, cluster, rock


# ---------------------------------------------------------------- node helpers

def pin(sockets, name):
    """The live socket with this name. Compare, Mix, Map Range and Random Value keep one per data type."""
    return next(s for s in sockets if s.name == name and s.enabled)


def add(tree, kind, inputs=None, **props):
    """A node with its properties set, then its inputs: a socket is linked, anything else is a value."""
    n = tree.nodes.new(kind)
    for k, v in props.items():
        setattr(n, k, v)
    for name, v in (inputs or {}).items():
        s = n.inputs[name] if isinstance(name, int) else pin(n.inputs, name)
        if isinstance(v, bpy.types.NodeSocket):
            tree.links.new(v, s)
        else:
            s.default_value = v
    return n


def material(name):
    m = bpy.data.materials.new(name)
    if not (m.node_tree and m.node_tree.nodes.get("Principled BSDF")):
        m.use_nodes = True  # Blender 4.x; 5.x materials always have nodes and the flag is going away
    return m, m.node_tree, m.node_tree.nodes["Principled BSDF"]


def ramp(tree, factor, stops):
    n = add(tree, "ShaderNodeValToRGB", {"Factor": factor})
    els = n.color_ramp.elements
    while len(els) < len(stops):
        els.new(0.5)
    for el, (pos, rgb) in zip(els, stops):
        el.position, el.color = pos, (*rgb, 1)
    return n.outputs["Color"]


# ---------------------------------------------------------------- procedural materials

def procedural_materials(ground, cluster, rock):
    """Node trees that exist only in Blender: no engine reads them, so they are baked below."""
    # Ground: noisy moss on top, earth darkening downward on the sides.
    m, t, bsdf = material("ProcGround")
    obj_co = add(t, "ShaderNodeTexCoord").outputs["Object"]
    noise = add(t, "ShaderNodeTexNoise", {"Vector": obj_co, "Scale": 1.7, "Detail": 3.0})
    moss = ramp(t, noise.outputs["Factor"], [(0.3, (0.10, 0.22, 0.12)), (0.55, (0.22, 0.42, 0.18)), (0.75, (0.45, 0.55, 0.25))])
    z = add(t, "ShaderNodeSeparateXYZ", {"Vector": obj_co}).outputs["Z"]
    depth = add(t, "ShaderNodeMapRange", {"Value": z, "From Min": -0.5, "From Max": 0.0})
    earth = ramp(t, depth.outputs["Result"], [(0.0, (0.10, 0.06, 0.05)), (1.0, (0.36, 0.24, 0.15))])
    up = add(t, "ShaderNodeSeparateXYZ", {"Vector": add(t, "ShaderNodeNewGeometry").outputs["True Normal"]}).outputs["Z"]
    top = add(t, "ShaderNodeMath", {0: up, 1: 0.5}, operation="GREATER_THAN")
    mix = add(t, "ShaderNodeMix", {"Factor": top.outputs["Value"], "A": earth, "B": moss}, data_type="RGBA")
    t.links.new(pin(mix.outputs, "Result"), bsdf.inputs["Base Color"])
    ground.data.materials.append(m)

    # Crystal: a height gradient, violet at the base to cyan at the tip, and the tip glows.
    m, t, bsdf = material("ProcCrystal")
    h = add(t, "ShaderNodeSeparateXYZ", {"Vector": add(t, "ShaderNodeTexCoord").outputs["Generated"]}).outputs["Z"]
    t.links.new(ramp(t, h, [(0.0, (0.16, 0.05, 0.35)), (0.5, (0.42, 0.20, 0.85)), (1.0, (0.45, 0.95, 1.0))]),
                bsdf.inputs["Base Color"])
    glow = add(t, "ShaderNodeMath", {0: h, 1: 2.0}, operation="POWER")
    bsdf.inputs["Emission Color"].default_value = (0.35, 0.92, 0.96, 1)
    t.links.new(glow.outputs["Value"], bsdf.inputs["Emission Strength"])
    cluster.data.materials.append(m)

    # Rock: blotchy blue-grey.
    m, t, bsdf = material("ProcRock")
    noise = add(t, "ShaderNodeTexNoise", {"Vector": add(t, "ShaderNodeTexCoord").outputs["Object"], "Scale": 7.0})
    t.links.new(ramp(t, noise.outputs["Factor"], [(0.35, (0.20, 0.21, 0.27)), (0.7, (0.50, 0.52, 0.60))]),
                bsdf.inputs["Base Color"])
    rock.data.materials.append(m)
    for name in ("ProcGround", "ProcCrystal", "ProcRock"):
        bpy.data.materials[name].use_fake_user = True  # kept in the .blend to look at; not exported


# ---------------------------------------------------------------- unwrap and bake

def select(objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]


def unwrap(objs, boost):
    """One UV square for the whole kit: unwrap, move texels to what is looked at, pack across objects."""
    select(objs)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(50), island_margin=0.0)
    bpy.ops.object.mode_set(mode="OBJECT")
    for o, k in zip(objs, boost):
        uv = o.data.uv_layers.active.data
        every = [i for p in o.data.polygons for i in p.loop_indices]
        under = [i for p in o.data.polygons if p.normal.z < -0.9 for i in p.loop_indices]
        # small pieces seen close get k times the texel density; faces that point down are never seen
        for loops, scale in ((every, k), (under, 0.25)):
            c = sum((uv[i].uv for i in loops), Vector((0, 0))) / len(loops)
            for i in loops:
                uv[i].uv = c + (uv[i].uv - c) * scale
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.uv.select_all(action="SELECT")
    # islands are told apart by UV connectivity, across objects; GAP is a fraction of the UV square
    bpy.ops.uv.pack_islands(margin=GAP, margin_method="FRACTION")
    bpy.ops.object.mode_set(mode="OBJECT")


def new_image(name, size, out):
    img = bpy.data.images.new(name, size, size, alpha=False)  # sRGB: both maps hold colour
    img.filepath_raw = os.path.join(out, name + ".png")
    img.file_format = "PNG"
    return img


def bake(objs, out):
    """Cycles bakes each object's material into the active Image Texture node of that material."""
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 1  # colour and emission are surface properties: no light, no noise
    colour, emit = new_image(STEM, TEX, out), new_image(STEM + "-emit", EMIT_TEX, out)
    select(objs)
    for img, kind, passes in ((colour, "DIFFUSE", {"COLOR"}), (emit, "EMIT", set())):
        for o in objs:
            nodes = o.data.materials[0].node_tree.nodes
            target = nodes.new("ShaderNodeTexImage")  # linked to nothing: it only names the target
            target.image = img
            nodes.active = target
        # One call bakes all three objects into the image. Each is baked without seeing the others'
        # islands, so a margin wider than half the gap paints over the neighbour (it put crystal
        # glow on the ground's rim at 128 px).
        bpy.ops.object.bake(type=kind, pass_filter=passes, margin=max(1, int(GAP * img.size[0] / 2)),
                            margin_type="EXTEND")
        img.save()
        img.pack()
        img.filepath_raw = "//" + os.path.basename(img.filepath_raw)  # no absolute path in the .blend
    return colour, emit


def export_material(colour, emit):
    """What the engine gets: a Principled BSDF fed by image textures and nothing else."""
    m, t, bsdf = material("CrystalGround")
    t.links.new(add(t, "ShaderNodeTexImage", image=colour).outputs["Color"], bsdf.inputs["Base Color"])
    t.links.new(add(t, "ShaderNodeTexImage", image=emit).outputs["Color"], bsdf.inputs["Emission Color"])
    bsdf.inputs["Emission Strength"].default_value = 1.0
    bsdf.inputs["Roughness"].default_value = 0.85
    m.use_backface_culling = True  # closed meshes: glTF then says single-sided
    return m


# ---------------------------------------------------------------- Geometry Nodes

def scatter_group():
    """Scatter one piece over a ground's top face. Returns the group and its input identifiers."""
    g = bpy.data.node_groups.new("Scatter", "GeometryNodeTree")
    g.use_fake_user = True  # applying the modifiers leaves it with no user; keep it in the .blend
    ident = {}
    for name, kind in (("Ground", "Object"), ("Piece", "Object"), ("Seed", "Int"), ("First", "Int"),
                       ("Count", "Int"), ("Scale Min", "Float"), ("Scale Max", "Float")):
        ident[name] = g.interface.new_socket(name=name, in_out="INPUT", socket_type="NodeSocket" + kind).identifier
    g.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    gi = add(g, "NodeGroupInput").outputs

    # Points on the faces that point up, at least SPACING apart.
    ground = add(g, "GeometryNodeObjectInfo", {"Object": gi["Ground"]}, transform_space="RELATIVE")
    up = add(g, "ShaderNodeSeparateXYZ", {"Vector": add(g, "GeometryNodeInputNormal").outputs["Normal"]})
    is_top = add(g, "FunctionNodeCompare", {"A": up.outputs["Z"], "B": 0.9}, data_type="FLOAT", operation="GREATER_THAN")
    points = add(g, "GeometryNodeDistributePointsOnFaces", {
        "Mesh": ground.outputs["Geometry"], "Selection": is_top.outputs["Result"],
        "Distance Min": SPACING, "Density Max": 40.0, "Seed": gi["Seed"]}, distribute_method="POISSON")

    # Keep the ring between CLEAR and EDGE: delete where |radius - middle| > half the width.
    radius = add(g, "ShaderNodeVectorMath", {0: add(g, "GeometryNodeInputPosition").outputs["Position"]}, operation="LENGTH")
    off = add(g, "ShaderNodeMath", {0: radius.outputs["Value"], 1: (CLEAR + EDGE) / 2}, operation="SUBTRACT")
    off = add(g, "ShaderNodeMath", {0: off.outputs["Value"]}, operation="ABSOLUTE")
    outside = add(g, "FunctionNodeCompare", {"A": off.outputs["Value"], "B": (EDGE - CLEAR) / 2},
                  data_type="FLOAT", operation="GREATER_THAN")
    in_ring = add(g, "GeometryNodeDeleteGeometry", {"Geometry": points.outputs["Points"],
                                                    "Selection": outside.outputs["Result"]}, domain="POINT")

    # One random vector per point, from the seed: x orders the points, y sizes, z turns.
    rnd = add(g, "FunctionNodeRandomValue", {"Seed": gi["Seed"]}, data_type="FLOAT_VECTOR")
    rx, ry, rz = add(g, "ShaderNodeSeparateXYZ", {"Vector": pin(rnd.outputs, "Value")}).outputs

    # Sort by the random x, so the split below never leans on the node's own point order (which
    # is not documented), then keep indices First .. First + Count - 1.
    shuffled = add(g, "GeometryNodeSortElements", {"Geometry": in_ring.outputs["Geometry"], "Sort Weight": rx}, domain="POINT")
    rank = add(g, "FunctionNodeIntegerMath", {0: add(g, "GeometryNodeInputIndex").outputs["Index"], 1: gi["First"]},
               operation="SUBTRACT")
    low = add(g, "FunctionNodeCompare", {"A": rank.outputs["Value"], "B": 0}, data_type="INT", operation="LESS_THAN")
    high = add(g, "FunctionNodeCompare", {"A": rank.outputs["Value"], "B": gi["Count"]}, data_type="INT", operation="GREATER_EQUAL")
    drop = add(g, "FunctionNodeBooleanMath", {0: low.outputs["Result"], 1: high.outputs["Result"]}, operation="OR")
    kept = add(g, "GeometryNodeDeleteGeometry", {"Geometry": shuffled.outputs["Geometry"],
                                                 "Selection": drop.outputs["Boolean"]}, domain="POINT")

    # Instance the piece: random size, random turn about Z. No tilt, so every base stays in the ground.
    piece = add(g, "GeometryNodeObjectInfo", {"Object": gi["Piece"]}, transform_space="ORIGINAL")
    size = add(g, "ShaderNodeMapRange", {"Value": ry, "To Min": gi["Scale Min"], "To Max": gi["Scale Max"]})
    turn = add(g, "ShaderNodeMath", {0: rz, 1: 2 * math.pi}, operation="MULTIPLY")
    euler = add(g, "ShaderNodeCombineXYZ", {"Z": turn.outputs["Value"]})
    spin = add(g, "FunctionNodeEulerToRotation", {"Euler": euler.outputs["Vector"]})
    inst = add(g, "GeometryNodeInstanceOnPoints", {
        "Points": kept.outputs["Geometry"], "Instance": piece.outputs["Geometry"],
        "Rotation": spin.outputs["Rotation"], "Scale": pin(size.outputs, "Result")})

    # Instances are not a mesh: realize them here, so applying the modifier leaves plain geometry.
    real = add(g, "GeometryNodeRealizeInstances", {"Geometry": inst.outputs["Instances"]})
    add(g, "NodeGroupOutput", {"Geometry": real.outputs["Geometry"]})
    return g, ident


def scatter(name, group, ident, parent, **inputs):
    obj = bpy.data.objects.new(name, bpy.data.meshes.new(name))
    bpy.context.collection.objects.link(obj)
    obj.parent = parent
    mod = obj.modifiers.new("Scatter", "NODES")
    mod.node_group = group
    for key, value in inputs.items():
        if hasattr(mod, "properties"):  # Blender 5.3: mod["Socket_2"] = v raises TypeError here
            getattr(mod.properties.inputs, ident[key]).value = value
        else:
            mod[ident[key]] = value
    select([obj])
    bpy.ops.object.modifier_apply(modifier="Scatter")  # the engine gets the mesh, not the recipe
    return obj


# ---------------------------------------------------------------- build, check, save

def build(out, seed):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.object.empty_add(location=(0, 0, 0))
    root = bpy.context.active_object
    root.name = "CrystalGround"
    ground, cluster, rock = kit(root)
    procedural_materials(ground, cluster, rock)
    unwrap([ground, cluster, rock], boost=(1, 2.5, 2))
    mat = export_material(*bake([ground, cluster, rock], out))
    for o in (ground, cluster, rock):  # from here on, the baked material: instances carry it along
        o.data.materials.clear()
        o.data.materials.append(mat)
    group, ident = scatter_group()
    common = {"Ground": ground, "Seed": seed}
    crystals = scatter("Crystals", group, ident, root, Piece=cluster, First=0, Count=CRYSTALS,
                       **{"Scale Min": 0.75, "Scale Max": 1.2}, **common)
    rocks = scatter("Rocks", group, ident, root, Piece=rock, First=CRYSTALS, Count=ROCKS,
                    **{"Scale Min": 0.6, "Scale Max": 1.3}, **common)
    for o in (cluster, rock):  # the kit has done its job: only the three parts are exported
        bpy.data.objects.remove(o)
    return [ground, crystals, rocks]


def check(parts):
    """What the docs promise, measured on the built scene. Returns the number of failures."""
    rows, total = [], 0
    for o in parts:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        tris = sum(len(f.verts) - 2 for f in bm.faces)
        open_edges = sum(1 for e in bm.edges if len(e.link_faces) != 2)
        low = min((v.co.z for v in bm.verts), default=0.0)
        bm.free()
        total += tris
        rows.append((f"{o.name}_closed", open_edges == 0 and tris > 0, f"{tris} triangles, {open_edges} open edges"))
        rows.append((f"{o.name}_plain_mesh", not o.modifiers and len(o.data.materials) == 1 and bool(o.data.uv_layers),
                     f"{len(o.modifiers)} modifiers, {len(o.data.materials)} materials, {len(o.data.uv_layers)} UV maps"))
        if o.name != "Ground":  # every base is under the top face, none deeper than the biggest scale sinks it
            rows.append((f"{o.name}_seated", -0.2 < low < 0, f"lowest point z = {low:.3f}"))
    rows.append(("budget", total <= MAX_TRIS, f"{total} triangles, budget {MAX_TRIS}"))
    for name, ok, why in rows:
        print(f"{'PASS' if ok else 'FAIL'}\t{name}\t{why}")
    return sum(1 for _, ok, _ in rows if not ok)


def save(out, size):
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, f"{STEM}.blend"))
    bpy.ops.export_scene.gltf(filepath=os.path.join(out, f"{STEM}.glb"), export_format="GLB")
    # Roblox's FBX settings, as references/rigging.md and scripts/blender_export.py.
    bpy.ops.export_scene.fbx(
        filepath=os.path.join(out, f"{STEM}.fbx"), object_types={"EMPTY", "MESH"}, path_mode="COPY",
        embed_textures=True, apply_scale_options="FBX_SCALE_UNITS", add_leaf_bones=False,
        use_triangles=True, bake_anim=False)
    cat_kit.render(out, size)


def main():
    a = args()
    out = cat_kit.inside_cwd(a.out)
    os.makedirs(out, exist_ok=True)
    failed = check(build(out, a.seed))
    save(out, a.size)
    if a.variant != a.seed:
        # ponytail: renders all four views of the variant to keep one; give render() a view list if it gets slow
        with tempfile.TemporaryDirectory() as tmp:
            failed += check(build(tmp, a.variant))
            cat_kit.render(tmp, a.size)
            shutil.copy(os.path.join(tmp, "three-quarter.png"), os.path.join(out, f"three-quarter-seed-{a.variant}.png"))
    print(f"result\t{'PASS' if not failed else f'{failed} FAILED'}\t{out}\tseed={a.seed}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    try:
        main()
    except Exception:  # Blender exits 0 after a Python traceback unless told otherwise
        import traceback

        traceback.print_exc()
        sys.exit(1)
