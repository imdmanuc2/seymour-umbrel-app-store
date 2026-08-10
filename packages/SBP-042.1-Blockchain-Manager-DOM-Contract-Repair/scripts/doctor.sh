#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
WEB="$ROOT/seymour-blockchain-manager/data/web"
JS="$WEB/app.js"
HTML="$WEB/index.html"

[[ -f "$JS" ]] || { echo "SBP-042.1 doctor: app.js missing"; exit 1; }
[[ -f "$HTML" ]] || { echo "SBP-042.1 doctor: index.html missing"; exit 1; }

grep -Fq 'function renderOperationalSummary()' "$JS"
grep -Fq 'function renderRuntimeFocus()' "$JS"
grep -Fq 'async function loadCatalog()' "$JS"
grep -Fq 'id="runtimeFocus"' "$HTML"

echo "SBP-042.1 doctor: SBP-042 frontend anchors PASS"
echo "SBP-042.1 doctor: PASS"
