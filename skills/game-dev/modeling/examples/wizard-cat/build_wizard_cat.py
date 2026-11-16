"""The low-poly cat in a wizard's outfit. The source of the model: run it, never edit the .blend.

  blender -b --factory-startup --python build_wizard_cat.py -- --out <folder>

Builds ../lowpoly-cat/build_cat.py's cat, then dresses it: a purple pointed hat whose brim the
ears poke through, a purple cape with a gold clasp, a gold hat tip, and a floating cyan crystal
with three sparks. Same palette texture, so still one material. An original outfit: the Wizard
Cat on the reference board (references.md) is a black cat in a blue robe and yellow hat; this one
borrows only the idea.
"""
import importlib.util
import math
import os

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("build_cat", os.path.join(HERE, "..", "lowpoly-cat", "build_cat.py"))
cat_kit = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cat_kit)  # imported, not __main__: builds nothing by itself


def cone(name, cell, parent, sides, radius1, radius2, depth, location, rotation=(0, 0, 0)):
    # sides + a capped base (and top, when radius2 > 0): a closed solid
    bpy.ops.mesh.primitive_cone_add(vertices=sides, radius1=radius1, radius2=radius2, depth=depth)
    return cat_kit.finish(name, cell, parent, location, rotation)


def dress(cat):
    # v2, after the Fable 5.2 review (5/10): centred tapered cape, clasp where it shows, a staff
    # holding the crystal, ears clear of a smaller brim, sparks joined into one part.
    objects = bpy.data.objects
    # The crown tuft would sit inside the hat: geometry nobody sees is cut, not hidden.
    objects.remove(objects["FurCrown"])
    # Ears tilt out, so both triangles stand clear of the brim.
    for name, x in (("Ear_L", 1), ("Ear_R", -1), ("EarInner_L", 1), ("EarInner_R", -1)):
        objects[name].location.x = x * 0.38
        objects[name].rotation_euler.y = math.radians(-x * 30)

    brim = cone("HatBrim", "purple", cat, 6, 0.36, 0.36, 0.05, (0, -0.4, 1.66), (-6, 0, 0))
    cat_kit.patch(brim, "gold", lambda c: abs(c.z) < 0.01)  # the rim's side faces: a gold band, 0 triangles
    cone("Hat", "purple", cat, 5, 0.26, 0, 0.8, (0.02, -0.38, 2.06), (-14, 8, 0))
    cat_kit.spike("HatTip", "gold", cat, 0.07, 0.14, (0.07, -0.29, 2.46), (-14, 8, 0))

    # The cape: a closed tent along the back, ridge up and centred, narrow at the neck and wide,
    # low at the hem past the rump; a shoulder line keeps the round body inside it (16 triangles).
    front, back = -0.3, 0.75
    verts = [
        (0, front, 1.1), (0.31, front, 0.95), (0.34, front, 0.66), (-0.31, front, 0.95), (-0.34, front, 0.66),
        (0, back, 1.0), (0.4, back, 0.88), (0.48, back, 0.38), (-0.4, back, 0.88), (-0.48, back, 0.38),
    ]
    faces = [(0, 1, 2, 4, 3), (5, 8, 9, 7, 6), (0, 5, 6, 1), (1, 6, 7, 2), (0, 3, 8, 5), (3, 4, 9, 8), (2, 7, 9, 4)]
    cat_kit.solid("Cape", "plum", cat, verts, faces)
    cat_kit.spike_toward("CapeClasp", "gold", cat, 0.07, 0.1, (0, -0.64, 0.7), (0, -1, -0.15))

    # A staff planted by the front paw, the crystal (an octahedron, 8 triangles) on top.
    cat_kit.prism_toward("Staff", "wood", cat, 0.04, 1.45, (0.58, -0.55, 0.0), (-0.06, 0, 1))
    cx, cy, cz, a, h = 0.49, -0.55, 1.6, 0.09, 0.16
    crystal = [(cx + a, cy, cz), (cx - a, cy, cz), (cx, cy + a, cz), (cx, cy - a, cz), (cx, cy, cz + h), (cx, cy, cz - h)]
    cat_kit.solid("Crystal", "cyan", cat, crystal,
                  [(4, 0, 2), (4, 2, 1), (4, 1, 3), (4, 3, 0), (5, 2, 0), (5, 1, 2), (5, 3, 1), (5, 0, 3)])
    # Two sparks by the crystal, joined into one part (one MeshPart in Roblox, not two).
    sparks = [cat_kit.spike_toward(f"Spark{k}", "cyan", cat, 0.035, 0.08, base, d)
              for k, (base, d) in enumerate((((0.68, -0.5, 1.72), (1, 0, 1)), ((0.32, -0.62, 1.78), (-1, -0.3, 1))))]
    cat_kit.join("Sparks", sparks)


def main():
    a = cat_kit.args()
    out = os.path.abspath(a.out)
    os.makedirs(out, exist_ok=True)
    cat = cat_kit.build(out)
    dress(cat)
    cat_kit.save_all(out, "wizard-cat", a.size)


main()
