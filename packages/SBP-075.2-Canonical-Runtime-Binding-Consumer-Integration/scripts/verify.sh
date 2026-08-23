#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
PKG="$ROOT/packages/SBP-075.2-Canonical-Runtime-Binding-Consumer-Integration"

EXPECTED="$PKG/payload/seymour-blockchain-manager/data/web/installer.py"
INSTALLED="$ROOT/seymour-blockchain-manager/data/web/installer.py"
CONTRACT="$ROOT/seymour-blockchain-manager/data/shared/blockchain_install/runtime_binding.py"

echo "===== SBP-075.2 VERIFY ====="

cmp -s "$EXPECTED" "$INSTALLED"
echo "PASS: installed installer matches package payload"

PYTHONDONTWRITEBYTECODE=1 \
python3 - "$INSTALLED" "$CONTRACT" <<'PY'
from pathlib import Path
import ast
import sys

installer = Path(sys.argv[1])
contract = Path(sys.argv[2])

ast.parse(installer.read_text())
ast.parse(contract.read_text())

print("PASS: Python syntax")
PY

PYTHONDONTWRITEBYTECODE=1 \
python3 - <<'PY'
import sys
from pathlib import Path

sys.path.insert(
    0,
    "seymour-blockchain-manager/data",
)

from shared.blockchain_install.runtime_binding import (
    RuntimeBinding,
    RuntimeBindingMode,
    serialize_runtime_binding,
)

single = RuntimeBinding(
    provider_id="monero-mainnet",
    app_id="seymour-monero-node",
    mode=RuntimeBindingMode.SINGLE_PATH,
    data_path=Path(
        "/mnt/seymour-storage/monero-mainnet"
    ),
)

single_text = serialize_runtime_binding(single)

assert (
    "SEYMOUR_BLOCKCHAIN_PROVIDER_ID=monero-mainnet\n"
    in single_text
)
assert (
    "SEYMOUR_BLOCKCHAIN_APP_ID=seymour-monero-node\n"
    in single_text
)
assert (
    "SEYMOUR_BLOCKCHAIN_DATA_PATH="
    "/mnt/seymour-storage/monero-mainnet\n"
    in single_text
)
assert "LOCAL_DATA_PATH" not in single_text
assert "BLOCKS_PATH" not in single_text

hybrid = RuntimeBinding(
    provider_id="bitcoin-cash-mainnet",
    app_id="seymour-bch-node",
    mode=RuntimeBindingMode.HYBRID_BLOCKS,
    local_data_path=Path(
        "/home/umbrel/umbrel/app-data/"
        "seymour-bch-node/data/node"
    ),
    blocks_path=Path(
        "/mnt/seymour-storage/"
        "bitcoin-cash-mainnet/blocks"
    ),
)

hybrid_text = serialize_runtime_binding(hybrid)

assert (
    "SEYMOUR_BLOCKCHAIN_PROVIDER_ID="
    "bitcoin-cash-mainnet\n"
    in hybrid_text
)
assert (
    "SEYMOUR_BLOCKCHAIN_APP_ID="
    "seymour-bch-node\n"
    in hybrid_text
)
assert "SEYMOUR_BLOCKCHAIN_DATA_PATH=" not in hybrid_text
assert (
    "SEYMOUR_BLOCKCHAIN_LOCAL_DATA_PATH="
    in hybrid_text
)
assert (
    "SEYMOUR_BLOCKCHAIN_BLOCKS_PATH="
    in hybrid_text
)

print("PASS: single-path serialization")
print("PASS: hybrid-blocks serialization")
PY

echo
echo "===== LIVE RUNTIME NON-INTERFERENCE ====="

if sudo docker inspect \
  seymour-monero-node_node_1 \
  --format \
  'status={{.State.Status}} health={{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}} restarts={{.RestartCount}}'
then
  :
else
  echo "WARNING: live Monero observation unavailable"
fi

echo
echo "SBP-075.2 VERIFY PASS"
