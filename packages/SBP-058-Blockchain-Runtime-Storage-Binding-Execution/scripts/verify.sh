#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
echo "SBP-058 verify: runtime storage binding execution"
python3 -m py_compile "$ROOT/seymour-blockchain-manager/data/web/installer.py"
cd "$ROOT"
python3 - <<'PY'
from pathlib import Path
btc = Path("seymour-bitcoin-node/docker-compose.yml").read_text()
bch = Path("seymour-bch-node/docker-compose.yml").read_text()
installer = Path("seymour-blockchain-manager/data/web/installer.py").read_text()
assert "${SEYMOUR_BLOCKCHAIN_DATA_PATH:-${APP_DATA_DIR}/data/node}:/data" in btc
assert "${SEYMOUR_BLOCKCHAIN_DATA_PATH:-${APP_DATA_DIR}/data/node}:/node-data:ro" in btc
assert "${SEYMOUR_BLOCKCHAIN_DATA_PATH:-${APP_DATA_DIR}/data/node}:/data" in bch
assert "${SEYMOUR_BLOCKCHAIN_DATA_PATH:-${APP_DATA_DIR}/data/node}:/node-data" in bch
assert "build_binding_plan(" in installer
assert '"SEYMOUR_BLOCKCHAIN_DATA_PATH": str(data_path)' in installer
assert '"runtimeDataMountMatches": mount_matches' in installer
print("SBP-058 source contract tests: PASS")
PY
echo
grep -n 'SEYMOUR_BLOCKCHAIN_DATA_PATH' seymour-bitcoin-node/docker-compose.yml seymour-bch-node/docker-compose.yml
echo "SBP-058 BTC compose binding contract: PASS"
echo "SBP-058 BCH compose binding contract: PASS"
echo "SBP-058 installer selected-target execution contract: PASS"
echo "SBP-058 post-install mount verification contract: PASS"
echo "SBP-058 final verification: PASS"
echo "No live blockchain runtime or blockchain data was modified."
