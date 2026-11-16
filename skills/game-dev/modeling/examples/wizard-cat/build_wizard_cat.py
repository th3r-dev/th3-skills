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
    # The crown tuft would sit inside the hat: geometry nobody sees is cut, not hidden.
    bpy.data.objects.remove(bpy.data.objects["FurCrown"])
    # Brim low on the head, so the ears' upper halves stand above it.
    cone("HatBrim", "purple", cat, 6, 0.5, 0.5, 0.05, (0, -0.4, 1.6), (-6, 0, 0))
    cone("Hat", "purple", cat, 5, 0.3, 0, 0.8, (0.02, -0.36, 1.98), (-14, 8, 0))
    cat_kit.spike("HatTip", "gold", cat, 0.07, 0.14, (0.07, -0.27, 2.38), (-14, 8, 0))
    # The cape: a three-sided prism along the back, ridge up, wider than the body, so its sides
    # hang over the flanks like cloth (8 triangles).
    cape = cat_kit.prism("Cape", "purple", cat, 0.46, 0.72, (0, 0.18, 0.74), (90, -90, 0))
    cape.scale = (1, 1.35, 1)  # local Y is the world width here: wide enough that no body shows through
    cat_kit.spike("CapeClasp", "gold", cat, 0.08, 0.1, (0, -0.2, 1.02), (90, 0, 180))
    cat_kit.ico("Crystal", "cyan", cat, 0.12, (0.62, -0.78, 0.82), scale=(0.8, 0.8, 1.3))
    for k, (x, y, z) in enumerate(((0.82, -0.7, 1.05), (0.45, -0.95, 1.08), (0.78, -0.95, 0.58))):
        cat_kit.spike(f"Spark{k + 1}", "cyan", cat, 0.04, 0.08, (x, y, z), (k * 40, k * 70, 0))


def main():
    a = cat_kit.args()
    out = os.path.abspath(a.out)
    os.makedirs(out, exist_ok=True)
    cat = cat_kit.build(out)
    dress(cat)
    cat_kit.save_all(out, "wizard-cat", a.size)


main()
