#!/usr/bin/env python3
"""The scenes behind the Craghold thumbnails, as vector art (the image model was out of quota).

No text in the art: the title, ribbon and callouts are live text added by banner.py's keyart layout,
so they stay spellable and the bench can measure them.

  dungeon  the hero hits the first enemy on the bridge for gold; the key blazes in the gate behind it
  summit   sunrise: the hero points his sword up a switchback path to the flag on the peak
  loop     the core loop left to right: level up on the farm, fight for gold, buy the key to the gate

Run: python3 build_art.py            writes art-dungeon.svg, art-summit.svg and art-loop.svg next to this file
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


def range_svg(tops, base, rock, lip, snow, snow_below, col=32, rnd=None, shade="#C9D7E8"):
    """One rect per column plus a lighter lip on every step; snow only above `snow_below`, so the cap
    never floods the whole silhouette (the trap: snow drawn per column down to the base). Snow on a slope
    falling away from the sun (top-left) takes the `shade` tone, so a peak reads as a solid, not a flat blob."""
    out, prev = [], None
    for x, y in tops:
        lit = prev is None or y <= prev
        prev = y
        out.append(f'<rect x="{x}" y="{y}" width="{col}" height="{H - y}" fill="{rock}"/>')
        out.append(f'<rect x="{x}" y="{y}" width="{col}" height="6" fill="{lip}"/>')
        if y < snow_below:
            depth = snow_below - y + (rnd.choice((0, 24, 48)) if rnd else 0)
            out.append(f'<rect x="{x}" y="{y}" width="{col}" height="{depth}" fill="{snow if lit else shade}"/>'
                       f'<rect x="{x}" y="{y}" width="{col}" height="5" fill="#FFFFFF"/>')
    return "".join(out)


def pine(x, y, s, dark="#24492F", light="#2F6140"):
    """A voxel pine: three stacked blocks narrowing upward, the lit side on the right, snow on every ledge
    (the snow world has to reach the foreground, or a phone-size read misses it)."""
    out = [f'<rect x="{x - 6 * s}" y="{y - 30 * s}" width="{12 * s}" height="{30 * s}" fill="#4A3020"/>']
    for i, (w, h) in enumerate(((90, 60), (66, 54), (40, 50))):
        top = y - 30 * s - sum(hh for _, hh in ((90, 60), (66, 54), (40, 50))[:i + 1]) * s
        out.append(f'<rect x="{x - w / 2 * s}" y="{top}" width="{w * s}" height="{h * s}" fill="{dark}"/>'
                   f'<rect x="{x}" y="{top}" width="{w / 2 * s}" height="{h * s}" fill="{light}"/>'
                   f'<rect x="{x - w / 2 * s}" y="{top}" width="{w * s}" height="{12 * s}" fill="#F4F8FC"/>'
                   f'<rect x="{x - w / 2 * s + 8 * s}" y="{top + 12 * s}" width="{10 * s}" height="{8 * s}" fill="#F4F8FC"/>')
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
    for x0, x1 in ((0, far[0]), (near[2], far[2])):           # snow drifted against both kerbs
        out.append(f'<line x1="{x0}" y1="1080" x2="{x1}" y2="{far[1]}" stroke="#F4F8FC" stroke-width="16" stroke-linecap="round"/>')
    return "".join(out)


def gate(cx=1495, base=792):
    """Two stone pillars, a lintel, a dark arch lit from inside, a torch on each pillar."""
    pw, ph, gw = 86, 330, 220
    # the arch is near-black so the key is the brightest thing on screen; a lit arch competes with it
    out = ['<radialGradient id="glow" cx=".5" cy=".75" r=".7"><stop offset="0" stop-color="#3A1A12"/>'
           '<stop offset="1" stop-color="#0B0607"/></radialGradient>']
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
               f'<rect x="{lx0 + 30}" y="{base - ph - 96}" width="{lx1 - lx0 - 60}" height="40" fill="#757980" stroke="#3B3E44" stroke-width="5"/>'
               f'<rect x="{lx0 + 26}" y="{base - ph - 110}" width="{lx1 - lx0 - 52}" height="16" rx="6" fill="#F4F8FC"/>'
               f'<rect x="{lx0 - 4}" y="{base - ph - 70}" width="{lx1 - lx0 + 8}" height="12" rx="5" fill="#F4F8FC"/>')
    return "".join(out)


def key(cx, cy, s=1.0):
    """The goal: a gold key in a burst of light, brighter than anything else in the frame."""
    rays = "".join(f'<polygon points="{cx},{cy} {cx + 190 * s * math.cos(a - .05):.0f},{cy + 190 * s * math.sin(a - .05):.0f} '
                   f'{cx + 190 * s * math.cos(a + .05):.0f},{cy + 190 * s * math.sin(a + .05):.0f}" fill="#FFF3B0" opacity=".75"/>'
                   for a in (i * math.pi / 6 for i in range(12)))
    return ('<radialGradient id="keyglow"><stop offset="0" stop-color="#FFF6C8"/><stop offset=".4" stop-color="#FFD54A" stop-opacity=".8"/>'
            '<stop offset="1" stop-color="#FFB000" stop-opacity="0"/></radialGradient>'
            f'<circle cx="{cx}" cy="{cy}" r="{150 * s}" fill="url(#keyglow)"/>{rays}'
            f'<g transform="translate({cx} {cy}) rotate(-35) scale({s})" stroke="#7A4A00" stroke-width="7" stroke-linejoin="round">'
            '<circle cx="-46" cy="0" r="30" fill="none" stroke="#7A4A00" stroke-width="30"/>'
            '<circle cx="-46" cy="0" r="30" fill="none" stroke="#FFC83D" stroke-width="17"/>'
            '<rect x="-16" y="-10" width="96" height="20" fill="#FFC83D"/>'
            '<rect x="48" y="8" width="14" height="26" fill="#FFC83D"/><rect x="66" y="8" width="14" height="18" fill="#FFC83D"/></g>')


def blocky(x, y, s, skin, shirt, pants, flip=False, hood=None, eyes="#1B1B1B", run=1.0, reach=-70):
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
    # the face carries the emotion at phone size: big eyes, brows angled in, gritted teeth
    ex = x + (4 if not flip else -50) * s
    L = lambda a, b, c, e, w: f'<line x1="{ex + a * s:.0f}" y1="{y + b * s:.0f}" x2="{ex + c * s:.0f}" y2="{y + e * s:.0f}" stroke="#1C1A1A" stroke-width="{w * s:.1f}" stroke-linecap="round"/>'
    out.append(f'<rect x="{ex:.0f}" y="{y - 420 * s:.0f}" width="{18 * s:.0f}" height="{24 * s:.0f}" fill="{eyes}"/>'
               f'<rect x="{ex + 28 * s:.0f}" y="{y - 420 * s:.0f}" width="{18 * s:.0f}" height="{24 * s:.0f}" fill="{eyes}"/>'
               + L(-6, -436, 20, -424, 9) + L(26, -424, 52, -436, 9)
               + f'<rect x="{ex + 4 * s:.0f}" y="{y - 390 * s:.0f}" width="{40 * s:.0f}" height="{18 * s:.0f}" fill="#1C1A1A"/>'
               f'<rect x="{ex + 7 * s:.0f}" y="{y - 387 * s:.0f}" width="{34 * s:.0f}" height="{12 * s:.0f}" fill="#FFFFFF"/>'
               + "".join(L(7 + 8.5 * i, -387, 7 + 8.5 * i, -375, 2.5) for i in range(1, 4)))
    if hood:
        hx = x - 60 * s
        st = f'fill="{hood}" stroke="#1C1A1A" stroke-width="{5 * s:.1f}" stroke-linejoin="round"'
        out.append(f'<path d="M{hx:.0f} {y - 346 * s:.0f} V{y - 466 * s:.0f} H{hx + 122 * s:.0f} V{y - 428 * s:.0f} '
                   f'H{hx + 26 * s:.0f} V{y - 346 * s:.0f}Z" {st}/>'
                   f'<path d="M{hx + 10 * s:.0f} {y - 352 * s:.0f} L{hx - 150 * s:.0f} {y - 380 * s:.0f} '
                   f'L{hx - 130 * s:.0f} {y - 348 * s:.0f} L{hx + 10 * s:.0f} {y - 326 * s:.0f}Z" {st}/>')
    out.append(part(26, -330, 62, 150, shirt if hood else skin, rot=reach * run, ox=31, oy=10))   # front arm (reach: -70 forward, -140 up)
    # the hand: the arm's far end, rotated about the shoulder like the arm itself (a prop placed by eye floats)
    a = math.radians(reach * run * k)
    sx, sy = x + 57 * s * k, y - 320 * s
    hand = (sx - 135 * s * math.sin(a), sy + 135 * s * math.cos(a))
    return "".join(out), hand


def sword(x, y, s, angle=-24):
    """The blade held from the hand at (x, y), with a cold edge-glow so it reads against warm light."""
    return (f'<g transform="translate({x:.0f} {y:.0f}) rotate({angle}) scale({s})">'
            '<rect x="-10" y="-14" width="250" height="28" rx="6" fill="#6FE3FF" opacity=".35"/>'
            '<polygon points="0,-9 220,-9 246,0 220,9 0,9" fill="#E6F0FA" stroke="#1C1A1A" stroke-width="5"/>'
            '<rect x="-18" y="-26" width="16" height="52" fill="#7A4A00" stroke="#1C1A1A" stroke-width="5"/>'
            '<rect x="-60" y="-8" width="44" height="16" fill="#4A3020" stroke="#1C1A1A" stroke-width="5"/></g>')


def coin(cx, cy, r=18):
    """A gold coin flying out of a hit: the 'earn gold' half of the loop, shown instead of written."""
    return (f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#FFC83D" stroke="#7A4A00" stroke-width="5"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r * .55:.1f}" fill="none" stroke="#FFE58A" stroke-width="3"/>'
            f'<rect x="{cx - r * .5:.1f}" y="{cy - r * .7:.1f}" width="{r * .25:.1f}" height="{r * .5:.1f}" fill="#FFFFFF"/>')


def spark(cx, cy, r=60):
    """The hit: an eight-point white star with a cold rim, where the blade meets the enemy."""
    pts = " ".join(f"{cx + (r if i % 2 == 0 else r * .35) * math.cos(i * math.pi / 8):.0f},"
                   f"{cy + (r if i % 2 == 0 else r * .35) * math.sin(i * math.pi / 8):.0f}" for i in range(16))
    return f'<polygon points="{pts}" fill="#FFFFFF" stroke="#6FE3FF" stroke-width="6" stroke-linejoin="round"/>'


def flag(x, y):
    """The summit marker: a pole and a pennant, lit from behind by the sunrise (a halo disc read as a moon)."""
    return (f'<rect x="{x - 5}" y="{y - 200}" width="10" height="200" fill="#4A3020" stroke="#1C1A1A" stroke-width="4"/>'
            f'<polygon points="{x + 5},{y - 200} {x + 120},{y - 168} {x + 5},{y - 136}" fill="#E8432E" stroke="#1C1A1A" stroke-width="5"/>')


def switchback(x0, y0, x1, y1, legs=5, swing=150):
    """A path cut into the slope, zig-zagging from the bridge's end up to the peak: a trail you can
    follow with the eye, where floating steps read as platforms."""
    pts = [(x0, y0)] + [(x1 + (swing if i % 2 else -swing) * (1 - i / legs), y0 + (y1 - y0) * i / legs)
                        for i in range(1, legs)] + [(x1, y1)]
    d = "M" + " L".join(f"{x:.0f} {y:.0f}" for x, y in pts)
    return (f'<path d="{d}" fill="none" stroke="#3B3E44" stroke-width="34" stroke-linejoin="round" stroke-linecap="round"/>'
            f'<path d="{d}" fill="none" stroke="#E2D6C3" stroke-width="22" stroke-linejoin="round" stroke-linecap="round"/>')


def animal(x, y, s, kind):
    """A voxel farm animal facing left, feet at (x, y): the farm zone where you level up."""
    o = 'stroke="#1C1A1A" stroke-width="4"'
    body, head, nose = (("#F2A7B5", "#F2A7B5", "#E07C92") if kind == "pig" else ("#F4F4F0", "#F4F4F0", "#F2A7B5"))
    bw, bh = (120, 70) if kind == "pig" else (150, 84)
    out = [f'<rect x="{x + dx * s:.0f}" y="{y - 30 * s:.0f}" width="{16 * s:.0f}" height="{30 * s:.0f}" fill="{body}" {o}/>'
           for dx in (8, 34, bw - 52, bw - 26)]                                                      # legs
    out.append(f'<rect x="{x:.0f}" y="{y - (30 + bh) * s:.0f}" width="{bw * s:.0f}" height="{bh * s:.0f}" fill="{body}" {o}/>')
    if kind == "cow":                                                                                 # patches
        out += [f'<rect x="{x + px * s:.0f}" y="{y - (30 + bh - py) * s:.0f}" width="{w * s:.0f}" height="{h * s:.0f}" fill="#1C1A1A"/>'
                for px, py, w, h in ((30, 10, 36, 26), (90, 34, 30, 30), (60, 56, 22, 18))]
    hx, hy = x - 44 * s, y - (30 + bh + 14) * s
    out.append(f'<rect x="{hx:.0f}" y="{hy:.0f}" width="{60 * s:.0f}" height="{56 * s:.0f}" fill="{head}" {o}/>'
               f'<rect x="{hx - 14 * s:.0f}" y="{hy + 26 * s:.0f}" width="{28 * s:.0f}" height="{24 * s:.0f}" fill="{nose}" {o}/>'
               f'<rect x="{hx + 10 * s:.0f}" y="{hy + 12 * s:.0f}" width="{9 * s:.0f}" height="{11 * s:.0f}" fill="#1C1A1A"/>'
               f'<rect x="{hx + 34 * s:.0f}" y="{hy + 12 * s:.0f}" width="{9 * s:.0f}" height="{11 * s:.0f}" fill="#1C1A1A"/>')
    if kind == "cow":
        out.append(f'<rect x="{hx + 4 * s:.0f}" y="{hy - 14 * s:.0f}" width="{10 * s:.0f}" height="{14 * s:.0f}" fill="#E8DCC0" {o}/>'
                   f'<rect x="{hx + 44 * s:.0f}" y="{hy - 14 * s:.0f}" width="{10 * s:.0f}" height="{14 * s:.0f}" fill="#E8DCC0" {o}/>')
    return "".join(out)


def pen(x0, x1, y):
    """A wooden fence: the farm is a fenced training zone you grow out of."""
    o = 'fill="#8A5A34" stroke="#1C1A1A" stroke-width="4"'
    posts = "".join(f'<rect x="{x:.0f}" y="{y - 90}" width="18" height="96" {o}/>' for x in range(int(x0), int(x1) + 1, 110))
    return (f'<rect x="{x0}" y="{y - 74}" width="{x1 - x0 + 18}" height="14" {o}/>'
            f'<rect x="{x0}" y="{y - 38}" width="{x1 - x0 + 18}" height="14" {o}/>' + posts)


def scene(variant, seed=7):
    rnd = random.Random(seed)
    sunrise = variant == "summit"               # the summit is its own moment: dawn on the peak, not the dungeon's noon
    sky = (('#33397F', '.45', '#E7836C', '#FFE2B5') if sunrise else ('#2F63C4', '.55', '#9CC3E8', '#E6F0F8'))
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
           f'<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{sky[0]}"/>'
           f'<stop offset="{sky[1]}" stop-color="{sky[2]}"/><stop offset="1" stop-color="{sky[3]}"/></linearGradient>'
           # haze: soft stops at both ends, or the band draws a hard shelf across the sky
           '<linearGradient id="haze" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFFFFF" stop-opacity="0"/>'
           '<stop offset=".5" stop-color="#FFFFFF" stop-opacity=".7"/><stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/></linearGradient>'
           '<radialGradient id="sun" cx=".18" cy=".08" r=".45"><stop offset="0" stop-color="#FFF8E0" stop-opacity=".95"/>'
           '<stop offset="1" stop-color="#FFF8E0" stop-opacity="0"/></radialGradient>'
           '<radialGradient id="vignette" cx=".7" cy=".55" r=".85"><stop offset=".5" stop-color="#000" stop-opacity="0"/>'
           '<stop offset="1" stop-color="#0B1020" stop-opacity=".55"/></radialGradient>'
           '<linearGradient id="spill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFC060" stop-opacity=".55"/>'
           '<stop offset="1" stop-color="#FFC060" stop-opacity="0"/></linearGradient></defs>',
           f'<rect width="{W}" height="{H}" fill="url(#sky)"/>' + ('' if sunrise else f'<rect width="{W}" height="{H}" fill="url(#sun)"/>')]
    crag_peak = (1580, 230, 420) if sunrise else (1500, 150, 430)
    if sunrise:                                  # the sun just behind the peak: the rim light that makes it the goal
        out.append('<circle cx="1640" cy="300" r="150" fill="#FFF2C8" opacity=".55"/><circle cx="1640" cy="300" r="95" fill="#FFF6DA"/>')
    far = ridge([(420, 250, 420), (980, 360, 360), (1560, 420, 380)], 820)
    rock = (("#A79BCB", "#C3B8E0", "#F6E9F0", "#D8C7DE"), ("#5A5C96", "#7779B2", "#FBE7DA", "#D9C3D0")) if sunrise else \
           (("#9DB6E0", "#BCD0EE", "#F2F6FB", "#C9D7E8"), ("#4F6896", "#6A84B0", "#EEF3F9", "#C9D7E8"))
    out.append(range_svg(far, 820, *rock[0][:3], 400, rnd=rnd, shade=rock[0][3]))
    out.append('<rect x="0" y="560" width="1920" height="260" fill="url(#haze)"/>')
    mid = ridge([(240, 560, 300), (700, 600, 260), crag_peak], 1000)
    out.append(range_svg(mid, 1000, *rock[1][:3], 470, rnd=rnd, shade=rock[1][3]))
    out.append('<rect x="0" y="760" width="1920" height="140" fill="url(#haze)" opacity=".6"/>')
    trees = ((1840, 1.3),) if variant == "loop" else ((60, 1.35), (170, 1.05), (1840, 1.3))
    out += [pine(x, 900 + rnd.randint(-10, 10), s) for x, s in trees]
    out.append(bridge())
    if variant == "loop":                        # the farm: where every run starts and you level up to 10
        out.append('<polygon points="0,812 600,836 600,968 0,1092" fill="#86AE63"/>'
                   '<polygon points="0,812 600,836 600,846 0,824" fill="#F4F8FC"/>')
        out.append(pen(20, 560, 935))
        out.append(animal(110, 990, 1.0, "pig") + animal(330, 975, 0.95, "cow"))
    if variant in ("dungeon", "loop"):
        out.append(gate())
        out.append('<polygon points="1395,792 1595,792 1250,1080 600,1080" fill="url(#spill)"/>')   # the key's light down the bridge
        out.append(key(1495, 610, 1.4))
        # the first enemy, between the hero and the gate and facing him: the fight is the loop
        out.append(blocky(1270, 905, 0.95, "#6FAE4E", "#5B4A36", "#3E4A3A", flip=True, eyes="#FF3B30", run=0.7)[0])
    else:                                       # a path cut up the slope from the bridge's end to the flag
        top = min(y for x, y in mid if 1550 <= x <= 1610)
        out.append(switchback(1490, 800, 1580, top + 6, legs=6, swing=120))
        out.append(flag(1580, top))
    up = variant == "summit"                     # on the summit he points the blade at the flag: the eye follows it
    hero, hand = blocky(900, 1075, 1.4, "#E8B98A", "#6B4A2F", "#3F5A3A", hood="#2F6FD0", reach=-140 if up else -70)
    out.append(hero)
    out.append(sword(*hand, 1.25, angle=-50 if up else -24))
    if variant in ("dungeon", "loop"):                    # where the blade meets the enemy: a spark and the gold it drops
        out.append(spark(1236, 648, 50))          # on the chest, clear of the face that sells the threat
        out += [coin(cx, cy, r) for cx, cy, r in ((1080, 520, 20), (1135, 475, 17), (1190, 505, 22), (1050, 585, 15))]
    out += [f'<rect x="{rnd.randint(0, W)}" y="{rnd.randint(0, H)}" width="{z}" height="{z}" fill="#FFFFFF" opacity=".85"/>'
            for z in (rnd.choice((4, 6, 8)) for _ in range(70))]                                           # falling snow
    out.append(f'<rect width="{W}" height="{H}" fill="url(#vignette)"/></svg>')
    return "".join(out)


def selftest():
    import xml.dom.minidom
    for v in ("dungeon", "summit", "loop"):
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
    for v in ("dungeon", "summit", "loop"):
        with open(os.path.join(HERE, f"art-{v}.svg"), "w", encoding="utf-8") as fh:
            fh.write(scene(v))
        print(f"art-{v}.svg")
