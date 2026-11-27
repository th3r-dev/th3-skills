#!/usr/bin/env bash
# Hard prerequisites for poc-spec-driven-builder's git/ticket/PR workflow.
# Exits non-zero with a one-line fix on the first missing requirement.
set -euo pipefail

fail() {
  echo "✗ $1" >&2
  exit 1
}

command -v git >/dev/null 2>&1 || fail "git is not installed. Install git, then re-run."
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || fail "Not inside a git repository. Run 'git init' or clone the target repo first."
command -v gh >/dev/null 2>&1 || fail "GitHub CLI (gh) is not installed. Install it: https://cli.github.com"
gh auth status >/dev/null 2>&1 || fail "GitHub CLI is not authenticated. Run 'gh auth login' first."

echo "✓ git present and inside a repo"
echo "✓ gh CLI present and authenticated"
echo "Note: Jira/Monday.com integration is optional and detected separately (see SKILL.md Step 0.5) — GitHub Issues is always the fallback ticket tracker since gh is already required."
