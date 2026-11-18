#!/usr/bin/env python3
"""Wire a coding agent to a game engine's MCP server. Stdlib only, Python 3.10+.

  list                                  the engines, their server, transport and the editor-side step
  doctor --engine ID                    is the server's command on disk, or its HTTP port listening
  config --engine ID --client NAME      show the client config entry; --write writes it
                                        (claude, cursor, gemini, vscode: project file; codex: printed only)
  --selftest                            run the built-in checks

Nothing is installed, downloaded or signed in to: those steps are printed for the person.
Every server is pinned to a version; references/<engine>.md says where each one comes from.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import socket
import sys
from pathlib import Path
from urllib.parse import urlparse

# client -> project config file, and the key its servers live under
PROJECT_FILES = {
    "claude": (".mcp.json", "mcpServers"),
    "cursor": (".cursor/mcp.json", "mcpServers"),
    "gemini": (".gemini/settings.json", "mcpServers"),
    "vscode": (".vscode/mcp.json", "servers"),
}
CLIENTS = (*PROJECT_FILES, "codex")


def _roblox(osn: str, root: str) -> dict:
    # create.roblox.com/docs/studio/mcp, read 2026-11-18
    if osn == "windows":
        return {"command": "cmd.exe", "args": ["/c", r"%LOCALAPPDATA%\Roblox\mcp.bat"]}
    if osn == "macos":
        return {"command": "/Applications/RobloxStudio.app/Contents/MacOS/StudioMCP"}
    raise SystemExit("engine_mcp: Roblox Studio runs on macOS and Windows only")


def _unity(osn: str, root: str) -> dict:
    # docs.unity3d.com/Packages/com.unity.ai.assistant@2.6 (Unity MCP), read 2026-11-18.
    # The docs warn that `~` may not expand, so the path is written out in full.
    relay = Path.home() / ".unity" / "relay"
    exe = {
        "windows": relay / "relay_win.exe",
        "linux": relay / "relay_linux",
    }.get(osn) or relay / ("relay_mac_x64.app/Contents/MacOS/relay_mac_x64" if platform.machine() == "x86_64"
                           else "relay_mac_arm64.app/Contents/MacOS/relay_mac_arm64")
    return {"command": str(exe), "args": ["--mcp"], "env": {"UNITY_PROJECT_PATH": root}}


def _npx(osn: str, *args: str) -> dict:
    return {"command": "cmd", "args": ["/c", "npx", "-y", *args]} if osn == "windows" else {"command": "npx", "args": ["-y", *args]}


# id -> (server name, official, entry maker, the editor-side step the person does)
ENGINES = {
    "roblox": ("Roblox_Studio", True, _roblox,
               "Studio: Assistant > ... > Manage MCP Servers > Enable Studio as MCP server"),
    "unity": ("unity-mcp", True, _unity,
              "Unity 6+ with com.unity.ai.assistant: Project Settings > AI > Unity MCP, bridge Running; accept the client's Pending Connection"),
    "unreal": ("unreal-mcp", True, lambda osn, root: {"url": "http://127.0.0.1:8000/mcp"},
               "UE 5.8+: enable the Unreal MCP plugin and a toolset plugin, restart; Editor Preferences > Model Context Protocol > Auto Start Server"),
    "godot": ("godot", False, lambda osn, root: _npx(osn, "godot-mcp-server@0.6.1"),
              "Godot 4.4+: install the Godlink addon (addons/godot_mcp), enable it in Project Settings > Plugins, keep the editor open"),
    "blender": ("blender", False, lambda osn, root: {"command": "uvx", "args": ["mcp-for-blender@2.3.0"], "env": {"DISABLE_TELEMETRY": "true"}},
                "Blender: `uvx mcp-for-blender@2.3.0 install-addon`, then enable 'Interface: MCP for Blender' in Preferences"),
    "web": ("chrome-devtools", True, lambda osn, root: _npx(osn, "chrome-devtools-mcp@1.13.0", "--no-usage-statistics", "--isolated"),
            "start the game's dev server; the MCP server opens its own Chrome"),
    "playwright": ("playwright", True, lambda osn, root: _npx(osn, "@playwright/mcp@0.0.85", "--caps=vision", "--isolated"),
                   "start the game's dev server; the MCP server opens its own browser"),
    "bevy": ("bevy_brp", False, lambda osn, root: {"command": "bevy_brp_mcp"},
             "`cargo install bevy_brp_mcp` (match the Bevy version), enable the game's bevy_remote feature"),
}


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
    return {"Darwin": "macos", "Windows": "windows"}.get(platform.system(), "linux")


def client_entry(base: dict, client: str) -> dict:
    """One server in the shape a client's config expects: stdio (command) or HTTP (url)."""
    if "url" in base:
        return {"httpUrl": base["url"]} if client == "gemini" else (
            {"url": base["url"]} if client == "cursor" else {"type": "http", "url": base["url"]})
    return {"type": "stdio", **base} if client == "vscode" else dict(base)


def merge_config(text: str | None, key: str, name: str, entry: dict) -> tuple[str, str]:
    """Add the server to a JSON config, keeping every other entry. Returns (new text, what changed)."""
    data = {} if not (text or "").strip() else json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("the config file is not a JSON object")
    servers = data.setdefault(key, {})
    if not isinstance(servers, dict):
        raise ValueError(f'"{key}" is not a JSON object')
    old = servers.get(name)
    if old == entry:
        return json.dumps(data, indent=2) + "\n", "unchanged"
    servers[name] = entry
    return json.dumps(data, indent=2) + "\n", "replaced" if old is not None else "added"


def codex_snippet(name: str, entry: dict) -> str:
    lines = [f"[mcp_servers.{name}]"]  # TOML bare keys allow letters, digits, - and _
    if "url" in entry:
        lines.append(f"url = {json.dumps(entry['url'])}")
    else:
        lines.append(f"command = {json.dumps(entry['command'])}")
        if entry.get("args"):
            lines.append("args = [" + ", ".join(json.dumps(a) for a in entry["args"]) + "]")
        if entry.get("env"):
            lines.append("env = { " + ", ".join(f"{k} = {json.dumps(v)}" for k, v in entry["env"].items()) + " }")
    return "\n".join(lines)


def claude_add(name: str, entry: dict) -> str:
    if "url" in entry:
        return f"claude mcp add --transport http {name} {entry['url']}"
    env = "".join(f" -e {k}={v}" for k, v in entry.get("env", {}).items())
    return " ".join([f"claude mcp add{env} {name} --", entry["command"], *entry.get("args", [])])


def cmd_list(args) -> int:
    print("engine\tserver\ttransport\tofficial\teditor side")
    for eid, (name, official, make, step) in ENGINES.items():
        transport = "http" if "url" in make("macos", "") else "stdio"
        print(f"{eid}\t{name}\t{transport}\t{'yes' if official else 'community'}\t{step}")
    return 0


def cmd_doctor(args) -> int:
    name, _, make, step = ENGINES[args.engine]
    base = make(os_name(args.os), args.root)
    if "url" in base:
        u = urlparse(base["url"])
        try:
            with socket.create_connection((u.hostname, u.port), timeout=1):
                print(f"server\t{base['url']}\tlistening")
                return 0
        except OSError:
            print(f"server\t{base['url']}\tnot listening")
    else:
        cmd = base["command"]
        found = shutil.which(cmd) or (cmd if Path(cmd).exists() else None)
        print(f"command\t{cmd}\t{found or '-'}")
        if found:
            return 0
    print(f"NEEDS\t{step}")
    return 1


def cmd_config(args) -> int:
    name, _, make, step = ENGINES[args.engine]
    base = make(os_name(args.os), args.root)
    if args.client == "codex":
        print("# Codex keeps MCP servers in its global ~/.codex/config.toml; add this block there:")
        print(codex_snippet(name, base))
        return 0
    rel, key = PROJECT_FILES[args.client]
    path = Path(args.root) / rel
    old = path.read_text(encoding="utf-8") if path.exists() else None
    try:
        new, change = merge_config(old, key, name, client_entry(base, args.client))
    except (ValueError, json.JSONDecodeError) as e:
        print(f"refused\t{rel}\t{e}: fix it by hand, nothing was written")
        return 3
    if args.client == "claude":
        print(f"# or, without a project file: {claude_add(name, base)}")
    if str(Path.home()) in json.dumps(base):
        print(f"# {rel} will hold a path under your home folder: keep it out of git, or use the user-scope command")
    print(f"{'write' if args.write else 'would_write'}\t{rel}\t{change}")
    if not args.write:
        print(new, end="")
        return 0
    if change != "unchanged":
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(new, encoding="utf-8")
    print(f"next\t{step}, then restart the agent")
    return 0


def selftest() -> int:
    mac = _roblox("macos", "/p")
    assert mac == {"command": "/Applications/RobloxStudio.app/Contents/MacOS/StudioMCP"}
    win = client_entry(_roblox("windows", "/p"), "vscode")
    assert win["type"] == "stdio" and win["command"] == "cmd.exe" and win["args"][0] == "/c"
    text, ch = merge_config('{"mcpServers": {"other": {"command": "x"}}}', "mcpServers", "Roblox_Studio", mac)
    data = json.loads(text)
    assert ch == "added" and data["mcpServers"]["other"] == {"command": "x"} and "Roblox_Studio" in data["mcpServers"]
    assert merge_config(text, "mcpServers", "Roblox_Studio", mac)[1] == "unchanged"
    for bad in ("[]", '{"mcpServers": []}'):
        try:
            merge_config(bad, "mcpServers", "x", mac)
            raise AssertionError("bad config accepted")
        except ValueError:
            pass
    http = ENGINES["unreal"][2]("macos", "/p")
    assert client_entry(http, "claude") == {"type": "http", "url": "http://127.0.0.1:8000/mcp"}
    assert client_entry(http, "gemini") == {"httpUrl": "http://127.0.0.1:8000/mcp"}
    assert client_entry(http, "cursor") == {"url": "http://127.0.0.1:8000/mcp"}
    assert 'url = "http://127.0.0.1:8000/mcp"' in codex_snippet("unreal-mcp", http)
    assert codex_snippet("unreal-mcp", http).startswith("[mcp_servers.unreal-mcp]")
    unity = _unity("linux", "/proj")
    assert unity["env"] == {"UNITY_PROJECT_PATH": "/proj"} and Path(unity["command"]).is_absolute()
    assert 'env = { DISABLE_TELEMETRY = "true" }' in codex_snippet("blender", ENGINES["blender"][2]("macos", "/p"))
    assert _npx("windows", "x@1")["args"] == ["/c", "npx", "-y", "x@1"]
    for eid, (name, _, make, _) in ENGINES.items():  # every npx/uvx server is pinned to a version
        entry = make("macos", "/p")
        if entry.get("command") in ("npx", "uvx"):
            pkg = next(a for a in entry["args"] if a != "-y")
            assert "@" in pkg.lstrip("@") and "latest" not in pkg, f"{eid}: unpinned {pkg}"
    print("selftest ok")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true", help="run the built-in checks")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("list")
    for name in ("doctor", "config"):
        p = sub.add_parser(name)
        p.add_argument("--engine", required=True, choices=ENGINES)
        p.add_argument("--root", default=".", help="the game project (default: here)")
        p.add_argument("--os", choices=("macos", "windows", "linux"), help="override the detected OS")
        if name == "config":
            p.add_argument("--client", required=True, choices=CLIENTS)
            p.add_argument("--write", action="store_true", help="write the project config (default: show it)")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    if not args.cmd:
        ap.print_help()
        return 2
    if args.cmd == "list":
        return cmd_list(args)
    args.root = inside_cwd(args.root)
    return {"doctor": cmd_doctor, "config": cmd_config}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
