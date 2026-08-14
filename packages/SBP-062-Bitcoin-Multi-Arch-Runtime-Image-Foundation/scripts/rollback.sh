#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"

BACKUP="$(
  find "$ROOT/backups" -maxdepth 1 -type d -name 'sbp-062-*' |
  sort |
  tail -1
)"
test -n "$BACKUP"

rm -rf "$ROOT/runtime-images/bitcoin-core"

if [ -d "$BACKUP/bitcoin-core" ]; then
  cp -a "$BACKUP/bitcoin-core" "$ROOT/runtime-images/bitcoin-core"
fi

rm -f "$ROOT/.github/workflows/seymour-bitcoin-node-multiarch.yml"

if [ -f "$BACKUP/seymour-bitcoin-node-multiarch.yml" ]; then
  cp -a \
    "$BACKUP/seymour-bitcoin-node-multiarch.yml" \
    "$ROOT/.github/workflows/seymour-bitcoin-node-multiarch.yml"
fi

echo "SBP-062 rollback: PASS"
echo "No blockchain runtime or blockchain data was modified."
