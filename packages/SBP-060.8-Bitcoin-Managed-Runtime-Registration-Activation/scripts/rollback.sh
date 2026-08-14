#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"

rm -rf \
  "$ROOT/shared/bitcoin_managed_runtime"

rm -f \
  "$ROOT/scripts/seymour-bitcoin-managed-runtime" \
  "$ROOT/tests/test_bitcoin_managed_runtime.py"

echo "SBP-060.8 rollback: PASS"
echo "No Bitcoin runtime or blockchain data was modified."
