#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

mkdir -p .git/hooks
cp scripts/git-hooks/pre-commit .git/hooks/pre-commit
cp scripts/git-hooks/pre-push .git/hooks/pre-push
chmod +x .git/hooks/pre-commit .git/hooks/pre-push

echo "Installed LearnLoop Git hooks:"
echo "- pre-commit: staged-file guardrails plus backend and frontend tests"
echo "- pre-push: full verification including frontend production build"
