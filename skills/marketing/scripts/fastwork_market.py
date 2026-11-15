# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright==1.62.0"]
# ///
"""Measure a Fastwork category: what sellers charge, how fast they deliver, how many revisions.

Opens the public category page, follows up to --limit service pages one at a time with a pause
between them, and reads each service's declared package block (name, price, delivery days,
revisions). Stops at the first bot check; never logs in. Writes the raw sample as JSON and prints
the numbers a pricing decision needs: the cheapest-package median and quartiles, the per-tier
medians of three-package sellers, delivery days and revisions.

Run:  uv run fastwork_market.py https://fastwork.co/web-development --limit 40 --out sample.json
      uv run fastwork_market.py --selftest
"""
import argparse, json, re, statistics as st, sys, time
from collections import Counter

DAYS = re.compile(r"ระยะเวลาในการทำงาน\s*(\d+)\s*วัน(?:\s*จำนวนการปรับแก้ชิ้นงาน\s*(\S+)\s*ครั้ง)?")


def packages(txt):
    """The packages of one service page's text: the block after "แพ็กเกจ: N แพ็กเกจ", where each
    package is a name line, a ฿ price line, then the delivery / revisions line."""
    lines = [l.strip() for l in txt.splitlines()]
    i = next((k for k, l in enumerate(lines) if re.match(r"แพ็กเกจ:\s*\d+\s*แพ็กเกจ", l)), None)
    if i is None:
        return []
    n = int(re.search(r"\d+", lines[i]).group())
    out, k = [], i + 1
    while k < len(lines) and len(out) < n:
        m = re.fullmatch(r"฿([\d,]+)", lines[k])
        if m:
            name = next((lines[j] for j in range(k - 1, i, -1) if lines[j]), "")
            d = next((DAYS.search(lines[j]) for j in range(k + 1, min(k + 4, len(lines))) if DAYS.search(lines[j])), None)
            out.append({"name": name, "price": int(m.group(1).replace(",", "")),
                        "days": int(d.group(1)) if d else None, "revisions": d.group(2) if d and d.group(2) else None})
        k += 1
    return out


def stats(sample):
    with_pk = [s for s in sample if s["packages"]]
    entry = sorted(min(p["price"] for p in s["packages"]) for s in with_pk)
    three = [sorted(p["price"] for p in s["packages"]) for s in with_pk if len(s["packages"]) == 3]
    q = st.quantiles(entry, n=4) if len(entry) > 1 else [entry[0]] * 3
    days = [p["days"] for s in with_pk for p in s["packages"] if p["days"]]
    revs = Counter(p["revisions"] for s in with_pk for p in s["packages"] if p["revisions"])
    return {"services": len(sample), "with_packages": len(with_pk),
            "entry_median": st.median(entry), "entry_p25": q[0], "entry_p75": q[2],
            "three_package_sellers": len(three),
            "tier_medians": [st.median(t[i] for t in three) for i in range(3)] if three else [],
            "days_median": st.median(days) if days else None,
            "revisions_most_common": [r for r, _ in revs.most_common(3)]}


def selftest():
    page = ("ข้อความอื่น\nแพ็กเกจ: 2 แพ็กเกจ\nเริ่มต้น\n฿1,500\n ระยะเวลาในการทำงาน 5 วัน จำนวนการปรับแก้ชิ้นงาน 3 ครั้ง\n"
            "รายละเอียด\nแนะนำ\n฿2,900\n ระยะเวลาในการทำงาน 7 วัน จำนวนการปรับแก้ชิ้นงาน ไม่จำกัด ครั้ง\n฿9,999\n")
    p = packages(page)
    assert [x["price"] for x in p] == [1500, 2900] and p[1]["name"] == "แนะนำ" and p[0]["revisions"] == "3", p
    assert packages("no block here") == []
    s = stats([{"packages": p}, {"packages": [{"price": 4000, "days": 10, "revisions": "2"}]}])
    assert s["entry_median"] == 2750 and s["with_packages"] == 2, s
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("category", nargs="?")
    ap.add_argument("--limit", type=int, default=40)
    ap.add_argument("--pause", type=float, default=2.0, help="seconds between service pages")
    ap.add_argument("--out", default="sample.json")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    if not a.category:
        ap.error("give a category URL, or --selftest")
    from playwright.sync_api import sync_playwright
    slug = a.category.rstrip("/").rsplit("/", 1)[-1]
    sample = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1440, "height": 2000})
        pg.goto(a.category, wait_until="domcontentloaded", timeout=45000)
        pg.wait_for_timeout(6000)
        links = pg.eval_on_selector_all("a[href*='/user/']", f"els => [...new Set(els.map(e => e.href.split('?')[0]))]"
                                        f".filter(h => /{re.escape(slug)}-\\d+$/.test(h))")[:a.limit]
        for u in links:
            pg.goto(u, wait_until="domcontentloaded", timeout=45000)
            pg.wait_for_timeout(3500)
            txt = pg.inner_text("body")
            if "security verification" in txt.lower() or "verifying you are" in txt.lower():
                print(f"bot check at {u}: stopping, nothing past this point is read", file=sys.stderr)
                break
            title = pg.eval_on_selector("h1", "e => e.innerText").strip() if pg.query_selector("h1") else pg.title()
            sample.append({"url": u, "title": title, "packages": packages(txt)})
            time.sleep(a.pause)
        b.close()
    json.dump(sample, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(stats(sample), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
