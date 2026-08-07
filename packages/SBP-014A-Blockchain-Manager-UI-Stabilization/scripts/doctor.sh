#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

fail() {
  echo "SBP-014A doctor: FAIL — $*" >&2
  exit 1
}

[[ -d "$REPO/.git" ]] || fail "Repository not found"
[[ "$(git -C "$REPO" branch --show-current)" == "master" ]] \
  || fail "Expected master branch"

APP_JS="$REPO/seymour-blockchain-manager/data/web/app.js"
[[ -f "$APP_JS" ]] || fail "Missing app.js"

for marker in \
  "function renderFilters" \
  "function renderProviders" \
  "showSyncManager" \
  "showAdoptionWizard" \
  "showOperationsCenter"; do
  grep -q "$marker" "$APP_JS" || fail "Missing marker: $marker"
done

python3 -m py_compile \
  "$ROOT/payload/repair_app_js.py" \
  "$ROOT/payload/tests/test_ui_stabilization.py" \
  "$ROOT/payload/tests/test_ui_action_contract.py"

echo "SBP-014A doctor: PASS"
