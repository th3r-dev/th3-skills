"""Measure a still against the reference, the cutaway way: dark share and proportions inside the subject's box.

    python measure.py REF.png STILL.png [--crop x0,y0,x1,y1]   (crop: the 3D window of a page still)
    python measure.py --selftest

The subject is every pixel that differs from the background (sampled at the corners of the crop) by more than
BG_TOL. Dark share = pixels with luma < 80 inside the subject box / box area. Needs Pillow and numpy.
"""

import sys

import numpy as np
from PIL import Image

BG_TOL = 24
DARK = 80


def stats(img, crop=None):
    a = np.asarray(img.convert("RGB"), dtype=np.float32)
    if crop:
        x0, y0, x1, y1 = crop
        a = a[y0:y1, x0:x1]
    bg = np.median(np.concatenate([a[:8, :8].reshape(-1, 3), a[:8, -8:].reshape(-1, 3)]), axis=0)
    fg = np.abs(a - bg).max(axis=2) > BG_TOL
    ys, xs = np.nonzero(fg)
    if not len(xs):
        raise SystemExit("no subject found")
    box = a[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1]
    luma = box @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    g = box[..., 1] - np.maximum(box[..., 0], box[..., 2])
    h, w = box.shape[:2]
    return {"h/w": h / w, "dark": float((luma < DARK).mean()), "green": float((g > 60).mean()), "box": (w, h)}


def report(ref, still, crop=None):
    r, s = stats(Image.open(ref)), stats(Image.open(still), crop)
    print(f"{'':8}{'ref':>8}{'still':>8}  pass")
    print(f"{'h/w':8}{r['h/w']:8.3f}{s['h/w']:8.3f}  {'yes' if abs(r['h/w'] - s['h/w']) <= 0.05 * r['h/w'] else 'no'}")
    print(f"{'dark':8}{r['dark']:8.3f}{s['dark']:8.3f}  {'yes' if s['dark'] >= 0.8 * r['dark'] else 'no'} (ratio {s['dark'] / r['dark']:.2f}, needs 0.80)")
    print(f"{'green':8}{r['green']:8.3f}{s['green']:8.3f}  (info)")
    return r, s


def selftest():
    im = Image.new("RGB", (200, 200), (247, 249, 248))
    px = im.load()
    for x in range(50, 150):
        for y in range(20, 180):
            px[x, y] = (20, 20, 20) if x < 75 else (200, 200, 200)
    s = stats(im)
    assert abs(s["h/w"] - 1.6) < 1e-6, s
    assert abs(s["dark"] - 0.25) < 1e-6, s
    print("selftest ok")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        args = [a for a in sys.argv[1:] if not a.startswith("--")]
        crop = None
        if "--crop" in sys.argv:
            crop = tuple(int(v) for v in sys.argv[sys.argv.index("--crop") + 1].split(","))
            args.remove(sys.argv[sys.argv.index("--crop") + 1])
        report(*args[:2], crop)
