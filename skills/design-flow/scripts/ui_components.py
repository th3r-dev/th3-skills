#!/usr/bin/env python3
"""Code → Figma components, automated: plan from a code scan + layer samples, then build and swap.

  ui_components.py names  --map map.json --out names.json         layer regex per component (input for ui-samples)
  ui_components.py plan   --inventory inv.json --samples samples.json --map map.json --out plan.json
  ui_components.py apply  plan.json --page UI_PAGE --components-page PAGE [--section Components]
  ui_components.py sync   --page UI_PAGE [--ignore REGEX] [--prune]   swap EVERY component into every screen, list (and prune) unused
  ui_components.py --self-test

map.json  {"<code component>": {"figma": "Button", "layers": "^Button$", "text": ["Label"]}, …}
          code component as ui_scan.py names it (e.g. "Form.Control"); figma = simple component name.
Flow: ui_scan.py scan → names → figma_js.py ui-samples (read-only) → plan → apply.
apply = per component: figma_js.py componentize (new set, or extend an existing one with missing variants;
State values named after the code's own variants when the fill token matches, e.g. green → success) → swap.js
replaces every matching copy on every screen with an instance (texts carried over). Bridge calls honour FIGMA_FILE.
"""
import argparse, json, re, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
COLOR_TO_CODE = [(r"green|success", "success"), (r"red|danger|error", "danger"), (r"orange|amber|yellow|warning", "warning"),
                 (r"primary|blue|navy", "primary"), (r"gray|grey|secondary|muted", "secondary"), (r"white|light", "light"),
                 (r"info|teal|cyan|sky", "info")]


def token_short(name):
    """'Color/Green/500' → 'Green', 'Color/Theme/Primary' → 'Primary', '#ff6f0c' → '#ff6f0c'."""
    if not name or name in ("none", "var"):
        return ""
    if name.startswith("#"):
        return name
    parts = [p for p in name.split("/") if p and p.lower() != "color"]
    if parts and re.fullmatch(r"\d+", parts[-1]) and len(parts) > 1:
        return parts[-2]
    return parts[-1] if parts else name


def state_name(fill_key, code_values, icon=False):
    """Simple variant name for a fill/stroke token pair: the code's own value when the color matches
    (green → success …), 'soft-…' for light background tokens ('… Bg'), 'outline-…' for stroke-only.
    Icon-only parts use the plain color word (blue / amber / red), since each action has its own color and icon."""
    fill, stroke = (fill_key.split("~") + ["", ""])[:2]   # "fill~stroke~geometry"
    base, outline = token_short(fill), False
    if not base:
        base, outline = token_short(stroke), True
    if not base:
        return "plain"
    last = fill.split("/")[-1] if "/" in fill else fill
    soft = bool(re.search(r"\bbg\b|soft|^(50|100)$", last, re.I)) and not outline
    if icon:
        word = re.sub(r"\b(bg|edit|soft|theme)\b", "", base, flags=re.I).strip().lower() or base.lower()
        return word.replace(" ", "-")
    for rx, code in COLOR_TO_CODE:
        if re.search(rx, base, re.I):
            want = f"outline-{code}" if outline else (f"soft-{code}" if soft and code != "light" else code)
            hit = next((v for v in code_values if v.lower() == want), None)
            return hit or want
    return ("outline-" if outline else "") + base.lower().replace(" ", "-")


def plan(inventory, samples, cmap, min_copies=20):
    """One Figma component per frequent shape of a code component: text parts keep the simple name (Button),
    icon-only parts become 'Icon <name>', further text shapes get a size word (Small / Large)."""
    inv = {r["component"]: r for r in inventory}
    out = []
    for comp, m in cmap.items():
        groups = samples.get(comp) or []
        if not groups:
            continue
        top = groups[0]["count"]
        keep = [g for g in groups if g["count"] >= max(min_copies, top * 0.1)][:3] or groups[:1]
        r = inv.get(comp)
        code_vals = [v for vals in (r["figma_spec"]["variants"].values() if r else []) for v in vals]
        names_used, text_h = set(), None
        for g in keep:
            icon = not any(f.get("text") for f in g["fills"])
            if icon:
                name = m["figma"] if m["figma"].lower().startswith("icon") else f"Icon {m['figma']}"
            elif text_h is None:
                name, text_h = m["figma"], g["h"]
            else:
                name = f"{m['figma']} {'Small' if g['h'] < text_h else 'Large'}"
            if name in names_used:
                continue
            names_used.add(name)
            seen, smp = set(), []
            for f in g["fills"]:
                if f["count"] < 2 and smp:
                    continue
                if len(smp) >= 12:
                    break
                st = state_name(f["fill"], code_vals, icon)
                if st in seen:
                    st = f"{st}-outline" if "~none" not in f["fill"] and f"{st}-outline" not in seen else st
                k, base = 2, st
                while st in seen:
                    st = f"{base}-{k}"; k += 1
                seen.add(st)
                smp.append({"id": f["sample"], "state": st})
            out.append({"code": comp, "name": name, "layers": m["layers"], "text_names": [] if icon else m.get("text", ["Label"]),
                        "copies": g["count"], "screens": g["screens"], "samples": smp,
                        "description": f"From code: {comp} ({r['source']}), used {r['uses']}× in {r['files']} files." if r else None})
    return sorted(out, key=lambda p: -p["copies"])


def run(cmd):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    try:
        return json.loads(r.stdout).get("result", json.loads(r.stdout))
    except ValueError:
        raise SystemExit(f"failed: {' '.join(map(str, cmd))}\n{r.stdout[-400:]}\n{r.stderr[-400:]}")


def screens(page, tmp):
    js = tmp / "screens.js"
    js.write_text(f"await figma.setCurrentPageAsync(await figma.getNodeByIdAsync('{page}'));\n"
                  "return figma.currentPage.children.filter(n => n.type === 'FRAME' && n.width >= 1000 && n.height >= 600).map(n => n.id);", encoding="utf-8")
    return run([sys.executable, HERE / "bridge.py", "run", js, "--timeout", "600"])


def swap(cid, page, roots, tmp, layers=None):
    subprocess.run([sys.executable, HERE / "figma_js.py", "swap", "--page", page, "--component", cid, "--roots", ",".join(roots),
                    *(["--name-match", layers] if layers else []), "-o", tmp / "s.js"], check=True, capture_output=True)
    return run([sys.executable, HERE / "bridge.py", "run", tmp / "s.js", "--allow-remove", "--timeout", "1800"])


def usage(page, tmp, ignore):
    spec = tmp / "u.json"; spec.write_text(json.dumps({"ignore": ignore} if ignore else {}), encoding="utf-8")
    subprocess.run([sys.executable, HERE / "figma_js.py", "usage", "--page", page, "--spec", spec, "-o", tmp / "u.js"], check=True, capture_output=True)
    return run([sys.executable, HERE / "bridge.py", "run", tmp / "u.js", "--timeout", "1800"])


def sync(page, ignore, prune=False):
    """Rule: a component exists to be used. Swap every local component into every screen (copies made before it
    existed, screens built after it), then report what is still unused, so it gets used or removed."""
    tmp = Path(tempfile.mkdtemp())
    roots = screens(page, tmp)
    before = usage(page, tmp, ignore)
    for c in before["components"]:
        s = swap(c["id"], page, roots, tmp)
        if s.get("swapped"):
            print(f"{c['name']}: +{s['swapped']} instances {s.get('byVariant')}")
    after = usage(page, tmp, ignore)
    for c in after["components"]:
        print(f"{c['total']:>5}  {c['name']}")
    print("unused components:", after["unused"] or "none")
    print("unused variants:", after["unusedVariants"] or "none")
    if prune:   # use it or remove it: drop variants nothing uses (a set always keeps at least one)
        ids = [v for c in after["components"] for v in c.get("variantIds", {}).values()]
        js = tmp / "prune.js"
        js.write_text("const ids = " + json.dumps(ids) + ";\nconst out = [];\n"
                      "for (const id of ids) { const v = await figma.getNodeByIdAsync(id); if (!v || v.parent.type !== 'COMPONENT_SET' || v.parent.children.length < 2) continue;\n"
                      "  if ((await v.getInstancesAsync()).length) continue; out.push(v.parent.name + ' / ' + v.name); v.remove(); }\nreturn out;", encoding="utf-8")
        print("pruned:", run([sys.executable, HERE / "bridge.py", "run", js, "--allow-remove", "--timeout", "900"]) or "none")
    return after


def apply(plan_rows, page, comp_page, section):
    tmp = Path(tempfile.mkdtemp())
    roots = screens(page, tmp)
    report = []
    for p in plan_rows:
        spec = tmp / "c.json"
        spec.write_text(json.dumps({"section": section, "name": p["name"], "samples": p["samples"], "text_names": p["text_names"],
                                    **({"description": p["description"]} if p.get("description") else {})}, ensure_ascii=False), encoding="utf-8")
        subprocess.run([sys.executable, HERE / "figma_js.py", "componentize", "--page", comp_page, "--spec", spec, "-o", tmp / "c.js"], check=True, capture_output=True)
        c = run([sys.executable, HERE / "bridge.py", "run", tmp / "c.js", "--timeout", "600"])
        cid = c.get("id") if isinstance(c, dict) else None
        if not cid:
            report.append({"name": p["name"], "error": c}); print("componentize failed", p["name"], c); continue
        s = swap(cid, page, roots, tmp, p["layers"])
        row = {"name": p["name"], "component": cid, "variants": c.get("variants") or c.get("extended"), "props": c.get("props"),
               "swapped": s.get("swapped"), "byVariant": s.get("byVariant"), "errors": (s.get("errors") or [])[:5]}
        report.append(row)
        print(f"{p['name']}: component {cid} · swapped {row['swapped']} {row['byVariant']} · errors {len(s.get('errors') or [])}")
    u = usage(page, tmp, None)   # the rule: nothing built here may stay unused
    idle = [r["name"] for r in report if any(c["name"] == r["name"] and not c["total"] for c in u["components"])]
    if idle:
        print("NOT USED in the design yet (run sync, or remove):", idle)
    return report


def self_test():
    assert token_short("Color/Green/500") == "Green" and token_short("Color/Theme/Primary") == "Primary" and token_short("none") == ""
    assert state_name("Color/Green/500~none", ["primary", "success"]) == "success"
    assert state_name("none~Color/Theme/Primary", ["outline-primary", "primary"]) == "outline-primary"
    assert state_name("Color/Theme/White~none", ["link"]) == "light"
    assert state_name("none~none", []) == "plain"
    assert state_name("Color/Action/Blue Bg~none", ["primary"]) == "soft-primary"
    assert state_name("Color/Action/Amber Edit Bg~none", [], icon=True) == "amber"
    inv = [{"component": "Button", "source": "ui", "uses": 9, "files": 3, "figma_spec": {"variants": {"Variant": ["primary", "success"]}}}]
    smp = {"Button": [{"count": 9, "screens": 3, "w": 100, "h": 36, "fills": [
        {"fill": "Color/Green/500~none", "count": 5, "sample": "1:1", "text": "ok"}, {"fill": "Color/Theme/Primary~none", "count": 4, "sample": "1:2", "text": "go"}]}]}
    pl = plan(inv, smp, {"Button": {"figma": "Button", "layers": "^Button$"}})
    assert pl[0]["samples"] == [{"id": "1:1", "state": "success"}, {"id": "1:2", "state": "primary"}]
    print("self-test ok")


def main():
    if "--self-test" in sys.argv:
        return self_test()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["names", "plan", "apply", "sync"]); ap.add_argument("plan_file", nargs="?")
    ap.add_argument("--inventory"); ap.add_argument("--samples"); ap.add_argument("--map"); ap.add_argument("--out")
    ap.add_argument("--page"); ap.add_argument("--components-page"); ap.add_argument("--section", default="Components")
    ap.add_argument("--prune", action="store_true", help="sync: remove variants no instance uses (confirm with the user first)")
    ap.add_argument("--ignore", help="regex on component names sync/usage skip (e.g. kit components: '^Flow/|^\\.')")
    a = ap.parse_args()
    if a.cmd == "names":
        m = json.loads(Path(a.map).read_text(encoding="utf-8"))
        Path(a.out).write_text(json.dumps({"names": {k: v["layers"] for k, v in m.items()}, "min": 3}, ensure_ascii=False), encoding="utf-8")
        print(f"wrote {a.out}"); return
    if a.cmd == "plan":
        rows = plan(json.loads(Path(a.inventory).read_text(encoding="utf-8")), json.loads(Path(a.samples).read_text(encoding="utf-8")),
                    json.loads(Path(a.map).read_text(encoding="utf-8")))
        Path(a.out).write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
        for r in rows:
            print(f"{r['copies']:>5} copies on {r['screens']:>3} screens  {r['name']:<16} ← {r['code']:<14} states: {', '.join(s['state'] for s in r['samples'])}")
        return
    if a.cmd == "sync":
        rep = sync(a.page, a.ignore, a.prune)
        if a.out:
            Path(a.out).write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
        return
    rows = json.loads(Path(a.plan_file).read_text(encoding="utf-8"))
    rep = apply(rows, a.page, a.components_page, a.section)
    if a.out:
        Path(a.out).write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
