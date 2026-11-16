"""A furry cat character at the lowest polygon count that still reads as a cat.

The source of the model: run it, never edit the .blend by hand.

  blender -b --factory-startup --python build_cat.py -- --out <folder>

Writes <folder>/cat.blend, cat.glb, and renders front/side/three-quarter/top .png.
"Furry" at this budget means faceted tufts (three-sided spikes) at the cheeks, chest, crown and
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

FUR = (0.93, 0.55, 0.22, 1)  # orange tabby
CREAM = (0.98, 0.88, 0.70, 1)
PINK = (0.95, 0.55, 0.62, 1)
DARK = (0.08, 0.07, 0.07, 1)


def args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--size", type=int, default=512, help="render size, px")
    return ap.parse_args(argv)


def material(name, color):
    m = bpy.data.materials.new(name)
    m.diffuse_color = color  # Workbench and the viewport read this
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color  # glTF exports this
        bsdf.inputs["Roughness"].default_value = 0.9
    return m


def finish(name, mat, parent, location=None, rotation=None, scale=None):
    o = bpy.context.active_object
    o.name = o.data.name = name
    if location:
        o.location = location
    if rotation:
        o.rotation_euler = [math.radians(a) for a in rotation]
    if scale:
        o.scale = scale
    o.data.materials.append(mat)
    o.parent = parent
    return o


def ico(name, mat, parent, radius, location, scale=None):
    # subdivisions=1: an icosahedron, 20 triangles
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=radius)
    return finish(name, mat, parent, location, scale=scale)


def prism(name, mat, parent, radius, depth, location, rotation=None, cap=True):
    # 3 sides: 3 quads + 2 caps = 8 triangles
    bpy.ops.mesh.primitive_cylinder_add(vertices=3, radius=radius, depth=depth,
                                        end_fill_type="NGON" if cap else "NOTHING")
    return finish(name, mat, parent, location, rotation)


def spike(name, mat, parent, radius, depth, location, rotation):
    # a 3-sided cone: a tetrahedron, 4 triangles
    bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=radius, radius2=0, depth=depth)
    return finish(name, mat, parent, location, rotation)


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    fur, cream, pink, dark = (material(n, c) for n, c in
                              (("Fur", FUR), ("Cream", CREAM), ("Pink", PINK), ("Dark", DARK)))
    bpy.ops.object.empty_add(location=(0, 0, 0))
    cat = bpy.context.active_object
    cat.name = "Cat"

    ico("Body", fur, cat, 0.5, (0, 0.05, 0.75), scale=(0.95, 1.7, 0.9))
    ico("Head", fur, cat, 0.42, (0, -0.85, 1.25))
    ico("Muzzle", cream, cat, 0.17, (0, -1.18, 1.14), scale=(1.3, 0.8, 0.8))
    spike("Nose", pink, cat, 0.06, 0.08, (0, -1.32, 1.22), (90, 0, 180))
    for side, x in (("L", 0.15), ("R", -0.15)):
        spike(f"Eye_{side}", dark, cat, 0.06, 0.05, (x, -1.2, 1.36), (90, 0, 180))
        spike(f"Ear_{side}", fur, cat, 0.15, 0.32, (x * 1.5, -0.82, 1.68), (0, -x * 80, 0))
        spike(f"EarInner_{side}", pink, cat, 0.08, 0.2, (x * 1.5, -0.88, 1.66), (0, -x * 80, 0))
        spike(f"FurCheek_{side}", fur, cat, 0.1, 0.24, (x * 2.4, -0.95, 1.12), (0, x * 500, 0))
        for front, y in (("F", -0.45), ("B", 0.55)):
            prism(f"Leg_{front}{side}", fur, cat, 0.12, 0.6, (x * 1.6, y, 0.3))
    spike("FurChest", cream, cat, 0.13, 0.3, (0, -0.72, 0.86), (150, 0, 0))
    spike("FurCrown", fur, cat, 0.08, 0.22, (0, -0.8, 1.68), (0, 0, 0))
    prism("Tail", fur, cat, 0.08, 0.8, (0, 0.95, 1.05), (-35, 0, 0))
    spike("FurTailTip", cream, cat, 0.12, 0.28, (0, 1.2, 1.45), (-35, 0, 0))
    return cat


def render(out, size):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_object_outline = True
    scene.render.resolution_x = scene.render.resolution_y = size
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "Standard"  # flat colours as picked, no filmic wash
    world = bpy.data.worlds.new("World")
    world.color = (0.92, 0.92, 0.95)
    scene.world = world
    bpy.ops.object.camera_add()
    cam = bpy.context.active_object
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = 3.2
    scene.camera = cam
    target = (0, -0.1, 0.9)
    views = {
        "front": (0, -8, 0.9),
        "side": (8, -0.1, 0.9),
        "three-quarter": (5.5, -5.5, 3.5),
        "top": (0, -0.1, 9),
    }
    for name, (x, y, z) in views.items():
        cam.location = (x, y, z)
        dx, dy, dz = target[0] - x, target[1] - y, target[2] - z
        cam.rotation_euler = (math.atan2(math.hypot(dx, dy), -dz), 0, math.atan2(dy, dx) - math.pi / 2)
        scene.render.filepath = os.path.join(out, f"{name}.png")
        bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam)


def main():
    a = args()
    out = os.path.abspath(a.out)
    os.makedirs(out, exist_ok=True)
    build()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, "cat.blend"))
    bpy.ops.export_scene.gltf(filepath=os.path.join(out, "cat.glb"), export_format="GLB")
    render(out, a.size)
    tris = sum(len(p.vertices) - 2 for o in bpy.data.objects if o.type == "MESH" for p in o.data.polygons)
    print(f"built\t{out}\ttris={tris}")


main()
