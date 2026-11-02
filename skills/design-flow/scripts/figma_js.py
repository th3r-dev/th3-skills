#!/usr/bin/env python3
"""Render the Figma plugin scripts this skill runs inside Figma.

Run the output as `code` with either backend (same Plugin API JavaScript):
  - official Figma MCP `use_figma` (counts against the Figma plan's MCP limit), or
  - figma-mcp-bridge `run_script` (local plugin, no Figma API quota; server env
    FIGMA_BRIDGE_ENABLE_RUN_SCRIPT=1; pass allowRemove: true for `place`, which removes placeholders).

Why not do the edit from Python directly: changing layers (binding variables, applying text
styles, moving/removing nodes, building a card) only exists in Figma's Plugin API, which runs
inside Figma and takes JavaScript. The REST API cannot edit layers (and writes variables only
on Enterprise plans). So this CLI fills a JS template with your parameters and prints it; pass
the output verbatim as `code`.

  figma_js.py tokenize --page 1:2 --root 10:20 [--prefer-collection NAME] [--font-map "Fallback=Real"]
  figma_js.py place --page 1:2 --capture 10:20 --target 10:30 --name "Role ▸ Menu ▸ Screen"
      [--placeholder-match placeholder] [--version v1.2.21 --old-version v1.2.20 --date 2026-10-29 --note "..."]
      [--card-fill-var Color/Theme/Primary --card-text-var Color/Theme/White --title-style Huge --body-style 3xl]
  figma_js.py autolayout --page 1:2 --root 10:20 [--tolerance 2]
  figma_js.py swap --page 1:2 --component 10:40 --roots 10:20,10:30 [--name-match "^Button$"]
  figma_js.py flow-kit --page 1:2 --tokens tokens.json        (build Flow/Node, Flow/Decision, Flow/Marker, Flow/Element Row)
  figma_js.py flow --page 1:2 --spec flow.json                  (UI → flow → UI: element on screen → kit nodes → target screen)
  figma_js.py state --page 1:2 --spec state.json                (target state screen: copy + dialog overlay, or imported page + sidebar)
  figma_js.py make-room --page 1:2 --from-x 24900 --dx 10000 [--label <section label id>] [--y-from Y --y-to Y]   (shift a section right)
  figma_js.py redraw-connectors --page 1:2 [--ids a,b] [--slack 400]   (fix stale connector routes after moves)
  figma_js.py images --page 1:2 --root 10:20 --images capture.images.json   (raster images of an html-figma import)
  figma_js.py place-check --page 1:2                          (stage 1 check: screens overlapping, on a title? read-only)
  figma_js.py usage --page 1:2 [--spec usage.json]                         (rule check: every component used? read-only)
  figma_js.py ui-samples --page 1:2 --spec names.json         (code component → matching layers, grouped by structure and fill)
  figma_js.py componentize --page 1:2 --spec comp.json      (duplicate → component: State variants + simple Label/Value/Icon props)
  figma_js.py extract --page 1:2                                (read-only graph extraction for design_graph.py)
  figma_js.py --self-test

stdlib only. Output goes to stdout or -o FILE.
"""
import argparse, json, os, sys
from pathlib import Path

JS = Path(__file__).with_name("js")


def inside_work(p, what="path"):
    """CLI paths come from an agent, so every file this script reads or writes stays inside the working folder:
    the current directory, or $DESIGN_FLOW_ROOT when set."""
    root = os.path.realpath(os.environ.get("DESIGN_FLOW_ROOT") or os.getcwd())
    full = os.path.realpath(os.path.join(root, os.path.expanduser(p)))
    if os.path.commonpath([root, full]) != root:
        raise SystemExit(f"{what} {p!r} is outside the working folder {root}; run from that folder or set DESIGN_FLOW_ROOT")
    return Path(full)


def read_json(p, what):
    return json.loads(inside_work(p, what).read_text(encoding="utf-8"))


def ui_to_ui(spec):
    """A flow joins real UI to real UI: every anchor's chain must end on a screen (another page, or a state copy of
    this one: dialog open, alert shown). Returns the anchors whose chain never reaches one."""
    screens = {s["id"] for s in spec.get("screens") or []}
    nxt = {}
    for e in spec.get("edges") or []:
        nxt.setdefault(e["from"], []).append(e["to"])
    def reaches(v, seen):
        return v in screens or any(t not in seen and reaches(t, seen | {t}) for t in nxt.get(v, []))
    return [a["id"] for a in spec.get("anchors") or [] if not reaches(a["id"], {a["id"]})]
TOKEN = "__PARAMS__"


def render(template, params):
    src = (JS / f"{template}.js").read_text(encoding="utf-8")
    if src.count(TOKEN) != 1:
        raise SystemExit(f"{template}.js must contain {TOKEN} exactly once")
    return src.replace(TOKEN, json.dumps(params, ensure_ascii=False))


def font_map(pairs):
    out = {}
    for p in pairs or []:
        k, sep, v = p.partition("=")
        if not sep or not k or not v:
            raise SystemExit(f'--font-map wants "Captured Family=Real Family", got {p!r}')
        out[k.strip()] = v.strip()
    return out


def self_test():
    t = render("tokenize", {"page": "1:1", "root": "2:2", "font_map": font_map(["A B=C"])})
    assert TOKEN not in t and '"A B": "C"' in t and t.startswith("//")
    for t in ("flow_kit", "flow_render", "graph_extract", "state", "make_room", "connector_redraw", "componentize", "ui_samples", "component_usage", "place_check"):
        assert TOKEN not in render(t, {"page": "1:1"})
    w = render("swap", {"page": "1:1", "component": "5:5", "roots": ["2:2"]})
    assert TOKEN not in w and '"roots": ["2:2"]' in w
    a = render("autolayout", {"page": "1:1", "root": "2:2"})
    assert TOKEN not in a and '"root": "2:2"' in a
    i = render("images", {"page": "1:1", "root": "2:2", "images": {"k": {"b64": "QUJD"}}})
    assert TOKEN not in i and '"QUJD"' in i
    p = render("place", {"page": "1:1", "capture": "3:3", "target": "4:4", "name": "Role ▸ Menu ▸ ทดสอบ"})
    assert TOKEN not in p and "ทดสอบ" in p
    try:
        font_map(["broken"])
    except SystemExit:
        pass
    else:
        raise AssertionError("bad --font-map accepted")
    spec = {"anchors": [{"id": "a"}, {"id": "b"}], "screens": [{"id": "s"}],
            "edges": [{"from": "a", "to": "n"}, {"from": "n", "to": "s"}, {"from": "b", "to": "x"}, {"from": "x", "to": "b"}]}
    assert ui_to_ui(spec) == ["b"]
    for bad in ("../x.json", "/etc/hosts"):
        try:
            inside_work(bad)
        except SystemExit:
            pass
        else:
            raise AssertionError(f"{bad} accepted")
    print("self-test ok")


def main():
    if "--self-test" in sys.argv:
        return self_test()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    rc = sub.add_parser("redraw-connectors")
    rc.add_argument("--page", required=True); rc.add_argument("--ids", help="comma-separated connector ids (default: all stale)")
    rc.add_argument("--slack", type=float, default=400); rc.add_argument("-o", "--out")
    im = sub.add_parser("images")
    im.add_argument("--page", required=True); im.add_argument("--root", required=True, help="the imported frame")
    im.add_argument("--images", required=True, help="the <capture>.images.json capture.py wrote"); im.add_argument("-o", "--out")
    mr = sub.add_parser("make-room")
    mr.add_argument("--page", required=True); mr.add_argument("--from-x", type=float, required=True)
    mr.add_argument("--dx", type=float, required=True); mr.add_argument("--label"); mr.add_argument("-o", "--out")
    mr.add_argument("--y-from", type=float, help="row band: only nodes whose top is at or below this y move")
    mr.add_argument("--y-to", type=float, help="row band: ... and above this y")
    for name in ("flow-kit", "flow", "extract", "state", "componentize", "ui-samples", "usage", "place-check"):
        s = sub.add_parser(name)
        s.add_argument("--page", required=True)
        s.add_argument("-o", "--out")
        if name == "flow-kit":
            s.add_argument("--tokens", required=True, help="JSON file: {ink,line,paper,alert,success,accent,on_accent,muted,node_text,small_text,marker_text}")
        if name in ("flow", "state", "componentize", "ui-samples"):
            s.add_argument("--spec", required=True, help="JSON file (see SKILL.md: UI → flow → UI)")
        if name == "usage":
            s.add_argument("--spec", help='optional JSON: {"section": "Components", "ignore": "^\\."}')
    for name in ("tokenize", "place", "autolayout", "swap"):
        s = sub.add_parser(name)
        s.add_argument("--page", required=True, help="page node id, e.g. 2:2")
        s.add_argument("--prefer-collection", default="", help="variable collection to prefer on ties")
        s.add_argument("-o", "--out")
    t = sub.choices["tokenize"]
    t.add_argument("--root", required=True, help="node id whose subtree gets tokenized")
    t.add_argument("--font-map", action="append", help='"Captured Family=Real Family", repeatable')
    sw = sub.choices["swap"]
    sw.add_argument("--component", required=True, help="component set (or component) whose variants replace matching layers")
    sw.add_argument("--roots", required=True, help="comma-separated node ids to search under")
    sw.add_argument("--name-match", help="regex the layer name must match, e.g. '^Button$'")
    sw.add_argument("--tolerance", type=float, default=1)
    al = sub.choices["autolayout"]
    al.add_argument("--root", required=True, help="node id whose absolute frames become auto layout")
    al.add_argument("--tolerance", type=float, default=2, help="px of overlap still treated as a clean row/column")
    p = sub.choices["place"]
    p.add_argument("--capture", required=True, help="node id of the new screen")
    p.add_argument("--target", required=True, help="placeholder or old screen it replaces")
    p.add_argument("--name", help="breadcrumb name for the new screen (default: target's name)")
    p.add_argument("--placeholder-match", default="placeholder", help="regex on the placeholder component name")
    p.add_argument("--gap", type=int, default=200)
    p.add_argument("--version"); p.add_argument("--old-version"); p.add_argument("--date"); p.add_argument("--note")
    p.add_argument("--title", default="New version")
    p.add_argument("--card-fill-var", default="Color/Theme/Primary")
    p.add_argument("--card-text-var", default="Color/Theme/White")
    p.add_argument("--title-style", default="Huge")
    p.add_argument("--body-style", default="3xl")
    a = ap.parse_args()

    if a.cmd == "flow-kit":
        a.cmd, params = "flow_kit", {"page": a.page, "tokens": read_json(a.tokens, "--tokens")}
    elif a.cmd == "flow":
        a.cmd, params = "flow_render", {"page": a.page, **read_json(a.spec, "--spec")}
        if dead := ui_to_ui(params):
            raise SystemExit(f"anchors {dead} never reach a screen. Build the result state first (capture.py jobs "
                             "with steps/selector, then figma_js.py state), list it in `screens`, and end the chain on it")
    elif a.cmd == "redraw-connectors":
        a.cmd, params = "connector_redraw", {"page": a.page, "slack": a.slack, **({"ids": [i.strip() for i in a.ids.split(",")]} if a.ids else {})}
    elif a.cmd == "images":
        params = {"page": a.page, "root": a.root, "images": read_json(a.images, "--images")}
    elif a.cmd == "make-room":
        a.cmd, params = "make_room", {"page": a.page, "from_x": a.from_x, "dx": a.dx, "label": a.label, "y_from": a.y_from, "y_to": a.y_to}
    elif a.cmd == "place-check":
        a.cmd, params = "place_check", {"page": a.page}
    elif a.cmd == "usage":
        a.cmd, params = "component_usage", {"pages": [a.page], **(read_json(a.spec, "--spec") if a.spec else {})}
    elif a.cmd == "ui-samples":
        a.cmd, params = "ui_samples", {"page": a.page, **read_json(a.spec, "--spec")}
    elif a.cmd == "componentize":
        a.cmd, params = "componentize", {"page": a.page, **read_json(a.spec, "--spec")}
    elif a.cmd == "state":
        a.cmd, params = "state", {"page": a.page, **read_json(a.spec, "--spec")}
    elif a.cmd == "extract":
        a.cmd, params = "graph_extract", {"page": a.page}
    elif a.cmd == "swap":
        params = {"page": a.page, "component": a.component, "roots": [r.strip() for r in a.roots.split(",") if r.strip()],
                  "name_match": a.name_match, "tolerance": a.tolerance}
    elif a.cmd == "autolayout":
        params = {"page": a.page, "root": a.root, "tolerance": a.tolerance}
    elif a.cmd == "tokenize":
        params = {"page": a.page, "root": a.root, "prefer_collection": a.prefer_collection, "font_map": font_map(a.font_map)}
    else:
        params = {k: v for k, v in {
            "page": a.page, "capture": a.capture, "target": a.target, "name": a.name, "gap": a.gap,
            "placeholder_match": a.placeholder_match, "prefer_collection": a.prefer_collection,
            "version": a.version, "old_version": a.old_version, "date": a.date, "note": a.note, "title": a.title,
            "card_fill_var": a.card_fill_var, "card_text_var": a.card_text_var,
            "title_style": a.title_style, "body_style": a.body_style}.items() if v is not None}
    code = render(a.cmd, params)
    if a.out:
        inside_work(a.out, "--out").write_text(code, encoding="utf-8")
        print(f"wrote {a.out} ({len(code)} chars)")
    else:
        sys.stdout.write(code)


if __name__ == "__main__":
    main()
