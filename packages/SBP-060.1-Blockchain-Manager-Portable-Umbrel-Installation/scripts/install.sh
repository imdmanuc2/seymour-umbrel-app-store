#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
"$PKG/scripts/doctor.sh" "$ROOT"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$ROOT/backups/sbp-060.1-$STAMP"
mkdir -p "$BACKUP/seymour-blockchain-manager"
cp -a "$ROOT/seymour-blockchain-manager/docker-compose.yml" "$BACKUP/seymour-blockchain-manager/docker-compose.yml"

python3 "$PKG/scripts/patch.py" "$ROOT"

cp "$PKG/payload/tests/test_blockchain_manager_portable_install.py"   "$ROOT/tests/test_blockchain_manager_portable_install.py"

printf '%s\n' "$BACKUP" > "$ROOT/backups/sbp-060.1-latest"

echo "Backup: $BACKUP"
echo "SBP-060.1 private env hard dependency removed: PASS"
echo "SBP-060.1 self-contained control payload installed: PASS"
echo "SBP-060.1 self-contained shared payload installed: PASS"
echo "SBP-060.1 portable compose mounts installed: PASS"
echo "SBP-060.1 install: PASS"
echo "No Umbrel app was installed/restarted and no blockchain runtime was modified."
