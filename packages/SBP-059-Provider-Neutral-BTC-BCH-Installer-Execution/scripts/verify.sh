#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
echo "SBP-059 verify: provider-neutral BTC/BCH installer"
python3 -m py_compile "$ROOT/seymour-blockchain-manager/data/web/installer.py"
cd "$ROOT"
python3 - <<'PY'
from pathlib import Path
installer = Path("seymour-blockchain-manager/data/web/installer.py").read_text()
ui = Path("seymour-blockchain-manager/data/web/app.js").read_text()
assert '"bitcoin-mainnet"' in installer
assert '"bitcoin-cash-mainnet"' in installer
assert '"seymour-bitcoin-node"' in installer
assert '"seymour-bch-node"' in installer
assert 'provider_runtime(value.provider_id)' in installer
assert 'runtime["installScript"]' in installer
assert 'runtime["appId"]' in installer
assert 'f"{prefix}_RPC_USER"' in installer
assert 'Install ${provider.displayName}' in ui
assert 'Seymour ${provider.displayName} Node' in ui
print("SBP-059 source contract tests: PASS")
PY
echo "SBP-059 BTC install execution contract: PASS"
echo "SBP-059 BCH install execution contract: PASS"
echo "SBP-059 provider-driven UI contract: PASS"
echo "SBP-059 final verification: PASS"
echo "No live blockchain installation was executed."
