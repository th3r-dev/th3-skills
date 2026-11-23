#!/usr/bin/env python3
"""Check a built model against a benchmark case kept in TOON (benchmarks/*.toon).

  python bench_model.py <case.toon> <model.glb>     exit code = failed checks
  python bench_model.py --selftest

The case holds the prompt as the user typed it, the budget and a rubric table. Each rubric id is
a check below; an id with no check fails, so the case and the script stay in step. An id whose
check text starts with "manual:" is printed for a person and not counted.

  budget   total triangles (every mesh instance) at most max_tris
  engine   mesh_check.py's limits for the case's target pass
  closed   every mesh is closed: edges, welded by position, each shared by exactly 2 triangles
  parts    every name in parts is a node in the file
  fur      at least min_fur nodes whose names start with fur_prefix
  source   the case's source file sits next to the model
  renders  every name in views has <name>.png of at least 2 KB next to the model
  materials  at most max_materials materials in the file
  textures   every image is a power of two on both sides and at most max_texture px

Stdlib only. Reads the TOON subset the cases use (as marketing/social-media's bench_post.py does).
"""
from __future__ import annotations

import argparse
import contextlib
import csv
import importlib.util
import io
import json
import re
import struct
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("mesh_check", HERE / "mesh_check.py")
mesh_check = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mesh_check)

HEAD = re.compile(r"^(\w[\w-]*)(?:\[(\d+)\])?(?:\{([^}]*)\})?:\s?(.*)$")
COMPONENT = {5121: ("B", 1), 5123: ("H", 2), 5125: ("I", 4), 5126: ("f", 4)}
WIDTH = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}


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
        key, n, cols, rest = m.groups()
        if cols:
            names = [c.strip() for c in cols.split(",")]
            rows = []
            while i < len(lines) and lines[i].startswith("  "):
                rows.append(dict(zip(names, row(lines[i]))))
                i += 1
            assert len(rows) == int(n), f"{key}: declared {n} rows, found {len(rows)}"
            out[key] = rows
        elif n is not None:
            items = row(rest) if rest else []
            assert len(items) == int(n), f"{key}: declared {n} items, found {len(items)}"
            out[key] = items
        else:
            out[key] = scalar(rest)
    return out


def accessor_values(doc, binary, index):
    """An accessor's values as a flat list (no sparse accessors, buffer 0 only)."""
    acc = doc["accessors"][index]
    fmt, size = COMPONENT[acc["componentType"]]
    width = WIDTH[acc["type"]]
    view = doc["bufferViews"][acc["bufferView"]]
    start = view.get("byteOffset", 0) + acc.get("byteOffset", 0)
    stride = view.get("byteStride") or size * width
    values = []
    for k in range(acc["count"]):
        values.extend(struct.unpack_from(f"<{width}{fmt}", binary, start + k * stride))
    return values


def open_edges(doc, binary, mesh) -> int:
    """Edges not shared by exactly two triangles, with vertices welded by position."""
    edges: dict[tuple, int] = {}
    for prim in mesh.get("primitives", []):
        if prim.get("mode", 4) != 4:
            continue
        pos = accessor_values(doc, binary, prim["attributes"]["POSITION"])
        keys = [tuple(round(c, 4) for c in pos[i:i + 3]) for i in range(0, len(pos), 3)]
        idx = accessor_values(doc, binary, prim["indices"]) if "indices" in prim else list(range(len(keys)))
        for t in range(0, len(idx) - 2, 3):
            a, b, c = keys[idx[t]], keys[idx[t + 1]], keys[idx[t + 2]]
            for e in ((a, b), (b, c), (c, a)):
                if e[0] != e[1]:
                    k = tuple(sorted(e))
                    edges[k] = edges.get(k, 0) + 1
    return sum(1 for n in edges.values() if n != 2)


def run(case: dict, model: Path) -> dict[str, tuple[bool | None, str]]:
    doc, binary = mesh_check.read_gltf(model)
    meshes, images = mesh_check.check_gltf(model)
    names = {n.get("name", "") for n in doc.get("nodes", [])}
    results: dict[str, tuple[bool | None, str]] = {}
    for r in case["rubric"]:
        rid = r["id"]
        if str(r["check"]).startswith("manual:"):
            results[rid] = (None, r["check"])
        elif rid == "budget":
            total = sum(m["tris"] * m["instances"] for m in meshes)
            results[rid] = (total <= case["max_tris"], f"{total} triangles, budget {case['max_tris']}")
        elif rid == "engine":
            t = mesh_check.TARGETS[case["target"]]
            with contextlib.redirect_stdout(io.StringIO()) as out:
                code = mesh_check.check(model, t["max_tris_per_mesh"], t["max_texture"], None)
            over = [ln for ln in out.getvalue().splitlines() if ln.startswith("over")]
            results[rid] = (code == 0, f"{case['target']}: " + ("; ".join(over) or "within limits"))
        elif rid == "closed":
            bad = {m.get("name", f"mesh{i}"): open_edges(doc, binary, m)
                   for i, m in enumerate(doc.get("meshes", []))}
            bad = {k: v for k, v in bad.items() if v}
            results[rid] = (not bad, "all closed" if not bad else
                            ", ".join(f"{k}: {v} open edges" for k, v in bad.items()))
        elif rid == "parts":
            missing = [p for p in case["parts"] if p not in names]
            results[rid] = (not missing, "all present" if not missing else "missing " + ", ".join(missing))
        elif rid == "fur":
            fur = sorted(n for n in names if n.startswith(case["fur_prefix"]))
            results[rid] = (len(fur) >= case["min_fur"], f"{len(fur)} fur nodes: {', '.join(fur) or '-'}")
        elif rid == "source":
            p = model.parent / case["source"]
            results[rid] = (p.is_file(), str(p.name) + (" present" if p.is_file() else " missing"))
        elif rid == "renders":
            small = [v for v in case["views"]
                     if not (model.parent / f"{v}.png").is_file() or (model.parent / f"{v}.png").stat().st_size < 2048]
            results[rid] = (not small, "all views rendered" if not small else "missing or blank: " + ", ".join(small))
        elif rid == "materials":
            n = len(doc.get("materials", []))
            results[rid] = (n <= case["max_materials"], f"{n} materials, at most {case['max_materials']}")
        elif rid == "textures":
            pot = lambda v: v > 0 and v & (v - 1) == 0
            bad = [f"{t['name']} {t['size']}" for t in images
                   if not t["size"] or not all(pot(v) and v <= case["max_texture"] for v in t["size"])]
            sizes = ", ".join(f"{t['name']} {t['size'][0]}x{t['size'][1]}" for t in images if t["size"]) or "none"
            results[rid] = (not bad, sizes if not bad else "not a power of two or too big: " + ", ".join(bad))
        else:
            results[rid] = (False, "no check implements this rubric id")
    return results


def _tetra_glb(path: Path, open_one=False):
    pos = [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1]
    idx = [0, 2, 1, 0, 1, 3, 0, 3, 2] + ([] if open_one else [1, 2, 3])
    pb = struct.pack(f"<{len(pos)}f", *pos)
    ib = struct.pack(f"<{len(idx)}H", *idx)
    doc = {
        "asset": {"version": "2.0"},
        "buffers": [{"byteLength": len(pb) + len(ib)}],
        "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": len(pb)},
                        {"buffer": 0, "byteOffset": len(pb), "byteLength": len(ib)}],
        "accessors": [{"bufferView": 0, "componentType": 5126, "count": 4, "type": "VEC3",
                       "min": [0, 0, 0], "max": [1, 1, 1]},
                      {"bufferView": 1, "componentType": 5123, "count": len(idx), "type": "SCALAR"}],
        "meshes": [{"name": "Body", "primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}],
        "nodes": [{"name": "Body", "mesh": 0}, {"name": "FurA", "mesh": 0}],
    }
    path.write_bytes(mesh_check._glb(doc, pb + ib))


def selftest() -> int:
    case = load_toon(
        "target: roblox\nmax_tris: 8\nmin_fur: 1\nfur_prefix: Fur\nsource: build.py\n"
        "parts[2]: Body,Tail\nviews[1]: front\n"
        "max_materials: 1\nmax_texture: 512\n"
        "rubric[10]{id,check}:\n  budget,x\n  engine,x\n  closed,x\n  parts,x\n  fur,x\n"
        "  source,x\n  renders,x\n  materials,x\n  textures,x\n  look,\"manual: open it\"\n")
    with tempfile.TemporaryDirectory() as d:
        glb = Path(d) / "m.glb"
        _tetra_glb(glb)
        r = run(case, glb)
        assert r["budget"][0] and r["engine"][0] and r["closed"][0], r
        assert not r["parts"][0] and "Tail" in r["parts"][1]
        assert r["fur"][0] and not r["source"][0] and not r["renders"][0]
        assert r["look"][0] is None
        assert r["materials"][0] and r["textures"][0]  # no materials, no images: nothing over
        _tetra_glb(glb, open_one=True)
        assert not run(case, glb)["closed"][0]
        case["rubric"].append({"id": "nope", "check": "x"})
        assert run(case, glb)["nope"][0] is False
    print("selftest ok")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("case", nargs="?")
    ap.add_argument("model", nargs="?")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if not (a.case and a.model):
        ap.print_help()
        return 2
    case = load_toon(Path(mesh_check.inside_cwd(a.case)).read_text(encoding="utf-8"))
    results = run(case, Path(mesh_check.inside_cwd(a.model)))
    failed = 0
    for rid, (ok, why) in results.items():
        mark = "MANUAL" if ok is None else "PASS" if ok else "FAIL"
        failed += ok is False
        print(f"{mark}\t{rid}\t{why}")
    counted = sum(1 for ok, _ in results.values() if ok is not None)
    print(f"score\t{counted - failed}/{counted}")
    return failed


if __name__ == "__main__":
    sys.exit(main())
