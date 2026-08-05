#!/usr/bin/env bash
set -euo pipefail
REPO="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fail(){ echo "SBP-001 DOCTOR FAIL: $*" >&2; exit 1; }
[[ -d "$REPO/.git" ]]||fail "Not a Git repository"
[[ "$(git -C "$REPO" branch --show-current)" == "master" ]]||fail "Expected master branch"
[[ -f "$REPO/seymour-bch-node/umbrel-app.yml" ]]||fail "Missing BCH manifest"
grep -q "Initial placeholder app" "$REPO/seymour-bch-node/umbrel-app.yml"||fail "Expected BCH placeholder baseline"
python3 -m py_compile "$ROOT/tests/verify.py"
echo "SBP-001 doctor: PASS"
