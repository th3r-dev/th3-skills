import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE.parent / "scripts" / "check_report.py"
sys.path.insert(0, str(SCRIPT.parent))
import check_report  # noqa: E402


def test_selftest():
    check_report.selftest()


def test_unfilled_template_fails():
    # a template copied and never filled in must not pass
    for t in ("template-th.md", "template-en.md"):
        found = check_report.check((HERE.parent / "references" / t).read_text(encoding="utf-8"), HERE)
        rules = {f.split(": ")[1] for f in found}
        assert {"front-matter", "placeholder", "image"} <= rules, (t, rules)
        assert "sections" not in rules, t  # both templates carry every fixed page


def test_cli_exit_code(tmp_path):
    ok = tmp_path / "r.md"
    ok.write_text("---\ntitle: Release v2.0.0\n---\n\n# Overview\n\nx\n\n# BA Decision\n\nx\n\n"
                  "# Change details\n\nx\n\n# Test plan\n\nx\n", encoding="utf-8")
    assert subprocess.run([sys.executable, str(SCRIPT), str(ok)]).returncode == 0
    ok.write_text(ok.read_text(encoding="utf-8").replace("# Test plan", "# Tests"), encoding="utf-8")
    assert subprocess.run([sys.executable, str(SCRIPT), str(ok)], capture_output=True).returncode == 1
