import csv
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
openpyxl = pytest.importorskip("openpyxl")
PIL = pytest.importorskip("PIL")
import make_qa_report as mk  # noqa: E402
import collect_export as ce  # noqa: E402


def write_csv(path, rows, header):
    with path.open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=header)
        w.writeheader()
        w.writerows(rows)


def test_build_report(tmp_path):
    ev = tmp_path / "evidence"
    (ev / "01_a" / "screenshots").mkdir(parents=True)
    PIL.Image.new("RGB", (1200, 600), "white").save(ev / "01_a" / "screenshots" / "01-open-page.png")
    write_csv(ev / "01_a" / "steps.csv", [
        {"step": 1, "action": "open", "result": "PASS", "evidence": "screenshots/01-open-page.png"},
        {"step": 2, "action": "file", "result": "FAIL", "evidence": "screenshots/missing.png"},
    ], ["step", "action", "result", "evidence"])
    write_csv(ev / "index.csv", [
        {"no": 1, "title": "A · Excel", "sheet": "g1", "folder": "01_a", "result": "PASS", "actual": "ok"},
        {"no": 2, "title": "B · PDF", "sheet": "g2", "folder": "01_a", "result": "FAIL", "actual": ""},
    ], ["no", "title", "sheet", "folder", "result", "actual"])
    write_csv(ev / "environment.csv", [{"key": "env", "value": "UAT"}], ["key", "value"])
    a = SimpleNamespace(title="T", env="UAT", date="NOV 9, 2026", only_sheets=None)
    out = tmp_path / "r.xlsx"
    wb = mk.build(ev, out, a, mk.LABELS)
    assert wb.sheetnames == ["Summary", "Report01", "Report02"]
    s = wb["Summary"]
    assert s["B4"].value == "Test Result:  Fail (1/2 PASS)"
    assert wb["Report01"]["B7"].value == "Actual Result: ok"
    assert "(no image: screenshots/missing.png)" in [c.value for row in wb["Report01"].iter_rows() for c in row]
    a.only_sheets = ["g2"]
    wb = mk.build(ev, out, a, mk.LABELS)
    assert wb.sheetnames == ["Summary", "Report01"]


def test_status_words_failure_first():
    ui = ce.DEFAULT_UI
    assert ce.status_words("สร้างรายงาน สำเร็จ", ui) == (True, False)
    assert ce.status_words("สร้างรายงาน ไม่สำเร็จ", ui) == (False, True)  # "ไม่สำเร็จ" contains "สำเร็จ"
    assert ce.status_words("Completed", ce.deep_merge(ui, {"success_words": ["Completed"]})) == (True, False)


def test_deep_merge_keeps_defaults():
    ui = ce.deep_merge(ce.DEFAULT_UI, {"captions": {"open-page": "x"}, "refresh": "R"})
    assert ui["captions"]["open-page"] == "x" and ui["captions"]["error"] == ce.DEFAULT_UI["captions"]["error"]
    assert ui["refresh"] == "R" and ui["alert"] == ".swal2-popup"
