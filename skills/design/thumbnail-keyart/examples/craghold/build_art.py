#!/usr/bin/env python3
"""The scenes behind the Craghold thumbnails, as vector art (the image model was out of quota).

No text in the art: the title, ribbon and callouts are live text added by banner.py's keyart layout,
so they stay spellable and the bench can measure them.

  dungeon  the hero runs the bridge toward the gate; the first enemy behind; the key glows in the arch
  summit   the same hero and bridge, the path climbing to a flag on the snow peak

Run: python3 build_art.py            writes art-dungeon.svg and art-summit.svg next to this file
     python3 build_art.py --selftest
Stdlib only.
"""
import math, os, random, sys

W, H = 1920, 1080
HERE = os.path.dirname(os.path.abspath(__file__))


def ridge(peaks, base, x0=0, x1=W, col=32, step=24):
    """Column tops of a blocky range: the highest of a few smooth peaks, snapped to a voxel grid."""
    tops = []
    for x in range(x0, x1, col):
        y = base
        for px, py, spread in peaks:
            y = min(y, py + (base - py) * min(1, ((x + col / 2 - px) / spread) ** 2))
        tops.append((x, round(y / step) * step))
    return tops


def range_svg(tops, base, rock, lip, snow, snow_below, col=32, rnd=None):
    """One rect per column plus a lighter lip on every step; snow only above `snow_below`, so the cap
    never floods the whole silhouette (the trap: snow drawn per column down to the base)."""
    out = []
    for x, y in tops:
        out.append(f'<rect x="{x}" y="{y}" width="{col}" height="{H - y}" fill="{rock}"/>')
        out.append(f'<rect x="{x}" y="{y}" width="{col}" height="6" fill="{lip}"/>')
        if y < snow_below:
            depth = snow_below - y + (rnd.choice((0, 24, 48)) if rnd else 0)
            out.append(f'<rect x="{x}" y="{y}" width="{col}" height="{depth}" fill="{snow}"/>'
                       f'<rect x="{x}" y="{y}" width="{col}" height="5" fill="#FFFFFF"/>')
    return "".join(out)


def pine(x, y, s, dark="#24492F", light="#2F6140"):
    """A voxel pine: three stacked blocks narrowing upward, the lit side on the right."""
    out = [f'<rect x="{x - 6 * s}" y="{y - 30 * s}" width="{12 * s}" height="{30 * s}" fill="#4A3020"/>']
    for i, (w, h) in enumerate(((90, 60), (66, 54), (40, 50))):
        top = y - 30 * s - sum(hh for _, hh in ((90, 60), (66, 54), (40, 50))[:i + 1]) * s
        out.append(f'<rect x="{x - w / 2 * s}" y="{top}" width="{w * s}" height="{h * s}" fill="{dark}"/>'
                   f'<rect x="{x}" y="{top}" width="{w / 2 * s}" height="{h * s}" fill="{light}"/>')
    return "".join(out)


def bridge():
    """The stone walkway from the bottom-left corner to the gate: the leading line into the goal."""
    near, far = (0, 1080, 1180, 1080), (1330, 792, 1660, 792)     # left, y, right, y
    out = [f'<polygon points="0,1080 {near[2]},1080 {far[2]},{far[1]} {far[0]},{far[1]}" fill="#9A9EA6"/>',
           f'<polygon points="0,1080 {far[0]},{far[1]} {far[0]},{far[1] + 30} 0,1110" fill="#5B5F67"/>']
    for i in range(1, 9):                       # rows of stones, closer together toward the gate
        t = 1 - (1 - i / 9) ** 1.6
        y = 1080 + (far[1] - 1080) * t
        xl = near[0] + (far[0] - near[0]) * t
        xr = near[2] + (far[2] - near[2]) * t
        out.append(f'<line x1="{xl:.0f}" y1="{y:.0f}" x2="{xr:.0f}" y2="{y:.0f}" stroke="#6D7178" stroke-width="{4 - 2.5 * t:.1f}"/>')
    for j in range(1, 6):                       # joints along the walk, converging on the gate
        f = j / 6
        out.append(f'<line x1="{near[0] + (near[2] - near[0]) * f:.0f}" y1="1080" x2="{far[0] + (far[2] - far[0]) * f:.0f}" '
                   f'y2="{far[1]}" stroke="#6D7178" stroke-width="2.5"/>')
    return "".join(out)


def gate(cx=1495, base=792):
    """Two stone pillars, a lintel, a dark arch lit from inside, a torch on each pillar."""
    pw, ph, gw = 86, 330, 220
    out = ['<radialGradient id="glow" cx=".5" cy=".7" r=".6"><stop offset="0" stop-color="#FFB347"/>'
           '<stop offset=".55" stop-color="#C2501E"/><stop offset="1" stop-color="#2A1414"/></radialGradient>']
    out.append(f'<path d="M{cx - gw / 2} {base} V{base - ph + 110} A{gw / 2} {gw / 2} 0 0 1 {cx + gw / 2} {base - ph + 110} '
               f'V{base} Z" fill="url(#glow)"/>')
    for side in (-1, 1):
        x = cx + side * (gw / 2 + pw / 2) - pw / 2
        out.append(f'<rect x="{x}" y="{base - ph}" width="{pw}" height="{ph}" fill="#80848C" stroke="#3B3E44" stroke-width="5"/>')
        out += [f'<line x1="{x}" y1="{base - ph + k * 55}" x2="{x + pw}" y2="{base - ph + k * 55}" stroke="#5E6168" stroke-width="3"/>'
                for k in range(1, 6)]
        fx, fy = x + pw / 2, base - ph + 150
        out.append(f'<circle cx="{fx}" cy="{fy}" r="46" fill="#FFB347" opacity=".35"/>'
                   f'<rect x="{fx - 8}" y="{fy}" width="16" height="34" fill="#4A3020"/>'
                   f'<path d="M{fx} {fy - 40} Q{fx + 20} {fy - 10} {fx} {fy + 2} Q{fx - 20} {fy - 10} {fx} {fy - 40}Z" fill="#FFD25A"/>')
    lx0, lx1 = cx - gw / 2 - pw - 24, cx + gw / 2 + pw + 24
    out.append(f'<rect x="{lx0}" y="{base - ph - 60}" width="{lx1 - lx0}" height="64" fill="#8C9098" stroke="#3B3E44" stroke-width="5"/>'
               f'<rect x="{lx0 + 30}" y="{base - ph - 96}" width="{lx1 - lx0 - 60}" height="40" fill="#757980" stroke="#3B3E44" stroke-width="5"/>')
    return "".join(out)


def key(cx, cy, s=1.0):
    """The goal: a gold key in a burst of light, brighter than anything else in the frame."""
    rays = "".join(f'<polygon points="{cx},{cy} {cx + 190 * s * math.cos(a - .05):.0f},{cy + 190 * s * math.sin(a - .05):.0f} '
                   f'{cx + 190 * s * math.cos(a + .05):.0f},{cy + 190 * s * math.sin(a + .05):.0f}" fill="#FFF3B0" opacity=".55"/>'
                   for a in (i * math.pi / 6 for i in range(12)))
    return ('<radialGradient id="keyglow"><stop offset="0" stop-color="#FFF6C8"/><stop offset=".4" stop-color="#FFD54A" stop-opacity=".8"/>'
            '<stop offset="1" stop-color="#FFB000" stop-opacity="0"/></radialGradient>'
            f'<circle cx="{cx}" cy="{cy}" r="{150 * s}" fill="url(#keyglow)"/>{rays}'
            f'<g transform="translate({cx} {cy}) rotate(-35) scale({s})" stroke="#7A4A00" stroke-width="7" stroke-linejoin="round">'
            '<circle cx="-46" cy="0" r="30" fill="none" stroke="#7A4A00" stroke-width="30"/>'
            '<circle cx="-46" cy="0" r="30" fill="none" stroke="#FFC83D" stroke-width="17"/>'
            '<rect x="-16" y="-10" width="96" height="20" fill="#FFC83D"/>'
            '<rect x="48" y="8" width="14" height="26" fill="#FFC83D"/><rect x="66" y="8" width="14" height="18" fill="#FFC83D"/></g>')


def blocky(x, y, s, skin, shirt, pants, flip=False, hood=None, eyes="#1B1B1B", run=1.0):
    """A blocky avatar mid-stride, feet at (x, y). Back limbs first, then body, then the front limbs."""
    k = -1 if flip else 1
    def part(px, py, w, h, fill, rot=0, ox=0, oy=0, rim=True):
        r = f' transform="rotate({rot * k} {x + (px + ox) * s * k} {y + (py + oy) * s})"' if rot else ""
        x0 = x + (px if not flip else -px - w) * s
        g = f'<rect x="{x0:.0f}" y="{y + py * s:.0f}" width="{w * s:.0f}" height="{h * s:.0f}" fill="{fill}" stroke="#1C1A1A" stroke-width="{5 * s:.1f}"{r}/>'
        if rim:                                   # a warm rim on the side facing the gate's light
            rx = x0 + (w * s - 7 * s if not flip else 0)
            g += f'<rect x="{rx:.0f}" y="{y + py * s + 5 * s:.0f}" width="{7 * s:.0f}" height="{h * s - 10 * s:.0f}" fill="#FFD9A0" opacity=".55"{r}/>'
        return g
    out = [part(-34, -330, 62, 150, shirt, rot=40 * run, ox=31, oy=10, rim=False),     # back arm, swung back
           part(-30, -175, 66, 175, pants, rot=-32 * run, ox=33, oy=0, rim=False),     # back leg
           part(-62, -340, 124, 170, shirt),                                           # torso
           f'<rect x="{x + (-62 if not flip else -62) * s:.0f}" y="{y - 205 * s:.0f}" width="{124 * s:.0f}" height="{18 * s:.0f}" fill="#3A2618"/>',
           part(-36, -175, 66, 175, pants, rot=30 * run, ox=33, oy=0)]                 # front leg
    out.append(part(-52, -450, 104, 104, skin))                                        # head
    ex = x + (8 if not flip else -40) * s
    out.append(f'<rect x="{ex:.0f}" y="{y - 412 * s:.0f}" width="{12 * s:.0f}" height="{18 * s:.0f}" fill="{eyes}"/>'
               f'<rect x="{ex + 26 * s:.0f}" y="{y - 412 * s:.0f}" width="{12 * s:.0f}" height="{18 * s:.0f}" fill="{eyes}"/>'
               f'<line x1="{ex - 4 * s:.0f}" y1="{y - 424 * s:.0f}" x2="{ex + 16 * s:.0f}" y2="{y - 418 * s:.0f}" stroke="#1C1A1A" stroke-width="{6 * s:.1f}"/>'
               f'<line x1="{ex + 22 * s:.0f}" y1="{y - 418 * s:.0f}" x2="{ex + 42 * s:.0f}" y2="{y - 424 * s:.0f}" stroke="#1C1A1A" stroke-width="{6 * s:.1f}"/>')
    if hood:
        hx = x - 60 * s
        st = f'fill="{hood}" stroke="#1C1A1A" stroke-width="{5 * s:.1f}" stroke-linejoin="round"'
        out.append(f'<path d="M{hx:.0f} {y - 346 * s:.0f} V{y - 466 * s:.0f} H{hx + 122 * s:.0f} V{y - 428 * s:.0f} '
                   f'H{hx + 26 * s:.0f} V{y - 346 * s:.0f}Z" {st}/>'
                   f'<path d="M{hx + 10 * s:.0f} {y - 352 * s:.0f} L{hx - 150 * s:.0f} {y - 380 * s:.0f} '
                   f'L{hx - 130 * s:.0f} {y - 348 * s:.0f} L{hx + 10 * s:.0f} {y - 326 * s:.0f}Z" {st}/>')
    out.append(part(26, -330, 62, 150, shirt if hood else skin, rot=-70 * run, ox=31, oy=10))   # front arm, reaching forward
    # the hand: the arm's far end, rotated about the shoulder like the arm itself (a prop placed by eye floats)
    a = math.radians(-70 * run * k)
    sx, sy = x + 57 * s * k, y - 320 * s
    hand = (sx - 135 * s * math.sin(a), sy + 135 * s * math.cos(a))
    return "".join(out), hand


def sword(x, y, s):
    """The blade held forward from the hand at (x, y), with a cold edge-glow so it reads against the warm gate."""
    return (f'<g transform="translate({x:.0f} {y:.0f}) rotate(-24) scale({s})">'
            '<rect x="-10" y="-14" width="250" height="28" rx="6" fill="#6FE3FF" opacity=".35"/>'
            '<polygon points="0,-9 220,-9 246,0 220,9 0,9" fill="#E6F0FA" stroke="#1C1A1A" stroke-width="5"/>'
            '<rect x="-18" y="-26" width="16" height="52" fill="#7A4A00" stroke="#1C1A1A" stroke-width="5"/>'
            '<rect x="-60" y="-8" width="44" height="16" fill="#4A3020" stroke="#1C1A1A" stroke-width="5"/></g>')


def flag(x, y):
    """The summit marker: a pole, a pennant in the game's accent and a halo so it reads from far."""
    return (f'<circle cx="{x + 40}" cy="{y - 120}" r="120" fill="#FFF1A8" opacity=".75"/>'
            f'<rect x="{x - 5}" y="{y - 200}" width="10" height="200" fill="#4A3020" stroke="#1C1A1A" stroke-width="4"/>'
            f'<polygon points="{x + 5},{y - 200} {x + 120},{y - 168} {x + 5},{y - 136}" fill="#E8432E" stroke="#1C1A1A" stroke-width="5"/>')


def scene(variant, seed=7):
    rnd = random.Random(seed)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
           '<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3B6CB7"/>'
           '<stop offset=".55" stop-color="#9CC3E8"/><stop offset="1" stop-color="#E6F0F8"/></linearGradient>'
           # haze: soft stops at both ends, or the band draws a hard shelf across the sky
           '<linearGradient id="haze" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFFFFF" stop-opacity="0"/>'
           '<stop offset=".5" stop-color="#FFFFFF" stop-opacity=".7"/><stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/></linearGradient>'
           '<radialGradient id="sun" cx=".18" cy=".08" r=".45"><stop offset="0" stop-color="#FFF8E0" stop-opacity=".95"/>'
           '<stop offset="1" stop-color="#FFF8E0" stop-opacity="0"/></radialGradient>'
           '<radialGradient id="vignette" cx=".5" cy=".45" r=".75"><stop offset=".6" stop-color="#000" stop-opacity="0"/>'
           '<stop offset="1" stop-color="#0B1020" stop-opacity=".55"/></radialGradient></defs>',
           f'<rect width="{W}" height="{H}" fill="url(#sky)"/><rect width="{W}" height="{H}" fill="url(#sun)"/>']
    far = ridge([(420, 250, 420), (980, 360, 360), (1560, 420, 380)], 820)
    out.append(range_svg(far, 820, "#A9BCD6", "#C3D2E6", "#F2F6FB", 400, rnd=rnd))
    out.append('<rect x="0" y="560" width="1920" height="260" fill="url(#haze)"/>')
    crag_peak = (1500, 150, 430) if variant == "dungeon" else (1580, 300, 420)
    mid = ridge([(240, 560, 300), (700, 600, 260), crag_peak], 1000)
    out.append(range_svg(mid, 1000, "#66778F", "#7F90A8", "#EEF3F9", 470, rnd=rnd))
    out.append('<rect x="0" y="760" width="1920" height="140" fill="url(#haze)" opacity=".6"/>')
    out += [pine(x, 900 + rnd.randint(-10, 10), s) for x, s in ((60, 1.35), (170, 1.05), (1840, 1.3))]
    out.append(bridge())
    if variant == "dungeon":
        out.append(gate())
        out.append(blocky(430, 900, 0.78, "#6FAE4E", "#5B4A36", "#3E4A3A", flip=False, eyes="#FF3B30", run=0.6)[0])   # the first enemy
        out.append(key(1495, 640, 0.9))
    else:                                       # a stepped trail from the bridge's end up to the flag
        top = min(y for x, y in mid if 1540 <= x <= 1620)
        out += [f'<rect x="{1500 + 10 * i - 40 * (i % 2):.0f}" y="{792 - i * (792 - top) / 9:.0f}" width="90" height="22" '
                f'fill="#B9BDC4" stroke="#5B5F67" stroke-width="4"/>' for i in range(9)]
        out.append(flag(1580, top))
    hero, hand = blocky(900, 1075, 1.05, "#E8B98A", "#6B4A2F", "#3F5A3A", hood="#2F6FD0")                     # the hero
    out.append(hero)
    out.append(sword(*hand, 1.1))
    out.append(f'<rect width="{W}" height="{H}" fill="url(#vignette)"/></svg>')
    return "".join(out)


def selftest():
    import xml.dom.minidom
    for v in ("dungeon", "summit"):
        svg = scene(v)
        xml.dom.minidom.parseString(svg)
        assert "<text" not in svg, "the art carries no text; the title is live text on top"
    tops = ridge([(500, 200, 300)], 800)
    assert min(y for _, y in tops) == 192 and max(y for _, y in tops) == 792, "snapped to the 24px voxel grid"
    snow = range_svg([(0, 200), (32, 700)], 800, "#000", "#111", "#FFF", 470)
    assert snow.count('fill="#FFF"') == 1, "only the column above the snow line gets a cap"
    print("selftest ok")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest(); sys.exit(0)
    for v in ("dungeon", "summit"):
        with open(os.path.join(HERE, f"art-{v}.svg"), "w", encoding="utf-8") as fh:
            fh.write(scene(v))
        print(f"art-{v}.svg")
