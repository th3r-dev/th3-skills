import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import ticket_report as tr  # noqa: E402


def test_selftest_runs():
    tr.selftest()


def test_badges_and_mime():
    assert tr.badge("PASSED", True) == "{color:#00875A}*PASSED*{color}"
    assert tr.badge("BLOCKED", False).startswith('<span style="color:#FF8B00">')
    assert tr.preview_mime("x.csv") == "text/plain; charset=utf-8"
    assert tr.preview_mime("x.bin") == "application/octet-stream"


def test_version_label():
    assert tr.version_label("v1.2.22", "v1.2.22") == "v1.2.22"
    assert tr.version_label("v1.2.22", None) == "v1.2.22"
    assert tr.version_label(None, "v1.2.22") == "v1.2.22"
    assert tr.version_label("master-abc", "v1.2.22") == "v1.2.22 (master-abc)"
