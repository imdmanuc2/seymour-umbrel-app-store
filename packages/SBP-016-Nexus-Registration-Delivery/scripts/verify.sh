#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-/home/umbrel/seymour-umbrel-app-store-git}"

export PYTHONPATH="$REPO:$REPO/shared:$REPO/tests${PYTHONPATH:+:$PYTHONPATH}"

for test in \
  test_nexus_integration.py \
  test_nexus_api_contract.py \
  test_nexus_delivery.py \
  test_nexus_delivery_retry.py \
  test_nexus_delivery_api.py; do
  python3 "$REPO/tests/$test"
done

python3 -m py_compile \
  "$REPO/seymour-blockchain-manager/data/web/nexus_delivery.py" \
  "$REPO/seymour-blockchain-manager/data/web/app.py"

grep -q '/api/nexus/delivery/status' \
  "$REPO/seymour-blockchain-manager/data/web/app.py"

grep -q 'NEXUS_DELIVERY_EVIDENCE_PATH' \
  "$REPO/seymour-blockchain-manager/docker-compose.yml"

echo "SBP-016 authenticated delivery verification: PASS"
echo "SBP-016 idempotency verification: PASS"
echo "SBP-016 retry and backoff verification: PASS"
echo "SBP-016 delivery timeout verification: PASS"
echo "SBP-016 last-known status verification: PASS"
echo "SBP-016 failure evidence verification: PASS"
echo "SBP-016 dry-run verification: PASS"
echo "SBP-016 final verification: PASS"
