#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
LATEST="$(find "$REPO/backups" -maxdepth 1 -type d -name 'sbp-071.1-*' | sort | tail -1)"

test -n "$LATEST" || {
  echo "ERROR: no SBP-071.1 backup found"
  exit 1
}

cp "$LATEST/seymour-monero-node-multiarch.yml" "$REPO/.github/workflows/seymour-monero-node-multiarch.yml"

echo "SBP-071.1 rollback: PASS"
echo "No blockchain runtime was modified."
