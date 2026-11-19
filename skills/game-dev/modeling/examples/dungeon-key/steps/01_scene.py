# Step 1: a scene of its own, so nothing the person had open is touched (blender-core: live sessions
# are the user's work). Metric, 1 unit = 1 m; Roblox reads 1 stud as 0.28 m.
import bpy

scene = bpy.data.scenes.get("DungeonKey") or bpy.data.scenes.new("DungeonKey")
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 1.0
bpy.context.window.scene = scene
col = bpy.data.collections.get("DungeonKey") or bpy.data.collections.new("DungeonKey")
if col.name not in scene.collection.children:
    scene.collection.children.link(col)
result = {"scene": scene.name, "collection": col.name, "objects": len(scene.objects)}
