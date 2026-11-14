import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import qa  # noqa: E402

openpyxl = pytest.importorskip("openpyxl")


def test_merged_cell_keeps_team_text_and_replaces_ours():
    assert qa.merged_cell("", "- a", []) == "- a"
    assert qa.merged_cell("team", "- a", []) == "team\n\n- a"
    assert qa.merged_cell("team\n\n- a", "- b", ["- a"]) == "team\n\n- b"
    assert qa.merged_cell("team\n\n---- 06/10/2026 ----\nold", "- b", []) == "team\n\n- b"


def make_sheet(path, title, headers, rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = title
    ws.append(headers)
    for r in rows:
        ws.append(r)
    wb.save(path)


def test_pull_then_merge(tmp_path):
    xlsx = tmp_path / "s.xlsx"
    make_sheet(xlsx, "Q&A List ACME", ["No", "Question", "Answer", "Remark"],
               [[1, "q1", "a1", ""], [2.0, "q2", "a2", "team note"]])
    out = tmp_path / "out"
    assert qa.pull(xlsx, out, qa.DEFAULT_TAB, qa.DEFAULT_HEADERS) == 1
    data = json.loads((out / "ACME" / "qa.json").read_text(encoding="utf-8"))
    assert [r["No"] for r in data["rows"]] == ["1", "2"]
    day = out / "ACME" / "09112026"
    day.mkdir()
    (day / "final.json").write_text(json.dumps({"2": "- fix it"}), encoding="utf-8")
    plan = qa.merge("ACME", out, "09/11/2026")
    assert plan == [{"No": "2", "row": 3, "old": "team note", "new": "team note\n\n- fix it"}]


def test_pull_rejects_renamed_header(tmp_path):
    xlsx = tmp_path / "s.xlsx"
    make_sheet(xlsx, "Q&A ACME", ["No", "Q", "A", "Remark"], [[1, "q", "a", ""]])
    with pytest.raises(SystemExit):
        qa.pull(xlsx, tmp_path / "out", qa.DEFAULT_TAB, qa.DEFAULT_HEADERS)


def test_custom_headers_and_tab(tmp_path):
    xlsx = tmp_path / "s.xlsx"
    make_sheet(xlsx, "Meeting TOP", ["ลำดับ", "คำถาม", "คำตอบ", "หมายเหตุ"], [[1, "q", "a", ""]])
    assert qa.pull(xlsx, tmp_path / "out", r"Meeting (\S+)", ["ลำดับ", "คำถาม", "คำตอบ", "หมายเหตุ"]) == 1
    assert (tmp_path / "out" / "TOP" / "qa.json").exists()
