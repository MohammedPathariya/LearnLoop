#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

CURRENT_BRANCH="$(git branch --show-current)"
if [[ "$CURRENT_BRANCH" != "main" ]]; then
  echo "Commits for this revamp should be made on main. Current branch: $CURRENT_BRANCH" >&2
  exit 1
fi

if git diff --cached --diff-filter=ACMR --name-only | grep -E '(^|/)\.env$|(^|/)conversations\.db$' >/dev/null; then
  echo "Refusing to commit staged secrets or mutable local data files." >&2
  echo "Unstage .env files and backend/conversations.db before committing." >&2
  exit 1
fi

echo "==> Checking staged diff whitespace"
git diff --cached --check

echo "==> Running backend tests"
python3.11 -m pytest

echo "==> Running frontend tests"
npm --prefix frontend test

echo "==> Pre-commit checks passed"
