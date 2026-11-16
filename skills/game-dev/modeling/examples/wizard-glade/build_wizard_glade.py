"""The glade the wizard cat lives in: a small low-poly environment built from a kit.

The source of the scene: run it, never edit the .blend by hand.

  blender -b --factory-startup --python build_wizard_glade.py -- --out <folder>
  blender -b --factory-startup --python build_wizard_glade.py -- --out <folder> --verify kit/TreePine.fbx

Writes <folder>/wizard-glade.blend and .glb (the whole scene), kit/<Piece>.fbx (each unique piece
once, at the origin, Roblox FBX settings), layout.json (where every copy goes), palette.png, the
front/side/three-quarter/top renders and wide.png (the wizard cat in the glade, for scale).
Method: ../../references/environment.md. Look: ../../references/art-theme.md.

Every piece is built once at the origin with its base on the ground, then placed from LAYOUT as a
linked copy (one mesh, many objects), so the GLB holds each mesh once and Roblox uploads it once.
Blender is Z-up; the door faces -Y like the cat. One Blender unit is one Roblox stud.
"""
import importlib.util
import json
import math
import os
import random

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "build_wizard_cat", os.path.join(HERE, "..", "wizard-cat", "build_wizard_cat.py"))
wizard = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(wizard)  # imported, not __main__: builds nothing by itself
kit = wizard.cat_kit  # the one build_cat module the outfit uses too, so the palette is shared

# Six new cells after the cat's nine, in this script's copy of the palette only. Appended, never
# reordered: every UV already points at a cell's centre. One cell of the 16 stays spare.
# The environment sits under the cat: value at most 0.80, saturation at most 0.60 (art-theme.md).
kit.PALETTE.update({
    "grass": (0.42, 0.66, 0.30, 1), "leaf": (0.30, 0.56, 0.28, 1), "pine": (0.16, 0.40, 0.30, 1),
    "sand": (0.80, 0.66, 0.44, 1), "stone": (0.62, 0.62, 0.66, 1), "slate": (0.40, 0.40, 0.47, 1),
})
kit.CELLS[:] = list(kit.PALETTE)
ACCENTS = ("purple", "gold", "cyan", "plum", "pink")  # the wizard's colours: landmark and mushrooms only

TILE = 24.0  # studs, square, centred on the origin, top at z = 0
MAX_TRIS = 3000
PATH_WIDTH = 3.0  # studs: two cats pass (1.56 wide each at the cheek fur)
PATH = [(-4.0, -12.0), (-4.5, -8.5), (-2.0, -5.0), (1.5, -2.5), (1.5, 0.5), (0.0, 3.0), (0.0, 5.6)]
SINK = 0.1  # every piece's base goes this far under its origin, so nothing floats

# (piece, x, y, turn about Z in degrees, uniform scale). Positions snap to 0.5 studs, turns to 15
# degrees. The radius is the piece's footprint, used to keep the path clear.
RADIUS = {"WizardDoor": 0, "TreeRound": 0.5, "TreePine": 0.5, "TreeYoung": 0.4, "RockLarge": 1.4,
          "RockSmall": 0.6, "Mushroom": 0.3, "GrassTuft": 0.3}
LAYOUT = [
    ("Ground", 0, 0, 0, 1), ("Path", 0, 0, 0, 1),
    ("WizardDoor", 0, 6.5, 0, 1),  # the landmark: the path ends at its step
    ("TreePine", -4.5, 9.5, 0, 1), ("TreePine", 4.5, 9.5, 45, 1.1), ("TreePine", -9.5, 3, 90, 0.9),
    ("TreeRound", 7.5, 3.5, 0, 1), ("TreeRound", -8.5, -5, 120, 1.1), ("TreeRound", 9, -7.5, 60, 0.9),
    ("TreeYoung", 4.5, -6.5, 0, 1), ("TreeYoung", -9.5, 9.5, 90, 1.1), ("TreeYoung", 9.5, 9.5, 30, 0.9),
    ("RockLarge", 3.5, 6, 0, 1), ("RockLarge", -7.5, -10, 75, 1), ("RockLarge", -3.5, 7.5, 150, 0.8),
    ("RockSmall", -1.5, -9, 0, 1), ("RockSmall", 4.5, 1.5, 105, 1.2), ("RockSmall", -5.5, 1, 45, 1),
    ("RockSmall", 6, -3.5, 210, 0.9),
    # Mushrooms in clusters by the door and under a tree, not sprinkled evenly.
    ("Mushroom", -2.5, 5.5, 0, 1.2), ("Mushroom", -3, 4.5, 60, 0.9), ("Mushroom", 2.5, 4.5, 30, 1),
    ("Mushroom", 6.5, 2, 90, 1.1), ("Mushroom", 7, 1.5, 15, 0.8), ("Mushroom", -7.5, -6.5, 45, 1),
    ("GrassTuft", -7, -1.5, 0, 1), ("GrassTuft", -1.5, -1, 45, 1.2), ("GrassTuft", 4, -9.5, 90, 1),
    ("GrassTuft", 8.5, -1, 15, 0.9), ("GrassTuft", -10, -8.5, 60, 1.1), ("GrassTuft", 2, -10.5, 30, 1),
    ("GrassTuft", -5.5, 5, 75, 1), ("GrassTuft", 10, 6, 0, 1.2), ("GrassTuft", -2, 10.5, 45, 0.9),
    ("GrassTuft", 5.5, -4.5, 120, 1),
]
CAT_AT = (1.0, 3.0, 20)  # x, y, turn: on the path in front of the door, for the scale shot


def box(name, cell, lo, hi):
    """A closed box between two corners (12 triangles)."""
    (x0, y0, z0), (x1, y1, z1) = lo, hi
    verts = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
             (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    faces = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return kit.solid(name, cell, None, verts, faces)


def octahedron(name, cell, centre, a, h):
    """A crystal, as the cat's staff carries (8 triangles)."""
    x, y, z = centre
    verts = [(x + a, y, z), (x - a, y, z), (x, y + a, z), (x, y - a, z), (x, y, z + h), (x, y, z - h)]
    return kit.solid(name, cell, None, verts,
                     [(4, 0, 2), (4, 2, 1), (4, 1, 3), (4, 3, 0), (5, 2, 0), (5, 1, 2), (5, 3, 1), (5, 0, 3)])


def piece(name, parts):
    """Join the parts into one mesh named `name`, transforms applied, triangulated, origin at 0."""
    import bmesh

    obj = kit.join(name, parts) if len(parts) > 1 else parts[0]
    obj.name = obj.data.name = name
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.triangulate(bm, faces=bm.faces)  # the .blend, the GLB and the FBX then count the same
    assert all(e.is_manifold for e in bm.edges), f"{name}: not closed"
    bm.to_mesh(obj.data)
    bm.free()
    return obj


def ground():
    return piece("Ground", [box("Ground", "grass", (-TILE / 2, -TILE / 2, -1.0), (TILE / 2, TILE / 2, 0.0))])


def path():
    """A sand ribbon lofted along PATH: four corners per section, the top a little narrower."""
    verts, loops = [], []
    for i, (x, y) in enumerate(PATH):
        a = Vector(PATH[max(i - 1, 0)])
        b = Vector(PATH[min(i + 1, len(PATH) - 1)])
        t = Vector((0, 1)) if i in (0, len(PATH) - 1) else (b - a).normalized()  # ends square to the tile and the step
        n = Vector((t.y, -t.x))
        base = len(verts)
        for half, z in ((PATH_WIDTH / 2, 0.0), (PATH_WIDTH / 2 - 0.12, 0.08)):
            verts += [(x - n.x * half, y - n.y * half, z), (x + n.x * half, y + n.y * half, z)]
        loops.append([base, base + 1, base + 3, base + 2])
    faces = [tuple(loops[0]), tuple(reversed(loops[-1]))]
    for a, b in zip(loops, loops[1:]):
        faces += [(a[k], a[(k + 1) % 4], b[(k + 1) % 4], b[k]) for k in range(4)]
    return piece("Path", [kit.solid("Path", "sand", None, verts, faces)])


def tree_round():
    """A broadleaf: tapered trunk, one faceted crown, leaf spikes breaking the outline. 7.0 studs."""
    trunk = wizard.cone("Trunk", "wood", None, 5, 0.5, 0.3, 3.0, (0, 0, 1.5 - SINK))
    crown = kit.ico("Crown", "leaf", None, 2.0, (0, 0, 4.5), scale=(1.0, 1.0, 0.9))
    kit.patch(crown, "pine", lambda c: c.z < -0.3)  # the underside in shade: colour, not a light
    tufts = [kit.spike_toward(f"Leaf{k}", "leaf", None, 0.55, 1.1, base, d) for k, (base, d) in enumerate((
        ((1.3, -0.6, 5.2), (1, -0.4, 0.9)), ((-1.2, 0.7, 5.3), (-1, 0.5, 1)), ((0.2, 1.3, 4.9), (0.2, 1, 0.6)),
        ((-0.9, -1.2, 4.6), (-0.7, -1, 0.4)), ((0, 0, 5.9), (0.15, -0.1, 1))))]
    return piece("TreeRound", [trunk, crown] + tufts)


def tree_pine():
    """A pine: three stacked six-sided cones, each rim hanging over the one below. 7.9 studs."""
    parts = [wizard.cone("Trunk", "wood", None, 5, 0.45, 0.3, 2.4, (0, 0, 1.2 - SINK))]
    for k, (radius, depth, z) in enumerate(((2.2, 3.0, 3.1), (1.7, 2.6, 4.9), (1.15, 2.4, 6.7))):
        tier = wizard.cone(f"Tier{k}", "pine", None, 6, radius, 0, depth, (0, 0, z), (0, 0, 30 * k))
        kit.patch(tier, "leaf", lambda c: c.z > -0.4 and c.y < -0.2)  # two lit facets per tier
        parts.append(tier)
    return piece("TreePine", parts)


def tree_young():
    """A sapling, the small end of the size ladder: a head taller than the cat. 3.6 studs."""
    trunk = wizard.cone("Trunk", "wood", None, 5, 0.26, 0.16, 1.5, (0, 0, 0.75 - SINK))
    crown = kit.ico("Crown", "leaf", None, 1.0, (0, 0, 2.2), scale=(1.0, 1.0, 1.1))
    kit.patch(crown, "pine", lambda c: c.z < -0.2)
    tufts = [kit.spike_toward(f"Leaf{k}", "leaf", None, 0.32, 0.65, base, d) for k, (base, d) in enumerate((
        ((0.6, -0.3, 2.6), (1, -0.5, 0.8)), ((-0.6, 0.3, 2.5), (-1, 0.5, 0.7)), ((0, 0, 3.0), (-0.1, 0.1, 1))))]
    return piece("TreeYoung", [trunk, crown] + tufts)


def rock(name, radius, scale, seed):
    """An icosahedron pushed about by a seeded jitter, flat underneath, moss painted on top (20 triangles)."""
    rng = random.Random(seed)  # the seed is the rock: change it and the piece changes
    obj = kit.ico(name, "stone", None, radius, (0, 0, 0), scale=scale)
    floor = -SINK / scale[2]
    for v in obj.data.vertices:
        v.co *= 1 + rng.uniform(-0.22, 0.22)
        v.co.z = max(v.co.z + 0.35 * radius, floor)
    obj.data.update()
    kit.patch(obj, "slate", lambda c: c.z < 0.25 * radius)
    kit.patch(obj, "grass", lambda c: c.z > 0.95 * radius)
    return piece(name, [obj])


def mushroom():
    """A purple cap on a cream stem: the hat's colour, small (16 triangles)."""
    stem = wizard.cone("Stem", "cream", None, 3, 0.14, 0.1, 0.5, (0, 0, 0.25 - SINK))
    cap = wizard.cone("Cap", "purple", None, 5, 0.38, 0, 0.36, (0, 0, 0.56))
    return piece("Mushroom", [stem, cap])


def grass_tuft():
    """Three tapered blades, the cat's fur tufts in green (12 triangles)."""
    return piece("GrassTuft", [kit.spike_toward(f"Blade{k}", "leaf", None, 0.16, depth, (x, y, -SINK), d)
                               for k, (x, y, depth, d) in enumerate((
                                   (0, 0, 0.75, (0.1, 0, 1)), (0.2, 0.1, 0.55, (0.6, 0.3, 1)), (-0.18, -0.08, 0.5, (-0.6, -0.2, 1))))])


def wizard_door():
    """The landmark: a purple door in a stone frame under a gable, a crystal on the peak.

    Sized to the cat, not to Roblox's 5-stud default avatar: the opening is 2.1 wide and 3.35 tall,
    the cat with its hat 2.54. 5.65 studs to the crystal's tip.
    """
    parts = [box("Step", "slate", (-1.7, -1.1, -SINK), (1.7, 0.5, 0.25))]
    for side, x in (("L", 1), ("R", -1)):
        parts.append(box(f"Pillar_{side}", "stone", (x * 1.05, -0.3, 0.2), (x * 1.6, 0.3, 3.65)))
    parts.append(box("Leaf", "purple", (-1.1, -0.12, 0.2), (1.1, 0.12, 3.62)))
    gable = [(-1.9, -0.4, 3.6), (1.9, -0.4, 3.6), (0, -0.4, 4.9), (-1.9, 0.4, 3.6), (1.9, 0.4, 3.6), (0, 0.4, 4.9)]
    parts.append(kit.solid("Gable", "slate", None, gable, [(0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)]))
    parts.append(octahedron("Knob", "gold", (0.7, -0.14, 1.75), 0.12, 0.12))
    parts.append(octahedron("Crystal", "cyan", (0, 0, 5.25), 0.24, 0.4))  # its lower tip sits in the peak
    return piece("WizardDoor", parts)


BUILDERS = {
    "Ground": ground, "Path": path, "WizardDoor": wizard_door,
    "TreeRound": tree_round, "TreePine": tree_pine, "TreeYoung": tree_young,
    "RockLarge": lambda: rock("RockLarge", 1.3, (1.25, 1.0, 0.8), 7),
    "RockSmall": lambda: rock("RockSmall", 0.55, (1.2, 0.9, 0.75), 3),
    "Mushroom": mushroom, "GrassTuft": grass_tuft,
}


def tris(mesh):
    return sum(len(p.vertices) - 2 for p in mesh.polygons)


def export_fbx(obj, path):
    """One piece alone, with Roblox's settings (references/rigging.md, scripts/blender_export.py)."""
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={"MESH"}, path_mode="COPY",
                             embed_textures=True, apply_scale_options="FBX_SCALE_UNITS", add_leaf_bones=False,
                             use_triangles=True, bake_anim=False)


def path_distance(x, y):
    p = Vector((x, y))
    best = 1e9
    for a, b in zip(PATH, PATH[1:]):
        a, b = Vector(a), Vector(b)
        t = max(0.0, min(1.0, (p - a).dot(b - a) / (b - a).length_squared))
        best = min(best, (p - (a + (b - a) * t)).length)
    return best


def assemble(kit_dir=None):
    """Build every piece once, then place LAYOUT's linked copies under an empty. Returns the layout rows."""
    bpy.ops.object.empty_add(location=(0, 0, 0))
    root = bpy.context.active_object
    root.name = "Glade"
    meshes = {}
    for name, builder in BUILDERS.items():
        master = builder()
        meshes[name] = master.data
        if kit_dir:
            export_fbx(master, os.path.join(kit_dir, f"{name}.fbx"))
            print(f"kit\t{name}\ttris={tris(master.data)}")
        bpy.data.objects.remove(master)  # the mesh stays; only its copies are in the scene
    rows, count = [], {}
    for name, x, y, turn, scale in LAYOUT:
        count[name] = count.get(name, 0) + 1
        single = sum(1 for row in LAYOUT if row[0] == name) == 1
        obj = bpy.data.objects.new(name if single else f"{name}_{count[name]}", meshes[name])
        bpy.context.collection.objects.link(obj)
        obj.location = (x, y, 0)
        obj.rotation_euler = (0, 0, math.radians(turn))
        obj.scale = (scale, scale, scale)
        obj.parent = root
        rows.append({"name": obj.name, "kit": name, "position": [x, y, 0], "rotation_deg": [0, 0, turn], "scale": scale})
    bpy.context.view_layer.update()
    return root, rows


def check(rows):
    """The scene's own rules: budget, inside the tile, on the ground, path clear, accents rare."""
    objs = [o for o in bpy.data.objects if o.type == "MESH"]
    total = sum(tris(o.data) for o in objs)
    assert total <= MAX_TRIS, f"{total} triangles, budget {MAX_TRIS}"
    area = {}
    for o in objs:
        corners = [o.matrix_world @ v.co for v in o.data.vertices]  # not bound_box: a turned box overstates
        lo = [min(c[i] for c in corners) for i in range(3)]
        hi = [max(c[i] for c in corners) for i in range(3)]
        assert max(abs(v) for v in lo[:2] + hi[:2]) <= TILE / 2 + 1e-4, f"{o.name}: hangs over the tile's edge"
        if o.name != "Ground":
            assert -0.2 <= lo[2] <= 0.001, f"{o.name}: base at z = {lo[2]:.2f}, floating or buried"
        uv = o.data.uv_layers.active.data
        for p in o.data.polygons:
            if (o.matrix_world.to_3x3() @ p.normal).z > -0.5:  # faces a camera can see
                u, v = uv[p.loop_indices[0]].uv
                cell = kit.CELLS[int(v * kit.GRID) * kit.GRID + int(u * kit.GRID)]
                area[cell] = area.get(cell, 0) + p.area * o.scale.x ** 2
    for row in rows:
        if row["kit"] in RADIUS and row["kit"] != "WizardDoor":
            gap = path_distance(*row["position"][:2]) - PATH_WIDTH / 2 - RADIUS[row["kit"]] * row["scale"]
            assert gap >= 0, f"{row['name']}: {-gap:.2f} studs onto the path"
    whole = sum(area.values())
    accent = sum(area.get(c, 0) for c in ACCENTS) / whole
    print("palette\t" + "\t".join(f"{c}={100 * a / whole:.1f}%" for c, a in sorted(area.items(), key=lambda kv: -kv[1])))
    print(f"accent\t{100 * accent:.1f}% of the visible surface, budget 10%")
    assert accent <= 0.10, "more than a tenth of the scene is in the wizard's colours"
    return total


def render_views(root, out, size):
    """build_cat's four views. Its orthographic camera stands 8 units from the centre, sized for a
    character, which is inside a 24-stud scene: shrink the scene for the shots, then put it back."""
    root.scale = (0.25, 0.25, 0.25)
    bpy.context.view_layer.update()
    kit.render(out, size)
    root.scale = (1, 1, 1)


def render_wide(out, size):
    """The game's view: a perspective camera at the tile's edge, the wizard cat on the path."""
    cat = kit.build(out)  # empties the scene; the cat is built in memory and never saved
    wizard.dress(cat)
    x, y, turn = CAT_AT
    cat.location = (x, y, 0.08)  # on the path's top
    cat.rotation_euler = (0, 0, math.radians(turn))
    assemble()
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    bpy.ops.object.light_add(type="SUN", rotation=(math.radians(50), 0, math.radians(30)))  # build_cat.render's sun and world
    bpy.context.active_object.data.energy = 1.6
    scene.view_settings.view_transform = "Standard"
    world = bpy.data.worlds.new("World")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.9, 0.9, 0.93, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.35
    scene.world = world
    bpy.ops.object.camera_add(location=(-3.5, -13.5, 4.2))
    cam = bpy.context.active_object
    cam.data.lens = 32
    look = Vector((0.3, 5.0, 2.3)) - cam.location
    cam.rotation_euler = look.to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam
    scene.render.resolution_x, scene.render.resolution_y = size * 2, size * 9 // 8
    scene.render.filepath = os.path.join(out, "wide.png")
    bpy.ops.render.render(write_still=True)


def verify(path):
    """Open one kit FBX in an empty Blender: one closed mesh, one material, the triangles it left with."""
    import bmesh

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=path)
    objs = [o for o in bpy.data.objects if o.type == "MESH"]
    bm = bmesh.new()
    for o in objs:
        bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)  # weld by position first, as bench_model.py does
    open_edges = sum(1 for e in bm.edges if not e.is_manifold)
    o = objs[0]
    name = os.path.splitext(os.path.basename(path))[0]
    kit.PALETTE_MAT = None  # the builder needs a material slot, not a texture
    bpy.ops.object.select_all(action="DESELECT")
    expected = tris(BUILDERS[name]().data)
    print(f"verify\t{name}\tmeshes={len(objs)}\tmaterials={len(o.data.materials)}\ttris={len(bm.faces)}"
          f"\texpected={expected}\topen_edges={open_edges}\tscale={tuple(round(s, 4) for s in o.scale)}"
          f"\tsize={tuple(round(d, 2) for d in o.dimensions)}")
    ok = len(objs) == 1 and len(o.data.materials) == 1 and len(bm.faces) == expected and open_edges == 0
    raise SystemExit(0 if ok else 1)


def main():
    import argparse
    import sys

    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--size", type=int, default=512, help="render size, px")
    ap.add_argument("--verify", help="a kit FBX to re-import and check; builds nothing")
    a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    if a.verify:
        verify(os.path.abspath(a.verify))
    out = os.path.abspath(a.out)
    kit_dir = os.path.join(out, "kit")
    os.makedirs(kit_dir, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    kit.PALETTE_MAT = kit.palette_material(out)
    root, rows = assemble(kit_dir)
    total = check(rows)
    with open(os.path.join(out, "layout.json"), "w", encoding="utf-8") as f:
        json.dump({"units": "studs", "axes": "Blender: Z up, the door faces -Y. In the GLB and in Roblox Y is up: (x, y, z) here is (x, z, -y) there.",
                   "tile": [TILE, TILE], "kit": "kit/<kit>.fbx", "pieces": rows}, f, indent=1)
        f.write("\n")
    bpy.context.preferences.filepaths.save_version = 0  # no .blend1 backups
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, "wizard-glade.blend"))
    bpy.ops.export_scene.gltf(filepath=os.path.join(out, "wizard-glade.glb"), export_format="GLB")
    render_views(root, out, a.size)
    render_wide(out, a.size)
    print(f"built\t{out}\ttris={total}\tpieces={len(rows)}\tkit={len(BUILDERS)}")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # Blender exits 0 after a script's traceback: make a failed build fail
        import sys
        import traceback

        traceback.print_exc()
        sys.exit(1)
