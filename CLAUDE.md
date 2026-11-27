# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

A collection of Claude Code skills, shipped as one plugin (`.claude-plugin/`) and installable per skill via `npx skills`. Most are umbrella skills with sub-skills in subdirs.

**Default workflow:** start any new job through the `th3-skills` front door (`/th3-skills:th3-skills`) — it reads the task and routes to the skill that owns it, defaulting to `plans` for anything that gets built.

## Layout

Skills live in status buckets under `skills/` (after [9arm-skills](https://github.com/thananon/9arm-skills)):

- `shipped/` — production: listed in `plugin.json` `skills`, the README Skills list and the README hero (`assets/hero.py`).
- `in-progress/` — drafts, still tested in CI and installable by name, never in `plugin.json` or the README.
- `personal/` — tied to one machine or client; `deprecated/` — kept for history. Neither is listed anywhere.

Promoting or demoting a skill is a `git mv` between buckets plus: its workflow's `paths` and `working-directory`, the `plugin.json` list, the README entry and hero index. Links between skills in the same bucket use `../<skill>/`; across buckets, `../../<bucket>/<skill>/`. `python3 scripts/check_layout.py` (CI: `layout.yml`) fails on any mismatch, a flat `skills/<name>/` path or a broken relative link.

## Git

- Branch `feat/<skill-slug>` or `fix/<slug>` off `dev`; PR into `dev`; `dev` → `main` is the release.
- Commit subjects are plain imperative, optionally scoped (`qa: ...`, `fix(thai-mock-naming): ...`).

## Tests

Python runs through **uv** everywhere: locally, in CI, and in the repo's own scripts. No root test config. From inside the skill dir, set up once with the pins its workflow installs, then run pytest and the self-checks CI runs:

```bash
uv venv && uv pip install --no-build <pins from .github/workflows/<skill>.yml>   # add --python 3.8 to test the oldest
uv run --no-project python -m pytest -q
```

- qa: then `uv run --no-project python answer-review/scripts/qa.py selfcheck`, `… excel-import/scripts/run_web.py selftest`, `… ticket-report/scripts/ticket_report.py --selftest`
- devops: then `uv run --no-project python release-scope/scripts/release_scope.py --selftest`
- thai-mock-naming: pytest only (`pytest==8.3.5`, the last pin that supports 3.8–3.13)
- containers: then `uv run --no-project python podman/scripts/reclaim.py --help`
- agent-kit: no pytest; `uv run --script cost/scripts/agent_guard.py --selftest` and `uv run --script prompt-cache/scripts/pcache.py --self-test`

Each skill has its own path-filtered workflow in `.github/workflows/<skill>.yml`, set up with `astral-sh/setup-uv` (uv supplies every matrix Python itself, so the runner's OS doesn't limit the versions). devops/qa/containers run Python 3.10–3.13; thai-mock-naming runs 3.8–3.13, so keep its code 3.8-compatible. CI installs pinned versions with `uv pip install --no-build` (wheels only, SonarCloud rules) — pin only versions that have wheels for every matrix Python, and quote the install line in YAML.

## Agents

Spawning a subagent, fork or Workflow here follows `skills/shipped/agent-kit/cost/SKILL.md`: inline first, set `model` to the cheapest tier that can finish, every brief ends with how done is checked. A PreToolUse hook (`agent_guard.py`) adds the tier table to any Agent call that sets no model.

## Skill conventions

- SKILL.md frontmatter is `name` and `description` only. Descriptions are trigger-heavy ("Use WHENEVER ..."). Sub-skills are prefixed (`qa-excel-import`).
- Scripts are stdlib-only Python unless the skill's CI already pins a dependency. Give them `--dry-run` / `--selftest` / `--help` where they change state or are testable.
- devops and qa were generalised from a client project: no real hosts, IPs, company names or client data in any skill.
- Mock/sample data uses the thai-mock-naming markers (ทดสอบ นามสมมุติ), never real-looking common Thai names. The linter is `skills/shipped/thai-mock-naming/scripts/check_mock_names.py`; a PostToolUse hook runs it on edited files. Files that must contain the blocklist go in that skill's `.mocknamesignore`.
- A new skill starts in `skills/in-progress/` with its own workflow if it has tests; it gets a README entry and a `plugin.json` line when it moves to `shipped/`. `/new-skill <name>` scaffolds this.
- Every skill has an icon and a hero: add its drawing to `assets/icons.py` (it refuses to build while a skill lacks one) and its steps to `assets/skill_heroes.py` (plus the index in `assets/hero.py`), then run them with `uv run assets/…` (each script declares its dependencies in a PEP 723 header) and check with `uv run assets/check_heroes.py`.
