#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-/home/umbrel/seymour-umbrel-app-store-git}"

export PYTHONPATH="$REPO:$REPO/shared${PYTHONPATH:+:$PYTHONPATH}"

python3 "$REPO/tests/test_provider_catalog.py"
python3 "$REPO/tests/test_bch_catalog_compatibility.py"
python3 "$REPO/tests/test_blockchain_manager_ui.py"
python3 "$REPO/tests/test_blockchain_manager_catalog.py"

python3 -m py_compile \
  "$REPO/seymour-blockchain-manager/data/web/app.py"

grep -q \
  'id: seymour-blockchain-manager' \
  "$REPO/seymour-blockchain-manager/umbrel-app.yml"

grep -q \
  'port: 8570' \
  "$REPO/seymour-blockchain-manager/umbrel-app.yml"

grep -q \
  'bitcoin-cash-mainnet' \
  "$REPO/seymour-blockchain-manager/data/catalog/providers.v1.json"

echo "SBP-008 blockchain manager UI verification: PASS"
echo "SBP-008 catalog API verification: PASS"
echo "SBP-008 BCH action contract verification: PASS"
echo "SBP-008 final verification: PASS"
