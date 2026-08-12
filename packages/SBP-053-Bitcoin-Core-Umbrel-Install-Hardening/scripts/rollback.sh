#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
LATEST="$ROOT/backups/sbp-053-latest"
[[ -f "$LATEST" ]] || { echo "SBP-053 rollback: backup pointer missing" >&2; exit 1; }
BACKUP="$(cat "$LATEST")"
[[ -d "$BACKUP" ]] || { echo "SBP-053 rollback: backup missing: $BACKUP" >&2; exit 1; }
cp -a "$BACKUP/seymour-install-btc" "$ROOT/scripts/seymour-install-btc"
cp -a "$BACKUP/entrypoint.sh" "$ROOT/seymour-bitcoin-node/data/node/entrypoint.sh"
rm -f "$ROOT/seymour-bitcoin-node/data/generated/.gitkeep" "$ROOT/seymour-bitcoin-node/data/state/.gitkeep"
rmdir "$ROOT/seymour-bitcoin-node/data/generated" 2>/dev/null || true
rmdir "$ROOT/seymour-bitcoin-node/data/state" 2>/dev/null || true
echo "SBP-053 rollback: PASS"
echo "No running Bitcoin container or chain data was modified."
