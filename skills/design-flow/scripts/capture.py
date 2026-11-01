# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright>=1.47"]
# ///
"""Capture web pages or local HTML into Figma as editable layers. Two backends:

  --to figma   Figma's html-to-design capture.js (auto layout, binds variables). Needs one
               single-use capture id per page from the official Figma MCP `generate_figma_design`,
               which counts against the Figma MCP plan limit.
  --to layers  html-figma JSON written to --out DIR, imported with the figma-mcp-bridge tool
               `import_html_layers` (no Figma API/MCP quota; absolute layout, run autolayout after).
               Needs node/npx once to bundle html-figma (cached in ~/.cache/design-flow).

  login  --url https://app.example.com/login --state ~/.cache/figma-capture/app.json
         headed Chrome; you sign in, the session is saved (never printed)
  url    [--state FILE] (--capture ID ... | --to layers --out DIR) URL [URL ...]
  html   (--capture ID | --to layers --out DIR) path/to/page.html|dir/   served on 127.0.0.1
  jobs   jobs.json   [{"url", "captureId"?, "state"?, "name"?, "steps"?, "selector"?}]  (--to/--out apply to all)
         steps put the page in a state first (e.g. a dialog open) for UI → flow → UI targets;
         selector captures one element only (e.g. the dialog) to overlay on a copy of the screen
  --self-test

Options: --viewport 1920x1080  --selector body  --wait 2500  --allow-writes  --allow-post REGEX  --headed
Every non-GET request to the target host is aborted unless --allow-writes (read-only browsing);
only mcp.figma.com may POST (the capture submit). CSP is stripped from documents so injected
scripts run.
"""
from __future__ import annotations

import argparse, base64, functools, http.server, json, os, re, shutil, subprocess, sys, tempfile, threading
from pathlib import Path
from urllib.parse import urlsplit

FIGMA = "mcp.figma.com"
CAPTURE_JS = f"https://{FIGMA}/mcp/html-to-design/capture.js"
HTML_FIGMA = "html-figma@0.3.1"
CACHE = Path.home() / ".cache" / "design-flow"
DROP = ("content-security-policy", "content-security-policy-report-only", "content-length",
        "content-encoding", "transfer-encoding")
SUBMIT = """(c) => Promise.race([
  window.figma.captureForDesign({captureId: c, selector: SEL,
    endpoint: `https://mcp.figma.com/mcp/capture/${c}/submit?bindVariables=true`}).then(() => 'submitted'),
  new Promise(r => setTimeout(() => r('timeout-60s'), 60000))])"""  # the promise often never settles; the submit still lands


def html_figma_bundle():
    """Browser IIFE of html-figma (global htmlFigma.htmlToFigma), built once with npm + esbuild."""
    out = CACHE / f"{HTML_FIGMA.replace('@', '-')}.js"
    if out.exists():
        return out.read_text(encoding="utf-8")
    if not shutil.which("npx") or not shutil.which("npm"):
        sys.exit("--to layers needs node (npm, npx) once to bundle html-figma; install node or use --to figma")
    CACHE.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        run = functools.partial(subprocess.run, cwd=tmp, check=True, capture_output=True, text=True)
        run(["npm", "init", "-y"])
        run(["npm", "i", "--ignore-scripts", "--no-audit", "--no-fund", HTML_FIGMA])
        run(["npx", "-y", "esbuild@0.24.0", "node_modules/html-figma/browser/index.js", "--bundle",
             "--format=iife", "--global-name=htmlFigma", "--platform=browser", f"--outfile={out}"])
    return out.read_text(encoding="utf-8")


SVG_COLOR = re.compile(r'style="[^"]*?(?<![-\w])color:\s*([^;"]+)')


def fix_svg(svg):
    """html-figma 0.3.1 writes `style="…"fill="…">>` and leaves currentColor unresolved; repair both."""
    svg = re.sub(r'"(?=[a-zA-Z-]+=")', '" ', svg).replace('>>', '>', 1)
    m = SVG_COLOR.search(svg)
    return svg.replace("currentColor", m.group(1).strip()) if m else svg


def fix_layers(node):
    if isinstance(node, dict):
        if isinstance(node.get("svg"), str):
            node["svg"] = fix_svg(node["svg"])
        for c in node.get("children") or []:
            fix_layers(c)
    return node


# html-figma drops CSS gradients; give such elements a solid fill (first color stop) in our copy of the page
FLATTEN_GRADIENTS = r"""() => { let n = 0;
  for (const el of document.querySelectorAll('*')) {
    const cs = getComputedStyle(el);
    if (!cs.backgroundImage.includes('gradient')) continue;
    const bg = cs.backgroundColor;
    if (bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent') continue;
    const m = cs.backgroundImage.match(/rgba?\([^)]+\)|#[0-9a-fA-F]{3,8}/);
    if (m) { el.style.backgroundImage = 'none'; el.style.backgroundColor = m[0]; n++; }
  }
  return n; }"""


def inline_images(node, fetch, cache):
    """IMAGE fills keep a remote url the Figma plugin can't fetch; embed them as data URIs."""
    if isinstance(node, dict):
        for f in node.get("fills") or []:
            url = f.get("url") if isinstance(f, dict) and f.get("type") == "IMAGE" else None
            if url and not url.startswith("data:"):
                if url not in cache:
                    cache[url] = fetch(url)
                if cache[url]:
                    f["url"] = cache[url]
        for c in node.get("children") or []:
            inline_images(c, fetch, cache)
    return node


def run_steps(page, steps):
    """Bring the page into a state before capture: a dialog open, a tab selected, a field filled.
    Steps: {"click": "<selector or text=…>"} · {"fill": ["<selector>", "value"]} · {"press": "Escape"} · {"wait": ms}.
    Writes stay blocked by the router, so a step that would save something only shows the client-side result."""
    for st in steps:
        if "click" in st:
            page.locator(st["click"]).first.click(timeout=15_000)
        elif "fill" in st:
            page.locator(st["fill"][0]).first.fill(st["fill"][1], timeout=15_000)
        elif "press" in st:
            page.keyboard.press(st["press"])
        page.wait_for_timeout(int(st.get("wait", 1200)))


def router(hosts, allow_writes, blocked, allow_post=None):
    """Read-only browsing: block non-GET to the target host, except POSTs that only read (allow_post regex on the
    path), e.g. report endpoints that fetch rows by POST to keep long filters out of the URL."""
    def handle(route, request):
        host = urlsplit(request.url).netloc
        if host == FIGMA:
            return route.continue_()
        if request.resource_type == "document" and request.method == "GET" and host in hosts:
            resp = route.fetch()
            return route.fulfill(response=resp, headers={k: v for k, v in resp.headers.items() if k.lower() not in DROP})
        if allow_post and request.method == "POST" and allow_post.search(urlsplit(request.url).path):
            return route.continue_()
        if not allow_writes and host in hosts and request.method not in ("GET", "HEAD", "OPTIONS"):
            blocked.append(f"{request.method} {urlsplit(request.url).path}")
            return route.abort()
        return route.continue_()
    return handle


def slug(text):
    return re.sub(r"[^\w-]+", "-", text, flags=re.UNICODE).strip("-")[:80] or "page"


def capture(jobs, to, out_dir, viewport, selector, wait, allow_writes, headed, allow_post=None):
    from playwright.sync_api import sync_playwright
    w, h = map(int, viewport.lower().split("x"))
    script = html_figma_bundle() if to == "layers" else None
    if out_dir:
        Path(out_dir).mkdir(parents=True, exist_ok=True)
    results = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome", headless=not headed)
        groups = {}
        for j in jobs:
            groups.setdefault(j.get("state"), []).append(j)
        for state, group in groups.items():
            ctx = browser.new_context(viewport={"width": w, "height": h}, storage_state=state)
            blocked = []
            ctx.route("**/*", router({urlsplit(j["url"]).netloc for j in group}, allow_writes, blocked, re.compile(allow_post) if allow_post else None))
            if to == "figma":
                script = script or ctx.request.get(CAPTURE_JS).text()
            page = ctx.new_page()
            for j in group:
                try:
                    page.goto(j["url"], wait_until="domcontentloaded", timeout=60_000)
                    try:
                        page.wait_for_load_state("networkidle", timeout=30_000)
                    except Exception:
                        pass  # long-polling apps never go idle
                    page.wait_for_timeout(wait)
                    run_steps(page, j.get("steps") or [])
                    page.add_script_tag(content=script)
                    row = {"url": j["url"], "landed": page.url, "title": page.title()}
                    if to == "figma":
                        page.wait_for_timeout(500)
                        row["captureId"] = j["captureId"]
                        row["result"] = page.evaluate(SUBMIT.replace("SEL", json.dumps(j.get("selector") or selector)), j["captureId"])
                    else:
                        row["flattened"] = page.evaluate(FLATTEN_GRADIENTS)
                        sel = j.get("selector") or selector
                        layers = page.evaluate("(sel) => htmlFigma.htmlToFigma(document.querySelector(sel))", sel)

                        def fetch(url, req=ctx.request):
                            try:
                                r = req.get(url, timeout=20_000)
                                if not r.ok:
                                    return None
                                mime = (r.headers.get("content-type") or "image/png").split(";")[0]
                                return f"data:{mime};base64," + base64.b64encode(r.body()).decode()
                            except Exception:
                                return None
                        layers = inline_images(layers, fetch, {})
                        path = Path(out_dir) / f"{slug(j.get('name') or urlsplit(page.url).path)}.json"
                        path.write_text(json.dumps(fix_layers(layers), ensure_ascii=False), encoding="utf-8")
                        row["layers"] = str(path)
                    results.append(row)
                    print(json.dumps(row, ensure_ascii=False), flush=True)
                except Exception as exc:  # one bad step or selector must not stop the rest of the batch
                    row = {"url": j["url"], "name": j.get("name"), "error": str(exc).splitlines()[0][:300]}
                    results.append(row)
                    print(json.dumps(row, ensure_ascii=False), flush=True)
            if blocked:
                print(json.dumps({"blocked_writes": blocked[:30]}), flush=True)
            ctx.close()
        browser.close()
    return results


def login(url, state):
    from playwright.sync_api import sync_playwright
    path = Path(state).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome", headless=False)
        ctx = browser.new_context()
        page = ctx.new_page()
        page.goto(url)
        print("Sign in in the Chrome window. Waiting up to 10 minutes.", flush=True)
        page.wait_for_url(lambda u: u.rstrip("/") != url.rstrip("/"), timeout=600_000)
        page.wait_for_load_state("networkidle")
        ctx.storage_state(path=str(path))
        os.chmod(path, 0o600)
        print(f"saved {path}")
        browser.close()


def serve(target):
    p = Path(target).resolve()
    root, name = (p, "") if p.is_dir() else (p.parent, p.name)
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(root))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)  # route.fetch needs a 2nd connection
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, f"http://127.0.0.1:{httpd.server_address[1]}/{name}"


def build_jobs(a):
    if a.cmd == "jobs":
        return json.loads(Path(a.targets[0]).read_text(encoding="utf-8"))
    urls = a.targets
    if a.cmd == "html":
        if len(a.targets) != 1:
            sys.exit("html takes one file or directory per run")
        urls = [serve(a.targets[0])[1]]
    if a.to == "figma" and len(a.capture) != len(urls):
        sys.exit("--to figma needs exactly one --capture id per page (ids are single-use)")
    return [{"url": u, "captureId": (a.capture[i] if a.to == "figma" else None), "state": a.state} for i, u in enumerate(urls)]


def self_test():
    assert slug("/a/reports/daily") == "a-reports-daily" and slug("///") == "page"
    t = inline_images({"fills": [{"type": "IMAGE", "url": "https://x/a.png"}], "children": [{"fills": [{"type": "IMAGE", "url": "https://x/a.png"}]}]},
                      lambda u: "data:image/png;base64,QQ==", {})
    assert t["fills"][0]["url"].startswith("data:") and t["children"][0]["fills"][0]["url"].startswith("data:")
    bad = '<svg style="color: rgb(1, 2, 3);"fill="rgb(0, 0, 0)">><path stroke="currentColor"/></svg>'
    good = fix_svg(bad)
    assert '" fill=' in good and ">>" not in good and 'stroke="rgb(1, 2, 3)"' in good, good
    blocked, calls = [], []

    class R:  # minimal stand-ins for Playwright Route/Request
        def __init__(s, url, method="GET", rtype="xhr"): s.url, s.method, s.resource_type = url, method, rtype
        def continue_(s): calls.append("continue")
        def abort(s): calls.append("abort")
    h = router({"app.test"}, False, blocked, re.compile(r"/report/[^/]+/data$"))
    req = R("https://app.test/api/report/x/data", "POST"); h(req, req)   # read-only POST allowed
    calls.clear()
    for url, m in [("https://app.test/api/x", "POST"), ("https://mcp.figma.com/x", "POST"), ("https://cdn.test/a.js", "GET")]:
        req = R(url, m); h(req, req)
    assert calls == ["abort", "continue", "continue"] and blocked == ["POST /api/x"], (calls, blocked)
    print("self-test ok")


def main():
    if "--self-test" in sys.argv:
        return self_test()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["login", "url", "html", "jobs"])
    ap.add_argument("targets", nargs="*")
    ap.add_argument("--url")
    ap.add_argument("--state", help="Playwright storage-state file for a signed-in session")
    ap.add_argument("--to", choices=["figma", "layers"], default="figma")
    ap.add_argument("--out", help="--to layers: directory for the html-figma JSON (inside the bridge's working dir)")
    ap.add_argument("--capture", action="append", default=[], help="--to figma: capture id, one per page, in order")
    ap.add_argument("--viewport", default="1920x1080")
    ap.add_argument("--selector", default="body")
    ap.add_argument("--wait", type=int, default=2500, help="ms to let the page settle before capture")
    ap.add_argument("--allow-writes", action="store_true", help="let the page POST/PUT/DELETE to its own host")
    ap.add_argument("--allow-post", help="regex of POST paths that only read (e.g. report data endpoints) to let through")
    ap.add_argument("--headed", action="store_true")
    a = ap.parse_args()
    if a.cmd == "login":
        return login(a.url, a.state)
    if a.to == "layers" and not a.out:
        sys.exit("--to layers needs --out DIR")
    capture(build_jobs(a), a.to, a.out, a.viewport, a.selector, a.wait, a.allow_writes, a.headed, a.allow_post)


if __name__ == "__main__":
    main()
