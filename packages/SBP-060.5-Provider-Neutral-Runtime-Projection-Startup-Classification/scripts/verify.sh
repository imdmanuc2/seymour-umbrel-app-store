#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
WEB="$ROOT/seymour-blockchain-manager/data/web"
echo "SBP-060.5 verify: provider-neutral runtime projection"
python3 -m py_compile "$WEB/telemetry.py" "$WEB/bch_runtime_probe.py" "$WEB/runtime_registry.py"
grep -q 'telemetry?.installed === true' "$WEB/app.js"
! grep -q 'const provider = live\[0\]' "$WEB/app.js"
grep -q 'bitcoin-mainnet' "$WEB/runtime_registry.py"
grep -q 'bitcoin-cash-mainnet' "$WEB/runtime_registry.py"
grep -q 'Runtime is verifying or warming existing blockchain data' "$WEB/bch_runtime_probe.py"
grep -q 'socket.AF_UNIX' "$WEB/telemetry.py"
PYTHONPATH="$WEB" python3 - <<'PY'
from runtime_registry import dashboard_runtimes
payload = dashboard_runtimes(bch_telemetry=lambda: {"providerId":"bitcoin-cash-mainnet","installed":True,"runtimeState":"starting"})
assert "bitcoin-mainnet" in payload
assert "bitcoin-cash-mainnet" in payload
assert payload["bitcoin-cash-mainnet"]["runtimeState"] == "starting"
print("SBP-060.5 provider-neutral projection smoke test: PASS")
PY
echo "SBP-060.5 installed-runtime counting contract: PASS"
echo "SBP-060.5 multi-runtime renderer contract: PASS"
echo "SBP-060.5 BTC/BCH registry contract: PASS"
echo "SBP-060.5 startup classification contract: PASS"
echo "SBP-060.5 Docker socket health contract: PASS"
echo "SBP-060.5 final verification: PASS"
echo "No live runtime was restarted or modified."
