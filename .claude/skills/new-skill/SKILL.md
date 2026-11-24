---
name: new-skill
description: Scaffold a new skill in this repo (skills/in-progress/<name>/SKILL.md and a CI workflow if it has tests; README and plugin.json on promotion to shipped/). Use when adding a skill to th3-skills.
disable-model-invocation: true
---

Scaffold skill `$ARGUMENTS` (kebab-case) in this repo.

1. Confirm you're on a `feat/<name>` branch cut from `dev`; create it if not.
2. Create `skills/in-progress/<name>/SKILL.md` with frontmatter of only `name` and a trigger-heavy `description` ("Use WHENEVER ..."), plus a short body. Add `references/`, `scripts/`, `tests/` only if needed. Scripts stdlib-only, with `--selftest` / `--dry-run` where useful.
3. No README or `plugin.json` entry yet. When the owner says it ships: `git mv` it to `skills/shipped/`, add a one-paragraph README entry in the same style as the others, add it to `plugin.json` `skills`, and its icon/hero (CLAUDE.md).
4. If the skill has tests, copy `.github/workflows/qa.yml` to `.github/workflows/<name>.yml`: change `name`, both `paths` filters, `working-directory`, the pinned `uv pip install --no-build` line (versions with wheels for every matrix Python) and the self-check steps.
5. Mock data must use thai-mock-naming markers; no client hosts, IPs or names.
6. Run the skill's tests locally and `python3 scripts/check_layout.py` before finishing.
