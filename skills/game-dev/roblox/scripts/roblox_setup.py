#!/usr/bin/env python3
"""Roblox Studio setup for any coding agent. Stdlib only, Python 3.10+.

  doctor                      what is installed: Studio, its MCP binary, Rokit and the pinned tools
  mcp --client NAME [--write] wire an agent to Studio's built-in MCP server
                              (claude, cursor, gemini, vscode: project file; codex: printed only)
  scaffold [--dry-run]        copy the Rojo starter into the project, never overwriting a file
  --selftest                  run the built-in checks

Nothing is installed, downloaded or signed in to: those steps are printed for the person.
Every write is shown first; `mcp` and `scaffold` change files only without --dry-run / with --write.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCAFFOLD = HERE.parent / "scaffold"
TOOLS = ("rokit", "rojo", "selene", "stylua", "lune")
SERVER = "Roblox_Studio"

# create.roblox.com/docs/studio/mcp, read 2026-11-16
MAC_STUDIO = Path("/Applications/RobloxStudio.app")
MAC_MCP = MAC_STUDIO / "Contents/MacOS/StudioMCP"
WIN_MCP_ARGS = ["/c", r"%LOCALAPPDATA%\Roblox\mcp.bat"]

# client -> project config file, and the key its servers live under
PROJECT_FILES = {
    "claude": (".mcp.json", "mcpServers"),
    "cursor": (".cursor/mcp.json", "mcpServers"),
    "gemini": (".gemini/settings.json", "mcpServers"),
    "vscode": (".vscode/mcp.json", "servers"),
}
CLIENTS = (*PROJECT_FILES, "codex")


def inside_cwd(path: str) -> str:
    """`path` resolved, refused unless it lies inside the current directory: a path argument (often
    written by an agent) can never read or write elsewhere."""
    base = os.path.realpath(os.getcwd())
    full = os.path.realpath(path)
    if os.path.commonpath([base, full]) != base:
        raise SystemExit(f"{path}: outside the current directory ({base}); run from a folder that contains it")
    return full


def os_name(override: str | None = None) -> str:
    if override:
        return override
    s = platform.system()
    return {"Darwin": "macos", "Windows": "windows"}.get(s, "linux")


def server_entry(osn: str, client: str) -> dict:
    """The Studio MCP server as one client config entry."""
    if osn == "windows":
        entry = {"command": "cmd.exe", "args": list(WIN_MCP_ARGS)}
    elif osn == "macos":
        entry = {"command": str(MAC_MCP)}
    else:
        raise SystemExit("roblox_setup: Roblox Studio runs on macOS and Windows only")
    if client == "vscode":
        entry = {"type": "stdio", **entry}
    return entry


def merge_config(text: str | None, key: str, entry: dict) -> tuple[str, str]:
    """Add the server to a JSON config, keeping every other entry. Returns (new text, what changed)."""
    data = {} if not (text or "").strip() else json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("the config file is not a JSON object")
    servers = data.setdefault(key, {})
    if not isinstance(servers, dict):
        raise ValueError(f'"{key}" is not a JSON object')
    old = servers.get(SERVER)
    if old == entry:
        return json.dumps(data, indent=2) + "\n", "unchanged"
    servers[SERVER] = entry
    return json.dumps(data, indent=2) + "\n", "replaced" if old is not None else "added"


def codex_snippet(entry: dict) -> str:
    lines = [f"[mcp_servers.{SERVER}]", f"command = {json.dumps(entry['command'])}"]
    if entry.get("args"):
        lines.append("args = [" + ", ".join(json.dumps(a) for a in entry["args"]) + "]")
    return "\n".join(lines)


def tool_version(name: str) -> str:
    exe = shutil.which(name)
    if not exe:
        return "-"
    try:
        out = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=15)
        return (out.stdout or out.stderr).strip().splitlines()[0] if (out.stdout or out.stderr).strip() else exe
    except (OSError, subprocess.TimeoutExpired):
        return exe


def cmd_doctor(args) -> int:
    osn = os_name(args.os)
    rows = [("os", osn)]
    if osn == "macos":
        rows += [("studio", str(MAC_STUDIO) if MAC_STUDIO.exists() else "-"),
                 ("studio_mcp", str(MAC_MCP) if MAC_MCP.exists() else "-")]
    elif osn == "windows":
        base = Path(os.environ.get("LOCALAPPDATA", "")) / "Roblox"
        rows += [("studio", str(base / "Versions") if (base / "Versions").exists() else "-"),
                 ("studio_mcp", str(base / "mcp.bat") if (base / "mcp.bat").exists() else "-")]
    else:
        rows += [("studio", "- (Studio runs on macOS and Windows only)")]
    rows += [(f"tool:{t}", tool_version(t)) for t in TOOLS]
    root = Path(args.root)
    rows += [(f, "present" if (root / f).exists() else "-") for f in ("default.project.json", "rokit.toml", "tests/run.luau")]
    for k, v in rows:
        print(f"{k}\t{v}")
    needs = []
    if dict(rows).get("studio", "-").startswith("-") and osn != "linux":
        needs.append("install Roblox Studio from create.roblox.com and sign in (by hand)")
    if dict(rows).get("studio_mcp") == "-" and osn != "linux":
        needs.append("update Studio, then Assistant > ... > Manage MCP Servers > Enable Studio as MCP server")
    if dict(rows)["tool:rokit"] == "-":
        needs.append("install Rokit: github.com/rojo-rbx/rokit (Installation)")
    elif dict(rows)["tool:rojo"] == "-":
        needs.append("rokit install (downloads rokit.toml's pinned tools: ask first)")
    for n in needs:
        print(f"NEEDS\t{n}")
    return 0


def cmd_mcp(args) -> int:
    osn = os_name(args.os)
    entry = server_entry(osn, args.client)
    if args.client == "codex":
        print("# Codex keeps MCP servers in its global ~/.codex/config.toml; add this block there:")
        print(codex_snippet(entry))
        return 0
    rel, key = PROJECT_FILES[args.client]
    path = Path(args.root) / rel
    old = path.read_text(encoding="utf-8") if path.exists() else None
    try:
        new, change = merge_config(old, key, entry)
    except (ValueError, json.JSONDecodeError) as e:
        print(f"refused\t{rel}\t{e}: fix it by hand, nothing was written")
        return 3
    if args.client == "claude":
        cmd = " ".join([SERVER, "--", entry["command"], *entry.get("args", [])])
        print(f"# or, without a project file: claude mcp add {cmd}")
    print(f"{'write' if args.write else 'would_write'}\t{rel}\t{change}")
    if not args.write:
        print(new, end="")
        return 0
    if change != "unchanged":
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(new, encoding="utf-8")
    print("next\tin Studio: Assistant > ... > Manage MCP Servers > Enable Studio as MCP server, then restart the agent")
    return 0


def cmd_scaffold(args) -> int:
    root = Path(args.root)
    if (root / "default.project.json").exists():
        print("refused\tdefault.project.json\tan existing Rojo project is here: nothing is copied over it")
        return 3
    title = args.title or root.resolve().name
    made = 0
    for src in sorted(p for p in SCAFFOLD.rglob("*") if p.is_file()):
        rel = src.relative_to(SCAFFOLD).as_posix()
        dst = root / rel
        if dst.exists():
            print(f"EXISTS\t{rel}")
            continue
        made += 1
        if args.dry_run:
            print(f"WOULD_CREATE\t{rel}")
            continue
        text = src.read_text(encoding="utf-8")
        if rel == "default.project.json":
            text = text.replace('"@TITLE@"', json.dumps(title))
        dst.parent.mkdir(parents=True, exist_ok=True)
        with open(dst, "x", encoding="utf-8") as fh:
            fh.write(text)
        print(f"CREATED\t{rel}")
    print(f"{'would_create' if args.dry_run else 'created'}\t{made}")
    if not args.dry_run:
        print("next\trokit install, then rojo serve and Studio > Plugins > Rojo > Connect")
    return 0


def selftest() -> int:
    mac = server_entry("macos", "claude")
    assert mac == {"command": str(MAC_MCP)}
    win = server_entry("windows", "vscode")
    assert win["type"] == "stdio" and win["command"] == "cmd.exe" and win["args"] == WIN_MCP_ARGS
    text, ch = merge_config('{"mcpServers": {"other": {"command": "x"}}}', "mcpServers", mac)
    data = json.loads(text)
    assert ch == "added" and data["mcpServers"]["other"] == {"command": "x"} and SERVER in data["mcpServers"]
    assert merge_config(text, "mcpServers", mac)[1] == "unchanged"
    for bad in ("[]", '{"mcpServers": []}'):
        try:
            merge_config(bad, "mcpServers", mac)
            raise AssertionError("bad config accepted")
        except ValueError:
            pass
    assert 'args = ["/c"' in codex_snippet(server_entry("windows", "codex"))
    with tempfile.TemporaryDirectory() as d:
        ns = argparse.Namespace(root=d, title='a "quoted" game', dry_run=False)
        assert cmd_scaffold(ns) == 0
        proj = json.loads((Path(d) / "default.project.json").read_text())
        assert proj["name"] == 'a "quoted" game'
        assert (Path(d) / "tests/run.luau").exists()
        assert cmd_scaffold(ns) == 3  # never over an existing project
    print("selftest ok")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true", help="run the built-in checks")
    sub = ap.add_subparsers(dest="cmd")
    for name in ("doctor", "mcp", "scaffold"):
        p = sub.add_parser(name)
        p.add_argument("--root", default=".", help="the game project (default: here)")
        p.add_argument("--os", choices=("macos", "windows", "linux"), help="override the detected OS")
        if name == "mcp":
            p.add_argument("--client", required=True, choices=CLIENTS)
            p.add_argument("--write", action="store_true", help="write the project config (default: show it)")
        if name == "scaffold":
            p.add_argument("--dry-run", action="store_true")
            p.add_argument("--title", help="the game's name (default: the folder's)")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    if not args.cmd:
        ap.print_help()
        return 2
    args.root = inside_cwd(args.root)
    return {"doctor": cmd_doctor, "mcp": cmd_mcp, "scaffold": cmd_scaffold}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
