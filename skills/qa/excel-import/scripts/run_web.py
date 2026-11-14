# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright>=1.47", "openpyxl>=3.1", "pillow>=10"]
# ///
"""Run an Excel-import test set through a web portal with Playwright, three checks per case.

    S=skills/qa/excel-import/scripts
    # once per account: a PERSON signs in in the opened window; the session is saved outside the repo
    uv run $S/run_web.py login --adapter adapter.py --account acme
    # validate every case for that account (writes nothing)
    uv run $S/run_web.py run --adapter adapter.py --cases <dir>/cases.json --account acme
    # ... and submit the cases whose mode is "submit"
    uv run $S/run_web.py run --adapter adapter.py --cases <dir>/cases.json --account acme --ids R4 --submit
    uv run $S/run_web.py report --adapter adapter.py --cases <dir>/cases.json      # rebuild results/report.xlsx
    uv run $S/run_web.py selftest

Per case, three checks must agree before a case passes:
  1. file   -- adapter.check() replays the importer's validator against the test DB; must equal case.expect
  2. web    -- the real validate response body; must equal case.expect
  3. db     -- after --submit only: the created document's details / totals (adapter.db_verify)

cases.json: [{id, file (relative to cases.json), company, mode: validate|submit,
              expect: {status, detailCount, errors: [substring, ...]}, note, source,
              scenario?: Happy Case|Edge Case|Negative, trace?: requirement it proves}]
Results land in <cases dir>/results/<stamp>-<account>.{json,md} with every raw response body and a
screenshot per case; results/report.xlsx is rebuilt after every run from ALL runs in that folder
(screenshots embedded, links in-workbook only, so the file survives being sent elsewhere).

The agent never types a password: `login` opens a headed browser and waits for a person.
The adapter contract is documented in adapter_example.py.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

STATE_DIR = Path.home() / ".cache" / "qa-excel-import"


def load_adapter(path: str):
    p = Path(path).resolve()
    spec = importlib.util.spec_from_file_location("qa_import_adapter", p)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(p.parent))
    spec.loader.exec_module(mod)
    for name in ("BASE", "ACCOUNTS", "read", "check", "connect", "open_import", "web_validate", "web_errors", "web_status"):
        if not hasattr(mod, name):
            sys.exit(f"adapter {p.name} lacks {name} (see adapter_example.py)")
    return mod


def state_path(base, account):
    return STATE_DIR / re.sub(r"\W+", "_", base.split("//")[-1]) / f"{account}.json"


def login(args, ad):
    from playwright.sync_api import sync_playwright
    out = state_path(args.base, args.account)
    out.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(headless=False, channel=args.channel)
        ctx = b.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        login_path = getattr(ad, "LOGIN_PATH", "/login")
        page.goto(f"{args.base}{login_path}")
        print(f"sign in as the {args.account.upper()} account in the opened window (waiting up to 5 min)...")
        page.wait_for_url(lambda u: login_path not in u, timeout=300_000)
        page.wait_for_load_state("networkidle")
        ctx.storage_state(path=str(out))
        out.chmod(0o600)
        print(f"session saved: {out}")
        b.close()


# ---- checks ----------------------------------------------------------------------------
def compare(expect, status, details, errors):
    """list of mismatches between a verdict and case.expect (empty = pass)."""
    bad = []
    if status != expect["status"]:
        bad.append(f"status {status} != {expect['status']}")
    if expect["status"] == "VALIDATED" and details != expect.get("detailCount"):
        bad.append(f"detailCount {details} != {expect.get('detailCount')}")
    for want in expect.get("errors") or []:
        if not any(want in e for e in errors):
            bad.append(f"missing error: {want}")
    if expect["status"] != "VALIDATED" and not errors:
        bad.append("expected errors, got none")
    return bad


def norm(s) -> str:
    return re.sub(r"\s+", "", str(s if s is not None else "")).upper()


def run(args, ad):
    from playwright.sync_api import sync_playwright
    cases_path = Path(args.cases).resolve()
    company = ad.ACCOUNTS[args.account]
    cases = [c for c in json.loads(cases_path.read_text(encoding="utf-8")) if c["company"] == company]
    if args.ids:
        keep = set(args.ids.split(","))
        cases = [c for c in cases if c["id"] in keep]
    if not cases:
        sys.exit(f"no case in {cases_path.name} for account {args.account}")
    state = state_path(args.base, args.account)
    if not state.exists():
        sys.exit(f"no saved session for {args.account}: run `run_web.py login --account {args.account}` first")

    con = ad.connect()
    cur = con.cursor()
    company_name = ad.tenant_name(cur, company) if hasattr(ad, "tenant_name") else None

    out_dir = cases_path.parent / "results"
    out_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S") + f"-{args.account}"
    results = []
    with sync_playwright() as p:
        b = p.chromium.launch(headless=not args.headed, channel=args.channel)
        ctx = b.new_context(storage_state=str(state), viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        ad.open_import(page, args.base)
        if company_name and norm(company_name) not in norm(page.locator("body").inner_text()):
            sys.exit(f"signed-in tenant is not {company_name!r} -- wrong session for --account {args.account}")
        for c in cases:
            xlsx = cases_path.parent / c["file"]
            res = dict(id=c["id"], file=c["file"], mode=c["mode"], expect=c["expect"])
            # 1. file
            st, errs, groups = ad.check(con, c["company"], xlsx)
            res["file_check"] = dict(status=st, detailCount=groups, errors=errs, mismatch=compare(c["expect"], st, groups, errs))
            if res["file_check"]["mismatch"]:
                res["verdict"] = "FAIL (file)"
                results.append(res)
                print(f"{c['id']:4} FAIL file  {res['file_check']['mismatch']}")
                continue
            # 2. web validate
            if c is not cases[0]:
                ad.open_import(page, args.base)
            body = ad.web_validate(page, xlsx)
            (out_dir / f"{stamp}-{c['id']}-validate.json").write_text(json.dumps(body, ensure_ascii=False, indent=1), encoding="utf-8")
            wst, wdet = ad.web_status(body)
            werrs = ad.web_errors(body)
            res["web"] = dict(status=wst, detailCount=wdet, errors=werrs, mismatch=compare(c["expect"], wst, wdet, werrs))
            page.screenshot(path=str(out_dir / f"{stamp}-{c['id']}-validate.png"), full_page=False)
            verdict = "PASS" if not res["web"]["mismatch"] else "FAIL (web)"
            # 3. submit + db
            if verdict == "PASS" and c["mode"] == "submit" and args.submit:
                receipt = ad.receipt_of(xlsx)
                dup = ad.already_imported(cur, c["company"], receipt)
                if dup:
                    res["submit"] = dict(skipped=f"receipt {receipt} already imported as {dup}")
                    verdict = "PASS (validate) · submit skipped"
                else:
                    sb = ad.web_submit(page)
                    (out_dir / f"{stamp}-{c['id']}-submit.json").write_text(json.dumps(sb, ensure_ascii=False, indent=1), encoding="utf-8")
                    sst, doc_id = ad.submit_status(sb)
                    res["submit"] = dict(status=sst, documentId=doc_id)
                    time.sleep(1)
                    got, bad = ad.db_verify(cur, doc_id, c["company"], xlsx) if doc_id else (None, ["no document id in submit response"])
                    if got and got.get("details") != c["expect"]["detailCount"]:
                        bad.append(f"db details {got.get('details')} != {c['expect']['detailCount']}")
                    res["db"] = dict(found=got, mismatch=bad)
                    verdict = "PASS" if sst == getattr(ad, "SUBMITTED_STATUS", "SUBMITTED") and not bad else "FAIL (submit/db)"
            else:
                page.keyboard.press("Escape")
            res["verdict"] = verdict
            results.append(res)
            print(f"{c['id']:4} {verdict:32} web={wst} details={wdet}"
                  + (f" doc={res.get('submit', {}).get('documentId')}" if res.get("submit") else ""))
            for m in res["web"]["mismatch"] + (res.get("db") or {}).get("mismatch", []):
                print(f"      - {m}")
        b.close()

    (out_dir / f"{stamp}.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [f"# Excel import QA · {args.account} · {stamp}", "", f"cases: `{cases_path.name}` · base: {args.base}", "",
             "| id | mode | expect | file check | web | submit / db | verdict |", "|---|---|---|---|---|---|---|"]
    for r in results:
        fc, w, s, dbr = r.get("file_check", {}), r.get("web", {}), r.get("submit", {}), r.get("db", {})
        sub = s.get("skipped") or (f"{s.get('documentId')} · {(dbr.get('found') or {}).get('details')} details" if s else "—")
        lines.append(f"| {r['id']} | {r['mode']} | {r['expect']['status']} {r['expect'].get('detailCount') or ''} | "
                     f"{fc.get('status')} {fc.get('detailCount')} | {w.get('status', '—')} {w.get('detailCount') or ''} | {sub} | **{r['verdict']}** |")
    (out_dir / f"{stamp}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    xlsx = build_report(out_dir, cases_path, ad)
    print(f"\nreport: {out_dir / (stamp + '.md')}" + (f" · {xlsx}" if xlsx else ""))
    return 0 if all(r["verdict"].startswith("PASS") for r in results) else 1


# ---- xlsx report -------------------------------------------------------------------------
RUN_FILE = re.compile(r"^(\d{8})-(\d{6})-([a-z0-9]+)\.json$")  # <stamp>.json; per-case bodies have an -<id>- part


def _run_rows(results_dir):
    """every (stamp, day, hms, account, result) from results/<stamp>.json, oldest first."""
    for f in sorted(f for f in results_dir.iterdir() if RUN_FILE.match(f.name)):
        day, hms, account = RUN_FILE.match(f.name).groups()
        for r in json.loads(f.read_text(encoding="utf-8")):
            yield f.stem, day, hms, account, r


def _cells(r):
    e, fc, w = r.get("expect", {}), r.get("file_check", {}), r.get("web", {})
    s, dbr = r.get("submit", {}), r.get("db", {})
    fmt = lambda st, n: f"{st or '—'}" + (f" · {n} detail" if n not in (None, "", 0) else "")
    if s.get("skipped"):
        sub = s["skipped"]
    elif s:
        found = dbr.get("found") or {}
        sub = f"{s.get('status')} {s.get('documentId') or ''}".strip() + (
            " · DB " + " · ".join(f"{k} {v:,.0f}" if isinstance(v, float) else f"{k} {v}" for k, v in found.items()) if found else "")
    else:
        sub = "—"
    mism = (fc.get("mismatch") or []) + (w.get("mismatch") or []) + (dbr.get("mismatch") or [])
    return (fmt(e.get("status"), e.get("detailCount")), fmt(fc.get("status"), fc.get("detailCount")),
            fmt(w.get("status"), w.get("detailCount")), "\n".join(w.get("errors") or []), sub, "\n".join(mism))


def build_report(results_dir: Path, cases_path: Path, ad=None):
    """results/report.xlsx -- one self-contained file: screenshots embedded, links in-workbook.

    sheets: Summary (latest verdict per case) · Runs (every run) · one sheet per case with the test
    input read back from the .xlsx (via adapter.read), the latest result, and its screenshot embedded.
    """
    from openpyxl import Workbook
    from openpyxl.drawing.image import Image as XLImage
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.hyperlink import Hyperlink
    runs = list(_run_rows(results_dir))
    if not runs:
        return None
    cases = json.loads(cases_path.read_text(encoding="utf-8")) if cases_path.exists() else []
    order = [c["id"] for c in cases] + sorted({r["id"] for *_, r in runs} - {c["id"] for c in cases})
    cmeta = {c["id"]: c for c in cases}
    latest, latest_submit = {}, {}
    for stamp, day, hms, acc, r in runs:
        latest[r["id"]] = (stamp, day, hms, acc, r)
        if r.get("submit"):
            latest_submit[r["id"]] = (stamp, r)
    bold, link = Font(bold=True), Font(color="0563C1", underline="single")
    head = PatternFill("solid", fgColor="073763")
    fills = {"PASS": PatternFill("solid", fgColor="E2F0D9"), "FAIL": PatternFill("solid", fgColor="FBE2E2")}
    wrap = Alignment(wrap_text=True, vertical="top")

    def verdict_fill(cell, v):
        k = "PASS" if str(v).startswith("PASS") else "FAIL" if str(v).startswith("FAIL") else None
        if k:
            cell.fill = fills[k]

    def header(ws, cols):
        ws.append([h for h, _ in cols])
        for i, (_, w) in enumerate(cols, 1):
            ws.column_dimensions[get_column_letter(i)].width = w
            c = ws.cell(1, i)
            c.font, c.fill = Font(bold=True, color="FFFFFF"), head

    wb = Workbook()
    ws = wb.active
    ws.title = "Summary"
    header(ws, [("case", 6), ("test file", 32), ("company", 8), ("mode", 8), ("expected", 22), ("file check", 22),
                ("web validate", 22), ("submit / DB (latest)", 58), ("verdict", 18), ("last run", 16), ("evidence", 10)])
    for cid in order:
        if cid not in latest:
            c = cmeta[cid]
            ws.append([cid, c["file"], c["company"], c["mode"], c["expect"]["status"], "", "", "not run yet", "", "", ""])
            continue
        stamp, day, hms, acc, r = latest[cid]
        e, fc, w, _, sub, _ = _cells(r)
        if cid in latest_submit and not r.get("submit"):
            sub = _cells(latest_submit[cid][1])[4] + f"  (run {latest_submit[cid][0]})"
        ws.append([cid, r.get("file"), cmeta.get(cid, {}).get("company", ""), r.get("mode"), e, fc, w, sub,
                   r.get("verdict"), f"{day[6:]}/{day[4:6]} {hms[:2]}:{hms[2:4]} {acc}", f"see {cid}"])
        row = ws.max_row
        verdict_fill(ws.cell(row, 9), r.get("verdict"))
        ln = ws.cell(row, 11)
        ln.hyperlink, ln.font = Hyperlink(ref=ln.coordinate, location=f"'{cid}'!A1"), link
    passed = sum(1 for cid in order if cid in latest and str(latest[cid][4].get("verdict")).startswith("PASS"))
    ws.append([])
    ws.append([f"passed {passed}/{len(order)} cases"])
    ws.cell(ws.max_row, 1).font = bold
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.alignment = wrap
    ws.freeze_panes = "B2"

    wh = wb.create_sheet("Runs")
    header(wh, [("date", 11), ("time", 7), ("account", 8), ("case", 6), ("mode", 8), ("expected", 20),
                ("file check", 20), ("web validate", 20), ("web errors", 60), ("submit / DB", 50),
                ("verdict", 18), ("mismatch", 40)])
    for stamp, day, hms, acc, r in runs:
        e, fc, w, errs, sub, mism = _cells(r)
        wh.append([f"{day[6:]}/{day[4:6]}/{day[:4]}", f"{hms[:2]}:{hms[2:4]}", acc, r["id"], r.get("mode"),
                   e, fc, w, errs, sub, r.get("verdict"), mism])
        verdict_fill(wh.cell(wh.max_row, 11), r.get("verdict"))
    for row in wh.iter_rows(min_row=2):
        for c in row:
            c.alignment = wrap
    wh.freeze_panes = "E2"
    wh.auto_filter.ref = wh.dimensions

    for cid in order:
        c = cmeta.get(cid, {})
        wc = wb.create_sheet(cid[:31])
        wc.column_dimensions["A"].width = 24
        for col in "BCDEFGHIJKLMNOPQR":
            wc.column_dimensions[col].width = 16
        back = wc.cell(1, 1, "← Summary")
        back.hyperlink, back.font = Hyperlink(ref="A1", location="'Summary'!A1"), link
        wc.cell(2, 1, f"{cid} · {c.get('file', '')}").font = Font(bold=True, size=13)
        r0 = 3
        for k, v in [("mode", c.get("mode")), ("company", c.get("company")), ("source", c.get("source")),
                     ("expected", c.get("note")), ("scenario", c.get("scenario")), ("trace", c.get("trace"))]:
            wc.cell(r0, 1, k).font = bold
            wc.cell(r0, 2, v)
            r0 += 1
        xlsx = cases_path.parent / c["file"] if c.get("file") else None
        if ad and xlsx and xlsx.exists():
            heads, hdr, rows = ad.read(xlsx)
            r0 += 1
            wc.cell(r0, 1, "test input — header").font = bold
            for lbl, val in zip(getattr(ad, "HEADER_LABELS", [f"H{i + 1}" for i in range(len(hdr))]), hdr):
                r0 += 1
                wc.cell(r0, 1, lbl)
                wc.cell(r0, 2, val)
            r0 += 2
            wc.cell(r0, 1, "test input — rows").font = bold
            r0 += 1
            for i, h in enumerate(["row"] + list(heads)):
                cell = wc.cell(r0, 1 + i, h)
                cell.font, cell.fill = Font(bold=True, color="FFFFFF"), head
            for rn, v in rows:
                r0 += 1
                for i, val in enumerate([rn] + list(v)):
                    wc.cell(r0, 1 + i, val)
        r0 += 2
        wc.cell(r0, 1, "latest result").font = bold
        if cid in latest:
            stamp, day, hms, acc, r = latest[cid]
            e, fc, w, errs, sub, mism = _cells(r)
            if cid in latest_submit and not r.get("submit"):
                sub = _cells(latest_submit[cid][1])[4] + f"  (run {latest_submit[cid][0]})"
            for k, v in [("run", stamp), ("expected", e), ("file check", fc), ("web validate", w),
                         ("web errors", errs), ("submit / DB", sub), ("mismatch", mism or "—"), ("verdict", r.get("verdict"))]:
                r0 += 1
                wc.cell(r0, 1, k).font = bold
                cell = wc.cell(r0, 2, v)
                cell.alignment = Alignment(wrap_text=True, vertical="top")
                if k == "verdict":
                    verdict_fill(cell, v)
            png = results_dir / f"{stamp}-{cid}-validate.png"
            if png.exists():
                r0 += 2
                wc.cell(r0, 1, "evidence (screen after validate)").font = bold
                img = XLImage(str(png))          # bytes are copied into the xlsx -- no external link
                scale = 1100 / img.width
                img.width, img.height = int(img.width * scale), int(img.height * scale)
                wc.add_image(img, f"A{r0 + 1}")
        else:
            wc.cell(r0 + 1, 1, "not run yet")
    out = results_dir / "report.xlsx"
    wb.save(out)
    return out


def report(args, ad):
    cases_path = Path(args.cases).resolve()
    out = build_report(cases_path.parent / "results", cases_path, ad)
    print(f"report: {out}" if out else f"no <stamp>.json under {cases_path.parent / 'results'}")
    return 0


def selftest():
    e = dict(status="VALIDATION_ERROR", detailCount=0, errors=["does not match tax right"])
    assert compare(e, "VALIDATION_ERROR", 0, ["row 12: form type X does not match tax right Y"]) == []
    assert compare(e, "VALIDATED", 1, []) != []
    assert compare(dict(status="VALIDATED", detailCount=2, errors=[]), "VALIDATED", 1, []) == ["detailCount 1 != 2"]
    print("selftest ok")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("login", "run", "report"):
        sp = sub.add_parser(name)
        sp.add_argument("--adapter", required=True, help="python file implementing the adapter contract")
        if name != "report":
            sp.add_argument("--account", required=True)
            sp.add_argument("--base", help="portal base URL (default adapter.BASE)")
            sp.add_argument("--channel", default="chrome", help="playwright browser channel (chrome | msedge | chromium)")
        if name != "login":
            sp.add_argument("--cases", required=True)
        if name == "run":
            sp.add_argument("--ids", help="comma list, default all cases of the account")
            sp.add_argument("--submit", action="store_true", help="also submit cases whose mode is submit")
            sp.add_argument("--headed", action="store_true")
    sub.add_parser("selftest")
    a = ap.parse_args()
    if a.cmd == "selftest":
        return selftest()
    ad = load_adapter(a.adapter)
    if getattr(a, "base", None) is None and a.cmd != "report":
        a.base = ad.BASE
    if a.cmd != "report" and a.account not in ad.ACCOUNTS:
        sys.exit(f"--account must be one of {sorted(ad.ACCOUNTS)}")
    return {"login": login, "run": run, "report": report}[a.cmd](a, ad)


if __name__ == "__main__":
    sys.exit(main())
