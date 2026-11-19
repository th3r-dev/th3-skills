# Step 4: finish as a live modifier stack (kept, so the person can still tune it in the Modifier panel;
# the FBX export applies it), one gold material, flat-ish shading that reads at Roblox distances.
import bpy

key = bpy.data.objects["DungeonKey"]
if "Chamfer" not in key.modifiers:
    bev = key.modifiers.new("Chamfer", "BEVEL")
    bev.width, bev.segments, bev.limit_method, bev.angle_limit = 0.006, 1, "ANGLE", 0.6
    bev.harden_normals = False
if "WeightedNormals" not in key.modifiers:
    wn = key.modifiers.new("WeightedNormals", "WEIGHTED_NORMAL")
    wn.keep_sharp = True
mat = bpy.data.materials.get("KeyGold") or bpy.data.materials.new("KeyGold")
bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")   # by type, not localized name
bsdf.inputs["Base Color"].default_value = (1.0, 0.55, 0.08, 1.0)   # linear: reads as #FFC23D-ish gold
bsdf.inputs["Metallic"].default_value = 1.0
bsdf.inputs["Roughness"].default_value = 0.32
mat.diffuse_color = (1.0, 0.62, 0.12, 1.0)                          # what Solid view and Roblox's part colour show
key.data.materials.clear()
key.data.materials.append(mat)
for p in key.data.polygons:
    p.use_smooth = True
dg = bpy.context.evaluated_depsgraph_get()
ev = key.evaluated_get(dg).to_mesh()
tris = sum(len(p.vertices) - 2 for p in ev.polygons)
key.evaluated_get(dg).to_mesh_clear()
result = {"modifiers": [m.name for m in key.modifiers], "material": mat.name, "tris_after_modifiers": tris}
