# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright==1.62.0"]
# ///
"""Bench a banner SVG: export PNGs and run the principles.md tests that a script can measure.

  safe zone    every [data-zone=core] box is >= MARGIN px from each edge
  contrast     every <text> fill vs the nearest data-bg behind it, >= 4.5:1 (>= 3:1 at 24px+ bold)
  type size    smallest text >= 14px per 1280px of width; core text >= 10px at phone width (400px),
               which is the 32px headline minimum at 1280
  file size    the 1x PNG is under --max-kb (default 1024: GitHub's social preview; Roblox takes 3000)
  bottom band  with --bottom N, no text in the bottom N px (Roblox lays the player count over it)
  overlap      no two lines of text drawn over each other

Writes <name>.png (1x), <name>@2x.png, <name>-400.png (two-second test) and <name>-crop.png
(the 1.91:1 link-unfurl crop) next to the SVG, for the eye checks: grayscale and spelling stay human.

Run: uv run bench.py banner.svg [--margin N] [--bottom N] [--max-kb N]   exit code = number of failures
"""
import argparse, pathlib, sys
from playwright.sync_api import sync_playwright


def lum(hex_):
    c = [int(hex_.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def ratio(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


assert round(ratio("#000000", "#FFFFFF"), 1) == 21.0 and round(ratio("#777777", "#FFFFFF"), 2) == 4.48

MEASURE = """() => {
  const svg = document.querySelector('svg');
  const W = svg.viewBox.baseVal.width, H = svg.viewBox.baseVal.height;
  // canvas units, after every transform: a layout drawn at 1280 and scaled to 1920 measures as 1920
  const r = svg.getBoundingClientRect(), k = W / r.width;
  const core = [...svg.querySelectorAll('[data-zone=core]')].map(g => { const b = g.getBoundingClientRect();
    return [(b.left - r.left) * k, (b.top - r.top) * k, (b.right - r.left) * k, (b.bottom - r.top) * k]; });
  // decorative text (a riso misregistration, a watermark) is art, not copy: no contrast or size rules
  const texts = [...svg.querySelectorAll('text')].filter(t => !t.closest('[data-zone=decor]')).map(t => ({
    s: t.textContent, fill: t.getAttribute('fill'), size: +t.getAttribute('font-size') * Math.hypot(t.getScreenCTM().a, t.getScreenCTM().b) * k, w: +t.getAttribute('font-weight'),
    bg: t.closest('[data-bg]').getAttribute('data-bg'), core: !!t.closest('[data-zone=core]'),
    box: (b => [(b.left - r.left) * k, (b.top - r.top) * k, (b.right - r.left) * k, (b.bottom - r.top) * k])(t.getBoundingClientRect()) }));
  return {W, H, core, texts};
}"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("svg")
    ap.add_argument("--margin", type=int, help="edge band in px (default 5%% of the width: 64 at 1280)")
    ap.add_argument("--clear", help="cx,cy,r in canvas px: a circle the platform covers (an avatar); no text may touch it")
    ap.add_argument("--safe-ratio", help="a crop the platform shows, e.g. 4:3 (Fastwork's service card): core "
                                         "content must sit inside the centred crop, and a -safe.png preview is written")
    ap.add_argument("--bottom", type=int, default=0, help="a band in px along the bottom edge the platform covers "
                                                         "(Roblox's player count: 120 at 1080); no text may enter it")
    ap.add_argument("--max-kb", type=int, default=1024, help="the 1x PNG's limit (default 1024, GitHub; Roblox: 3000)")
    a = ap.parse_args()
    src = pathlib.Path(a.svg).resolve()
    stem = src.with_suffix("")
    fails = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.goto(src.as_uri())
        err = pg.evaluate("() => { const e = document.querySelector('parsererror'); return e ? e.textContent.slice(0, 200) : null; }")
        if err:                                  # a broken SVG still half-renders in Chromium; never pass it
            print(f"{src.name}: not well-formed XML: {err}")
            return 1
        m = pg.evaluate(MEASURE)
        W, H = int(m["W"]), int(m["H"])
        for scale, suffix in ((1, ""), (2, "@2x")):
            pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=scale)
            pg.goto(src.as_uri()); pg.wait_for_timeout(200)
            pg.screenshot(path=f"{stem}{suffix}.png")
        pg = b.new_page(viewport={"width": 400, "height": round(400 * H / W)})
        pg.goto(src.as_uri())
        pg.evaluate("w => { const s = document.querySelector('svg'); s.setAttribute('width', w); s.removeAttribute('height'); }", 400)
        pg.wait_for_timeout(200)
        pg.screenshot(path=f"{stem}-400.png")
        cw = min(round(H * 1.91), W)          # link unfurlers show 1.91:1, centred
        pg = b.new_page(viewport={"width": cw, "height": H})
        pg.goto(src.as_uri())
        pg.evaluate("x => document.querySelector('svg').style.transform = `translateX(${-x}px)`", (W - cw) // 2)
        pg.wait_for_timeout(200)
        pg.screenshot(path=f"{stem}-crop.png")
        if a.safe_ratio:
            ra, rb = (int(v) for v in a.safe_ratio.split(":"))
            sw, sh = min(round(H * ra / rb), W), min(round(W * rb / ra), H)   # a tall crop cuts the sides, a wide one the top and bottom
            pg = b.new_page(viewport={"width": sw, "height": sh})
            pg.goto(src.as_uri())
            pg.evaluate("([x, y]) => document.querySelector('svg').style.transform = `translate(${-x}px, ${-y}px)`", [(W - sw) // 2, (H - sh) // 2])
            pg.wait_for_timeout(200)
            pg.screenshot(path=f"{stem}-safe.png")
        b.close()

    # with a platform crop, the crop is what people see: size and margin rules are measured against it
    SW, SH = W, H
    if a.safe_ratio:
        ra, rb = (int(v) for v in a.safe_ratio.split(":"))
        SW, SH = min(round(H * ra / rb), W), min(round(W * rb / ra), H)
    mg = a.margin if a.margin is not None else round(SW * 0.05)
    small_min = 14 * SW / 1280     # 14px at 1280, scaled with what is shown
    left, right = (W - SW) / 2, (W + SW) / 2    # the visible span; the edge band applies inside it
    top_, bot = (H - SH) / 2, (H + SH) / 2
    vm = mg if SH == H else round(SH * 0.05)
    for x0, y0, x1, y1 in m["core"]:
        if x0 < left + mg or y0 < top_ + vm or x1 > right - mg or y1 > bot - vm:
            fails.append(f"core box ({x0:.0f},{y0:.0f})-({x1:.0f},{y1:.0f}) is outside the safe area"
                         + (f" of the {a.safe_ratio} crop" if a.safe_ratio else f" ({mg}px edge band)"))
    worst = min(m["texts"], key=lambda t: ratio(t["fill"], t["bg"]))
    for t in m["texts"]:
        need = 3.0 if t["size"] >= 24 and t["w"] >= 700 else 4.5
        r = ratio(t["fill"], t["bg"])
        if r < need:
            fails.append(f"contrast {r:.2f} < {need} for {t['s']!r} ({t['fill']} on {t['bg']})")
        if t["size"] < small_min - 0.01:
            fails.append(f"{t['s']!r} is {t['size']:.1f}px, under {small_min:.0f}px")
        if t["core"] and t["size"] * 400 / SW < 10:
            fails.append(f"core text {t['s']!r} is {t['size'] * 400 / SW:.1f}px at phone width")
    # two lines of text drawn over each other. A text box is the font's whole line box, mostly empty above
    # and below the letters (Kanit at 150px is far taller than its glyphs), so compare the middle half,
    # where the letters sit
    core = lambda b: (b[0], b[1] + (b[3] - b[1]) / 4, b[2], b[3] - (b[3] - b[1]) / 4)
    T = m["texts"]
    for i in range(len(T)):
        for j in range(i + 1, len(T)):
            a1, b1 = core(T[i]["box"]), core(T[j]["box"])
            ox = min(a1[2], b1[2]) - max(a1[0], b1[0])
            oy = min(a1[3], b1[3]) - max(a1[1], b1[1])
            if ox > 6 and oy > 2:
                fails.append(f"text overlaps: {T[i]['s']!r} and {T[j]['s']!r}")
    if a.clear:                      # nothing readable under an avatar or other overlay
        ccx, ccy, cr = (float(v) for v in a.clear.split(","))
        for t in m["texts"]:
            x0, y0, x1, y1 = t["box"]
            nx, ny = min(max(ccx, x0), x1), min(max(ccy, y0), y1)
            if (nx - ccx) ** 2 + (ny - ccy) ** 2 < cr ** 2:
                fails.append(f"{t['s']!r} sits under the covered circle {a.clear}")
    if a.bottom:
        fails += [f"{t['s']!r} reaches into the bottom {a.bottom}px band" for t in m["texts"] if t["box"][3] > H - a.bottom]
    kb = pathlib.Path(f"{stem}.png").stat().st_size / 1024
    if kb >= a.max_kb:
        fails.append(f"{stem.name}.png is {kb:.0f} KB, over {a.max_kb} KB")

    small = min(t["size"] for t in m["texts"] if t["core"]) * 400 / SW
    print(f"{src.name}: {W}x{H}, {len(m['core'])} core boxes, {len(m['texts'])} texts")
    print(f"  worst contrast {ratio(worst['fill'], worst['bg']):.2f}:1 ({worst['s']!r})")
    print(f"  smallest core text at 400px wide: {small:.1f}px")
    print(f"  PNG 1x: {kb:.0f} KB")
    for f in fails:
        print("  FAIL", f)
    print("bench:", "pass" if not fails else f"{len(fails)} failures")
    return len(fails)


if __name__ == "__main__":
    sys.exit(main())
