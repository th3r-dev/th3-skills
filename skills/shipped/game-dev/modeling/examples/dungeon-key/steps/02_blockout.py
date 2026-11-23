# Step 2: blockout. Separate parts first, so each can be judged and moved in the viewport before they
# are joined: bow (a ring), collar, shaft, two teeth. Low segment counts: a Roblox prop seen at arm's
# length. Built with bmesh (the data API), not operators.
import math

import bmesh
import bpy
from mathutils import Matrix

STUD = 0.28
col = bpy.data.collections["DungeonKey"]


def obj(name, bm):
    me = bpy.data.meshes.get(name) or bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.get(name) or bpy.data.objects.new(name, me)
    ob.data = me
    if ob.name not in col.objects:
        col.objects.link(ob)
    return ob


def torus(major, minor, seg=12, ring=6):
    bm = bmesh.new()
    rows = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        row = []
        for j in range(ring):
            b = 2 * math.pi * j / ring
            r = major + minor * math.cos(b)
            # the ring stands in the XZ plane, so the key lies flat along X with its bow upright
            row.append(bm.verts.new((r * math.cos(a), 0.0 + minor * math.sin(b) * 0.9, r * math.sin(a))))
        rows.append(row)
    for i in range(seg):
        for j in range(ring):
            bm.faces.new((rows[i][j], rows[(i + 1) % seg][j], rows[(i + 1) % seg][(j + 1) % ring], rows[i][(j + 1) % ring]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def cylinder(r, length, seg=8):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=length)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "Y"))
    return bm


def box(sx, sy, sz):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    return bm


bow = obj("KeyBow", torus(0.55 * STUD, 0.16 * STUD))
bow.location = (-0.75 * STUD, 0, 0)
collar = obj("KeyCollar", cylinder(0.2 * STUD, 0.18 * STUD, seg=8))
collar.location = (-0.12 * STUD, 0, 0)
shaft = obj("KeyShaft", cylinder(0.12 * STUD, 2.0 * STUD, seg=8))
shaft.location = (0.85 * STUD, 0, 0)
t1 = obj("KeyTooth1", box(0.22 * STUD, 0.16 * STUD, 0.42 * STUD))
t1.location = (1.62 * STUD, 0, -0.28 * STUD)
t2 = obj("KeyTooth2", box(0.22 * STUD, 0.16 * STUD, 0.3 * STUD))
t2.location = (1.25 * STUD, 0, -0.22 * STUD)
bpy.context.view_layer.update()
parts = [bow, collar, shaft, t1, t2]
result = {
    "parts": {o.name: [round(v, 3) for v in o.dimensions] for o in parts},
    "tris": sum(len(o.data.polygons) for o in parts),
}
