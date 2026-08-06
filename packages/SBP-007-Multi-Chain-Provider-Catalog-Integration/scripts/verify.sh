#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
export PYTHONPATH="$REPO${PYTHONPATH:+:$PYTHONPATH}"

python3 "$REPO/tests/test_provider_catalog.py"
python3 "$REPO/tests/test_bch_catalog_compatibility.py"

"$REPO/scripts/seymour-provider-catalog" api |
python3 -c '
import json,sys
data=json.load(sys.stdin)
assert data["providerCount"] == 9
assert data["liveProviderCount"] == 1
assert data["frozen"] is True
'

"$REPO/scripts/seymour-provider-catalog" selectable |
python3 -c '
import json,sys
data=json.load(sys.stdin)
assert len(data) == 1
assert data[0]["providerId"] == "bitcoin-cash-mainnet"
assert data[0]["selectable"] is True
'

"$REPO/scripts/seymour-provider-catalog" \
  validate-selection \
  bitcoin-cash-mainnet \
  --architecture arm64 |
python3 -c '
import json,sys
data=json.load(sys.stdin)
assert data["valid"] is True
assert data["provider"]["providerId"] == "bitcoin-cash-mainnet"
'

if "$REPO/scripts/seymour-provider-catalog" \
  validate-selection \
  bitcoin-mainnet \
  --architecture arm64 \
  >/tmp/sbp007-invalid.out \
  2>/tmp/sbp007-invalid.err; then
  echo "Planned Bitcoin provider was incorrectly selectable." >&2
  exit 1
fi

grep -q \
  'not yet available for installation' \
  /tmp/sbp007-invalid.err

echo "SBP-007 provider catalog verification: PASS"
echo "SBP-007 selection guardrail verification: PASS"
echo "SBP-007 BCH preservation verification: PASS"
echo "SBP-007 final verification: PASS"
