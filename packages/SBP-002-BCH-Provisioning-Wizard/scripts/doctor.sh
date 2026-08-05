#!/usr/bin/env bash
set -euo pipefail
REPO="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fail(){ echo "SBP-002 DOCTOR FAIL: $*" >&2; exit 1; }

[[ -d "$REPO/.git" ]] || fail "Not a Git repository"
[[ "$(git -C "$REPO" branch --show-current)" == "master" ]] || fail "Expected master"
[[ -f "$REPO/seymour-bch-node/data/status/app.py" ]] || fail "Missing SBP-001 status app"
grep -q 'version: "0.2.0-alpha"' "$REPO/seymour-bch-node/umbrel-app.yml" || fail "Missing SBP-001 baseline"

python3 -m py_compile "$ROOT/tests/verify.py" "$ROOT/payload/seymour-bch-node/data/status/provisioning.py"
echo "SBP-002 doctor: PASS"
