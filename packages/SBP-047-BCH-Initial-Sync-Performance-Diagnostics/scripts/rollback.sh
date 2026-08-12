#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"; MARKER="$ROOT/backups/sbp-047-latest"; WEB="$ROOT/seymour-blockchain-manager/data/web"; INSTALLED="/home/umbrel/umbrel/app-data/seymour-blockchain-manager/data/web"
[[ -f "$MARKER" ]] || { echo 'SBP-047 rollback: backup marker missing'; exit 1; }; BACKUP="$(cat "$MARKER")"
for f in app.py app.js style.css; do cp -a "$BACKUP/$f" "$WEB/$f"; done; rm -f "$WEB/sync_performance.py"
if [[ -d "$INSTALLED" ]]; then for f in app.py app.js style.css; do cp -a "$WEB/$f" "$INSTALLED/$f"; done; rm -f "$INSTALLED/sync_performance.py"; fi
echo 'SBP-047 rollback: sync performance diagnostics removed'; echo 'Blockchain Manager restart is required after rollback.'; echo 'SBP-047 rollback: PASS'
