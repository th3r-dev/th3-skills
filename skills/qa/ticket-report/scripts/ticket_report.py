# /// script
# requires-python = ">=3.10"
# dependencies = ["requests"]
# ///
"""QA result comment for a Jira ticket, in the team format, with screenshots inline.

    S=skills/qa/ticket-report/scripts
    uv run $S/ticket_report.py draft <evidence dir> --ticket PROJ-273 --env uat --platform "Web (admin app)" \
        [--account "Section in accounts.ini" | --test-data "user1"] [--release v1.2.22] [--actual "<1-2 sentences>"] \
        [--lang th|en] [--max-seconds 60] [--date "DD/MM/YYYY HH:MM"]
    uv run $S/ticket_report.py post <evidence dir> --ticket PROJ-273 [--update <comment id>]   # only after the owner said OK
    uv run $S/ticket_report.py --selftest

draft writes <dir>/ticket-report.md (preview, images by relative path), ticket-report.wiki (the exact comment
body) and ticket-report.json (what post uploads, under which name). Cases come from <dir>/cases.json, else one
case is built from results.json (a page-timing run: {url, api, version?, run_at?, same_order?, runs:[{run,
status, seconds, total?, page_rows?, screenshot?}]}) or from steps.csv (qa/export-evidence).

Test Data carries the password on dev/uat only; master/prd: username only, no override.
post authenticates with JIRA_BASE_URL + JIRA_EMAIL + JIRA_API_TOKEN (Atlassian Cloud basic auth) and
posts REST v2 wiki markup so the images render inline in the comment.
"""
from __future__ import annotations

import argparse
import configparser
import csv
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

ENVS = {"dev": "Dev", "uat": "UAT", "master": "Master", "prd": "PRD"}
PASSWORD_ENVS = {"dev", "uat"}  # never master/prd
IMG = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
TODO = "TODO"
RESULTS = {"PASSED": "#00875A", "FAILED": "#DE350B", "BLOCKED": "#FF8B00", "NOT TESTED": "#6B778C"}
WORST = ["FAILED", "BLOCKED", "NOT TESTED", "PASSED"]
DEFAULT_INI = Path.home() / ".config" / "qa-ticket-report" / "accounts.ini"
LABELS = {
    "th": dict(what="สิ่งที่เกิดขึ้น", expected="ควรได้", actual="ได้จริง", steps="ขั้นตอน", why="สาเหตุ", data="ข้อมูลที่ใช้",
               tech="รายละเอียดสำหรับทีมพัฒนา", files="ไฟล์ประกอบ", baseline="(ก่อนแก้ · ไว้เทียบ)",
               passed_of="ผ่าน {p} จาก {n} เคส", todo_actual="สรุปสิ่งที่เกิดขึ้น",
               run="รอบ {run}: HTTP {status} · {seconds} วินาที", run_total=" · total {total}",
               timing_case="เปิด {path} แล้วรอ {api}", timing_expected="HTTP 2xx ทุกรอบ ภายใน {max} วินาที และลำดับแถวเท่ากันทุกรอบ",
               same={True: "ลำดับแถวเท่ากันทุกรอบ", False: "ลำดับแถวไม่เท่ากัน", None: "ไม่มีแถวให้เทียบลำดับ"},
               table_head="| รอบ | HTTP | วินาที | total | แถวต่อหน้า |",
               steps_expected="ทุกขั้นผ่าน", steps_actual="{ok} จาก {n} ขั้นผ่าน"),
    "en": dict(what="What happened", expected="Expected", actual="Actual", steps="Steps", why="Cause", data="Test data",
               tech="Details for the dev team", files="Attached files", baseline="(before the fix · for comparison)",
               passed_of="{p} of {n} cases passed", todo_actual="summarise what happened",
               run="run {run}: HTTP {status} · {seconds} s", run_total=" · total {total}",
               timing_case="open {path} and wait for {api}", timing_expected="HTTP 2xx on every run within {max} s, same row order every run",
               same={True: "same row order every run", False: "row order differs", None: "no rows to compare"},
               table_head="| run | HTTP | seconds | total | rows/page |",
               steps_expected="every step passes", steps_actual="{ok} of {n} steps passed"),
}
TEXT_TYPES = {".md", ".json", ".csv", ".log", ".txt", ".sql", ".tsv"}


def badge(result: str, wiki: bool) -> str:
    c = RESULTS[result]
    return f"{{color:{c}}}*{result}*{{color}}" if wiki else f'<span style="color:{c}">**{result}**</span>'


def die(msg):
    raise SystemExit(f"ticket_report: {msg}")


def preview_mime(name: str) -> str:
    """Jira previews images, PDF, video and text/plain; anything else only downloads."""
    ext = Path(name).suffix.lower()
    if ext in TEXT_TYPES:
        return "text/plain; charset=utf-8"
    if ext in IMG:
        return {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "gif": "image/gif", "webp": "image/webp"}[ext[1:]]
    if ext == ".pdf":
        return "application/pdf"
    return "application/octet-stream"


# ---------- inputs ----------

def test_data(ini: Path, section: str, env: str) -> str:
    cp = configparser.ConfigParser(interpolation=None)
    cp.read(ini, encoding="utf-8")
    if not cp.has_section(section) or not cp[section].get("UserName", "").strip():
        die(f"[{section}] needs UserName in {ini}")
    user = cp[section]["UserName"].strip()
    pw = cp[section].get("Password", "").strip()
    return f"{user} / {pw}" if env in PASSWORD_ENVS and pw else user


def live_badge(page_url: str | None, regex: str) -> str | None:
    """the version the portal reports about itself, read from its login page — a read-only GET, no sign-in."""
    if not page_url:
        return None
    m = re.match(r"(https?://[^/]+)(/[^/]+)?", page_url)
    import requests
    try:
        html = requests.get(f"{m.group(1)}{m.group(2) or ''}/login", headers={"User-Agent": "qa-ticket-report/1"}, timeout=20).text
    except Exception:
        return None
    v = re.search(regex, html)
    return v.group(1) if v else None


def version_label(badge: str | None, release: str | None) -> str:
    badge = None if badge in (None, "", "-") else badge.strip()
    release = (release or "").strip() or None
    if not badge and not release:
        die("no version: results.json has none, the login page gave none, and --release was not given")
    if badge and release and re.fullmatch(r"v?\d+(\.\d+)+", badge) and badge.lstrip("v") != release.lstrip("v"):
        die(f"the portal says {badge} but --release says {release}")
    if badge and release and badge.lstrip("v") != release.lstrip("v"):
        return f"{release} ({badge})"
    return release or badge


def cases_from_results(res: dict, max_s: float, L: dict) -> dict:
    runs = res["runs"]
    ok = all(isinstance(r["status"], int) and 200 <= r["status"] < 300 and r["seconds"] <= max_s for r in runs)
    ok = ok and res.get("same_order") is not False

    def one(r):
        return L["run"].format(**r) + (L["run_total"].format(total=r["total"]) if r.get("total") is not None else "")
    rows = [L["table_head"], "|---|---|---|---|---|"] + [
        f"| {r['run']} | {r['status']} | {r['seconds']} | {r.get('total', '-')} | {r.get('page_rows', '-')} |" for r in runs]
    path = re.sub(r"^https?://[^/]+", "", res["url"])
    return dict(case=L["timing_case"].format(path=path, api=res["api"]),
                expected=L["timing_expected"].format(max=f"{max_s:g}"),
                actual=" · ".join(one(r) for r in runs) + f" · {L['same'][res.get('same_order')]}",
                result="PASSED" if ok else "FAILED", table=rows,
                evidence=[r["screenshot"] for r in runs if r.get("screenshot")])


def cases_from_steps(path: Path, L: dict) -> dict:
    steps = list(csv.DictReader(path.open(encoding="utf-8-sig")))
    bad = [s for s in steps if s.get("result", "").upper() in {"FAIL", "FAILED"}]
    return dict(case=path.parent.name, expected=L["steps_expected"], actual=L["steps_actual"].format(ok=len(steps) - len(bad), n=len(steps)),
                result="FAILED" if bad else "PASSED",
                evidence=[{"file": s["evidence"], "caption": f"{s['step']}. {s['action']}"} for s in steps if s.get("evidence")])


# ---------- render ----------

def cell(t: str, wiki: bool) -> str:
    return str(t).replace("|", "/").replace("\n", " ") if wiki else str(t).replace("|", "\\|").replace("\n", " ")


def render(meta: dict, cases: list[dict], others: list[str], names: dict, wiki: bool, L: dict) -> str:
    out = [f"Test Result: {badge(meta['result'], wiki)}", f"Test Environment: {meta['env']} - Version {meta['version']}",
           f"Platform: {meta['platform']}", f"Test Date : {meta['date']}", f"Test Data: {meta['data']}",
           "Actual Result :", meta["actual"], ""]
    if len(cases) > 1:
        out += ["||Test Case||Actual Result||Expected Result||" if wiki else "| Test Case | Actual Result | Expected Result |"]
        if not wiki:
            out += ["|---|---|---|"]
        for i, c in enumerate(cases, 1):
            tag = f" {L['baseline']}" if c.get("baseline") else ""
            out += [f"| {i}. {cell(c['case'], wiki)}{tag} | {badge(c['result'], wiki)} {cell(c['actual'], wiki)} | {cell(c['expected'], wiki)} |"]
        out += [""]
    out += [f"h3. {L['what']}" if wiki else f"### {L['what']}", ""]

    def label(t):
        return f"*{t}*" if wiki else f"**{t}**"

    def bullets(items, numbered=False):
        mark = ("# " if numbered else "* ") if wiki else None
        return [f"{mark}{x}" if wiki else (f"{n}. {x}" if numbered else f"- {x}") for n, x in enumerate(items, 1)]

    for i, c in enumerate(cases, 1):
        head = f"{i}. {c['case']}" if len(cases) > 1 else c["case"]
        out += [f"{label(head)}  {badge(c['result'], wiki)}"]
        # reading order: expected → actual → steps → why → data → images → dev notes
        out += [f"{label(L['expected'])} {c['expected']}", f"{label(L['actual'])} {c['actual']}"]
        if c.get("steps"):
            out += [label(L["steps"])] + bullets(c["steps"], numbered=True)
        if c.get("why"):
            out += [f"{label(L['why'])} {c['why']}"]
        if c.get("data"):
            out += [label(L["data"])] + bullets(c["data"])
        if c.get("detail"):  # legacy free text
            out += [c["detail"]]
        for t in c.get("table", []):
            if wiki:
                if t.startswith("|---"):
                    continue
                t = "||" + "||".join(x.strip() for x in t.strip("|").split("|")) + "||" if t is c["table"][0] else t
            out += [t]
        for ev in c["evidence"]:
            f, cap = (ev["file"], ev.get("caption", "")) if isinstance(ev, dict) else (ev, "")
            if Path(f).suffix.lower() not in IMG:
                continue
            out += ([f"!{names[c['_dir_key'], f]}|width=700!", cap] if wiki else [f"![{cap or f}]({f})", cap])
        if c.get("tech"):
            out += [label(L["tech"])] + bullets(c["tech"])
        out += [""]
    files = [("", f) for f in others] + [(c["_dir_key"], ev if isinstance(ev, str) else ev["file"]) for c in cases
                                         for ev in c["evidence"] if Path(ev if isinstance(ev, str) else ev["file"]).suffix.lower() not in IMG]
    if files:
        out += [f"h3. {L['files']}" if wiki else f"### {L['files']}", ""]
        out += [f"* [^{names[k]}]" if wiki else f"- [{Path(k[1]).name}]({k[1]})" for k in files]
    return "\n".join(x for x in out if x is not None).rstrip() + "\n"


def draft(a, ini: Path | None = None, fetch_badge=live_badge) -> Path:
    L = LABELS[a.lang]
    d = Path(a.dir).resolve()
    if not d.is_dir():
        die(f"{d} is not a directory")
    res = json.loads((d / "results.json").read_text(encoding="utf-8")) if (d / "results.json").exists() else None
    if (d / "cases.json").exists():
        cases = json.loads((d / "cases.json").read_text(encoding="utf-8"))
    elif res:
        cases = [cases_from_results(res, a.max_seconds, L)]
    elif (d / "steps.csv").exists():
        cases = [cases_from_steps(d / "steps.csv", L)]
    else:
        die(f"{d} has no cases.json, results.json or steps.csv")
    for c in cases:
        if c.get("result") not in RESULTS:
            die(f"case {c.get('case')!r}: result must be one of {', '.join(RESULTS)}")
        for ev in c.get("evidence", []):
            f = ev if isinstance(ev, str) else ev["file"]
            if not (d / f).is_file():
                die(f"case {c['case']!r}: evidence {f} not found under {d}")
        c.setdefault("evidence", [])
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    prefix = f"qa-{a.env}-{stamp}"
    old = d / "ticket-report.json"  # a redraft keeps the upload names, so a re-post skips files already on Jira
    if old.exists():
        prev = json.loads(old.read_text(encoding="utf-8")).get("uploads") or [{}]
        m = re.match(r"(qa-[a-z]+-\d{8}-\d{4})-", prev[0].get("name", ""))
        prefix = m.group(1) if m else prefix
    names, uploads = {}, []
    for i, c in enumerate(cases, 1):
        c["_dir_key"] = str(i)  # the same file may back several cases; each upload gets its own name
        for ev in c["evidence"]:
            f = ev if isinstance(ev, str) else ev["file"]
            n = f"{prefix}-c{i}-{Path(f).name}"
            names[str(i), f] = n
            uploads.append({"file": str((d / f).resolve()), "name": n})
    others = [p.name for p in sorted(d.iterdir()) if p.is_file() and p.suffix.lower() in {".md", ".json", ".xlsx", ".csv", ".pdf"}
              and not p.name.startswith(("ticket-report", "cases"))  # cases.json and its backups stay local
              and (d / p.name).resolve() not in {Path(u["file"]) for u in uploads}]
    for f in others:
        names["", f] = f"{prefix}-{f}"
        uploads.append({"file": str(d / f), "name": names["", f]})
    if not a.platform:
        die("--platform is required (e.g. \"Web (admin app)\", \"Mobile app\")")
    badge_v = (res or {}).get("version")
    if badge_v in (None, "", "-"):
        badge_v = fetch_badge((res or {}).get("url"), a.version_regex)
    run_at = (res or {}).get("run_at")
    date = datetime.strptime(run_at, "%Y%m%d-%H%M%S").strftime("%d/%m/%Y %H:%M") if run_at else (a.date or datetime.now().strftime("%d/%m/%Y %H:%M"))
    judged = [c for c in cases if not c.get("baseline")]
    if not judged:
        die("every case is baseline — at least one case has to be the test itself")
    passed = sum(c["result"] == "PASSED" for c in judged)
    if a.test_data:
        data = a.test_data
    elif a.account:
        data = test_data(ini or Path(a.ini), a.account, a.env)
    else:
        die("--account <ini section> or --test-data <text> is required")
    meta = dict(result=next(w for w in WORST if any(c["result"] == w for c in judged)), env=ENVS[a.env],
                version=version_label(badge_v, a.release), platform=a.platform, date=date, data=data,
                actual=a.actual or ((L["passed_of"].format(p=passed, n=len(judged)) + f" · {TODO}: {L['todo_actual']}")
                                    if len(cases) > 1 else f"{TODO}: {L['todo_actual']}"))
    (d / "ticket-report.md").write_text(render(meta, cases, others, names, False, L), encoding="utf-8")
    (d / "ticket-report.wiki").write_text(render(meta, cases, others, names, True, L), encoding="utf-8")
    (d / "ticket-report.json").write_text(json.dumps(dict(ticket=a.ticket, uploads=uploads), ensure_ascii=False, indent=2), encoding="utf-8")
    print(d / "ticket-report.md")
    return d


def jira_session():
    base, email, token = (os.environ.get(k, "").strip() for k in ("JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN"))
    if not (base and email and token):
        die("set JIRA_BASE_URL, JIRA_EMAIL and JIRA_API_TOKEN (Atlassian API token) in the environment")
    import requests
    s = requests.Session()
    s.auth = (email, token)
    s.headers["X-Atlassian-Token"] = "no-check"
    return base.rstrip("/"), s


def post(a):
    d = Path(a.dir).resolve()
    body = (d / "ticket-report.wiki").read_text(encoding="utf-8")
    plan = json.loads((d / "ticket-report.json").read_text(encoding="utf-8"))
    if TODO in body:
        die("the draft still has TODO — write the Actual Result first (--actual or cases.json), then draft again")
    if plan["ticket"] != a.ticket:
        die(f"the draft is for {plan['ticket']}, not {a.ticket}")
    base, s = jira_session()
    if s.get(f"{base}/rest/api/3/myself").status_code != 200:
        die("Jira rejected the credentials")
    have = {x["filename"] for x in s.get(f"{base}/rest/api/3/issue/{a.ticket}", params={"fields": "attachment"}).json()["fields"]["attachment"]}
    for u in plan["uploads"]:
        if u["name"] in have:
            print("skip", u["name"])
            continue
        with open(u["file"], "rb") as fh:
            r = s.post(f"{base}/rest/api/3/issue/{a.ticket}/attachments", files={"file": (u["name"], fh, preview_mime(u["name"]))})
        print("upload", u["name"], r.status_code)
        if not r.ok:
            die(f"upload failed: {r.text[:200]}")
    if a.update:  # rewrite an existing comment in place (same id, same thread position)
        r = s.put(f"{base}/rest/api/2/issue/{a.ticket}/comment/{a.update}", json={"body": body})
    else:
        r = s.post(f"{base}/rest/api/2/issue/{a.ticket}/comment", json={"body": body})
    if not r.ok:
        die(f"comment failed {r.status_code}: {r.text[:300]}")
    cid = a.update or r.json()["id"]
    back = s.get(f"{base}/rest/api/2/issue/{a.ticket}/comment/{cid}", params={"expand": "renderedBody"}).json()
    imgs = len(re.findall(r'<img(?![^>]*rendericon)', back.get("renderedBody", "")))  # not the paperclip icons
    want = sum(Path(u["name"]).suffix.lower() in IMG for u in plan["uploads"])
    print(f"{base}/browse/{a.ticket}?focusedCommentId={cid} · inline images {imgs}/{want}")


# ---------- selftest ----------

def selftest():
    import tempfile
    from types import SimpleNamespace as NS
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        ini = t / "c.ini"
        ini.write_text("[Acc]\nUserName = u1\nPassword = secretpw\n", encoding="utf-8")
        run = t / "run"
        run.mkdir()
        (run / "run-1.png").write_bytes(b"x")
        (run / "run-2.png").write_bytes(b"x")
        res = dict(url="https://h.example.com/app/p", api="/api/x", version="-", run_at="20261106-132840", same_order=True,
                   runs=[dict(run=1, status=201, seconds=6.7, total=9, page_rows=3, screenshot="run-1.png"),
                         dict(run=2, status=504, seconds=60.1, screenshot="run-2.png")])
        (run / "results.json").write_text(json.dumps(res), encoding="utf-8")
        A = lambda env, **k: NS(dir=str(run), ticket="PROJ-1", env=env, account="Acc", test_data=None, ini=str(ini),
                                platform="Web (admin app)", release=k.get("release", "v1.2.22"), actual=k.get("actual"),
                                max_seconds=60, date=None, lang=k.get("lang", "th"), version_regex=r'"appVersion":"([^"]+)"')
        nob = lambda url, rx: None
        draft(A("master"), ini, nob)
        md = (run / "ticket-report.md").read_text(encoding="utf-8")
        assert "secretpw" not in md and "Test Data: u1\n" in md, "master must not carry the password"
        assert "Test Result: " + badge("FAILED", False) in md, "a 504 run is FAILED"
        assert "Master - Version v1.2.22" in md and "| Test Case |" not in md, "one case → no table"
        wk = (run / "ticket-report.wiki").read_text(encoding="utf-8")
        assert re.search(r"!qa-master-\d{8}-\d{4}-c1-run-1\.png\|width=700!", wk), "image inline in the wiki body"
        draft(A("dev"), ini, nob)
        assert "Test Data: u1 / secretpw" in (run / "ticket-report.md").read_text(encoding="utf-8"), "dev carries the password"
        try:
            draft(A("dev", release=None), ini, nob)
            raise AssertionError("missing version must fail")
        except SystemExit:
            pass
        assert version_label("master-6ca0cf2", "v1.2.22") == "v1.2.22 (master-6ca0cf2)"
        try:
            version_label("v1.2.21", "v1.2.22")
            raise AssertionError("badge/release disagreement must fail")
        except SystemExit:
            pass
        cases = [dict(case=f"c{i}", expected="e", actual="a", result=r, evidence=["run-1.png"]) for i, r in
                 enumerate(["PASSED", "FAILED", "PASSED"], 1)]
        (run / "cases.json").write_text(json.dumps(cases), encoding="utf-8")
        draft(A("uat"), ini, nob)
        md = (run / "ticket-report.md").read_text(encoding="utf-8")
        assert md.count("| 1. c1 |") == 1 and "| 3. c3 |" in md and "Test Result: " + badge("FAILED", False) in md and "ผ่าน 2 จาก 3 เคส" in md
        wk = (run / "ticket-report.wiki").read_text(encoding="utf-8")
        assert "||Test Case||Actual Result||Expected Result||" in wk
        try:
            post(NS(dir=str(run), ticket="PROJ-1", update=None))
            raise AssertionError("TODO must block post")
        except SystemExit as e:
            assert "TODO" in str(e)
        cases[0]["evidence"] = ["nope.png"]
        (run / "cases.json").write_text(json.dumps(cases), encoding="utf-8")
        try:
            draft(A("uat"), ini, nob)
            raise AssertionError("missing evidence must fail")
        except SystemExit:
            pass
        base = [dict(case="before", expected="e", actual="504", result="FAILED", baseline=True, evidence=[]),
                dict(case="after", expected="e", actual="201", result="PASSED", evidence=[])]
        (run / "cases.json").write_text(json.dumps(base), encoding="utf-8")
        draft(A("uat", actual="ok"), ini, nob)
        md = (run / "ticket-report.md").read_text(encoding="utf-8")
        assert "Test Result: " + badge("PASSED", False) in md and "(ก่อนแก้ · ไว้เทียบ)" in md, "baseline rows are shown, not judged"
        assert "Test Result: {color:#00875A}*PASSED*{color}" in (run / "ticket-report.wiki").read_text(encoding="utf-8")
        base[1]["result"] = "BLOCKED"
        (run / "cases.json").write_text(json.dumps(base), encoding="utf-8")
        draft(A("uat", actual="ok"), ini, nob)
        assert "Test Result: {color:#FF8B00}*BLOCKED*{color}" in (run / "ticket-report.wiki").read_text(encoding="utf-8")
        st = [dict(case="c", expected="e", actual="a", result="FAILED", steps=["s1", "s2"], why="w", data=["d1"],
                   tech=["t1"], evidence=[])]
        (run / "cases.json").write_text(json.dumps(st), encoding="utf-8")
        draft(A("uat", actual="ok"), ini, nob)
        wk = (run / "ticket-report.wiki").read_text(encoding="utf-8")
        assert "*ขั้นตอน*\n# s1\n# s2" in wk and "*สาเหตุ* w" in wk and "* d1" in wk and "*รายละเอียดสำหรับทีมพัฒนา*\n* t1" in wk, wk
        draft(A("uat", actual="ok", lang="en"), ini, nob)
        wk = (run / "ticket-report.wiki").read_text(encoding="utf-8")
        assert "*Steps*\n# s1" in wk and "h3. What happened" in wk
        (run / "cases.v1.json").write_text("[]", encoding="utf-8")
        first = json.loads((run / "ticket-report.json").read_text(encoding="utf-8"))["uploads"]
        draft(A("uat", actual="ok"), ini, nob)
        again = json.loads((run / "ticket-report.json").read_text(encoding="utf-8"))["uploads"]
        assert [u["name"] for u in again] == [u["name"] for u in first], "redraft must keep upload names"
        assert not any("cases" in u["name"] for u in again), "cases*.json never uploads"
        assert preview_mime("a.json") == "text/plain; charset=utf-8" and preview_mime("a.png") == "image/png"
    print("selftest ok")


def main():
    if "--selftest" in sys.argv:
        return selftest()
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    dr = sub.add_parser("draft")
    dr.add_argument("dir")
    dr.add_argument("--ticket", required=True)
    dr.add_argument("--env", required=True, choices=ENVS)
    dr.add_argument("--platform", required=True, help='free text, e.g. "Web (admin app)", "Mobile app"')
    dr.add_argument("--account", help="section of --ini with UserName (+ Password)")
    dr.add_argument("--ini", default=str(DEFAULT_INI), help=f"accounts file (default {DEFAULT_INI}); keep it outside the repo")
    dr.add_argument("--test-data", help="Test Data text to print as-is (instead of --account)")
    dr.add_argument("--release", help="release tag, e.g. v1.2.22 — shown beside the portal's own label")
    dr.add_argument("--actual", help="the header's Actual Result text")
    dr.add_argument("--lang", default="th", choices=LABELS, help="language of the body labels")
    dr.add_argument("--max-seconds", type=float, default=60, help="results.json case: slower than this = FAILED")
    dr.add_argument("--date", help="DD/MM/YYYY HH:MM when there is no results.json")
    dr.add_argument("--version-regex", default=r'"appVersion":"([^"]+)"', help="regex (1 group) to read the version off the login page")
    po = sub.add_parser("post")
    po.add_argument("dir")
    po.add_argument("--ticket", required=True)
    po.add_argument("--update", metavar="COMMENT_ID", help="replace this existing comment instead of adding a new one")
    a = p.parse_args()
    draft(a) if a.cmd == "draft" else post(a)


if __name__ == "__main__":
    main()
