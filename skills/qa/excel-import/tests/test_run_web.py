import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import run_web  # noqa: E402


def test_compare_substring_errors():
    e = dict(status="VALIDATION_ERROR", detailCount=0, errors=["does not match"])
    assert run_web.compare(e, "VALIDATION_ERROR", 0, ["row 12: form type X does not match right Y"]) == []
    assert run_web.compare(e, "VALIDATED", 1, []) == ["status VALIDATED != VALIDATION_ERROR", "missing error: does not match", "expected errors, got none"]
    assert run_web.compare(dict(status="VALIDATED", detailCount=2, errors=[]), "VALIDATED", 1, []) == ["detailCount 1 != 2"]


def test_load_adapter_example_and_contract(tmp_path):
    ad = run_web.load_adapter(str(Path(__file__).resolve().parents[1] / "scripts" / "adapter_example.py"))
    assert ad.ACCOUNTS["acme"] == 1
    body = {"status": "VALIDATION_ERROR", "data": {"errors": ["x"], "rows": [{"rowNo": 10, "errors": ["y"]}]}}
    assert ad.web_errors(body) == ["x", "row 10: y"]
    assert ad.web_status(body) == ("VALIDATION_ERROR", None)
    bad = tmp_path / "bad.py"
    bad.write_text("BASE='x'\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        run_web.load_adapter(str(bad))


def test_build_report_without_runs(tmp_path):
    cases = tmp_path / "cases.json"
    cases.write_text("[]", encoding="utf-8")
    (tmp_path / "results").mkdir()
    assert run_web.build_report(tmp_path / "results", cases) is None


def test_build_report_embeds_latest_verdict(tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    cases = tmp_path / "cases.json"
    cases.write_text(json.dumps([{"id": "V1", "file": "v1.xlsx", "company": 1, "mode": "validate",
                                  "expect": {"status": "VALIDATED", "detailCount": 1}}]), encoding="utf-8")
    res = tmp_path / "results"
    res.mkdir()
    run = [{"id": "V1", "file": "v1.xlsx", "mode": "validate", "expect": {"status": "VALIDATED", "detailCount": 1},
            "file_check": {"status": "VALIDATED", "detailCount": 1, "errors": [], "mismatch": []},
            "web": {"status": "VALIDATED", "detailCount": 1, "errors": [], "mismatch": []}, "verdict": "PASS"}]
    (res / "20261109-120000-acme.json").write_text(json.dumps(run), encoding="utf-8")
    out = run_web.build_report(res, cases)
    wb = openpyxl.load_workbook(out)
    assert wb.sheetnames == ["Summary", "Runs", "V1"]
    assert wb["Summary"]["I2"].value == "PASS"
    assert wb["Summary"]["A4"].value == "passed 1/1 cases"
