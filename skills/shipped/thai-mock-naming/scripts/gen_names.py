#!/usr/bin/env python3
"""Generate Thai mock names that are unmistakably fake.

Every generated given name carries a test marker, so a record is legible as
fabricated even when the surname is truncated away.

    python3 gen_names.py --count 10 --format table
    python3 gen_names.py --count 50 --format sql --table users --seed 42
    python3 gen_names.py --roles --format json
    python3 gen_names.py --edge-cases --format json
    python3 gen_names.py --count 5 --with-id --with-contact --format table

No third-party dependencies. Python 3.8+.
"""

import argparse
import csv
import io
import json
import random
import re
import sys

# ---------------------------------------------------------------- token banks

GIVEN_MARKERS = [
    "ทดสอบ",
    "ตัวอย่าง",
    "ทดลอง",
    "สมมุติ",
    "นำร่อง",
    "ชั่วคราว",
    "สาธิต",
]

SURNAME_MARKERS = [
    "นามสมมุติ",
    "ข้อมูลจำลอง",
    "นามทดสอบ",
    "มิใช่บุคคลจริง",
    "ตัวอย่างสกุล",
    "ระบบทดสอบ",
]

ROLES = [
    "ผู้ยื่นคำขอ",
    "ผู้อนุมัติ",
    "ผู้ตรวจสอบ",
    "ผู้ดูแลระบบ",
    "เจ้าหน้าที่รัฐ",
    "ผู้ประกอบการ",
    "ผู้รับมอบอำนาจ",
    "ผู้ใช้ทั่วไป",
]

# (title, given-name suffix) — suffix is appended to the marker
TITLES = [
    ("นาย", "ชาย"),
    ("นาง", "หญิง"),
    ("นางสาว", "หญิง"),
    ("เด็กชาย", "เล็ก"),
    ("เด็กหญิง", "เล็ก"),
]

COMPANY_FORMS = [
    "บริษัท {} จำกัด",
    "บริษัท {} จำกัด (มหาชน)",
    "ห้างหุ้นส่วนจำกัด {}",
    "ห้างหุ้นส่วนสามัญ {}",
    "ร้าน{}",
]

COMPANY_STEMS = [
    "ทดสอบระบบ",
    "ตัวอย่างข้อมูล",
    "นามสมมุติการค้า",
    "ทดสอบพาณิชย์",
    "สาธิตอุตสาหกรรม",
    "ทดลองการช่าง",
]

THAI_DIGITS = "๐๑๒๓๔๕๖๗๘๙"


def to_thai_digits(s):
    return "".join(THAI_DIGITS[int(c)] if c.isdigit() else c for c in str(s))


# ------------------------------------------------------------------ edge cases

EDGE_CASES = [
    ("ก", "ข", "minimum length — single character each"),
    ("ทด", "สอบ", "two-character names, legal in Thai"),
    ("ทดสอบ", "นามสมมุติ", "baseline"),
    ("ทดสอบกิตติ์", "นามสมมุติ ณ ทดสอบ", "การันต์ mark + surname containing spaces"),
    ("ทดสอบฤทธิ์", "เครื่องหมายซ้อนชั้น", "ฤ character + stacked vowel/tone marks"),
    ("ทดสอบรำ", "นามสมมุติ", "sara am — one char, two glyph parts"),
    (
        "ทดสอบความยาวของชื่อที่มากเกินปกติ",
        "มิใช่บุคคลจริงนามสกุลยาวมากเกินกำหนด",
        "long unbroken Thai token — no space to wrap at",
    ),
    ("ทดสอบ Test-นามสมมุติ", "นามสมมุติ", "mixed Thai/Latin script"),
    ("เทดสอบ", "แนามสมมุติ", "leading vowels — stored before, pronounced after"),
    ("ทดสอบ๑๒๓", "นามสมมุติ", "Thai numerals inside a name field"),
    ("ทดสอบ​ใน", "นามสมมุติ", "contains U+200B zero-width space"),
    (" ทดสอบ ", " นามสมมุติ ", "leading and trailing whitespace"),
]


# ------------------------------------------------------- national ID utilities


def id_check_digit(first12):
    """Return the correct 13th digit for a Thai national ID."""
    total = sum(int(first12[i]) * (13 - i) for i in range(12))
    return (11 - (total % 11)) % 10


def is_valid_thai_id(digits):
    """True if a 13-digit string has a correct check digit."""
    d = "".join(ch for ch in str(digits) if ch.isdigit())
    if len(d) != 13:
        return False
    return int(d[12]) == id_check_digit(d[:12])


def make_invalid_id(rng, prefix="0"):
    """A 13-digit ID whose check digit is deliberately wrong.

    Keeps the real format so masks and validators still fire, but can never
    match a real citizen. Uses an unissued leading digit as a second guard.
    """
    body = prefix + "".join(str(rng.randint(0, 9)) for _ in range(11))
    correct = id_check_digit(body)
    wrong = (correct + rng.randint(1, 9)) % 10
    return body + str(wrong)


def format_id(d):
    return "{} {} {} {} {}".format(d[0], d[1:5], d[5:10], d[10:12], d[12])


# ----------------------------------------------------------------- generation


def gen_people(count, rng, use_roles=False, use_titles=False,
               thai_digits=False, with_id=False, with_contact=False):
    rows = []
    for i in range(1, count + 1):
        title = ""
        given = rng.choice(GIVEN_MARKERS)

        if use_titles:
            title, suffix = TITLES[(i - 1) % len(TITLES)]
            given = given + suffix

        if use_roles:
            surname = ROLES[(i - 1) % len(ROLES)]
        else:
            idx = "{:03d}".format(i)
            if thai_digits:
                idx = to_thai_digits(idx)
            base = rng.choice(SURNAME_MARKERS)
            surname = base + idx if count > 1 else base

        row = {"index": i, "title": title, "given_name": given,
               "surname": surname,
               "full_name": " ".join(p for p in (title, given, surname) if p)}

        if with_id:
            nid = make_invalid_id(rng, prefix=rng.choice("09"))
            row["national_id"] = nid
            row["national_id_formatted"] = format_id(nid)

        if with_contact:
            row["email"] = "mock{:03d}@example.com".format(i)
            row["phone"] = "0{}0000{:04d}".format(rng.choice("689"), i)

        rows.append(row)
    return rows


def gen_companies(count, rng):
    rows = []
    for i in range(1, count + 1):
        form = COMPANY_FORMS[(i - 1) % len(COMPANY_FORMS)]
        stem = rng.choice(COMPANY_STEMS)
        rows.append({"index": i, "name": form.format(stem)})
    return rows


def gen_edge_cases():
    return [
        {"index": i, "title": "", "given_name": g, "surname": s,
         "full_name": "{} {}".format(g, s), "note": note}
        for i, (g, s, note) in enumerate(EDGE_CASES, 1)
    ]


# -------------------------------------------------------------------- output


def emit_table(rows):
    if not rows:
        return ""
    cols = list(rows[0].keys())
    widths = {c: max(len(c), *(_dwidth(str(r.get(c, ""))) for r in rows)) for c in cols}
    out = []
    out.append("  ".join(c.ljust(widths[c]) for c in cols))
    out.append("  ".join("-" * widths[c] for c in cols))
    for r in rows:
        out.append("  ".join(
            _pad(str(r.get(c, "")), widths[c]) for c in cols))
    return "\n".join(out)


def _dwidth(s):
    """Thai combining marks take no column width in a terminal."""
    return sum(0 if _combining(ch) else 1 for ch in s)


def _combining(ch):
    o = ord(ch)
    # Thai above/below vowels and tone marks, plus ZWSP
    return (o == 0x0E31 or 0x0E34 <= o <= 0x0E3A or 0x0E47 <= o <= 0x0E4E
            or o == 0x200B)


def _pad(s, w):
    return s + " " * max(0, w - _dwidth(s))


def emit_json(rows):
    return json.dumps(rows, ensure_ascii=False, indent=2)


def emit_csv(rows):
    if not rows:
        return ""
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue().rstrip("\n")


# A SQL identifier: a bare name, or schema-qualified. Anything else is
# rejected rather than escaped — this tool builds statements as text, so the
# table name must never be able to carry syntax of its own.
SQL_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)?$")


def quote_sql_identifier(name):
    """Validate a table or column name, or raise ValueError."""
    if not SQL_IDENT.match(str(name)):
        raise ValueError(
            "unsafe SQL identifier: {!r} (expected letters, digits and "
            "underscores, optionally schema-qualified)".format(name))
    return str(name)


def quote_sql_literal(value):
    """Quote a value as a SQL string literal.

    Doubles single quotes per the SQL standard and drops NUL, which no
    engine accepts inside a literal. Backslash is left alone: it is not an
    escape character in standard SQL, and doubling it would corrupt the data
    on PostgreSQL. On MySQL, run with NO_BACKSLASH_ESCAPES or import the CSV
    output instead.
    """
    text = str(value).replace("\x00", "")
    return "'" + text.replace("'", "''") + "'"


def emit_sql(rows, table):
    if not rows:
        return ""
    table = quote_sql_identifier(table)
    cols = [quote_sql_identifier(c) for c in rows[0] if c != "note"]
    col_list = ", ".join(cols)
    lines = []
    for r in rows:
        vals = ", ".join(quote_sql_literal(r.get(c, "")) for c in cols)
        # Identifiers are validated above and values are quoted literals.
        stmt = "INSERT INTO {} ({}) VALUES ({});".format(table, col_list, vals)  # noqa: S608  # nosec B608  # NOSONAR - identifiers validated, values quoted
        lines.append(stmt)
    return "\n".join(lines)


EMITTERS = {"table": emit_table, "json": emit_json, "csv": emit_csv}


# ---------------------------------------------------------------------- main


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Generate unmistakably-fake Thai names for mock data.")
    p.add_argument("--count", "-n", type=int, default=5,
                   help="how many records (default 5)")
    p.add_argument("--format", "-f", default="table",
                   choices=["table", "json", "csv", "sql"])
    p.add_argument("--table", default="users",
                   help="table name for --format sql (default: users)")
    p.add_argument("--seed", type=int, default=None,
                   help="fix the RNG so output is reproducible")
    p.add_argument("--roles", action="store_true",
                   help="use role surnames (ผู้ยื่นคำขอ, ผู้อนุมัติ, ...)")
    p.add_argument("--titles", action="store_true",
                   help="include คำนำหน้า and gendered given names")
    p.add_argument("--thai-digits", action="store_true",
                   help="index with Thai numerals (๐๑๒) instead of Arabic")
    p.add_argument("--with-id", action="store_true",
                   help="add a national ID with a deliberately invalid checksum")
    p.add_argument("--with-contact", action="store_true",
                   help="add a reserved-domain email and an all-zeros phone")
    p.add_argument("--companies", action="store_true",
                   help="generate juristic person names instead of people")
    p.add_argument("--edge-cases", action="store_true",
                   help="emit the QA stress-test set instead of normal names")
    args = p.parse_args(argv)

    # A seedable PRNG is the correct choice here, not a weakness. Everything
    # this tool emits is deliberately fake and deliberately public, and
    # `--seed` exists so regenerating a fixture produces a stable diff rather
    # than churn. `secrets` would make that impossible and protects nothing:
    # there is no secret to protect in a row that announces itself as a test
    # record. Security scanners flag the import on sight, hence the markers.
    rng = random.Random(args.seed)  # noqa: S311  # nosec B311  # NOSONAR - mock data

    if args.edge_cases:
        rows = gen_edge_cases()
    elif args.companies:
        rows = gen_companies(args.count, rng)
    else:
        rows = gen_people(args.count, rng, use_roles=args.roles,
                          use_titles=args.titles, thai_digits=args.thai_digits,
                          with_id=args.with_id, with_contact=args.with_contact)

    if args.format == "sql":
        try:
            out = emit_sql(rows, args.table)
        except ValueError as exc:
            p.error(str(exc))  # exits 2 with a clean message, no traceback
        print(out)
    else:
        print(EMITTERS[args.format](rows))

    return 0


if __name__ == "__main__":
    sys.exit(main())
