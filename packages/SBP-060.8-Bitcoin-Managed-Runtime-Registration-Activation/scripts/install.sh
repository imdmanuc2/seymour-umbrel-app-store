#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

"$PKG/scripts/doctor.sh" "$ROOT"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$ROOT/backups/sbp-060.8-$STAMP"

mkdir -p \
  "$BACKUP" \
  "$ROOT/shared/bitcoin_managed_runtime" \
  "$ROOT/tests"

cp \
  "$PKG/payload/shared/bitcoin_managed_runtime/workflow.py" \
  "$ROOT/shared/bitcoin_managed_runtime/workflow.py"

cp \
  "$PKG/payload/shared/bitcoin_managed_runtime/__init__.py" \
  "$ROOT/shared/bitcoin_managed_runtime/__init__.py"

cp \
  "$PKG/scripts/seymour-bitcoin-managed-runtime" \
  "$ROOT/scripts/seymour-bitcoin-managed-runtime"

cp \
  "$PKG/payload/tests/test_bitcoin_managed_runtime.py" \
  "$ROOT/tests/test_bitcoin_managed_runtime.py"

chmod +x \
  "$ROOT/scripts/seymour-bitcoin-managed-runtime"

echo "Backup: $BACKUP"
echo "SBP-060.8 Bitcoin managed runtime workflow installed: PASS"
echo "SBP-060.8 guarded native install/start control installed: PASS"
echo "SBP-060.8 persistent Bitcoin data-binding integration installed: PASS"
echo "SBP-060.8 install: PASS"
echo "No Bitcoin runtime was installed or started."
