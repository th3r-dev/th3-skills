"""Score for the LITHE LC-21 film (lithium-cutaway): a bed in E minor at 96 bpm (Em9, Cmaj7, Am9, B7sus: e-piano,
bass, soft drums, a pad) at one level the whole way, a quiet click on every button press, and a short accent on
every part that moves: a lift and a seat for the cap stack, a slide for the wrap, a run of ticks as the roll's layers
telescope, a thin rising tone as the pin draws out, a whoosh into the explode and three clicks as the cell seats.
Continuous motion stays silent. Every time comes from timeline.json.

    TL=<this folder>/timeline.json python "$SKILL_DIR/run_sfx.py" <this folder>/score.py
"""

import os

from sfx.score_kit import airy, bed, chords, hz, thud
from sfx.synth import blip, click, envelope, pad

TIMELINE = os.environ.get("TL", os.path.join(os.path.dirname(os.path.abspath(__file__)), "timeline.json"))
OUT = os.environ.get("OUT", os.path.join(os.environ.get("CUTAWAY_OUT", "cutaway-out"), "lithium-score.wav"))
TARGET_LUFS = -14.0
SEED = 21

CHORDS = chords("Em9:E3 G3 B3 D4 F#4/E2", "Cmaj7:C3 E3 G3 B3 E4/C2", "Am9:A2 C3 E3 G3 B3/A1", "B7sus:B2 E3 F#3 A3 D4/B1")
MOTIF = [(0.5, hz("B5")), (1.5, hz("G5")), (2.5, hz("F#5"))]


def seat(mix, t, level=0.05, pan=0.0):
    """A part landing home: a short click on a soft low knock."""
    mix.put(t, click(1700, 0.03), level, pan=pan)
    mix.put(t, thud(120, 0.06, 0.25), level * 0.5, pan=pan)


def score(mix, tl):
    dur = tl["duration"]
    left, right, low, drums = bed(dur, 96, CHORDS, MOTIF, motif_voice="blip", kicks=(0, 2.5), snares=(1, 3), hats=8, swing=0.06, keys_vel=0.72, keys_lp=3400)
    mix.put_stereo(0, left, right, 0.13)
    mix.put(0, low, 0.13)
    mix.put(0, drums, 0.05)
    bar = 4 * 60 / 96
    changes = [(0.12 + b * bar, list(CHORDS[b % len(CHORDS)][0][:4])) for b in range(int(dur / bar) + 1)]
    pl, pr = pad(dur, changes, volume=envelope([(0, 0), (1.0, 1), (dur - 1.6, 1), (dur, 0)]), detune=0.8, tremolo=0.18, xfade=0.5)
    mix.put_stereo(0, pl, pr, 0.07)

    script = sorted(tl["script"], key=lambda e: e["t"])
    for i, e in enumerate(script):
        t, act = e["t"], e["act"]
        close = (script[i + 1]["t"] if i + 1 < len(script) else dur) - 0.6
        mix.put(t, click(2400, 0.025), 0.055, pan=0.45)
        if act == "cap":
            mix.put(t + 0.1, airy(0.7, 900, 2200, 0.5), 0.014, pan=0.1)
            seat(mix, close + 0.5, 0.045)
        elif act == "sleeve":
            mix.put(t + 0.1, airy(0.9, 500, 1400, 0.6), 0.016, pan=-0.3)
            seat(mix, close + 0.5, 0.04, pan=-0.2)
        elif act == "roll":
            for k in range(8):
                mix.put(t + 0.15 + k * 0.09, click(3200 - k * 120, 0.012), 0.022, pan=0.2)
            seat(mix, close + 0.5, 0.04)
        elif act == "mandrel":
            mix.put(t + 0.1, blip(hz("E6"), 0.5), 0.012, pan=0.0)
            seat(mix, close + 0.5, 0.045)
        elif act == "exploded":
            mix.put(t + 0.05, airy(1.6, 300, 1800, 0.7), 0.03, pan=0.0)
        elif act == "assemble":
            for k in range(3):
                seat(mix, t + 0.45 + k * 0.22, 0.045, pan=(-0.3, 0.0, 0.3)[k])
