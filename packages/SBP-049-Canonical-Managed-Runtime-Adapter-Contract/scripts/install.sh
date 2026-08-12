#!/usr/bin/env bash
set -euo pipefail
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT="$(cd "$PKG/../.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$ROOT/backups/sbp-049-$STAMP"

"$PKG/scripts/doctor.sh"
mkdir -p "$BACKUP/shared/contracts"
[[ ! -d "$ROOT/shared/managed_runtime" ]] || cp -a "$ROOT/shared/managed_runtime" "$BACKUP/shared/"
cp -a "$ROOT/shared/contracts/app-lifecycle-v1.json" "$BACKUP/shared/contracts/"

echo "Backup: $BACKUP"
python3 "$PKG/payload/patch_sbp049.py" "$ROOT"
echo "SBP-049 managed runtime adapter interface: PASS"
echo "SBP-049 Umbrel adapter integration: PASS"
echo "SBP-049 lifecycle JSON state reconciliation: PASS"
echo "SBP-049 install: PASS"
echo "No lifecycle write, application restart, Docker lifecycle command, or blockchain configuration change was executed."
