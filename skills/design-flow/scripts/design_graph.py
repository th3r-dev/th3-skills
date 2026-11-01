#!/usr/bin/env python3
"""Design knowledge graph for a Figma file: what is where, what uses what, what repeats.

Adapted from Understand-Anything (MIT): deterministic local extraction, a typed node/edge graph
saved as JSON, incremental by fingerprint, and questions answered from the graph instead of
re-reading the file. No LLM involved.

  design_graph.py extract --page 1:2 [--page 1:3] --out DIR      run graph_extract.js through the bridge
  design_graph.py build DIR                                       raw extracts -> DIR/graph.json (+ changes since last build)
  design_graph.py dupes DIR [--min 3]                             repeated structures that are not components yet
  design_graph.py impact DIR "<variable | component | style>"     screens that change if this changes
  design_graph.py tour DIR                                        screens top-down per section, with what they use
  design_graph.py gaps DIR                                        placeholders, raw paints/texts, screens without a flow
  design_graph.py --self-test

Node kinds: page, section, screen, label, component, variable, text_style, flow.
Edge kinds: in_section, uses_component, binds_variable, uses_text_style, navigates_to, has_flow.
"""
import argparse, hashlib, json, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def extract(pages, out):
    out.mkdir(parents=True, exist_ok=True)
    for pid in pages:
        js = out / f"extract-{pid.replace(':', '_')}.js"
        subprocess.run([sys.executable, str(HERE / "figma_js.py"), "extract", "--page", pid, "-o", str(js)], check=True, capture_output=True)
        r = subprocess.run([sys.executable, str(HERE / "bridge.py"), "run", str(js), "--timeout", "600"], capture_output=True, text=True)
        data = json.loads(r.stdout).get("result") if r.stdout.strip().startswith("{") else None
        if not data:
            sys.exit(f"extract {pid} failed: {r.stdout[:300]} {r.stderr[:300]}")
        (out / f"raw-{pid.replace(':', '_')}.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        print(f"page {pid}: {len(data['screens'])} screens, {len(data['dupes'])} repeated structures")


def fingerprint(obj):
    return hashlib.sha1(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:12]


def build(d):
    raws = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(d.glob("raw-*.json"))]
    nodes, edges, dupes = {}, [], {}
    add = lambda nid, kind, **kw: nodes.setdefault(nid, {"id": nid, "kind": kind, **kw})
    for raw in raws:
        pg = raw["page"]; add(pg["id"], "page", name=pg["name"])
        for v in raw.get("variables", []):
            add(v["id"], "variable", name=v["name"], collection=v["collection"])
        for t in raw.get("textStyles", []):
            add(t["id"], "text_style", name=t["name"], font=t["font"], size=t["size"])
        for c in raw["components"]:
            add(c["id"], "component", name=c["name"], page=pg["id"], variants=len(c.get("variants", [])))
        for l in raw["labels"]:
            add(l["id"], "label", name=l["name"], x=l["x"], y=l["y"], page=pg["id"])
        for s in raw["screens"]:
            add(s["id"], "screen", name=s["name"], page=pg["id"], x=s["x"], y=s["y"], w=s["w"], h=s["h"],
                placeholder=s["placeholder"], raw_paints=s["rawPaints"], raw_texts=s["rawTexts"], layers=s["layers"],
                fp=fingerprint(s))
            for cid, n in s["instances"].items():
                edges.append({"from": s["id"], "to": cid, "kind": "uses_component", "n": n})
            for vid, n in s["variables"].items():
                edges.append({"from": s["id"], "to": vid, "kind": "binds_variable", "n": n})
            for tid, n in s["textStyles"].items():
                edges.append({"from": s["id"], "to": tid, "kind": "uses_text_style", "n": n})
        names = {s["id"]: s["name"] for s in raw["screens"]}
        for c in raw["connectors"]:
            if c.get("from") and c.get("to"):
                edges.append({"from": c["from"], "to": c["to"], "kind": "navigates_to", "label": c["label"]})
        for k, v in raw["dupes"].items():
            e = dupes.setdefault(k, {**v, "screens": {}})
            if e is not v:
                e["count"] += v["count"]; e["samples"] = (e["samples"] + v["samples"])[:5]
            for sid, n in v["screens"].items():
                e["screens"][sid] = e["screens"].get(sid, 0) + n
        for fl in raw.get("flows", []):
            add(fl["id"], "flow", name=fl["name"])
            target = next((sid for sid, nm in names.items() if fl["name"] == f"Flow · {nm}"), None)
            if target:
                edges.append({"from": target, "to": fl["id"], "kind": "has_flow"})
    prev = d / "graph.json"
    old = json.loads(prev.read_text(encoding="utf-8")) if prev.exists() else {"nodes": []}
    oldfp = {n["id"]: n.get("fp") for n in old["nodes"] if n["kind"] == "screen"}
    changed = [n["id"] for n in nodes.values() if n["kind"] == "screen" and oldfp.get(n["id"]) != n["fp"]]
    graph = {"nodes": list(nodes.values()), "edges": edges, "dupes": dupes}
    prev.write_text(json.dumps(graph, ensure_ascii=False, indent=1), encoding="utf-8")
    kinds = {}
    for n in nodes.values():
        kinds[n["kind"]] = kinds.get(n["kind"], 0) + 1
    print(f"graph: {kinds} · {len(edges)} edges · {len(dupes)} repeated structures · {len(changed)} screens new/changed since last build")
    return graph


def load(d):
    return json.loads((Path(d) / "graph.json").read_text(encoding="utf-8"))


def dupes(g, min_count):
    rows = sorted((v for v in g["dupes"].values() if v["count"] >= min_count),
                  key=lambda v: (-(v["count"] * len(v["screens"])), -v["w"] * v["h"]))
    print(f"{'count':>5} {'screens':>7}  size       name                 sample ids")
    for v in rows[:40]:
        print(f"{v['count']:>5} {len(v['screens']):>7}  {v['w']:>4}x{v['h']:<5} {v['name'][:20]:20} {', '.join(v['samples'][:3])}")
    print("\nCandidates repeat on several screens: make one a component (figma_js.py swap afterwards).")
    return rows


def impact(g, q):
    hits = [n for n in g["nodes"] if n["kind"] in ("variable", "component", "text_style") and (n["id"] == q or q.lower() in n["name"].lower())]
    byid = {n["id"]: n for n in g["nodes"]}
    for h in hits:
        users = [(e["from"], e.get("n", 1)) for e in g["edges"] if e["to"] == h["id"]]
        print(f"{h['kind']} {h['name']} ({h['id']}): {len(users)} screens")
        for sid, n in sorted(users, key=lambda x: -x[1])[:30]:
            print(f"  {n:>5}× {byid.get(sid, {}).get('name', sid)}")
    if not hits:
        print("no variable/component/style matches", q)


def tour(g):
    screens = sorted((n for n in g["nodes"] if n["kind"] == "screen"), key=lambda n: (n["page"], n["x"] // 2500, n["y"]))
    comps = {n["id"]: n["name"] for n in g["nodes"] if n["kind"] == "component"}
    col = None
    for s in screens:
        c = (s["page"], s["x"] // 2500)
        if c != col:
            col = c; print(f"\n## page {s['page']} · column x≈{s['x']}")
        used = [comps.get(e["to"], e["to"]) for e in g["edges"] if e["from"] == s["id"] and e["kind"] == "uses_component"]
        print(f"- {s['name']}" + (f"  [{s['placeholder']}]" if s["placeholder"] else "") + (f"  uses: {', '.join(sorted(set(used))[:6])}" if used else ""))


def gaps(g):
    flows = {e["from"] for e in g["edges"] if e["kind"] == "has_flow"}
    for s in (n for n in g["nodes"] if n["kind"] == "screen"):
        issues = []
        if s["placeholder"]:
            issues.append(f"placeholder:{s['placeholder']}")
        if s["raw_paints"]:
            issues.append(f"{s['raw_paints']} raw paints")
        if s["raw_texts"]:
            issues.append(f"{s['raw_texts']} unstyled texts")
        if s["id"] not in flows and not s["placeholder"]:
            issues.append("no flow")
        if issues:
            print(f"{s['name'][:70]:70} {' · '.join(issues)}")


def self_test():
    tmp = Path(__file__).with_name("__graph_selftest__"); tmp.mkdir(exist_ok=True)
    raw = {"page": {"id": "1:1", "name": "UI"}, "labels": [], "connectors": [], "variables": [{"id": "V:1", "name": "Color/A", "collection": "C", "type": "COLOR"}],
           "textStyles": [], "components": [{"id": "9:9", "name": "Button", "type": "COMPONENT_SET", "variants": []}],
           "screens": [{"id": "2:2", "name": "Role A ▸ Menu 1 ▸ Screen 1.1", "type": "FRAME", "x": 0, "y": 0, "w": 1920, "h": 1080, "placeholder": None,
                        "instances": {"9:9": 3}, "variables": {"V:1": 5}, "textStyles": {}, "rawPaints": 0, "rawTexts": 2, "layers": 10}],
           "dupes": {"sig": {"count": 4, "w": 100, "h": 40, "name": "Row", "samples": ["3:3"], "screens": {"2:2": 4}}}}
    (tmp / "raw-1_1.json").write_text(json.dumps(raw))
    g = build(tmp)
    assert {e["kind"] for e in g["edges"]} == {"uses_component", "binds_variable"} and len(g["dupes"]) == 1
    g2 = build(tmp)  # unchanged rebuild
    for p in tmp.iterdir():
        p.unlink()
    tmp.rmdir()
    print("self-test ok")


def main():
    if "--self-test" in sys.argv:
        return self_test()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["extract", "build", "dupes", "impact", "tour", "gaps"])
    ap.add_argument("dir", nargs="?")
    ap.add_argument("query", nargs="?")
    ap.add_argument("--page", action="append", default=[])
    ap.add_argument("--out")
    ap.add_argument("--min", type=int, default=3)
    a = ap.parse_args()
    if a.cmd == "extract":
        return extract(a.page, Path(a.out))
    if a.cmd == "build":
        return build(Path(a.dir))
    g = load(a.dir)
    {"dupes": lambda: dupes(g, a.min), "impact": lambda: impact(g, a.query or ""), "tour": lambda: tour(g), "gaps": lambda: gaps(g)}[a.cmd]()


if __name__ == "__main__":
    main()
