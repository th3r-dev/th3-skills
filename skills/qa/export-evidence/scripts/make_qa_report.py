# /// script
# requires-python = ">=3.10"
# dependencies = ["openpyxl", "pillow"]
# ///
"""QA test report: <evidence>/ -> one .xlsx in the team layout.

    uv run make_qa_report.py <evidence dir> --out <report.xlsx> --title "<summary title>" --env PROD --date "OCT 27, 2026"
        [--only-sheets "blue app export excel" ...] [--labels labels.json]

Evidence contract (what collect_export.py writes; a hand-made run only has to follow the same columns):
  evidence/environment.csv   key,value                       -> Summary header block
  evidence/index.csv         one row per case; required: no,title,folder,result
                             optional: sheet (groups cases for --only-sheets), actual (B7 Actual Result text).
                             Every other column shows on Summary.
  evidence/<folder>/steps.csv step,action,result,evidence (+ anything) — evidence = PNG path relative to <folder>

Sheet layout: Summary (B2 title, B4 Test Result, B5 Test Environment, B6 Test Date, env block, case table with
links), then one tab per case (Report01, Report02 …): B2 title, B4–B7 header block, a bold heading row, and
the step screenshots captioned in a 2-column grid. --labels overrides the caption words (see LABELS).
"""
from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path

from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.styles import Font, PatternFill
from PIL import Image

def inside_work(p, what="path"):
    """CLI paths come from an agent, so this script only reads and writes inside the folder it runs from."""
    root = os.path.realpath(os.getcwd())
    full = os.path.realpath(os.path.join(root, os.path.expanduser(str(p))))
    if full != root and not full.startswith(root + os.sep):
        raise SystemExit(f"{what} {p!r} is outside the working folder {root}; run the script from that folder")
    return full


W = 900                      # rendered screenshot width, px
COLS = (2, 17)               # B and Q: two screenshots per grid row
ROW_PX = 20                  # default row height, px
HEAD = PatternFill("solid", fgColor="005487")
FAIL_HEAD = PatternFill("solid", fgColor="B91C1C")
OK = PatternFill("solid", fgColor="DCFCE7")
BAD = PatternFill("solid", fgColor="FEE2E2")
LABELS = {
    "step": "step {step}",
    "no_image": "(no image: {path})",
    "all_pass": "All {n} cases exported a file; every file opened and held data.",
    "some_fail": "{p} of {n} cases exported a file; {f} failed: {bad}",
}


def read(path: Path):
    return list(csv.DictReader(path.open(encoding="utf-8-sig")))


def sheet_name(case):
    """the group a case belongs to — what --only-sheets selects; not the tab"""
    return (case.get("sheet") or f"Report{int(case['no']):02d}")[:31]


def summary(wb, cases, env, a):
    ws = wb.active
    ws.title = "Summary"
    ws["B2"] = a.title
    ws["B2"].font = Font(bold=True, size=14)
    passed = sum(c["result"] == "PASS" for c in cases)
    ws["B4"] = f"Test Result:  {'Success' if passed == len(cases) else 'Fail'} ({passed}/{len(cases)} PASS)"
    ws["B5"] = f"Test Environment: {a.env}"
    ws["B6"] = f"Test Date: {a.date}"
    row = 8
    for e in env:
        ws.cell(row=row, column=2, value=e["key"]).font = Font(bold=True)
        ws.cell(row=row, column=3, value=e["value"])
        row += 1
    row += 1
    cols = [k for k in cases[0] if k not in ("folder", "actual") and not k.startswith("_")] if cases else []
    for i, h in enumerate(cols, 2):
        c = ws.cell(row=row, column=i, value=h)
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = HEAD
    for case in cases:
        row += 1
        for i, k in enumerate(cols, 2):
            c = ws.cell(row=row, column=i, value=case[k])
            if k == "result":
                c.fill = OK if case[k] == "PASS" else BAD
        link = ws.cell(row=row, column=2)
        link.hyperlink = f"#'{case['_tab']}'!A1"
        link.font = Font(color="0563C1", underline="single")
    ws.column_dimensions["B"].width = 18
    ws.column_dimensions["C"].width = 40


def actual_many(cases, labels):
    p = sum(c["result"] == "PASS" for c in cases)
    n = len(cases)
    if p == n:
        return labels["all_pass"].format(n=n)
    bad = ", ".join(c["title"].split(" · ")[0] for c in cases if c["result"] != "PASS")
    return labels["some_fail"].format(p=p, n=n, f=n - p, bad=bad)


def head(ws, cases, a, labels):
    ok = all(c["result"] == "PASS" for c in cases)
    ws["B2"] = cases[0].get("title") or ws.title
    ws["B2"].font = Font(bold=True, size=14)
    ws["B4"] = f"Test Result:  {'Success' if ok else 'Fail'}"
    ws["B5"] = f"Test Environment: {a.env}"
    ws["B6"] = f"Test Date: {a.date}"
    acts = [c.get("actual", "") for c in cases if c.get("actual")]
    ws["B7"] = "Actual Result: " + (acts[0] if len(acts) == 1 else actual_many(cases, labels))
    for c in ("B4", "B5", "B6", "B7"):
        ws[c].font = Font(size=12)


def case_block(ws, case, evidence: Path, row: int, labels) -> int:
    d = evidence / case["folder"]
    h = ws.cell(row=row, column=2, value=f"{case['no']}. {case['title']} · {case['result']}")
    h.font = Font(bold=True, size=13, color="FFFFFF")
    h.fill = HEAD if case["result"] == "PASS" else FAIL_HEAD
    if case.get("actual"):
        ws.cell(row=row + 1, column=2, value=case["actual"])
    row += 3
    steps = read(d / "steps.csv")
    for i in range(0, len(steps), 2):
        tallest = 0
        for col, s in zip(COLS, steps[i:i + 2]):
            cap = f"{labels['step'].format(step=s['step'])} · {s['action']} · {s['result']}"
            ws.cell(row=row, column=col, value=cap).font = Font(bold=True)
            png = d / s["evidence"] if s.get("evidence") else None
            if not png or not png.is_file():
                ws.cell(row=row + 1, column=col, value=labels["no_image"].format(path=s.get("evidence") or "-"))
                tallest = max(tallest, ROW_PX * 2)
                continue
            with Image.open(png) as im:
                w, hgt = im.size
            scale = min(1.0, W / w)
            img = XLImage(str(png))
            img.width, img.height = int(w * scale), int(hgt * scale)
            ws.add_image(img, ws.cell(row=row + 1, column=col).coordinate)
            tallest = max(tallest, img.height)
        row += 1 + tallest // ROW_PX + 2
    return row + 2


def build(evidence: Path, out: Path, a, labels) -> Workbook:
    cases = read(evidence / "index.csv")
    if a.only_sheets:
        cases = [c for c in cases if sheet_name(c) in a.only_sheets]
    if not cases:
        raise SystemExit("no cases to write")
    env = read(evidence / "environment.csv") if (evidence / "environment.csv").exists() else []
    for i, c in enumerate(cases, 1):
        c["_tab"] = f"Report{i:02d}"
    wb = Workbook()
    summary(wb, cases, env, a)
    for case in cases:  # one tab per case, never stacked
        ws = wb.create_sheet(case["_tab"])
        head(ws, [case], a, labels)
        case_block(ws, case, evidence, 9, labels)
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    return wb


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("evidence", help="evidence/ folder (index.csv + environment.csv + <folder>/steps.csv)")
    ap.add_argument("--out", required=True, help=".xlsx to write")
    ap.add_argument("--title", default="QA Test Report", help="Summary B2")
    ap.add_argument("--env", default="DEV", help="DEV · UAT · PROD")
    ap.add_argument("--date", required=True, help='e.g. "OCT 27, 2026" (the real run date)')
    ap.add_argument("--only-sheets", nargs="*", help="keep only cases whose sheet is listed (split one run into several workbooks)")
    ap.add_argument("--labels", help="JSON file overriding caption words (keys: " + ", ".join(LABELS) + ")")
    a = ap.parse_args()
    labels = {**LABELS, **(json.loads(Path(inside_work(a.labels, "labels")).read_text(encoding="utf-8")) if a.labels else {})}
    out = Path(inside_work(a.out, "output"))
    wb = build(Path(inside_work(a.evidence, "evidence dir")), out, a, labels)
    print(out, out.stat().st_size, "bytes,", len(wb.sheetnames), "sheets")


if __name__ == "__main__":
    main()
