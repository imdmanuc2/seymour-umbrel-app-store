#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

SOURCE="$PKG/payload/seymour-bitcoin-node"
TARGET="$ROOT/seymour-bitcoin-node"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$ROOT/backups/sbp-050-$STAMP"

"$PKG/scripts/doctor.sh" "$ROOT"

mkdir -p "$BACKUP"

if [[ -d "$TARGET" ]]; then
  cp -a "$TARGET" "$BACKUP/seymour-bitcoin-node"
fi

rm -rf "$TARGET"
cp -a "$SOURCE" "$TARGET"

chmod +x "$TARGET/data/node/entrypoint.sh"

printf '%s\n' "$BACKUP" > "$ROOT/backups/sbp-050-latest"

echo "Backup: $BACKUP"
echo "SBP-050 Bitcoin Core app foundation installed: PASS"
echo "SBP-050 node entrypoint installed: PASS"
echo "SBP-050 status service installed: PASS"
echo "SBP-050 runtime contract installed: PASS"
echo "SBP-050 install: PASS"
echo
echo "No Bitcoin node was started."
echo "No blockchain data was created or modified."
echo "No lifecycle write was executed."
