#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "== Tool presence =="
for t in subfinder amass httpx rg jq python3; do
  if command -v "$t" >/dev/null 2>&1; then
    echo "OK  $t"
  else
    echo "MISS $t"
  fi
done

echo
echo "== Script syntax =="
for f in "$ROOT_DIR"/scripts/*.sh; do
  bash -n "$f"
  echo "OK  ${f#$ROOT_DIR/}"
done

echo
echo "== AG2 dry run =="
(
  cd "$ROOT_DIR/ag2"
  python3 run_team.py --dry-run >/dev/null
)
echo "OK  ag2/run_team.py --dry-run"

echo
echo "Readiness check complete."
