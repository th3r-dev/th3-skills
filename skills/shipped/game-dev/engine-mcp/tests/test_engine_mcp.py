import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("engine_mcp", HERE.parent / "scripts" / "engine_mcp.py")
em = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(em)


@pytest.fixture(autouse=True)
def _run_inside_tmp(tmp_path, monkeypatch):
    # path arguments are refused outside the current directory, so each test runs inside its own
    monkeypatch.chdir(tmp_path)


def test_selftest():
    assert em.selftest() == 0


@pytest.mark.parametrize("engine", sorted(em.ENGINES))
def test_every_engine_dry_runs_for_claude(tmp_path, capsys, engine):
    assert em.main(["config", "--engine", engine, "--client", "claude", "--root", str(tmp_path), "--os", "macos"]) == 0
    assert not (tmp_path / ".mcp.json").exists()
    out = capsys.readouterr().out
    assert "would_write\t.mcp.json\tadded" in out
    assert em.ENGINES[engine][0] in out


def test_http_server_shape_per_client(tmp_path):
    for client, key, expect in (("cursor", "mcpServers", {"url": "http://127.0.0.1:8000/mcp"}),
                                ("gemini", "mcpServers", {"httpUrl": "http://127.0.0.1:8000/mcp"}),
                                ("vscode", "servers", {"type": "http", "url": "http://127.0.0.1:8000/mcp"})):
        assert em.main(["config", "--engine", "unreal", "--client", client, "--root", str(tmp_path), "--write"]) == 0
        rel = em.PROJECT_FILES[client][0]
        assert json.loads((tmp_path / rel).read_text())[key]["unreal-mcp"] == expect


def test_write_keeps_other_servers_and_is_idempotent(tmp_path, capsys):
    cfg = tmp_path / ".mcp.json"
    cfg.write_text(json.dumps({"mcpServers": {"figma": {"command": "f"}}}))
    args = ["config", "--engine", "godot", "--client", "claude", "--root", str(tmp_path), "--os", "macos", "--write"]
    assert em.main(args) == 0
    data = json.loads(cfg.read_text())
    assert data["mcpServers"]["figma"] == {"command": "f"}
    assert data["mcpServers"]["godot"] == {"command": "npx", "args": ["-y", "godot-mcp-server@0.6.1"]}
    assert em.main(args) == 0
    assert "write\t.mcp.json\tunchanged" in capsys.readouterr().out


def test_unity_points_at_this_project(tmp_path, capsys):
    assert em.main(["config", "--engine", "unity", "--client", "codex", "--root", str(tmp_path), "--os", "linux"]) == 0
    out = capsys.readouterr().out
    assert "[mcp_servers.unity-mcp]" in out and f'UNITY_PROJECT_PATH = "{tmp_path.resolve()}"' in out
    assert list(tmp_path.iterdir()) == []  # codex is printed only


def test_broken_json_is_refused(tmp_path, capsys):
    (tmp_path / ".cursor").mkdir()
    (tmp_path / ".cursor" / "mcp.json").write_text("{not json")
    assert em.main(["config", "--engine", "web", "--client", "cursor", "--root", str(tmp_path), "--write"]) == 3
    assert (tmp_path / ".cursor" / "mcp.json").read_text() == "{not json"
    assert "refused" in capsys.readouterr().out


def test_doctor_reports_a_closed_port(tmp_path, capsys, monkeypatch):
    monkeypatch.setitem(em.ENGINES, "unreal", ("unreal-mcp", True, lambda osn, root: {"url": "http://127.0.0.1:9/mcp"}, "start it"))
    assert em.main(["doctor", "--engine", "unreal", "--root", str(tmp_path)]) == 1
    out = capsys.readouterr().out
    assert "not listening" in out and "NEEDS\tstart it" in out


def test_roblox_on_linux_is_refused(tmp_path):
    with pytest.raises(SystemExit, match="macOS and Windows"):
        em.main(["config", "--engine", "roblox", "--client", "claude", "--root", str(tmp_path), "--os", "linux"])


def test_root_outside_the_current_directory_is_refused(tmp_path):
    with pytest.raises(SystemExit, match="outside the current directory"):
        em.main(["config", "--engine", "web", "--client", "claude", "--root", str(tmp_path.parent / "elsewhere")])
