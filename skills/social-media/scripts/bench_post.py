#!/usr/bin/env python3
"""Check a written post against a benchmark case kept in TOON (benchmarks/*.toon).

The case holds the prompt (original and English), the facts the post may cite and a rubric table.
Each rubric id is a check below; an id with no check fails, so the case and the script stay in step.

  titles   the first ## section of the titles file has at least min_titles numbered options
  steps    the post has at least min_steps numbered steps (headings or list items)
  method   the post names every method_terms item
  hook     a hook_terms phrase sits after the last step and before the CTA link
  cta      the post links cta_url
  dashes   no em or en dash in prose (code spans and blocks are skipped)
  facts    every multi-digit or decimal number in the prose appears in the facts table
  length   the text a reader sees is at most max_chars characters (see shown())
  images   a cover before the first step, an image inside every step, and a closing image
           after the last step's own image

Run:  python3 bench_post.py <case.toon> <post.md> [--titles titles.md]   exit code = failures
      python3 bench_post.py --selftest
Stdlib only. Reads the TOON subset the cases use: scalars, `key[n]: a,b` inline lists and
`key[n]{cols}:` tables with one indented CSV row per line.
"""
import argparse, csv, re, sys
from pathlib import Path

HEAD = re.compile(r"^(\w[\w-]*)(?:\[(\d+)\])?(?:\{([^}]*)\})?:\s?(.*)$")


def scalar(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] == '"':
        return v[1:-1].replace('\\"', '"')
    return int(v) if re.fullmatch(r"-?\d+", v) else v


def row(line):
    return [scalar(f'"{c}"') if c else "" for c in next(csv.reader([line.strip()], skipinitialspace=True))]


def load_toon(text):
    out, lines, i = {}, text.splitlines(), 0
    while i < len(lines):
        line = lines[i]
        i += 1
        if not line.strip() or line.startswith(" "):
            continue
        m = HEAD.match(line)
        assert m, f"line {i}: not TOON: {line!r}"
        key, n, cols, rest = m.groups()
        if cols:                                   # table: n indented rows
            names = [c.strip() for c in cols.split(",")]
            rows = []
            while i < len(lines) and lines[i].startswith("  "):
                rows.append(dict(zip(names, row(lines[i]))))
                i += 1
            assert len(rows) == int(n), f"{key}: declared {n} rows, found {len(rows)}"
            out[key] = rows
        elif n is not None:                        # inline list
            items = row(rest) if rest else []
            assert len(items) == int(n), f"{key}: declared {n} items, found {len(items)}"
            out[key] = items
        else:
            out[key] = scalar(rest)
    return out


IMG = re.compile(r"!\[[^\]]*\]\([^)]*\)")


def prose(md):
    """The post without fenced blocks or inline code: what a reader reads as sentences."""
    md = re.sub(r"```.*?```", "", md, flags=re.S)
    md = IMG.sub("", md)                                   # file names are not claims
    md = re.sub(r"\]\([^)]*\)", "]", md)                    # nor are link targets
    return re.sub(r"`[^`]*`", "", md)


def shown(md):
    """The text a reader sees, as a blog editor counts it: no code fences, image lines, URLs or
    markdown marks, and every run of whitespace counts as one character."""
    md = re.sub(r"```.*?```", "", md, flags=re.S)
    md = IMG.sub("", md)
    md = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", md)          # links keep their text
    md = re.sub(r"^(#+|-|\*|>|---)\s*", "", md, flags=re.M)
    md = md.replace("`", "")
    return re.sub(r"\s+", " ", md).strip()


STEP = re.compile(r"^(?:#{2,4}\s*)?(?:ขั้นที่\s*)?\d+[.)]\s", re.M)


def check(case, post, titles=""):
    p = prose(post)
    facts = " ".join(f["text"] for f in case["facts"])
    steps = list(STEP.finditer(post))
    cta = post.find(case["cta_url"])
    results = {}
    for r in case["rubric"]:
        rid = r["id"]
        if rid == "titles":
            first = re.split(r"^## ", titles, flags=re.M)[1:2] or [titles]   # the titles list is the first ## section
            n = len(re.findall(r"^\d+[.)]\s", first[0], re.M))
            results[rid] = (n >= case["min_titles"], f"{n} title options")
        elif rid == "steps":
            results[rid] = (len(steps) >= case["min_steps"], f"{len(steps)} numbered steps")
        elif rid == "method":
            miss = [t for t in case["method_terms"] if t not in post]
            results[rid] = (not miss, f"missing {miss}" if miss else "all named")
        elif rid == "hook":
            after = steps[-1].end() if steps else 0
            hits = [h for h in case["hook_terms"] if after < post.find(h, after) < (cta if cta >= 0 else len(post))]
            results[rid] = (bool(hits), f"found {hits}" if hits else "no hook between the last step and the CTA")
        elif rid == "cta":
            results[rid] = (cta >= 0, "linked" if cta >= 0 else f"{case['cta_url']} missing")
        elif rid == "dashes":
            n = len(re.findall("[–—]", p))
            results[rid] = (n == 0, f"{n} dashes")
        elif rid == "facts":
            nums = {m for m in re.findall(r"\d+(?:[.,]\d+)*", p) if len(m) > 1}
            nums -= {m.group(0).strip(" .)#") for m in STEP.finditer(post)}
            bad = sorted(n for n in nums if n not in facts)
            results[rid] = (not bad, f"not in facts: {bad}" if bad else f"{len(nums)} numbers, all in facts")
        elif rid == "length":
            n = len(shown(post))
            results[rid] = (n <= case["max_chars"], f"{n} of {case['max_chars']} characters")
        elif rid == "images":
            imgs = [m.start() for m in IMG.finditer(post)]
            bounds = [m.start() for m in steps] + [len(post)]
            cover = bool(imgs) and bool(steps) and imgs[0] < steps[0].start()
            bare = [i + 1 for i in range(len(steps)) if not any(bounds[i] < x < bounds[i + 1] for x in imgs)]
            last_step_img = [x for x in imgs if steps and x > steps[-1].start()]
            closing = len(last_step_img) >= 2
            ok = cover and not bare and closing
            why = (f"{len(imgs)} images" if ok else
                   "; ".join(w for w, bad in [("no cover before step 1", not cover),
                                              (f"steps without an image: {bare}", bool(bare)),
                                              ("no closing image after the last step's image", not closing)] if bad))
            results[rid] = (ok, why)
        else:
            results[rid] = (False, "no check implements this rubric id")
    return results


def selftest():
    case = load_toon('id: t\ncta_url: "https://x.test/u"\nmin_titles: 2\nmin_steps: 2\n'
                     'method_terms[1]: tool.py\nhook_terms[1]: ถ้าอยาก\n'
                     'facts[1]{id,text}:\n  a,"size 1920 x 1080, contrast 4.5:1"\n'
                     'max_chars: 400\n'
                     'rubric[10]{id,check}:\n  titles,x\n  steps,x\n  method,x\n  hook,x\n  cta,x\n  dashes,x\n  facts,x\n  length,x\n  images,x\n  nope,x\n')
    assert case["facts"][0]["text"] == "size 1920 x 1080, contrast 4.5:1" and case["min_steps"] == 2
    good = ("![c](c.png)\n## 1. แรก\n![a](a.png)\nใช้ tool.py ที่ 1920 px\n## 2. สอง\n![b](b.png)\n4.5 พอ\n"
            "![end](e.png)\n\nถ้าอยากได้แบบนี้ [จ้างผม](https://x.test/u)\n`code — 999`\n")
    r = check(case, good, "# T\n## Titles\n1. a\n2. b\n## Hooks\n1. h\n")
    assert check(case, good, "## Titles\n1. a\n## Hooks\n1. h\n2. h\n")["titles"][1] == "1 title options"
    assert all(ok for k, (ok, _) in r.items() if k != "nope"), r
    assert not r["nope"][0], "an unknown rubric id must fail"
    bad = check(case, "## 1. แรก — 777\n[x](https://x.test/u)\nถ้าอยาก\n", "1. a\n")
    assert not bad["titles"][0] and not bad["steps"][0] and not bad["dashes"][0] and not bad["method"][0]
    assert bad["facts"][1] == "not in facts: ['777']", bad["facts"]
    assert not bad["images"][0] and "no cover" in bad["images"][1]
    assert shown("# T\n![x](y.png)\n[link](https://u)  a\n\n`c`") == "T link a c"
    long = dict(case, max_chars=5)
    assert not check(long, good, "")["length"][0]
    assert not bad["hook"][0], "hook before the last step does not count"
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("case", nargs="?")
    ap.add_argument("post", nargs="?")
    ap.add_argument("--titles", help="the titles file the titles check counts")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    if not (a.case and a.post):
        ap.error("give a case and a post, or --selftest")
    case = load_toon(Path(a.case).read_text(encoding="utf-8"))
    titles = Path(a.titles).read_text(encoding="utf-8") if a.titles else ""
    res = check(case, Path(a.post).read_text(encoding="utf-8"), titles)
    for rid, (ok, why) in res.items():
        print(f"{'PASS' if ok else 'FAIL'}  {rid:7} {why}")
    fails = sum(not ok for ok, _ in res.values())
    print(f"{case['id']}: {len(res) - fails}/{len(res)} pass")
    return fails


if __name__ == "__main__":
    sys.exit(main())
