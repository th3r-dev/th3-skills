"""A furry cat character at the lowest polygon count that still reads as a cat.

The source of the model: run it, never edit the .blend by hand.

  blender -b --factory-startup --python build_cat.py -- --out <folder>

Writes <folder>/cat.blend, cat.glb, palette.png (16 px, one material), and renders front/side/three-quarter/top .png.
Built after a reference board (references.md). "Furry" at this budget means faceted tufts (three-sided spikes) at the cheeks, chest, crown and
tail tip, not hair particles: hair cannot be exported to a game mesh.
Every part is its own named, closed object under an empty "Cat", so a rig or Roblox's importer
can move parts separately (Roblox makes one MeshPart each).
Blender is Z-up; the cat faces -Y. One Blender unit is one Roblox stud here.
"""
import argparse
import math
import os
import sys

import bpy

FUR = (0.95, 0.5, 0.15, 1)  # orange
CREAM = (0.98, 0.88, 0.70, 1)
PINK = (0.95, 0.55, 0.62, 1)
DARK = (0.08, 0.07, 0.07, 1)
# One material, one 16 px palette texture (power of two), every face UV'd to the middle of its
# colour's cell: one draw call per part, and new colours are new cells, not new materials.
PALETTE = {
    "fur": FUR, "cream": CREAM, "pink": PINK, "dark": DARK,
    "purple": (0.45, 0.22, 0.68, 1), "gold": (0.96, 0.78, 0.25, 1), "cyan": (0.35, 0.92, 0.96, 1),
    "plum": (0.28, 0.12, 0.42, 1), "wood": (0.45, 0.28, 0.14, 1),
}  # 4 x 4 cells, 4 px each; outfits use the spare colours
CELLS = list(PALETTE)
GRID = 4
PALETTE_SIZE = 16
PALETTE_MAT = None


def args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--size", type=int, default=512, help="render size, px")
    return ap.parse_args(argv)


def palette_material(out):
    cell = PALETTE_SIZE // GRID
    img = bpy.data.images.new("Palette", PALETTE_SIZE, PALETTE_SIZE)
    colours = list(PALETTE.values())
    pixels = []
    for y in range(PALETTE_SIZE):
        for x in range(PALETTE_SIZE):
            k = (y // cell) * GRID + x // cell
            pixels.extend(colours[k] if k < len(colours) else (1, 0, 1, 1))  # magenta = unused
    img.pixels = pixels
    img.filepath_raw = os.path.join(out, "palette.png")
    img.file_format = "PNG"
    img.save()
    img.pack()  # the .blend carries it too
    m = bpy.data.materials.new("Palette")
    m.use_nodes = True
    nodes = m.node_tree.nodes
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Closest"  # flat cells, no bleeding between colours
    bsdf = nodes["Principled BSDF"]
    m.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.9
    return m


def paint(obj, cell, inside=None):
    """UV the faces (all, or those whose local centre passes `inside`) to a palette cell."""
    i = CELLS.index(cell)
    u = ((i % GRID + 0.5) / GRID, (i // GRID + 0.5) / GRID)
    mesh = obj.data
    if not mesh.uv_layers:
        mesh.uv_layers.new(name="UVMap")
    uv = mesh.uv_layers.active.data
    for poly in mesh.polygons:
        if inside is None or inside(poly.center):
            for li in poly.loop_indices:
                uv[li].uv = u


def finish(name, mat, parent, location=None, rotation=None, scale=None):
    o = bpy.context.active_object
    o.name = o.data.name = name
    if location:
        o.location = location
    if rotation:
        o.rotation_euler = [math.radians(a) for a in rotation]
    if scale:
        o.scale = scale
    o.data.materials.append(PALETTE_MAT)
    paint(o, mat)
    o.parent = parent
    return o


def ico(name, mat, parent, radius, location, scale=None, mirror=False):
    # subdivisions=1: an icosahedron, 20 triangles
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=radius)
    if mirror:
        # Turn it about Z so a vertex of the upper ring points straight forward (-Y): the
        # icosahedron is then mirror-symmetric across x = 0, and so is any patch painted on it.
        import math as _m
        from mathutils import Matrix

        mesh = bpy.context.active_object.data
        ring = [v.co for v in mesh.vertices if 0.1 * radius < v.co.z < 0.9 * radius]
        phi = _m.atan2(ring[0].y, ring[0].x)
        mesh.transform(Matrix.Rotation(-_m.pi / 2 - phi, 4, "Z"))
    return finish(name, mat, parent, location, scale=scale)


# v3 body: one closed mesh lofted through hexagonal cross-sections (y, half-width, half-height,
# centre z), with the legs extruded from its belly, so body and legs are one surface (8 + 8 + ...).
BODY_RINGS = [(-0.34, 0.24, 0.26, 0.68), (-0.05, 0.34, 0.33, 0.63), (0.28, 0.34, 0.3, 0.6),
              (0.56, 0.26, 0.25, 0.62), (0.72, 0.13, 0.14, 0.68)]  # the last ring rounds the rump
# (segment between rings, bottom face: 2 = +x side, 3 = -x side, leg name)
BODY_LEGS = [(0, 2, "Leg_FL"), (0, 3, "Leg_FR"), (2, 2, "Leg_BL"), (2, 3, "Leg_BR")]


def ring_points(w, h, zc):
    """A hexagon, top first, then clockwise seen from the front: flat bottom with a centre vertex."""
    return [(0, zc + h), (w, zc + 0.3 * h), (0.85 * w, zc - h), (0, zc - h), (-0.85 * w, zc - h), (-w, zc + 0.3 * h)]


def body_with_legs(name, cell, parent, belly_cell):
    import bmesh
    from mathutils import Vector

    bm = bmesh.new()
    rings = [[bm.verts.new((x, y, z)) for x, z in ring_points(w, h, zc)] for y, w, h, zc in BODY_RINGS]
    sides = {}
    for i in range(len(rings) - 1):
        a, b = rings[i], rings[i + 1]
        for k in range(6):
            sides[(i, k)] = bm.faces.new((a[k], a[(k + 1) % 6], b[(k + 1) % 6], b[k]))
    bm.faces.new(rings[0])
    bm.faces.new(rings[-1])
    legs = {}
    for seg, k, leg in BODY_LEGS:
        face = sides[(seg, k)]
        out = bmesh.ops.extrude_face_region(bm, geom=[face])
        # bmesh keeps the source face (the editor's extrude removes it): left in, it sits inside the
        # leg's top and every edge round it is shared by three faces, so the body is not closed.
        bmesh.ops.delete(bm, geom=[face], context="FACES_ONLY")
        new = [g for g in out["geom"] if isinstance(g, bmesh.types.BMVert)]
        c = sum((v.co for v in new), Vector()) / len(new)
        for v in new:  # down to the ground, tapering toward the paw
            v.co.x = c.x + (v.co.x - c.x) * 0.6
            v.co.y = c.y + (v.co.y - c.y) * 0.6
            v.co.z = 0.0
        legs[leg] = new
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.verts.index_update()
    bm.faces.index_update()
    leg_verts = {v for vs in legs.values() for v in vs}
    leg_faces = {f.index for f in bm.faces if any(v in leg_verts for v in f.verts)}
    groups = {leg: [v.index for v in vs] for leg, vs in legs.items()}
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    finish(name, cell, parent)
    # Cream on the body's underside between the legs and on the chest face; every leg face stays fur.
    i = CELLS.index(belly_cell)
    u = ((i % GRID + 0.5) / GRID, (i // GRID + 0.5) / GRID)
    uv = mesh.uv_layers.active.data
    for poly in mesh.polygons:
        c = poly.center
        if poly.index not in leg_faces and (poly.normal.z < -0.7 or (c.y < -0.33 and c.z > 0.45)):
            for li in poly.loop_indices:
                uv[li].uv = u
    for leg, idx in groups.items():  # vertex groups: the rig weights each leg to its bones
        obj.vertex_groups.new(name=leg).add(idx, 1.0, "REPLACE")
    return obj


def prism(name, mat, parent, radius, depth, location, rotation=None, cap=True):
    # 3 sides: 3 quads + 2 caps = 8 triangles
    bpy.ops.mesh.primitive_cylinder_add(vertices=3, radius=radius, depth=depth,
                                        end_fill_type="NGON" if cap else "NOTHING")
    return finish(name, mat, parent, location, rotation)


def spike(name, mat, parent, radius, depth, location, rotation):
    # a 3-sided cone: a tetrahedron, 4 triangles
    bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=radius, radius2=0, depth=depth)
    return finish(name, mat, parent, location, rotation)


def _aim(obj, base, direction, depth):
    """Point a primitive's +Z axis along `direction`, its base at `base`."""
    from mathutils import Vector

    d = Vector(direction).normalized()
    obj.location = Vector(base) + d * depth / 2
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = d.to_track_quat("Z", "Y")
    return obj


def spike_toward(name, cell, parent, radius, depth, base, direction):
    """A tetrahedron from `base` along `direction` (4 triangles): tufts, fans, ruffs."""
    bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=radius, radius2=0, depth=depth)
    return _aim(finish(name, cell, parent), base, direction, depth)


def prism_toward(name, cell, parent, radius, depth, base, direction):
    """A 3-sided prism from `base` along `direction` (8 triangles): tail segments, a staff."""
    bpy.ops.mesh.primitive_cylinder_add(vertices=3, radius=radius, depth=depth, end_fill_type="NGON")
    return _aim(finish(name, cell, parent), base, direction, depth)


def solid(name, cell, parent, verts, faces):
    """A closed mesh from explicit vertices and faces, for shapes no primitive gives."""
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    import bmesh

    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)  # outward, whatever order the faces came in
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    return finish(name, cell, parent)


def on_surface(target, x, z):
    """Where a ray from the front at (x, z) meets `target`, and the surface normal there."""
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree

    bpy.context.view_layer.update()
    tree = BVHTree.FromObject(target, bpy.context.evaluated_depsgraph_get())
    inv = target.matrix_world.inverted()
    origin = inv @ Vector((x, -5.0, z))
    direction = (inv.to_3x3() @ Vector((0, 1, 0))).normalized()
    hit, normal, _, _ = tree.ray_cast(origin, direction)
    world = target.matrix_world
    return world @ hit, (world.to_3x3().inverted().transposed() @ normal).normalized()


def seated(name, cell, parent, target, radius, depth, x, z, sink=0.012):
    """A tetrahedron standing on `target`'s surface at (x, z) as seen from the front: flush, never floating."""
    point, normal = on_surface(target, x, z)
    return spike_toward(name, cell, parent, radius, depth, tuple(point - normal * sink), tuple(normal))


def join(name, objs):
    """Join parts that never move apart into one: one Roblox MeshPart instead of several."""
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    joined = bpy.context.active_object
    joined.name = joined.data.name = name
    return joined


def patch(obj, cell, inside):
    """A colour patch on the faces whose local centre passes `inside`: 0 extra triangles."""
    paint(obj, cell, inside)


def build(out):
    # v2, after the reference board (references.md): character proportions (head as big as the
    # body, big ears, short legs), colour patches per facet instead of extra shapes, fur as tufts.
    bpy.ops.wm.read_factory_settings(use_empty=True)
    global PALETTE_MAT
    PALETTE_MAT = palette_material(out)
    fur, cream, pink, dark = CELLS[:4]
    bpy.ops.object.empty_add(location=(0, 0, 0))
    cat = bpy.context.active_object
    cat.name = "Cat"

    body_with_legs("Body", fur, cat, cream)
    head = ico("Head", fur, cat, 0.55, (0, -0.4, 1.18), scale=(1.15, 0.95, 0.92), mirror=True)
    patch(head, cream, lambda c: c.y < -0.3 and c.z < -0.05)  # muzzle and chin
    # Face features sit flush: their bases just under the head's surface (review: they floated).
    seated("Nose", pink, cat, head, 0.07, 0.06, 0, 1.12)
    for side, x in (("L", 1), ("R", -1)):
        seated(f"Eye_{side}", dark, cat, head, 0.11, 0.035, x * 0.2, 1.3)
        spike(f"Ear_{side}", fur, cat, 0.22, 0.45, (x * 0.3, -0.35, 1.66), (0, -x * 18, 0))
        spike(f"EarInner_{side}", pink, cat, 0.12, 0.28, (x * 0.3, -0.43, 1.62), (0, -x * 18, 0))
        # Cheek fur: two spikes per side, fanned down and back (review: one flat spike read as an arm).
        join(f"FurCheek_{side}", [
            spike_toward(f"FurCheek_{side}1", fur, cat, 0.09, 0.26, (x * 0.5, -0.6, 1.08), (x, 0.5, -0.45)),
            spike_toward(f"FurCheek_{side}2", fur, cat, 0.08, 0.22, (x * 0.48, -0.55, 0.95), (x, 0.6, -0.9)),
        ])
    # Chest ruff: three cream spikes under the chin, pointing down and forward.
    join("FurChest", [spike_toward(f"FurChest{k + 1}", cream, cat, 0.1, 0.26, (dx * 0.15, -0.5, 0.72), (dx, -0.7, -1))
                      for k, dx in enumerate((-0.6, 0, 0.6))])
    spike("FurCrown", fur, cat, 0.09, 0.24, (0, -0.4, 1.72), (0, 0, 0))
    # Tail: two segments curling up and forward, a cat's question mark, not a fox's brush.
    prism_toward("Tail", fur, cat, 0.085, 0.5, (0, 0.62, 0.78), (0, 1, 0.9))
    prism_toward("TailUpper", fur, cat, 0.075, 0.42, (0, 0.95, 1.1), (0, -0.25, 1))
    spike_toward("FurTailTip", fur, cat, 0.1, 0.24, (0, 0.86, 1.48), (0, -0.4, 1))
    return cat


def render(out, size):
    scene = bpy.context.scene
    try:
        scene.render.engine = "BLENDER_EEVEE"  # Blender 5.x
    except TypeError:
        scene.render.engine = "BLENDER_EEVEE_NEXT"  # Blender 4.2-4.x
    bpy.ops.object.light_add(type="SUN", rotation=(math.radians(50), 0, math.radians(30)))
    bpy.context.active_object.data.energy = 1.6
    scene.render.resolution_x = scene.render.resolution_y = size
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "Standard"  # flat colours as picked, no filmic wash
    world = bpy.data.worlds.new("World")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.9, 0.9, 0.93, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.35
    scene.world = world
    # Frame the whole model, whatever an outfit adds: the centre and size of every mesh's corners.
    from mathutils import Vector

    corners = [o.matrix_world @ Vector(c) for o in scene.objects if o.type == "MESH" for c in o.bound_box]
    lo = Vector(tuple(min(c[i] for c in corners) for i in range(3)))
    hi = Vector(tuple(max(c[i] for c in corners) for i in range(3)))
    target = (lo + hi) / 2
    bpy.ops.object.camera_add()
    cam = bpy.context.active_object
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = max(hi - lo) * 1.3
    scene.camera = cam
    tx, ty, tz = target
    views = {
        "front": (tx, ty - 8, tz),
        "side": (tx + 8, ty, tz),
        "three-quarter": (tx + 5.5, ty - 5.5, tz + 2.6),
        "top": (tx, ty, tz + 9),
    }
    for name, (x, y, z) in views.items():
        cam.location = (x, y, z)
        dx, dy, dz = target[0] - x, target[1] - y, target[2] - z
        cam.rotation_euler = (math.atan2(math.hypot(dx, dy), -dz), 0, math.atan2(dy, dx) - math.pi / 2)
        scene.render.filepath = os.path.join(out, f"{name}.png")
        bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam)


def save_all(out, stem, size):
    """Save the .blend and the GLB, render the four views, print the triangle count."""
    bpy.context.preferences.filepaths.save_version = 0  # no cat.blend1 backups
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, f"{stem}.blend"))
    bpy.ops.export_scene.gltf(filepath=os.path.join(out, f"{stem}.glb"), export_format="GLB")
    render(out, size)
    tris = sum(len(p.vertices) - 2 for o in bpy.data.objects if o.type == "MESH" for p in o.data.polygons)
    print(f"built\t{out}\ttris={tris}")


def main():
    a = args()
    out = os.path.abspath(a.out)
    os.makedirs(out, exist_ok=True)
    build(out)
    save_all(out, "cat", a.size)


if __name__ == "__main__":  # blender --python runs it as __main__; an outfit script imports it
    main()
