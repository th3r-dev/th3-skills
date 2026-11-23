"""Invariants for the name generator.

The point of these tests is not that the generator produces *some* output —
it is that every record it produces is impossible to mistake for a real
person, and impossible to mistake for a real citizen's ID.
"""

import json
import random

import pytest

import gen_names as g


# ------------------------------------------------------------------ national ID

def test_validator_accepts_well_formed_ids():
    """Sanity-check the checksum implementation against constructed IDs."""
    rng = random.Random(1)
    for _ in range(2000):
        body = "".join(str(rng.randint(0, 9)) for _ in range(12))
        assert g.is_valid_thai_id(body + str(g.id_check_digit(body)))


def test_validator_rejects_wrong_check_digit():
    rng = random.Random(2)
    for _ in range(2000):
        body = "".join(str(rng.randint(0, 9)) for _ in range(12))
        correct = g.id_check_digit(body)
        wrong = (correct + rng.randint(1, 9)) % 10
        assert not g.is_valid_thai_id(body + str(wrong))


def test_validator_rejects_malformed():
    for bad in ["", "123", "0" * 12, "0" * 14, "abcdefghijklm"]:
        assert not g.is_valid_thai_id(bad)


@pytest.mark.parametrize("seed", range(20))
def test_generated_ids_never_have_a_valid_checksum(seed):
    """The core safety property: a mock ID can never belong to anyone."""
    rng = random.Random(seed)
    for _ in range(1000):
        nid = g.make_invalid_id(rng, prefix=rng.choice("09"))
        assert len(nid) == 13 and nid.isdigit()
        assert nid[0] in "09", "must use an unissued leading digit"
        assert not g.is_valid_thai_id(nid), "leaked a structurally real ID"


def test_id_formatting_round_trips():
    rng = random.Random(3)
    nid = g.make_invalid_id(rng)
    formatted = g.format_id(nid)
    assert formatted.replace(" ", "") == nid


# ----------------------------------------------------------------------- names

def _markers():
    return set(g.GIVEN_MARKERS)


@pytest.mark.parametrize("seed", range(10))
def test_every_given_name_starts_with_a_marker(seed):
    rng = random.Random(seed)
    for rows in (
        g.gen_people(40, rng),
        g.gen_people(40, rng, use_roles=True),
        g.gen_people(40, rng, use_titles=True),
        g.gen_people(40, rng, use_roles=True, use_titles=True),
        g.gen_people(40, rng, thai_digits=True),
    ):
        for r in rows:
            assert any(r["given_name"].startswith(m) for m in _markers()), r


def test_surnames_are_markers_or_roles():
    rng = random.Random(0)
    allowed = set(g.SURNAME_MARKERS)
    for r in g.gen_people(30, rng):
        stripped = r["surname"].rstrip("0123456789" + g.THAI_DIGITS)
        assert stripped in allowed, r

    for r in g.gen_people(30, rng, use_roles=True):
        assert r["surname"] in set(g.ROLES), r


def test_no_blocklisted_token_is_ever_a_given_name():
    """จำลอง is a real given name; it may only appear inside a compound."""
    import check_mock_names as c
    rng = random.Random(7)
    blocked = set(c.GIVEN_NAMES) | set(c.SURNAMES)
    rows = (g.gen_people(200, rng)
            + g.gen_people(200, rng, use_roles=True, use_titles=True)
            + g.gen_companies(100, rng))
    for r in rows:
        for field in ("given_name", "surname", "name"):
            value = r.get(field)
            if value:
                assert value not in blocked, r


def test_single_record_gets_no_index_suffix():
    rows = g.gen_people(1, random.Random(0))
    assert rows[0]["surname"] in set(g.SURNAME_MARKERS)


def test_indexes_are_zero_padded_so_string_sort_matches_numeric_sort():
    rows = g.gen_people(12, random.Random(0))
    suffixes = [r["surname"][-3:] for r in rows]
    assert suffixes[0] == "001" and suffixes[-1] == "012"
    assert sorted(suffixes) == suffixes


def test_thai_digit_mode_emits_thai_numerals():
    rows = g.gen_people(3, random.Random(0), thai_digits=True)
    assert any(ch in g.THAI_DIGITS for ch in rows[0]["surname"])
    assert not any(ch.isdigit() and ch.isascii() for ch in rows[0]["surname"])


def test_full_name_is_the_parts_joined():
    rows = g.gen_people(10, random.Random(0), use_titles=True)
    for r in rows:
        parts = [p for p in (r["title"], r["given_name"], r["surname"]) if p]
        assert r["full_name"] == " ".join(parts)


def test_titles_cycle_through_all_forms():
    rows = g.gen_people(len(g.TITLES), random.Random(0), use_titles=True)
    assert {r["title"] for r in rows} == {t for t, _ in g.TITLES}


# ------------------------------------------------------------------- contact

def test_emails_use_reserved_domains_only():
    rows = g.gen_people(25, random.Random(0), with_contact=True)
    for r in rows:
        domain = r["email"].split("@", 1)[1]
        assert domain in {"example.com", "example.net", "example.org",
                          "test.invalid"}, r


def test_phones_keep_a_real_prefix_and_an_all_zeros_block():
    rows = g.gen_people(25, random.Random(0), with_contact=True)
    for r in rows:
        assert r["phone"].startswith("0")
        assert r["phone"][1] in "689", "must keep a real Thai mobile prefix"
        assert r["phone"][2:6] == "0000", "subscriber block must be unmistakable"
        assert len(r["phone"]) == 10


# ---------------------------------------------------------------- determinism

@pytest.mark.parametrize("kwargs", [
    {},
    {"use_roles": True},
    {"use_titles": True, "with_id": True, "with_contact": True},
])
def test_same_seed_produces_identical_output(kwargs):
    a = g.gen_people(25, random.Random(99), **kwargs)
    b = g.gen_people(25, random.Random(99), **kwargs)
    assert a == b


def test_different_seeds_differ():
    a = g.gen_people(25, random.Random(1), with_id=True)
    b = g.gen_people(25, random.Random(2), with_id=True)
    assert a != b


# ------------------------------------------------------------------ edge cases

def test_edge_cases_cover_the_documented_hazards():
    rows = g.gen_edge_cases()
    joined = " ".join(r["full_name"] for r in rows)
    assert "​" in joined, "zero-width space case missing"
    assert "์" in joined, "การันต์ case missing"
    assert "ฤ" in joined, "ฤ case missing"
    assert any(" " in r["surname"].strip() for r in rows), "ณ-surname case missing"
    assert any(len(r["given_name"]) == 1 for r in rows), "min-length case missing"
    assert any(len(r["given_name"]) > 25 for r in rows), "long-name case missing"
    assert all(r["note"] for r in rows), "every edge case needs a note"


def test_edge_cases_are_stable():
    assert g.gen_edge_cases() == g.gen_edge_cases()


# --------------------------------------------------------------------- output

def test_emitters_produce_parseable_output():
    rows = g.gen_people(5, random.Random(0), with_id=True)

    parsed = json.loads(g.emit_json(rows))
    assert len(parsed) == 5

    csv_out = g.emit_csv(rows)
    assert len(csv_out.splitlines()) == 6  # header + 5

    sql = g.emit_sql(rows, "users")
    assert sql.count("INSERT INTO users") == 5
    assert sql.rstrip().endswith(";")

    assert len(g.emit_table(rows).splitlines()) == 7  # header + rule + 5


def test_sql_escapes_single_quotes():
    rows = [{"given_name": "ทดสอบ's", "surname": "นามสมมุติ"}]
    assert "''" in g.emit_sql(rows, "t")


@pytest.mark.parametrize("name", [
    "users", "mock_users", "t1", "_private", "public.users",
])
def test_sql_identifiers_accepts_valid_names(name):
    assert g.quote_sql_identifier(name) == name


@pytest.mark.parametrize("name", [
    "users; DROP TABLE students",
    "users--",
    "users'",
    'users"',
    "users WHERE 1=1",
    "1users",
    "",
    "a.b.c",
    "ตาราง",
    "users)",
])
def test_sql_identifiers_rejects_anything_that_could_carry_syntax(name):
    with pytest.raises(ValueError):
        g.quote_sql_identifier(name)


def test_emit_sql_rejects_an_unsafe_table_name():
    rows = g.gen_people(1, random.Random(0))
    with pytest.raises(ValueError):
        g.emit_sql(rows, "users; DROP TABLE users")


def test_sql_literal_quoting():
    assert g.quote_sql_literal("plain") == "'plain'"
    assert g.quote_sql_literal("it's") == "'it''s'"
    assert g.quote_sql_literal("a\x00b") == "'ab'", "NUL must be dropped"
    # Backslash is not a standard-SQL escape and must pass through untouched.
    assert g.quote_sql_literal("back\\slash") == "'back\\slash'"


def test_sql_output_has_balanced_quotes():
    rows = g.gen_people(20, random.Random(0), with_id=True, with_contact=True)
    for line in g.emit_sql(rows, "users").splitlines():
        assert line.count("'") % 2 == 0, line
        assert line.startswith("INSERT INTO users (") and line.endswith(");")


def test_emitters_handle_empty_input():
    for fn in (g.emit_table, g.emit_csv, g.emit_json):
        fn([])
    assert g.emit_sql([], "t") == ""


# ----------------------------------------------------------------------- CLI

@pytest.mark.parametrize("argv", [
    ["--count", "3"],
    ["--count", "3", "--format", "json"],
    ["--count", "3", "--format", "csv"],
    ["--count", "3", "--format", "sql", "--table", "mock"],
    ["--count", "3", "--roles", "--titles"],
    ["--count", "3", "--with-id", "--with-contact"],
    ["--count", "3", "--companies"],
    ["--count", "3", "--thai-digits"],
    ["--edge-cases"],
    ["--edge-cases", "--format", "json"],
])
def test_cli_exits_zero(argv, capsys):
    assert g.main(argv) == 0
    assert capsys.readouterr().out.strip()
