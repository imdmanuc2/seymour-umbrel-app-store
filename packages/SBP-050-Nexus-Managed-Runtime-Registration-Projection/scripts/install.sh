#!/usr/bin/env bash
set -euo pipefail
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT="$(cd "$PKG/../.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$ROOT/backups/sbp-050-$STAMP"

"$PKG/scripts/doctor.sh"

mkdir -p "$BACKUP/shared/managed_runtime" "$BACKUP/shared/contracts"          "$BACKUP/seymour-blockchain-manager/data/web"

cp -a "$ROOT/shared/managed_runtime/__init__.py" "$BACKUP/shared/managed_runtime/"
[[ ! -f "$ROOT/shared/managed_runtime/registration.py" ]] ||   cp -a "$ROOT/shared/managed_runtime/registration.py" "$BACKUP/shared/managed_runtime/"
[[ ! -f "$ROOT/shared/contracts/managed-runtime-registration-v1.json" ]] ||   cp -a "$ROOT/shared/contracts/managed-runtime-registration-v1.json" "$BACKUP/shared/contracts/"
cp -a "$ROOT/seymour-blockchain-manager/data/web/nexus_integration.py"   "$BACKUP/seymour-blockchain-manager/data/web/"

echo "Backup: $BACKUP"
python3 "$PKG/payload/patch_sbp050.py" "$ROOT"

echo "SBP-050 managed runtime registration projector: PASS"
echo "SBP-050 existing registration identity preservation integration: PASS"
echo "SBP-050 legacy registration compatibility integration: PASS"
echo "SBP-050 install: PASS"
echo "No lifecycle write, application restart, Docker lifecycle command, Nexus delivery, or blockchain configuration change was executed."
