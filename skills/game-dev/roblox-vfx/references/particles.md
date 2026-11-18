# ParticleEmitter reference

Adapted from [nonlooped/roblox-suite@fc1c3dd](https://github.com/nonlooped/roblox-suite/tree/fc1c3dd26fef67ee4d7b6e20b1299b44fc6101ae/roblox-vfx) (MIT, © 2026 nonlooped).

Condensed from the Roblox docs (create.roblox.com/docs/effects/particle-emitters) via the source
above. Read the class page for any property not listed. The rules are in [`../SKILL.md`](../SKILL.md).

## Emission

| Property | Notes |
|---|---|
| `Enabled` | stops new particles; live ones finish. `:Clear()` removes them |
| `Rate` | particles/s; ~400 desktop, ~100 mobile per emitter |
| `Emit(n)` | one burst of `n`, regardless of `Rate`. For a one-shot: `Rate = 0`, then `Emit` |
| `Lifetime` | NumberRange, random per particle; capped at 20 s |
| `Speed` | birth velocity, studs/s (range); negative goes backward. Only affects new particles |
| `SpreadAngle` | Vector2 degrees off the emission direction |
| `EmissionDirection` | which part face emits; **ignored under an Attachment** (rotate the Attachment) |

## Appearance

| Property | Notes |
|---|---|
| `Texture` | PNG with alpha. Grayscale + `LightEmission = 1` drops the dark areas |
| `Color` | ColorSequence over the life; one Color3 is stored as a one-key sequence |
| `Size` | NumberSequence; envelope (the pink band) gives per-particle variation |
| `Transparency` | NumberSequence; fade in and/or out |
| `Squash` | NumberSequence; positive tall and thin, negative wide and flat |
| `Rotation`, `RotSpeed` | start angle and spin, degrees (ranges); negative is counter-clockwise |

Size and Transparency are read over each particle's own life (0 to 1).

## Motion

| Property | Notes |
|---|---|
| `Acceleration` | Vector3 velocity change per second: gravity `(0, -30, 0)`, a draft `(0, 4, 0)`. Also moves live particles |
| `Drag` | speed loss; higher stops sooner |
| `WindAffectsDrag` | with global wind on and `Drag > 0`, wind pushes the particles |
| `VelocityInheritance` | 0-1 share of the parent's velocity given to new particles |
| `LockedToPart` | particles follow the emitter as it moves |
| `TimeScale` | 0-1 speed of this emitter, for slow motion without retuning |
| `Orientation` | `FacingCamera`, `FacingCameraWorldUp`, `VelocityParallel` (streaks, sparks, rain), `VelocityPerpendicular` |

## Shape

| Property | Values |
|---|---|
| `Shape` | Box, Sphere, Cylinder, Disc |
| `ShapeStyle` | Volume (anywhere inside) or Surface (the skin only) |
| `ShapeInOut` | Outward, Inward, InAndOut |
| `ShapePartial` | Cylinder: radius on the emission side. Disc: inner-radius share, `0` closed, `1` rim only. Sphere: `1` full, `0.5` half-dome, `0` a point |

Sphere and Cylinder render wrong when the parent is an Attachment: use a small invisible part.

## Flipbook

Atlas as a grid (power-of-two size, 2x2, 4x4, 8x8 or Custom via `FlipbookSizeX/Y`), with transparent
gaps between frames because of mipmaps.

| Property | Notes |
|---|---|
| `FlipbookLayout` | the grid |
| `FlipbookFramerate` | number or range, max 30 |
| `FlipbookMode` | `Loop`, `OneShot` (ignores framerate, plays once over `Lifetime`; explosions), `PingPong`, `Random` |
| `FlipbookBlendFrames` | crossfade neighbours in Loop, OneShot, PingPong |
| `FlipbookStartRandom` | random first frame; with framerate 0 gives static but varied (leaves, debris) |

Atlases cost memory: reuse them, and preload (`ContentProvider:PreloadAsync`). Older phones disable
flipbooks.

## Lighting and layering

| Property | Notes |
|---|---|
| `LightEmission` | 0 normal blend, 1 additive: glows in the dark |
| `LightInfluence` | 0 ignores world light, 1 fully lit |
| `Brightness` | scales the light the emitter gives when `LightInfluence` is 0; no effect at 1 |
| `ZOffset` | render order in studs, to layer emitters without moving them |

## Performance

- Fill rate and overdraw are the cost: `Rate × Size × opacity × overlap`. Cut size and overlap
  before rate.
- Many large transparent emitters get throttled on weak clients.
- Measure: View → Stats → GPU → Fill Rate; Render → Overdraw; at lowest and highest quality.
- A strong effect is 2-5 emitters on one Attachment: core, smoke, sparks, glow; layer with `ZOffset`.

## Recipes (starting values, then tune by looking)

| Effect | Key values |
|---|---|
| Fire | `Rate` 40-80, `Lifetime` 0.6-1.2, `Speed` 2-5, `Acceleration` (0, 4, 0), `Size` shrinking to 0, `Color` yellow to dark red, `Transparency` 0.2 to 1, `LightEmission` 1; a Loop flipbook if you have one |
| Smoke | `Rate` 10-20, `Lifetime` 3-6, `Speed` 1-3, `Size` growing 2 to 8, `Transparency` 1 to 0.6 to 1, `LightEmission` 0, `LightInfluence` 1, `Drag` 1 + `WindAffectsDrag`, slow `RotSpeed` |
| Sparks | `Emit` 15-30, `Lifetime` 0.3-0.8, `Speed` 20-50, wide `SpreadAngle`, `Acceleration` (0, -60, 0), `Orientation` VelocityParallel, `Size` 0.3, `LightEmission` 1 |
| Impact burst | `Emit` 10-25, `Lifetime` 0.4-0.8, Disc shape Outward, `Speed` 10-20, `Drag` 4, `Size` 1 to 5, `Transparency` 0.3 to 1 |
| Ground dust | as impact burst, `LightEmission` 0, `LightInfluence` 1, earth `Color`, `Acceleration` (0, 2, 0) |
| Aura | `Rate` 20-30, `Lifetime` 1-2, Cylinder Surface on an invisible part, `LockedToPart`, `Speed` 0-1, `Acceleration` (0, 3, 0), `LightEmission` 1 |
| Rain | `Rate` 150-300, `Lifetime` 1-2, `Speed` 60, `Acceleration` (0, -40, 0), `Orientation` VelocityParallel, `Squash` tall, `Transparency` 0.6; Box shape above the camera, spawned near the camera only |
