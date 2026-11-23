# Changelog

All notable changes to `thai-mock-naming`. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2026-10-13

First release.

### Added

- `SKILL.md` — the one rule (the given-name slot always carries a test marker)
  and the three tiers that follow from it: default pair, role-bearing, indexed.
- `references/name-bank.md` — approved given-name and surname markers, role
  tokens, ready-made sets, juristic-person forms, and the blocklist of real
  Thai names that routinely appear in mock data.
- `references/edge-cases.md` — names built to break things: length boundaries,
  stacked tone marks, การันต์, `ณ อยุธยา` surnames containing spaces, ฤ/ฦ,
  sara am, mixed script, whitespace and zero-width characters, and a Thai
  collation ordering set.
- `references/identity-fields.md` — national ID checksum algorithm and how to
  deliberately fail it, juristic person numbers, phone numbers, reserved email
  domains, addresses, and postcodes.
- `scripts/gen_names.py` — generator with `--roles`, `--titles`, `--with-id`,
  `--with-contact`, `--companies`, `--thai-digits`, `--edge-cases`, and
  `--seed`; emits table, JSON, CSV, or SQL.
- `scripts/check_mock_names.py` — linter that flags plausible-real Thai names,
  with `--exclude`, `.mocknamesignore`, and inline `mock-names-ignore` markers.
- 98 tests covering generator invariants and linter behaviour.
- CI across Python 3.8–3.13, MIT license, pre-commit hook definition.

### Notes on design decisions

- **Markers live in the given name, not the surname.** The given name appears
  first in nearly every list, sort, salutation, and truncated column, so a
  record stays legible as fake even when the surname is cut off.
- **Generated national IDs always fail their checksum.** A mock ID with a valid
  checksum is a well-formed Thai national ID that some real citizen holds. This
  is enforced by test, over 20,000 generated IDs across 20 seeds.
- **The linter segments Thai rather than matching substrings.** Thai has no word
  separators, and `จำลอง` is both a real given name and the tail of the approved
  marker `ข้อมูลจำลอง`. Naive substring matching flagged every legitimate
  `ข้อมูลจำลอง`, which would have trained people to ignore the linter. Each line
  is split into maximal Thai runs and the run is judged as a whole.
- **`จำลอง` is not an approved standalone marker**, despite meaning "simulated",
  because it is a real Thai given name. It is permitted only inside a compound.

[1.0.0]: https://github.com/TheeraphatStudent/th3-skills/tree/main/skills/thai-mock-naming
