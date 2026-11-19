# Step 3: one watertight mesh. Roblox wants a closed MeshPart; five overlapping shells would import as
# one mesh with hidden inner faces. Boolean union (exact) on a copy of the bow, applied through the
# evaluated mesh (data API), then the parts this session made are removed.
import bpy

col = bpy.data.collections["DungeonKey"]
parts = ["KeyCollar", "KeyShaft", "KeyTooth1", "KeyTooth2"]
base = bpy.data.objects["KeyBow"]
key = bpy.data.objects.new("DungeonKey", base.data.copy())
key.matrix_world = base.matrix_world.copy()
col.objects.link(key)
for name in parts:
    m = key.modifiers.new("Union_" + name, "BOOLEAN")
    m.operation, m.solver, m.object = "UNION", "EXACT", bpy.data.objects[name]
dg = bpy.context.evaluated_depsgraph_get()
ev = key.evaluated_get(dg)
me = bpy.data.meshes.new_from_object(ev)
me.name = "DungeonKey"
for m in [m.name for m in key.modifiers]:
    key.modifiers.remove(key.modifiers[m])
key.data = me
# the parts were made in step 2 by this session; collect names first, then remove (blender-core: freed data)
for name in ["KeyBow"] + parts:
    ob = bpy.data.objects[name]
    mesh = ob.data
    bpy.data.objects.remove(ob)
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)
# origin at the bow's centre, so the key turns around the grip
key.location = (0, 0, 0)
bpy.context.view_layer.update()
result = {"object": key.name, "verts": len(me.vertices), "faces": len(me.polygons),
          "tris": sum(len(p.vertices) - 2 for p in me.polygons), "dims": [round(v, 3) for v in key.dimensions]}
