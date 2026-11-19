# Step 8: save the session's work as the source file. The .blend, not a rebuild script, is what the
# next person opens; the steps/ folder records how it got there.
import os

import bpy

OUT_DIR = os.environ.get("OUT_DIR") or bpy.path.dirname(bpy.data.filepath)
assert OUT_DIR, "save the .blend first, or set OUT_DIR: an unsaved session has no folder to write to"

bpy.ops.wm.save_as_mainfile(filepath=OUT_DIR + "/dungeon-key.blend", copy=True)
result = {"saved": OUT_DIR + "/dungeon-key.blend"}
