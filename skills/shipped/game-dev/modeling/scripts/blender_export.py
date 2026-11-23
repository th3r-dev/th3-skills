"""Export the open Blender scene for a game engine. Runs inside Blender, not plain Python:

  blender -b model.blend --python blender_export.py -- --target roblox --out build/model.fbx
  blender -b model.blend --python blender_export.py -- --target web --out build/model.glb
  add --dry-run to print the checks and the export settings without writing

roblox: applies scale and rotation on meshes, then writes FBX with the settings from
create.roblox.com/docs/art/modeling/export-requirements (read 2026-11-16): Path Mode Copy,
Embed Textures, Apply Scalings = FBX Unit Scale, no leaf bones, no baked animation unless asked.
web: glTF binary (.glb) for three.js and other browser engines.
Before writing it prints, per mesh: triangles, faces with more than 4 corners, and whether scale
and rotation were already applied. Check the export with mesh_check.py after.
Checked on Blender 5.3.0 with examples/lowpoly-cat: the FBX re-imports with every scale 1 and the
same triangle count.
"""
import argparse
import sys

import bpy  # only inside Blender


def args_after_dashdash():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser(prog="blender_export.py")
    ap.add_argument("--target", choices=("roblox", "web"), required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--animation", action="store_true", help="keep baked animation (FBX)")
    ap.add_argument("--dry-run", action="store_true")
    return ap.parse_args(argv)


def report():
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    for o in meshes:
        polys = o.data.polygons
        tris = sum(len(p.vertices) - 2 for p in polys)
        ngons = sum(1 for p in polys if len(p.vertices) > 4)
        applied = tuple(o.scale) == (1.0, 1.0, 1.0) and tuple(o.rotation_euler) == (0.0, 0.0, 0.0)
        print(f"mesh\t{o.name}\ttris={tris}\tngons={ngons}\ttransforms_applied={applied}")
    return meshes


def main():
    a = args_after_dashdash()
    meshes = report()
    if a.target == "roblox":
        settings = dict(filepath=a.out, path_mode="COPY", embed_textures=True,
                        apply_scale_options="FBX_SCALE_UNITS", add_leaf_bones=False,
                        bake_anim=a.animation)
    else:
        settings = dict(filepath=a.out, export_format="GLB")
    print(f"export\t{a.target}\t{settings}")
    if a.dry_run:
        return
    if a.target == "roblox" and meshes:
        bpy.ops.object.select_all(action="DESELECT")
        for o in meshes:
            o.select_set(True)
        bpy.context.view_layer.objects.active = meshes[0]
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        bpy.ops.export_scene.fbx(**settings)
    else:
        bpy.ops.export_scene.gltf(**settings)
    print(f"wrote\t{a.out}")


main()
