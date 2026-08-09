#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fail(){ echo "SBP-024 doctor: FAIL — $*" >&2; exit 1; }
[[ -d "$ROOT/.git" ]] || fail "Umbrel app-store repository not found"
[[ "$(git -C "$ROOT" branch --show-current)" == "master" ]] || fail "Expected master branch"
for file in seymour-bch-node/docker-compose.yml seymour-bch-node/data/status/app.py shared/umbrel_control/bridge.py; do
  [[ -f "$ROOT/$file" ]] || fail "Missing $file"
done
grep -q 'healthcheck:' "$ROOT/seymour-bch-node/docker-compose.yml" || fail "BCH healthcheck override not found"
grep -q '_state_matches_action' "$ROOT/shared/umbrel_control/bridge.py" || fail "Lifecycle helper not found"
python3 -m py_compile "$PKG/payload/patch_bch_healthcheck.py" "$PKG/payload/patch_lifecycle_reconciliation.py"
echo "SBP-024 doctor: PASS"
