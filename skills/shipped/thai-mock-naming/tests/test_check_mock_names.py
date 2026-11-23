"""Behaviour of the mock-name linter.

Two failure modes matter, in this order:

  1. A false NEGATIVE ships a real Thai person's name into a fixture.
  2. A false POSITIVE on a legitimate compound (ข้อมูลจำลอง contains จำลอง,
     a real given name) trains people to ignore the linter.

Most of these tests guard the second, because Thai has no word separators and
naive substring matching gets it wrong.
"""

import random

import pytest

import check_mock_names as c
import gen_names as g


def tokens(line):
    return [tok for _, tok, _ in c.find_thai(line, _blocked())]


def _blocked():
    blocked = {t: "given" for t in c.GIVEN_NAMES}
    for t in c.SURNAMES:
        blocked.setdefault(t, "surname")
    return blocked


# ------------------------------------------------------------- true positives

@pytest.mark.parametrize("line,expected", [
    ("สมชาย ใจดี", ["สมชาย", "ใจดี"]),
    ("สมหญิง พอใจ", ["สมหญิง", "พอใจ"]),
    ("'มานี','รักเรียน'", ["มานี", "รักเรียน"]),
    ("ปิติ ทองดี", ["ปิติ", "ทองดี"]),
    ("name: ชูใจ", ["ชูใจ"]),
    ("จำลอง ศรีเมือง", ["จำลอง", "ศรีเมือง"]),
])
def test_catches_real_names(line, expected):
    assert tokens(line) == expected


def test_catches_concatenated_names_without_a_separator():
    """Thai writes without spaces, so สมชายใจดี is one run of two real names."""
    assert tokens("สมชายใจดี") == ["สมชาย", "ใจดี"]


def test_catches_names_inside_quotes_and_sql():
    line = "INSERT INTO users VALUES ('สมชาย', 'ใจดี');"
    assert tokens(line) == ["สมชาย", "ใจดี"]


def test_latin_placeholders_are_flagged():
    pat = c.build_pattern(c.LATIN)
    assert pat.search('{ name: "John Doe" }')
    assert pat.search("Jane Doe")


# ------------------------------------------------------------ false positives

@pytest.mark.parametrize("line", [
    "ข้อมูลจำลอง",            # approved surname marker, contains จำลอง
    "ข้อมูลจำลอง001",
    "ทดสอบ นามสมมุติ",
    "ทดสอบ ผู้อนุมัติ",
    "บริษัท ทดสอบระบบ จำกัด",
    "การจำลองสถานการณ์",      # ordinary Thai word containing จำลอง
    "ระบบจำลองการทำงาน",
    "มิใช่บุคคลจริง",
])
def test_does_not_flag_legitimate_thai(line):
    assert tokens(line) == []


def test_marker_compound_is_spared_but_bare_token_is_not():
    """The exact distinction SKILL.md draws about จำลอง."""
    assert tokens("ข้อมูลจำลอง") == []
    assert tokens("จำลอง") == ["จำลอง"]


@pytest.mark.parametrize("seed", range(5))
def test_generator_output_is_never_flagged(seed):
    """The generator and the linter must agree, or the skill contradicts itself."""
    rng = random.Random(seed)
    rows = (g.gen_people(100, rng, with_id=True, with_contact=True)
            + g.gen_people(50, rng, use_roles=True, use_titles=True)
            + g.gen_people(50, rng, thai_digits=True)
            + g.gen_companies(40, rng)
            + g.gen_edge_cases())
    for r in rows:
        for value in r.values():
            if isinstance(value, str) and value:
                assert tokens(value) == [], (r, value)


# ------------------------------------------------------------------ allowlist

def test_allow_removes_a_token():
    blocked = _blocked()
    del blocked["สมชาย"]
    found = [tok for _, tok, _ in c.find_thai("สมชาย ใจดี", blocked)]
    assert found == ["ใจดี"]


# --------------------------------------------------------------- file scanning

def write(tmp_path, name, text):
    p = tmp_path / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def test_scan_reports_line_and_column(tmp_path):
    p = write(tmp_path, "seed.sql", "ok\nVALUES ('สมชาย');\n")
    findings = c.scan_file(str(p), _blocked(), c.build_pattern(c.LATIN))
    assert len(findings) == 1
    assert findings[0]["line"] == 2
    assert findings[0]["token"] == "สมชาย"
    assert findings[0]["kind"] == "given"
    assert findings[0]["suggestion"]


def test_inline_marker_suppresses_a_line(tmp_path):
    p = write(tmp_path, "seed.sql",
              "VALUES ('สมชาย'); -- {}\nVALUES ('สมศรี');\n".format(c.INLINE_IGNORE))
    findings = c.scan_file(str(p), _blocked(), None)
    assert [f["token"] for f in findings] == ["สมศรี"]


def test_binary_and_undecodable_files_are_skipped(tmp_path):
    p = tmp_path / "blob.dat"
    p.write_bytes(b"\xff\xfe\x00\x01" + "สมชาย".encode("utf-16-le"))
    assert c.scan_file(str(p), _blocked(), None) == []


def test_exclude_glob(tmp_path):
    write(tmp_path, "a.sql", "สมชาย")
    write(tmp_path, "docs/b.md", "สมชาย")
    all_files = set(c.iter_files(str(tmp_path), []))
    assert len(all_files) == 2
    kept = set(c.iter_files(str(tmp_path), ["*.sql"]))
    assert len(kept) == 1
    assert not any(p.endswith(".sql") for p in kept)


def test_exclude_directory_prefix(tmp_path):
    write(tmp_path, "docs/b.md", "สมชาย")
    write(tmp_path, "src/c.py", "สมชาย")
    kept = set(c.iter_files(str(tmp_path), [str(tmp_path / "docs")]))
    assert len(kept) == 1
    assert kept.pop().endswith("c.py")


def test_skip_dirs_are_not_walked(tmp_path):
    write(tmp_path, "node_modules/x.js", "สมชาย")
    write(tmp_path, "keep.js", "สมชาย")
    found = list(c.iter_files(str(tmp_path), []))
    assert len(found) == 1


def test_ignore_file_is_read(tmp_path):
    write(tmp_path, c.IGNORE_FILE, "# comment\nlegacy/**\n")
    patterns = c.load_ignore_file(str(tmp_path))
    assert patterns == ["legacy/**"]


def test_missing_ignore_file_is_not_an_error(tmp_path):
    assert c.load_ignore_file(str(tmp_path)) == []


# ----------------------------------------------------------------------- CLI

def test_cli_exit_codes(tmp_path, capsys):
    write(tmp_path, "bad.sql", "VALUES ('สมชาย','ใจดี');")
    assert c.main([str(tmp_path), "--quiet"]) == 1

    write(tmp_path, "bad.sql", "VALUES ('ทดสอบ','นามสมมุติ');")
    assert c.main([str(tmp_path), "--quiet"]) == 0
    capsys.readouterr()


def test_cli_json_output_is_parseable(tmp_path, capsys):
    import json
    write(tmp_path, "bad.sql", "VALUES ('สมชาย');")
    assert c.main([str(tmp_path), "--format", "json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload[0]["token"] == "สมชาย"


def test_cli_allow_flag(tmp_path, capsys):
    write(tmp_path, "bad.sql", "VALUES ('สมชาย');")
    assert c.main([str(tmp_path), "--allow", "สมชาย", "--quiet"]) == 0
    capsys.readouterr()


def test_cli_honours_ignore_file_and_can_disable_it(tmp_path, capsys):
    write(tmp_path, "legacy.sql", "VALUES ('สมชาย');")
    write(tmp_path, c.IGNORE_FILE, "legacy.sql\n")
    assert c.main([str(tmp_path), "--quiet"]) == 0
    assert c.main([str(tmp_path), "--quiet", "--no-ignore-file"]) == 1
    capsys.readouterr()
