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
import importlib.util
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

# The MCP config writer is shared by every engine: it lives in the engine-mcp sub-skill.
_spec = importlib.util.spec_from_file_location("engine_mcp", HERE.parents[1] / "engine-mcp/scripts/engine_mcp.py")
engine_mcp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(engine_mcp)
CLIENTS = engine_mcp.CLIENTS

MAC_STUDIO = Path("/Applications/RobloxStudio.app")
MAC_MCP = Path(engine_mcp.ENGINES["roblox"][2]("macos", "")["command"])


def inside_cwd(path: str) -> str:
    """`path` resolved, refused unless it lies inside the current directory: a path argument (often
    written by an agent) can never read or write elsewhere."""
    base = os.path.realpath(os.getcwd())
    full = os.path.realpath(path)
    if full != base and not full.startswith(base + os.sep):
        raise SystemExit(f"{path}: outside the current directory ({base}); run from a folder that contains it")
    return full


def os_name(override: str | None = None) -> str:
    if override:
        return override
    s = platform.system()
    return {"Darwin": "macos", "Windows": "windows"}.get(s, "linux")


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
    args.engine = "roblox"
    return engine_mcp.cmd_config(args)


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
    assert engine_mcp.selftest() == 0  # the MCP config writer
    assert MAC_MCP.name == "StudioMCP"
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
            # any agent the skill runs in; Claude Code is the default, the others are one flag away
            p.add_argument("--client", default="claude", choices=CLIENTS, help="the agent to wire (default: claude)")
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
