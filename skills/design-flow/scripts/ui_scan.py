#!/usr/bin/env python3
"""Scan a React/TSX codebase for the UI components it actually uses, and propose Figma components from them.

Code is the source of truth for what a component is and which states it has, so building Figma components from
the code is faster and more faithful than guessing from repeated pixels. stdlib only; regex/scanner based (no TS
parser), good enough for counting usage and literal props.

  ui_scan.py scan SRC [SRC …] [--out inventory.json] [--min 5]
      per component (import source + name): uses, files, literal prop values, boolean flags, label texts,
      icon usage → proposed Figma spec with simple names:
        variant axes  Variant / Size / Tone …  (props with 2–8 literal values, e.g. variant="primary")
        State         Default + boolean flags seen (Disabled, Loading, Active, Checked, Invalid)
        text          Label (when it has literal children text)
        boolean       Icon  (when an icon is passed or nested)
  ui_scan.py --self-test
"""
import argparse, json, re, sys
from collections import Counter, defaultdict
from pathlib import Path

SKIP_DIRS = {"node_modules", ".next", "dist", "build", ".turbo", "coverage", "__tests__", "__mocks__"}
NOT_UI = re.compile(r"(Provider|Layout|Gate|Guard|Route|Router|Fragment|Suspense|Template|Context|Head|Script|Html|Body|Wrapper|Query|Boundary)$"
                    r"|^(Col|Row|Container|Stack|Controller|Image|Link|Form|FormProvider|Trans)$")   # layout/plumbing, not visual parts
HTML_ONLY = {"button", "submit", "reset"}
AXIS_NAMES = {"variant": "Variant", "size": "Size", "color": "Tone", "bg": "Tone", "tone": "Tone", "theme": "Tone", "status": "Status",
              "type": "Type", "kind": "Kind", "appearance": "Variant", "intent": "Tone", "mode": "Mode", "shape": "Shape"}
STATE_FLAGS = {"disabled": "Disabled", "loading": "Loading", "active": "Active", "checked": "Checked",
               "isInvalid": "Invalid", "invalid": "Invalid", "readOnly": "Read only", "selected": "Selected", "isLoading": "Loading"}
IMPORT = re.compile(r"import\s+(?:type\s+)?([\w\s{},*]+?)\s+from\s+['\"]([^'\"]+)['\"]")
TAG = re.compile(r"(?<![\w.)\]])<([A-Z][\w]*(?:\.[A-Z][\w]*)?)(?=[\s/>])")   # not a TS generic like useState<T>


def imports(src):
    out = {}
    for names, mod in IMPORT.findall(src):
        names = names.strip()
        default, _, rest = names.partition("{")
        default = default.strip().strip(",").strip()
        if default and default != "*" and not default.startswith("* as"):
            out[default] = mod
        if "{" in names:
            for part in names[names.index("{") + 1: names.rindex("}")].split(","):
                part = part.strip()
                if not part or part.startswith("type "):
                    continue
                orig, _, alias = part.partition(" as ")
                out[(alias or orig).strip()] = mod
    return out


def read_tag(src, i):
    """From just after `<Name`, return (attribute text, self_closing, end index) honouring {}, quotes and template strings."""
    depth, q, j = 0, None, i
    while j < len(src):
        c = src[j]
        if q:
            if c == "\\":
                j += 2; continue
            if c == q:
                q = None
        elif c in "\"'`":
            q = c
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        elif c == ">" and depth == 0:
            return src[i:j], src[j - 1] == "/", j + 1
        j += 1
    return src[i:], True, len(src)


ATTR = re.compile(r"""([A-Za-z_][\w-]*)\s*(?:=\s*(?:"([^"]*)"|'([^']*)'|\{\s*(?:"([^"]*)"|'([^']*)'|`([^`$]*)`)\s*\}|(\{)))?""")


def attrs(text):
    text = re.sub(r"\{\s*/\*.*?\*/\s*\}|/\*.*?\*/|//[^\n]*", " ", text, flags=re.S)   # comments
    text = re.sub(r"\{\s*\.\.\.[^{}]*\}", " ", text)                                    # {...spread}
    out, i = {}, 0
    while i < len(text):
        m = ATTR.match(text, i)
        if not m:
            i += 1; continue
        name = m.group(1)
        lit = next((g for g in m.groups()[1:6] if g is not None), None)
        if m.group(7):   # {expression}: skip to its matching brace
            depth, j = 0, m.end() - 1
            while j < len(text):
                if text[j] == "{": depth += 1
                elif text[j] == "}":
                    depth -= 1
                    if depth == 0: break
                j += 1
            out[name] = ("expr", text[m.end():j].strip()[:80]); i = j + 1; continue
        out[name] = ("lit", lit) if lit is not None else ("bool", True)
        i = m.end() if m.end() > i else i + 1
    return out


def scan(roots, min_uses):
    comp = defaultdict(lambda: {"uses": 0, "files": set(), "props": defaultdict(Counter), "dyn": Counter(), "flags": Counter(),
                                "labels": Counter(), "icon": 0})
    for root in roots:
        for f in Path(root).rglob("*"):
            if f.suffix not in (".tsx", ".jsx") or any(p in SKIP_DIRS for p in f.parts) or ".test." in f.name or ".spec." in f.name:
                continue
            src = f.read_text(encoding="utf-8", errors="ignore")
            imp = imports(src)
            for m in TAG.finditer(src):
                name = m.group(1)
                base = name.split(".")[0]
                mod = imp.get(base)
                if not mod or NOT_UI.search(name):
                    continue
                a_text, closed, end = read_tag(src, m.end())
                key = f"{mod}::{name}"
                c = comp[key]; c["uses"] += 1; c["files"].add(str(f))
                for k, (kind, v) in attrs(a_text).items():
                    if k in ("key", "className", "style", "onClick", "onChange", "id", "ref", "children", "href"):
                        continue
                    if kind == "lit": c["props"][k][v] += 1
                    elif kind == "bool": c["flags"][k] += 1
                    else:
                        c["dyn"][k] += 1
                        if re.fullmatch(r"(true|false)", v or ""): c["flags"][k] += 1
                    if "icon" in k.lower(): c["icon"] += 1
                if not closed:
                    body = src[end:end + 400]
                    if re.match(r"\s*<(IconifyIcon|Icon|svg|i)\b", body) or re.search(r"<(IconifyIcon|Icon)\b", body.split("</")[0]):
                        c["icon"] += 1
                    txt = re.sub(r"<[^>]*>|\{[^}]*\}", " ", body.split(f"</{name}")[0])
                    txt = re.sub(r"\s+", " ", txt).strip()
                    if 0 < len(txt) <= 40 and not re.search(r"[;=(){}]", txt):
                        c["labels"][txt] += 1
    inv = []
    for key, c in comp.items():
        if c["uses"] < min_uses:
            continue
        mod, name = key.split("::")
        axes = {}
        for k, vals in c["props"].items():
            keep = [v for v, n in vals.most_common() if n >= 2 and v][:8] or [v for v, _ in vals.most_common(8) if v]
            if k in AXIS_NAMES and len(keep) >= 2 and sum(vals.values()) >= 3 and not set(keep) <= HTML_ONLY:
                axes.setdefault(AXIS_NAMES[k], keep)
        states = ["Default"] + sorted({STATE_FLAGS[k] for k in c["flags"] if k in STATE_FLAGS} |
                                      {STATE_FLAGS[k] for k in c["dyn"] if k in STATE_FLAGS})
        spec = {"name": name.replace(".", "/"), "variants": axes, "State": states if len(states) > 1 else None,
                "text": ["Label"] if c["labels"] else [], "Icon": c["icon"] > 0,
                "figma_names": sorted({name.split(".")[-1], name.replace(".", "")})}
        inv.append({"component": name, "source": mod, "uses": c["uses"], "files": len(c["files"]),
                    "props": {k: dict(v.most_common(8)) for k, v in c["props"].items()},
                    "flags": dict(c["flags"].most_common(8)), "dynamic": dict(c["dyn"].most_common(8)),
                    "labels": [t for t, _ in c["labels"].most_common(6)], "icon_uses": c["icon"], "figma_spec": spec})
    inv.sort(key=lambda r: -r["uses"])
    return inv


def self_test():
    src = """import { Button, Badge as B } from 'react-bootstrap';
import IconifyIcon from '@app/ui/IconifyIcon';
export const X = () => (<div>
  <Button variant="primary" size="sm" disabled onClick={() => go()}><IconifyIcon icon="a" /> บันทึก</Button>
  <Button variant={'outline-primary'} loading={isBusy}>ยกเลิก</Button>
  <Button variant="danger" style={{a: {b: 1}}}>ลบ</Button>
  <B bg="success">ok</B>
</div>);"""
    imp = imports(src)
    assert imp["Button"] == "react-bootstrap" and imp["B"] == "react-bootstrap" and imp["IconifyIcon"] == "@app/ui/IconifyIcon"
    a = attrs(' variant="primary" size="sm" disabled onClick={() => go({x: 1})} data={"q"}')
    assert a["variant"] == ("lit", "primary") and a["disabled"] == ("bool", True) and a["onClick"][0] == "expr" and a["data"] == ("lit", "q")
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        Path(d, "x.tsx").write_text(src, encoding="utf-8")
        inv = scan([d], 1)
    btn = next(r for r in inv if r["component"] == "Button")
    assert btn["uses"] == 3 and btn["props"]["variant"] == {"primary": 1, "outline-primary": 1, "danger": 1}
    assert btn["figma_spec"]["variants"]["Variant"][0] in ("primary", "outline-primary", "danger")
    assert "Disabled" in btn["figma_spec"]["State"] and "Loading" in btn["figma_spec"]["State"] and btn["figma_spec"]["Icon"]
    assert "บันทึก" in btn["labels"] or "ยกเลิก" in btn["labels"]
    print("self-test ok")


def main():
    if "--self-test" in sys.argv:
        return self_test()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["scan"]); ap.add_argument("src", nargs="+")
    ap.add_argument("--out"); ap.add_argument("--min", type=int, default=5)
    a = ap.parse_args()
    inv = scan(a.src, a.min)
    if a.out:
        Path(a.out).write_text(json.dumps(inv, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{'uses':>5} {'files':>5}  component (source) → proposed Figma spec")
    for r in inv[:60]:
        sp = r["figma_spec"]
        bits = [f"{k}={'|'.join(v[:4])}" for k, v in sp["variants"].items()]
        if sp["State"]: bits.append("State=" + "|".join(sp["State"]))
        if sp["text"]: bits.append("Label")
        if sp["Icon"]: bits.append("Icon")
        print(f"{r['uses']:>5} {r['files']:>5}  {r['component']} ({r['source']}) → {sp['name']}: {', '.join(bits)}")
    print(f"\n{len(inv)} components used ≥ {a.min} times")


if __name__ == "__main__":
    main()
