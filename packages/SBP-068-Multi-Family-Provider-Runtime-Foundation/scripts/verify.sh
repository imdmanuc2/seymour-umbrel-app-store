#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"

CATALOG="$REPO/shared/provider_catalog/providers.v1.json"
MODEL="$REPO/shared/provider_catalog/catalog.py"

echo "SBP-068 verify: multi-family provider runtime foundation"

python3 -m py_compile "$MODEL"

PYTHONPATH="$REPO" python3 - "$CATALOG" <<'PY'
import sys
from pathlib import Path

from shared.provider_catalog.catalog import ProviderCatalog

catalog = ProviderCatalog.load(Path(sys.argv[1]))

btc = catalog.get("bitcoin-mainnet")
bch = catalog.get("bitcoin-cash-mainnet")
xmr = catalog.get("monero-mainnet")

assert btc.runtime is not None
assert bch.runtime is not None
assert xmr.runtime is not None

assert btc.runtime["appId"] == "seymour-bitcoin-node"
assert bch.runtime["appId"] == "seymour-bch-node"

assert xmr.family == "cryptonote"
assert xmr.implementation == "monerod"
assert xmr.runtime["appId"] == "seymour-monero-node"
assert xmr.runtime["service"] == "node"
assert xmr.runtime["dataDirectory"] == "/data"
assert xmr.runtime["rpc"]["port"] == 18081
assert xmr.runtime["rpc"]["authentication"] == "none"
assert xmr.runtime["p2p"]["port"] == 18080

assert xmr.availability == "planned"
assert xmr.selectable is False
assert xmr.production_image is None

print("SBP-068 Bitcoin runtime metadata contract: PASS")
print("SBP-068 BCH runtime metadata contract: PASS")
print("SBP-068 Monero runtime identity contract: PASS")
print("SBP-068 Monero remains non-selectable: PASS")
PY

if grep -q 'SBP-007 requires exactly one live provider' "$MODEL"; then
  echo "ERROR: obsolete single-live-provider invariant remains"
  exit 1
fi

if grep -q 'Bitcoin Cash must remain the live provider' "$MODEL"; then
  echo "ERROR: obsolete BCH-only invariant remains"
  exit 1
fi

echo "SBP-068 obsolete single-provider invariant removed: PASS"

grep -q 'provider_id' \
  "$REPO/shared/managed_runtime/models.py"

grep -q 'provider_id' \
  "$REPO/shared/blockchain_install/binding.py"

echo "SBP-068 provider-neutral managed runtime contract: PASS"
echo "SBP-068 provider-neutral storage contract: PASS"

for path in \
  "$REPO/seymour-blockchain-manager/data/catalog/providers.v1.json" \
  "$REPO/seymour-blockchain-manager/data/shared/provider_catalog/providers.v1.json"
do
  cmp -s "$CATALOG" "$path" || {
    echo "ERROR: provider catalog copies differ"
    exit 1
  }
done

echo "SBP-068 catalog synchronization contract: PASS"

echo "SBP-068 final multi-family provider foundation: PASS"
echo "Monero was not activated or installed."
echo "No blockchain runtime was modified."
