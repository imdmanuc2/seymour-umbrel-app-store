#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
for f in \
  "$ROOT/seymour-blockchain-manager/data/web/app.js" \
  "$ROOT/seymour-blockchain-manager/data/web/style.css"
do
  [[ -f "$f" ]] || { echo "SBP-039 doctor: missing $f"; exit 1; }
done
grep -Fq 'function lifecycle(provider)' "$ROOT/seymour-blockchain-manager/data/web/app.js"
grep -Fq 'function showManage(providerId)' "$ROOT/seymour-blockchain-manager/data/web/app.js"
grep -Fq '.provider-card' "$ROOT/seymour-blockchain-manager/data/web/style.css"
echo "SBP-039 doctor: Blockchain Manager frontend anchors PASS"
echo "SBP-039 doctor: PASS"
