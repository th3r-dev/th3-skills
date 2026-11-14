import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "drawio_board.py"
sys.path.insert(0, str(SCRIPT.parent))
db = pytest.importorskip("drawio_board")

W, H = 400, 300


def board(x0, y0, version, date, title, ids):
    return (f'<mxCell id="{ids}t" value="{title}" style="text;" vertex="1" parent="1"><mxGeometry x="{x0+10}" y="{y0+10}" width="200" height="20" as="geometry"/></mxCell>'
            f'<mxCell id="{ids}v" value="Version {version} Update {date}" style="text;" vertex="1" parent="1"><mxGeometry x="{x0+10}" y="{y0+40}" width="200" height="20" as="geometry"/></mxCell>'
            f'<mxCell id="{ids}b" value="web" style="rounded=0;" vertex="1" parent="1"><mxGeometry x="{x0+50}" y="{y0+100}" width="80" height="40" as="geometry"/></mxCell>')


def drawio(tmp_path):
    cells = board(0, 0, "1.1.3", "01/10/2026", "Non Production System Diagram", "a") + board(W, 0, "1.1.5", "05/10/2026", "Production System Diagram", "b")
    x = (f'<mxfile><diagram id="d" name="Page-1"><mxGraphModel pageWidth="{W}" pageHeight="{H}" pageScale="1"><root>'
         f'<mxCell id="0"/><mxCell id="1" parent="0"/>{cells}</root></mxGraphModel></diagram></mxfile>')
    f = tmp_path / "d.drawio"
    f.write_text(x, encoding="utf-8")
    return f


def test_list_finds_both_boards(tmp_path):
    pages = db.pages_of(db.load(drawio(tmp_path)))
    b = pages[0].boards()
    assert [(x["tile"], x["version"], x["title"]) for x in b] == [
        ((0, 0), "1.1.3", "Non Production System Diagram"), ((1, 0), "1.1.5", "Production System Diagram")]


def test_clone_adds_a_board_in_the_free_tile_below(tmp_path):
    f = drawio(tmp_path)
    r = subprocess.run([sys.executable, str(SCRIPT), "clone", str(f), "--from", "1.1.5", "--version", "1.1.6", "--date", "06/11/2026"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert f.with_suffix(".drawio.bak").exists()
    b = db.pages_of(db.load(f))[0].boards()
    assert [(x["tile"], x["version"]) for x in b] == [((0, 0), "1.1.3"), ((1, 0), "1.1.5"), ((1, 1), "1.1.6")]
    assert b[2]["date"] == ("06", "11", "2026") and b[2]["cells"] == 3


def test_find_board_errors(tmp_path):
    pages = db.pages_of(db.load(drawio(tmp_path)))
    with pytest.raises(SystemExit):
        db.find_board(pages, "9.9.9")
