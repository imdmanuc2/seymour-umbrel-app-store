#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"; WEB="$ROOT/seymour-blockchain-manager/data/web"
for f in "$WEB/app.py" "$WEB/app.js" "$WEB/style.css" "$WEB/bch_rpc_probe.py" "$WEB/bch_runtime_probe.py"; do [[ -f "$f" ]] || { echo "SBP-047 doctor: missing $f"; exit 1; }; done
grep -Fq 'def call_rpc(' "$WEB/bch_rpc_probe.py"; grep -Fq 'async function showSyncManager(providerId)' "$WEB/app.js"; grep -Fq 'if self.path == "/api/sync":' "$WEB/app.py"
echo 'SBP-047 doctor: sync performance anchors PASS'; echo 'SBP-047 doctor: PASS'
