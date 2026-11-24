#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["openpyxl"]
# ///
"""Pull the Q&A tabs of a sheet export, and merge the condensed review notes into Remark text.

    qa.py pull <sheet.xlsx | download.json> [--out DIR] [--tab REGEX] [--headers "No,Question,Answer,Remark"]
        -> DIR/<key>/qa.json
    qa.py merge <key> [--out DIR] [--date DD/MM/YYYY]
        DIR/<key>/<DDMMYYYY>/final.json -> DIR/<key>/<DDMMYYYY>/plan.json
    qa.py selfcheck

<src> is the .xlsx export, or a JSON file with a base64 `content` field (what some Drive MCP
downloads spill to disk). `--tab` is a regex with one capture group; the group is the folder key.
`merge` reads final.json ({No: "- ...\n- ..."}, the lens notes condensed by hand into the team's
own bullet style) and writes plan.json (row -> full new Remark cell: the team's text kept, our
bullets appended after a blank line). Our bullets from any earlier final.json of the same key are
stripped first, so a re-review replaces, not stacks.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import io
import json
import re
import sys
import warnings
from pathlib import Path

DEFAULT_OUT = Path("work") / "qa-review"
DEFAULT_TAB = r"Q&A\s*(?:List)?\s*(\S+)"
DEFAULT_HEADERS = ["No", "Question", "Answer", "Remark"]
SEP = re.compile(r"\n*---- (\d\d/\d\d/\d{4}) ----\n")  # legacy dated blocks from a first run


def load(src: Path):
    import openpyxl
    raw = src.read_bytes()
    if src.suffix.lower() != ".xlsx":
        raw = base64.b64decode(json.loads(raw)["content"])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return openpyxl.load_workbook(io.BytesIO(raw), data_only=True)


def cell_no(v) -> str:
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v or "").strip()


def pull(src: Path, out: Path, tab: str, headers: list[str]) -> int:
    rx = re.compile(tab)
    found = 0
    for ws in load(src):
        m = rx.search(ws.title)
        if not m:
            continue
        key = m.group(1) if m.groups() else re.sub(r"\W+", "_", ws.title)
        head = [str(c or "").strip() for c in next(ws.iter_rows(max_row=1, values_only=True))]
        if head[:4] != headers:
            sys.exit(f"{ws.title}: header row is {head[:4]}, expected {headers} (pass --headers)")
        rows = []
        for i, r in enumerate(ws.iter_rows(min_row=2, max_col=4, values_only=True), 2):
            if r[1] is None:
                continue
            rows.append({"No": cell_no(r[0]), "row": i, "question": str(r[1]).strip(),
                         "answer": str(r[2] or "").strip(), "remark": str(r[3] or "").strip()})
        d = out / key
        d.mkdir(parents=True, exist_ok=True)
        (d / "qa.json").write_text(json.dumps({"tab": ws.title, "headers": headers, "rows": rows},
                                              ensure_ascii=False, indent=1), encoding="utf-8")
        noted = sum(1 for r in rows if r["remark"])
        print(f"{ws.title}: {len(rows)} questions, {noted} with a Remark already -> {d / 'qa.json'}")
        found += 1
    if not found:
        sys.exit(f"no tab matches /{tab}/")
    return found


def merged_cell(old: str, note: str, ours: list[str]) -> str:
    """Team text kept; earlier notes of ours (and legacy dated blocks) removed; `note` appended."""
    text = SEP.split(old)[0]
    for prev in ours:
        if prev:
            text = text.replace(prev, "")
    text = text.strip()
    return f"{text}\n\n{note}" if text else note


def merge(key: str, out: Path, date: str) -> list[dict]:
    day = out / key / date.replace("/", "")  # DD/MM/YYYY -> DDMMYYYY
    qa = json.loads((out / key / "qa.json").read_text(encoding="utf-8"))
    final = json.loads((day / "final.json").read_text(encoding="utf-8"))
    ours = [v.strip() for f in (out / key).glob("*/final.json")
            for v in json.loads(f.read_text(encoding="utf-8")).values()]
    plan = [{"No": r["No"], "row": r["row"], "old": r["remark"],
             "new": merged_cell(r["remark"], final[r["No"]].strip(), ours)}
            for r in qa["rows"] if final.get(r["No"], "").strip()]
    (day / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(plan)}/{len(qa['rows'])} rows get a Remark -> {day / 'plan.json'}")
    return plan


def selfcheck() -> None:
    assert merged_cell("", "- a", []) == "- a"
    assert merged_cell("team", "- a", []) == "team\n\n- a"
    assert merged_cell("team\n\n- a", "- b", ["- a"]) == "team\n\n- b"  # re-review replaces ours
    assert merged_cell("team\n\n---- 06/10/2026 ----\nBusiness (OK): x", "- b", []) == "team\n\n- b"
    assert cell_no(3.0) == "3" and cell_no("3a") == "3a" and cell_no(None) == ""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pull")
    p.add_argument("src", type=Path)
    p.add_argument("--out", type=Path, default=DEFAULT_OUT)
    p.add_argument("--tab", default=DEFAULT_TAB, help="regex with one capture group = folder key")
    p.add_argument("--headers", default=",".join(DEFAULT_HEADERS), help="the four header labels, comma separated")
    m = sub.add_parser("merge")
    m.add_argument("key")
    m.add_argument("--out", type=Path, default=DEFAULT_OUT)
    m.add_argument("--date", default=dt.date.today().strftime("%d/%m/%Y"))
    sub.add_parser("selfcheck")
    a = ap.parse_args()
    if a.cmd == "pull":
        pull(a.src.resolve(), a.out.resolve(), a.tab, [h.strip() for h in a.headers.split(",")])
    elif a.cmd == "merge":
        merge(a.key, a.out.resolve(), a.date)
    else:
        selfcheck()
        print("ok")


if __name__ == "__main__":
    main()
