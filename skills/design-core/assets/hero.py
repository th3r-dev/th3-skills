"""Build design-core's animated hero: hero.svg next to this file.

The animation is the skill's loop, in order: twelve references come in, three variants are
built from them, the generic one loses and one is picked, then a fresh critic scores each round
until the score crosses the bar. The author's own score shows once and is set aside.

Run: ~/.venvs/diagram-design/bin/python hero.py [--check]   (needs fonttools + brotli)
Fonts: Archivo + JetBrains Mono (OFL) from ../examples/github-profile/src/fonts.
"""
import base64, io, os, sys
from html import escape
from fontTools import subset
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "..", "examples", "github-profile", "src", "fonts")

# tokens: same system as the github-profile example
Y, INK, INK2, INK3 = "#FFD60A", "#0A0A0A", "#2B2B2B", "#5E5200"
W, H, CYCLE = 1280, 640, 12.0
EASE = "cubic-bezier(.2,.7,.2,1)"

_fonts = {}


def font(key):
    if key not in _fonts:
        _fonts[key] = TTFont(f"{FONTS}/{key}.woff2")
    return _fonts[key]


def width(s, size, key):
    f = font(key)
    cmap, hmtx, upm = f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm
    missing = [ch for ch in s if ord(ch) not in cmap]
    assert not missing, f"{key} has no glyph for {missing!r} in {s!r}"
    return sum(hmtx[cmap[ord(ch)]][0] for ch in s) * size / upm


def embed_fonts(text):
    """@font-face rules for Archivo (A) and JetBrains Mono (M), subset to the text used."""
    out = []
    for fam, key in (("A", "arc"), ("M", "jbm")):
        for w in (500, 800):
            f = TTFont(f"{FONTS}/{key}-{w}.woff2")
            s = subset.Subsetter()
            s.populate(text=text[key] + " ")
            s.subset(f)
            f.flavor = "woff2"
            b = io.BytesIO()
            f.save(b)
            out.append(f"@font-face{{font-family:{fam};font-weight:{w};"
                       f"src:url(data:font/woff2;base64,{base64.b64encode(b.getvalue()).decode()}) format('woff2')}}")
    return "".join(out)


class Doc:
    def __init__(self):
        self.body, self.css, self.text = [], [], {"arc": "", "jbm": ""}
        self.n = 0

    def t(self, x, y, s, size, fill, w=500, mono=False, anchor=None, cls="", maxw=None):
        key = "jbm" if mono else "arc"
        if maxw:
            got = width(s, size, f"{key}-{w}")
            assert got <= maxw, f"{s!r} is {got:.0f}px, column is {maxw}px"
        self.text[key] += s
        a = f' text-anchor="{anchor}"' if anchor else ""
        c = f' class="{"m" if mono else "a"} {cls}"'
        return (f'<text{c} x="{x}" y="{y}" font-size="{size}" font-weight="{w}" fill="{fill}"{a}>'
                f'{escape(s)}</text>')

    def window(self, t_in, t_out, cycle, base=0, rise=6):
        """A class shown only inside [t_in, t_out] of each `cycle`; `base` is the static opacity."""
        self.n += 1
        name = f"w{self.n}"
        p = lambda t: round(t / cycle * 100, 2)
        a, a2, b, b2 = p(t_in), p(t_in + 0.3), p(t_out - 0.25), p(t_out)
        lead = f"0%,{a}%" if a > 0 else "0%"
        self.css.append(
            f"@keyframes {name}{{{lead}{{opacity:0;transform:translateY({rise}px)}}{a2}%,{b}%{{opacity:1;transform:none}}"
            f"{b2}%,100%{{opacity:0;transform:none}}}}"
            f".{name}{{opacity:{base};animation:{name} {cycle}s {EASE} infinite}}")
        return name

    def show(self, t_in, t_out=CYCLE - 0.7, rise=8, to=1.0):
        """A class that is hidden until t_in, visible until t_out, every cycle."""
        self.n += 1
        name = f"s{self.n}"
        p = lambda t: round(t / CYCLE * 100, 2)
        a, b = p(t_in), p(t_out)
        a2 = min(round(a + 4, 2), b)
        self.css.append(
            f"@keyframes {name}{{0%,{a}%{{opacity:0;transform:translateY({rise}px)}}"
            f"{a2}%,{b}%{{opacity:{to};transform:none}}100%{{opacity:0;transform:none}}}}"
            f".{name}{{animation:{name} {CYCLE}s {EASE} infinite}}")
        return name

    def draw(self, t_in, t_out=CYCLE - 0.7, dur=0.6):
        """A class for a path (pathLength=1) that draws itself at t_in."""
        self.n += 1
        name = f"d{self.n}"
        p = lambda t: round(t / CYCLE * 100, 2)
        a, a2, b = p(t_in), p(t_in + dur), p(t_out)
        self.css.append(
            f"@keyframes {name}{{0%,{a}%{{stroke-dashoffset:1}}{a2}%,{b}%{{stroke-dashoffset:0;opacity:1}}"
            f"100%{{stroke-dashoffset:0;opacity:0}}}}"
            f".{name}{{stroke-dasharray:1;animation:{name} {CYCLE}s {EASE} infinite}}")
        return name

    def fade_to(self, t_at, to, t_out=CYCLE - 0.7):
        """A class that is fully visible, then fades to `to` at t_at (the base state is `to`)."""
        self.n += 1
        name = f"f{self.n}"
        p = lambda t: round(t / CYCLE * 100, 2)
        a, a2, b = p(t_at), p(t_at + 0.5), p(t_out)
        self.css.append(
            f"@keyframes {name}{{0%,{a}%{{opacity:1}}{a2}%,{b}%{{opacity:{to}}}100%{{opacity:0}}}}"
            f".{name}{{opacity:{to};animation:{name} {CYCLE}s {EASE} infinite}}")
        return name


def arrow(d, x, y1, y2, t):
    """A vertical arrow drawn as a path, head included."""
    c = d.draw(t, dur=0.4)
    h = d.show(t + 0.3, rise=0)
    return (f'<path class="{c}" pathLength="1" d="M{x} {y1}V{y2 - 2}" stroke="{INK}" stroke-width="2" fill="none"/>'
            f'<path class="{h}" d="M{x - 6} {y2 - 8}L{x} {y2}L{x + 6} {y2 - 8}" stroke="{INK}" stroke-width="2" fill="none"/>')


# tiny wireframes, drawn inside a w x h box at (x, y)
def wire(kind, x, y, w, h, ink=INK):
    r = lambda a, b, c, e, op=1: (f'<rect x="{x + a:.1f}" y="{y + b:.1f}" width="{c:.1f}" height="{e:.1f}" '
                                  f'rx="1.5" fill="{ink}" opacity="{op}"/>')
    if kind == "centre":
        return r(w * .2, h * .22, w * .6, h * .14) + r(w * .3, h * .45, w * .4, h * .06, .5) + r(w * .38, h * .64, w * .24, h * .12)
    if kind == "split":
        return r(w * .08, h * .2, w * .42, h * .16) + r(w * .08, h * .45, w * .32, h * .06, .5) + r(w * .08, h * .63, w * .18, h * .12) + r(w * .58, h * .14, w * .34, h * .72, .35)
    if kind == "cards":
        cw = w * .25
        return r(w * .2, h * .12, w * .6, h * .1) + "".join(r(w * .08 + i * (cw + w * .055), h * .36, cw, h * .5, .35) for i in range(3))
    if kind == "list":
        return "".join(r(w * .08, h * (.16 + i * .18), w * (.84 if i % 2 == 0 else .6), h * .08, .5 if i else 1) for i in range(4))
    if kind == "photo":
        return r(0, 0, w, h * .62, .35) + r(w * .08, h * .72, w * .5, h * .1)
    if kind == "big":
        return r(w * .08, h * .18, w * .84, h * .3) + r(w * .08, h * .6, w * .45, h * .07, .5)
    raise ValueError(kind)


def build():
    d = Doc()
    out = []

    # ---- left column: copy written first, then placed
    L, COL = 64, 500
    out.append(d.t(L, 236, "design-core", 80, INK, 800, cls=d.show(0.1), maxw=COL))
    out.append(d.t(L, 296, "Design from references,", 32, INK, 800, cls=d.show(0.3), maxw=COL))
    out.append(d.t(L, 336, "not adjectives.", 32, INK, 800, cls=d.show(0.4), maxw=COL))
    out.append(d.t(L, 384, "A critic that didn’t build it", 22, INK2, 500, cls=d.show(0.6), maxw=COL))
    out.append(d.t(L, 414, "decides when it’s done.", 22, INK2, 500, cls=d.show(0.7), maxw=COL))
    facts = ["9–12 references, 3 variants", "layout first, motion second", "pass at 9.2, never self-scored"]
    for i, s in enumerate(facts):
        y = 478 + i * 30
        c = d.show(0.9 + i * 0.1)
        out.append(f'<g class="{c}"><rect x="{L}" y="{y - 11}" width="8" height="8" fill="{INK}"/>'
                   + d.t(L + 22, y, s, 16, INK, 500, mono=True, maxw=COL - 22) + "</g>")
    out.append(d.t(L, 600, "th3r-dev/th3-skills", 14, INK3, 500, mono=True))

    # ---- right stage
    X0, X1 = 660, 1216
    SW = X1 - X0

    # references: 12 tiles
    out.append(d.t(X0, 82, "references", 14, INK3, 500, mono=True, cls=d.show(1.0)))
    kinds = ["centre", "split", "photo", "list", "big", "cards", "split", "photo", "centre", "big", "list", "split"]
    tw, th, gap = 84, 50, (SW - 6 * 84) / 5
    for i, k in enumerate(kinds):
        x, y = X0 + (i % 6) * (tw + gap), 96 + (i // 6) * (th + 10)
        c = d.show(1.1 + i * 0.08)
        out.append(f'<g class="{c}"><rect x="{x:.1f}" y="{y}" width="{tw}" height="{th}" fill="none" '
                   f'stroke="{INK}" stroke-width="1.5"/>{wire(k, x + 6, y + 6, tw - 12, th - 12)}</g>')

    out.append(arrow(d, X0 + SW / 2, 214, 248, 2.2))

    # three variants; C is the generic three-card row and loses
    out.append(d.t(X0, 270, "3 variants", 14, INK3, 500, mono=True, cls=d.show(2.5)))
    vw, vh = (SW - 2 * 20) / 3, 104
    vy = 282
    picked_x = None
    for i, (name, k) in enumerate((("A", "centre"), ("B", "split"), ("C", "cards"))):
        x = X0 + i * (vw + 20)
        c = d.show(2.7 + i * 0.15)
        inner = (f'<rect x="{x:.1f}" y="{vy}" width="{vw:.1f}" height="{vh}" fill="none" stroke="{INK}" stroke-width="1.5"/>'
                 + wire(k, x + 12, vy + 26, vw - 24, vh - 38)
                 + d.t(x + 10, vy + 18, name, 13, INK, 800, mono=True))
        if name == "B":
            picked_x = x
            out.append(f'<g class="{c}">{inner}</g>')
        else:
            out.append(f'<g class="{c}"><g class="{d.fade_to(4.0, 0.3)}">{inner}</g></g>')
    # the pick: heavy frame + tag
    pk = d.show(4.0, rise=0)
    out.append(f'<g class="{pk}"><rect x="{picked_x - 3:.1f}" y="{vy - 3}" width="{vw + 6:.1f}" height="{vh + 6}" '
               f'fill="none" stroke="{INK}" stroke-width="4"/>'
               f'<rect x="{picked_x + vw - 62:.1f}" y="{vy + vh - 10}" width="64" height="22" fill="{INK}"/>'
               + d.t(picked_x + vw - 30, vy + vh + 5, "picked", 12, Y, 800, mono=True, anchor="middle") + "</g>")

    out.append(arrow(d, picked_x + vw / 2, vy + vh + 16, 432, 4.5))

    # critic score per round, against the bar
    out.append(d.t(X0, 452, "critic score", 14, INK3, 500, mono=True, cls=d.show(4.8)))
    sy = lambda s: 598 - (s - 5) * 30          # 5..10 -> 598..448
    rx = lambda i: X0 + 150 + i * 96             # r1..r5
    bar = sy(9.2)
    bc = d.draw(4.9, dur=0.8)
    out.append(f'<path class="{bc}" pathLength="1" d="M{X0 + 120} {bar:.1f}H{X1}" stroke="{INK}" '
               f'stroke-width="1.5" fill="none"/>')
    out.append(d.t(X0 + 110, bar + 5, "bar 9.2", 13, INK, 800, mono=True, anchor="end", cls=d.show(5.0)))

    # round 1: the author scores itself 9.8 (a pass), set aside; the critic says 6.1
    self_c = d.show(5.3)
    out.append(f'<g class="{self_c}"><g class="{d.fade_to(6.0, 0.35)}">'
               f'<circle cx="{rx(0)}" cy="{sy(9.8):.1f}" r="7" fill="none" stroke="{INK}" stroke-width="2"/>'
               + d.t(rx(0) + 14, sy(9.8) + 4, "self 9.8", 12, INK, 500, mono=True) + "</g></g>")

    scores = [6.1, 7.3, 8.2, 8.8, 9.4]
    t0 = 6.0
    for i, s in enumerate(scores):
        t = t0 + i * 0.8
        if i:
            lc = d.draw(t - 0.3, dur=0.35)
            out.append(f'<path class="{lc}" pathLength="1" d="M{rx(i - 1)} {sy(scores[i - 1]):.1f}L{rx(i)} {sy(s):.1f}" '
                       f'stroke="{INK}" stroke-width="3" fill="none"/>')
        dc = d.show(t, rise=0)
        out.append(f'<g class="{dc}"><circle cx="{rx(i)}" cy="{sy(s):.1f}" r="7" fill="{INK}"/>'
                   + d.t(rx(i), sy(s) + 26, f"{s}", 13, INK, 800, mono=True, anchor="middle") + "</g>")
        out.append(d.t(rx(i), 626, f"r{i + 1}", 12, INK3, 500, mono=True, anchor="middle", cls=d.show(4.9 + i * 0.05)))

    # pass
    pc = d.show(t0 + 4 * 0.8 + 0.5)
    px, py = X1 - 92, sy(9.4) - 52
    out.append(f'<g class="{pc}"><rect x="{px}" y="{py}" width="92" height="30" fill="{INK}"/>'
               f'<path d="M{px + 14} {py + 15}l6 6l11-12" stroke="{Y}" stroke-width="3" fill="none"/>'
               + d.t(px + 58, py + 20, "pass", 15, Y, 800, mono=True, anchor="middle") + "</g>")

    label = ("design-core: design from references, not adjectives. Twelve references feed three variants; "
             "the generic three-card variant is dropped and variant B is picked. A fresh critic scores each round, "
             "6.1, 7.3, 8.2, 8.8, 9.4, until the score passes the 9.2 bar. The author's own score of 9.8 is set aside.")

    fonts = [embed_fonts(d.text)]
    css = ("".join(fonts)
           + ".a{font-family:A,'Helvetica Neue',Arial,sans-serif}"
           + ".m{font-family:M,ui-monospace,SFMono-Regular,Menlo,monospace;white-space:pre}"
           + "".join(d.css)
           + "@media (prefers-reduced-motion:reduce){*{animation:none!important}}")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
            f'role="img" aria-label="{escape(label)}"><title>{escape(label)}</title>'
            f'<style>{css}</style><rect width="{W}" height="{H}" fill="{Y}"/>{"".join(out)}</svg>')


if __name__ == "__main__":
    svg = build()
    path = os.path.join(HERE, "hero.svg")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(svg)
    print(f"{path}: {len(svg) / 1024:.0f} KB")
