#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
LATEST="$ROOT/backups/sbp-052-latest"
TARGET="$ROOT/scripts/seymour-install-btc"
[[ -f "$LATEST" ]] || { echo "SBP-052 rollback: latest backup pointer missing" >&2; exit 1; }
BACKUP="$(cat "$LATEST")"
[[ -d "$BACKUP" ]] || { echo "SBP-052 rollback: backup directory missing: $BACKUP" >&2; exit 1; }
if [[ -f "$BACKUP/seymour-install-btc" ]]; then
  cp -a "$BACKUP/seymour-install-btc" "$TARGET"
  chmod +x "$TARGET"
  echo "SBP-052 rollback: previous BTC install workflow restored"
else
  rm -f "$TARGET"
  echo "SBP-052 rollback: BTC install workflow removed"
fi
echo "SBP-052 rollback: PASS"
echo "No running Bitcoin container or chain data was modified."
