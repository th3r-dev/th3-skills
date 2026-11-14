# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

A collection of Claude Code skills in `skills/`, shipped as one plugin (`.claude-plugin/`) and installable per skill via `npx skills`. `devops` and `qa` are umbrella skills with sub-skills in subdirs.

## Git

- Branch `feat/<skill-slug>` or `fix/<slug>` off `dev`; PR into `dxev`; `dev` → `main` is the release.
- Commit subjects are plain imperative, optionally scoped (`qa: ...`, `fix(thai-mock-naming): ...`).

## Tests

No root test config. Run pytest from inside the skill dir, and run the script self-checks CI runs:

- `cd skills/qa && python -m pytest -q`, then `python answer-review/scripts/qa.py selfcheck`, `python excel-import/scripts/run_web.py selftest`, `python ticket-report/scripts/ticket_report.py --selftest`
- `cd skills/devops && python -m pytest -q`, then `python release-scope/scripts/release_scope.py --selftest`
- `cd skills/thai-mock-naming && python -m pytest -q`

Each skill has its own path-filtered workflow in `.github/workflows/<skill>.yml`. devops/qa run Python 3.10–3.13; thai-mock-naming runs 3.8–3.13, so keep its code 3.8-compatible. CI installs pinned versions with `--only-binary :all:` (SonarCloud rules) — pin only versions that have wheels for every matrix Python, and quote the `pip install` line in YAML.

## Skill conventions

- SKILL.md frontmatter is `name` and `description` only. Descriptions are trigger-heavy ("Use WHENEVER ..."). Sub-skills are prefixed (`qa-excel-import`).
- Scripts are stdlib-only Python unless the skill's CI already pins a dependency. Give them `--dry-run` / `--selftest` / `--help` where they change state or are testable.
- devops and qa were generalised from a client project: no real hosts, IPs, company names or client data in any skill.
- Mock/sample data uses the thai-mock-naming markers (ทดสอบ นามสมมุติ), never real-looking common Thai names. The linter is `skills/thai-mock-naming/scripts/check_mock_names.py`; a PostToolUse hook runs it on edited files. Files that must contain the blocklist go in that skill's `.mocknamesignore`.
- A new skill needs a README entry and, if it has tests, its own workflow. `/new-skill <name>` scaffolds this.
