#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 \
  "$ROOT/tests/verify.py" \
  "$REPO"

echo "SBP-003 final verification: PASS"
