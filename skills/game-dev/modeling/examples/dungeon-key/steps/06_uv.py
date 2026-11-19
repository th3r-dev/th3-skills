# Step 6: one UV map inside 0-1 (Roblox: a single UV set), smart unwrap at a 1024 px texel budget
# (blender-skills retopology-uv, pinned at 9e7e04a).
import importlib
import os
import sys

import bpy

BLENDER_SKILLS = os.environ.get("BLENDER_SKILLS", os.path.expanduser("~/.claude/skills"))
sys.path.insert(0, BLENDER_SKILLS + "/blender-retopology-uv/scripts")
import uv_pack
importlib.reload(uv_pack)
result = uv_pack.run(objects=["DungeonKey"], method="smart", res=1024, margin_px=8)
