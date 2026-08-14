#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"

BACKUP="$(
  find "$ROOT/backups" \
    -maxdepth 1 \
    -type d \
    -name 'sbp-062.1.1-prestage-*' \
    | sort \
    | tail -1
)"

test -n "$BACKUP"

cp -a \
  "$BACKUP/Dockerfile" \
  "$ROOT/runtime-images/bitcoin-core/Dockerfile"

cp -a \
  "$BACKUP/seymour-bitcoin-node-multiarch.yml" \
  "$ROOT/.github/workflows/seymour-bitcoin-node-multiarch.yml"

rm -rf "$ROOT/runtime-images/bitcoin-core/staged"

echo "SBP-062.1.1 rollback: PASS"
