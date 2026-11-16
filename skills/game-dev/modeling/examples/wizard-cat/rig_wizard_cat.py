"""Rig and animate the wizard cat for Roblox. The source of the rig: run it, never edit the .blend.

  blender -b --factory-startup --python rig_wizard_cat.py -- --out rig
  blender -b --factory-startup --python rig_wizard_cat.py -- --verify rig/wizard-cat-rigged.fbx

The first builds the cat in memory (build_cat.py, then build_wizard_cat.py's dress), rigs it, and
writes into <out> only: wizard-cat-rigged.blend, wizard-cat-rigged.fbx (every action as a take),
wizard-cat-<Action>.fbx (one action each), palette.png and key-frame renders of each action. The
second re-imports an FBX into an empty Blender and runs the same Roblox checks on what an
importer sees. Both exit 1 on a failed check. Method and sources: ../../references/rigging.md.

Skinning: the 22 parts are joined into ONE mesh and weighted by region. The FBX then holds one
skinned mesh, which Roblox's rig rules are written for, and one material means one draw call.
Parenting each part to a bone would export rigid meshes and no skin at all. A separate part
follows one bone. The Body is weighted per ring: each cross-section follows Chest, Spine or Hips,
each paw follows its leg bone, and the outer corners of a leg's top ring give a quarter to the
leg so the shoulder moves with it. No vertex has more than 2 influences.

Legs have one bone each: a v3 leg is two rings of vertices, the belly ring (the body's own) and
the paw. A lower-leg bone would own no vertex. The leg bone's rotation and location place the
paw, and the leg's sides stretch between belly and paw.

Bones: every bone lies along +Y with roll 0, so its rest matrix is the identity rotation. That is
the strict reading of Roblox's "rotation 0,0,0", and it makes a pose bone's X/Y/Z the world's:
X pitches (a leg swings), Y rolls, Z yaws (a tail sways). The cost: bones do not point along the
limbs in Blender's viewport. Deform bones are keyed directly; there are no IK or control bones.
"""
import argparse
import importlib.util
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
STEM = "wizard-cat-rigged"
RIG = "WizardCatRig"
FPS = 24

# name: (parent, head, collection). Tail = head + (0, 0.15, 0): rest rotation 0 for every bone.
BONES = {
    "Root": (None, (0, 0, 0), "Root"),  # at the origin, never weighted
    "Hips": ("Root", (0, 0.45, 0.6), "Torso"),
    "Spine": ("Hips", (0, 0.42, 0.6), "Torso"),  # hinges between the body's rings 2 and 3
    "Chest": ("Spine", (0, 0.1, 0.62), "Torso"),  # hinges between rings 1 and 2
    "Neck": ("Chest", (0, -0.3, 0.9), "Torso"),  # a joint only: the head sits on the body, no neck mesh
    "Head": ("Neck", (0, -0.38, 1.0), "Torso"),  # ears, face and fur cheeks ride it
    "Hat": ("Head", (0, -0.4, 1.66), "Outfit"),  # its own bone so it can tip and fall off
    "Leg_F.L": ("Chest", (0.12, -0.195, 0.36), "Legs"),  # pivots at the middle of the leg's top ring
    "Leg_F.R": ("Chest", (-0.12, -0.195, 0.36), "Legs"),
    "Leg_B.L": ("Hips", (0.125, 0.42, 0.335), "Legs"),
    "Leg_B.R": ("Hips", (-0.125, 0.42, 0.335), "Legs"),
    "Tail1": ("Hips", (0, 0.62, 0.78), "Tail"),
    "Tail2": ("Tail1", (0, 0.95, 1.1), "Tail"),
    "Cape": ("Hips", (0, 0.56, 0.9), "Outfit"),  # hinge over the rump, moves the trailing hem
    "Prop": ("Root", (0.58, -0.55, 0), "Outfit"),  # staff, crystal and spark
}
HEAD_PARTS = "Head Nose Eye_L Eye_R Ear_L Ear_R EarInner_L EarInner_R FurCheek_L FurCheek_R".split()
PART_BONE = {
    **{p: "Head" for p in HEAD_PARTS},
    "HatBrim": "Hat", "Hat": "Hat", "HatTip": "Hat",
    "FurChest": "Chest",
    "Tail": "Tail1", "TailUpper": "Tail2", "FurTailTip": "Tail2",
    "Staff": "Prop", "Crystal": "Prop", "Sparks": "Prop",
}
LEG_BONE = {"Leg_FL": "Leg_F.L", "Leg_FR": "Leg_F.R", "Leg_BL": "Leg_B.L", "Leg_BR": "Leg_B.R"}  # Body's groups
SPINE = (("Chest", -0.05), ("Spine", 0.28), ("Hips", 0.56))  # the body's rings 1, 2, 3: one bone each
SHOULDER = 0.25  # how much of a leg's top-ring corner follows the leg bone
HAT_DOWN = Matrix.Translation((-0.5, -1.1, 0.33)) @ Matrix.Rotation(math.radians(113), 4, "X")  # on its side


def args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser(prog="rig_wizard_cat.py")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--out", help="folder for the .blend, the .fbx and the renders")
    mode.add_argument("--verify", metavar="FBX", help="re-import this FBX and run the Roblox checks")
    ap.add_argument("--size", type=int, default=512, help="render size, px")
    return ap.parse_args(argv)


def load_wizard():
    spec = importlib.util.spec_from_file_location("build_wizard_cat", os.path.join(HERE, "build_wizard_cat.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # guarded main(): builds nothing by itself
    return mod


def spine_weights(y):
    """Chest/Spine/Hips weights for a Body vertex at world y: linear between neighbouring bones."""
    if y <= SPINE[0][1]:
        return {SPINE[0][0]: 1.0}
    for (a, ya), (b, yb) in zip(SPINE, SPINE[1:]):
        if y <= yb:
            t = (y - ya) / (yb - ya)
            return {a: 1 - t, b: t}
    return {SPINE[-1][0]: 1.0}


def weigh(part):
    """Vertex groups on one part, before the join (joining merges groups by name)."""
    world = [part.matrix_world @ v.co for v in part.data.vertices]
    weights = [{} for _ in world]
    if part.name == "Body":
        paws = {}  # vertex -> leg bone, from the groups build_cat.py leaves on the Body
        names = {g.index: g.name for g in part.vertex_groups}
        for v in part.data.vertices:
            for e in v.groups:
                paws[v.index] = LEG_BONE[names[e.group]]
        part.vertex_groups.clear()  # the bones' names replace them below
        for i, p in enumerate(world):
            weights[i] = {paws[i]: 1.0} if i in paws else spine_weights(p.y)
        for a, b in part.data.edge_keys:  # a leg's top ring: the body vertices its paw connects to
            for paw, top in ((a, b), (b, a)):
                if paw in paws and top not in paws and abs(world[top].x) > 0.1:  # the centre line stays put
                    weights[top] = {**{k: w * (1 - SHOULDER) for k, w in spine_weights(world[top].y).items()},
                                    paws[paw]: SHOULDER}
    elif part.name == "Cape":  # over the body it follows the body's rings; the trailing hem has its bone
        weights = [{"Cape": 1.0} if p.y > 0.7 else spine_weights(p.y) for p in world]
    else:
        weights = [{PART_BONE[part.name]: 1.0}] * len(world)  # KeyError = a part this rig does not know
    for i, ws in enumerate(weights):
        for bone, w in ws.items():
            if w > 1e-4:
                (part.vertex_groups.get(bone) or part.vertex_groups.new(name=bone)).add([i], w, "REPLACE")


def build_armature():
    data = bpy.data.armatures.new(RIG)
    arm = bpy.data.objects.new(RIG, data)
    bpy.context.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    for name, (parent, head, _) in BONES.items():
        b = data.edit_bones.new(name)
        b.head = head
        b.tail = Vector(head) + Vector((0, 0.15, 0))
        b.roll = 0
        b.parent = data.edit_bones[parent] if parent else None  # not connected: heads are the pivots
    bpy.ops.object.mode_set(mode="OBJECT")
    data.bones["Root"].use_deform = False
    for name, (_, _, coll) in BONES.items():
        (data.collections.get(coll) or data.collections.new(coll)).assign(data.bones[name])
        arm.pose.bones[name].rotation_mode = "XYZ"
    return arm


def skin(cat, kit, arm):
    """Join every part into one mesh, weighted part by part, and bind it to the armature."""
    bpy.context.view_layer.update()  # matrix_world of the parts
    parts = [o for o in cat.children if o.type == "MESH"]
    parts.sort(key=lambda o: o.name != "Body")  # the join keeps the first one's object
    for p in parts:
        weigh(p)
    mesh = kit.join("WizardCat", parts)
    mesh.parent = None  # the empty sat at the origin with no transform
    bpy.data.objects.remove(cat)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    mesh.parent = arm
    mesh.modifiers.new("Armature", "ARMATURE").object = arm
    return mesh


def wave(t, phase=0.0, times=1):
    return math.sin(2 * math.pi * (times * t + phase))


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def track(t, *keys):
    """A value through (time, value) keys, eased between neighbours."""
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1:
            return v0 + (v1 - v0) * ease((t - t0) / (t1 - t0))
    return keys[-1][1]


# A pose is {bone: ((rx, ry, rz) degrees, (x, y, z) studs)}; t runs 0..1 over the action.
# +X rotation carries a paw back and a tail or staff tip forward; +Y rolls the top toward +X.

def idle(t):
    """A breath (the chest rises, the front paws stay down) and a slow tail sway."""
    rise = 0.012 * wave(t)
    return {
        "Chest": ((0, 0, 0), (0, 0, rise)),
        "Leg_F.L": ((0, 0, 0), (0, 0, -rise)),
        "Leg_F.R": ((0, 0, 0), (0, 0, -rise)),
        "Head": ((1.5 * wave(t, -0.1), 0, 0), (0, 0, 0)),
        "Cape": ((1.5 + 1.5 * wave(t), 0, 0), (0, 0, 0)),
        "Tail1": ((0, 0, 12 * wave(t)), (0, 0, 0)),
        "Tail2": ((0, 0, 16 * wave(t, -0.15)), (0, 0, 0)),
    }


def walk(t):
    """A lateral-sequence walk on the spot: back left, front left, back right, front right."""
    pose = {
        "Hips": ((0, 3 * wave(t), 0), (0, 0, 0.015 * wave(t, times=2))),
        "Spine": ((0, 0, 4 * wave(t)), (0, 0, 0)),
        "Chest": ((0, 0, -6 * wave(t)), (0, 0, 0)),
        "Head": ((2 * wave(t, times=2), 0, 2 * wave(t)), (0, 0, 0)),
        "Cape": ((4 + 4 * wave(t, times=2), 0, 0), (0, 0, 0)),
        "Tail1": ((0, 0, 14 * wave(t)), (0, 0, 0)),
        "Tail2": ((0, 0, 18 * wave(t, -0.15)), (0, 0, 0)),
        "Prop": ((5 * wave(t), 0, 0), (0, 0, 0.1 + 0.04 * wave(t, times=2))),  # the staff hovers along
    }
    for leg, phase in (("Leg_B.L", 0), ("Leg_F.L", 0.25), ("Leg_B.R", 0.5), ("Leg_F.R", 0.75)):
        lift = 0.07 * max(0.0, -math.cos(2 * math.pi * (t + phase)))  # up while it comes forward
        pose[leg] = ((28 * wave(t, phase), 0, 0), (0, 0, lift))
    return pose


def run(t):
    """A bound: both back paws push, the cat stretches in the air, both front paws land, it gathers."""
    e = wave(t)  # +1 stretched and airborne, -1 gathered with the back arched
    pose = {
        "Hips": ((10 * e, 0, 0), (0, 0, 0.09 + 0.09 * e)),
        "Spine": ((-10 * e, 0, 0), (0, 0, 0)),
        "Chest": ((-8 * e, 0, 0), (0, 0, 0)),
        "Head": ((8 * e, 0, 0), (0, 0, 0)),  # stays level
        "Hat": ((-5 + 3 * e, 0, 0), (0, 0, 0)),
        "Cape": ((14 + 8 * e, 0, 0), (0, 0, 0)),  # streams behind
        "Tail1": ((-25 - 10 * e, 0, 0), (0, 0, 0)),
        "Tail2": ((-20 - 10 * wave(t, -0.15), 0, 0), (0, 0, 0)),
        "Prop": ((18 + 4 * e, 0, 0), (0, 0, 0.22 + 0.06 * e)),  # flies alongside, crystal first
    }
    for leg, sign in (("Leg_F", -1), ("Leg_B", 1)):
        for side, lag in ((".L", 0.0), (".R", 0.04)):  # the pair lands a beat apart, as in a gallop
            swing = wave(t, -lag)
            forward = sign * math.cos(2 * math.pi * (t - lag)) < 0  # this paw is coming forward
            lift = 0.09 * abs(math.cos(2 * math.pi * (t - lag))) if forward else 0.0
            pose[leg + side] = ((sign * 42 * swing, 0, 0), (0, 0, lift))
    return pose


def attack(t):
    """One shot: crouch back, pounce with the right front paw and the staff, recover to rest."""
    c = track(t, (0, 0), (0.3, 1), (0.45, 0))  # the crouch
    k = track(t, (0, 0), (0.3, 0), (0.45, 1), (0.6, 1), (1, 0))  # the strike
    hy, hz = 0.10 * c - 0.26 * k, -0.07 * c + 0.03 * k
    planted = ((0, 0, 0), (0, -hy, -hz))  # a paw that stays where it stood while the body moves
    return {
        "Hips": ((6 * c - 9 * k, 0, 0), (0, hy, hz)),
        "Chest": ((6 * c - 10 * k, 0, 0), (0, 0, 0)),
        "Head": ((8 * c - 8 * k, 0, 0), (0, 0, 0)),
        "Hat": ((-7 * k, 0, 0), (0, 0, 0)),
        "Leg_B.L": planted,
        "Leg_B.R": planted,
        "Leg_F.L": ((-15 * k, 0, 0), (0, -0.10 * c, 0.07 * c - hz * k)),  # steps into the pounce
        "Leg_F.R": ((20 * c - 80 * k, 0, 0), (0, -0.10 * c - 0.06 * k, 0.07 * c + 0.16 * k)),  # the swipe
        "Tail1": ((-22 * k, 0, 10 * c * wave(t, times=5)), (0, 0, 0)),
        "Tail2": ((-15 * k, 0, 0), (0, 0, 0)),
        "Cape": ((16 * k, 0, 0), (0, 0, 0)),
        "Prop": ((-14 * c + 48 * k, 0, 0), (0, -0.12 * k, 0.14 * k + 0.04 * c)),  # back, then the crystal leads
    }


def dead(t):
    """One shot: a stagger, a fall onto its right side, the hat and the staff to the ground, held."""
    stagger = math.sin(math.pi * t / 0.3) * wave(t / 0.3) if t < 0.3 else 0.0
    s = ease((t - 0.3) / 0.4)  # the fall
    bounce = 0.04 * math.sin(math.pi * min(1.0, max(0.0, (t - 0.7) / 0.12)))
    p = ease((t - 0.25) / 0.4)  # the staff, let go a moment earlier
    return {
        "Hips": ((0, 13 * stagger - 75 * s, 6 * stagger), (-0.08 * stagger - 0.1 * s, 0, -0.18 * s + bounce)),
        "Spine": ((0, 0, -4 * stagger), (0, 0, 0)),
        "Chest": ((0, 6 * stagger + 10 * s, 0), (0, 0, 0)),
        "Head": ((12 * abs(stagger) + 8 * s, 8 * stagger + 20 * s, 0), (0, 0, 0)),
        "Leg_F.L": ((-20 * s, 25 * s, 0), (0, 0, 0)),  # the upper pair hangs
        "Leg_B.L": ((20 * s, 25 * s, 0), (0, 0, 0)),
        "Leg_F.R": ((-10 * s, -12 * s, 0), (0, 0, 0)),  # the lower pair rests on the ground
        "Leg_B.R": ((10 * s, -6 * s, 0), (0, 0, 0)),
        "Tail1": ((0, -20 * s, 8 * stagger), (0, 0, 0)),
        "Tail2": ((0, -15 * s, 0), (0, 0, 0)),
        "Cape": ((70 * s, 0, 0), (0, 0, 0)),  # the long hem trails behind instead of spearing the ground
        "Prop": ((-88 * p, 4 * stagger, -35 * p), (0, 0, 0.05 * p)),  # falls back and outward, clear of the paws
        "Hat": ("world", HAT_DOWN, ease((t - 0.35) / 0.4), 0.25),  # leaves the head and lands in front
    }


# name, frames, pose, loop. A loop keys 1..frames+1 (the last repeats the first); a one-shot 1..frames.
ACTIONS = (("Idle", 48, idle, True), ("Walk", 24, walk, True), ("Run", 16, run, True),
           ("Attack", 20, attack, False), ("Dead", 30, dead, False))
WANT = {name: (1, frames + loop) for name, frames, _, loop in ACTIONS}


def rest(arm):
    if arm.animation_data:
        arm.animation_data.action = None
    for pb in arm.pose.bones:
        pb.location = (0, 0, 0)
        pb.rotation_euler = (0, 0, 0)
        pb.rotation_quaternion = (1, 0, 0, 0)  # what the FBX importer keys
        pb.scale = (1, 1, 1)


def animate(arm, name, frames, pose_at, loop):
    rest(arm)
    action = bpy.data.actions.new(name)
    action.use_fake_user = True  # kept in the .blend while another action is assigned
    arm.animation_data_create().action = action
    span = frames if loop else frames - 1
    keys = range(1, WANT[name][1] + 1)

    def key(pb, frame):
        pb.keyframe_insert("rotation_euler", frame=frame)
        pb.keyframe_insert("location", frame=frame)

    for f in keys:
        for bone, value in pose_at((f - 1) / span).items():
            if value[0] != "world":
                pb = arm.pose.bones[bone]
                pb.rotation_euler = [math.radians(a) for a in value[0]]
                pb.location = value[1]
                key(pb, f)
    # ("world", target, k, arc): the bone leaves its parent for a place in the world. k blends from
    # riding the parent (0) to the target matrix (1), with a hop of `arc` studs on the way.
    for f in keys:
        for bone, value in pose_at((f - 1) / span).items():
            if value[0] == "world":
                _, target, k, arc = value
                bpy.context.scene.frame_set(f)  # the parents, from the keys above
                pb = arm.pose.bones[bone]
                riding = pb.parent.matrix @ Matrix.Translation(pb.bone.head_local - pb.parent.bone.head_local)
                goal = riding.lerp(target, k)
                goal.translation.z += arc * 4 * k * (1 - k)
                local = riding.inverted() @ goal
                pb.location, pb.rotation_euler = local.to_translation(), local.to_euler("XYZ")
                key(pb, f)
    return action


def play(arm, action, frame):
    rest(arm)
    if action:
        arm.animation_data.action = action
        arm.animation_data.action_slot = action.slots[0]
    bpy.context.scene.frame_set(frame)


def motion(arm, mesh, action):
    """Over the whole action: how far any vertex gets from rest, and the lowest any vertex goes."""
    def shape(act, frame):
        play(arm, act, frame)
        ev = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
        return [ev.matrix_world @ v.co for v in ev.data.vertices]

    still = shape(None, 1)
    first, last = (int(round(f)) for f in action.frame_range)
    shapes = [shape(action, f) for f in range(first, last + 1)]
    rest(arm)
    return (max((p - q).length for sh in shapes for p, q in zip(sh, still)),
            min(p.z for sh in shapes for p in sh), min(p.z for p in still))


def report_motion(arm, mesh, action):
    moved, low, rest_low = motion(arm, mesh, action)
    ok = moved > 0.01 and moved < 4.0 and low > rest_low - 0.15  # it deforms; nothing flies off or sinks
    print(f"check\tdeforms\t{'ok' if ok else 'FAIL'}\t{action.name.split('|')[-1]}: a vertex moves up to {moved:.3f} "
          f"studs from rest, lowest z {low:.3f} (rest {rest_low:.3f})")
    return not ok


def export_fbx(path, arm, action=None):
    """Every action as a take, or with `action` that one alone."""
    # create.roblox.com/docs/art/modeling/export-requirements, same as scripts/blender_export.py.
    # The bone nodes are written from the pose at export time, so the armature is at rest for it.
    rest(arm)
    track = None
    if action:
        # One action alone goes out as an NLA strip: like an action take it starts at time 0 (a
        # scene take would start one frame in). Frame 0 is before the strip, so the pose is rest.
        track = arm.animation_data.nla_tracks.new()
        strip = track.strips.new(action.name, 1, action)
        strip.extrapolation = "NOTHING"
        bpy.context.scene.frame_set(0)
    bpy.ops.export_scene.fbx(
        filepath=path, object_types={"ARMATURE", "MESH"}, path_mode="COPY", embed_textures=True,
        apply_scale_options="FBX_SCALE_UNITS", add_leaf_bones=False, use_triangles=True,
        bake_anim=True, bake_anim_use_all_actions=action is None, bake_anim_use_nla_strips=action is not None,
        bake_anim_use_all_bones=True, bake_anim_simplify_factor=0.0)
    if track:
        arm.animation_data.nla_tracks.remove(track)
    bpy.context.scene.frame_set(1)


def render(out, size, arm, shots):
    """build_cat.py's framing (ortho, the rest bounding box), held still across poses. shots: (action, frame, views)."""
    scene = bpy.context.scene
    try:
        scene.render.engine = "BLENDER_EEVEE"  # Blender 5.x
    except TypeError:
        scene.render.engine = "BLENDER_EEVEE_NEXT"  # Blender 4.2-4.x
    bpy.ops.object.light_add(type="SUN", rotation=(math.radians(50), 0, math.radians(30)))
    bpy.context.active_object.data.energy = 1.6
    scene.render.resolution_x = scene.render.resolution_y = size
    scene.view_settings.view_transform = "Standard"
    world = bpy.data.worlds.new("World")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.9, 0.9, 0.93, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.35
    scene.world = world
    corners = [o.matrix_world @ Vector(c) for o in scene.objects if o.type == "MESH" for c in o.bound_box]
    lo = Vector([min(c[i] for c in corners) for i in range(3)])
    hi = Vector([max(c[i] for c in corners) for i in range(3)])
    target = (lo + hi) / 2
    bpy.ops.object.camera_add()
    cam = bpy.context.active_object
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = max(hi - lo) * 1.7  # room for a pounce and a fallen staff
    bpy.ops.mesh.primitive_plane_add(size=40)  # the ground, so a jump and a fall read
    scene.camera = cam
    offsets = {"side": Vector((8, 0, 1.4)), "back": Vector((-4, 7, 2.6)), "front": Vector((5.5, -5.5, 4))}
    for action, frame, views in shots:
        play(arm, action, frame)
        for view in views.split():
            cam.location = target + offsets[view]
            cam.rotation_euler = (-offsets[view]).to_track_quat("-Z", "Y").to_euler()
            stem = f"{action.name.lower()}-f{frame:02d}" if action else "rest"
            scene.render.filepath = os.path.join(out, f"{stem}-{view}.png")
            bpy.ops.render.render(write_still=True)
    rest(arm)


def fbx_limb_nodes(path):
    """Each bone's own rotation and scale as written in the FBX file (absent = 0 and 1)."""
    from io_scene_fbx import parse_fbx

    root, _ = parse_fbx.parse(path)
    objects = next(e for e in root.elems if e.id == b"Objects")
    out = {}
    for model in (e for e in objects.elems if e.id == b"Model" and e.props[2] == b"LimbNode"):
        name = model.props[1].split(b"\x00")[0].decode()
        vals = {"Lcl Rotation": (0, 0, 0), "PreRotation": (0, 0, 0), "Lcl Scaling": (1, 1, 1)}
        for p70 in (e for e in model.elems if e.id == b"Properties70"):
            for p in p70.elems:
                if p.props[0].decode() in vals:
                    vals[p.props[0].decode()] = tuple(p.props[4:7])
        out[name] = vals
    return out


def near(values, want, eps=1e-4):
    return all(abs(v - want) < eps for v in values)


def checks(arm, mesh, fbx=None):
    """Print the report; return the number of failed Roblox rig checks."""
    bones = arm.data.bones
    groups = {g.index: g.name for g in mesh.vertex_groups if g.name in bones}
    per_vertex = [[groups[g.group] for g in v.groups if g.group in groups and g.weight > 1e-6]
                  for v in mesh.data.vertices]
    max_inf = max(len(names) for names in per_vertex)
    unweighted = sum(1 for names in per_vertex if not names)
    on_root = sum(1 for names in per_vertex if "Root" in names)
    # matrix_local is the rest pose in armature space: identity rotation, scale 1 wanted.
    bad_rot = [b.name for b in bones if not near(b.matrix_local.to_euler(), 0)]
    bad_scale = [b.name for b in bones if not near(b.matrix_local.to_scale(), 1)]
    posed = [pb.name for pb in arm.pose.bones if not near(pb.scale, 1)]
    roots = [b for b in bones if b.parent is None]
    root_at = tuple(round(c, 5) for c in (arm.matrix_world @ roots[0].head_local))
    tris = sum(len(p.vertices) - 2 for p in mesh.data.polygons)
    print(f"armature\t{arm.name}\tbones={len(bones)}\t{' '.join(b.name for b in bones)}")
    print(f"collections\t{' '.join(f'{c.name}={len(c.bones)}' for c in arm.data.collections)}")
    print(f"mesh\t{mesh.name}\tverts={len(mesh.data.vertices)}\ttris={tris}"
          f"\tskinned_to={next((m.object.name for m in mesh.modifiers if m.type == 'ARMATURE'), None)}")
    rows = [
        ("root_bone", f"{roots[0].name} at {root_at}, {len(roots)} root(s)",
         len(roots) == 1 and near(root_at, 0)),
        ("root_weights", f"{on_root} vertices weighted to the root", on_root == 0),
        ("max_influences", f"{max_inf} per vertex (limit 4)", max_inf <= 4),
        ("unweighted", f"{unweighted} vertices", unweighted == 0),
        ("rest_rotation", f"non-zero on: {bad_rot or 'none'}", not bad_rot),
        ("rest_scale", f"not 1 on: {bad_scale + posed or 'none'}", not bad_scale and not posed),
    ]
    if fbx:
        nodes = fbx_limb_nodes(fbx)
        off = sorted(n for n, v in nodes.items() if not (near(v["Lcl Rotation"], 0, 1e-3)
                     and near(v["PreRotation"], 0, 1e-3) and near(v["Lcl Scaling"], 1, 1e-3)))
        rows.append(("fbx_bone_nodes", f"{len(nodes)} LimbNodes in the file, rotation or scale set on: {off or 'none'}",
                     len(nodes) == len(bones) and not off))
    for name, text, ok in rows:
        print(f"check\t{name}\t{'ok' if ok else 'FAIL'}\t{text}")
    return sum(1 for _, _, ok in rows if not ok)


def report_actions(want):
    """Print every action; return 1 unless they are exactly `want` {name: (first, last)}."""
    found = {}
    for a in bpy.data.actions:
        first, last = (int(round(f)) for f in a.frame_range)
        found[a.name.split("|")[-1]] = (first, last)  # the FBX importer prefixes the armature's name
        print(f"action\t{a.name}\tframes={first}-{last}\tfps={bpy.context.scene.render.fps}")
    ok = found == want
    print(f"check\tactions\t{'ok' if ok else 'FAIL'}\twanted {' '.join(f'{n} {a}-{b}' for n, (a, b) in want.items())}")
    return not ok


def verify(path):
    """What an importer sees: the FBX in an empty Blender, the same checks, and that it moves."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=path)
    arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
    mesh = next(o for o in bpy.data.objects if o.type == "MESH")
    name = os.path.basename(path)[len("wizard-cat-"):-len(".fbx")]  # "rigged", or one action's name
    want = WANT if name == "rigged" else {name: WANT[name]}
    print(f"verify\t{path}")
    print(f"objects\t{' '.join(f'{o.name}:{o.type}' for o in bpy.data.objects)}")
    print(f"images\t{' '.join(f'{i.name}:{i.size[0]}x{i.size[1]}' for i in bpy.data.images) or 'none'}")
    failed = checks(arm, mesh, fbx=path) + report_actions(want)
    return failed + sum(report_motion(arm, mesh, a) for a in bpy.data.actions)


def main():
    a = args()
    wizard = load_wizard()
    kit = wizard.cat_kit
    if a.verify:
        failed = verify(kit.inside_cwd(a.verify))
        print(f"result\t{'PASS' if not failed else f'{failed} FAILED'}")
        sys.exit(1 if failed else 0)
    out = kit.inside_cwd(a.out)
    os.makedirs(out, exist_ok=True)
    cat = kit.build(out)  # writes palette.png into <out>
    wizard.dress(cat)
    arm = build_armature()
    mesh = skin(cat, kit, arm)
    assert bpy.utils.flip_name("Leg_F.L") == "Leg_F.R"  # Blender mirrors these names
    bpy.context.scene.render.fps = FPS
    act = {name: animate(arm, name, frames, fn, loop) for name, frames, fn, loop in ACTIONS}
    rest(arm)
    failed = checks(arm, mesh) + report_actions(WANT) + sum(report_motion(arm, mesh, x) for x in act.values())

    export_fbx(os.path.join(out, f"{STEM}.fbx"), arm)
    for name, action in act.items():  # Roblox's importer may read one take per file
        export_fbx(os.path.join(out, f"wizard-cat-{name}.fbx"), arm, action)
    bpy.context.scene.frame_start, bpy.context.scene.frame_end = 1, 48
    play(arm, act["Idle"], 1)  # the .blend opens on the idle
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, f"{STEM}.blend"))
    render(out, a.size, arm, (
        (None, 1, "side"), (act["Idle"], 13, "side back"),
        (act["Walk"], 4, "side back"), (act["Walk"], 16, "side"),
        (act["Run"], 5, "side back"), (act["Run"], 9, "side"), (act["Run"], 13, "side"),
        (act["Attack"], 6, "side"), (act["Attack"], 10, "side front"), (act["Attack"], 15, "side"),
        (act["Dead"], 4, "side back"), (act["Dead"], 16, "side"), (act["Dead"], 30, "side front"),
    ))
    print(f"result\t{'PASS' if not failed else f'{failed} FAILED'}\t{out}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
