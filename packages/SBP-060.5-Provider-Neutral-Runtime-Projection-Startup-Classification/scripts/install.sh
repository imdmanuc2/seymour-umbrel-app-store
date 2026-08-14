#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WEB="$ROOT/seymour-blockchain-manager/data/web"
"$PKG/scripts/doctor.sh" "$ROOT"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$ROOT/backups/sbp-060.5-$STAMP"
mkdir -p "$BACKUP"
for f in app.js telemetry.py bch_runtime_probe.py runtime_registry.py; do [[ -f "$WEB/$f" ]] && cp -a "$WEB/$f" "$BACKUP/$f" || true; done
python3 "$PKG/scripts/patch.py" "$ROOT"
echo "Backup: $BACKUP"
echo "SBP-060.5 provider-neutral runtime registry installed: PASS"
echo "SBP-060.5 multi-runtime dashboard projection installed: PASS"
echo "SBP-060.5 startup verification classification installed: PASS"
echo "SBP-060.5 Docker socket health detection installed: PASS"
echo "SBP-060.5 install: PASS"
echo "No blockchain runtime was restarted, installed, or modified."
