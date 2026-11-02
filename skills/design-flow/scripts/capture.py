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

import argparse, base64, functools, hashlib, http.server, json, os, re, shutil, subprocess, sys, tempfile, threading
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


def inside_work(p, what="path"):
    """CLI paths come from an agent, so this script only reads and writes inside the folder it runs from."""
    root = os.path.realpath(os.getcwd())
    full = os.path.realpath(os.path.join(root, os.path.expanduser(p)))
    if os.path.commonpath([root, full]) == root:
        return full
    raise ValueError(f"{what} {p!r} is outside the working folder {root}; run the script from that folder")


def html_figma_bundle():
    """Browser IIFE of html-figma (global htmlFigma.htmlToFigma), built once with npm + esbuild."""
    out = CACHE / f"{HTML_FIGMA.replace('@', '-')}.js"
    if out.exists():
        return patch_bundle(out.read_text(encoding="utf-8"))
    if not shutil.which("npx") or not shutil.which("npm"):
        sys.exit("--to layers needs node (npm, npx) once to bundle html-figma; install node or use --to figma")
    CACHE.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        run = functools.partial(subprocess.run, cwd=tmp, check=True, capture_output=True, text=True)
        run(["npm", "init", "-y"])
        run(["npm", "i", "--ignore-scripts", "--no-audit", "--no-fund", HTML_FIGMA])
        run(["npx", "-y", "esbuild@0.24.0", "node_modules/html-figma/browser/index.js", "--bundle",
             "--format=iife", "--global-name=htmlFigma", "--platform=browser", f"--outfile={out}"])
    return patch_bundle(out.read_text(encoding="utf-8"))


# Patches to html-figma 0.3.1, applied to the bundle as text (each hook must exist, else the upgrade broke it):
#  - it keeps a text's family and size but not its weight, so every bold label imports as Regular; the bridge
#    plugin already maps a numeric fontWeight to Bold/SemiBold/Medium.
#  - it names every layer "Frame", but ui-samples / swap find components by layer name ("Button", "Badge",
#    "Input"…). Name each frame from the DOM: data-figma-name, then common framework class words, role, tag.
#  - it drops any element under 1px together with its whole subtree, so a fixed sidebar inside a 0px-high
#    wrapper (common in app shells) vanishes. Keep such an element when it has children, as a 1px frame.
LAYER_NAMER = r"""
  var __layerName = (el) => {
    if (el.dataset && el.dataset.figmaName) return el.dataset.figmaName;
    const cls = typeof el.className === "string" ? el.className : "";
    const words = [[/(^|\s)\S*-control(\s|$)/, "Select"], [/flatpickr-input/, "Date Input"], [/(^|\s)(badge|status|chip|pill)(\s|-|$)/, "Badge"],
      [/(^|\s)btn(\s|-|$)/, "Button"], [/(^|\s)nav-link(\s|$)/, "Nav Link"], [/(^|\s)(panel|card)(\s|$)/, "Panel"],
      [/breadcrumb/, "Breadcrumbs"], [/(^|\s)pagination(\s|$)/, "Pagination"], [/(^|\s)form-(input|control)(\s|$)/, "Input"],
      [/(^|\s)form-select(\s|$)/, "Select"], [/(^|\s)form-textarea(\s|$)/, "Textarea"], [/(^|\s)form-checkbox(\s|$)/, "Checkbox"],
      [/(^|\s)(modal|dialog)(\s|-|$)/, "Dialog"]];
    for (const [rx, name] of words) if (rx.test(cls)) return name;
    const role = el.getAttribute && el.getAttribute("role");
    const roles = { dialog: "Dialog", button: "Button", tab: "Tab", tablist: "Tabs", checkbox: "Checkbox", radio: "Radio", switch: "Switch" };
    if (role && roles[role]) return roles[role];
    const type = (el.getAttribute && el.getAttribute("type")) || "";
    const tags = { BUTTON: "Button", A: "Link", TEXTAREA: "Textarea", SELECT: "Select", TABLE: "Table", THEAD: "Table Head",
      TBODY: "Table Body", TR: "Table Row", TH: "Table Header Cell", TD: "Table Cell", NAV: "Nav", HEADER: "Header",
      FOOTER: "Footer", UL: "List", OL: "List", LI: "List Item", IMG: "Image", LABEL: "Label", FORM: "Form",
      H1: "Heading", H2: "Heading", H3: "Heading", H4: "Heading", H5: "Heading", H6: "Heading",
      INPUT: type === "checkbox" ? "Checkbox" : type === "radio" ? "Radio" : "Input" };
    return tags[el.tagName] || "Frame";
  };
  var elementToFigma = (el, pseudo) => {"""

BUNDLE_PATCHES = [
    ("  var elementToFigma = (el, pseudo) => {", LAYER_NAMER),
    ('    const rectNode = {\n      type: "FRAME",\n      ref: el,', '    const rectNode = {\n      type: "FRAME",\n      name: __layerName(el),\n      ref: el,'),
    ("textNode.fontFamily = computedStyles.fontFamily;",
     "textNode.fontFamily = computedStyles.fontFamily; textNode.fontWeight = parseInt(computedStyles.fontWeight, 10) || 400;"),
    ("if (rect.width < 1 || rect.height < 1) {\n      return;",
     "if ((rect.width < 1 || rect.height < 1) && !el.children.length) {\n      return;"),
    ("      width: Math.round(rect.width),\n      height: Math.round(rect.height),\n      clipsContent: !!overflowHidden,",
     "      width: Math.max(1, Math.round(rect.width)),\n      height: Math.max(1, Math.round(rect.height)),\n      clipsContent: !!overflowHidden && rect.width >= 1 && rect.height >= 1,"),
]


def patch_bundle(bundle):
    for hook, new in BUNDLE_PATCHES:
        if hook not in bundle:
            sys.exit(f"html-figma bundle changed: patch hook not found ({hook[:40]}...), check {HTML_FIGMA}")
        bundle = bundle.replace(hook, new, 1)
    return bundle


# next/font serves a family as `__Prompt_a1b2c3, __Prompt_Fallback_a1b2c3`: no installed font has that name,
# so the plugin falls back to Roboto. Map the hashed names back to the real family and drop the metric fallback.
NEXT_FONT = re.compile(r"^__(.+?)_[0-9a-f]{6}$")


def real_families(families):
    out = []
    for f in (x.strip().strip("'\"") for x in families.split(",")):
        m = NEXT_FONT.match(f)
        f = m.group(1).replace("_", " ") if m else f
        if f and not f.endswith(" Fallback") and f not in out:
            out.append(f)
    return ", ".join(out)


SVG_COLOR = re.compile(r'style="[^"]*?(?<![-\w])color:\s*([^;"]+)')


def fix_svg(svg):
    """html-figma 0.3.1 writes `style="…"fill="…">>` and leaves currentColor unresolved; repair both."""
    svg = re.sub(r'"(?=[a-zA-Z-]+=")', '" ', svg).replace('>>', '>', 1)
    m = SVG_COLOR.search(svg)
    return svg.replace("currentColor", m.group(1).strip()) if m else svg


def is_one_line(text):
    lh = (text.get("lineHeight") or {}).get("value") or (text.get("fontSize") or 0) * 1.2
    return bool(lh) and text.get("height", 0) < lh * 1.5 and "\n" not in text.get("characters", "")


def fix_layers(node):
    if isinstance(node, dict):
        if isinstance(node.get("svg"), str):
            node["svg"] = fix_svg(node["svg"])
        if isinstance(node.get("fontFamily"), str):
            node["fontFamily"] = real_families(node["fontFamily"])
        if node.get("type") == "TEXT" and is_one_line(node) and node.get("textAlignHorizontal", "LEFT") == "LEFT":
            # Figma's metrics run a little wider than Chrome's, so a fixed-width one-line label wraps in Figma, and
            # in Thai the break can land inside a cluster (tofu). Let it size to its text; left edge stays put.
            node["textAutoResize"] = "WIDTH_AND_HEIGHT"
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


# html-figma ignores CSS transforms, so a chevron rotated to point left imports pointing down. Bake a pure
# rotation/flip on the svg or on an icon-only wrapper (no text) into the svg as a <g transform> about its centre.
BAKE_ROTATIONS = r"""() => { let n = 0;
  for (const svg of document.querySelectorAll('svg')) {
    if (svg.parentElement && svg.parentElement.closest('svg')) continue;
    let m = new DOMMatrix(), e = svg, hops = [];
    for (let d = 0; e && d < 4; d++, e = e.parentElement) {
      if (d > 0 && e.textContent.trim()) break;
      const t = getComputedStyle(e).transform;
      if (t === 'none') continue;
      const k = new DOMMatrix(t);
      if (Math.abs(k.e) > 0.01 || Math.abs(k.f) > 0.01) break;
      m = k.multiply(m); hops.push(e);
    }
    if (!hops.length) continue;
    const vb = svg.viewBox && svg.viewBox.baseVal && svg.viewBox.baseVal.width ? svg.viewBox.baseVal
      : { x: 0, y: 0, width: svg.width.baseVal.value, height: svg.height.baseVal.value };
    const cx = vb.x + vb.width / 2, cy = vb.y + vb.height / 2;
    const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    g.setAttribute('transform', `translate(${cx} ${cy}) matrix(${m.a} ${m.b} ${m.c} ${m.d} 0 0) translate(${-cx} ${-cy})`);
    while (svg.firstChild) g.appendChild(svg.firstChild);
    svg.appendChild(g);
    for (const h of hops) h.style.transform = 'none';
    n++;
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
        # Figma's createImage takes PNG/JPEG/GIF only: an <img src="*.svg"> becomes an SVG layer instead
        svgs = [f for f in node.get("fills") or [] if isinstance(f, dict) and f.get("type") == "IMAGE"
                and str(f.get("url", "")).startswith("data:image/svg+xml;base64,")]
        for f in svgs:
            node["fills"].remove(f)
            svg = base64.b64decode(f["url"].split(",", 1)[1]).decode("utf-8", "replace")
            node.setdefault("children", []).insert(0, {"type": "SVG", "svg": svg[svg.find("<svg"):], "x": 0, "y": 0,
                                                       "width": node.get("width", 0), "height": node.get("height", 0)})
        for c in node.get("children") or []:
            inline_images(c, fetch, cache)
    return node


def image_entry(fill):
    """(key, {b64, scaleMode}) for a raster data-URI IMAGE fill, else None."""
    url = fill.get("url", "") if isinstance(fill, dict) and fill.get("type") == "IMAGE" else ""
    m = re.match(r"data:image/(png|jpe?g|gif);base64,(.+)", url, re.S)
    if not m:
        return None
    return hashlib.sha1(m.group(2).encode()).hexdigest()[:12], {"b64": m.group(2), "scaleMode": fill.get("scaleMode") or "FILL"}


def split_images(node, images):
    """The bridge plugin only turns an IMAGE fill into pixels when it carries a Uint8Array, which JSON can't hold:
    a data-URI fill imports as an empty frame. Move each raster image to `images` (key -> base64), tag the layer
    with data.image = key (the importer keeps `data` as shared plugin data), and let `figma_js.py images` fill it."""
    if not isinstance(node, dict):
        return node
    keep = []
    for f in node.get("fills") or []:
        hit = image_entry(f)
        if hit is None:
            keep.append(f)
            continue
        images[hit[0]] = hit[1]
        node["data"] = {**(node.get("data") or {}), "image": hit[0]}
    if "fills" in node:
        node["fills"] = keep
    for c in node.get("children") or []:
        split_images(c, images)
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
                        row["rotations"] = page.evaluate(BAKE_ROTATIONS)
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
                        images = {}
                        layers = split_images(fix_layers(layers), images)
                        path.write_text(json.dumps(layers, ensure_ascii=False), encoding="utf-8")
                        row["layers"] = str(path)
                        if images:
                            img_path = path.with_suffix(".images.json")
                            img_path.write_text(json.dumps(images), encoding="utf-8")
                            row["images"] = str(img_path)  # after import: figma_js.py images --root <frame> --images this
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
        return json.loads(Path(inside_work(a.targets[0], "jobs file")).read_text(encoding="utf-8"))
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
    assert real_families("__Prompt_a1b2c3, __Prompt_Fallback_a1b2c3") == "Prompt"
    assert real_families("__IBM_Plex_Sans_Thai_a1b2c3, Arial, sans-serif") == "IBM Plex Sans Thai, Arial, sans-serif"
    svg_node = inline_images({"width": 4, "height": 4, "fills": [{"type": "IMAGE", "url": "data:image/svg+xml;base64,"
                              + base64.b64encode(b'<?xml version="1.0"?><svg/>').decode()}]}, None, {})
    assert svg_node["fills"] == [] and svg_node["children"][0] == {"type": "SVG", "svg": "<svg/>", "x": 0, "y": 0, "width": 4, "height": 4}
    one = fix_layers({"type": "TEXT", "characters": "บริษัท", "height": 20, "lineHeight": {"value": 20}})
    two = fix_layers({"type": "TEXT", "characters": "a b", "height": 40, "lineHeight": {"value": 20}})
    right = fix_layers({"type": "TEXT", "characters": "21.40", "height": 20, "fontSize": 14, "textAlignHorizontal": "RIGHT"})
    assert one["textAutoResize"] == "WIDTH_AND_HEIGHT" and "textAutoResize" not in two and "textAutoResize" not in right
    imgs = {}
    tagged = split_images({"fills": [{"type": "IMAGE", "url": "data:image/png;base64,QUJD", "scaleMode": "FIT"},
                                     {"type": "SOLID"}]}, imgs)
    assert tagged["fills"] == [{"type": "SOLID"}] and imgs[tagged["data"]["image"]] == {"b64": "QUJD", "scaleMode": "FIT"}
    patched = patch_bundle(" ".join(h for h, _ in BUNDLE_PATCHES))
    assert "__layerName(el)" in patched and "fontWeight = parseInt" in patched and "!el.children.length" in patched and "Math.max(1" in patched
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
    assert inside_work("captures") == os.path.join(os.path.realpath(os.getcwd()), "captures")
    for bad in ("../outside.json", "/etc/hosts"):
        try:
            inside_work(bad)
        except ValueError:
            continue
        raise AssertionError(f"{bad} accepted")
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
    if a.out:
        a.out = inside_work(a.out, "--out")
    capture(build_jobs(a), a.to, a.out, a.viewport, a.selector, a.wait, a.allow_writes, a.headed, a.allow_post)


if __name__ == "__main__":
    try:
        main()
    except ValueError as exc:  # a path outside the working folder: a clear message, not a traceback
        sys.exit(f"error: {exc}")
