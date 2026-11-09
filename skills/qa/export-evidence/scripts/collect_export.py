# /// script
# requires-python = ">=3.10"
# dependencies = ["playwright", "openpyxl", "pypdf", "pymupdf"]
# ///
"""Walk export-button cases on a signed-in CDP Chrome and write the evidence folder make_qa_report.py reads.

One case = one page x one format. Each case gets screenshots/NN-*.png + steps.csv + run.json + the
downloaded file; one failing case never stops the rest. index.csv + environment.csv are rebuilt
from every run.json after each case, so re-running one slug keeps the others.

    uv run collect_export.py cases.json <evidence dir> [slug ...] [--cdp http://127.0.0.1:9222]
    uv run collect_export.py cases.json <evidence dir> --index-only      # notes changed: rewrite index.csv, no browser

cases.json:
{
  "env":  {"key": "value", ...},                 # shown on the report's Summary sheet
  "ui":   {...},                                 # optional overrides of UI words, see DEFAULT_UI
  "cases": [ {
    "no": 1, "slug": "daily-receive-excel", "title": "Daily receive report · Excel",
    "sheet": "blue app export excel",            # group name (--only-sheets in the builder)
    "url": "https://<host>/reports/daily-receive",
    "kind": "auto" | "stimulsoft",               # auto: a download = direct, an alert + POST enqueue = queue
    "format": "csv" | "excel" | "pdf",
    "pre": [                                     # optional filter actions; one with "caption" gets its own step
      {"fill": "<css/xpath>", "value": "10/10/2026", "enter": true, "escape": true, "caption": "pick a date", "id": "fill-filter"},
      {"click": "Search", "role": "button|link|text", "caption": "press Search", "id": "query-result", "count": true}],
    "dates": ["01/10/2026", "27/10/2026"],       # optional: typed into the date inputs (ui.date_placeholder)
    "query": "Load data",                         # optional: button pressed after the filter
    "select_rows": 2,                             # optional: tick N row checkboxes first
    "button": "Export Excel",                     # optional regex; default per format: CSV / Excel / PDF|Print
    "menu_item": "Adobe PDF",                     # optional: menu entry clicked after the button
    "open": "Print",                              # stimulsoft only: the row button that opens the viewer
    "queue_wait": 600,                            # optional seconds to wait for the queue job (default 300)
    "note": "...",                                # optional; becomes the case's Actual Result text
    "folder": "01_daily-receive-excel"            # optional evidence folder name (default NN_slug)
  } ]
}

Run ONE collector at a time: each CDP client sets Chrome's download behaviour, so a second client
sends the first one's downloads to ~/Downloads and leaves it a 0-byte copy.

The collector clicks only: filter inputs, the query button, row checkboxes, the export button, the
"queued" alert's OK, and the queue modal's refresh / download. Nothing that saves or submits.
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import os
import re
import shutil
import sys
import time
from datetime import date
from pathlib import Path

def inside_work(p, what="path"):
    """CLI paths come from an agent, so this script only reads and writes inside the folder it runs from."""
    root = os.path.realpath(os.getcwd())
    full = os.path.realpath(os.path.join(root, os.path.expanduser(str(p))))
    if full != root and not full.startswith(root + os.sep):
        raise SystemExit(f"{what} {p!r} is outside the working folder {root}; run the script from that folder")
    return full


DEFAULT_BUTTON = {"csv": r"CSV", "excel": r"Excel", "pdf": r"PDF|Print"}
EXT = {"csv": ".csv", "excel": ".xlsx", "pdf": ".pdf"}
DEFAULT_UI = {  # override any of these in cases.json "ui"
    "enqueue_path": "/report-export",          # POST that puts an export job on the queue
    "export_path": "/export",                   # direct-download GET
    "date_placeholder": "วว/ดด/ปปปป",            # placeholder of the date inputs used by "dates"
    "rows_regex": r"(?:of|จากทั้งหมด)\s*([\d,]+)\s*(?:rows|items|แถว|รายการ)",
    "alert": ".swal2-popup", "alert_ok": ".swal2-confirm",
    "modal": ".modal.show", "modal_close": ".modal.show .btn-close",
    "refresh": r"Refresh|รีเฟรช",
    "success_words": ["success", "สำเร็จ"],
    "failure_words": ["fail", "ไม่สำเร็จ", "ล้มเหลว", "error"],
    "viewer_save": "Save", "viewer_menu_item": "Adobe PDF", "viewer_settings": "Export Settings",
    "captions": {  # step captions in the report; keep them in the team's language
        "open-page": "open the page", "fill-filter": "fill the date range", "query-result": "press the query button",
        "select-rows": "select rows", "export-button": "export button", "queued-alert": "button → queued",
        "queue-success": "export queue", "downloaded-file": "open the downloaded file",
        "viewer-button": "first row's print button", "viewer": "document viewer", "save-menu": "Save menu",
        "export-form": "export settings → OK", "no-response": "nothing happened after the click",
        "alert": "an alert appeared", "error": "stopped midway",
        "pass_text": "exported ({detail})", "fail_text": "export failed: {reason}",
        "empty_file": "empty file (0 bytes)", "not_pdf": "not a PDF", "not_xlsx": "not an xlsx",
        "pages": "pages", "sheets": "sheets", "rows": "rows with values", "on_screen": "on screen {n} rows",
    },
}


def deep_merge(base: dict, over: dict) -> dict:
    out = dict(base)
    for k, v in (over or {}).items():
        out[k] = deep_merge(base[k], v) if isinstance(v, dict) and isinstance(base.get(k), dict) else v
    return out


def mark(loc):
    loc.evaluate("el => { el.style.setProperty('outline', '4px solid #e11d48', 'important'); "
                 "el.style.setProperty('outline-offset', '2px', 'important'); "
                 "el.style.setProperty('box-shadow', '0 0 0 6px rgba(225,29,72,.35)', 'important'); }")


def table_png(ctx, title, info, rows, shot):
    e = html.escape
    tab = ctx.new_page()
    tab.set_viewport_size({"width": 1440, "height": 900})
    body = "".join("<tr>" + "".join(f"<td>{e('' if c is None else str(c))}</td>" for c in r) + "</tr>" for r in rows[:20])
    tab.set_content(f"""<!doctype html><meta charset="utf-8"><style>body{{font:14px system-ui,sans-serif;margin:24px}}
table{{border-collapse:collapse}}td{{border:1px solid #bbb;padding:4px 8px;white-space:nowrap;max-width:360px;overflow:hidden}}
tr:first-child td{{background:#005487;color:#fff}}</style><div id=f style="display:inline-block;padding:4px">
<h3>{e(title)}</h3><p>{e(info)}</p><table>{body}</table></div>""")
    tab.locator("#f").screenshot(path=str(shot))
    tab.close()


def status_words(text: str, ui: dict):
    low = text.lower()
    failed = any(w.lower() in low for w in ui["failure_words"])
    done = (not failed) and any(w.lower() in low for w in ui["success_words"])
    return done, failed


def verify(ctx, f: Path, fmt: str, shot: Path, cap: dict):
    """open the file with a real parser; returns (ok, detail) and writes the preview PNG"""
    raw = f.read_bytes()
    if not raw:
        return False, cap["empty_file"]
    if fmt == "pdf":
        from pypdf import PdfReader
        import pymupdf as fitz
        if not raw.startswith(b"%PDF"):
            return False, f"{cap['not_pdf']} ({raw[:8]!r})"
        n = len(PdfReader(str(f)).pages)
        doc = fitz.open(str(f))
        doc[0].get_pixmap(dpi=110).save(str(shot))
        doc.close()
        return n > 0, f"{f.name} · PDF {n} {cap['pages']} · {len(raw):,} bytes"
    if fmt == "excel":
        from openpyxl import load_workbook
        if not raw.startswith(b"PK"):
            return False, f"{cap['not_xlsx']} ({raw[:8]!r})"
        wb = load_workbook(str(f), read_only=True, data_only=True)
        ws = wb.worksheets[0]
        rows = [list(r) for r in ws.iter_rows(values_only=True) if any(c not in (None, "") for c in r)]
        info = f"{len(raw):,} bytes · {cap['sheets']} {wb.sheetnames} · {len(rows)} {cap['rows']}"
        table_png(ctx, f"📄 {f.name}", info, rows, shot)
        return len(rows) > 0, f"{f.name} · {info}"
    rows = [r for r in csv.reader(raw.decode("utf-8-sig").splitlines()) if any(c.strip() for c in r)]
    info = f"{len(raw):,} bytes · {len(rows)} {cap['rows']}"
    table_png(ctx, f"📄 {f.name}", info, rows, shot)
    return len(rows) > 0, f"{f.name} · {info}"


def save_download(page, dw, d: Path) -> Path:
    """wait for the download, check failure() and size, then copy it in (fallback: GET with the session cookies)."""
    f = d / dw.suggested_filename
    err = dw.failure()  # blocks until finished
    if not err:
        dw.save_as(str(f))
    if (err or not f.exists() or f.stat().st_size == 0) and dw.url.startswith("http"):
        r = page.context.request.get(dw.url, timeout=180_000)
        if r.ok and r.body():
            f.write_bytes(r.body())
    if not f.exists():
        f.write_bytes(b"")
    return f


class Collector:
    def __init__(self, page, ctx, ui: dict):
        self.page, self.ctx, self.ui, self.cap = page, ctx, ui, ui["captions"]

    def rows_on_screen(self):
        m = re.search(self.ui["rows_regex"], self.page.locator("body").inner_text())
        return m.group(1) if m else None

    def do_action(self, a: dict):
        """pre-export filter actions: fill / click / wait — never a save or submit"""
        page = self.page
        if "fill" in a:
            el = page.locator(a["fill"]).nth(a.get("nth", 0))
            el.click()
            el.fill(a["value"])
            if a.get("enter"):
                el.press("Enter")
            if a.get("escape"):
                page.keyboard.press("Escape")
        elif "click" in a:
            role = a.get("role", "button")
            loc = page.get_by_text(re.compile(a["click"])) if role == "text" else page.get_by_role(role, name=re.compile(a["click"]))
            loc.nth(a.get("nth", 0)).click()
            try:
                page.wait_for_load_state("networkidle", timeout=60_000)
            except Exception:
                pass
        if a.get("wait"):
            page.wait_for_timeout(a["wait"])

    def type_date(self, i: int, v: str):
        inp = self.page.get_by_placeholder(self.ui["date_placeholder"]).nth(i)
        inp.click()
        inp.fill(v)
        inp.press("Enter")
        self.page.keyboard.press("Escape")

    def stimulsoft(self, case, steps, shot):
        """document viewer (Stimulsoft): row button -> viewer -> Save -> <menu item> -> settings OK -> download"""
        page, ui, cap = self.page, self.ui, self.cap
        opener = page.get_by_role("button", name=re.compile(case["open"])).first
        opener.scroll_into_view_if_needed()
        mark(opener)
        steps.append(("open-viewer-button", cap["viewer-button"], case["open"], shot("viewer-button"), "PASS"))
        opener.click()
        save = page.get_by_text(ui["viewer_save"], exact=True).first
        save.wait_for(timeout=90_000)
        page.wait_for_timeout(5000)
        steps.append(("viewer", cap["viewer"], "viewer", shot("viewer"), "PASS"))
        mark(save)
        save.click()
        page.wait_for_timeout(800)
        item = page.get_by_text(re.compile(case.get("menu_item", ui["viewer_menu_item"]))).first
        mark(item)
        steps.append(("save-menu", cap["save-menu"], "-", shot("save-menu"), "PASS"))
        got = []
        page.on("download", got.append)
        item.click()
        deadline = time.time() + 120
        while time.time() < deadline and not got:
            ok = page.locator("text=/^\\s*OK\\s*$/ >> visible=true")
            if page.get_by_text(ui["viewer_settings"]).first.is_visible() and ok.count():
                mark(ok.first)
                steps.append(("export-form", cap["export-form"], "-", shot("export-form"), "PASS"))
                ok.first.click()
            page.wait_for_timeout(1000)
        page.remove_listener("download", got.append)
        if not got:
            raise RuntimeError("no download from the viewer's Save menu")
        return got[0]

    def queue_flow(self, net, steps, shot, case):
        page, ui, cap = self.page, self.ui, self.cap
        ok = net.get("enqueue_status") in (200, 201)
        steps.append(("queued-alert", cap["queued-alert"], net.get("enqueue", "?") + " " + net.get("enqueue_error", ""),
                      shot("queued-alert"), "PASS" if ok else "FAIL"))
        if not ok:
            raise RuntimeError(f"enqueue failed: {net.get('enqueue')} {net.get('enqueue_error', '')}")
        page.locator(ui["alert_ok"]).click(timeout=10_000)
        page.locator(ui["alert"]).wait_for(state="hidden", timeout=10_000)
        modal = page.locator(ui["modal"]).last
        modal.wait_for(timeout=30_000)
        row = modal.locator("tbody tr").first
        dl = row.locator("button, a").filter(has=page.locator("svg")).last
        deadline, text = time.time() + case.get("queue_wait", 300), ""
        done = failed = False
        while time.time() < deadline:  # real queue: wait for the job
            try:  # the list re-renders while polling; a miss is just a retry
                text = " ".join(row.inner_text(timeout=10_000).split())
                done, failed = status_words(text, ui)
                if (done and dl.count() and dl.is_enabled()) or failed:
                    break
                rf = modal.get_by_role("button", name=re.compile(ui["refresh"]))
                if rf.count():
                    rf.first.click(timeout=5_000)
            except Exception:
                pass
            page.wait_for_timeout(5000)
        net["queue_row"] = text[:300]
        steps.append(("queue-success", cap["queue-success"], text[:200], shot("queue-modal", modal.locator(".modal-content")),
                      "PASS" if done else "FAIL"))
        if not done:
            raise RuntimeError(f"queue row not success: {text[:200]}")
        mark(dl)
        with page.expect_download(timeout=180_000) as di:
            dl.click()
        return di.value

    def run(self, case: dict, out: Path):
        page, ui, cap = self.page, self.ui, self.cap
        no, slug, fmt = case["no"], case["slug"], case["format"]
        d = out / case.get("folder", f"{no:02d}_{slug}")
        if d.exists():
            shutil.rmtree(d)  # a re-run replaces the case, no stale shots
        (d / "screenshots").mkdir(parents=True, exist_ok=True)
        steps, net = [], {}
        shots = iter(range(1, 99))

        def shot(name, target=None):
            f = d / "screenshots" / f"{next(shots):02d}-{name}.png"
            (target.screenshot(path=str(f)) if target else page.screenshot(path=str(f)))
            return f"screenshots/{f.name}"

        def on_resp(r):
            if ui["enqueue_path"] in r.url and r.request.method == "POST":
                net["enqueue"] = f"POST {r.url.split('?')[0]} → {r.status}"
                net["enqueue_status"] = r.status
                try:
                    net["enqueue_body"] = r.request.post_data_json
                except Exception:
                    pass
                if r.status >= 400:
                    net["enqueue_error"] = r.text()[:500]
            elif ui["export_path"] in r.url and r.request.method == "GET" and r.status >= 400:
                net["export_error"] = f"GET {r.url.split('?')[0]} → {r.status} {r.text()[:300]}"

        page.on("response", on_resp)
        summary = dict(no=no, slug=slug, title=case["title"], sheet=case.get("sheet", ""), format=fmt,
                       kind=case.get("kind", "auto"), url=case["url"])
        try:
            page.goto(case["url"], timeout=90_000)
            page.wait_for_load_state("networkidle", timeout=60_000)
            page.wait_for_timeout(1500)
            steps.append(("open-page", cap["open-page"], case["url"], shot("open-page"), "PASS"))
            for a in case.get("pre", []):
                self.do_action(a)
                if a.get("caption"):
                    page.wait_for_timeout(1000)
                    n = self.rows_on_screen()
                    if n:
                        summary["rows_on_screen"] = n
                    note = a.get("note", a.get("value", "-")) + (f" · {cap['on_screen'].format(n=n)}" if n and a.get("count") else "")
                    steps.append((a.get("id", "filter"), a["caption"], note, shot(a.get("id", "filter")), "PASS"))
            if case.get("dates"):
                for i, v in enumerate(case["dates"]):
                    self.type_date(i, v)
                steps.append(("fill-filter", cap["fill-filter"], " - ".join(case["dates"]), shot("fill-filter"), "PASS"))
            if case.get("query"):
                page.get_by_role("button", name=case["query"]).first.click()
                page.wait_for_load_state("networkidle", timeout=60_000)
                page.wait_for_timeout(1500)
                summary["rows_on_screen"] = self.rows_on_screen() or "?"
                steps.append(("query-result", f'{cap["query-result"]} "{case["query"]}"',
                              cap["on_screen"].format(n=summary["rows_on_screen"]), shot("query-result"), "PASS"))
            if case.get("select_rows"):
                boxes = page.locator("tbody input[type=checkbox]")
                for i in range(min(case["select_rows"], boxes.count())):
                    boxes.nth(i).check()
                steps.append(("select-rows", cap["select-rows"], f"{case['select_rows']}", shot("select-rows"),
                              "PASS" if boxes.count() else "FAIL"))
            if case.get("kind") == "stimulsoft":
                dw = self.stimulsoft(case, steps, shot)
            else:
                btn = page.get_by_role("button", name=re.compile(case.get("button") or DEFAULT_BUTTON[fmt])).first
                btn.scroll_into_view_if_needed()
                mark(btn)
                steps.append(("export-button", cap["export-button"], btn.inner_text().strip(), shot("export-button"),
                              "PASS" if btn.is_enabled() else "FAIL"))
                got = []
                page.on("download", got.append)
                btn.click()
                if case.get("menu_item"):
                    page.get_by_text(re.compile(case["menu_item"])).last.click()
                deadline = time.time() + 240
                alert = page.locator(ui["alert"])
                while time.time() < deadline and not got and not alert.is_visible():
                    page.wait_for_timeout(500)
                page.remove_listener("download", got.append)
                if not got and not alert.is_visible():
                    steps.append(("no-response", cap["no-response"], "no file, no queue job, no alert within 4 min",
                                  shot("no-response"), "FAIL"))
                    raise RuntimeError("click produced no download, no enqueue and no alert")
                if got:
                    dw = got[0]
                    summary["kind"] = "direct"
                else:
                    alert.wait_for(timeout=1_000)
                    page.wait_for_timeout(500)
                    if not net.get("enqueue_status"):  # an alert with no enqueue = an error alert
                        msg = " ".join(alert.inner_text().split())
                        steps.append(("alert", cap["alert"], msg[:200] + " " + net.get("export_error", ""), shot("alert"), "FAIL"))
                        raise RuntimeError(f"alert without download/enqueue: {msg[:200]} {net.get('export_error', '')}")
                    summary["kind"] = "queue"
                    dw = self.queue_flow(net, steps, shot, case)
            f = save_download(page, dw, d)
            pv = d / "screenshots" / f"{next(shots):02d}-downloaded-file.png"
            ok, detail = verify(self.ctx, f, fmt, pv, cap)
            if f.suffix.lower() != EXT[fmt]:
                ok, detail = False, f"extension {f.suffix} is not {EXT[fmt]} · " + detail
            steps.append(("downloaded-file", cap["downloaded-file"], detail, f"screenshots/{pv.name}", "PASS" if ok else "FAIL"))
            summary.update(file=f.name, detail=detail)
            close = page.locator(ui["modal_close"])  # leave the page clean
            if close.count():
                close.first.click()
        except Exception as ex:  # one case failing never stops the batch
            msg = str(ex).splitlines()[0][:300]
            try:
                ev = shot("error")
            except Exception:
                ev = ""
            steps.append(("error", cap["error"], msg, ev, "FAIL"))
            summary["error"] = msg
        finally:
            page.remove_listener("response", on_resp)
        summary["net"] = net
        summary["result"] = "PASS" if steps and all(s[-1] == "PASS" for s in steps) else "FAIL"
        with open(d / "steps.csv", "w", newline="", encoding="utf-8-sig") as fh:
            w = csv.writer(fh)
            w.writerow(["step", "step_id", "action", "input / data", "evidence", "result"])
            for i, s in enumerate(steps, 1):
                w.writerow([i, *s])
        summary["folder"] = d.name
        (d / "run.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{no:02d} {slug}: {summary['result']} {summary.get('detail') or summary.get('error', '')}", flush=True)


def write_index(out: Path, spec: dict, cap: dict):
    """index.csv from every run.json; a case's "note" is prefixed to the Actual Result text (e.g. a FAIL cause)."""
    notes = {c["no"]: c.get("note") for c in spec["cases"]}
    runs = sorted((json.loads(p.read_text(encoding="utf-8")) for p in out.glob("*/run.json")), key=lambda r: r["no"])
    with open(out / "index.csv", "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(["no", "title", "sheet", "format", "kind", "url", "file", "result", "folder", "actual"])
        for r in runs:
            actual = (cap["pass_text"].format(detail=r.get("detail")) if r["result"] == "PASS"
                      else cap["fail_text"].format(reason=r.get("error") or r.get("detail") or "-"))
            if notes.get(r["no"]):
                actual = f"{notes[r['no']]} · {actual}"
            w.writerow([r["no"], r["title"], r["sheet"], r["format"], r["kind"], r["url"], r.get("file", ""),
                        r["result"], r["folder"], actual])
    with open(out / "environment.csv", "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(["key", "value"])
        for k, v in {"run date": date.today().isoformat(), **spec.get("env", {})}.items():
            w.writerow([k, v])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cases")
    ap.add_argument("out")
    ap.add_argument("slugs", nargs="*", help="only these cases (default all)")
    ap.add_argument("--cdp", default="http://127.0.0.1:9222", help="CDP endpoint of the signed-in Chrome")
    ap.add_argument("--index-only", action="store_true", help="rewrite index.csv / environment.csv without a browser")
    a = ap.parse_args()
    spec = json.loads(Path(inside_work(a.cases, "cases")).read_text(encoding="utf-8"))
    ui = deep_merge(DEFAULT_UI, spec.get("ui", {}))
    out = Path(inside_work(a.out, "evidence dir"))
    out.mkdir(parents=True, exist_ok=True)
    if a.index_only:
        write_index(out, spec, ui["captions"])
        return
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp(a.cdp)
        ctx = b.contexts[0]
        page = ctx.new_page()
        page.set_viewport_size({"width": 1440, "height": 900})
        col = Collector(page, ctx, ui)
        try:
            for case in spec["cases"]:
                if not a.slugs or case["slug"] in a.slugs:
                    col.run(case, out)
                    write_index(out, spec, ui["captions"])
        finally:
            page.close()  # our tab only — never browser.close()


if __name__ == "__main__":
    main()
