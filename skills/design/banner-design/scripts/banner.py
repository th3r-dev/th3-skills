# /// script
# requires-python = ">=3.10"
# dependencies = ["fonttools==4.65.0", "brotli==1.2.1"]
# ///
"""Render a banner spec (*.banner.json) to SVG: brand on one side, four steps, one CTA.
A game thumbnail brief (*.keyart.toon, thumbnail-keyart) renders through the same code as the `keyart` layout.

The spec is the shareable part: copy, size, mark, icons, custom styles and the variants to build.
This script holds the four layouts (references/layouts.md) and three preset styles
(references/sizes-and-styles.md). Every layout is drawn on a 1280-wide design grid and scaled to
the spec's size, so 1280 x 640, 1920 x 1080 and 1500 x 500 come from the same code.

Run: uv run banner.py <spec.banner.json | brief.keyart.toon> [layout-style ...]   default: the spec's "variants",
     at every size in "sizes" (or the one "size")
     writes {layout}-{style}-{W}x{H}.svg next to the spec; bench.py checks each
     uv run banner.py --selftest
"""
import argparse, csv, importlib.util, json, math, os, re, sys
from html import escape

HERE = os.path.dirname(os.path.abspath(__file__))
CORE = os.path.join(HERE, "..", "..", "core", "assets", "hero.py")   # fonts, width(), text helper
_spec = importlib.util.spec_from_file_location("dc_hero", CORE)
dc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dc)
Y, INK, INK2, INK3 = dc.Y, dc.INK, dc.INK2, dc.INK3

DW, M = 1280, 64            # design grid width and edge band; the canvas scales from these

#   ground, brand panel, text on panel, text, secondary, numbers, rules, CTA ground, CTA text, panel edge
#   optional: pattern (grid|dots) + pattern_color, shadow (layer depth), accent (the request line),
#   accent_text (text set in the accent role, when the accent is too light to read)
STYLES = {
    "flat":    dict(bg=Y, panel=INK, on_panel=Y, fg=INK, fg2=INK2, fg3=INK3, rule=INK,
                    cta=INK, on_cta=Y, edge=None),                        # 20 flat / solid color
    "dark":    dict(bg="#111113", panel=Y, on_panel=INK, fg="#F2F2F0", fg2="#B4B4AE", fg3=Y, rule=Y,
                    cta=Y, on_cta=INK, edge=None),                        # 19 dark / moody
    "minimal": dict(bg="#FAFAF7", panel="#FAFAF7", on_panel=INK, fg=INK, fg2="#3D3D3A", fg3="#6B6B66",
                    rule="#D9D9D2", cta=INK, on_cta="#FAFAF7", edge=Y),   # 1 minimalist
}
TOKENS = set(STYLES["flat"])


# ---- TOON: the reader marketing/scripts/offer.py and social-media/scripts/bench_post.py also carry
# ponytail: a copy per script, since each skill installs on its own; a shared module if they ever ship together
HEAD = re.compile(r"^(\w[\w-]*)(?:\[(\d+)\])?(?:\{([^}]*)\})?:\s?(.*)$")


def scalar(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] == '"':
        return v[1:-1].replace('\\"', '"')
    return int(v) if re.fullmatch(r"-?\d+", v) else v


def row(line):
    return [scalar(f'"{c}"') if c else "" for c in next(csv.reader([line.strip()], skipinitialspace=True))]


def load_toon(text):
    out, lines, i = {}, text.splitlines(), 0
    while i < len(lines):
        line = lines[i]
        i += 1
        if not line.strip() or line.startswith(" "):
            continue
        m = HEAD.match(line)
        assert m, f"line {i}: not TOON: {line!r}"
        key_, n, cols, rest = m.groups()
        if cols:
            names = [c.strip() for c in cols.split(",")]
            rows = []
            while i < len(lines) and lines[i].startswith("  "):
                rows.append(dict(zip(names, row(lines[i]))))
                i += 1
            assert len(rows) == int(n), f"{key_}: declared {n} rows, found {len(rows)}"
            out[key_] = rows
        elif n is not None:
            items = row(rest) if rest else []
            assert len(items) == int(n), f"{key_}: declared {n} items, found {len(items)}"
            out[key_] = items
        else:
            out[key_] = scalar(rest)
    return out


def keyart_spec(o):
    """A thumbnail brief (thumbnail-keyart's *.keyart.toon) as a render spec. The brief keeps the game read
    (is, loop, goal), the anchor table, the prompt and the variants in one file; the render uses the title,
    kicker, art, callouts and colours, and the rest travels with it so the image can be made again."""
    anchors = o.get("anchors", [])
    assert len(anchors) <= 5, f"{len(anchors)} anchors: a thumbnail reads in under a second, keep five or fewer"
    style = o.get("style", "dark")
    assert style in STYLES, f"style {style!r}: pick a preset ({', '.join(STYLES)}) and override it with `colors`"
    s = {"size": [int(v) for v in o["size"]], "id": o["id"]}
    if o.get("sizes"):
        s["sizes"] = [[int(v) for v in z.split("x")] for z in o["sizes"]]
    if o.get("colors"):                       # a game palette over a preset, named after the game
        s["styles"] = {o["id"]: dict(STYLES[style], **{c["token"]: c["value"] for c in o["colors"]})}
        style = o["id"]
    if o.get("fonts"):
        s["fonts"] = {f["role"]: f["font"] for f in o["fonts"]}
    s["style"] = style
    s["keyart"] = {
        "title": o["title"], "kicker": o.get("kicker", ""), "art": o.get("art"),
        "title_at": o.get("title_at", "top-center"), "title_max": int(o.get("title_max", 100)),
        "is": o.get("is", ""), "loop": o.get("loop", ""), "goal": o.get("goal", ""),
        "anchors": anchors, "prompt": o.get("prompt", ""), "negative": o.get("negative", ""),
        "callouts": [dict(c, x=float(c["x"]), y=float(c["y"]), fill=float(c["fill"]) if c.get("fill", "") != "" else None,
                          to=(float(c["tx"]), float(c["ty"])) if c.get("tx", "") != "" else None)
                     for c in o.get("callouts", [])],
        "variants": o.get("variants", []),
    }
    return s


# ---- spec

def load(path):
    with open(path, encoding="utf-8") as fh:
        s = keyart_spec(load_toon(fh.read())) if path.endswith(".toon") else json.load(fh)
    base = os.path.dirname(os.path.abspath(path))
    rel = lambda p: os.path.normpath(os.path.join(base, p)) if p else None
    s["_dir"] = base
    for part in [s] + s.get("pages", []):      # a page spec carries its own brand, steps and cover
        if "brand" in part:
            part["brand"]["mark"] = rel(part["brand"].get("mark"))
        for st in part.get("steps", []):
            for it in st.get("items", []):
                it["icon"] = rel(it.get("icon"))
        if "hook" in part:
            part["hook"]["image"] = rel(part["hook"].get("image"))
        if "keyart" in part:                   # the scene, and each variant's own scene
            part["keyart"]["art"] = rel(part["keyart"].get("art"))
            for v in part["keyart"].get("variants", []):
                v["art"] = rel(v.get("art"))
        if "showcase" in part:                 # work-sample screenshots, relative to the spec
            sc = part["showcase"]
            sc["image"] = rel(sc.get("image"))
            sc["images"] = [rel(x) for x in sc.get("images", [])]
    styles = dict(STYLES)
    for name, t in s.get("styles", {}).items():
        missing = TOKENS - set(t)
        assert not missing, f"style {name!r} lacks tokens {sorted(missing)}"
        styles[name] = t
    s["_styles"] = styles
    assert "pages" in s or "cover" in s or "keyart" in s or len(s.get("steps", [])) == 4, \
        "the step layouts take four steps; a cover takes a `cover` block; a post takes `pages`; a thumbnail a `.keyart.toon`"
    return s


# ---- pieces

def key(d, role):
    """The font (family-weight) a text role uses in this banner: the spec's "fonts", else the defaults."""
    return getattr(d, "fonts", {}).get(role, ROLE[role])


def wrap(s, maxw, size, key="jbm-500", sep=r"[^-]+-?"):
    """Break s into lines that fit maxw, splitting only at `sep` pieces (hyphens by default)."""
    lines, cur = [], ""
    for part in re.findall(sep, s):
        if cur and dc.width((cur + part).rstrip(), size, key) > maxw:
            lines.append(cur.rstrip())
            cur = part.lstrip()
        else:
            cur += part
    return lines + [cur.rstrip()]


def embed(path, x, y, size, t=None):
    """Place an SVG file as a size x size box. With a style, its ink/yellow are mapped onto it."""
    if not path:
        return ""
    svg = open(path, encoding="utf-8").read()
    svg = re.sub(r"<title>.*?</title>", "", svg, flags=re.S)
    svg = re.sub(r'\s(width|height)="[^"]*"', "", svg.split(">", 1)[0], count=2) + ">" + svg.split(">", 1)[1]
    svg = svg.replace("<svg ", f'<svg x="{x:.1f}" y="{y:.1f}" width="{size}" height="{size}" ', 1)
    if t:  # icons are drawn in the repo's ink on yellow; map them onto this style's text and ground
        svg = svg.replace(INK, "\0").replace(Y, t["bg"]).replace("\0", t["fg"])
    return svg


def brand(d, s, t, x, y, w, h, pad, r=0):
    """The core zone: badge, mark, name, promise; facts at the foot."""
    b = s["brand"]
    cx, cy, cw = x + pad, y + pad, w - pad - 24
    top = ""
    if b.get("badge"):                         # availability, e.g. "Open for freelance": a status pill
        bw = dc.width(b["badge"], 15, key(d, "mono")) + 56
        top = (f'<rect x="{cx}" y="{cy}" width="{bw:.0f}" height="40" rx="20" fill="none" stroke="{t["on_panel"]}" stroke-width="2"/>'
               f'<circle cx="{cx + 22}" cy="{cy + 20}" r="6" fill="{t["on_panel"]}"/>'
               + d.t(cx + 38, cy + 25, b["badge"], 15, t["on_panel"], 500, mono=True, maxw=cw - 56))
        cy += 72
    sizes = (64, 60, 56, 52, 48, 44) if b.get("mark") else (120, 104, 96, 88, 80, 72, 64, 56, 48)
    nz = next(z for z in sizes if dc.width(b["name"], z, key(d, "title")) <= cw)
    ny = cy + 184 if b.get("mark") else cy + round(nz * 0.88)   # no mark: the ascent box (~0.88 em) starts on the pad
    edge = (f'<rect x="{x}" y="{y}" width="12" height="{h}" fill="{t["edge"]}"/>'
            f'<rect x="{x + w - 1}" y="{y}" width="1" height="{h}" fill="{t["rule"]}"/>') if t["edge"] and not r else ""
    stroke = f' stroke="{t["rule"]}" stroke-width="2"' if r and t["panel"] == t["bg"] else ""
    return (f'<g data-bg="{t["panel"]}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{t["panel"]}"{stroke}/>{edge}'
            f'{top}<g data-zone="core">{embed(b.get("mark"), cx, cy, 96)}'   # the badge is support: read second
            + d.t(cx, ny, b["name"], nz, t["on_panel"], 800, maxw=cw)
            + "".join(d.t(cx, ny + 68 + i * 40, line, 32, t["on_panel"], 500, maxw=cw) for i, line in enumerate(b["promise"]))
            + "</g>"
            + facts(d, t, b.get("facts"), cx, y + h - pad, cw)
            + "</g>")


def facts(d, t, f, x, base, w):
    """One mono line, or labelled columns ([["LABEL", "value"], ...]) a buyer scans like a spec sheet."""
    if not f:
        return ""
    if isinstance(f, str):
        return d.t(x, base, f, 15, t["on_panel"], 500, mono=True, maxw=w)
    cw = w / len(f)
    return "".join(d.t(x + i * cw, base - 30, lab, 14, t["on_panel"], 500, mono=True, maxw=cw - 12)
                   + d.t(x + i * cw, base, val, 20, t["on_panel"], 800, maxw=cw - 12) for i, (lab, val) in enumerate(f))


def cta(d, s, t, x0, x1, y, h=64, r=0):
    """One CTA where the eye ends. The verb is core; the detail (command, URL) is support."""
    c = s["cta"]
    cx = x0 + 24 + round(dc.width(c["verb"], 32, key(d, "title"))) + 20
    return (f'<g data-bg="{t["cta"]}"><rect x="{x0}" y="{y}" width="{x1 - x0}" height="{h}" rx="{r}" fill="{t["cta"]}"/>'
            + '<g data-zone="core">' + d.t(x0 + 24, y + h / 2 + 12, c["verb"], 32, t["on_cta"], 800) + "</g>"
            + (d.t(cx, y + h / 2 + 7, c["detail"], 16, t["on_cta"], 500, mono=True, maxw=x1 - cx - 16) if c.get("detail") else "")
            + "</g>")


def item_row(d, t, x, y, items, maxw, size=24):
    """Icons and names inline on one line: the proof under a step."""
    out, cx = [], x
    for it in items:
        if it.get("icon"):
            out.append(embed(it["icon"], cx, y - size + 6, size, t))
            cx += size + 6
        out.append(d.t(cx, y, it["name"], 14, t["fg"], 500, mono=True))
        cx += dc.width(it["name"], 14, key(d, "mono")) + 18
    assert cx - 18 - x <= maxw, f"{[i['name'] for i in items]} is {cx - 18 - x:.0f}px, room is {maxw:.0f}px"
    return "".join(out)


# ---- layouts: drawn on a DW x DH grid

def columns(d, s, t, DH):
    """Four equal columns beside the brand, a numbered rule over each, the CTA under them."""
    BW = 416
    out = [brand(d, s, t, 0, 0, BW, DH, M)]
    X0, X1, GAP = BW + 48, DW - M, 24
    CW = (X1 - X0 - 3 * GAP) / 4
    for k, st in enumerate(s["steps"]):
        x = X0 + k * (CW + GAP)
        g = [f'<rect x="{x:.1f}" y="{M}" width="{CW:.1f}" height="3" fill="{t["rule"]}"/>',
             d.t(x, M + 30, st["num"], 15, t["fg3"], 500, mono=True),
             d.t(x, M + 84, st["verb"], 40, t["fg"], 800, maxw=CW)]
        g += [d.t(x, M + 120 + i * 24, line, 18, t["fg2"], 500, maxw=CW) for i, line in enumerate(st["line"])]
        y = M + 186
        for it in st.get("items", []):
            ix = x + (42 if it.get("icon") else 0)
            if it.get("icon"):
                g.append(embed(it["icon"], x, y, 32, t))
            parts = wrap(it["name"], x + CW - ix, 14, key(d, "mono"))
            g += [d.t(ix, y + 15 + i * 18, p, 14, t["fg"], 500, mono=True, maxw=x + CW - ix) for i, p in enumerate(parts)]
            y += max(48, 18 * len(parts) + 26)
        out.append(f'<g data-zone="support">{"".join(g)}</g>')
    out.append(cta(d, s, t, X0, X1, DH - M - 64))
    return out


def rail(d, s, t, DH):
    """Four rows on a vertical line: number and verb left, what it does and its proof right."""
    BW = 416
    out = [brand(d, s, t, 0, 0, BW, DH, M)]
    X0, X1 = BW + 48, DW - M
    RX, VX, DX = X0 + 8, X0 + 40, X0 + 236
    RH = (DH - 2 * M - 64 - 8) / 4
    ys = [M + k * RH for k in range(4)]
    out.append(f'<rect x="{RX - 1}" y="{ys[0] + 26:.1f}" width="2" height="{ys[3] - ys[0]:.1f}" fill="{t["rule"]}"/>')
    for k, st in enumerate(s["steps"]):
        y = ys[k]
        g = [f'<circle cx="{RX}" cy="{y + 26:.1f}" r="8" fill="{t["fg"]}"/>',
             d.t(VX, y + 32, st["num"], 15, t["fg3"], 500, mono=True),
             d.t(VX, y + 76, st["verb"], 40, t["fg"], 800, maxw=DX - VX - 16),
             d.t(DX, y + 32, " ".join(st["line"]), 18, t["fg2"], 500, maxw=X1 - DX),
             item_row(d, t, DX, y + 70, st.get("items", []), X1 - DX)]
        out.append(f'<g data-zone="support">{"".join(g)}</g>')
    out.append(cta(d, s, t, X0, X1, DH - M - 64))
    return out


def stairs(d, s, t, DH):
    """Four bands stepping down and right: the eye walks the diagonal from the brand to the CTA."""
    BW = 416
    out = [brand(d, s, t, 0, 0, BW, DH, M)]
    X0, X1 = BW + 48, DW - M
    GAP, STEP, TAB = 14, 40, 170
    BH = (DH - 2 * M - 64 - 40 - 3 * GAP) / 4
    for k, st in enumerate(s["steps"]):
        x, y = X0 + k * STEP, M + k * (BH + GAP)
        c, room = y + BH / 2, X1 - x - TAB - 40
        names = ", ".join(i["name"] for i in st.get("items", []))
        out.append(
            f'<g data-zone="support">'
            f'<rect x="{x}" y="{y:.1f}" width="{X1 - x}" height="{BH:.1f}" fill="none" stroke="{t["rule"]}" stroke-width="2"/>'
            f'<g data-bg="{t["fg"]}"><rect x="{x}" y="{y:.1f}" width="{TAB}" height="{BH:.1f}" fill="{t["fg"]}"/>'
            + d.t(x + 18, c - 14, st["num"], 15, t["bg"], 500, mono=True)
            + d.t(x + 18, c + 28, st["verb"], 36, t["bg"], 800, maxw=TAB - 30) + "</g>"
            + d.t(x + TAB + 22, c - 8, " ".join(st["line"]), 18, t["fg2"], 500, maxw=room)
            + (d.t(x + TAB + 22, c + 22, names, 14, t["fg"], 500, mono=True, maxw=room) if names else "")
            + "</g>")
    out.append(cta(d, s, t, X0, X1, DH - M - 64))   # the floor the stairs land on: full width
    return out


def bento(d, s, t, DH):
    """Brand as one tall tile, the four steps as a 2 x 2 grid, the CTA as a wide tile under it."""
    R, G, BW, CH = 20, 20, 380, 72
    out = [brand(d, s, t, M, M, BW, DH - 2 * M, 40, r=R)]
    X0, X1 = M + BW + G, DW - M
    TW = (X1 - X0 - G) / 2
    TH = (DH - 2 * M - CH - 2 * G) / 2
    lists = [wrap(", ".join(i["name"] for i in st.get("items", [])), TW - 48, 14, key(d, "mono"), sep=r"[^ ]+ ?") for st in s["steps"]]
    tall = max(map(len, lists))                    # one divider height for every tile
    for k, st in enumerate(s["steps"]):
        x, y = X0 + (k % 2) * (TW + G), M + (k // 2) * (TH + G)
        first = next((i["icon"] for i in st.get("items", []) if i.get("icon")), None)
        foot = y + TH - 24 - 20 * (tall - 1)       # the proof sits at the foot of the tile
        g = [f'<rect x="{x:.1f}" y="{y:.1f}" width="{TW:.1f}" height="{TH:.1f}" rx="{R}" fill="none" stroke="{t["rule"]}" stroke-width="2"/>',
             d.t(x + 24, y + 40, st["num"], 15, t["fg3"], 500, mono=True),
             d.t(x + 58, y + 42, st["verb"], 32, t["fg"], 800, maxw=TW - 130),
             d.t(x + 24, y + 80, " ".join(st["line"]), 18, t["fg2"], 500, maxw=TW - 48),
             embed(first, x + TW - 64, y + 14, 40, t)]
        if lists[k][0]:
            g.append(f'<rect x="{x + 24:.1f}" y="{foot - 34:.1f}" width="{TW - 48:.1f}" height="1" fill="{t["rule"]}" opacity=".3"/>')
            g += [d.t(x + 24, foot + i * 20, line, 14, t["fg"], 500, mono=True, maxw=TW - 48) for i, line in enumerate(lists[k])]
        out.append(f'<g data-zone="support">{"".join(g)}</g>')
    out.append(cta(d, s, t, X0, X1, DH - M - CH, CH, r=R))
    return out


def pills(d, t, x, y, items, maxw, h=30):
    """Tools as outlined pills on one line."""
    out, cx = [], x
    for it in items:
        w = dc.width(it["name"], 14, key(d, "mono")) + 24
        out.append(f'<rect x="{cx:.1f}" y="{y}" width="{w:.1f}" height="{h}" rx="{h / 2}" fill="none" '
                   f'stroke="{t["fg"]}" stroke-width="1.5"/>' + d.t(cx + 12, y + h / 2 + 5, it["name"], 14, t["fg"], 500, mono=True))
        cx += w + 10
    assert cx - 10 - x <= maxw, f"{[i['name'] for i in items]} is {cx - 10 - x:.0f}px, room is {maxw:.0f}px"
    return "".join(out)


def stack(d, s, t, DH):
    """Four layers stacked like an architecture diagram; a request runs down through them into the CTA."""
    BW = 416
    out = [brand(d, s, t, 0, 0, BW, DH, M)]
    X0, X1 = BW + 48, DW - M
    RX, SX = X0 + 34, X0 + 76                  # the request line (room for its label), the layers' left edge
    GAP, SH, LX = 18, 8, 236                   # gap, depth offset, where the description starts
    cta_y = DH - M - 64
    BH = (cta_y - 28 - M - 3 * GAP - SH) / 4
    shadow = t.get("shadow", t["rule"])
    acc = t.get("accent", t["fg"])
    through = s.get("through")                 # optional label along the line: what carries the request
    if through:
        ly = M + (cta_y - 28 - M) / 2
        out.append(f'<g data-zone="support" transform="rotate(-90 {RX - 20} {ly:.1f})">'
                   + d.t(RX - 20, ly, through, 14, t.get("accent_text", acc), 500, mono=True, anchor="middle",
                         maxw=cta_y - 28 - M) + "</g>")
    out.append(f'<path d="M{RX} {M}V{cta_y - 10}" stroke="{acc}" stroke-width="3" stroke-dasharray="2 8" stroke-linecap="round"/>'
               f'<path d="M{RX - 8} {cta_y - 18}L{RX} {cta_y - 6}L{RX + 8} {cta_y - 18}" stroke="{acc}" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')
    for k, st in enumerate(s["steps"]):
        y = M + k * (BH + GAP)
        c = y + BH / 2
        g = [f'<rect x="{SX + SH}" y="{y + SH:.1f}" width="{X1 - SX - SH}" height="{BH:.1f}" rx="10" fill="{shadow}"/>',
             f'<rect x="{SX}" y="{y:.1f}" width="{X1 - SX - SH}" height="{BH:.1f}" rx="10" fill="{t["bg"]}" stroke="{t["rule"]}" stroke-width="2"/>',
             f'<path d="M{RX} {c:.1f}H{SX}" stroke="{acc}" stroke-width="2"/><circle cx="{RX}" cy="{c:.1f}" r="7" fill="{acc}"/>',
             d.t(SX + 24, c - 16, st["num"], 15, t["fg3"], 500, mono=True),
             d.t(SX + 24, c + 24, st["verb"], 36, t["fg"], 800, maxw=LX - 40),
             d.t(SX + LX, c - 12, " ".join(st["line"]), 18, t["fg2"], 500, maxw=X1 - SH - SX - LX - 24)]
        if st.get("items"):
            g.append(pills(d, t, SX + LX, round(c + 2), st["items"], X1 - SH - SX - LX - 24))
        out.append(f'<g data-zone="support">{"".join(g)}</g>')
    out.append(cta(d, s, t, X0, X1, cta_y, r=10))
    return out


# ---- cover: title-led, for a blog post or an article (no steps, no CTA)

ROLE = {"title": "arc-800", "text": "arc-500", "strong": "arc-800", "accent": "arc-500", "mono": "jbm-500"}


def T(d, s, role, x, y, text, size, fill, **kw):
    """Text in a role's font. The spec's "fonts" maps roles to family-weight, e.g. "title": "kanit-700";
    Thai text needs a Thai family (kanit, anuphan, mali), since Archivo and JetBrains Mono have no Thai."""
    fam, w = s.get("fonts", {}).get(role, ROLE[role]).rsplit("-", 1)
    if fam in ("arc", "jbm"):
        return d.t(x, y, text, size, fill, int(w), mono=fam == "jbm", **kw)
    return d.t(x, y, text, size, fill, int(w), family=fam, **kw)


def mini(kind, x, y, w, h, ink, acc):
    """A thumbnail of one banner layout: the cover of a post about banners shows its own subject."""
    r = lambda a, b, c, e, f=ink, rx=2: f'<rect x="{x + a:.1f}" y="{y + b:.1f}" width="{c:.1f}" height="{e:.1f}" rx="{rx}" fill="{f}"/>'
    o = lambda a, b, c, e, rx=4: (f'<rect x="{x + a:.1f}" y="{y + b:.1f}" width="{c:.1f}" height="{e:.1f}" rx="{rx}" '
                                  f'fill="none" stroke="{ink}" stroke-width="2"/>')
    out = [r(0, 0, w * .28, h)]                # the brand side, every layout has it
    R = w * .34                                # where the right side starts
    if kind == "columns":
        cw = (w - R) / 4 - 6
        out += [r(R + i * (cw + 6), 4, cw, 3) + r(R + i * (cw + 6), 14, cw * .8, 8) + r(R + i * (cw + 6), 28, cw * .6, 4, acc)
                for i in range(4)] + [r(R, h - 14, w - R, 14)]
    elif kind == "rail":
        out += [r(R + 4, 6, 2, h - 24)] + [f'<circle cx="{x + R + 5:.1f}" cy="{y + 8 + i * (h - 24) / 3:.1f}" r="4" fill="{acc}"/>'
                                           + r(R + 16, 4 + i * (h - 24) / 3, (w - R - 20) * (.9 - i * .1), 7) for i in range(4)]
    elif kind == "stairs":
        bh = (h - 16) / 4 - 4
        out += [o(R + i * 10, i * (bh + 4), w - R - i * 10, bh, 2) + r(R + i * 10, i * (bh + 4), 18, bh, acc, 0) for i in range(4)]
    elif kind == "bento":
        tw, th = (w - R - 6) / 2, (h - 22) / 2
        out += [o(R + (i % 2) * (tw + 6), (i // 2) * (th + 6), tw, th) for i in range(4)] + [r(R, h - 10, w - R, 10, acc, 4)]
    elif kind == "stack":
        bh = (h - 22) / 4 - 4
        out += [r(R + 10, i * (bh + 4) + 3, w - R - 10, bh, acc) + o(R + 6, i * (bh + 4), w - R - 12, bh, 3) for i in range(4)]
        out.append(f'<path d="M{x + R:.1f} {y}V{y + h - 8:.1f}" stroke="{ink}" stroke-width="2" stroke-dasharray="2 4"/>')
    return "".join(out)


def cover(d, s, t, DH):
    """Kicker, a two-to-three line title printed twice (pink offset under ink, a risograph
    misregistration), a handwritten note, the author; the motif fans out on the right."""
    c = s["cover"]
    ink, acc = t["fg"], t.get("accent", t["rule"])
    out = []
    # the motif first, so the text column sits above any overlap
    MX0, MX1, CW, CH = 770, DW - M, 250, 150
    kinds = c.get("motif", [])
    if kinds:
        out.append(f'<defs><pattern id="tone" width="14" height="14" patternUnits="userSpaceOnUse">'
                   f'<circle cx="7" cy="7" r="3.2" fill="{acc}"/></pattern></defs>'
                   f'<circle cx="{MX0 + 250}" cy="{DH / 2 + 10:.0f}" r="250" fill="url(#tone)" opacity=".55"/>'
                   f'<circle cx="{MX0 + 238}" cy="{DH / 2:.0f}" r="250" fill="none" stroke="{ink}" stroke-width="2" opacity=".5"/>')
        step = (MX1 - MX0 - CW) / max(len(kinds) - 1, 1)
        drop = (DH - 2 * M - CH - 10) / max(len(kinds) - 1, 1)
        for i, kind in enumerate(kinds):
            x, y = MX0 + i * step, M + i * drop
            rot = (-4, 3, -2, 4, -3)[i % 5]
            out.append(f'<g transform="rotate({rot} {x + CW / 2:.0f} {y + CH / 2:.0f})" data-zone="support">'
                       f'<rect x="{x + 9:.1f}" y="{y + 9:.1f}" width="{CW}" height="{CH}" rx="6" fill="{acc}"/>'
                       f'<rect x="{x:.1f}" y="{y:.1f}" width="{CW}" height="{CH}" rx="6" fill="{t["bg"]}" stroke="{ink}" stroke-width="3"/>'
                       + T(d, s, "mono", x + 16, y + 30, kind, 14, ink)
                       + mini(kind, x + 16, y + 44, CW - 32, CH - 60, ink, acc) + "</g>")
    # the text column; inset a little because Thai ascenders and Kanit's overhang reach past the box
    TX, TW = M + 8, 652
    out.append('<g data-zone="support">'           # the kicker is a label, read after the title
               + f'<rect x="{TX}" y="{M + 26}" width="28" height="10" fill="{acc}"/>'
               + T(d, s, "strong", TX + 40, M + 40, c["kicker"], 22, ink, maxw=TW - 40) + "</g>")
    lines = c["title"]
    fam, w = s.get("fonts", {}).get("title", ROLE["title"]).rsplit("-", 1)
    key = f"{fam}-{w}"
    tz = next(z for z in (92, 84, 76, 68, 60, 52, 46) if all(dc.width(l, z, key) <= TW for l in lines))
    lh = round(tz * 1.18)
    ty = M + 84 + tz
    out.append('<g data-zone="decor" aria-hidden="true">'
               + "".join(T(d, s, "title", TX + 6, ty + i * lh + 6, l, tz, acc) for i, l in enumerate(lines)) + "</g>")
    out.append('<g data-zone="core">'
               + "".join(T(d, s, "title", TX, ty + i * lh, l, tz, ink, maxw=TW) for i, l in enumerate(lines)) + "</g>")
    ny = ty + (len(lines) - 1) * lh + 76
    if c.get("note"):
        nw = dc.width(c["note"], 28, s.get("fonts", {}).get("accent", ROLE["accent"]))
        out.append(f'<g transform="rotate(-2 {TX} {ny})">'
                   + T(d, s, "accent", TX, ny, c["note"], 28, ink, maxw=TW)
                   + f'<path d="M{TX} {ny + 14}q{nw / 4:.0f} -8 {nw / 2:.0f} 0t{nw / 2:.0f} 0" fill="none" stroke="{acc}" '
                     f'stroke-width="5" stroke-linecap="round"/></g>')
    if c.get("author"):
        out.append(T(d, s, "mono", TX, DH - M, c["author"], 16, t["fg2"], maxw=TW))
    return out


def visual(d, s, t, v, x, y, w, h):
    """The right-hand picture of one step: code lines, a checklist, or a size diagram."""
    ink, acc, out = t["fg"], t.get("accent", t["rule"]), []
    if v["kind"] == "code":
        top = y + max(0, (h - len(v["lines"]) * 32) / 2)          # centred in the card
        for i, line in enumerate(v["lines"]):
            out.append(T(d, s, "mono", x, top + 22 + i * 32, line, 18, ink, maxw=w))
    elif v["kind"] == "checks":
        rh = min(72, h / len(v["rows"]))
        top = y + (h - rh * len(v["rows"])) / 2                    # centred in the card
        for i, r in enumerate(v["rows"]):
            cy = top + rh * i + rh / 2
            if r["mark"] == "fail":
                out.append(f'<circle cx="{x + 16}" cy="{cy:.0f}" r="16" fill="{acc}"/>'
                           f'<path d="M{x + 9} {cy - 7:.0f}l14 14M{x + 23} {cy - 7:.0f}l-14 14" stroke="{ink}" stroke-width="3.5" stroke-linecap="round"/>')
            else:
                out.append(f'<circle cx="{x + 16}" cy="{cy:.0f}" r="16" fill="none" stroke="{ink}" stroke-width="3"/>'
                           f'<path d="M{x + 8} {cy:.0f}l6 6l11-12" stroke="{ink}" stroke-width="3.5" fill="none" stroke-linecap="round"/>')
            out.append(T(d, s, "text", x + 48, cy + 8, r["text"], 22, ink, maxw=w - 48))
    elif v["kind"] == "size":
        # the outer frame is the file, the inner one what the page shows; both labelled
        ow, oh = w, w * 9 / 16
        iw, ih = ow * .44, oh * .44
        oy = y + (h - oh) / 2 + 10
        out.append(f'<rect x="{x}" y="{oy:.1f}" width="{ow}" height="{oh:.1f}" rx="6" fill="none" stroke="{ink}" stroke-width="3"/>'
                   f'<rect x="{x + 24}" y="{oy + 24:.1f}" width="{iw:.1f}" height="{ih:.1f}" rx="4" fill="{acc}"/>'
                   + T(d, s, "strong", x + 24, oy - 14, v["outer"], 22, ink, maxw=ow)
                   + T(d, s, "text", x + 24 + iw + 18, oy + 24 + ih / 2 + 8, v["inner"], 20, ink, maxw=ow - iw - 60))
    return "".join(out)


def step(d, s, t, DH):
    """One explained step of a post: kicker, big number, title, caption on the left; the step's
    picture on a riso print card on the right (pink offset under an ink outline)."""
    st = s["step"]
    ink, acc = t["fg"], t.get("accent", t["rule"])
    TX, TW = M + 8, 480
    out = ['<g data-zone="support">' + f'<rect x="{TX}" y="{M + 26}" width="28" height="10" fill="{acc}"/>'
           + T(d, s, "strong", TX + 40, M + 40, st["kicker"], 22, ink, maxw=TW - 40) + "</g>"]
    ny = M + 70 + 150
    out.append('<g data-zone="decor" aria-hidden="true">' + T(d, s, "title", TX + 6, ny + 6, st["num"], 150, acc) + "</g>")
    out.append('<g data-zone="support">' + T(d, s, "title", TX, ny, st["num"], 150, ink) + "</g>")
    fam, w = s.get("fonts", {}).get("title", ROLE["title"]).rsplit("-", 1)
    tz = next(z for z in (60, 54, 48, 42) if all(dc.width(l, z, f"{fam}-{w}") <= TW for l in st["title"]))
    ty = ny + 34 + tz
    out.append('<g data-zone="core">' + "".join(T(d, s, "title", TX, ty + i * round(tz * 1.2), l, tz, ink, maxw=TW)
                                                for i, l in enumerate(st["title"])) + "</g>")
    cy = ty + (len(st["title"]) - 1) * round(tz * 1.2) + 52
    out.append("".join(T(d, s, "text", TX, cy + i * 34, l, 22, t["fg2"], maxw=TW) for i, l in enumerate(st.get("caption", []))))
    if st.get("author"):
        out.append(T(d, s, "mono", TX, DH - M, st["author"], 16, t["fg2"], maxw=TW))
    # the card
    CX, CY, CW, CH = 620, M + 10, DW - M - 620, DH - 2 * M - 20
    out.append(f'<g data-zone="support"><rect x="{CX + 12}" y="{CY + 12}" width="{CW}" height="{CH}" rx="10" fill="{acc}"/>'
               f'<rect x="{CX}" y="{CY}" width="{CW}" height="{CH}" rx="10" fill="{t["bg"]}" stroke="{ink}" stroke-width="3"/>'
               + visual(d, s, t, st["visual"], CX + 40, CY + 40, CW - 80, CH - 80) + "</g>")
    return out


def image_tag(path, x, y, w, h, cid, rx=10):
    """A raster (or SVG) image embedded as data, clipped to a rounded box."""
    import base64, mimetypes
    mime = mimetypes.guess_type(path)[0] or "image/png"
    data = base64.b64encode(open(path, "rb").read()).decode()
    return (f'<clipPath id="{cid}"><rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}"/></clipPath>'
            f'<image href="data:{mime};base64,{data}" x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
            f'preserveAspectRatio="xMidYMid slice" clip-path="url(#{cid})"/>')


def showcase(d, s, t, DH):
    """A work sample, centred: kicker and title above, the work in a framed 16:9 window, a caption and
    tags under it. With no image yet the window holds a placeholder ("Coming soon"), so the same spec
    becomes the real sample later by adding the image path."""
    sc = s["showcase"]
    ink, acc = t["fg"], t.get("accent", t["rule"])
    cx = DW / 2
    out = ['<g data-zone="support">' + T(d, s, "strong", cx, M + 30, sc["kicker"], 22, t["fg3"], anchor="middle", maxw=DW - 2 * M) + "</g>",
           '<g data-zone="core">' + T(d, s, "title", cx, M + 92, sc["title"], 52, ink, anchor="middle", maxw=DW - 2 * M) + "</g>"]
    FH = DH - M - 120 - (M + 160)                   # the window fills what the text leaves
    FW = FH * 16 / 9
    fx, fy = cx - FW / 2, M + 120
    out.append(f'<rect x="{fx + 12:.1f}" y="{fy + 12:.1f}" width="{FW:.1f}" height="{FH:.1f}" rx="14" fill="{t.get("shadow", acc)}"/>'
               f'<rect x="{fx:.1f}" y="{fy:.1f}" width="{FW:.1f}" height="{FH:.1f}" rx="14" fill="{t["bg"]}" stroke="{ink}" stroke-width="3"/>')
    img, imgs = sc.get("image"), sc.get("images") or []
    if imgs:
        # several pages of one work: the first large, the rest stacked beside it, each at its own
        # proportions (a fixed frame would crop logos and headings off real screenshots)
        out.pop()                                    # no single window
        ar = sc.get("aspect", 1.8)                   # width / height of the screenshots
        G, top = 18, M + 120
        avail_h = DH - top - 200                     # room below for the caption, tags and author
        rest = len(imgs) - 1
        avail_w = DW - 2 * M
        # total width = B + G + (B - G * ar * (rest - 1)) / rest, solved for B
        Bw = (avail_w - G + G * ar * (rest - 1) / rest) / (1 + 1 / rest) if rest else avail_w
        B = min(avail_h * ar, Bw)
        bh = B / ar
        sh = (bh - G * (rest - 1)) / rest if rest else 0
        sw = sh * ar
        total = B + (G + sw if rest else 0)
        x0 = cx - total / 2
        boxes = [(x0, top, B, bh)] + [(x0 + B + G, top + i * (sh + G), sw, sh) for i in range(rest)]
        for i, (bx, by, bw2, bh2) in enumerate(boxes):
            out.append(f'<rect x="{bx + 10:.1f}" y="{by + 10:.1f}" width="{bw2:.1f}" height="{bh2:.1f}" rx="10" fill="{t.get("shadow", acc)}"/>'
                       + image_tag(imgs[i], bx, by, bw2, bh2, f"shot{i}")
                       + f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bw2:.1f}" height="{bh2:.1f}" rx="10" fill="none" stroke="{ink}" stroke-width="2"/>')
        fy, FH = top, bh
        lx, ly = boxes[0][0], boxes[0][1]
    elif img:
        import base64, mimetypes
        mime = mimetypes.guess_type(img)[0] or "image/png"
        data = base64.b64encode(open(img, "rb").read()).decode()
        out.append(f'<clipPath id="win"><rect x="{fx + 10:.1f}" y="{fy + 10:.1f}" width="{FW - 20:.1f}" height="{FH - 20:.1f}" rx="8"/></clipPath>'
                   f'<image href="data:{mime};base64,{data}" x="{fx + 10:.1f}" y="{fy + 10:.1f}" width="{FW - 20:.1f}" height="{FH - 20:.1f}" '
                   f'preserveAspectRatio="xMidYMid slice" clip-path="url(#win)"/>')
    else:
        out.append(f'<rect x="{fx + 24:.1f}" y="{fy + 24:.1f}" width="{FW - 48:.1f}" height="{FH - 48:.1f}" rx="8" fill="none" '
                   f'stroke="{t["rule"]}" stroke-width="2" stroke-dasharray="10 10"/>'
                   + T(d, s, "title", cx, fy + FH / 2 + 4, sc.get("placeholder", "Coming soon"), 56, ink, anchor="middle", maxw=FW - 80)
                   + T(d, s, "text", cx, fy + FH / 2 + 50, sc.get("placeholder_note", ""), 22, t["fg2"], anchor="middle", maxw=FW - 80))
    if sc.get("client"):
        # who the work was for: a sticker on the work's top-left corner, in the CTA colours
        cl = sc["client"]
        lx, ly = (lx, ly) if imgs else (fx, fy)
        lab = cl.get("label", "ผลงานสำหรับ")
        w = max(dc.width(cl["name"], 26, key(d, "title")), dc.width(lab, 15, key(d, "text"))) + 44
        out.append(f'<g data-zone="support" data-bg="{t["cta"]}">'
                   f'<rect x="{lx + 20 + 6:.1f}" y="{ly + 20 + 6:.1f}" width="{w:.1f}" height="76" rx="12" fill="{t.get("shadow", ink)}"/>'
                   f'<rect x="{lx + 20:.1f}" y="{ly + 20:.1f}" width="{w:.1f}" height="76" rx="12" fill="{t["cta"]}"/>'
                   + T(d, s, "text", lx + 42, ly + 46, lab, 15, t["on_cta"])
                   + T(d, s, "title", lx + 42, ly + 80, cl["name"], 26, t["on_cta"]) + "</g>")
    cy = fy + FH + 52
    out.append('<g data-zone="support">' + "".join(T(d, s, "text", cx, cy + i * 32, l, 22, t["fg2"], anchor="middle", maxw=DW - 2 * M)
                                                   for i, l in enumerate(sc.get("caption", []))) + "</g>")
    if sc.get("tags"):
        tw = [dc.width(x, 14, key(d, "mono")) + 24 for x in sc["tags"]]
        tx = cx - (sum(tw) + 10 * (len(tw) - 1)) / 2
        ty = cy + 32 * len(sc.get("caption", [])) + 6
        out.append(pills(d, t, tx, round(ty), [{"name": x} for x in sc["tags"]], DW - 2 * M))
    if sc.get("author"):
        out.append(T(d, s, "mono", cx, DH - M + 20, sc["author"], 16, t["fg2"], anchor="middle", maxw=DW - 2 * M))
    return out


LAYOUTS = {"columns": columns, "rail": rail, "stairs": stairs, "bento": bento, "stack": stack, "cover": cover, "step": step,
           "showcase": showcase}


def ground(t, k):
    """Optional ground texture: "grid" (blueprint lines) or "dots" (paper), from the style's tokens."""
    kind, col = t.get("pattern"), t.get("pattern_color")
    if not kind:
        return ""
    n = 32 * k
    mark = (f'<path d="M{n} 0H0V{n}" fill="none" stroke="{col}" stroke-width="1"/>' if kind == "grid"
            else f'<circle cx="{n / 2}" cy="{n / 2}" r="{1.4 * k:.2f}" fill="{col}"/>')
    return (f'<defs><pattern id="ground" width="{n}" height="{n}" patternUnits="userSpaceOnUse">{mark}</pattern></defs>'
            f'<rect width="100%" height="100%" fill="url(#ground)"/>')


def browser(x, y, w, img, t, cid):
    """A screenshot inside a browser window: a top bar with three dots, then the page at its own
    proportions. At thumbnail size the bar is what says "this is a real website"."""
    ink = t["fg"]
    bar = 34
    ih = w / 1.8 if not img else w / _aspect(img)
    out = (f'<rect x="{x + 12:.1f}" y="{y + 12:.1f}" width="{w:.1f}" height="{bar + ih:.1f}" rx="12" fill="{t.get("shadow", ink)}"/>'
           f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{bar + ih:.1f}" rx="12" fill="{t["bg"]}" stroke="{ink}" stroke-width="2.5"/>'
           + "".join(f'<circle cx="{x + 22 + i * 18:.1f}" cy="{y + bar / 2:.1f}" r="5.5" fill="{ink}" opacity=".55"/>' for i in range(3)))
    if img:
        out += image_tag(img, x + 2, y + bar, w - 4, ih - 2, cid)
    return out, bar + ih


def _aspect(path):
    """Width / height of a PNG or JPEG, read from its header (stdlib only)."""
    b = open(path, "rb").read(64 * 1024)
    if b[:8] == b"\x89PNG\r\n\x1a\n":
        w, h = int.from_bytes(b[16:20], "big"), int.from_bytes(b[20:24], "big")
        return w / h
    i = 2
    while i < len(b) - 9:                       # JPEG: walk the markers to the first SOF
        if b[i] != 0xFF:
            i += 1
            continue
        m, n = b[i + 1], int.from_bytes(b[i + 2:i + 4], "big")
        if m in (0xC0, 0xC1, 0xC2):
            h, w = int.from_bytes(b[i + 5:i + 7], "big"), int.from_bytes(b[i + 7:i + 9], "big")
            return w / h
        i += 2 + n
    return 1.8


FLOW_ICONS = {
    # line icons in a 48 x 48 box, centred on (0, 0); drawn in one colour
    "chat": 'M-17 -15H17Q21 -15 21 -11V7Q21 11 17 11H-3L-13 19V11H-17Q-21 11 -21 7V-11Q-21 -15 -17 -15Z|c-9 -2|c0 -2|c9 -2',
    "brief": 'M-15 -20H9L17 -12V20H-15Z|M9 -20V-12H17|M-8 -4H10|M-8 4H10|M-8 12H4',
    "build": 'M-21 -16H21V10H-21Z|M-6 20H6|M0 10V20|M-6 -9L-12 -3L-6 3|M6 -9L12 -3L6 3',
    "launch": 'M0 12V-16|M-10 -6L0 -16L10 -6|M-18 20H18',
    "support": 'M0 -21L17 -14V0Q17 13 0 21Q-17 13 -17 0V-14Z|M-7 0L-2 6L8 -6',
    "ui": 'M-20 -16H20V16H-20Z|M-20 -8H20|M-12 0H-2V10H-12Z|M4 0H14|M4 6H12',
    "mobile": 'M-11 -20H11Q14 -20 14 -17V17Q14 20 11 20H-11Q-14 20 -14 17V-17Q-14 -20 -11 -20Z|M-4 14H4',
    "server": 'M-18 -18H18V-4H-18Z|M-18 4H18V18H-18Z|c10 -11|c10 11|M-11 -11H0|M-11 11H0',
    "network": 'M0 -12V0|M-14 12V4H14V12|M-6 -20H6V-12H-6Z|M-20 12H-8V20H-20Z|M8 12H20V20H8Z',
    "bug": 'M-9 -6Q-9 -16 0 -16Q9 -16 9 -6V8Q9 18 0 18Q-9 18 -9 8Z|M-9 0H-18|M9 0H18|M-8 -12L-15 -18|M8 -12L15 -18|M-9 10L-17 16|M9 10L17 16|M0 -4V14',
    "ai": 'M-14 -14H14V14H-14Z|M-6 -6H6V6H-6Z|M-8 -14V-20|M0 -14V-20|M8 -14V-20|M-8 14V20|M0 14V20|M8 14V20|M-14 -6H-20|M-14 6H-20|M14 -6H20|M14 6H20',
    "game": 'M-14 -10H14Q22 -10 22 0V6Q22 14 14 14Q10 14 8 8H-8Q-10 14 -14 14Q-22 14 -22 6V0Q-22 -10 -14 -10Z|M-12 -2V6|M-16 2H-8|c8 0|c13 4',
}


def flow_icon(kind, cx, cy, color, scale=1.0):
    parts = []
    for seg in FLOW_ICONS[kind].split("|"):
        if seg.startswith("c"):
            x, y = (float(v) for v in seg[1:].split())
            parts.append(f'<circle cx="{x}" cy="{y}" r="2.6" fill="{color}"/>')
        else:
            parts.append(f'<path d="{seg}" fill="none" stroke="{color}" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/>')
    return f'<g transform="translate({cx:.1f} {cy:.1f}) scale({scale})">{"".join(parts)}</g>'


def flow_strip(d, s, t, x0, x1, y, steps):
    """Steps in one line: an icon in a filled circle, a short label under it, arrows between."""
    acc, ink = t.get("accent", t["rule"]), t["fg"]
    n, r = len(steps), 34
    gap = (x1 - x0 - 2 * r) / (n - 1)
    out = []
    for i, st in enumerate(steps):
        cx = x0 + r + i * gap
        if i < n - 1:
            ax0, ax1 = cx + r + 14, cx + gap - r - 14
            out.append(f'<path d="M{ax0:.1f} {y}H{ax1:.1f}M{ax1 - 9:.1f} {y - 7}L{ax1:.1f} {y}L{ax1 - 9:.1f} {y + 7}" '
                       f'fill="none" stroke="{t["rule"]}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>')
        out.append(f'<circle cx="{cx:.1f}" cy="{y}" r="{r}" fill="{acc}"/>' + flow_icon(st["icon"], cx, y, t["bg"], 0.95)
                   + T(d, s, "text", cx, y + r + 34, st["label"], 22, ink, anchor="middle", maxw=gap - 8))
    return '<g data-zone="support">' + "".join(out) + "</g>"


def circuits(t, DH, traces):
    """Faint circuit traces from the canvas edges: 45-degree bends, a solder pad at each end."""
    acc, out = t.get("accent", t["rule"]), []
    for pts in traces:
        dpath = "M" + "L".join(f"{x} {y}" for x, y in pts)
        out.append(f'<path d="{dpath}" fill="none" stroke="{acc}" stroke-width="2" stroke-linejoin="round" opacity=".22"/>')
        x, y = pts[-1]
        out.append(f'<circle cx="{x}" cy="{y}" r="5" fill="none" stroke="{acc}" stroke-width="2" opacity=".35"/>'
                   f'<circle cx="{x}" cy="{y}" r="2" fill="{acc}" opacity=".5"/>')
    return '<g data-zone="decor" aria-hidden="true">' + "".join(out) + "</g>"


def cat(x, y, t, scale=1.0, flip=False):
    """A small sitting cat, (x, y) the middle of its base: it sits on whatever edge that is."""
    acc, ink = t.get("accent", t["rule"]), t["bg"]
    f = -1 if flip else 1
    body = (f'<path d="M-17 0Q-21 -24 -9 -33H9Q21 -24 17 0Z" fill="{acc}"/>'
            f'<circle cx="0" cy="-43" r="13" fill="{acc}"/>'
            f'<path d="M-12 -50L-9 -63L-2 -55ZM12 -50L9 -63L2 -55Z" fill="{acc}"/>'
            f'<path d="M15 -3Q34 -4 31 -22" fill="none" stroke="{acc}" stroke-width="5" stroke-linecap="round"/>'
            f'<circle cx="-5" cy="-44" r="2.2" fill="{ink}"/><circle cx="5" cy="-44" r="2.2" fill="{ink}"/>'
            f'<path d="M-2 -38Q0 -36 2 -38" fill="none" stroke="{ink}" stroke-width="1.6" stroke-linecap="round"/>')
    return (f'<g data-zone="decor" aria-hidden="true" transform="translate({x:.1f} {y:.1f}) scale({f * scale} {scale})">'
            f'{body}</g>')


def orbit(d, s, t, DH):
    """A person's capabilities as a system map: the name in the centre, capability nodes on an orbit,
    a spoke from the centre to each. For profile covers, which platforms crop to a wide band and cover
    with an avatar: `clear` keeps that circle free, and nodes sit only where the band shows them."""
    ob = s["orbit"]
    ink, acc = t["fg"], t.get("accent", t["rule"])
    cx, cy = DW / 2, ob.get("cy", DH / 2 - 30)
    rx, ry = ob.get("rx", 470), ob.get("ry", 165)
    import math
    out = [f'<defs><radialGradient id="glow"><stop offset="0" stop-color="{acc}" stop-opacity=".28"/>'
           f'<stop offset="1" stop-color="{acc}" stop-opacity="0"/></radialGradient></defs>'
           f'<ellipse cx="{cx}" cy="{cy}" rx="330" ry="230" fill="url(#glow)"/>']
    for k, a in ((1.0, .55), (1.32, .22), (1.7, .1)):         # the orbit and two fainter rings beyond it
        out.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx * k:.0f}" ry="{ry * k:.0f}" fill="none" stroke="{t["rule"]}" '
                   f'stroke-width="1.6" stroke-dasharray="3 9" opacity="{a}"/>')
    if ob.get("circuits"):
        out.append(circuits(t, DH, ob["circuits"]))
    nodes = ob["nodes"]
    angles = ob.get("angles") or [180 + i * (360 - 100) / (len(nodes) - 1) for i in range(len(nodes))]
    pos = [(cx + rx * math.cos(math.radians(a)), cy + ry * math.sin(math.radians(a))) for a in angles]
    for (x, y) in pos:                                          # spokes first, under everything
        out.append(f'<path d="M{cx} {cy}L{x:.1f} {y:.1f}" stroke="{acc}" stroke-width="1.6" opacity=".35"/>')
    # the centre: name, tagline, facts
    nz = 150
    out.append('<g data-zone="core">' + T(d, s, "title", cx, cy + 22, ob["name"], nz, ink, anchor="middle") + "</g>")
    out.append('<g data-zone="support">'
               + T(d, s, "strong", cx, cy + 72, ob["tagline"], 28, ink, anchor="middle", maxw=520)
               + (T(d, s, "text", cx, cy + 108, ob["sub"], 20, t["fg2"], anchor="middle", maxw=520) if ob.get("sub") else "") + "</g>")
    if ob.get("chip"):
        cw = dc.width(ob["chip"], 18, key(d, "strong")) + 48
        out.append(f'<g data-zone="support" data-bg="{t["cta"]}"><rect x="{cx - cw / 2:.1f}" y="{cy - 150}" width="{cw:.1f}" height="40" rx="20" fill="{t["cta"]}"/>'
                   + T(d, s, "strong", cx, cy - 124, ob["chip"], 18, t["on_cta"], anchor="middle") + "</g>")
    # the nodes: an icon disc, the label, the platform's own skill names under it
    for (x, y), nd in zip(pos, nodes):
        lw = max(dc.width(nd["label"], 20, key(d, "strong")), dc.width(nd.get("sub", ""), 14, key(d, "mono"))) + 70
        bx, by = x - lw / 2, y - 30
        out.append(f'<g data-zone="support" data-bg="{t["bg"]}">'
                   f'<rect x="{bx:.1f}" y="{by:.1f}" width="{lw:.1f}" height="60" rx="30" fill="{t["bg"]}" stroke="{t["rule"]}" stroke-width="1.6"/>'
                   f'<circle cx="{bx + 30:.1f}" cy="{y:.1f}" r="22" fill="{acc}"/>' + flow_icon(nd["icon"], bx + 30, y, t["bg"], 0.62)
                   + T(d, s, "strong", bx + 60, y - 2, nd["label"], 20, ink)
                   + (T(d, s, "mono", bx + 60, y + 18, nd["sub"], 14, t["fg2"]) if nd.get("sub") else "") + "</g>")
    if ob.get("cat") is not None:                            # a cat sitting on top of one node's card
        i = ob["cat"]["node"]
        (x, y), nd = pos[i], nodes[i]
        lw = max(dc.width(nd["label"], 20, key(d, "strong")), dc.width(nd.get("sub", ""), 14, key(d, "mono"))) + 70
        out.append(cat(x - lw / 2 + lw * ob["cat"].get("at", 0.75), y - 30, t, ob["cat"].get("scale", 0.8), ob["cat"].get("flip", False)))
    # desktop-only corners: who, availability, where to hire
    if ob.get("top_left"):
        out.append(T(d, s, "mono", M, M + 10, ob["top_left"], 18, t["fg2"]))
    if ob.get("badge"):
        bw = dc.width(ob["badge"], 16, key(d, "mono")) + 52
        out.append(f'<rect x="{DW - M - bw:.1f}" y="{M - 14}" width="{bw:.1f}" height="38" rx="19" fill="none" stroke="{acc}" stroke-width="2"/>'
                   f'<circle cx="{DW - M - bw + 20:.1f}" cy="{M + 5}" r="6" fill="{acc}"/>'
                   + T(d, s, "mono", DW - M - bw + 36, M + 10, ob["badge"], 16, ink))
    if ob.get("bottom_left"):
        out.append(T(d, s, "mono", M, DH - M + 10, ob["bottom_left"], 18, t["fg2"]))
    if ob.get("bottom_right"):
        out.append(T(d, s, "mono", DW - M, DH - M + 10, ob["bottom_right"], 18, t["fg2"], anchor="end"))
    return out


def halo(d, s, t, DH):
    """The profile photo as the hub: half-rings radiate from where the platform puts the avatar
    (`hub`), capability icons sit on the rings, the name and facts fill the sides. On desktop, where
    nothing covers the hub, `hub_mark` fills it."""
    hl = s["halo"]
    import math
    ink, acc = t["fg"], t.get("accent", t["rule"])
    hx, hy = hl.get("hub", [DW / 2, 581])
    out = [f'<defs><radialGradient id="halo"><stop offset="0" stop-color="{acc}" stop-opacity=".35"/>'
           f'<stop offset=".55" stop-color="{acc}" stop-opacity=".08"/><stop offset="1" stop-color="{acc}" stop-opacity="0"/></radialGradient></defs>'
           f'<circle cx="{hx}" cy="{hy}" r="420" fill="url(#halo)"/>']
    for r, a, dash in ((130, .7, "none"), (220, .45, "3 8"), (330, .35, "3 8"), (440, .18, "3 10"), (560, .1, "3 12")):
        out.append(f'<circle cx="{hx}" cy="{hy}" r="{r}" fill="none" stroke="{acc if r == 130 else t["rule"]}" '
                   f'stroke-width="{2.5 if r == 130 else 1.6}" stroke-dasharray="{dash}" opacity="{a}"/>')
    if hl.get("hub_mark"):
        out.append('<g data-zone="support">' + T(d, s, "title", hx, hy + 26, hl["hub_mark"], 72, ink, anchor="middle") + "</g>")
    for nd in hl["nodes"]:                                   # icon discs on the rings, a label under each
        r, ang = nd["ring"], math.radians(nd["angle"])
        x, y = hx + r * math.cos(ang), hy + r * math.sin(ang)
        out.append(f'<g data-zone="support"><circle cx="{x:.1f}" cy="{y:.1f}" r="34" fill="{t["bg"]}" stroke="{acc}" stroke-width="2.5"/>'
                   f'<circle cx="{x:.1f}" cy="{y:.1f}" r="27" fill="{acc}"/>' + flow_icon(nd["icon"], x, y, t["bg"], 0.78)
                   + T(d, s, "strong", x, y + 58, nd["label"], 18, ink, anchor="middle", maxw=190) + "</g>")
    L = hl["left"]                                           # name, tagline, site
    out.append('<g data-zone="core">' + T(d, s, "title", M + 8, L.get("y", 250), L["name"], 112, ink) + "</g>")
    out.append('<g data-zone="support">' + "".join(T(d, s, "strong", M + 8, L.get("y", 250) + 52 + i * 36, l, 26, ink, maxw=400)
                                                    for i, l in enumerate(L["tagline"])) + "</g>")
    if L.get("site"):
        sy = L.get("y", 250) + 52 + len(L["tagline"]) * 36 + 10
        sw = dc.width(L["site"], 20, key(d, "strong")) + 44
        out.append(f'<g data-zone="support" data-bg="{t["cta"]}"><rect x="{M + 8}" y="{sy}" width="{sw:.1f}" height="44" rx="22" fill="{t["cta"]}"/>'
                   + T(d, s, "strong", M + 30, sy + 29, L["site"], 20, t["on_cta"]) + "</g>")
    R = hl["right"]                                          # one big number and what it means
    rx = DW - M - 8
    out.append('<g data-zone="support">' + T(d, s, "title", rx, R.get("y", 250), R["big"], 112, acc, anchor="end")
               + "".join(T(d, s, "strong", rx, R.get("y", 250) + 44 + i * 32, l, 22, ink, anchor="end", maxw=360)
                         for i, l in enumerate(R["lines"])) + "</g>")
    if R.get("chip"):
        cw = dc.width(R["chip"], 18, key(d, "strong")) + 44
        cy = R.get("y", 250) + 44 + len(R["lines"]) * 32 + 6
        out.append(f'<g data-zone="support"><rect x="{rx - cw:.1f}" y="{cy}" width="{cw:.1f}" height="40" rx="20" fill="none" stroke="{acc}" stroke-width="2"/>'
                   + T(d, s, "strong", rx - cw / 2, cy + 27, R["chip"], 18, ink, anchor="middle") + "</g>")
    for k, anchor, x, y in (("top_left", None, M, M + 10), ("top_right", "end", DW - M, M + 10),
                            ("bottom_left", None, M, DH - M + 10), ("bottom_right", "end", DW - M, DH - M + 10)):
        if hl.get(k):
            out.append(T(d, s, "mono", x, y, hl[k], 18, t["fg2"], anchor=anchor))
    return out


def hook(d, s, t, DH):
    """The first image a buyer sees in search: one promise, a short checklist, the price, and real
    work in a browser frame. Everything else (layers, steps, samples) comes later in the gallery."""
    hk = s["hook"]
    ink, acc = t["fg"], t.get("accent", t["rule"])
    TX, TW = M + 8, 560
    out = ['<g data-zone="support">' + T(d, s, "strong", TX, M + 40, hk["kicker"], 24, t["fg3"], maxw=TW) + "</g>"]
    start = len(out) - 1                     # the text block, centred vertically once its height is known
    fam, w = key(d, "title").rsplit("-", 1)
    tz = next(z for z in (96, 88, 80, 72, 64, 56) if all(dc.width(l, z, f"{fam}-{w}") <= TW for l in hk["title"]))
    lh = round(tz * 1.15)
    ty = M + 80 + tz
    out.append('<g data-zone="core">' + "".join(T(d, s, "title", TX, ty + i * lh, l, tz, ink, maxw=TW)
                                                for i, l in enumerate(hk["title"])) + "</g>")
    cy = ty + (len(hk["title"]) - 1) * lh + 70
    rows = []
    for i, c in enumerate(hk.get("checks", [])):
        y = cy + i * 52
        rows.append(f'<circle cx="{TX + 15}" cy="{y - 9}" r="15" fill="{acc}"/>'
                    f'<path d="M{TX + 8} {y - 9}l5 5l9-10" stroke="{t["bg"]}" stroke-width="3.5" fill="none" stroke-linecap="round"/>'
                    + T(d, s, "text", TX + 44, y, c, 28, ink, maxw=TW - 44))
    out.append('<g data-zone="support">' + "".join(rows) + "</g>")
    if hk.get("price"):
        pr = hk["price"]
        py = cy + len(hk.get("checks", [])) * 52 + 20
        pw = max(dc.width(pr["value"], 44, key(d, "title")), dc.width(pr["label"], 18, key(d, "text"))) + 56
        out.append(f'<g data-bg="{t["cta"]}"><rect x="{TX}" y="{py}" width="{pw:.0f}" height="104" rx="14" fill="{t["cta"]}"/>'
                   + '<g data-zone="support">' + T(d, s, "text", TX + 28, py + 34, pr["label"], 18, t["on_cta"]) + "</g>"
                   + '<g data-zone="core">' + T(d, s, "title", TX + 28, py + 84, pr["value"], 44, t["on_cta"]) + "</g></g>")
        bottom = py + 104
    else:
        bottom = cy + len(hk.get("checks", [])) * 52
    top = M + 12
    # the workflow strip sits above the footer; everything else centres in the space above it
    flow = hk.get("flow")
    area = DH - 40 - (190 if flow else 0)
    dy = (area - (bottom - top)) / 2 - top
    out[start:] = [f'<g transform="translate(0 {dy:.1f})">' + "".join(out[start:]) + "</g>"]
    if hk.get("author"):
        out.append(T(d, s, "mono", TX, DH - M, hk["author"], 18, t["fg2"], maxw=TW))
    # the proof: real work in a browser window, vertically centred on the right
    BX, BW = TX + TW + 56, DW - M - (TX + TW + 56)
    frame, fh = browser(0, 0, BW, hk.get("image"), t, "hookshot")
    by = (area - fh) / 2 + 10
    if flow:
        out.append(flow_strip(d, s, t, TX, DW - M - 8, DH - M - 130, flow))
    out.append(f'<g data-zone="support" transform="translate({BX} {by:.1f})">{frame}</g>')
    if hk.get("client"):
        cl = hk["client"]
        lab = cl.get("label", "ผลงานจริง")
        cw = max(dc.width(cl["name"], 24, key(d, "title")), dc.width(lab, 15, key(d, "text"))) + 40
        cx, cyy = BX + BW - cw + 18, by + fh - 36
        out.append(f'<g data-zone="support" data-bg="{t["cta"]}">'
                   f'<rect x="{cx + 6:.1f}" y="{cyy + 6:.1f}" width="{cw:.1f}" height="72" rx="12" fill="{t.get("shadow", ink)}"/>'
                   f'<rect x="{cx:.1f}" y="{cyy:.1f}" width="{cw:.1f}" height="72" rx="12" fill="{t["cta"]}"/>'
                   + T(d, s, "text", cx + 20, cyy + 26, lab, 15, t["on_cta"])
                   + T(d, s, "title", cx + 20, cyy + 58, cl["name"], 24, t["on_cta"]) + "</g>")
    return out


LAYOUTS["hook"] = hook
LAYOUTS["orbit"] = orbit
LAYOUTS["halo"] = halo

def pointer(cx, cy, w, h, tx, ty, fill, dark):
    """A bent arrow from a callout plate's edge to the prop it names (the level bar to its enemy, the price
    to the key): a callout that floats free of its prop reads as UI, not as part of the scene."""
    import math
    sx, sy = min(max(tx, cx - w / 2), cx + w / 2), min(max(ty, cy - h / 2), cy + h / 2)   # nearest point on the plate
    dx, dy = tx - sx, ty - sy
    n = math.hypot(dx, dy) or 1
    ux, uy = dx / n, dy / n
    mx, my = (sx + tx) / 2 - uy * n * 0.25, (sy + ty) / 2 + ux * n * 0.25    # bend a quarter of the length sideways
    hx, hy = tx - ux * 26, ty - uy * 26                                       # the shaft stops where the head starts
    head = f"{tx:.1f},{ty:.1f} {hx - uy * 18:.1f},{hy + ux * 18:.1f} {hx + uy * 18:.1f},{hy - ux * 18:.1f}"
    shaft = f'M{sx:.1f} {sy:.1f} Q{mx:.1f} {my:.1f} {hx:.1f} {hy:.1f}'
    return (f'<g aria-hidden="true" stroke-linejoin="round" stroke-linecap="round">'
            f'<path d="{shaft}" fill="none" stroke="{dark}" stroke-width="20"/>'
            f'<polygon points="{head}" fill="{dark}" stroke="{dark}" stroke-width="10"/>'
            f'<path d="{shaft}" fill="none" stroke="{fill}" stroke-width="11"/>'
            f'<polygon points="{head}" fill="{fill}"/></g>')


def keyart(d, s, t, DH):
    """A game thumbnail: the scene full-bleed (an image model's render or vector art, no text in it), the
    title in block type with a stepped side, the update on a ribbon under it, and a few callouts pinned to
    props in the scene (a level bar over the first enemy, the price over the goal). The scene says what the
    game is; the type only names it. Colours: fg and title2 (else accent) are the title's two lines, panel the outline,
    the side and the callout plates, cta / on_cta the ribbon, `bar` (else accent) the level bar."""
    ka = s["keyart"]
    dark = t["panel"]
    out = []
    if ka.get("art"):
        out.append(image_tag(ka["art"], 0, 0, DW, DH, "art", rx=0))
    lines = ka["title"]
    left = ka.get("title_at", "top-center") == "top-left"
    TW = 560 if left else 760
    fk = key(d, "title")
    # title_max caps the size: the scene, not the name, should be the first thing seen (the critic checks)
    tz = next((z for z in (100, 92, 84, 76, 68, 64, 56) if z <= ka.get("title_max", 100)
               and all(dc.width(l, z, fk) <= TW for l in lines)), None)
    assert tz, f"title {lines} does not fit {TW}px at 56px: shorten it or break the line"
    lh, stroke, depth = round(tz * 0.98), max(6, round(tz * 0.11)), max(4, round(tz * 0.06))
    x, anchor = (M, None) if left else (DW / 2, "middle")
    ty = M + round(tz * 0.92)
    fills = (t["fg"], t.get("title2", t.get("accent", t["fg"])))
    side, face = [], []
    for i, l in enumerate(lines):
        y = ty + i * lh
        side += [T(d, s, "title", x, y + k * 2, l, tz, dark, anchor=anchor) for k in range(depth, 0, -1)]
        face.append(T(d, s, "title", x, y, l, tz, fills[i % 2], anchor=anchor, maxw=TW))
    sw = f'stroke="{dark}" stroke-width="{stroke}" stroke-linejoin="round" paint-order="stroke"'
    # ponytail: contrast is measured against the outline, the only colour sure to sit behind the letters
    out.append(f'<g data-zone="decor" aria-hidden="true" {sw}>' + "".join(side) + "</g>")
    out.append(f'<g data-zone="core" data-bg="{dark}" {sw}>' + "".join(face) + "</g>")
    if ka.get("kicker"):
        kz, rh, notch = 26, 48, 16
        ky = ty + (len(lines) - 1) * lh + stroke + depth * 2 + 18
        kw = dc.width(ka["kicker"], kz, key(d, "strong")) + 56
        kx = M + notch if left else DW / 2 - kw / 2
        pts = [(kx - notch, ky), (kx + kw + notch, ky), (kx + kw, ky + rh / 2), (kx + kw + notch, ky + rh),
               (kx - notch, ky + rh), (kx, ky + rh / 2)]          # a ribbon with swallowtail ends
        out.append(f'<g data-zone="support" data-bg="{t["cta"]}">'
                   f'<polygon points="{" ".join(f"{a:.1f},{b:.1f}" for a, b in pts)}" fill="{t["cta"]}" '
                   f'stroke="{dark}" stroke-width="4" stroke-linejoin="round"/>'
                   + T(d, s, "strong", kx + kw / 2, ky + rh / 2 + kz * 0.36, ka["kicker"], kz, t["on_cta"], anchor="middle")
                   + "</g>")
    # callout type is 28px on the 1280 grid (42px at 1920, about 9px at phone width): smaller is lost at 400px
    for i, c in enumerate(ka.get("callouts", [])):
        cx, cy = c["x"] * DW, c["y"] * DH                     # the callout's centre, as fractions of the scene
        if c["kind"] == "bar":
            bw = 170
            w, h = bw + 36, 86
            body = (T(d, s, "strong", cx - bw / 2, cy - 8, c["text"], 28, t["on_panel"])
                    + f'<rect x="{cx - bw / 2:.1f}" y="{cy + 6:.1f}" width="{bw}" height="18" rx="9" fill="{t["fg3"]}" opacity=".35"/>'
                    + f'<rect x="{cx - bw / 2:.1f}" y="{cy + 6:.1f}" width="{bw * (c["fill"] or 0):.1f}" height="18" rx="9" '
                      f'fill="{t.get("bar", t.get("accent", t["fg"]))}"/>')
        else:
            sub_ = c.get("sub") or ""
            w = max(dc.width(c["text"], 28, key(d, "strong")), dc.width(sub_, 44, key(d, "title")) if sub_ else 0) + 44
            h = 112 if sub_ else 60
            body = (T(d, s, "strong", cx, cy - 18 if sub_ else cy + 10, c["text"], 28, t["on_panel"], anchor="middle")
                    + (T(d, s, "title", cx, cy + 38, sub_, 44, t.get("accent", t["on_panel"]), anchor="middle") if sub_ else ""))
        if c.get("to"):
            out.append(pointer(cx, cy, w, h, c["to"][0] * DW, c["to"][1] * DH, t["cta"], dark))
        out.append(f'<g data-zone="support" data-bg="{dark}">'
                   f'<rect x="{cx - w / 2:.1f}" y="{cy - h / 2:.1f}" width="{w:.1f}" height="{h}" rx="12" fill="{dark}" '
                   f'stroke="{t.get("accent", t["fg"])}" stroke-width="3"/>' + body + "</g>")
    return out


LAYOUTS["keyart"] = keyart
BRAND_LEFT = ("columns", "rail", "stairs", "stack")    # layouts whose brand panel runs from x = 0


def build(s, layout, style):
    W, H = s["size"]
    # "content_ratio": [4, 3] draws everything inside the centred 4:3 area of the canvas, for places
    # that crop the image (Fastwork's service card shows a 4:3 centre crop of a 16:9 upload)
    ratio = s.get("content_ratio")
    CW = round(H * ratio[0] / ratio[1]) if ratio else W
    assert CW <= W, f"content_ratio {ratio} is wider than the {W}x{H} canvas"
    ox = (W - CW) / 2
    k = CW / DW
    DH = round(H / k)
    assert DH >= 600, f"{W}x{H} is too wide for these layouts (needs >= 1280x600 in proportion)"
    t = s["_styles"][style]
    d = dc.Doc()
    d.fonts = s.get("fonts", {})
    if d.fonts:
        # layouts written for Archivo / JetBrains Mono call d.t directly; with "fonts" set, map those calls
        # to roles by weight (mono, bold = title, regular = text) so Thai text gets a Thai family
        plain = d.t
        def themed(x, y, text, size, fill, w=500, mono=False, family=None, **kw):
            if family:
                return plain(x, y, text, size, fill, w, family=family, **kw)
            fam, fw = key(d, "mono" if mono else ("title" if w >= 700 else "text")).rsplit("-", 1)
            if fam in ("arc", "jbm"):
                return plain(x, y, text, size, fill, int(fw), mono=fam == "jbm", **kw)
            return plain(x, y, text, size, fill, int(fw), family=fam, **kw)
        d.t = themed
    body = LAYOUTS[layout](d, s, t, DH)
    if layout == "keyart":
        ka = s["keyart"]
        label = ". ".join(p for p in (" ".join(ka["title"]) + (f": {ka['kicker']}" if ka.get("kicker") else ""),
                                      ka.get("is"), ka.get("loop"), ka.get("goal")) if p)
    elif layout == "halo":
        hl = s["halo"]
        label = f"{hl['left']['name']}: {' '.join(hl['left']['tagline'])}. " + ", ".join(n["label"] for n in hl["nodes"])
    elif layout == "orbit":
        ob = s["orbit"]
        label = f"{ob['name']}: {ob['tagline']}. " + ", ".join(f"{n['label']} ({n.get('sub', '')})" for n in ob["nodes"])
    elif layout == "hook":
        hk = s["hook"]
        label = (f"{hk['kicker']}: {' '.join(hk['title'])}. {' '.join(hk.get('checks', []))}. "
                 f"{hk.get('price', {}).get('label', '')} {hk.get('price', {}).get('value', '')}").strip()
    elif layout == "showcase":
        sc = s["showcase"]
        label = f"{sc['kicker']}: {sc['title']}. {' '.join(sc.get('caption', []))} {sc.get('placeholder', '') if not (sc.get('image') or sc.get('images')) else ''}".strip()
    elif layout == "step":
        st = s["step"]
        label = f"{st['kicker']}. {st['num']} {' '.join(st['title'])}. {' '.join(st.get('caption', []))}"
    elif layout == "cover":
        cv = s["cover"]
        label = f"{cv['kicker']}: {' '.join(cv['title'])}. {cv.get('note', '')} {cv.get('author', '')}".strip()
    else:
        b, c = s["brand"], s["cta"]
        label = (f"{b['name']}: {' '.join(b['promise'])} "
                 + " ".join(f"{st['num']} {st['verb']}: {' '.join(st['line'])}"
                            + (f" ({', '.join(i['name'] for i in st.get('items', []))})." if st.get("items") else ".")
                            for st in s["steps"])
                 + f" {c['verb']}: {c.get('detail', '')}")
    css = (dc.embed_fonts(d.text) + dc.embed_extra(d)
           + ".a{font-family:A,'Helvetica Neue',Arial,sans-serif}"
           + ".m{font-family:M,ui-monospace,SFMono-Regular,Menlo,monospace;white-space:pre}")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
            f'role="img" aria-label="{escape(label)}" data-bg="{t["bg"]}"><title>{escape(label)}</title>'
            f'<style>{css}</style><rect width="{W}" height="{H}" fill="{t["bg"]}"/>{ground(t, k)}'
            + (f'<rect width="{ox + 1:g}" height="{H}" fill="{t["panel"]}"/>' if ox and layout in BRAND_LEFT else "")
            + f'<g transform="translate({ox:g} 0) scale({k:g})">{"".join(body)}</g></svg>')


def jobs(s, picked=()):
    """(spec, layout, style, file prefix) for every image a spec makes."""
    if "pages" in s:
        # a post: every page names its layout; "render" lists the styles (a page may override it)
        return [(dict(s, **pg), pg["layout"], st, pg["id"]) for pg in s["pages"]
                for st in pg.get("render", s["render"])]
    if "keyart" in s:
        # a thumbnail set: one image per variant row, each its own scene and ribbon (Roblox tests 2-5 at once)
        ka = s["keyart"]
        # a callout with `only` set belongs to those variants, space-separated (no key price in the summit scene)
        # a variant aimed at another motivation may promise another goal (`goal` column), so its critic scores that
        return [(dict(s, keyart=dict(ka, art=v.get("art") or ka["art"], kicker=v.get("kicker") or ka["kicker"],
                                     goal=v.get("goal") or ka["goal"], loop=v.get("loop") or ka["loop"],
                                     callouts=[c for c in ka["callouts"] if not c.get("only") or v["id"] in c["only"].split()])),
                 "keyart", s["style"], f"keyart-{v['id']}") for v in ka["variants"]] \
            or [(s, "keyart", s["style"], "keyart")]
    return [(s, *v.split("-", 1), None) for v in picked or s["variants"]]


def selftest():
    assert wrap("dependency-vuln-explainer", 100, 14) == ["dependency-", "vuln-", "explainer"]
    assert wrap("a, b, c", 1000, 14, sep=r"[^ ]+ ?") == ["a, b, c"]
    s = {"size": [1920, 1080], "brand": {"name": "Name", "promise": ["one", "two"]},
         "steps": [{"num": f"0{i}", "verb": "Verb", "line": ["a", "b"], "items": [{"name": "x"}]} for i in range(1, 5)],
         "cta": {"verb": "Go"}, "_styles": STYLES}
    for lay in (l for l in LAYOUTS if l not in ("cover", "step", "showcase", "hook", "orbit", "halo", "keyart")):
        svg = build(s, lay, "flat")
        __import__("xml.dom.minidom").dom.minidom.parseString(svg)
        assert 'viewBox="0 0 1920 1080"' in svg and "scale(1.5)" in svg, lay
    c = dict(s, size=[1200, 630], cover={"kicker": "ทดสอบ", "title": ["หัวข้อทดสอบ", "บรรทัดสอง"],
                                         "note": "ทดลอง", "author": "a", "motif": ["columns", "stack"]},
             fonts={"title": "kanit-700", "strong": "anuphan-700", "text": "anuphan-500", "accent": "mali-600"})
    svg = build(c, "cover", "flat")
    import xml.dom.minidom
    xml.dom.minidom.parseString(svg)            # every layout must be well-formed XML
    assert "@font-face{font-family:kanit" in svg and 'data-zone="decor"' in svg, "cover: Thai fonts and decor zone"
    from fontTools.ttLib import TTFont
    import base64, io, re as _re
    kanit = _re.search(r"font-family:kanit;font-weight:700;src:url\(data:font/woff2;base64,([^)]+)\)", svg).group(1)
    cmap = TTFont(io.BytesIO(base64.b64decode(kanit))).getBestCmap()
    c2 = dict(c, cover=dict(c["cover"], title=["ทำแบนเนอร์"]))
    kanit = _re.search(r"font-family:kanit;font-weight:700;src:url\(data:font/woff2;base64,([^)]+)\)", build(c2, "cover", "flat")).group(1)
    cmap = TTFont(io.BytesIO(base64.b64decode(kanit))).getBestCmap()
    assert 0x0E4D in cmap and 0x0E32 in cmap, "SARA AM needs NIKHAHIT + SARA AA in the subset cmap"
    sp = dict(c, size=[1200, 675], step={"kicker": "ขั้นที่ 1", "num": "01", "title": ["ทดสอบ"], "caption": ["ทดลอง"],
                                          "visual": {"kind": "checks", "rows": [{"mark": "fail", "text": "ทดสอบ"}, {"mark": "pass", "text": "ok"}]}})
    xml.dom.minidom.parseString(build(sp, "step", "flat"))
    sh = dict(c, size=[1920, 1080], showcase={"kicker": "ผลงาน", "title": "ทดสอบ", "caption": ["ทดลอง"], "placeholder": "Coming soon",
                                                "tags": ["Cloud"], "author": "a"})
    assert "Coming soon" in build(sh, "showcase", "flat")
    import tempfile, struct, zlib
    png = tempfile.NamedTemporaryFile(suffix=".png", delete=False)    # a 2x1 PNG, enough to embed
    raw = b"\x00" + b"\xff\x00\x00" * 2
    chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    png.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 1, 8, 2, 0, 0, 0))
              + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")); png.close()
    three = build(dict(sh, showcase=dict(sh["showcase"], images=[png.name] * 3)), "showcase", "flat")
    assert three.count("<image ") == 3 and "Coming soon" not in three, "three screenshots replace the placeholder"
    ks = keyart_spec(load_toon(
        "id: t\nsize[2]: 1920,1080\nsizes[2]: 1920x1080,1280x720\nis: a game\nloop: fight\ngoal: a key\n"
        "title[2]: TEST,QUEST\nkicker: UPDATE\nstyle: dark\ncolors[1]{token,value}:\n  cta,#C8102E\n"
        "anchors[1]{beat,anchor,where}:\n  goal,key,right\n"
        "callouts[2]{kind,text,sub,x,y,fill,only,tx,ty}:\n  badge,KEY,\"1,000 GOLD\",0.7,0.6,,a c,0.8,0.8\n  bar,LVL 5,,0.1,0.6,0.4,,,\n"
        "variants[2]{id,motivation,art,kicker,goal,loop}:\n  a,competition,,,,\n  b,exploration,,NEW,the top,climb\n"))
    assert ks["sizes"] == [[1920, 1080], [1280, 720]] and ks["style"] == "t", "sizes and a palette over a preset"
    assert ks["keyart"]["callouts"][0]["sub"] == "1,000 GOLD" and math.isclose(ks["keyart"]["callouts"][1]["fill"], 0.4)
    ks["_styles"] = dict(STYLES, **ks["styles"])
    ks["keyart"]["art"] = png.name
    js = jobs(ks)
    assert [(j[3], j[0]["keyart"]["kicker"]) for j in js] == [("keyart-a", "UPDATE"), ("keyart-b", "NEW")], "a file per variant"
    assert [len(j[0]["keyart"]["callouts"]) for j in js] == [2, 1], "a callout marked `only` stays in its variant"
    assert all(map(math.isclose, ks["keyart"]["callouts"][0]["to"], (0.8, 0.8))) and ks["keyart"]["callouts"][1]["to"] is None, "tx, ty: the pointer target"
    assert [j[0]["keyart"]["goal"] for j in js] == ["a key", "the top"], "a variant's own goal overrides the brief's"
    assert [j[0]["keyart"]["loop"] for j in js] == ["fight", "climb"], "and its own loop"
    capped = build(dict(js[0][0], keyart=dict(js[0][0]["keyart"], title_max=64)), "keyart", "t")
    assert 'font-size="64"' in capped and 'font-size="100"' not in capped, "title_max caps the title size"
    ka = build(js[0][0], "keyart", "t")
    xml.dom.minidom.parseString(ka)
    assert ka.count("<image ") == 1 and 'data-bg="#C8102E"' in ka and "TEST QUEST: UPDATE. a game" in ka
    assert ka.count("<polygon points=") == 3, "the ribbon plus one pointer head (outline and fill)"
    try:
        keyart_spec(load_toon("id: t\nsize[2]: 1,1\ntitle[1]: T\nanchors[6]{beat,anchor,where}:\n" + "  a,b,c\n" * 6))
        raise SystemExit("six anchors must be refused")
    except AssertionError:
        pass
    os.unlink(png.name)
    th = dict(s, fonts={"title": "kanit-700", "text": "anuphan-500", "mono": "anuphan-500"},
              steps=[dict(st, verb="หน้าเว็บ", items=[{"name": "ทดสอบ"}]) for st in s["steps"]])
    assert "font-family:kanit" in build(th, "stack", "flat"), "a spec with fonts gets Thai in the step layouts"
    hk = build(dict(sh, hook={"kicker": "ทดสอบ", "title": ["ทดสอบ"], "checks": ["ทดลอง"],
                              "price": {"label": "เริ่มต้น", "value": "1,000"}, "image": None}), "hook", "flat")
    xml.dom.minidom.parseString(hk)
    ob = build(dict(sh, orbit={"name": "Name", "tagline": "ทดสอบ", "angles": [180, 0],
                               "nodes": [{"icon": "ui", "label": "ทดสอบ"}, {"icon": "ai", "label": "ทดลอง"}]}), "orbit", "flat")
    xml.dom.minidom.parseString(ob)
    narrow = build(dict(sh, content_ratio=[4, 3]), "showcase", "flat")
    assert 'translate(240 0) scale(1.125)' in narrow, "1920x1080 at 4:3 content: 1440 wide, centred"
    print("selftest ok")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("spec", nargs="?")
    ap.add_argument("variants", nargs="*", help="layout-style pairs; default: the spec's variants")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest(); sys.exit(0)
    if not a.spec:
        ap.error("give a spec file or --selftest")
    s = load(a.spec)
    for spec, layout, style, pid in jobs(s, a.variants):
        for W, H in spec.get("sizes") or [spec["size"]]:   # one spec, several placements (OG card, 16:9 post)
            spec = dict(spec, size=[W, H])
            path = os.path.join(s["_dir"], f"{pid or layout}-{style}-{W}x{H}.svg")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(build(spec, layout, style))
            print(os.path.relpath(path))
