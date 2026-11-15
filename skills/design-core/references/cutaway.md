# Cutaway: one picture into a 3D object that takes itself apart

The reference-first loop applied to a 3D build. One picture of a robotic animal, machine or
device goes in. What comes out is a three.js object written entirely in code, graded against
the picture, opened part by part under its own camera, and filmed frame by frame at 60 fps
with a procedural score on the same timeline. Adapted from
[Nyxera0x/cutaway](https://github.com/Nyxera0x/cutaway) (MIT), which builds on
[whaleyxbt/claude-motion](https://github.com/whaleyxbt/claude-motion) (MIT).

design-core holds the method. The runtime, capture, sound engine and the three example objects
(tarantula, piranha, wasp) live in the cutaway skill, so install that skill for the build.

**The default output is the interactive page**, driven by hand, built with design-core's
[`cutaway/`](../cutaway) modules, passed through `check_page.mjs` and handed over open. Rules and
structure: [The interactive page](#the-interactive-page-required). The MP4 and the score are
made only when the user asks for a video, a recording or sound.

## Setup

```
npx skills add Nyxera0x/cutaway -g -a claude-code
cd <installed cutaway folder> && npm install && npx playwright install chromium
```

Node.js 20+. The film needs `ffmpeg` on PATH and the score needs Python 3 (stdlib only).
`FFMPEG`, `PYTHON`, `CHROMIUM` override the binaries. `SKILL_DIR` below is the installed
cutaway folder. Output goes to `./cutaway-out` of the folder you run from.

Before the first object, read the cutaway skill's `docs/JOB_DESCRIPTION.md`, `CHECKLIST.md`,
`PROMPTS.md` and `LESSONS.md`. Copy `JOB_DESCRIPTION.md` into the work folder. Every correction
the user gives goes into it as one line.

## How it maps onto design-core

| design-core | In a cutaway |
|---|---|
| References carry the look ([reference-first.md](reference-first.md)) | Exactly **one** picture. Rebuild it in code; never import it as a texture or mesh. No picture: generate one with the prompt in `docs/PROMPTS.md`. |
| A bar per dimension ([cook-loop.md](cook-loop.md#3-the-bar-per-dimension)) | A **checklist of 10 to 12 numbered lines** for this picture, written before any code, graded yes / partial / no every round. |
| Fresh-context critic, side-by-side images | Stack reference \| still \| an approved still, plus the same stack at 900 px wide. Grade against the picture, never against your memory of the build. |
| Three static variants before app code | **A still before a film.** Stop after round 2 and show the user. Nothing is filmed until they say yes. |
| Layout before motion | Body before choreography: port the closest approved film 1:1 and change the body only. |
| A user's correction becomes a calibration offset | A correction becomes a line in `JOB_DESCRIPTION.md`, so the next object starts with it. |

## The order

1. **The picture.** One. Pick subjects with many joints, a dense core and one main set of
   limbs (legs, or wings, or tentacles). Smooth bodies (snakes, rays, shells) read as toys
   however many rounds they get.
2. **Measure it** before writing code. Body height, head length, jaw or limb length as shares of
   body length. Dark-pixel share (luma under 80) inside the subject's bounding box.
3. **Write the checklist.** Order: silhouette and view with the measured proportions, the
   signature feature, the second feature with a `NEVER` next to the default it fights, plates,
   eyes, the open or glass section in counts, limbs with thickness in numbers, small parts,
   accent placement, density at 900 px, and last, dark share ≥ 0.8 of the reference's.
   Every vague word gets a number.
4. **Still loop.** Build every part that will come apart as its own group with a named anchor.
   Render a still at 1600x900 posed like the picture, stack it, grade every line, measure dark
   share and proportions on both images and report them side by side. Fix the no's, then the
   partials. **Stop after round 2.**
5. **The film.** Port the example with the closest body: its beat times and moves, distances
   scaled. Give every part its own camera. Flag an object with no close body before starting;
   it costs about twice the rounds.
6. **The short version.** A 10-second film with its own script, opening and exit. Never cut
   pieces out of the long film.
7. **Hand over the page.** Build it with manual mode wired, review its frames, run
   `check_page.mjs` until it passes, then open it. The MP4 and the score are extras for a
   request that names a video; render and score them then.

## Measured checks

These are the checks that decide pass or fail. They exist because objects kept passing every
feature line while the whole read as a clean white diagram.

| Check | Pass |
|---|---|
| Dark share (luma < 80) in the bounding box | ≥ 0.8 of the reference's |
| Proportions (height, head, jaw or limb ÷ body length) | Within a few hundredths of the reference |
| Density at 900 px wide | Reads as dense as the approved still |
| Bristles, spikes | 0.15 to 0.25 of the limb's thickness |
| Size at rest | The object fills 60 to 70% of the 3D window; the part being opened fills the frame |

Raise dark share by breaking white surfaces into separate curved plates in 3 sizes with gaps
over the mechanism. Sprinkled dots don't count, and they read as polka dots.

## The look

- White clearcoat shells broken into plates; dark mechanism in two levels (big gears, rings,
  actuators, plus a couple of hundred small pistons, hoses and screws) showing through cut
  windows and clear glass.
- One accent colour, as lines and glows only (tips, rims, edges, joint rings, a bezel), and it
  marks what is moving right now. Never dots.
- Glowing parts sit inside the mechanism or behind glass, never on the surface.
- Eyes are glossy black lenses with a thin accent bezel. Membranes milky and frosted with thin
  veins. Every limb has its own pose and segment lengths.
- Near-white studio, soft floor shadow.

This is the cutaway house style. When the user's product has its own palette or materials,
those win (order of authority in [SKILL.md](../SKILL.md)); the measured checks still apply.

When the picture has warm materials (copper, brass, wood), skip the green look's `retint` on the object: it turns
every warm colour green. Build the accents green directly and retint only the lights.

## The film

- Frame 0 is the thumbnail: front 3/4 hero view, the object big and already moving.
- A part opens in about 1 s, holds with its parts still turning, closes in 0.5 s. A new beat
  every 2 to 3 s. Then a full explode on a turntable, a fast reassembly while it turns, an exit.
- Every beat gets its own side, height and distance, aimed at its part and pushing in while it
  hangs open: an eye in macro, a tail from behind, a back from above, a jaw from below. The
  camera never copies a wing beat or a footstep. Check with `sims/green/cam_track.mjs`: if
  azimuth, elevation and distance barely change between beats, the film looks parked.
- Only the part being opened has to stay in frame; the rest may run off.
- The page around it: an invented product name, one pill button per part that a cursor clicks,
  live cards that move with the parts, labels that never cover the part they name.
- On the live page the film hands over to the viewer: see
  [The interactive page](#the-interactive-page-required).
- Visible wing beats 1.5 to 2.5 Hz.

**`render(t)` is pure.** No `Math.random` (seeded `rng` at setup), no `Date`, no state between
frames. Anything integrated over time (a gait, a speed ramp) is tabulated at load. Every beat
lives in `<name>-film/timeline.json` in seconds; the picture and the score both read that file,
so the sound can't drift. A frame-by-frame render can't drop frames the way a screen recorder
does.

## The interactive page (required)

Every cutaway is handed over as a page the viewer drives by hand. A page that only plays the
film, or only jumps to beats, isn't done: it reads as "stuck" to anyone who clicks it.

**Behaviour, all required:**

| Input | What it does |
|---|---|
| Nothing yet | The film plays on a loop, the scripted cursor pressing the pills |
| A part's pill (click, Enter, space) or its number key | Takes over from the film's current frame (nothing jumps), then opens that part, or closes it if open. It stays as left, and parts combine |
| Drag on the object | Orbits (azimuth, elevation clamped −8° to 75°) |
| Scroll | Zooms (distance clamped) |
| Double-click | Eases back to the last opened part's beat camera |
| "Play film" | Hands back to the film from 0 |

While the viewer drives: every open part's pill is lit, the scripted cursor is hidden, the film
clock reads "Manual", and the hint bar says how to orbit and zoom. Parts that can't physically
stay out alone close together (`closes`: closing the cap closes the roll). Capture never enters
manual mode, so the film's `render(t)` stays pure.

**Structure.** One folder per object, the cutaway skill's split plus design-core's two modules:

| File | Job |
|---|---|
| `<object>.js` | The body from code; every part that comes apart is its own group with an anchor; `pose(state)` sets one moment |
| `tour.js` | The film as functions of t; exports its beat cameras, labels, status words and card readouts so manual mode reuses them |
| `main.js` | The page: stage, console, `makeManual(...)` + `attachManual(...)` under `if (!capture)`, `render(t)` taking `page.state(t, stateAt)` |
| `timeline.json`, `score.py` | The beats in seconds; the score on the same file |
| [`cutaway/manual.js`](../cutaway/manual.js) | Manual mode, object-agnostic: parts, cameras, labels, `closes`, `fromFilm`, `toState` come in as config |
| [`cutaway/interactive.js`](../cutaway/interactive.js) | The page wiring: pills as buttons, number keys, hint bar, "Play film", lit pills, the Manual clock; sets `window.CUTAWAY` |

Import the two modules by relative path from the object's folder; esbuild bundles them into the
one HTML file. The worked example's `main.js` is the reference wiring.

**The gate.** A page is handed over only after this passes:

```
CUTAWAY_DIR="$SKILL_DIR" node <design-core>/cutaway/check_page.mjs cutaway-out/dist/<name>.html --shots cutaway-out/check
```

It drives the page like a viewer: film playing, every pill opening its part, two parts open
together, drag, scroll, a number key, "Play film", no page errors. Exit 1 lists what failed. Read
its screenshots too. Then `open cutaway-out/dist/<name>.html` and tell the user what they can do
on it (click parts, drag, scroll, Play film).

## Sound

Synthesised in Python at 48 kHz from the same `timeline.json`, mastered to −14 LUFS with true
peak ≤ −2 dBFS. Accent, don't narrate: a quiet click per button press, a short accent on every
part that moves, continuous motion silent, one music bed under the whole film. Every time comes
from the timeline, never a typed number.

## Commands

```
node "$SKILL_DIR/sims/build.mjs" ./my-object             # one HTML, offline: the default output
CUTAWAY_DIR="$SKILL_DIR" node <design-core>/cutaway/check_page.mjs cutaway-out/dist/my-object.html
open cutaway-out/dist/my-object.html                      # hand it over open, once the check passes
# stills for review, and a video only when asked (upstream's examples shown):
node "$SKILL_DIR/sims/capture.mjs" piranha-film --size 1600x900 --dpr 1.2 --still 9.4 --out cutaway-out/still.png
node "$SKILL_DIR/sims/capture.mjs" piranha-film --size 1600x900 --dpr 1.2 --stills beats --cols 4 --out cutaway-out/beats.png
node "$SKILL_DIR/sims/capture.mjs" piranha-film --size 1600x900 --dpr 2.4 --out cutaway-out/film-4k.mp4
python "$SKILL_DIR/run_sfx.py" "$SKILL_DIR/sims/piranha-shared/score.py"
ffmpeg -y -i cutaway-out/film-4k.mp4 -i cutaway-out/piranha-score.wav -map 0:v -map 1:a \
  -vf scale=1920:1080:flags=lanczos -c:v libx264 -crf 16 -pix_fmt yuv420p \
  -c:a aac -b:a 256k -shortest -movflags +faststart cutaway-out/film.mp4
node "$SKILL_DIR/sheet.mjs" --video cutaway-out/film.mp4 --timeline <timeline.json>
```

**macOS:** upstream's `paths.mjs` sets an ANGLE backend only on Windows, and on macOS the headless shell then
can't create a WebGL context (capture times out waiting for `SIM.ready`). Add `'--use-angle=metal'` for `darwin` to
`CHROMIUM_ARGS`. A sandboxed shell blocks the GPU too, so run capture outside the sandbox.

`--size` is the CSS layout and `--dpr` multiplies it: 1600x900 at 2.4 renders 4K, scaled down to
1080p so thin veins stay sharp. Capture prints the GPU it got; a software renderer means the GPU
flags didn't take. A new object outside `SKILL_DIR` is a folder with a `main.js` importing
`cutaway-kit/runtime.js`, built with `node "$SKILL_DIR/sims/build.mjs" ./my-object`.

## Review

You can't watch the film; you can read frames. Never call it done without reading sheets of the
current render.

1. `--stills beats`: one tile per beat, 0.3 s after it. Read each against the checklist.
2. Zoom: `--stills every:0.2 --from A --to B` for a transition, `--still T` for one frame.
3. Check: every part goes back where it was, nothing passes through anything, cards match the
   motion, no leftover off-palette colour (`sims/green/probe_warm.mjs`), no parked camera.
4. Fix, rebuild, repeat until a full pass finds nothing. Then read the final `sheet.mjs` output.

Before showing a new film, put its frames at the same times next to the approved film's. Smaller,
flatter or blurrier doesn't ship.

## Worked example

[examples/lithium-cutaway](../examples/lithium-cutaway/README.md) benches this method on a lithium-ion cell icon:
the checklist, two still rounds with measurements (h/w 2.12 → 2.25 against 2.26, dark share 0.64 → 0.85 of the
reference), the line-by-line grades, the stop at the still gate, and the 18 s film with its score after approval.
A page that only holds the still looks broken to a viewer: say it is the gate, or show the stack image instead.

## Cost control

- Two objects at a time at most, reviewed after round 2. A note after round 2 changes the
  outcome; after round 6 it only costs tokens (one dropped object ate about 430k).
- The still gate is the cheapest place to say no.

## three.js traps

- An HDR glow colour above 1 breaks `getHSL`; read and write it at unit peak.
- A colour the pose rewrites every frame comes back every frame; retint after each pose.
- Vertex-colour attributes ignore the material colour; retint them too.
- `smoothstep(a, b, x)` with `a > b` returns 0 on ANGLE/D3D; write `1.0 - smoothstep(b, a, x)`.
- One NaN pixel blacks out the whole frame through bloom; clamp every `pow()` base in shaders.
