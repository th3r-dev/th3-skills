#!/usr/bin/env bash
# Ensures a `dev` branch exists (creating it off the repo's default branch
# if needed) and cuts feat/<ticket-id>-<slug> off it. Run from Step 2.5,
# after a ticket exists, before any implementation work.
#
# Usage: ensure_branches.sh <ticket-id> <slug>
set -euo pipefail

if [ $# -ne 2 ]; then
  echo "Usage: $0 <ticket-id> <slug>" >&2
  exit 1
fi

TICKET_ID="$1"
SLUG="$2"
FEAT_BRANCH="feat/${TICKET_ID}-${SLUG}"

git fetch origin --quiet 2>/dev/null || true

DEFAULT_BRANCH="$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || true)"
if [ -z "$DEFAULT_BRANCH" ]; then
  if git show-ref --verify --quiet refs/heads/main; then
    DEFAULT_BRANCH=main
  elif git show-ref --verify --quiet refs/heads/master; then
    DEFAULT_BRANCH=master
  else
    DEFAULT_BRANCH="$(git branch --show-current)"
  fi
fi

if git show-ref --verify --quiet refs/heads/dev; then
  git checkout dev
elif git show-ref --verify --quiet refs/remotes/origin/dev; then
  git checkout -b dev origin/dev
else
  echo "No dev branch found — creating it off ${DEFAULT_BRANCH}."
  git checkout "${DEFAULT_BRANCH}"
  git checkout -b dev
  git push -u origin dev
fi

if git show-ref --verify --quiet "refs/heads/${FEAT_BRANCH}"; then
  echo "Branch ${FEAT_BRANCH} already exists locally — check it out manually if that's intentional." >&2
  exit 1
fi

git checkout -b "${FEAT_BRANCH}"
echo "✓ on ${FEAT_BRANCH} (branched from dev)"
