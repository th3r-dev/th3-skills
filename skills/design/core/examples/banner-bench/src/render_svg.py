"""Render an SVG to PNG at full size and at icon size (Chromium via Playwright).
Usage: render_svg.py in.svg out.png [--width 1280 --height 640]"""
import argparse, pathlib, tempfile
from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser()
ap.add_argument("svg"); ap.add_argument("png")
ap.add_argument("--width", type=int, default=1280); ap.add_argument("--height", type=int, default=640)
a = ap.parse_args()
url = pathlib.Path(a.svg).resolve().as_uri()
with tempfile.TemporaryDirectory() as tmp, sync_playwright() as p:
    b = p.chromium.launch()
    for w, h, out in ((a.width, a.height, a.png), (a.width // 8, a.height // 8, a.png.replace(".png", "-icon.png"))):
        page_file = pathlib.Path(tmp, f"{w}.html")
        page_file.write_text(f'<html><body style="margin:0"><img src="{url}" style="width:{w}px;height:{h}px;display:block"></body></html>')
        pg = b.new_page(viewport={"width": w, "height": h})
        pg.goto(page_file.as_uri())
        pg.wait_for_load_state("load")
        pg.screenshot(path=out)
        print("wrote", out)
    b.close()
