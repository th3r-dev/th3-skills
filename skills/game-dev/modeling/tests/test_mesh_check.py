import pytest
import importlib.util
import json
import struct
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("mesh_check", HERE.parent / "scripts" / "mesh_check.py")
mc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mc)


@pytest.fixture(autouse=True)
def _run_inside_tmp(tmp_path, monkeypatch):
    # path arguments are refused outside the current directory, so each test runs inside its own
    monkeypatch.chdir(tmp_path)


def test_selftest():
    assert mc.selftest() == 0


def _write_glb(path, tris, strip=False):
    count = tris + 2 if strip else tris * 3
    doc = {
        "asset": {"version": "2.0"},
        "accessors": [{"count": count, "min": [0, 0, 0], "max": [1, 1, 1]}],
        "meshes": [{"name": "m", "primitives": [{"attributes": {"POSITION": 0}, "mode": 5 if strip else 4}]}],
        "nodes": [{"mesh": 0}],
    }
    path.write_bytes(mc._glb(doc))


def test_roblox_limit_is_per_mesh(tmp_path, capsys):
    ok = tmp_path / "ok.glb"
    _write_glb(ok, 20000)
    assert mc.main([str(ok), "--target", "roblox"]) == 0
    big = tmp_path / "big.glb"
    _write_glb(big, 20001)
    assert mc.main([str(big), "--target", "roblox"]) == 1
    assert "over\tmesh m: 20001 triangles > 20000" in capsys.readouterr().out


def test_triangle_strip_counts(tmp_path):
    p = tmp_path / "strip.glb"
    _write_glb(p, 10, strip=True)
    meshes, _ = mc.check_gltf(p)
    assert meshes[0]["tris"] == 10


def test_web_has_no_default_limit_but_takes_a_budget(tmp_path):
    p = tmp_path / "scene.glb"
    _write_glb(p, 50000)
    assert mc.main([str(p), "--target", "web"]) == 0
    assert mc.main([str(p), "--target", "web", "--max-total", "40000"]) == 1


def test_gltf_with_external_png(tmp_path):
    png = b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", 512, 512) + b"\0" * 5
    (tmp_path / "albedo.png").write_bytes(png)
    doc = {"asset": {"version": "2.0"}, "images": [{"uri": "albedo.png"}], "meshes": []}
    (tmp_path / "m.gltf").write_text(json.dumps(doc))
    _, textures = mc.check_gltf(tmp_path / "m.gltf")
    assert textures[0]["size"] == (512, 512)


def test_unreadable_is_exit_2(tmp_path):
    p = tmp_path / "x.glb"
    p.write_bytes(b"glTF" + struct.pack("<II", 1, 20) + b"\0" * 8)
    assert mc.main([str(p)]) == 2


def test_worked_cases_score_full_marks():
    spec = importlib.util.spec_from_file_location("bench_model", HERE.parent / "scripts" / "bench_model.py")
    bm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bm)
    assert bm.selftest() == 0
    for case_name, model in (("lowpoly-furry-cat", "lowpoly-cat/cat.glb"),
                             ("lowpoly-wizard-cat", "wizard-cat/wizard-cat.glb")):
        case = bm.load_toon((HERE.parent / "benchmarks" / f"{case_name}.toon").read_text(encoding="utf-8"))
        results = bm.run(case, HERE.parent / "examples" / model)
        assert all(ok in (True, None) for ok, _ in results.values()), (case_name, results)


def test_model_outside_the_current_directory_is_refused(tmp_path):
    with pytest.raises(SystemExit, match="outside the current directory"):
        mc.main([str(tmp_path.parent / "x.glb")])
