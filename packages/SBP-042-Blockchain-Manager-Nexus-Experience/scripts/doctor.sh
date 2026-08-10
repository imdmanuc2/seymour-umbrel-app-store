#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
WEB="$ROOT/seymour-blockchain-manager/data/web"

for f in "$WEB/app.js" "$WEB/index.html" "$WEB/style.css"; do
  [[ -f "$f" ]] || { echo "SBP-042 doctor: missing $f"; exit 1; }
done

grep -Fq 'function presentedRuntime(provider)' "$WEB/app.js"
grep -Fq 'RUNTIME_PRESENTATION_GRACE_MS' "$WEB/app.js"
grep -Fq '<section class="summary">' "$WEB/index.html"
grep -Fq '.provider-grid' "$WEB/style.css"

echo "SBP-042 doctor: Nexus experience anchors PASS"
echo "SBP-042 doctor: PASS"
