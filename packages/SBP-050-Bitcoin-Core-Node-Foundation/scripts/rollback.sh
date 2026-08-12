#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"

LATEST="$ROOT/backups/sbp-050-latest"
TARGET="$ROOT/seymour-bitcoin-node"

[[ -f "$LATEST" ]] || {
  echo "SBP-050 rollback: latest backup pointer missing"
  exit 1
}

BACKUP="$(cat "$LATEST")"

[[ -d "$BACKUP" ]] || {
  echo "SBP-050 rollback: backup directory missing: $BACKUP"
  exit 1
}

if [[ -d "$BACKUP/seymour-bitcoin-node" ]]; then
  rm -rf "$TARGET"
  cp -a "$BACKUP/seymour-bitcoin-node" "$TARGET"

  echo "SBP-050 rollback: previous Bitcoin app restored"
else
  rm -rf "$TARGET"

  echo "SBP-050 rollback: placeholder replacement removed"
fi

echo "SBP-050 rollback: PASS"
echo "No running container or blockchain data was modified."
