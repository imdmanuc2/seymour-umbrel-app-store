#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
WEB="$ROOT/seymour-blockchain-manager/data/web"
BACKUP="$(find "$ROOT/backups" -maxdepth 1 -type d -name 'sbp-060.5-*' | sort | tail -1)"
test -d "$BACKUP"
for f in app.js telemetry.py bch_runtime_probe.py; do cp -a "$BACKUP/$f" "$WEB/$f"; done
if [[ -f "$BACKUP/runtime_registry.py" ]]; then cp -a "$BACKUP/runtime_registry.py" "$WEB/runtime_registry.py"; else rm -f "$WEB/runtime_registry.py"; fi
echo "SBP-060.5 rollback: PASS"
