# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy==2.3.4", "pillow==12.0.0"]
# ///
"""How far apart the banners of each version are (higher = the runs converged less).

Usage: uv run src/spread.py round1   (reads <run>-<version>.png in that folder; render them first)
pixel: mean absolute difference of 64x32 thumbnails, per pair.
hue: half the L1 distance between 12-bin hue histograms of the saturated pixels, per pair."""
import itertools
import sys
from pathlib import Path

import numpy as np
from PIL import Image


def thumb(p):
    return np.asarray(Image.open(p).convert("RGB").resize((64, 32)), dtype=float) / 255


def hues(p):
    h, s, v = np.asarray(Image.open(p).convert("HSV").resize((128, 64))).reshape(-1, 3).T
    hist = np.histogram(h[(s > 60) & (v > 60)], bins=12, range=(0, 256))[0].astype(float)
    return hist / hist.sum() if hist.sum() else hist


groups = {}
for png in sorted(Path(sys.argv[1]).glob("*-*.png")):
    if png.stem != "sheet":
        groups.setdefault(png.stem.split("-", 1)[1], []).append(png)
for version, pngs in groups.items():
    pairs = list(itertools.combinations(pngs, 2))
    px = np.mean([np.abs(thumb(a) - thumb(b)).mean() for a, b in pairs])
    hu = np.mean([0.5 * np.abs(hues(a) - hues(b)).sum() for a, b in pairs])
    print(f"{version}\truns={len(pngs)}\tpixel={px:.3f}\thue={hu:.3f}")
