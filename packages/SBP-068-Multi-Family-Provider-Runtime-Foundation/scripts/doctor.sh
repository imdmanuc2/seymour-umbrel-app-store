#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"

CATALOG="$REPO/shared/provider_catalog/providers.v1.json"
MODEL="$REPO/shared/provider_catalog/catalog.py"
MANAGED="$REPO/shared/managed_runtime/models.py"
BINDING="$REPO/shared/blockchain_install/binding.py"

echo "SBP-068 doctor: checking multi-family provider prerequisites"

for f in "$CATALOG" "$MODEL" "$MANAGED" "$BINDING"; do
  test -f "$f" || {
    echo "ERROR: missing $f"
    exit 1
  }
done

python3 -m py_compile \
  "$MODEL" \
  "$MANAGED" \
  "$BINDING"

grep -q '"providerId": "monero-mainnet"' "$CATALOG"
grep -q '"family": "cryptonote"' "$CATALOG"
grep -q '"implementation": "monerod"' "$CATALOG"

echo "SBP-068 Monero catalog prerequisite: PASS"
echo "SBP-068 compile prerequisites: PASS"
echo "SBP-068 doctor: PASS"
