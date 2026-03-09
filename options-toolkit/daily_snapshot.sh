#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"

git add experience/ memory/ strategy/ options-toolkit/data/

if ! git diff --cached --quiet; then
  git commit -m "daily snapshot $(date +%F)"
  git push
fi
