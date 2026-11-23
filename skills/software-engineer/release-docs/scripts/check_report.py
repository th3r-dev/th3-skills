#!/usr/bin/env python3
"""Check a release report .md before it is rendered: the rules a reviewer would otherwise catch by eye.

    python3 scripts/check_report.py release-v1.4.0.md      # findings as file:line: rule: message, exit 1 if any
    python3 scripts/check_report.py --selftest

Rules:
  front-matter   the file opens with front matter whose title is "Release v<version>"
  sections       the four fixed pages exist: Overview, BA Decision, change details, test plan (Thai or English)
  placeholder    template text left in: <...>, vX.Y.Z, DD/MM/YYYY, #NN
  no-shot        "no screenshot yet" written instead of dropping the picture table
  image          a local image the report points at does not exist
  expected       a test case's Expected Result is empty or only says "same as before"
  qa-columns     Actual Result / Status already filled in (they are QA's to fill)
  secret         a password written into the report
Stdlib only.
"""
import argparse
import re
import sys
import tempfile
from pathlib import Path

SECTIONS = {
    "Overview": {"overview"},
    "BA Decision": {"ba decision"},
    "change details": {"รายละเอียดต่องาน", "change details"},
    "test plan": {"แผนเทส", "test plan"},
}
PLACEHOLDER = re.compile(r"<(?!/?[a-z]+\s*/?>)[^<>\n]{1,40}>|\bvX\.Y\.Z\b|\bDD/MM/YYYY\b|#NN\b")  # not <br>
NO_SHOT = re.compile(r"ยังไม่มีภาพ|no (?:screenshot|image|shot) yet", re.I)
VAGUE = re.compile(r"^(?:เหมือนเดิม|ครบเท่าเดิม|ไม่เปลี่ยน|ปกติ|same as before|as before|unchanged|works|ok|-)?\.?$", re.I)
SECRET = re.compile(r"(?:password|passwd|pwd|รหัสผ่าน)\s*[:=]\s*\S", re.I)
IMAGE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)")
FENCE = re.compile(r"^\s*(```|~~~)")


def cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def check(text: str, base: Path, name: str = "report") -> list[str]:
    out = []

    def say(n, rule, msg):
        out.append(f"{name}:{n}: {rule}: {msg}")

    lines = text.splitlines()
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    title = re.search(r"^title:\s*(.+)$", m.group(1), re.M) if m else None
    if not title or not re.fullmatch(r"Release v\d+(?:\.\d+)+\S*", title.group(1).strip().strip("'\"")):
        say(1, "front-matter", 'front matter must set title: "Release v<version>"')

    seen, header, in_fence = set(), None, False
    for n, line in enumerate(lines, 1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if line.startswith("# "):
            h = line[2:].strip().lower()
            seen |= {k for k, alts in SECTIONS.items() if h in alts}
        for hit in PLACEHOLDER.findall(re.sub(r"`[^`]*`", "", line)):
            say(n, "placeholder", f"template text left in: {hit}")
        if NO_SHOT.search(line):
            say(n, "no-shot", "drop the picture table and show other evidence instead of saying there is no shot")
        if SECRET.search(line):
            say(n, "secret", "a password is written in the report; name the account and role only")
        for src in IMAGE.findall(line):
            if not src.startswith(("http:", "https:", "data:")) and not (base / src).is_file():
                say(n, "image", f"{src} not found next to the report")

        # test case tables: the header carries Expected Result
        if not line.lstrip().startswith("|"):
            header = None
            continue
        row = cells(line)
        if re.fullmatch(r"[\s|:-]+", line):
            continue
        if "Expected Result" in row:
            header = {c: i for i, c in enumerate(row)}
            continue
        if header:
            def col(key):
                i = header.get(key)
                return row[i] if i is not None and i < len(row) else ""
            if VAGUE.fullmatch(col("Expected Result")):
                say(n, "expected", f"{row[0]}: Expected Result must be checkable (a number, a count, the text on screen, a timing)")
            if col("Actual Result") or col("Status"):
                say(n, "qa-columns", f"{row[0]}: leave Actual Result and Status blank for QA")

    for key in SECTIONS:
        if key not in seen:
            say(1, "sections", f'missing page: "# {key}"')
    return out


def selftest() -> None:
    good = """---
title: Release v1.4.0
author: ทดสอบ นามสมมุติ
date: 01/02/2026
---

# Overview

v1.4.0 is ready for staging.

# BA Decision

none open

# Change details

| Before | After |
|---|---|
| ![a](img/a.png) list was empty | ![b](img/b.png) 2 rows |

# Test plan

| TC | Ticket | Test Case | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|
| R01-01 | KEY-101 | open the list | 2 rows: KEY-1, KEY-2 | | |
"""
    with tempfile.TemporaryDirectory() as d:
        base = Path(d)
        (base / "img").mkdir()
        for f in ("a.png", "b.png"):
            (base / "img" / f).write_bytes(b"x")
        assert check(good, base) == [], check(good, base)

        def rules(text):
            return sorted({f.split(": ")[1] for f in check(text, base)})

        assert rules(good.replace("Release v1.4.0", "Release notes")) == ["front-matter"]
        assert rules(good.replace("# BA Decision", "# Questions")) == ["sections"]
        assert rules(good.replace("staging.", "staging on DD/MM/YYYY.")) == ["placeholder"]
        assert rules(good.replace("2 rows |\n", "ยังไม่มีภาพ |\n", 1)) == ["no-shot"]
        assert rules(good.replace("img/b.png", "img/missing.png")) == ["image"]
        assert rules(good.replace("2 rows: KEY-1, KEY-2", "เหมือนเดิม")) == ["expected"]
        assert rules(good.replace("2 rows: KEY-1, KEY-2 | | |", "2 rows | 2 rows | PASS |")) == ["qa-columns"]
        assert rules(good.replace("ready for staging.", "ready, password: hunter2")) == ["secret"]
        assert rules(good + "\n```\n<not a placeholder in code>\n```\n") == []
        assert rules(good.replace("staging.", "staging, `<tag>` in code.")) == []
        assert rules(good.replace("staging.", "staging<br>today.")) == []
        assert rules(good.replace("staging.", "<staging|production>.")) == ["placeholder"]
    print("selftest ok")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("report", nargs="?", type=Path)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    if not a.report:
        ap.error("report .md required")
    found = check(a.report.read_text(encoding="utf-8"), a.report.resolve().parent, str(a.report))
    print("\n".join(found) or f"{a.report}: ok")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
