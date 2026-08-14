#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
BACKUP="$(find "$ROOT/backups" -maxdepth 1 -type d -name 'sbp-062.1-*' | sort | tail -1)"
test -n "$BACKUP"
cp -a "$BACKUP/seymour-bitcoin-node-multiarch.yml" \
  "$ROOT/.github/workflows/seymour-bitcoin-node-multiarch.yml"
echo "SBP-062.1 rollback: PASS"
echo "No blockchain runtime or blockchain data was modified."
