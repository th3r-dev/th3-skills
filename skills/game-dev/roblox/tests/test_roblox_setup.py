import pytest
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("roblox_setup", HERE.parent / "scripts" / "roblox_setup.py")
rs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rs)


@pytest.fixture(autouse=True)
def _run_inside_tmp(tmp_path, monkeypatch):
    # path arguments are refused outside the current directory, so each test runs inside its own
    monkeypatch.chdir(tmp_path)


def test_selftest():
    assert rs.selftest() == 0


def test_mcp_dry_run_writes_nothing(tmp_path, capsys):
    assert rs.main(["mcp", "--client", "cursor", "--root", str(tmp_path), "--os", "macos"]) == 0
    assert not (tmp_path / ".cursor").exists()
    assert "would_write\t.cursor/mcp.json\tadded" in capsys.readouterr().out


def test_mcp_client_defaults_to_claude(tmp_path):
    assert rs.main(["mcp", "--root", str(tmp_path), "--os", "macos", "--write"]) == 0
    assert (tmp_path / ".mcp.json").exists(), "no --client wires Claude Code"


def test_mcp_write_keeps_other_servers(tmp_path):
    cfg = tmp_path / ".mcp.json"
    cfg.write_text(json.dumps({"mcpServers": {"figma": {"command": "f"}}}))
    assert rs.main(["mcp", "--client", "claude", "--root", str(tmp_path), "--os", "macos", "--write"]) == 0
    data = json.loads(cfg.read_text())
    assert data["mcpServers"]["figma"] == {"command": "f"}
    assert data["mcpServers"]["Roblox_Studio"]["command"].endswith("StudioMCP")


def test_mcp_refuses_broken_json(tmp_path, capsys):
    (tmp_path / ".gemini").mkdir()
    (tmp_path / ".gemini" / "settings.json").write_text("{not json")
    assert rs.main(["mcp", "--client", "gemini", "--root", str(tmp_path), "--os", "windows", "--write"]) == 3
    assert (tmp_path / ".gemini" / "settings.json").read_text() == "{not json"
    assert "refused" in capsys.readouterr().out


def test_codex_is_printed_only(tmp_path, capsys):
    assert rs.main(["mcp", "--client", "codex", "--root", str(tmp_path), "--os", "macos", "--write"]) == 0
    assert list(tmp_path.iterdir()) == []
    assert "[mcp_servers.Roblox_Studio]" in capsys.readouterr().out


def test_linux_has_no_studio(tmp_path):
    try:
        rs.main(["mcp", "--client", "claude", "--root", str(tmp_path), "--os", "linux"])
    except SystemExit as e:
        assert "macOS and Windows" in str(e)
    else:
        raise AssertionError("linux accepted")


def test_scaffold_dry_run_then_write(tmp_path, capsys):
    assert rs.main(["scaffold", "--root", str(tmp_path), "--dry-run"]) == 0
    assert not (tmp_path / "default.project.json").exists()
    assert rs.main(["scaffold", "--root", str(tmp_path), "--title", "Coin Run"]) == 0
    assert json.loads((tmp_path / "default.project.json").read_text())["name"] == "Coin Run"
    for name in ("Wallet", "Pickup", "PickupFactory"):
        text = (tmp_path / f"src/shared/{name}.luau").read_text()
        assert text.startswith("--!strict")
        assert "game:" not in text and "game." not in text  # shared classes stay instance-free, so Lune can test them


def test_scaffold_keeps_existing_files(tmp_path, capsys):
    (tmp_path / "rokit.toml").write_text("# mine\n")
    assert rs.main(["scaffold", "--root", str(tmp_path)]) == 0
    assert (tmp_path / "rokit.toml").read_text() == "# mine\n"
    assert "EXISTS\trokit.toml" in capsys.readouterr().out


def test_root_outside_the_current_directory_is_refused(tmp_path):
    outside = tmp_path.parent / "elsewhere"
    with pytest.raises(SystemExit, match="outside the current directory"):
        rs.main(["scaffold", "--root", str(outside), "--dry-run"])
