# Step 5: fix what asset-qa found after the union, on the base mesh (the live modifiers stay on top):
# duplicate verts and zero-length edges, back-to-back faces left inside, n-gons (Roblox wants none:
# triangulate only those, quads stay quads), then a UV map (uv_pack, blender-skills).
import bmesh
import bpy

key = bpy.data.objects["DungeonKey"]
bm = bmesh.new()
bm.from_mesh(key.data)
merged = bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005)
bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=0.0005)
# back-to-back faces: two faces on the same set of verts, facing each other inside the solid
seen, inner = {}, set()
for f in bm.faces:
    k = frozenset(v.index for v in f.verts)
    if k in seen:
        inner.update((f, seen[k]))
    else:
        seen[k] = f
bmesh.ops.delete(bm, geom=list(inner), context="FACES_ONLY")
ngons = [f for f in bm.faces if len(f.verts) > 4]
bmesh.ops.triangulate(bm, faces=ngons, quad_method="BEAUTY", ngon_method="BEAUTY")
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(key.data)
bm.free()
key.data.update()
result = {"back_to_back_removed": len(inner), "ngons_triangulated": len(ngons),
          "faces": len(key.data.polygons), "tris": sum(len(p.vertices) - 2 for p in key.data.polygons)}
