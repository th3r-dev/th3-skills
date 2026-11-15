#!/usr/bin/env python3
"""Price a service from its costs, and check a marketplace listing against the offer.

An offer lives in a TOON file (see ../examples/th3r-web-service/offer.toon): the platform fee,
working hours, monthly costs (each with its source), the target income, the packages with their
estimated hours, and the rules the listing must follow.

  price  cost per hour at break-even and at target, the listed price per hour after the platform
         fee, and for each package: net after the fee, the hours it pays for, and a verdict
         (LOSS if its estimated hours exceed what the price covers at break-even, UNDER TARGET if
         they exceed what it covers at the target rate)
  check  reads the listing (Markdown in the platform's field layout, see ../listing/references/
         listing.md) and checks: field lengths, units the platform offers, no forbidden symbols,
         no tech-stack terms, package names / prices / units match the offer, and every
         multi-digit number in the pasted text appears in the offer

Run:  python3 offer.py price <offer.toon>
      python3 offer.py check <offer.toon> <listing.md>        exit code = failures
      python3 offer.py --selftest
Stdlib only.
"""
import argparse, csv, re, sys
from pathlib import Path

# ---- the TOON subset (same reader as social-media/scripts/bench_post.py; skills install separately)
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
        if cols:
            names = [c.strip() for c in cols.split(",")]
            rows = []
            while i < len(lines) and lines[i].startswith("  "):
                rows.append(dict(zip(names, row(lines[i]))))
                i += 1
            assert len(rows) == int(n), f"{key}: declared {n} rows, found {len(rows)}"
            out[key] = rows
        elif n is not None:
            items = row(rest) if rest else []
            assert len(items) == int(n), f"{key}: declared {n} items, found {len(items)}"
            out[key] = items
        else:
            out[key] = scalar(rest)
    return out


num = lambda v: float(str(v).replace(",", ""))
# a number as people write it: 1,090 or 26,900 or 4.5; a comma is a thousands separator only before 3 digits
NUM = re.compile(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?")


# ---- price

def rates(o):
    """THB per working hour: (break-even, target), net of the fee; and the hours in a month."""
    hours = num(o["days_per_month"]) * num(o["hours_per_day"])
    costs = sum(num(c["thb_month"]) for c in o["costs"])
    business = sum(num(c["thb_month"]) for c in o["costs"] if c["kind"] == "business")
    return costs / hours, (num(o["target_income"]) + business) / hours, hours


def price(o):
    floor, target, hours = rates(o)
    fee = num(o["fee"])
    lines = [f"hours/month {hours:.0f}  fee {fee:.0%}",
             f"break-even {floor:.1f} THB/h net, list at >= {floor / (1 - fee):.1f}",
             f"target     {target:.1f} THB/h net, list at {target / (1 - fee):.1f}", ""]
    verdicts = []
    for p in o["packages"]:
        net = num(p["price"]) * (1 - fee)
        est = num(p["hours"])
        cover_t, cover_f = net / target, net / floor
        v = "LOSS" if est > cover_f else "UNDER TARGET" if est > cover_t else "ok"
        verdicts.append(v)
        lines.append(f"{p['name']:<40} {num(p['price']):>8,.0f} {p['unit']:<8} net {net:>8,.0f}  "
                     f"est {est:>5.1f} h  pays {cover_t:>5.1f} h at target, {cover_f:>5.1f} h before a loss  {v}")
    return "\n".join(lines), verdicts


# ---- check

def fields(md):
    """The pasted fields of a listing: service name and description, then each package."""
    block = lambda label, text: (re.search(rf"\*\*{re.escape(label)}\*\*[^\n]*\n+```\n(.*?)\n```", text, re.S) or [None, None])[1]
    head, *pk = re.split(r"^### Package \d+\s*$", md, flags=re.M)
    service = {"name": block("Service name", head), "desc": block("Describe your service", head)}
    m = re.search(r"\*\*Price:\*\*\s*`(\d+)`\s*THB, unit \*\*([^*]+)\*\*", head)
    service["price"], service["unit"] = (int(m.group(1)), m.group(2)) if m else (None, None)
    tags = re.search(r"\*\*Add tags to your service:\*\*\s*(.+)", head)
    service["tags"] = tags.group(1) if tags else ""
    packages = []
    for p in pk:
        m = re.search(r"\*\*Price:\*\*\s*`(\d+)`\s*THB, unit \*\*([^*]+)\*\*", p)
        packages.append({"name": block("Package name", p), "desc": block("Description", p),
                         "price": int(m.group(1)) if m else None, "unit": m.group(2) if m else None})
    return service, packages


def check(o, md):
    service, packages = fields(md)
    res = {}
    res["service-fields"] = (bool(service["name"] and service["desc"]), "name and description present")
    n = len(service["desc"] or "")
    res["service-length"] = (n <= int(o["service_max"]), f"{n}/{o['service_max']}")
    long = [(p["name"], len(p["desc"] or "")) for p in packages if len(p["desc"] or "") > int(o["package_max"])]
    res["package-length"] = (not long, f"over {o['package_max']}: {long}" if long else f"all <= {o['package_max']}")
    units = set(o["units"])
    badu = [u for u in [service["unit"]] + [p["unit"] for p in packages] if u not in units]
    res["units"] = (not badu, f"not offered by the platform: {badu}" if badu else "all offered")
    want = [(p["name"], int(num(p["price"])), p["unit"]) for p in o["packages"]]
    got = [(p["name"], p["price"], p["unit"]) for p in packages]
    res["packages-match"] = (want == got, "names, prices and units match the offer" if want == got else f"offer {want} vs listing {got}")
    pasted = "\n".join([service["name"] or "", service["desc"] or "", service["tags"]]
                       + [(p["name"] or "") + "\n" + (p["desc"] or "") for p in packages])
    sym = sorted(set(c for c in pasted if c in o["forbidden_symbols"]))
    res["symbols"] = (not sym, f"found {sym}" if sym else "none")
    stack = [t for t in o["avoid_terms"] if re.search(rf"(?<![\w.]){re.escape(t)}(?![\w])", pasted, re.I)]
    res["no-stack"] = (not stack, f"found {stack}" if stack else "none named")
    known = {n.replace(",", "") for n in NUM.findall(Path(o["_path"]).read_text(encoding="utf-8"))}
    nums = {n.replace(",", "") for n in NUM.findall(pasted)}
    stray = sorted(x for x in nums if len(x) > 1 and x not in known)
    res["numbers"] = (not stray, f"not in the offer: {stray}" if stray else "every number is in the offer")
    return res


def selftest():
    toon = ('fee: "0.20"\ndays_per_month: 20\nhours_per_day: 5\ntarget_income: 9000\n'
            'service_max: 50\npackage_max: 40\nunits[2]: Project,Session\nforbidden_symbols: "+"\n'
            'avoid_terms[1]: React\n'
            'costs[2]{item,kind,thb_month,source}:\n  living,living,5000,me\n  tools,business,1000,me\n'
            'packages[2]{name,price,unit,hours,days,revisions,support_days}:\n  A,1000,Project,4,3,2,14\n  B,500,Session,9,30,0,0\n')
    o = load_toon(toon)
    floor, target, h = rates(o)
    assert h == 100 and floor == 60 and target == 100, (floor, target, h)
    _, v = price(o)
    assert v == ["ok", "LOSS"], v          # A: 800 net pays 8 h at target; B: 400 net pays 6.7 h before a loss
    import tempfile, os
    with tempfile.NamedTemporaryFile("w", suffix=".toon", delete=False) as f:
        f.write(toon)
    o["_path"] = f.name
    good = ("**Service name**\n\n```\nเว็บ\n```\n\n**Describe your service** (3/50)\n\n```\nทำเว็บ 14 วัน\n```\n\n"
            "**Price:** `1000` THB, unit **Project**\n\n**Add tags to your service:** เว็บ\n\n"
            "### Package 1\n\n**Package name**\n\n```\nA\n```\n\n**Description**\n\n```\nได้เว็บ\n```\n\n**Price:** `1000` THB, unit **Project**\n\n"
            "### Package 2\n\n**Package name**\n\n```\nB\n```\n\n**Description**\n\n```\nดูแล\n```\n\n**Price:** `500` THB, unit **Session**\n")
    r = check(o, good)
    assert all(ok for ok, _ in r.values()), r
    bad = good.replace("ทำเว็บ 14 วัน", "ทำด้วย React + 777").replace("unit **Session**", "unit **Month**")
    r = check(o, bad)
    assert not r["symbols"][0] and not r["no-stack"][0] and not r["units"][0] and not r["numbers"][0], r
    assert "777" in r["numbers"][1]
    os.unlink(f.name)
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("cmd", nargs="?", choices=["price", "check"])
    ap.add_argument("offer", nargs="?")
    ap.add_argument("listing", nargs="?")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    if not (a.cmd and a.offer):
        ap.error("give price <offer> or check <offer> <listing>, or --selftest")
    o = load_toon(Path(a.offer).read_text(encoding="utf-8"))
    o["_path"] = a.offer
    if a.cmd == "price":
        text, verdicts = price(o)
        print(text)
        return sum(v == "LOSS" for v in verdicts)
    res = check(o, Path(a.listing).read_text(encoding="utf-8"))
    for k, (ok, why) in res.items():
        print(f"{'PASS' if ok else 'FAIL'}  {k:15} {why}")
    fails = sum(not ok for ok, _ in res.values())
    print(f"{len(res) - fails}/{len(res)} pass")
    return fails


if __name__ == "__main__":
    sys.exit(main())
