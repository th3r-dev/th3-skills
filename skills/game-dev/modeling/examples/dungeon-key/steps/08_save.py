# Step 8: save the session's work as the source file. The .blend, not a rebuild script, is what the
# next person opens; the steps/ folder records how it got there.
import bpy

bpy.ops.wm.save_as_mainfile(filepath=OUT_DIR + "/dungeon-key.blend", copy=True)
result = {"saved": OUT_DIR + "/dungeon-key.blend"}
