#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WF="$REPO/.github/workflows/seymour-monero-node-multiarch.yml"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$REPO/backups/sbp-071.1-$STAMP"

"$PKG/scripts/doctor.sh"

mkdir -p "$BACKUP"
cp "$WF" "$BACKUP/seymour-monero-node-multiarch.yml"

python3 "$PKG/scripts/patch.py" "$WF"

echo "SBP-071.1 install: PASS"
echo "Backup: $BACKUP"
echo "No blockchain runtime was modified."
