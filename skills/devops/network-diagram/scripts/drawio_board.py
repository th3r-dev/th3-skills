# /// script
# requires-python = ">=3.10"
# dependencies = ["pymupdf>=1.24", "numpy", "pillow"]
# ///
"""System / network diagram boards inside one .drawio canvas.

The team keeps every diagram version on ONE draw.io page, one board per page
tile (pageWidth x pageHeight, e.g. A2 landscape): Non-prod 1.1.3 beside Prod 1.1.5,
then 1.1.6 and 1.1.7 stacked below. A board is "the tile that holds a
`Version x.y.z Update dd/mm/yyyy` label". A plain `draw.io -x -f pdf` exports
every tile (6 pages, 2 blank), so this script cuts one board out instead.

  list    <file.drawio>                          boards on every page
  clone   <file.drawio> --from 1.1.7 --version 1.1.8 [--date 06/11/2026]
          copy a board into the free tile below it, new ids, new label (in place,
          a .bak copy is kept) -> edit that board in draw.io
  export  <file.drawio> --version 1.1.7 [--out DIR]
          -> <DIR>/<title> <Env> <ver> - <ddmmyy>.pdf   (--name changes the pattern)
             + the same name .drawio holding that board alone (editable)
  trace   <final.pdf> --out X.drawio [--assign X,Y=slug]
          rebuild an editable .drawio from a final PDF: text, boxes, lines, arrows from
          the vectors; every icon slot filled from assets/icons (team logo or draw.io
          built-in), never from the PDF. Prints which icon went where.
  compare <reference.pdf> <candidate.pdf> [--no-image-check]
          benchmark, exit 1 on FAIL (--no-image-check: icons were swapped on purpose)
"""
from __future__ import annotations

import argparse
import base64
import collections
import copy
import re
import shutil
import subprocess
import sys
import uuid
import zlib
import xml.etree.ElementTree as ET
from html import unescape
from pathlib import Path
from urllib.parse import unquote

DEFAULT_OUT = Path("diagram-out")
VERSION_RE = re.compile(r"Version\s+(\d+(?:\.\d+)+)\s+Update\s+(\d{2})/(\d{2})/(\d{4})")
ENV_NAME = {"Production": "Prd", "Non Production": "Uat"}   # --env-map overrides
TITLE_SUFFIX = "System Diagram"                                 # --title-suffix overrides
THAI_FONT = "Sarabun"


# ---------- drawio model ----------

def drawio_cli() -> str:
    for c in ("drawio", "draw.io", "/Applications/draw.io.app/Contents/MacOS/draw.io"):
        p = shutil.which(c) or (c if Path(c).exists() else None)
        if p:
            return p
    sys.exit("draw.io desktop not found (brew install --cask drawio)")


def load(path: Path) -> ET.ElementTree:
    tree = ET.parse(path)
    for d in tree.getroot().iter("diagram"):
        if d.find("mxGraphModel") is None and (d.text or "").strip():  # compressed page
            raw = zlib.decompress(base64.b64decode(d.text.strip()), -15).decode()
            d.text = None
            d.append(ET.fromstring(unquote(raw)))
    return tree


def plain(v: str | None) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", unescape(v or "")))).strip()


class Page:
    """One <diagram>. Elements are <mxCell> or an <object>/<UserObject> wrapping one."""

    def __init__(self, diagram: ET.Element):
        self.diagram = diagram
        self.model = diagram.find("mxGraphModel")
        self.root = self.model.find("root")
        self.W = float(self.model.get("pageWidth", 1169)) * float(self.model.get("pageScale", 1))
        self.H = float(self.model.get("pageHeight", 827)) * float(self.model.get("pageScale", 1))
        self.els = list(self.root)
        self.byid = {e.get("id"): e for e in self.els}
        self.kids = collections.defaultdict(list)
        for e in self.els:
            self.kids[self.cell(e).get("parent")].append(e)
        self.layers = [e.get("id") for e in self.kids.get(self.cell(self.els[0]).get("id") if self.els else None, [])]

    @staticmethod
    def cell(e):
        return e if e.tag == "mxCell" else (e.find("mxCell") if e.find("mxCell") is not None else e)

    def text(self, e):
        return plain(e.get("value") if e.tag == "mxCell" else e.get("label"))

    def geo(self, e):
        return self.cell(e).find("mxGeometry")

    def center(self, e, depth=0):
        """Absolute centre of a top-level element (vertex or edge), or None."""
        c, g = self.cell(e), self.geo(e)
        if c.get("edge") == "1":
            pts = []
            for term, key in (("source", "sourcePoint"), ("target", "targetPoint")):
                t = self.byid.get(c.get(term))
                if t is not None and depth < 3:
                    p = self.center(self.top(t), depth + 1)
                    if p: pts.append(p)
                elif g is not None:
                    m = g.find(f"mxPoint[@as='{key}']")
                    if m is not None: pts.append((float(m.get("x", 0)), float(m.get("y", 0))))
            if g is not None and g.find("Array") is not None:
                pts += [(float(m.get("x", 0)), float(m.get("y", 0))) for m in g.find("Array")]
            return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)) if pts else None
        if g is None:
            return None
        return (float(g.get("x", 0)) + float(g.get("width", 0)) / 2,
                float(g.get("y", 0)) + float(g.get("height", 0)) / 2)

    def top(self, e):
        """Climb to the ancestor that sits directly on a layer (its geometry is absolute)."""
        while self.cell(e).get("parent") not in self.layers and self.cell(e).get("parent") in self.byid:
            e = self.byid[self.cell(e).get("parent")]
        return e

    def tile(self, e):
        c = self.center(e)
        return None if c is None else (int(c[0] // self.W), int(c[1] // self.H))

    def tiles(self):
        t = collections.defaultdict(list)
        for lid in self.layers:
            for e in self.kids[lid]:
                k = self.tile(e)
                if k is not None:
                    t[k].append(e)
        return t

    def subtree(self, e):
        out = [e]
        for k in self.kids[e.get("id")]:
            out += self.subtree(k)
        return out

    def boards(self):
        res = []
        for k, tops in sorted(self.tiles().items(), key=lambda kv: (kv[0][1], kv[0][0])):
            texts = [self.text(x) for t in tops for x in self.subtree(t)]
            ver = next((m for m in map(VERSION_RE.search, texts) if m), None)
            title = next((s for s in texts if s.endswith(TITLE_SUFFIX)), "")
            res.append(dict(tile=k, tops=tops, version=ver.group(1) if ver else None,
                            date=ver.group(2, 3, 4) if ver else None, title=title,
                            cells=sum(len(self.subtree(t)) for t in tops)))
        return res


def shift_geo(g, dx, dy):
    if g is None:
        return
    for el in [g, *g.iter("mxPoint")]:
        for a, d in (("x", dx), ("y", dy)):
            if el is g and g.get("relative") == "1":
                continue  # edge-label geometry is relative
            if el.get(a) is not None or el is not g:
                el.set(a, f"{float(el.get(a, 0)) + d:g}")


def find_board(pages, version):
    hits = [(p, b) for p in pages for b in p.boards() if b["version"] == version]
    if not hits:
        sys.exit(f"no board labelled 'Version {version}' — run: list")
    if len(hits) > 1:
        sys.exit(f"{len(hits)} boards labelled 'Version {version}' — rename one first")
    return hits[0]


def pages_of(tree):
    return [Page(d) for d in tree.getroot().iter("diagram")]


# ---------- commands ----------

def cmd_list(a):
    for p in pages_of(load(a.file)):
        print(f"page '{p.diagram.get('name')}'  tile {p.W:g}x{p.H:g}")
        for b in p.boards():
            v = f"v{b['version']} {'/'.join(b['date'])}" if b["version"] else "(no version label)"
            print(f"  tile {b['tile']}  {v:24} {b['cells']:4} cells  {b['title']}")


def cmd_export(a):
    tree = load(a.file)
    page, b = find_board(pages_of(tree), a.version)
    col, row = b["tile"]
    dx, dy = -col * page.W, -row * page.H
    keep = {id(t) for t in b["tops"]}
    # board-alone model: drop other tiles' top-level elements, move this tile to the origin
    for lid in page.layers:
        for e in page.kids[lid]:
            if id(e) not in keep:
                for x in page.subtree(e):
                    page.root.remove(x)
            else:
                shift_geo(page.geo(e), dx, dy)
    left = {x.get("id") for x in page.root}
    for x in page.root:  # an edge must not point at a dropped cell
        c = page.cell(x)
        for t in ("source", "target"):
            if c.get(t) and c.get(t) not in left:
                print(f"  warn: {x.get('id')} {t} {c.get(t)} is outside the board — detached")
                del c.attrib[t]
    for d in list(tree.getroot()):
        if d is not page.diagram:
            tree.getroot().remove(d)
    page.diagram.set("name", f"{b['title'] or 'System Diagram'} {a.version}")

    env = next((v for k, v in sorted(ENV_NAME.items(), key=lambda kv: -len(kv[0])) if b["title"].startswith(k)), "Prd")
    dd, mm, yyyy = b["date"]
    out = Path(a.out).resolve() if a.out else DEFAULT_OUT
    out.mkdir(parents=True, exist_ok=True)
    title = a.title or b["title"] or TITLE_SUFFIX
    stem = a.name.format(title=title, env=env, version=a.version, ddmmyy=f"{dd}{mm}{yyyy[2:]}", ddmmyyyy=f"{dd}{mm}{yyyy}")
    src = out / f"{stem}.drawio"
    tree.write(src, encoding="utf-8", xml_declaration=False)
    pdf = out / f"{stem}.pdf"
    r = subprocess.run([drawio_cli(), "-x", "-f", "pdf", "-o", str(pdf), str(src)],
                       capture_output=True, text=True)
    if r.returncode or not pdf.exists():
        sys.exit(f"draw.io export failed:\n{r.stderr[-800:]}")
    # A cell poking a few px past the tile edge makes draw.io open a sliver page beside the
    # board (the title box at x=-6 does). Keep the page holding the version label; a dropped
    # page with words on it is a real spill and fails.
    import pymupdf
    doc = pymupdf.open(pdf)
    main = next((i for i, pg in enumerate(doc) if f"Version {a.version}" in pg.get_text()), 0)
    spill = [i for i, pg in enumerate(doc) if i != main and pg.get_text().strip()]
    if spill:
        sys.exit(f"board spills over its page tile onto page(s) {spill} — move those cells back inside it in draw.io")
    if doc.page_count > 1:
        doc.select([main])
        doc.save(pdf.with_suffix(".tmp"))
        pdf.with_suffix(".tmp").replace(pdf)
    print(f"{src}\n{pdf}  (1 page, {doc[0].rect.width:.0f}x{doc[0].rect.height:.0f}pt)")


def cmd_clone(a):
    tree = load(a.file)
    page, b = find_board(pages_of(tree), getattr(a, "from"))
    taken = set(page.tiles())
    col, row = b["tile"]
    dest = next((col, r) for r in range(row + 1, row + 99) if (col, r) not in taken)
    dx, dy = (dest[0] - col) * page.W, (dest[1] - row) * page.H
    old = [x for t in b["tops"] for x in page.subtree(t)]
    pre = uuid.uuid4().hex[:8]
    ids = {x.get("id"): f"{pre}-{i}" for i, x in enumerate(old)}
    tops = {id(t) for t in b["tops"]}
    dd, mm, yyyy = (a.date or __import__("datetime").date.today().strftime("%d/%m/%Y")).split("/")
    for x in old:
        n = copy.deepcopy(x)
        n.set("id", ids[x.get("id")])
        c = page.cell(n)
        for k in ("parent", "source", "target"):
            if c.get(k) in ids:
                c.set(k, ids[c.get(k)])
        if id(x) in tops:
            shift_geo(page.geo(n), dx, dy)
        lab = "value" if n.tag == "mxCell" else "label"
        if n.get(lab) and VERSION_RE.search(plain(n.get(lab))):
            n.set(lab, re.sub(r"Version\s+[\d.]+\s+Update\s+\d{2}/\d{2}/\d{4}",
                              f"Version {a.version} Update {dd}/{mm}/{yyyy}", unescape(n.get(lab))))
        page.root.append(n)
    shutil.copy2(a.file, a.file.with_suffix(a.file.suffix + ".bak"))
    tree.write(a.file, encoding="utf-8", xml_declaration=False)
    print(f"v{a.version} = copy of v{getattr(a, 'from')} at tile {dest}  ({len(old)} cells)  backup: {a.file.name}.bak")


def cmd_compare(a):
    import numpy as np
    import pymupdf
    from PIL import Image

    R, C = pymupdf.open(a.ref), pymupdf.open(a.cand)
    if not R[0].get_text().strip():
        sys.exit(f"reference has no text layer ({R[0].rect.width:.0f}x{R[0].rect.height:.0f}pt, creator "
                 f"{R.metadata.get('producer') or R.metadata.get('creator')!r}) — printed with text as outlines "
                 "(e.g. Microsoft Print to PDF), so there is nothing to align on. Compare by eye, or against a "
                 "draw.io-exported PDF of the same version.")
    rows = []

    def check(name, ok, detail):
        rows.append((name, ok, detail))

    check("one page", C.page_count == 1, f"candidate {C.page_count} page(s), reference {R.page_count}")
    r, c = R[0], C[0]
    same = abs(r.rect.width - c.rect.width) < 1 and abs(r.rect.height - c.rect.height) < 1
    check("same page size", same, f"{c.rect.width:.0f}x{c.rect.height:.0f}pt vs {r.rect.width:.0f}x{r.rect.height:.0f}pt")
    tr = collections.Counter(w[4] for w in r.get_text("words"))
    tc = collections.Counter(w[4] for w in c.get_text("words"))
    miss, extra = tr - tc, tc - tr
    check("same text", not miss and not extra,
          f"{sum(tc.values())} words; missing {dict(miss) or '-'}; extra {dict(extra) or '-'}")
    if not a.no_image_check:
        check("same images", len(r.get_images()) == len(c.get_images()), f"{len(c.get_images())} vs {len(r.get_images())}")
        nd_r, nd_c = len(r.get_drawings()), len(c.get_drawings())
        check("same vector paths", abs(nd_r - nd_c) <= max(2, nd_r // 100), f"{nd_c} vs {nd_r}")

    # layout: fit candidate -> reference (uniform scale + shift) on words that occur once in both
    uniq = lambda p: {w[4]: w for w in p.get_text("words") if (tr[w[4]] == 1 and tc[w[4]] == 1)}
    ur, uc = uniq(r), uniq(c)
    keys = sorted(set(ur) & set(uc))
    if len(keys) >= 5:
        P = np.array([[(uc[k][0] + uc[k][2]) / 2, (uc[k][1] + uc[k][3]) / 2] for k in keys])
        Q = np.array([[(ur[k][0] + ur[k][2]) / 2, (ur[k][1] + ur[k][3]) / 2] for k in keys])
        M = np.c_[P.reshape(-1, 1), np.tile([[1, 0], [0, 1]], (len(P), 1))]
        sol = np.linalg.lstsq(M, Q.reshape(-1), rcond=None)[0]
        s, tx, ty = sol
        err = np.abs(M @ sol - Q.reshape(-1)).reshape(-1, 2).max(axis=1)
        res = err.max()
        worst = ", ".join(f"{keys[i]!r} {err[i]:.1f}" for i in np.argsort(-err)[:3])
        check("same layout", res < 3, f"{len(keys)} anchor words, worst {res:.2f}pt after scale {s:.4f} "
                                      f"shift ({tx:.1f},{ty:.1f})pt; worst: {worst}")
    else:
        s, tx, ty = 1, 0, 0
        check("same layout", False, "too few shared words to align")

    # pixels: render the candidate through the fitted transform, then compare ink with a
    # 2 px tolerance (anti-aliasing moves thin lines by a pixel; that is not a difference).
    from PIL import ImageFilter
    z = 100 / 72
    pr = r.get_pixmap(matrix=pymupdf.Matrix(z, z))
    ir = Image.frombytes("RGB", (pr.width, pr.height), pr.samples)
    pc = c.get_pixmap(matrix=pymupdf.Matrix(s * z, s * z))
    canvas = Image.new("RGB", ir.size, "white")
    canvas.paste(Image.frombytes("RGB", (pc.width, pc.height), pc.samples), (round(tx * z), round(ty * z)))
    mr = ir.convert("L").point(lambda v: 255 if v < 200 else 0)
    mc = canvas.convert("L").point(lambda v: 255 if v < 200 else 0)
    grow = lambda m: np.array(m.filter(ImageFilter.MaxFilter(5))) > 0
    Ar, Ac = np.array(mr) > 0, np.array(mc) > 0
    if a.no_image_check:  # icons are swapped on purpose: leave every reference icon slot out
        keep = np.ones_like(Ar)
        for zn in icon_zones(r):
            x0, y0, x1, y1 = (round(v * z) for v in zn["rect"] + (-3, -3, 3, 3))
            keep[max(y0, 0):y1, max(x0, 0):x1] = False
        Ar, Ac = Ar & keep, Ac & keep
    only_r, only_c = Ar & ~grow(mc), Ac & ~grow(mr)
    frac = (only_r.sum() + only_c.sum()) / max(Ar.sum() + Ac.sum(), 1)
    check("same pixels", frac < a.pixel_tol,
          f"{only_r.sum()} px only in reference, {only_c.sum()} only in candidate = {100 * frac:.2f}% of ink (2 px tolerance, limit {100 * a.pixel_tol:g}%)")
    if a.diff_png:  # grey = both, red = only in reference, blue = only in candidate
        out = np.full((*Ar.shape, 3), 255, np.uint8)
        out[Ar | Ac] = (200, 200, 200)
        out[only_r] = (220, 0, 0)
        out[only_c] = (0, 80, 255)
        Image.fromarray(out).save(a.diff_png)

    w = max(len(n) for n, _, _ in rows)
    for n, ok, det in rows:
        print(f"{'PASS' if ok else 'FAIL'}  {n:<{w}}  {det}")
    passed = sum(ok for _, ok, _ in rows)
    print(f"{passed}/{len(rows)} checks passed")
    sys.exit(0 if passed == len(rows) else 1)


# ---------- trace: final PDF -> editable drawio (icons from the library, never from the PDF) ----------

ICONS = Path(__file__).resolve().parents[1] / "assets" / "icons"


def icon_library():
    import json
    lib = json.loads((ICONS / "icons.json").read_text())["icons"]
    for i in lib:
        i["rx"] = re.compile(i["match"], re.I)
        if i.get("file"):
            raw = (ICONS / i["file"]).read_bytes()
            mime = "svg+xml" if i["file"].endswith(".svg") else "png"
            i["style"] = (f"shape=image;aspect=fixed;imageAspect=1;html=1;verticalLabelPosition=bottom;"
                          f"verticalAlign=top;image=data:image/{mime},{base64.b64encode(raw).decode()};")
    return {i["slug"]: i for i in lib}


def hexcol(c):
    if c is None:
        return "none"
    if isinstance(c, int):
        return f"#{c:06X}"
    return "#" + "".join(f"{round(v * 255):02X}" for v in c[:3])


def icon_zones(page):
    """Bitmaps + vector icons (curve seeds grown over touching small paths). Shared with compare."""
    import pymupdf
    zones = [dict(rect=pymupdf.Rect(im["bbox"]), kind="image", paths=set()) for im in page.get_image_info()]
    ds = page.get_drawings()
    small = lambda r: max(r.width, r.height) < 45
    grey = lambda c: c is not None and max(c) - min(c) < .05 and .25 < c[0] < .85
    lonly = lambda e: {it[0] for it in e["items"]} == {"l"}
    arrow = lambda e: e["fill"] and lonly(e) and len(e["items"]) <= 5 and not grey(e["fill"])
    dashes = lambda e: e["fill"] and lonly(e) and len(e["items"]) > 8 and min(e["rect"].width, e["rect"].height) < 2.5
    # seeds: anything with curves (actor, phone, logos) or a grey cube face (server icon)
    for i, d in enumerate(ds):
        curved = any(it[0] == "c" for it in d["items"])
        cube = d["fill"] and lonly(d) and len(d["items"]) <= 5 and grey(d["fill"]) and small(d["rect"])
        if not (curved or cube) or any(i in z["paths"] for z in zones):
            continue
        z = dict(rect=pymupdf.Rect(d["rect"]), kind="vector", paths={i})
        grew = True
        while grew:
            grew = False
            near = z["rect"] + (-1.5, -1.5, 1.5, 1.5)
            for j, e in enumerate(ds):
                black_stroke = e["type"] == "s" and e["color"] is not None and max(e["color"]) < .1
                outline = black_stroke and {it[0] for it in e["items"]} == {"qu"}   # arrowhead outline
                if j not in z["paths"] and small(e["rect"]) and near.intersects(e["rect"]) and not arrow(e) \
                        and not dashes(e) and not outline and not (cube and black_stroke) \
                        and not pymupdf.Rect(e["rect"]).contains(page.rect):
                    z["paths"].add(j); z["rect"] |= e["rect"]; grew = True
        seed = pymupdf.Rect(d["rect"])
        circle = curved and all(it[0] == "c" for it in d["items"]) and abs(seed.width - seed.height) < 1 and d["fill"]
        if circle and z["rect"].width * z["rect"].height < 2 * seed.width * seed.height:
            z["kind"], z["rect"] = "dot", seed  # junction dot, not an icon
        z["fill"] = d["fill"]
        zones.append(z)
    return zones


def dash_style(d, k):
    """draw.io dash style measured off the PDF path (fixDash=1: pattern in px, not x strokeWidth)."""
    import statistics as st
    if d.get("type") == "s" and d.get("dashes") and d["dashes"] != "[] 0":
        nums = [float(v) * k for v in re.findall(r"[\d.]+", d["dashes"].split("]")[0])]
        return f"dashed=1;fixDash=1;dashPattern={' '.join(f'{v:.0f}' for v in nums)};" if nums else "dashed=1;"
    pieces, cur = [], []  # Skia fill: one closed quad per dash
    for it in d["items"]:
        if cur and (abs(it[1].x - cur[-1].x) > .3 or abs(it[1].y - cur[-1].y) > .3):
            pieces.append(cur); cur = []
        cur += [it[1], it[2]]
    pieces.append(cur)
    boxes = [(min(p.x for p in q), min(p.y for p in q), max(p.x for p in q), max(p.y for p in q)) for q in pieces if q]
    dash = st.median(max(b[2] - b[0], b[3] - b[1]) for b in boxes)
    gaps = []
    for horiz in (True, False):
        rows = {}
        for b in boxes:
            if ((b[2] - b[0]) >= (b[3] - b[1])) == horiz:
                rows.setdefault(round(b[1] if horiz else b[0]), []).append(b)
        for row in rows.values():
            row.sort(key=lambda b: b[0] if horiz else b[1])
            gaps += [(n[0] - p_[2]) if horiz else (n[1] - p_[3]) for p_, n in zip(row, row[1:])]
    gaps = [g for g in gaps if 0 < g < 4 * dash]
    gap = st.median(gaps) if gaps else dash
    return f"dashed=1;fixDash=1;dashPattern={dash * k:.0f} {gap * k:.0f};"


def cmd_trace(a):
    import json
    import pymupdf
    pg = pymupdf.open(a.pdf)[a.page - 1]
    k = a.page_width / pg.rect.width          # pt -> draw.io px
    W, H = a.page_width, round(pg.rect.height * k)
    lib = icon_library()
    assign = dict(s.split("=", 1) for s in (a.assign or []))
    ds = pg.get_drawings()
    zones = icon_zones(pg)
    in_zone = set().union(*(z["paths"] for z in zones)) if zones else set()
    cells, nid = [], iter(range(2, 10 ** 6))
    R = lambda r: (r.x0 * k, r.y0 * k, r.width * k, r.height * k)

    # cells are written in the PDF's paint order: a white label box must still cover the line under it
    def vertex(style, r, value="", seq=10 ** 9):
        x, y, w, h = r
        cells.append((seq, f'<mxCell id="t{next(nid)}" value="{value}" style="{style}" vertex="1" parent="1">'
                     f'<mxGeometry x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" as="geometry"/></mxCell>'))

    # lines first, so arrowheads can be attached to their ends
    lines, arrows, rects, outlines = [], [], [], []
    for i, d in enumerate(ds):
        if i in in_zone or pymupdf.Rect(d["rect"]).contains(pg.rect):
            continue
        its, r = d["items"], pymupdf.Rect(d["rect"])
        kinds = {it[0] for it in its}
        if d["fill"] and kinds == {"l"} and len(its) <= 5 and max(r.width, r.height) < 14:
            arrows.append(d)
        elif d["type"] == "s" and kinds == {"qu"} and max(r.width, r.height) < 14:
            outlines.append(r)                          # arrowhead outline, drawn again by endArrow
        elif kinds <= {"re", "qu"}:
            rects.append(d)
        elif d["fill"] and kinds == {"l"}:              # Skia turns a dashed stroke into filled dash pieces
            if min(r.width, r.height) < 2.5:
                y = r.y0 + r.height / 2; x = r.x0 + r.width / 2
                pts = [(r.x0, y), (r.x1, y)] if r.width >= r.height else [(x, r.y0), (x, r.y1)]
                lines.append(dict(pts=pts, color=d["fill"], width=min(r.width, r.height), dashed=dash_style(d, k), seq=d["seqno"]))
            else:
                rects.append(dict(d, type="s", color=d["fill"], fill=None, dash=dash_style(d, k), width=1 / k))
        elif kinds == {"l"} and d["color"] is not None:
            chain = [its[0][1]]
            for it in its:
                if abs(it[1].x - chain[-1].x) > .5 or abs(it[1].y - chain[-1].y) > .5:
                    lines.append(dict(pts=chain, color=d["color"], width=d["width"], seq=d["seqno"],
                                      dashed=(d["dashes"] or "[] 0") != "[] 0" and dash_style(d, k)))
                    chain = [it[1]]
                chain.append(it[2])
            lines.append(dict(pts=chain, color=d["color"], width=d["width"], seq=d["seqno"],
                              dashed=(d["dashes"] or "[] 0") != "[] 0" and dash_style(d, k)))
        else:
            print(f"  skip path {i} {sorted(kinds)} at {[round(v) for v in r]}")

    for ln in lines:
        ln["pts"] = [pymupdf.Point(p) for p in ln["pts"]]
        ln["end"] = ln["start"] = None
    for d in arrows:  # tip = triangle vertex farthest from the line end that sits inside it
        r = pymupdf.Rect(d["rect"]) + (-1.5, -1.5, 1.5, 1.5)
        verts = [it[1] for it in d["items"]]
        best = None
        for ln in lines:
            for side, p in (("end", ln["pts"][-1]), ("start", ln["pts"][0])):
                if r.contains(p) and ln[side] is None:
                    best = (ln, side, p); break
            if best: break
        if not best:
            vertex(f"triangle;whiteSpace=wrap;html=1;fillColor={hexcol(d['fill'])};strokeColor=none;", R(pymupdf.Rect(d["rect"])), seq=d["seqno"])
            continue
        ln, side, p = best
        tip = max(verts, key=lambda v: abs(v - p))
        ln[side] = "classic"
        if side == "end": ln["pts"][-1] = tip
        else: ln["pts"][0] = tip

    # rectangles: fill and stroke come as two paths with one bbox -> one cell
    merged = []
    for d in rects:
        r = pymupdf.Rect(d["rect"])
        if any(abs(r.x0 - o.x0) < .6 and abs(r.y1 - o.y1) < .6 for o in outlines):
            continue
        m = next((x for x in merged if abs(x["r"].x0 - r.x0) < .8 and abs(x["r"].y0 - r.y0) < .8
                  and abs(x["r"].x1 - r.x1) < .8 and abs(x["r"].y1 - r.y1) < .8), None)
        if m is None:
            m = dict(r=r, fill=None, stroke=None, width=None, dashed=False, seq=d["seqno"]); merged.append(m)
        if d.get("fill") is not None and m["fill"] is None: m["fill"] = d["fill"]
        if d.get("color") is not None and d["type"] in ("s", "fs"):
            m["stroke"], m["width"] = d["color"], d["width"]
            m["dashed"] = m["dashed"] or d.get("dash") or ((d.get("dashes") or "[] 0") != "[] 0" and dash_style(d, k))
        if d["type"] == "fs" and d.get("fill") is not None: m["fill"] = d["fill"]
    for m in merged:
        st = (f"rounded=0;whiteSpace=wrap;html=1;fillColor={hexcol(m['fill'])};strokeColor={hexcol(m['stroke'])};"
              f"strokeWidth={(m['width'] or 1 / k) * k:.2f};" + (m["dashed"] or ""))
        vertex(st, R(m["r"]), seq=m["seq"])

    for ln in lines:
        p = [(q.x * k, q.y * k) for q in ln["pts"]]
        st = (f"endArrow={ln['end'] or 'none'};startArrow={ln['start'] or 'none'};endFill=1;startFill=1;endSize=4;startSize=4;"
              f"html=1;rounded=0;strokeColor={hexcol(ln['color'])};strokeWidth={ln['width'] * k:.2f};"
              + (ln["dashed"] or ""))
        way = "".join(f'<mxPoint x="{x:.2f}" y="{y:.2f}"/>' for x, y in p[1:-1])
        cells.append((ln["seq"], f'<mxCell id="t{next(nid)}" style="{st}" edge="1" parent="1"><mxGeometry relative="1" as="geometry">'
                     f'<mxPoint x="{p[0][0]:.2f}" y="{p[0][1]:.2f}" as="sourcePoint"/>'
                     f'<mxPoint x="{p[-1][0]:.2f}" y="{p[-1][1]:.2f}" as="targetPoint"/>'
                     + (f'<Array as="points">{way}</Array>' if way else "") + "</mxGeometry></mxCell>"))

    # text, one cell per line
    trace = [(pymupdf.Rect(t["bbox"]), t["seqno"]) for t in pg.get_texttrace()]
    def tseq(r):  # paint position of the text-trace span that overlaps this line most
        best = max(trace, key=lambda t: abs(t[0] & r) / max(abs(t[0] | r), 1e-6), default=None)
        return best[1] if best and best[0].intersects(r) else 10 ** 8
    tlines = []
    for b in pg.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            sp = [s for s in l["spans"] if s["text"].strip()]
            if sp:
                tlines.append((l, sp, "".join(s["text"] for s in l["spans"]).strip()))
    for l, sp, _ in tlines:
        size = max(s["size"] for s in sp) * k
        fam = THAI_FONT if any((THAI_FONT in s["font"] or "Type3" in s["font"]) for s in sp) else "Helvetica"
        base = sp[0]["color"]
        html = ""
        for s in l["spans"]:
            t = s["text"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\xa0", "&nbsp;")
            if s["flags"] & 16: t = f"<b>{t}</b>"
            if s["color"] != base: t = f'<font color="{hexcol(s["color"])}">{t}</font>'
            html += t
        html = html.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")
        r = pymupdf.Rect(l["bbox"])
        # the web export embeds only the bold Thai-font run as Type3 (node names, all bold).
        # A regular Type3 run would come out bold too; check the render if a new board shows one.
        bold = all((s["flags"] & 16) or "Type3" in s["font"] for s in sp)
        st = (f"text;html=1;whiteSpace=nowrap;spacing=0;fontSize={size:.2f};fontFamily={fam};fontColor={hexcol(base)};"
              + ("fontStyle=1;" if bold else ""))
        dx, dy = l["dir"]
        if abs(dx - 1) < 1e-3:
            ox, oy = sp[0]["origin"]
            top = oy * k - a.baseline * size - a.baseline_px
            vertex(st + "align=left;verticalAlign=top;", (ox * k, top, r.width * k + 4, size * 1.2), html, tseq(r))
        else:  # rotated label: centre a horizontal box on it and turn it
            import math
            ang = math.degrees(math.atan2(dy, dx))
            length = max(r.width, r.height) * k if abs(dx) < 1e-3 else math.hypot(r.width, r.height) * k * .9
            cx, cy = (r.x0 + r.x1) / 2 * k, (r.y0 + r.y1) / 2 * k
            vertex(st + f"align=center;verticalAlign=middle;rotation={ang:.1f};",
                   (cx - length / 2, cy - size * .6, length, size * 1.2), html, tseq(r))

    # icons last so they sit on top of their boxes
    report = []
    texts = [(pymupdf.Rect(l["bbox"]), t) for l, _, t in tlines]
    boxes = [m["r"] for m in merged]
    for z in zones:
        zr = z["rect"]
        if z["kind"] == "dot":
            vertex(f"ellipse;whiteSpace=wrap;html=1;aspect=fixed;fillColor={hexcol(z['fill'])};strokeColor=none;", R(zr))
            continue
        gap = lambda tr: max(0, tr.x0 - zr.x1, zr.x0 - tr.x1) + max(0, tr.y0 - zr.y1, zr.y0 - tr.y1)
        cand = sorted((gap(tr), t) for tr, t in texts if gap(tr) < 45)
        box = min((b for b in boxes if b.contains(zr) and b.width < 400), key=lambda b: b.width * b.height, default=None)
        if box is not None:
            bg = lambda tr: max(0, tr.x0 - box.x1, box.x0 - tr.x1) + max(0, tr.y0 - box.y1, box.y0 - tr.y1)
            cand += sorted((100 + bg(tr), t) for tr, t in texts if bg(tr) < 20 and not box.contains(tr))
        key = f"{zr.x0 * k:.0f},{zr.y0 * k:.0f}"
        slug, why = assign.get(key), "assigned"
        if slug is None:
            slug, why = next(((i["slug"], t) for _, t in cand for i in lib.values() if i["rx"].search(t.strip())), (None, None))
        if slug is None:
            print(f"  icon {key} ({z['kind']}) no label matched {[t for _, t in cand[:3]]} — pass --assign {key}=<slug>")
            slug, why = "server", "fallback"
        ic = lib[slug]
        vertex(ic["style"], R(zr))
        report.append(dict(at=key, size=f"{zr.width * k:.0f}x{zr.height * k:.0f}", icon=slug, source=ic["source"], why=why))

    out = Path(a.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        f'<mxfile host="drawio_board.py trace"><diagram id="trace" name="{escape_attr(Path(a.pdf).stem)}">'
        f'<mxGraphModel grid="1" gridSize="10" page="1" pageScale="1" pageWidth="{W:g}" pageHeight="{H}" math="0" shadow="0">'
        f'<root><mxCell id="0"/><mxCell id="1" parent="0"/>{"".join(c for _, c in sorted(cells, key=lambda c: c[0]))}</root></mxGraphModel></diagram></mxfile>',
        encoding="utf-8")
    rep = out.with_suffix(".icons.json")
    rep.write_text(json.dumps(report, ensure_ascii=False, indent=1))
    print(f"{out}  ({len(cells)} cells, {len(report)} icons -> {rep.name})")
    for r_ in report:
        print(f"  icon {r_['at']:>10} {r_['size']:>6}  {r_['icon']:<16} {r_['source']:<8} via {r_['why']!r}")


def escape_attr(s):
    return s.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")


def main():
    global TITLE_SUFFIX, THAI_FONT
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("list"); p.add_argument("file", type=Path); p.set_defaults(fn=cmd_list)
    p = sp.add_parser("export"); p.add_argument("file", type=Path); p.add_argument("--version", required=True)
    p.add_argument("--out", help=f"default ./{DEFAULT_OUT}")
    p.add_argument("--name", default="{title} {env} {version} - {ddmmyy}", help="file stem pattern; fields: title env version ddmmyy ddmmyyyy")
    p.add_argument("--title", help="override the title read off the board")
    p.set_defaults(fn=cmd_export)
    p = sp.add_parser("clone"); p.add_argument("file", type=Path); p.add_argument("--from", required=True)
    p.add_argument("--version", required=True); p.add_argument("--date", help="dd/mm/yyyy, default today")
    p.set_defaults(fn=cmd_clone)
    p = sp.add_parser("compare"); p.add_argument("ref"); p.add_argument("cand")
    p.add_argument("--diff-png", help="write a red (reference only) / blue (candidate only) overlay here")
    p.add_argument("--pixel-tol", type=float, default=0.02, help="max share of ink that may differ (default 0.02)")
    p.add_argument("--no-image-check", action="store_true",
                   help="redrawn diagram: icons are draw.io shapes, not the reference's bitmaps")
    p.set_defaults(fn=cmd_compare)
    p = sp.add_parser("trace"); p.add_argument("pdf"); p.add_argument("--out", required=True)
    p.add_argument("--page", type=int, default=1); p.add_argument("--page-width", type=float, default=2336)
    p.add_argument("--baseline", type=float, default=0.97, help="text top = baseline - this x font size - --baseline-px")
    p.add_argument("--baseline-px", type=float, default=4.4, help="fitted on a draw.io web export at 7-25pt, see SKILL.md")
    p.add_argument("--assign", action="append", metavar="X,Y=SLUG", help="force the icon at draw.io px X,Y")
    p.set_defaults(fn=cmd_trace)
    ap.add_argument("--env-map", help='title prefix -> file label, e.g. "Production=Prd,Non Production=Uat"')
    ap.add_argument("--title-suffix", help=f"a board's title is the text ending with this (default '{TITLE_SUFFIX}')")
    ap.add_argument("--thai-font", help=f"font family for Thai text runs (default {THAI_FONT})")
    a = ap.parse_args()
    if a.env_map:
        ENV_NAME.clear()
        ENV_NAME.update(dict(kv.split("=", 1) for kv in a.env_map.split(",")))
    if a.title_suffix:
        TITLE_SUFFIX = a.title_suffix
    if a.thai_font:
        THAI_FONT = a.thai_font
    a.fn(a)


if __name__ == "__main__":
    main()
