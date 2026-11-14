"""Drift check for every hero SVG: render each at the same point of loop 1 and loop 4; identical pixels = no drift.

Run from the repo root: ~/.venvs/diagram-design/bin/python assets/check_heroes.py
"""
import sys, pathlib, re
from playwright.sync_api import sync_playwright
files = sorted(pathlib.Path("skills").glob("*/assets/hero.svg")) + [pathlib.Path("assets/hero.svg")]
bad = 0
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width":1280,"height":720})
    for f in files:
        svg = f.read_text()
        loops = set(re.findall(r"animation:\w+ ([0-9.]+)s \S+(?: ([0-9.]+)s)? infinite", svg))
        cycles = {float(c) for c, _ in loops}; delays = {float(d or 0) for _, d in loops}
        assert len(cycles) == 1 and len(delays) == 1, (f, loops)
        c, delay = cycles.pop(), delays.pop()
        pg.goto(f.resolve().as_uri()); pg.wait_for_timeout(150)
        same = []
        for frac in (0.15, 0.45, 0.8):
            h = []
            for loop in (0, 3):
                pg.evaluate("t=>document.getAnimations().forEach(a=>{a.pause();a.currentTime=t})",
                            (delay + (loop + frac) * c) * 1000)
                h.append(pg.screenshot())
            same.append(h[0] == h[1])
        bad += not all(same)
        print(f"{'OK   ' if all(same) else 'DRIFT'} {f}  cycle {c}s  delay {delay}s")
    b.close()
print("drift-free:", bad == 0); sys.exit(bad)
