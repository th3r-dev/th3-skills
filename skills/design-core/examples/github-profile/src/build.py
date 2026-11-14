"""Build the animated profile SVGs for github.com/th3r-dev.

  hero.svg    yellow poster: name, what I do, and one request traced through four layers
  agents.svg  black panel: an agent moving along Plan > Design > Build > Test > Ship with its skills

Run: python build.py <out_dir>   (needs fonttools + brotli)
Fonts (OFL, in ./fonts): Archivo 500/800 for display, JetBrains Mono 500/800 for labels.
"""
import base64, io, os, sys
from html import escape
from fontTools import subset
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))

# tokens
Y, INK = "#FFD60A", "#0A0A0A"
INK2, INK3 = "#2B2B2B", "#5E5200"          # on yellow: body, muted
TX, TX2, TX3, LINE = "#F2F2F2", "#B8B8B8", "#7A7A7A", "#2E2E2E"  # on black
MONO_W = 0.6


def font_css(sans, mono):
    out = []
    for fam, key, text in (("A", "arc", sans), ("M", "jbm", mono)):
        for w in (500, 800):
            f = TTFont(f"{HERE}/fonts/{key}-{w}.woff2")
            s = subset.Subsetter()
            s.populate(text=text + " ")
            s.subset(f)
            f.flavor = "woff2"
            b = io.BytesIO()
            f.save(b)
            out.append(f"@font-face{{font-family:{fam};font-weight:{w};"
                       f"src:url(data:font/woff2;base64,{base64.b64encode(b.getvalue()).decode()}) format('woff2')}}")
    return "".join(out)


class Doc:
    def __init__(self):
        self.parts, self.sans, self.mono = [], [], []

    def add(self, s):
        self.parts.append(s)
        return s

    def t(self, x, y, s, size, fill, w=500, mono=False, anchor=None, extra=""):
        (self.mono if mono else self.sans).append(s)
        fam = "m" if mono else "a"
        a = f' text-anchor="{anchor}"' if anchor else ""
        wt = ' font-weight="800"' if w == 800 else ""
        return (f'<text class="{fam}" x="{x}" y="{y}" font-size="{size}" fill="{fill}"{wt}{a}{extra}>'
                f'{escape(s)}</text>')


def anim(name, dur, delay=0, rest="both", ease="cubic-bezier(.2,.7,.2,1)"):
    return f' style="animation:{name} {dur}s {ease} {delay:.2f}s {rest}"'


def g(inner, name="up", dur=0.6, delay=0):
    return f'<g{anim(name, dur, delay)}>{inner}</g>'


BASE = (
    ".a{font-family:A,'Helvetica Neue',Arial,sans-serif}"
    ".m{font-family:M,ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;white-space:pre}"
    "@keyframes up{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}"
    "@keyframes fade{from{opacity:0}to{opacity:1}}"
    "@keyframes grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}"
    "@keyframes blink{50%{opacity:.15}}"
)
REDUCED = "@media (prefers-reduced-motion:reduce){*{animation:none!important}"


def windows_kf(name, wins, on=1, off=0, prop="opacity"):
    """Keyframes that hold `on` inside each [start, end] percent window, `off` elsewhere."""
    pts = [(0, off)]
    for a, b in wins:
        pts += [(max(a - 1, 0), off), (a, on), (b, on), (min(b + 1, 100), off)]
    pts.append((100, off))
    seen, body = set(), ""
    for p, v in sorted(pts):
        if p in seen:
            continue
        seen.add(p)
        body += f"{p}%{{{prop}:{v}}}"
    return f"@keyframes {name}{{{body}}}"


# ---------------------------------------------------------------- hero
LAYERS = [
    ("01", "Interface", "Next.js  Angular"),
    ("02", "Services", "NestJS  FastAPI"),
    ("03", "Data", "Oracle  PostgreSQL"),
    ("04", "Platform", "Kubernetes  ArgoCD"),
]


def hero():
    W, H = 900, 400
    d = Doc()
    d.add(f'<defs><clipPath id="c"><rect width="{W}" height="{H}" rx="14"/></clipPath></defs>')
    d.add('<g clip-path="url(#c)">')
    d.add(f'<rect width="{W}" height="{H}" fill="{Y}"/>')

    # top bar
    d.add(f'<rect width="{W}" height="34" fill="{INK}"/>')
    d.add(d.t(28, 22, "TH3R-DEV", 11.5, Y, 800, True))
    d.add(d.t(104, 22, "/  FULL-STACK + PLATFORM ENGINEER", 11.5, TX3, mono=True))
    d.add(f'<circle cx="{W - 186}" cy="17.5" r="4" fill="{Y}" style="animation:blink 1.6s steps(1) infinite"/>')
    d.add(d.t(W - 174, 22, "OPEN TO THE RIGHT ROLE", 11.5, TX2, mono=True))

    # left: name and statement
    x = 36
    d.add(g(d.t(x, 72, "CHAIYAPHUM, THAILAND  /  UTC+7", 11, INK3, 800, True), delay=0.1))
    d.add(g(d.t(x - 2, 128, "Theeraphat", 52, INK, 800, extra=' letter-spacing="-1"'), delay=0.2))
    d.add(g(d.t(x - 2, 182, "Chueanokkhum", 52, INK, 800, extra=' letter-spacing="-1"'), delay=0.32))
    d.add(f'<rect x="{x}" y="204" width="56" height="5" fill="{INK}" style="transform-origin:{x}px 0;'
          f'animation:grow .5s cubic-bezier(.65,0,.35,1) .6s both"/>')
    d.add(g(d.t(x, 242, "I build software from the interface", 18, INK2)
            + d.t(x, 266, "down to the cluster, and stay to run it.", 18, INK2), delay=0.7))
    now = (f'<rect x="{x}" y="296" width="42" height="20" rx="3" fill="{INK}"/>'
           + d.t(x + 21, 310, "NOW", 11, Y, 800, True, "middle")
           + d.t(x + 54, 310, "OCM, a nationwide oil-control platform", 12.5, INK, mono=True)
           + d.t(x + 54, 330, "for Thailand's Excise Department", 12.5, INK, mono=True))
    d.add(g(now, delay=0.85))

    # right: one request traced through four layers
    rx, rw, top, bh, gap = 520, 344, 70, 56, 10
    rail = rx - 22
    d.add(g(d.t(rx, 58, "ONE REQUEST, FOUR LAYERS", 11, INK3, 800, True), delay=0.9))
    d.add(f'<path d="M{rail} {top + bh / 2}V{top + 3 * (bh + gap) + bh / 2}" stroke="{INK}" stroke-width="2" '
          f'stroke-dasharray="2 4"{anim("fade", .4, 1.0)}/>')

    P = 6.4  # trace period, s
    downs = [4 + i * 12 for i in range(4)]        # % of period when the request reaches each layer
    ups = [86 - i * 12 for i in range(4)]
    kf = ""
    for i, (num, name, tools) in enumerate(LAYERS):
        y = top + i * (bh + gap)
        wins = [(downs[i] - 2, downs[i] + 7)] if i < 3 else [(downs[3] - 2, ups[3] + 7)]
        if i < 3:
            wins.append((ups[i] - 2, ups[i] + 7))
        kf += windows_kf(f"l{i}", wins)
        band = (f'<rect x="{rx}" y="{y}" width="{rw}" height="{bh}" rx="6" fill="none" stroke="{INK}" stroke-width="1.6"/>'
                + d.t(rx + 16, y + 34, num, 11, INK3, 800, True)
                + d.t(rx + 44, y + 36, name, 21, INK, 800)
                + d.t(rx + rw - 16, y + 34, tools, 11.5, INK2, mono=True, anchor="end")
                + f'<g style="opacity:0;animation:l{i} {P}s linear 1.6s infinite">'
                  f'<rect x="{rx}" y="{y}" width="{rw}" height="{bh}" rx="6" fill="{INK}"/>'
                + d.t(rx + 16, y + 34, num, 11, Y, 800, True)
                + d.t(rx + 44, y + 36, name, 21, Y, 800)
                + d.t(rx + rw - 16, y + 34, tools, 11.5, Y, mono=True, anchor="end")
                + '</g>'
                + f'<path d="M{rail} {y + bh / 2}H{rx}" stroke="{INK}" stroke-width="1.6"/>')
        d.add(g(band, delay=1.0 + i * 0.12))

    # the request dot: down through the layers, back up
    c = [top + i * (bh + gap) + bh / 2 for i in range(4)]
    stops = [(0, c[0])] + [(downs[i], c[i]) for i in range(4)] + [(ups[3], c[3])] \
        + [(ups[i], c[i]) for i in (2, 1, 0)] + [(100, c[0])]
    dot_kf = "@keyframes dot{" + "".join(f"{p}%{{transform:translateY({v - c[0]:.0f}px)}}" for p, v in stops) + "}"
    d.add(f'<g style="animation:fade .4s ease 1.5s both"><g style="animation:dot {P}s cubic-bezier(.6,0,.3,1) 1.6s infinite">'
          f'<circle cx="{rail}" cy="{c[0]}" r="9" fill="{Y}" stroke="{INK}" stroke-width="2.4"/>'
          f'<circle cx="{rail}" cy="{c[0]}" r="3.4" fill="{INK}"/></g></g>')

    # bottom: moving hazard strip
    sy = H - 18
    stripes = "".join(f'<path d="M{x0} {sy + 18}l18 -18h12l-18 18z" fill="{INK}"/>' for x0 in range(-60, W + 60, 30))
    d.add(f'<rect y="{sy}" width="{W}" height="18" fill="{Y}"/><path d="M0 {sy}H{W}" stroke="{INK}" stroke-width="1.6"/>')
    d.add(f'<g style="animation:strip 2.4s linear infinite">{stripes}</g>')
    d.add('</g>')
    d.add(f'<rect x="0.8" y="0.8" width="{W - 1.6}" height="{H - 1.6}" rx="13.5" fill="none" stroke="{INK}" stroke-width="1.6"/>')

    css = (BASE + kf + dot_kf + "@keyframes strip{to{transform:translateX(30px)}}"
           + REDUCED + "}")
    label = ("Theeraphat Chueanokkhum, full-stack and platform engineer in Chaiyaphum, Thailand. "
             "I build software from the interface down to the cluster, and stay to run it. "
             "Now: OCM, a nationwide oil-control platform for Thailand's Excise Department. "
             "An animated request travels down four layers and back: Interface (Next.js, Angular), "
             "Services (NestJS, FastAPI), Data (Oracle, PostgreSQL), Platform (Kubernetes, ArgoCD).")
    return wrap(W, H, label, "Theeraphat Chueanokkhum", css, d)


# ---------------------------------------------------------------- agents
STAGES = [
    ("Plan", [("poc-spec-driven-builder", "spec and tests first")]),
    ("Design", [("design-core", "scored UI review"), ("design-flow", "Figma + flowchart")]),
    ("Build", [("prompt-cache-kit", "cheaper agent runs"), ("thai-mock-naming", "safe mock data")]),
    ("Test", [("qa", "evidence and reports"), ("dependency-vuln-explainer", "does a CVE reach you")]),
    ("Ship", [("devops", "infra change, reported"), ("doc-style-builder", "Markdown to PDF + DOCX"),
              ("pdf-operations", "merge, split, stamp"), ("podman-disk-reclaim", "win back disk")]),
]


def agents():
    W, H = 900, 336
    d = Doc()
    d.add(f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="14" fill="{INK}" stroke="{LINE}"/>')
    d.add(d.t(28, 36, "AGENT SKILLS", 11.5, Y, 800, True))
    d.add(d.t(W - 28, 36, "/plugin marketplace add th3r-dev/th3-skills", 11.5, TX3, mono=True, anchor="end"))
    d.add(g(d.t(28, 74, "What my coding agents load, from idea to production.", 24, TX, 800), delay=0.1))

    x0, ty = 28, 132
    widths = [178, 150, 162, 196, 160]  # per stage, sized to its longest skill name
    xs = [x0 + sum(widths[:i]) for i in range(5)]
    d.add(f'<path d="M{x0 + 6} {ty}H{xs[4] + 6}" stroke="{LINE}" stroke-width="2"/>')
    d.add(f'<path d="M{x0 + 6} {ty}H{xs[4] + 6}" stroke="{Y}" stroke-width="2" '
          f'style="transform-origin:{x0 + 6}px 0;animation:grow 1.8s cubic-bezier(.65,0,.35,1) .4s both"/>')

    P = 8.0
    hold = 100 / 5
    kf = ""
    for i, (stage, skills) in enumerate(STAGES):
        x = xs[i]
        delay = 0.4 + i * 0.36
        a, b = i * hold, i * hold + hold * 0.7
        kf += windows_kf(f"s{i}", [(a + 2, b)])
        node = (f'<circle cx="{x + 6}" cy="{ty}" r="6" fill="{INK}" stroke="{Y}" stroke-width="2"/>'
                f'<circle cx="{x + 6}" cy="{ty}" r="6" fill="{Y}" style="opacity:0;animation:s{i} {P}s linear 2.4s infinite"/>'
                + d.t(x, ty - 18, f"0{i + 1}", 11, TX3, 800, True)
                + d.t(x + 22, ty - 18, stage.upper(), 12, TX, 800, True))
        d.add(g(node, "fade", 0.3, delay))
        for j, (name, tag) in enumerate(skills):
            y = ty + 42 + j * 40
            item = (f'<path d="M{x} {y - 15}h3v30h-3z" fill="{Y}"/>'
                    + d.t(x + 12, y, name, 11, TX, 800, True)
                    + d.t(x + 12, y + 17, tag, 11, TX3, mono=True))
            d.add(g(item, delay=delay + 0.15 + j * 0.08))

    # agent marker hops station to station
    stops = ""
    for i in range(5):
        a, b = i * hold, i * hold + hold * 0.7
        stops += f"{a:.1f}%{{transform:translateX({xs[i] - x0}px)}}{b:.1f}%{{transform:translateX({xs[i] - x0}px)}}"
    stops += f"100%{{transform:translateX({xs[4] - x0}px)}}"
    d.add(f'<g style="animation:fade .3s ease 2.3s both"><g style="animation:hop {P}s cubic-bezier(.6,0,.3,1) 2.4s infinite">'
          f'<circle cx="{x0 + 6}" cy="{ty}" r="13" fill="none" stroke="{Y}" stroke-width="1.6" opacity=".55"/></g></g>')

    css = (BASE + kf + "@keyframes hop{" + stops + "}" + REDUCED + "}")
    label = ("Agent skills from th3-skills, along a track from idea to production. "
             + " ".join(f"{s}: " + ", ".join(f"{n} ({t})" for n, t in sk) + "." for s, sk in STAGES))
    return wrap(W, H, label, "th3-skills", css, d)


def wrap(w, h, label, title, css, d):
    fonts = font_css("".join(d.sans), "".join(d.mono))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{escape(label)}"><title>{escape(title)}</title>'
            f'<style>{fonts}{css}</style>{"".join(d.parts)}</svg>')


def inside_work(p):
    """The output folder comes from the command line, so it must stay inside the folder the script runs from."""
    root = os.path.realpath(os.getcwd())
    full = os.path.realpath(os.path.join(root, os.path.expanduser(p)))
    if full != root and not full.startswith(root + os.sep):
        raise SystemExit(f"output folder {p!r} is outside the working folder {root}")
    return full


if __name__ == "__main__":
    out = inside_work(sys.argv[1] if len(sys.argv) > 1 else ".")
    os.makedirs(out, exist_ok=True)
    for name, fn in (("hero.svg", hero), ("agents.svg", agents)):
        s = fn()
        with open(os.path.join(out, name), "w", encoding="utf-8") as fh:
            fh.write(s)
        print(name, len(s) // 1024, "KB")
