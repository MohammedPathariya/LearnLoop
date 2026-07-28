#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

CURRENT_BRANCH="$(git branch --show-current)"
if [[ "$CURRENT_BRANCH" != "main" ]]; then
  echo "Expected to verify on main, but current branch is: $CURRENT_BRANCH" >&2
  exit 1
fi

echo "==> Checking Git diff whitespace"
git diff --check
git diff --cached --check

echo "==> Running backend tests"
python3.11 -m pytest

echo "==> Running frontend tests"
npm --prefix frontend test

echo "==> Running frontend production build"
npm --prefix frontend run build

echo "==> Auditing frontend production dependencies"
npm --prefix frontend audit --omit=dev

echo "==> Verification passed"
