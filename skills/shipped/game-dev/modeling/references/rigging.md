# Rigging a low-poly character for Roblox

Read before giving a model bones or animation. Each rule names its source (read 2026-11-16).
The worked case is `examples/wizard-cat/rig_wizard_cat.py`: 15 bones, one skinned mesh, five
actions (idle, walk, run, attack, dead), checked after a round trip through FBX.

## Sources

| Source | Reached | What it gives |
|---|---|---|
| [Roblox: specifications](https://create.roblox.com/docs/art/modeling/specifications) and [export requirements](https://create.roblox.com/docs/art/modeling/export-requirements) | yes | the rig rules and the FBX settings below |
| [UniRig](https://github.com/VAST-AI-Research/UniRig) (MIT), README and `requirements.txt` | yes | the ML route: what it needs, its three commands, its stated limits |
| [composio-community/opencode-skills: blender-rigging-animation](https://github.com/composio-community/opencode-skills/blob/master/skills/blender-rigging-animation/SKILL.md) | yes | a UI workflow in eight steps. The repo's README says MIT; there is no LICENSE file and the skill has no licence field, so ideas only, no wording reused |
| [Blender Studio: Rain v3](https://studio.blender.org/characters/rain/v3/) (rig CC-BY 4.0, "Rain Rig (CC) Blender Foundation, studio.blender.org") | yes | what a film rig carries: IK/FK switches with snapping, stretchy IK, FK hinge, IK parent switching, layered face controls, a UI script inside the `.blend`. The page lists no bone names or collections |
| [Skillshare: How to rig in Blender](https://www.skillshare.com/en/blog/how-to-rig-in-blender-a-step-by-step-tutorial-skillshare-blog/) | **no** | HTTP 403 (a bot challenge) from two clients. Nothing here comes from it |

Also not reached: the CloudRig documentation (404 and 403), so nothing below claims its prefixes.

## Roblox rig rules

| Rule | Value | How the script meets it |
|---|---|---|
| Bone scale | 1, 1, 1 | bones are never scaled; a breath is a translation |
| Bone rotation | 0, 0, 0, frozen | every bone lies along +Y with roll 0, so its rest matrix has no rotation |
| Root | at 0, 0, 0 | `Root` has its head at the origin; the armature object has no transform |
| Root weights | none | `Root` is a non-deform bone and no vertex group names it |
| Influences | at most 4 per vertex | 1 for a rigid part, 2 at a leg's shoulder corners |
| Export | FBX: Path Mode Copy, Embed Textures, Apply Scalings = FBX Unit Scale, Add Leaf Bones off | `export_fbx()`; also Triangulate on and Bake Animation on, with the armature at rest when it is written |

Scaled bones are out, so the actions key location and rotation only.

## Routes

| Route | When | Needs | Default |
|---|---|---|---|
| **Scripted rig in Blender** | segmented or low-poly models, anything whose bone names and pivots must be exact | Blender, a Python script | **yes** |
| **UniRig** (ML) | a dense, single-surface organic mesh with no rig, on a CUDA machine | see below | no |
| **Film-style control rig** (Rain, CloudRig, Rigify) | hand animation by an animator in Blender | control bones baked to deform bones before export | no |

### UniRig: not used here

From its README and `requirements.txt`:

- Python 3.11, PyTorch 2.3.1 or later, and a **CUDA GPU with at least 8 GB VRAM**. Also `spconv`
  built for the CUDA version, `torch_scatter` and `torch_cluster` wheels matched to torch and
  CUDA, `flash_attn` (the README warns it often fails to install), `bpy==4.2`, `numpy==1.26.4`.
- Weights download from Hugging Face (`VAST-AI/UniRig`) on first run. The README gives no size.
- Input `.obj`, `.fbx`, `.glb`, `.vrm`. Three steps: `launch/inference/generate_skeleton.sh`,
  then `generate_skin.sh` on that skeleton, then `merge.sh` back onto the original model.
- Stated limits: skinning "may degrade significantly" when the predicted skeleton is off (a
  missing tail bone, for example), so the skeleton is checked and fixed first. The README names
  no macOS, Apple Silicon or CPU path, and no mesh size limits. It points to SkinTokens as its
  successor.

Why not here. The machine is an Apple Silicon Mac: no CUDA, so the install stops at the GPU
requirement. It was not installed and no weights were downloaded. It also does not fit the model,
which is reasoning from the README and not a test: a 292-triangle cat in 22 closed parts wants
each part to follow one bone, and a predicted skeleton with smooth predicted weights gives
neither known bone names nor rigid parts. Its output would still need the Roblox rules applied
(rest rotation, root at the origin, the 4-influence cap). Consider it for a dense mesh from a
generator (the Meshy route), on a CUDA machine, with the same checks afterwards.

### Film-style rigs: conventions only

Rain is built for an animator: controls on top of the bones that deform the mesh, with a script
for the UI. A game engine reads none of that. Roblox gets deform bones and baked keys. So this
rig has deform bones only and keys them directly. Add control bones (IK feet, for example) when a
person will animate by hand, and bake them on export; `bake_anim` already does.

What carries over:

- **`.L` / `.R` suffixes**, so Blender mirrors poses and weights. The script asserts
  `bpy.utils.flip_name("Leg_F.L") == "Leg_F.R"`. Left is the cat's own left (+X, it faces -Y).
- **One name per bone, by body part, numbered along a chain** (`Tail1`, `Tail2`).
- **Bone collections by region** (`Root`, `Torso`, `Legs`, `Tail`, `Outfit`), Blender 4.0 and
  later. They are a Blender-side convenience and do not survive FBX.
- From the composio skill: apply transforms before binding, move the bones to test the
  deformation early, keep the rig simple. Not taken: its automatic weights, which blend
  neighbouring parts of a segmented model, and its IK, which a baked game rig does not need.

## Segmented low-poly models: join, then weight by region

The model is 22 separate closed parts. Two ways to make them follow bones:

| | (a) Join into one mesh, weight part by part | (b) Parent each part to a bone |
|---|---|---|
| In the FBX | one skinned mesh, 15 bones | 22 rigid meshes, bones with no skin |
| In Roblox (expected, not checked in Studio) | one skinned MeshPart, one draw call | a MeshPart per part |
| Blending | possible where a part spans two bones | none: a part is rigid |
| Recolour or swap a part in Studio | no | yes |

**(a) is used.** The whole cat is one material over one palette texture, so one mesh costs one
draw call; the body carries the legs and spans three spine bones; and Roblox's influence rules
are about a skin, which (b) does not have. Choose (b) when parts must be swapped or recoloured
in the engine.

How the weights are set, before the join (joining merges vertex groups by name):

- **A separate part follows one bone** at weight 1: the face, ears and fur cheeks follow `Head`;
  the hat's three parts follow `Hat`; staff, crystal and spark follow `Prop`.
- **`Body` is weighted per ring**, not as one part. Each of its five cross-sections follows one
  spine bone: the two front rings `Chest`, the middle ring `Spine`, the two rear rings `Hips`.
  The body bends in the segments between rings, where the `Spine` and `Chest` bones pivot.
- **Paws follow the leg bones.** `build_cat.py` leaves the groups `Leg_FL`, `Leg_FR`, `Leg_BL`,
  `Leg_BR` on the Body (the four paw vertices of each leg); the rig renames them to its bones.
- **Shoulders blend.** The outer corners of a leg's top ring give 0.25 to the leg bone and keep
  0.75 on their spine bone, so the shoulder moves a little with the leg. The centre-line
  vertices, shared by the left and right legs, stay on the spine. Nothing can tear: the leg and
  the belly share those vertices.
- **`Cape`** follows the body's rings where it lies on the body, so the fur does not come
  through when the spine bends. Only the trailing hem section follows the `Cape` bone.
- A part the table does not name stops the script with a `KeyError`.

**One bone per leg, and why not two.** A v3 leg is two rings of vertices: the belly ring, which
is the body's own, and the paw. A lower-leg bone would own no vertex, so it could not bend
anything. The leg bone's rotation and location place the paw (in effect a foot target), and the
leg's sides stretch between belly and paw. Walk, run and attack read with that. Add an
upper and lower bone when the leg gets a knee loop, and split the weights by height then.

Other limits: `Neck` is a joint with no weights (the head sits straight on the body), and the
cape's trailing hem is one rigid ring, so in `Dead` one side of it stands up like a wing.

## The rig

```
Root (origin, no weights)
├─ Hips ── Spine ── Chest ── Neck ── Head ── Hat
│   │                 └─ Leg_F.L, Leg_F.R
│   ├─ Leg_B.L, Leg_B.R
│   ├─ Tail1 ── Tail2
│   └─ Cape
└─ Prop
```

Every bone lies along +Y, so a pose bone's axes are the world's: X pitches (a leg swings), Y
rolls, Z yaws (a tail sways). The cost is that bones do not point along the limbs in Blender's
viewport.

All actions are 24 fps and key location and rotation on every frame. A loop's last frame repeats
its first; play one frame less for a seamless loop.

| Action | Frames | Kind | What moves |
|---|---|---|---|
| `Idle` | 1–49 | loop | the chest rises 0.012 studs while the front paws stay down; the tail sways |
| `Walk` | 1–25 | loop | lateral sequence on the spot: back left, front left, back right, front right, a quarter cycle apart; hips bob, spine and tail sway, the staff hovers |
| `Run` | 1–17 | loop | a bound: front pair and back pair each together (left and right a beat apart), the spine sags when stretched in the air and arches when gathered, the body lifts 0.18 studs, cape and tail stream back, the staff flies alongside |
| `Attack` | 1–20 | one-shot | crouch back to frame 7, pounce by frame 10 with the right front paw raised and the staff swung forward, crystal first; held to frame 12; back to rest at 20 |
| `Dead` | 1–30 | one-shot | a stagger to frame 9, a fall onto its right side by frame 21, the staff falling back and the hat leaving the head to land in front; a small bounce, then held from frame 25 |

`Dead` does not move `Root`: the fall is on `Hips`, so the root stays where the game put the
character. The hat's fall is keyed in world space (`"world"` in the pose): the bone blends from
riding its parent to a fixed matrix on the ground, so it lands flat wherever the head ends up.

## Run and check

```bash
blender -b --factory-startup --python examples/wizard-cat/rig_wizard_cat.py -- --out examples/wizard-cat/rig
for f in rigged Idle Walk Run Attack Dead; do
  blender -b --factory-startup --python examples/wizard-cat/rig_wizard_cat.py -- --verify examples/wizard-cat/rig/wizard-cat-$f.fbx
done
```

The first builds the cat from the two build scripts, rigs it, and writes into `rig/`:

| File | Holds |
|---|---|
| `wizard-cat-rigged.blend` | the rig with all five actions; opens on `Idle` |
| `wizard-cat-rigged.fbx` | mesh, rig and all five actions as takes |
| `wizard-cat-<Action>.fbx` | mesh, rig and that one action. Roblox's importer may read one take per file, so there is one file per action |
| `<action>-fNN-<view>.png`, `rest-side.png` | key frames, 19 renders |
| `palette.png` | the texture, also embedded in every FBX |

A single-action file is exported from an NLA strip, so its take starts at time 0 like the takes
in the combined file. Every FBX is written with the armature at rest: Blender writes the bone
nodes from the pose at export time, and a loop's first frame is not the rest pose.

`--verify` opens one FBX in an empty Blender. The build and the verify print the same rows and
exit 1 when one fails:

| Row | Passes when |
|---|---|
| `root_bone` | one root bone, at 0, 0, 0 |
| `root_weights` | no vertex is weighted to it |
| `max_influences` | no vertex has more than 4 bone weights |
| `unweighted` | every vertex follows a bone |
| `rest_rotation`, `rest_scale` | every bone's rest matrix has rotation 0 and scale 1 |
| `fbx_bone_nodes` (verify) | the file holds 15 bone nodes and none has a rotation, pre-rotation or scale written on it |
| `actions` | exactly the expected actions with their frame ranges: all five in the combined file, the named one in a single-action file |
| `deforms` | over the whole action a vertex moves more than 0.01 and less than 4 studs from rest, and none goes more than 0.15 below the rest pose's lowest point |

Then open the renders. The numbers do not show a leg swinging the wrong way, a pounce that
reads as a stumble, or a cape cutting through the body.

Checked on Blender 5.3.0: the build and all six verifies pass. **Not checked in Roblox Studio.**
Still to confirm there: that the 3D Importer brings the mesh in as one skinned MeshPart, and
whether the Animation Editor's FBX import reads the combined file's takes or needs the
single-action files.
