#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"

echo "SBP-060 verify: Bitcoin provider activation"
python3 -m py_compile "$ROOT/seymour-blockchain-manager/data/web/app.py"

cd "$ROOT"
python3 - <<'PY'
from pathlib import Path
import json

for catalog in (
    Path("shared/provider_catalog/providers.v1.json"),
    Path("seymour-blockchain-manager/data/catalog/providers.v1.json"),
):
    data = json.loads(catalog.read_text())
    btc = next(x for x in data["providers"] if x["providerId"] == "bitcoin-mainnet")
    print(catalog)
    print(json.dumps(btc, indent=2))
    assert btc["availability"] == "live"
    assert btc["selectable"] is True
    assert btc["productionImage"] == "ghcr.io/imdmanuc2/seymour-bitcoin-node:29.0.0"
    assert btc["installAction"]["appId"] == "seymour-bitcoin-node"
    assert btc["installAction"]["confirmation"] == "INSTALL-seymour-bitcoin-node"

app = Path("seymour-blockchain-manager/data/web/app.py").read_text()
js = Path("seymour-blockchain-manager/data/web/app.js").read_text()

assert 'provider_id=provider_id' in app
assert 'storage_target_id=storage_target_id' in app
assert '/api/install/preflight?providerId=' in js

print("SBP-060 source contract tests: PASS")
PY

echo "SBP-060 Bitcoin provider selectable contract: PASS"
echo "SBP-060 Bitcoin production image contract: PASS"
echo "SBP-060 provider-specific preflight contract: PASS"
echo "SBP-060 final verification: PASS"
echo "No live Bitcoin installation was executed."
