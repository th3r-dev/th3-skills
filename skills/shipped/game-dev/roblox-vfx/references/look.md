# The look: layers, light, timing

Based on lef's **Roblox VFX Design** guide,
[Wongsakorn-krub/SKILL_AI_VFXROBLOX@7d42130](https://github.com/Wongsakorn-krub/SKILL_AI_VFXROBLOX/blob/7d4213017038899d895374cf0f59801fc957af84/SKILL_VFX.md).
The repo states no licence, so this file links to it and restates its ideas; it copies none of
its tables or texture IDs. Read the guide for the measured values and the full recipes.

The guide's numbers come from one creator's study of three template packs (anime-style combat
bursts and character auras). They are starting points to look at, not Roblox defaults.

The rules are in [`../SKILL.md`](../SKILL.md); properties in [`particles.md`](particles.md); the
`Effect` class that plays a layered template in [`abilities.md`](abilities.md).

## One effect, many layers, one role each

A strong hit is many emitters (often 10-30), each doing one job. Pick the `Orientation` by the role:

| Role | `Orientation` | What it adds |
|---|---|---|
| Flash, glint, glow | `FacingCamera` | the first frame; scale |
| Rings, crescents, ground marks | `VelocityPerpendicular` | the shape and direction: the main structure, often half the layers |
| Sparks, streaks, needles, flames | `VelocityParallel` | speed |
| Debris, smoke puffs | `FacingCamera` (`FacingCameraWorldUp` to stay upright) | weight, the aftermath |
| Black layer | same as the layer it shadows | the silhouette that reads in daylight |

Signature shape per element: fire licks, lightning zigzags, wind is thin crescents, darkness is
mostly black layers. Sharp, tapered, high-contrast textures read better than soft round glows.

## Three stages

| Stage | Time | Layers |
|---|---|---|
| Flash | 0-0.1 s | a flash that shrinks to nothing, glints, a black impact frame |
| Impact | 0.1-0.4 s | rings, crescents, sparks |
| Residue | 0.5-4 s | smoke, dust, ground marks, falling debris |

Scale comes from the flash and the smoke, not from long lifetimes. A multi-hit repeats the impact
group at later `EmitDelay`s, then ends on the residue.

## Light and colour

- **Textures are white or grey; colour comes from `Color`.** One template then serves every
  element through a tint.
- `LightInfluence = 0`: the effect ignores the scene's light.
- `LightEmission = 1` (additive) washes out to white against a bright sky. Alone, it fails in daylight.
- `Brightness` picks the result: low reads dark, moderate (around 8-14) reads saturated, very high
  (40+) blooms to white. Keep only 1-2 core layers that bright; an orange layer at high brightness
  looks yellow-white.
- Bloom makes the core glow. Test with the game's own `Lighting` Bloom; the guide's reference scene
  used `Threshold` 2.
- The guide records **negative `LightEmission`** values that give opaque colour with dark edges.
  The API page documents 0-1 only: set one, read it back in Studio and look before relying on it
  (UNVERIFIED here).
- One hue per effect, varied in saturation and value. Gradients mostly run bright to dark.

## Black layers

The coloured layer is the glow; the black layer is the shape around it.

- Same texture as the coloured layer, made black by `Brightness = 0` or `Color` black.
- A bit larger than the coloured layer gives an outline; at the same size it gives weight.
- Thinner than the coloured layer (a lower `Rate` or count), or it smothers it.
- A near-black of the same hue is a softer alternative.
- Tag it `NoColor` so a tint leaves it black.

## Curves and motion

- **Size eases out**: fast growth, then a slow finish. Never linear. A flash does the reverse:
  large to 0 within ~0.1 s.
- Transparency: in fast, hold, fade (smoke); or opaque until the last third (most bursts); a flash
  is too short to need a fade.
- High `Speed` with high `Drag` gives a punch: a hard launch and a sudden stop.
- Negative `Acceleration.Y` for debris; a strong positive one for aura flames that shoot up and vanish.
- Fast `RotSpeed` (hundreds of degrees/s) on impact crescents and rings.

## Bursts versus auras

| | Burst | Aura |
|---|---|---|
| `Enabled` | false, played by `Emit` | true, `Rate` |
| Lifetime | mostly under 0.3 s | short (under ~1 s), emitted continuously |
| Attributes | `EmitCount`, `EmitDelay` | none: an `EmitCount` makes a continuous emitter fire once |
| Attach | a holder part at the hit `CFrame` | Attachments on the rig (hands, root), `LockedToPart` for half of them |

Large auras use rings several times the character's size with short lifetimes, so they pulse.

## Pitfalls

- `VelocityPerpendicular` at `Speed` 0 may not show: give it a tiny speed (0.01).
- A double-ended needle texture on `VelocityParallel` can render sideways: set `Rotation` 90.
- A ground layer with negative `ZOffset` sinks under the floor: raise its Attachment slightly instead.
- A flipbook sheet without its `FlipbookLayout` shows every cell at once.

## Designing a new effect

1. Write its story in one sentence ("the ground tears open, then seals").
2. Time the three stages.
3. Give each layer one role; pick 1-2 signature shapes.
4. Light: 1-2 bright cores, saturated colour layers, black layers.
5. Set `EmitCount`/`EmitDelay` per emitter; tag black layers and white flashes `NoColor`.
6. Look at it in daylight with Bloom, then tinted to a second colour.

## Inspecting it

Real-time playback hides a 0.05 s flash, and MCP `screen_capture` lags ~1-2 s. Freeze first:

1. Play the effect on a preview stage away from gameplay. Note the camera and `Lighting` settings
   so they can be restored.
2. After X seconds, set `TimeScale = 0` on every emitter and cancel pending `EmitDelay`s.
3. `screen_capture`. Repeat for X in the flash, the impact and the residue.
4. To isolate a group (perpendicular, parallel, camera-facing, black), clone the template, delete
   the other emitters, and emit.
5. Hold the view with `Camera.CameraType = Scriptable`; restore it afterwards.

Report what was built and looked at. "Matches the reference" needs the same textures, templates
and scene settings, compared in Studio.
