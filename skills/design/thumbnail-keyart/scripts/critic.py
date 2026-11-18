# /// script
# requires-python = ">=3.10"
# dependencies = ["fonttools==4.65.0", "brotli==1.2.1"]
# ///
"""A fresh critic for a game thumbnail: a vision model that never saw the brief looks at the PNG and says
what the game is, what you do, what the goal is and every word it can read. Then the read is scored
against the brief (*.keyart.toon), so the check is one the author didn't run.

  read    every title, ribbon and callout string of this variant was read back (exact, case-folded)
  beats   a second, text-only call scores the blind read against the brief's is / loop / goal, 0-2 each:
          pass needs every beat >= 1 and a total >= 4 of 6
  focus   printed, not scored: where the model's eye landed. Calibrated on a published thumbnail (a painted
          dungeon-update key art): the model named its logo first in 3 of 3 runs, as it does any title, so
          "the title" is no evidence of a weak scene; judge focus by eye on the 400 px PNG
  runs    one sample is noise (the same image flipped between pass and fail), so it runs --runs times (default 3)
          and passes on a majority

Any OpenAI-compatible endpoint with an image-input model works. Defaults: Tokenme
(https://api.tokenme.limited/api/v1) with deepseek-ai/deepseek-v4.1-flash-1017; the key comes from
$KEYART_CRITIC_KEY or $TOKENME_API_KEY. Override with --base-url / --model (e.g. unsloth/qwen3.8-27b-nvfp4).

Run: uv run critic.py <brief.keyart.toon> <keyart-<variant>-...-400.png>   exit code = failures
     uv run critic.py <brief> <png> --dry-run     the two requests, image elided, nothing sent
     uv run critic.py --selftest
Judge the phone-width PNG (bench.py's -400.png): that is the size a player scrolls past.
"""
import argparse, base64, importlib.util, json, os, re, sys, urllib.error, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.environ.get("KEYART_CRITIC_URL", "https://api.tokenme.limited/api/v1")
MODEL = os.environ.get("KEYART_CRITIC_MODEL", "deepseek-ai/deepseek-v4.1-flash-1017")

BLIND = ("You are a player scrolling a game discovery page on a phone and this thumbnail goes past. "
         "Answer only with JSON: {\"game\": what kind of game this is, one sentence; \"action\": what you do in it; "
         "\"goal\": what you are trying to get or reach; \"text\": [every word or number you can read, exactly as "
         "written]; \"focus\": the first thing your eye lands on}. If you cannot tell, say so in that field.")
JUDGE = ("A game's brief and a player's first read of its thumbnail follow. For each beat score how well the read "
         "matches the brief: 2 = same idea, 1 = partly or vaguely, 0 = missing or wrong. Answer only with JSON: "
         "{\"is\": n, \"loop\": n, \"goal\": n, \"why\": one sentence}.")


def banner():
    """banner.py from the sibling sub-skill: its TOON reader and variant expansion, so the brief parses one way."""
    spec = importlib.util.spec_from_file_location("banner", os.path.join(HERE, "..", "..", "banner-design", "scripts", "banner.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def expected(brief_path, png_path):
    """The variant's spec (picked by the `keyart-<id>-` file name) and every string drawn on it."""
    b = banner()
    with open(inside_cwd(brief_path), encoding="utf-8") as fh:
        s = b.keyart_spec(b.load_toon(fh.read()))
    name = os.path.basename(png_path)
    jobs = [j for j in b.jobs(s) if name.startswith(j[3] + "-")] or b.jobs(s)[:1]
    ka = jobs[0][0]["keyart"]
    strings = list(ka["title"]) + ([ka["kicker"]] if ka.get("kicker") else [])
    strings += [x for c in ka["callouts"] for x in (c["text"], c.get("sub")) if x]
    return ka, strings


def inside_cwd(path):
    """`path` resolved, refused unless it lies inside the current directory: the arguments are often
    written by an agent, so they can never read elsewhere (the same guard as game-dev's mesh_check)."""
    base = os.path.realpath(os.getcwd())
    full = os.path.realpath(path)
    if full != base and not full.startswith(base + os.sep):
        raise SystemExit(f"{path}: outside the current directory ({base}); run from a folder that contains it")
    return full


fold = lambda x: re.sub(r"[^0-9a-z]", "", str(x).lower())


def score(strings, read, beats):
    """Failures for one critic pass: strings not read back, beats the read missed."""
    seen = fold(" ".join(map(str, read.get("text") or [])))
    fails = [f"not read: {x!r}" for x in strings if fold(x) not in seen]
    got = {k: int(beats.get(k, 0)) for k in ("is", "loop", "goal")}
    fails += [f"beat {k!r} scored 0: the thumbnail does not show it" for k, v in got.items() if v < 1]
    if sum(got.values()) < 4:
        fails.append(f"beats total {sum(got.values())}/6, under 4")
    return fails


def ask(messages, model, key):
    body = json.dumps({"model": model, "messages": messages, "temperature": 0}).encode()
    # a named client: Cloudflare-fronted gateways (Tokenme among them) refuse urllib's default signature, error 1010
    req = urllib.request.Request(f"{BASE}/chat/completions", body, {"Content-Type": "application/json",
                                 "Authorization": f"Bearer {key}", "User-Agent": "th3-skills-keyart-critic/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            text = json.load(r)["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        sys.exit(f"critic endpoint {e.code}: {e.read()[:200]!r} (NOT ASSESSED)")
    m = re.search(r"\{.*\}", text, re.S)                 # models wrap JSON in prose or fences
    assert m, f"no JSON in the critic's answer: {text[:200]!r}"
    return json.loads(m.group(0))


def selftest():
    os.chdir(os.path.join(HERE, ".."))       # the guard below admits paths inside the working directory only
    try:
        inside_cwd("/etc/hosts")
        raise AssertionError("a path outside the working directory must be refused")
    except SystemExit:
        pass
    strings = ["CRAGHOLD", "QUEST", "DUNGEON UPDATE", "KEY", "12,500 GOLD"]
    read = {"text": ["Craghold", "Quest", "Dungeon Update", "KEY", "12,500 GOLD"], "focus": "the glowing key in the gate"}
    assert score(strings, read, {"is": 2, "loop": 1, "goal": 2}) == []
    assert score(strings, dict(read, text=["CRAGHOLD", "QUEST"]), {"is": 2, "loop": 2, "goal": 2}) == \
        ["not read: 'DUNGEON UPDATE'", "not read: 'KEY'", "not read: '12,500 GOLD'"]
    assert score(strings, dict(read, focus="The large CRAGHOLD QUEST title."), {"is": 2, "loop": 2, "goal": 2}) == [], \
        "focus is reported, never a fail: the model names any logo first"
    f = score(strings, read, {"is": 2, "loop": 1, "goal": 0})
    assert f == ["beat 'goal' scored 0: the thumbnail does not show it", "beats total 3/6, under 4"], f
    brief = os.path.join("examples", "craghold", "craghold.keyart.toon")
    if os.path.exists(brief):
        ka, strings = expected(brief, "keyart-summit-craghold-1920x1080-400.png")
        assert strings == ["CRAGHOLD", "QUEST", "NEW SUMMIT", "SUMMIT", "4,200 M"], strings
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("brief", nargs="?")
    ap.add_argument("png", nargs="?")
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--runs", type=int, default=3, help="samples; the verdict is the majority (default 3)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest(); return 0
    if not (a.brief and a.png):
        ap.error("give a brief and a PNG, or --selftest")
    ka, strings = expected(a.brief, a.png)
    with open(inside_cwd(a.png), "rb") as fh:
        url = "data:image/png;base64," + base64.b64encode(fh.read()).decode()
    blind = [{"role": "user", "content": [{"type": "text", "text": BLIND}, {"type": "image_url", "image_url": {"url": url}}]}]
    if a.dry_run:
        print(json.dumps({"endpoint": f"{BASE}/chat/completions", "model": a.model,
                          "blind": BLIND, "image": f"{a.png} ({len(url)} chars, not shown)", "expected": strings,
                          "brief": {k: ka.get(k) for k in ("is", "loop", "goal")}}, indent=2, ensure_ascii=False))
        return 0
    key = os.environ.get("KEYART_CRITIC_KEY") or os.environ.get("TOKENME_API_KEY")
    if not key:
        sys.exit("no key: set $KEYART_CRITIC_KEY or $TOKENME_API_KEY (the critic is NOT ASSESSED without one)")
    brief = "\n".join(f"{k}: {ka.get(k)}" for k in ("is", "loop", "goal"))
    print(f"{os.path.basename(a.png)}  critic {a.model}  {a.runs} runs")
    passed = 0
    for n in range(1, a.runs + 1):
        read = ask(blind, a.model, key)
        seen = "\n".join(f"{k}: {read.get(k)}" for k in ("game", "action", "goal"))
        beats = ask([{"role": "user", "content": f"{JUDGE}\n\nBrief\n{brief}\n\nPlayer's read\n{seen}"}], a.model, key)
        fails = score(strings, read, beats)
        passed += not fails
        print(f" run {n}: {'pass' if not fails else 'FAIL'}  is {beats.get('is', 0)} loop {beats.get('loop', 0)} "
              f"goal {beats.get('goal', 0)}  focus: {read.get('focus')}")
        for k, kb in (("game", "is"), ("action", "loop"), ("goal", "goal")):
            print(f"    {kb:<5} read: {read.get(k)!s:.110}")
        for f in fails:
            print("    FAIL", f)
    ok = passed * 2 > a.runs
    print(f"critic: {passed}/{a.runs} runs pass,", "pass" if ok else "FAIL")
    return 0 if ok else a.runs - passed


if __name__ == "__main__":
    sys.exit(main())
