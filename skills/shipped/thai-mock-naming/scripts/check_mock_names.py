#!/usr/bin/env python3
"""Scan a codebase for plausible-real Thai names used as mock data.

Reports file, line, column and the offending token, and exits non-zero when
anything is found — drop it into a pre-commit hook or a CI step.

    python3 check_mock_names.py path/to/seeds/
    python3 check_mock_names.py .
    python3 check_mock_names.py . --quiet                 # exit code only
    python3 check_mock_names.py . --format json
    python3 check_mock_names.py . --allow สมชาย           # whitelist a token
    python3 check_mock_names.py . --exclude 'docs/**'     # skip paths

Three ways to suppress a known-good hit:

  --exclude GLOB        repeatable, matched against the path
  .mocknamesignore      one glob per line, read from each scan root
  mock-names-ignore     put this marker in a comment on the line itself

No third-party dependencies. Python 3.8+.
"""

import argparse
import fnmatch
import json
import os
import re
import sys

__version__ = "1.0.0"

IGNORE_FILE = ".mocknamesignore"
INLINE_IGNORE = "mock-names-ignore"

# Real, common Thai given names that routinely show up in mock data.
# มานะ / มานี / ปิติ / ชูใจ are the ป.1 primary-reader cast — widely
# recognised, which is exactly why people wrongly assume they are safe.
GIVEN_NAMES = [
    "สมชาย", "สมหญิง", "สมศรี", "สมปอง", "สมพงษ์", "สมบัติ", "สมคิด",
    "สมหมาย", "สมบูรณ์", "มานะ", "มานี", "ปิติ", "ชูใจ", "วีระ", "สุดา",
    "ประเสริฐ", "อนันต์", "จำลอง", "สมพร", "สมจิตร",
]

# Real, common Thai surnames.
SURNAMES = [
    "ใจดี", "พอใจ", "ทองดี", "ศรีสุข", "สุขใจ", "รักเรียน", "ดีงาม",
    "แสงทอง", "รุ่งเรือง", "สว่างวงศ์", "บุญมี", "มีสุข", "ศรีเมือง",
    "ทองคำ", "จันทร์ดี", "แก้วมณี",
]

# Latin-script placeholders that are just as unhelpful in a Thai system.
LATIN = ["John Doe", "Jane Doe", "Foo Bar", "Test Test"]

SUGGESTIONS = {
    "given": "use a marker: ทดสอบ / ตัวอย่าง / ทดลอง / สาธิต",
    "surname": "use a marker: นามสมมุติ / ข้อมูลจำลอง / มิใช่บุคคลจริง, "
               "or a role: ผู้ยื่นคำขอ / ผู้อนุมัติ",
    "latin": "use ทดสอบ นามสมมุติ, or Test Mockname if the field is Latin-only",
}

SKIP_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "vendor", "dist", "build",
    ".next", ".nuxt", "__pycache__", ".venv", "venv", "target",
    ".idea", ".vscode", "coverage", ".mypy_cache", ".pytest_cache",
}

SKIP_EXTS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico", ".pdf",
    ".zip", ".gz", ".tar", ".bz2", ".xz", ".7z", ".rar",
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
    ".mp3", ".mp4", ".mov", ".avi", ".webm", ".wav",
    ".so", ".dylib", ".dll", ".exe", ".bin", ".class", ".jar",
    ".lock", ".pyc", ".pdb",
}

MAX_BYTES = 4 * 1024 * 1024


# Thai has no word separators, so substring matching produces false positives:
# `จำลอง` is a real given name AND the tail of the approved marker `ข้อมูลจำลอง`.
# Instead of matching substrings, split each line into maximal Thai runs and
# judge the run as a whole.

THAI_RUN = re.compile(r"[ก-ฺเ-๎]+")


def decompose(run, blocked):
    """Split a Thai run into blocked tokens, or return None.

    Returns a list of (offset, token, kind) if the ENTIRE run is made of
    blocked names — `สมชาย` alone, or `สมชายใจดี` concatenated. Returns None
    if any part of the run is something else, which means the blocked token
    is embedded in an ordinary Thai word and is not being used as a name.
    """
    out = []
    i = 0
    while i < len(run):
        for length in range(len(run) - i, 0, -1):
            cand = run[i:i + length]
            if cand in blocked:
                out.append((i, cand, blocked[cand]))
                i += length
                break
        else:
            return None
    return out or None


def find_thai(line, blocked):
    """Yield (column, token, kind) for blocked Thai names used as names."""
    for m in THAI_RUN.finditer(line):
        parts = decompose(m.group(0), blocked)
        if not parts:
            continue
        for offset, token, kind in parts:
            yield m.start() + offset, token, kind


def build_pattern(tokens):
    if not tokens:
        return None
    return re.compile("|".join(re.escape(t) for t in sorted(tokens, key=len, reverse=True)))


def load_ignore_file(root):
    """Read .mocknamesignore from a scan root. One glob per line, # comments."""
    base = root if os.path.isdir(root) else os.path.dirname(root) or "."
    path = os.path.join(base, IGNORE_FILE)
    patterns = []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.split("#", 1)[0].strip()
                if line:
                    patterns.append(line)
    except OSError:
        pass
    return patterns


def is_excluded(path, patterns):
    if not patterns:
        return False
    norm = path.replace(os.sep, "/").lstrip("./")
    for pat in patterns:
        p = pat.replace(os.sep, "/").lstrip("./")
        if fnmatch.fnmatch(norm, p) or fnmatch.fnmatch(os.path.basename(norm), p):
            return True
        # a bare directory pattern excludes everything under it
        if norm.startswith(p.rstrip("/") + "/"):
            return True
    return False


def iter_files(root, exclude):
    if os.path.isfile(root):
        if not is_excluded(root, exclude):
            yield root
        return
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames
                       if d not in SKIP_DIRS
                       and not is_excluded(os.path.join(dirpath, d), exclude)]
        for fn in filenames:
            if os.path.splitext(fn)[1].lower() in SKIP_EXTS:
                continue
            path = os.path.join(dirpath, fn)
            if is_excluded(path, exclude):
                continue
            try:
                if os.path.getsize(path) > MAX_BYTES:
                    continue
            except OSError:
                continue
            yield path


def scan_file(path, blocked, latin_pat):
    findings = []
    try:
        with open(path, "r", encoding="utf-8", errors="strict") as fh:
            for lineno, line in enumerate(fh, 1):
                if "\0" in line:
                    return []
                if INLINE_IGNORE in line:
                    continue
                hits = [(col, tok, kind)
                        for col, tok, kind in find_thai(line, blocked)]
                if latin_pat is not None:
                    hits += [(m.start(), m.group(0), "latin")
                             for m in latin_pat.finditer(line)]
                for col, tok, kind in sorted(hits):
                    findings.append({
                        "file": path,
                        "line": lineno,
                        "column": col + 1,
                        "token": tok,
                        "kind": kind,
                        "suggestion": SUGGESTIONS[kind],
                        "context": line.strip()[:120],
                    })
    except (UnicodeDecodeError, OSError):
        return []
    return findings


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Flag plausible-real Thai names used as mock data.")
    p.add_argument("paths", nargs="*", default=["."],
                   help="files or directories to scan (default: .)")
    p.add_argument("--quiet", "-q", action="store_true",
                   help="print nothing; signal via exit code only")
    p.add_argument("--format", "-f", default="text", choices=["text", "json"])
    p.add_argument("--allow", action="append", default=[],
                   help="token to ignore; repeatable")
    p.add_argument("--exclude", action="append", default=[],
                   help="glob of paths to skip; repeatable")
    p.add_argument("--no-ignore-file", action="store_true",
                   help="do not read .mocknamesignore")
    p.add_argument("--version", action="version",
                   version="check_mock_names {}".format(__version__))
    args = p.parse_args(argv)

    allow = set(args.allow)
    blocked = {}
    for t in GIVEN_NAMES:
        if t not in allow:
            blocked[t] = "given"
    for t in SURNAMES:
        if t not in allow:
            blocked.setdefault(t, "surname")
    latin_pat = build_pattern([t for t in LATIN if t not in allow])

    findings = []
    for root in (args.paths or ["."]):
        exclude = list(args.exclude)
        if not args.no_ignore_file:
            exclude += load_ignore_file(root)
        for path in iter_files(root, exclude):
            findings.extend(scan_file(path, blocked, latin_pat))

    if args.quiet:
        return 1 if findings else 0

    if args.format == "json":
        print(json.dumps(findings, ensure_ascii=False, indent=2))
        return 1 if findings else 0

    if not findings:
        print("No plausible-real Thai mock names found.")
        return 0

    by_file = {}
    for f in findings:
        by_file.setdefault(f["file"], []).append(f)

    for path in sorted(by_file):
        print("\n{}".format(path))
        for f in by_file[path]:
            print("  {}:{}  {}  ({})".format(
                f["line"], f["column"], f["token"], f["kind"]))
            print("      {}".format(f["context"]))
            print("      → {}".format(f["suggestion"]))

    files = len(by_file)
    print("\n{} finding{} in {} file{}.".format(
        len(findings), "" if len(findings) == 1 else "s",
        files, "" if files == 1 else "s"))
    print("These are real Thai names. Replace them with marker names so test "
          "records stay greppable and screenshots stay unambiguous.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
