#!/usr/bin/env python3
"""Run the figma-mcp-bridge server in a container (podman or docker) instead of on the host.

  bridge.py up [--work DIR] [--run-script]   build the image if missing, start the container
  bridge.py mcp                              stdio MCP server (use as the MCP command); runs `up` if needed
  bridge.py call TOOL ['{"json":"args"}' | @file.json]   one tool call over stdio, prints the result
  bridge.py run FILE.js [--allow-remove]    run_script with the file's code (e.g. figma_js.py output)
  bridge.py ensure [--file NAME]             macOS: start the plugin via Figma quick actions if NAME isn't connected
  --file NAME (or env FIGMA_FILE) on call/run targets that file by key and refuses when it isn't connected
  bridge.py hold                             keep a leader session open so the plugin stays connected
  bridge.py status | down | logs
  bridge.py --self-test

Register once:  claude mcp add figma-bridge -s user -- python3 /abs/path/bridge.py mcp
Then in Figma desktop: Plugins > Development > Import plugin from manifest (the release's
plugin/manifest.json) and run "Figma MCP Bridge" in each file.

Layout: one long-lived container publishes 127.0.0.1:1994 (the plugin's WebSocket) and mounts
--work at /work (import_html_layers and create_image read files there). Every MCP session is
`exec -i` into it: the first becomes the bridge leader, later ones follow it over localhost
inside the container, so several sessions share the plugin connection.
`run_script` (Plugin API JS, needed for figma_js.py output) is off unless --run-script.
"""
import argparse, json, os, shutil, subprocess, sys
from pathlib import Path

NAME = "figma-bridge"
IMAGE = "localhost/figma-mcp-bridge:0.0.25"
PORT = 1994
HERE = Path(__file__).resolve().parent
STATE = Path.home() / ".cache" / "design-flow" / "bridge.json"


def engine():
    for e in ("podman", "docker"):
        if shutil.which(e):
            return e
    sys.exit("needs podman or docker on PATH")


def sh(*args, check=True, capture=True):
    return subprocess.run(args, check=check, text=True, capture_output=capture)


def running(e):
    r = sh(e, "ps", "--filter", f"name=^{NAME}$", "--format", "{{.Names}}", check=False)
    return NAME in r.stdout.split()


def run_args(e, work, run_script):
    return [e, "run", "-d", "--name", NAME, "--restart", "unless-stopped",
            "-p", f"127.0.0.1:{PORT}:{PORT}",          # loopback only: the plugin is on this machine
            "-v", f"{work}:/work",
            "-e", f"FIGMA_BRIDGE_ENABLE_RUN_SCRIPT={'1' if run_script else '0'}",
            IMAGE]


def up(work=None, run_script=None):
    e = engine()
    saved = json.loads(STATE.read_text()) if STATE.exists() else {}
    work = str(Path(work or saved.get("work") or Path.cwd()).resolve())
    run_script = saved.get("run_script", False) if run_script is None else run_script
    if running(e):
        return e
    if sh(e, "image", "exists", IMAGE, check=False).returncode != 0 if e == "podman" else \
            not sh(e, "images", "-q", IMAGE, check=False).stdout.strip():
        print(f"building {IMAGE} ...", file=sys.stderr)
        sh(e, "build", "-t", IMAGE, "-f", str(HERE / "container" / "Containerfile"), str(HERE / "container"), capture=False)
    sh(e, "rm", "-f", NAME, check=False)
    r = sh(*run_args(e, work, run_script), check=False)
    if r.returncode:
        sys.exit(f"could not start {NAME}: {r.stderr.strip()}\n"
                 f"(port {PORT} busy? a host bridge started with npx would hold it — stop it first)")
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({"work": work, "run_script": run_script}))
    print(f"{NAME} up: ws://127.0.0.1:{PORT}  /work -> {work}  run_script={'on' if run_script else 'off'}", file=sys.stderr)
    return e


def mcp():
    e = up()
    # stdio passthrough; stdout must stay clean JSON-RPC, so nothing else is printed here
    os.execvp(e, [e, "exec", "-i", NAME, "figma-mcp-bridge"])


def call(tool, args, timeout=200):
    """One MCP tools/call over stdio (for agents whose session has no figma-bridge tools loaded)."""
    e = up()
    p = subprocess.Popen([e, "exec", "-i", NAME, "figma-mcp-bridge"], stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1)
    send = lambda m: (p.stdin.write(json.dumps(m) + "\n"), p.stdin.flush())
    send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "bridge.py", "version": "1"}}})
    send({"jsonrpc": "2.0", "method": "notifications/initialized"})
    send({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": tool, "arguments": args}})
    import threading
    timer = threading.Timer(timeout, p.kill); timer.start()
    try:
        for line in p.stdout:
            try:
                m = json.loads(line)
            except ValueError:
                continue
            if m.get("id") == 2:
                return m.get("result") or {"error": m.get("error")}
        return {"error": f"no reply within {timeout}s (is the Figma plugin running in the file?)"}
    finally:
        timer.cancel(); p.kill()


def files():
    """Connected files as [{fileKey, fileName}] ([] when no plugin is running)."""
    res = call("list_files", {}, 30)
    txt = "".join(c.get("text", "") for c in res.get("content", [])) if isinstance(res, dict) else ""
    try:
        return json.loads(txt)
    except ValueError:
        return []


def connected(name=None):
    fs = files()
    return any(f.get("fileName") == name for f in fs) if name else bool(fs)


def file_key(name):
    """The plugin connects to whichever file is open, so every write names its file: refuse anything else."""
    hits = [f for f in files() if f.get("fileName") == name]
    if not hits:
        sys.exit(f'file "{name}" is not connected (connected: {[f.get("fileName") for f in files()]}). '
                 f'Open it in Figma desktop and run: bridge.py ensure --file "{name}"')
    return hits[0]["fileKey"]


def ensure(name=None, plugin="Figma MCP Bridge", tries=10):
    """Figma closes dev plugins when you switch files/apps; relaunch it through quick actions (macOS only).
    With a file name, that file must be the connected one (the plugin runs in whichever tab is active)."""
    import time
    if connected(name):
        print("connected"); return 0
    if sys.platform != "darwin":
        sys.exit("plugin not connected: open the file in Figma desktop and run Plugins > Development > " + plugin)
    script = f'''tell application "Figma" to activate
delay 0.5
tell application "System Events" to tell process "Figma"
  keystroke "/" using {{command down}}
  delay 0.8
  keystroke "{plugin}"
  delay 1.2
  key code 36
end tell'''
    subprocess.run(["osascript", "-e", script], check=False, capture_output=True)
    for _ in range(tries):
        time.sleep(3)
        if connected(name):
            print("connected (plugin relaunched)"); return 0
    sys.exit(f"plugin not connected to {name or 'any file'}: is that file the active tab in Figma desktop?")


def self_test():
    a = run_args("podman", "/w", True)
    assert "127.0.0.1:1994:1994" in a and "/w:/work" in a and "FIGMA_BRIDGE_ENABLE_RUN_SCRIPT=1" in a
    assert "FIGMA_BRIDGE_ENABLE_RUN_SCRIPT=0" in run_args("docker", "/w", False)
    assert (HERE / "container" / "Containerfile").exists()
    print("self-test ok")


def main():
    if "--self-test" in sys.argv:
        return self_test()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["up", "mcp", "call", "run", "hold", "ensure", "status", "down", "logs"])
    ap.add_argument("tool", nargs="?")
    ap.add_argument("args", nargs="?", default="{}", help="JSON object, or @path to a JSON file")
    ap.add_argument("--timeout", type=int, default=200)
    ap.add_argument("--allow-remove", action="store_true", help="run: allow .remove() in the script")
    ap.add_argument("--file", default=os.environ.get("FIGMA_FILE"),
                    help="Figma file name to target (or env FIGMA_FILE); call/run refuse if it isn't connected")
    ap.add_argument("--work", help="host dir mounted at /work (default: last used, else cwd)")
    ap.add_argument("--run-script", action=argparse.BooleanOptionalAction, default=None,
                    help="enable run_script (arbitrary Plugin API JS in the open file)")
    a = ap.parse_args()
    if a.cmd == "mcp":
        return mcp()
    if a.cmd == "hold":  # stdin never closes, so this exec stays the bridge leader
        e = up()
        os.execvp("sh", ["sh", "-c", f"tail -f /dev/null | {e} exec -i {NAME} figma-mcp-bridge >/dev/null"])
    if a.cmd == "ensure":
        return ensure(a.file)
    if a.cmd in ("call", "run"):
        if a.cmd == "run":  # `tool` holds the JS file path here
            args = {"code": Path(a.tool).read_text(encoding="utf-8"), "allowRemove": a.allow_remove}
            a.tool = "run_script"
        else:
            raw = Path(a.args[1:]).read_text(encoding="utf-8") if a.args.startswith("@") else a.args
            args = json.loads(raw)
        if a.file and a.tool != "list_files":
            args["fileKey"] = file_key(a.file)
        res = call(a.tool, args, a.timeout)
        for c in res.get("content", []) if isinstance(res, dict) else []:
            print(c.get("text") if c.get("type") == "text" else json.dumps({k: v for k, v in c.items() if k != "data"}))
        if not res.get("content"):
            print(json.dumps(res, ensure_ascii=False))
        return 1 if res.get("isError") or res.get("error") else 0
    e = engine()
    if a.cmd == "up":
        if (a.work or a.run_script is not None) and running(e):
            sh(e, "rm", "-f", NAME)  # settings changed: recreate
        up(a.work, a.run_script)
    elif a.cmd == "down":
        sh(e, "rm", "-f", NAME, check=False)
        print(f"{NAME} removed")
    elif a.cmd == "logs":
        subprocess.run([e, "logs", "--tail", "50", NAME])
    else:
        print(f"{NAME}: {'running' if running(e) else 'stopped'}; state {STATE.read_text() if STATE.exists() else '-'}")


if __name__ == "__main__":
    main()
