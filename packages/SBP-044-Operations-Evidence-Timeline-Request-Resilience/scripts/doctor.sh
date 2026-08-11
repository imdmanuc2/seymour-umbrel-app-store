#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
JS="$ROOT/seymour-blockchain-manager/data/web/app.js"
CSS="$ROOT/seymour-blockchain-manager/data/web/style.css"

[[ -f "$JS" ]] || { echo "SBP-044 doctor: app.js missing"; exit 1; }
[[ -f "$CSS" ]] || { echo "SBP-044 doctor: style.css missing"; exit 1; }

grep -Fq 'async function lifecycleRequest' "$JS"
grep -Fq 'async function showOperationsCenter(providerId)' "$JS"
grep -Fq '/api/lifecycle/history' "$JS"
grep -Fq '/api/operations/diagnostics' "$JS"
grep -Fq '/api/operations/logs' "$JS"

echo "SBP-044 doctor: Operations evidence anchors PASS"
echo "SBP-044 doctor: PASS"
