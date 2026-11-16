#!/usr/bin/env python3
"""Check a model file against a game engine's import limits, before it is imported. Stdlib only.

  python mesh_check.py MODEL [--target roblox|web] [--max-tris N] [--max-texture PX]
  python mesh_check.py --selftest

Reads .glb, .gltf and .obj (FBX is binary and proprietary: export a .glb beside it to check).
Prints TSV rows: one `mesh` row per mesh (triangles, n-gons for OBJ, local bounds), one
`texture` row per image (pixel size), then `total` and one `over` row per broken limit.
Exit 0 within limits, 1 over a limit, 2 unreadable file.

Targets (sources read 2026-11-16):
  roblox  20,000 triangles per mesh; textures at most 1024 px per side recommended
          (create.roblox.com/docs/art/modeling/specifications, .../texture-specifications)
  web     no fixed limit: pass --max-tris for the scene budget
A count is geometry only: it says nothing about topology quality, UVs or how the model looks.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import struct
import sys
import tempfile
from pathlib import Path

TARGETS = {
    "roblox": {"max_tris_per_mesh": 20000, "max_texture": 1024},
    "web": {"max_tris_per_mesh": None, "max_texture": 4096},
}
GLB_MAGIC, CHUNK_JSON, CHUNK_BIN = b"glTF", 0x4E4F534A, 0x004E4942


def inside_cwd(path: str) -> str:
    """`path` resolved, refused unless it lies inside the current directory: a path argument (often
    written by an agent) can never read or write elsewhere."""
    base = os.path.realpath(os.getcwd())
    full = os.path.realpath(path)
    if full != base and not full.startswith(base + os.sep):
        raise SystemExit(f"{path}: outside the current directory ({base}); run from a folder that contains it")
    return full


class Unreadable(Exception):
    pass


def image_size(data: bytes) -> tuple[int, int] | None:
    """Width and height of a PNG or JPEG from its header, or None."""
    if data[:8] == b"\x89PNG\r\n\x1a\n" and len(data) >= 24:
        return struct.unpack(">II", data[16:24])
    if data[:2] == b"\xff\xd8":
        i = 2
        while i + 9 < len(data):
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            length = struct.unpack(">H", data[i + 2:i + 4])[0]
            if marker in (0xC0, 0xC1, 0xC2):
                h, w = struct.unpack(">HH", data[i + 5:i + 9])
                return w, h
            i += 2 + length
    return None


def read_gltf(path: Path) -> tuple[dict, bytes | None]:
    raw = path.read_bytes()
    if path.suffix.lower() == ".glb" or raw[:4] == GLB_MAGIC:
        if raw[:4] != GLB_MAGIC or len(raw) < 20:
            raise Unreadable("not a GLB file")
        version, _length = struct.unpack("<II", raw[4:12])
        if version != 2:
            raise Unreadable(f"GLB version {version}, only 2 is read")
        doc, binary, i = None, None, 12
        while i + 8 <= len(raw):
            size, kind = struct.unpack("<II", raw[i:i + 8])
            chunk = raw[i + 8:i + 8 + size]
            if kind == CHUNK_JSON:
                doc = json.loads(chunk.decode("utf-8"))
            elif kind == CHUNK_BIN:
                binary = chunk
            i += 8 + size
        if doc is None:
            raise Unreadable("GLB has no JSON chunk")
        return doc, binary
    try:
        return json.loads(raw.decode("utf-8")), None
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise Unreadable(f"not glTF JSON: {e}") from e


def uri_bytes(uri: str, base: Path) -> bytes | None:
    if uri.startswith("data:"):
        return base64.b64decode(uri.split(",", 1)[1])
    p = base / uri
    return p.read_bytes() if p.is_file() else None


def check_gltf(path: Path) -> tuple[list[dict], list[dict]]:
    doc, binary = read_gltf(path)
    accessors = doc.get("accessors", [])
    buffers = doc.get("buffers", [])
    views = doc.get("bufferViews", [])

    def buffer(index: int) -> bytes | None:
        if index == 0 and binary is not None and "uri" not in buffers[0]:
            return binary
        uri = buffers[index].get("uri")
        return uri_bytes(uri, path.parent) if uri else None

    # A mesh drawn by two nodes is two instances: count each.
    uses: dict[int, int] = {}
    for node in doc.get("nodes", []):
        if "mesh" in node:
            uses[node["mesh"]] = uses.get(node["mesh"], 0) + 1
    meshes = []
    for m, mesh in enumerate(doc.get("meshes", [])):
        tris, lo, hi = 0, [float("inf")] * 3, [float("-inf")] * 3
        for prim in mesh.get("primitives", []):
            mode = prim.get("mode", 4)
            pos = prim.get("attributes", {}).get("POSITION")
            count = accessors[prim["indices"]]["count"] if "indices" in prim else (
                accessors[pos]["count"] if pos is not None else 0)
            tris += count // 3 if mode == 4 else max(count - 2, 0) if mode in (5, 6) else 0
            if pos is not None and "min" in accessors[pos] and "max" in accessors[pos]:
                lo = [min(a, b) for a, b in zip(lo, accessors[pos]["min"])]
                hi = [max(a, b) for a, b in zip(hi, accessors[pos]["max"])]
        size = [round(h - l, 4) for l, h in zip(lo, hi)] if lo[0] != float("inf") else None
        meshes.append({"name": mesh.get("name") or f"mesh{m}", "tris": tris,
                       "instances": uses.get(m, 1), "ngons": 0, "size": size})
    textures = []
    for k, img in enumerate(doc.get("images", [])):
        data = None
        if "bufferView" in img:
            v = views[img["bufferView"]]
            buf = buffer(v["buffer"])
            if buf is not None:
                start = v.get("byteOffset", 0)
                data = buf[start:start + v["byteLength"]]
        elif "uri" in img:
            data = uri_bytes(img["uri"], path.parent)
        textures.append({"name": img.get("name") or img.get("uri") or f"image{k}",
                         "size": image_size(data) if data else None})
    return meshes, textures


def check_obj(path: Path) -> tuple[list[dict], list[dict]]:
    meshes: list[dict] = []
    current = {"name": path.stem, "tris": 0, "instances": 1, "ngons": 0, "size": None}
    lo, hi = [float("inf")] * 3, [float("-inf")] * 3
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = line.split()
        if not parts:
            continue
        if parts[0] in ("o", "g") and len(parts) > 1:
            if current["tris"]:
                meshes.append(current)
            current = {"name": parts[1], "tris": 0, "instances": 1, "ngons": 0, "size": None}
        elif parts[0] == "v" and len(parts) >= 4:
            xyz = [float(x) for x in parts[1:4]]
            lo = [min(a, b) for a, b in zip(lo, xyz)]
            hi = [max(a, b) for a, b in zip(hi, xyz)]
        elif parts[0] == "f":
            corners = len(parts) - 1
            current["tris"] += max(corners - 2, 0)
            current["ngons"] += corners > 4
    if current["tris"] or not meshes:
        meshes.append(current)
    if lo[0] != float("inf"):
        size = [round(h - l, 4) for l, h in zip(lo, hi)]
        for m in meshes:
            m["size"] = size  # OBJ shares one vertex list: bounds are the whole file's
    return meshes, []


def check(path: Path, max_tris: int | None, max_texture: int | None, max_total: int | None) -> int:
    try:
        meshes, textures = check_obj(path) if path.suffix.lower() == ".obj" else check_gltf(path)
    except (OSError, Unreadable, KeyError, IndexError, ValueError, struct.error) as e:
        print(f"error\t{path}\t{e}")
        return 2
    over = []
    for m in meshes:
        size = "x".join(str(s) for s in m["size"]) if m["size"] else "-"
        print(f"mesh\t{m['name']}\ttris={m['tris']}\tinstances={m['instances']}\tngons={m['ngons']}\tsize={size}")
        if max_tris and m["tris"] > max_tris:
            over.append(f"mesh {m['name']}: {m['tris']} triangles > {max_tris}")
        if m["ngons"]:
            over.append(f"mesh {m['name']}: {m['ngons']} faces with more than 4 corners")
    for t in textures:
        w_h = f"{t['size'][0]}x{t['size'][1]}" if t["size"] else "-"
        print(f"texture\t{t['name']}\t{w_h}")
        if max_texture and t["size"] and max(t["size"]) > max_texture:
            over.append(f"texture {t['name']}: {w_h} > {max_texture} px")
    total = sum(m["tris"] * m["instances"] for m in meshes)
    print(f"total\ttris={total}\tmeshes={len(meshes)}\ttextures={len(textures)}")
    if max_total and total > max_total:
        over.append(f"scene: {total} triangles > {max_total}")
    for o in over:
        print(f"over\t{o}")
    return 1 if over else 0


def _glb(doc: dict, binary: bytes = b"") -> bytes:
    js = json.dumps(doc).encode()
    js += b" " * (-len(js) % 4)
    binary += b"\0" * (-len(binary) % 4)
    body = struct.pack("<II", len(js), CHUNK_JSON) + js
    if binary:
        body += struct.pack("<II", len(binary), CHUNK_BIN) + binary
    return GLB_MAGIC + struct.pack("<II", 2, 12 + len(body)) + body


def selftest() -> int:
    png = b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", 2048, 512) + b"\0" * 5
    doc = {
        "asset": {"version": "2.0"},
        "buffers": [{"byteLength": len(png)}],
        "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": len(png)}],
        "images": [{"name": "albedo", "bufferView": 0, "mimeType": "image/png"}],
        "accessors": [
            {"count": 30000, "min": [0, 0, 0], "max": [2, 4, 1]},  # positions
            {"count": 63000},  # indices: 21,000 triangles
        ],
        "meshes": [{"name": "rock", "primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}],
        "nodes": [{"mesh": 0}, {"mesh": 0}],
    }
    with tempfile.TemporaryDirectory() as d:
        glb = Path(d) / "rock.glb"
        glb.write_bytes(_glb(doc, png))
        meshes, textures = check_gltf(glb)
        assert meshes[0]["tris"] == 21000 and meshes[0]["instances"] == 2, meshes
        assert meshes[0]["size"] == [2, 4, 1]
        assert textures[0]["size"] == (2048, 512)
        assert check(glb, 20000, 1024, None) == 1
        assert check(glb, 30000, 4096, None) == 0
        obj = Path(d) / "box.obj"
        obj.write_text("o box\nv 0 0 0\nv 1 0 0\nv 1 1 0\nv 0 1 0\nv 0 0 1\nf 1 2 3 4\nf 1 2 3 4 5\n")
        meshes, _ = check_obj(obj)
        assert meshes[0]["tris"] == 2 + 3 and meshes[0]["ngons"] == 1
        assert check(obj, 20000, None, None) == 1  # the n-gon is over
        bad = Path(d) / "bad.glb"
        bad.write_bytes(b"nope")
        assert check(bad, None, None, None) == 2
    print("selftest ok")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("model", nargs="?")
    ap.add_argument("--target", choices=sorted(TARGETS), default="roblox")
    ap.add_argument("--max-tris", type=int, help="override the per-mesh triangle limit")
    ap.add_argument("--max-total", type=int, help="a whole-file triangle budget")
    ap.add_argument("--max-texture", type=int, help="override the texture side limit, px")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    if not args.model:
        ap.print_help()
        return 2
    t = TARGETS[args.target]
    return check(Path(inside_cwd(args.model)), args.max_tris or t["max_tris_per_mesh"],
                 args.max_texture or t["max_texture"], args.max_total)


if __name__ == "__main__":
    sys.exit(main())
