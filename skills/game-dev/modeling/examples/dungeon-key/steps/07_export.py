# Step 7: export for Roblox with blender-skills' presets: roblox (FBX: FBX unit scale, modifiers applied,
# no leaf bones, embedded textures) and roblox_gltf (GLB, no scale tricks). Roblox imports either;
# mesh_check.py reads the GLB outside Blender.
import importlib
import os
import sys

import bpy

# where blender-skills is installed (its installer links ~/.claude/skills and ~/.agents/skills) and
# where to write; both overridable from the environment
BLENDER_SKILLS = os.environ.get("BLENDER_SKILLS", os.path.expanduser("~/.claude/skills"))
OUT_DIR = os.environ.get("OUT_DIR") or bpy.path.dirname(bpy.data.filepath)
assert OUT_DIR, "save the .blend first, or set OUT_DIR: an unsaved session has no folder to write to"
sys.path.insert(0, BLENDER_SKILLS + "/blender-export-pipelines/scripts")
import export_asset
importlib.reload(export_asset)
fbx = export_asset.run(preset="roblox", objects=["DungeonKey"], out=OUT_DIR + "/dungeon-key.fbx")
# use_active_scene: the glTF exporter walks every scene, and the startup scene's selected Cube leaked into
# the GLB (mesh_check.py counted 2 meshes); the FBX preset doesn't need it
glb = export_asset.run(preset="roblox_gltf", objects=["DungeonKey"], out=OUT_DIR + "/dungeon-key.glb",
                       set=["use_active_scene=True"])
result = {"fbx": fbx["files"], "glb": glb["files"], "warnings": fbx["warnings"] + glb["warnings"]}
