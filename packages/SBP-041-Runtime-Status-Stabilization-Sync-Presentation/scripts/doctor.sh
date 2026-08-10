#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
JS="$ROOT/seymour-blockchain-manager/data/web/app.js"
CSS="$ROOT/seymour-blockchain-manager/data/web/style.css"

[[ -f "$JS" ]] || { echo "SBP-041 doctor: app.js missing"; exit 1; }
[[ -f "$CSS" ]] || { echo "SBP-041 doctor: style.css missing"; exit 1; }

grep -Fq 'function lifecycle(provider)' "$JS"
grep -Fq 'function liveMetrics(provider)' "$JS"
grep -Fq 'runtimeState' "$JS"
grep -Fq '.provider-card.syncing' "$CSS"

echo "SBP-041 doctor: runtime presentation anchors PASS"
echo "SBP-041 doctor: PASS"
