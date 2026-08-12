#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
"$PKG/scripts/doctor.sh" "$ROOT"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$ROOT/backups/sbp-053-$STAMP"
mkdir -p "$BACKUP"
cp -a "$ROOT/scripts/seymour-install-btc" "$BACKUP/seymour-install-btc"
cp -a "$ROOT/seymour-bitcoin-node/data/node/entrypoint.sh" "$BACKUP/entrypoint.sh"

mkdir -p "$ROOT/seymour-bitcoin-node/data/generated" "$ROOT/seymour-bitcoin-node/data/state"
cp "$PKG/payload/seymour-bitcoin-node/data/generated/.gitkeep" "$ROOT/seymour-bitcoin-node/data/generated/.gitkeep"
cp "$PKG/payload/seymour-bitcoin-node/data/state/.gitkeep" "$ROOT/seymour-bitcoin-node/data/state/.gitkeep"

chmod +x "$ROOT/seymour-bitcoin-node/data/node/entrypoint.sh" "$ROOT/scripts/seymour-install-btc"
python3 "$PKG/scripts/patch-installer.py" "$ROOT"
chmod +x "$ROOT/scripts/seymour-install-btc"

printf '%s\n' "$BACKUP" > "$ROOT/backups/sbp-053-latest"
echo "Backup: $BACKUP"
echo "SBP-053 executable mode hardening installed: PASS"
echo "SBP-053 persistent directory hardening installed: PASS"
echo "SBP-053 native install result verification installed: PASS"
echo "SBP-053 install: PASS"
echo "No Bitcoin container was started, stopped, restarted, or reinstalled."
echo "No Bitcoin chain data was modified."
