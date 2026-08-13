#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
"$PKG/scripts/doctor.sh" "$ROOT"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$ROOT/backups/sbp-060-$STAMP"

mkdir -p   "$BACKUP/shared/provider_catalog"   "$BACKUP/seymour-blockchain-manager/data/catalog"   "$BACKUP/seymour-blockchain-manager/data/web"

cp -a "$ROOT/shared/provider_catalog/providers.v1.json" "$BACKUP/shared/provider_catalog/"
cp -a "$ROOT/seymour-blockchain-manager/data/catalog/providers.v1.json" "$BACKUP/seymour-blockchain-manager/data/catalog/"
cp -a "$ROOT/seymour-blockchain-manager/data/web/app.py" "$BACKUP/seymour-blockchain-manager/data/web/"
cp -a "$ROOT/seymour-blockchain-manager/data/web/app.js" "$BACKUP/seymour-blockchain-manager/data/web/"

python3 "$PKG/scripts/patch.py" "$ROOT"

cp "$PKG/payload/tests/test_bitcoin_provider_activation.py"   "$ROOT/tests/test_bitcoin_provider_activation.py"

printf '%s\n' "$BACKUP" > "$ROOT/backups/sbp-060-latest"

echo "Backup: $BACKUP"
echo "SBP-060 Bitcoin catalog activation installed: PASS"
echo "SBP-060 provider-specific preflight installed: PASS"
echo "SBP-060 Bitcoin install UI activation installed: PASS"
echo "SBP-060 install: PASS"
echo "No live blockchain installation was executed."
