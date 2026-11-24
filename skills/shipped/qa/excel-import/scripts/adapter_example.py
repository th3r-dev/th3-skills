"""Adapter contract for run_web.py — copy this file next to your cases.json and fill it in.

run_web.py loads it with `--adapter path/to/adapter.py`. It must expose:

  BASE          default portal base URL (overridable with --base)
  ACCOUNTS      {account name: company/tenant id} — the id the cases' "company" field uses
  LOGIN_PATH    path of the login page (default "/login")
  VALIDATE_URL  substring of the import validate request URL
  SUBMIT_URL    substring of the import submit request URL

  read(xlsx) -> (headers, header_values, rows)      the file the way the importer sees it
  check(con, company, xlsx) -> (status, errors, detail_count)
                                                    replay the importer's validator against the DB
  connect() -> connection                           DB handle (must refuse prod)
  tenant_name(cur, company) -> str                  the name the signed-in page shows for that tenant
  open_import(page, base)                           navigate to the import modal (sys.exit on /login)
  web_validate(page, xlsx) -> dict                  upload the file, return the validate JSON body
  web_submit(page) -> dict                          confirm, return the submit JSON body
  web_errors(body) -> list[str]                     flatten the validate body's errors
  web_status(body) -> (status, detail_count)        the two fields compare() looks at
  submit_status(body) -> (status, document_id)      from the submit body
  receipt_of(xlsx) -> str                           the natural key a re-submit must be refused on
  already_imported(cur, company, receipt) -> id|None
  db_verify(cur, document_id, company, xlsx) -> (found: dict|None, mismatches: list[str])

The example below is a sketch for a template whose header sits in B1:B7, data starts at row 10, and a
tenant-scoped validator with three stages (required cells → qty > 0 → DB lookups). Replace every
query and selector with your importer's. Keep the rule "stage 3 runs only when stage 2 is clean" if
your importer does the same, or the expected errors will never match.
"""
from __future__ import annotations

import re
import sys

BASE = "https://app.example.com"
ACCOUNTS = {"acme": 1, "globex": 2}
LOGIN_PATH = "/login"
VALIDATE_URL = "/import/validate"
SUBMIT_URL = "/import/submit"

REQUIRED = [0, 1, 2, 5]                 # 0-based column indexes that must not be blank
HEADERS = ["Product", "Code", "Tax code", "Tank", "Meter", "Quantity", "Customer code", "Form type"]
HEADER_LABELS = ["Document date", "Movement", "Transport", "Receipt no"]
QTY = 5


def norm(s) -> str:
    return re.sub(r"\s+", "", str(s if s is not None else "")).upper()


def text(v) -> str:
    return "" if v is None else str(v).strip()


def read(path):
    from openpyxl import load_workbook
    ws = load_workbook(path, data_only=True).worksheets[0]
    hdr = [text(ws.cell(i + 1, 2).value) for i in range(len(HEADER_LABELS))]
    heads = [text(ws.cell(9, c + 1).value) for c in range(len(HEADERS))]
    rows = []
    for r in range(10, 5010):
        vals = [text(ws.cell(r, c + 1).value) for c in range(len(HEADERS))]
        if not any(vals):
            break
        rows.append((r, vals))
    return heads, hdr, rows


def check(con, company, path):
    heads, hdr, rows = read(path)
    if [norm(h) for h in heads] != [norm(h) for h in HEADERS]:
        return "TEMPLATE_ERROR", ["header row does not match the template"], 0
    errs = []
    for i, lbl in enumerate(HEADER_LABELS[:3]):
        if not hdr[i]:
            errs.append(f"{lbl} is required")
    if not rows:
        errs.append("no detail rows")
    for r, v in rows:
        errs += [f"row {r}: {HEADERS[i]} is required" for i in REQUIRED if not v[i]]
        try:
            ok = float(v[QTY].replace(",", "")) > 0
        except ValueError:
            ok = False
        if not ok:
            errs.append(f"row {r}: quantity must be a number greater than 0")
    if errs:  # stage 3 never runs while stage 2 has an error
        return "VALIDATION_ERROR", errs, 0
    cur = con.cursor()
    groups = {}
    for r, v in rows:  # one detail per distinct (code, tax code, form type); errors land on the group's first row
        groups.setdefault((norm(v[1]), norm(v[2]), norm(v[7])), []).append((r, v))
    for grp in groups.values():
        r, v = grp[0]
        if not cur.execute("select 1 from product where code = :c", c=norm(v[1])).fetchone():
            errs.append(f"row {r}: product {v[1]} not found")
        if not cur.execute("select 1 from tank where tenant_id = :t and code = :c", t=company, c=norm(v[3])).fetchone():
            errs.append(f"row {r}: tank {v[3]} not in this tenant")
    return ("VALIDATED" if not errs else "VALIDATION_ERROR"), errs, len(groups)


def connect():
    """Return a DB-API connection to the TEST database. Refuse anything that looks like prod."""
    raise NotImplementedError("connect(): open your test DB here and sys.exit() if it looks like prod")


def tenant_name(cur, company):
    return cur.execute("select name from tenant where id = :i", i=company).fetchone()[0]


def open_import(page, base):
    page.goto(f"{base}/documents")
    page.wait_for_load_state("networkidle")
    if LOGIN_PATH in page.url:
        sys.exit("session expired -- rerun: run_web.py login --account <account>")
    page.get_by_role("button", name=re.compile(r"^\s*Import\s*$")).click()
    page.get_by_text("Import documents").first.wait_for()


def web_validate(page, xlsx):
    with page.expect_response(lambda r: VALIDATE_URL in r.url, timeout=120_000) as info:
        page.locator("input[type=file]").set_input_files(str(xlsx))
    return info.value.json()


def web_submit(page):
    page.get_by_role("button", name="Confirm import").last.click()      # modal footer
    with page.expect_response(lambda r: SUBMIT_URL in r.url, timeout=180_000) as info:
        page.get_by_role("button", name="Confirm import").last.click()  # confirm dialog
    body = info.value.json()
    ok = page.get_by_role("button", name="OK")
    ok.wait_for(timeout=30_000)
    ok.click()
    return body


def web_errors(body):
    d = body.get("data") or {}
    errs = list(d.get("errors") or [])
    for r in d.get("rows") or []:
        errs += [f"row {r.get('rowNo')}: {e}" for e in r.get("errors") or []]
    return errs


def web_status(body):
    return body.get("status"), (body.get("data") or {}).get("detailCount")


def submit_status(body):
    d = body.get("data") or {}
    return body.get("status"), d.get("documentId")


def receipt_of(xlsx):
    return read(xlsx)[1][3]


def already_imported(cur, company, receipt):
    row = cur.execute("select id from document where tenant_id = :t and receipt_no = :r and deleted = 0",
                      t=company, r=receipt).fetchone()
    return row[0] if row else None


def db_verify(cur, document_id, company, xlsx):
    _, _, rows = read(xlsx)
    want_qty = sum(float(v[QTY].replace(",", "")) for _, v in rows)
    h = cur.execute("select id, tenant_id from document where id = :i and deleted = 0", i=document_id).fetchone()
    if not h:
        return None, [f"document {document_id} not found"]
    n, qty = cur.execute("select count(*), sum(quantity) from document_detail where document_id = :i and deleted = 0",
                         i=document_id).fetchone()
    bad = []
    if h[1] != company:
        bad.append(f"tenant {h[1]} != {company}")
    if abs(float(qty or 0) - want_qty) > 0.001:
        bad.append(f"quantity {qty} != {want_qty}")
    return dict(headerId=h[0], details=n, volume=float(qty or 0)), bad
