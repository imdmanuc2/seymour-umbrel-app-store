#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
WEB="$ROOT/seymour-blockchain-manager/data/web"
JS="$WEB/app.js"
CSS="$WEB/style.css"

[[ -f "$JS" ]] || { echo "SBP-043 doctor: app.js missing"; exit 1; }
[[ -f "$CSS" ]] || { echo "SBP-043 doctor: style.css missing"; exit 1; }

grep -Fq 'async function showOperationsCenter(providerId)' "$JS"
grep -Fq '/api/operations/diagnostics' "$JS"
grep -Fq '/api/operations/logs' "$JS"
grep -Fq 'presentedRuntime(provider)' "$JS"
grep -Fq '.operation-result' "$CSS"

echo "SBP-043 doctor: Operations frontend anchors PASS"
echo "SBP-043 doctor: PASS"
