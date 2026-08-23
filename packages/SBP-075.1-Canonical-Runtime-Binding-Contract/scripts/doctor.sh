#!/usr/bin/env bash
set -euo pipefail

PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "===== SBP-075.1 DOCTOR ====="

python3 -m py_compile \
  "$PKG/payload/shared/blockchain_install/runtime_binding.py"

echo "PASS: Python syntax"

python3 - "$PKG" <<'PY'
from pathlib import Path
import importlib.util
import sys

pkg = Path(sys.argv[1])

path = (
    pkg
    / "payload/shared/blockchain_install/runtime_binding.py"
)

spec = importlib.util.spec_from_file_location(
    "runtime_binding_contract",
    path,
)

module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

single = module.RuntimeBinding(
    provider_id="monero-mainnet",
    app_id="seymour-monero-node",
    mode=module.RuntimeBindingMode.SINGLE_PATH,
    data_path=Path(
        "/mnt/seymour-storage/monero-mainnet"
    ),
)

text = module.serialize_runtime_binding(single)

assert (
    "SEYMOUR_BLOCKCHAIN_PROVIDER_ID=monero-mainnet"
    in text
)
assert (
    "SEYMOUR_BLOCKCHAIN_APP_ID=seymour-monero-node"
    in text
)
assert (
    "SEYMOUR_BLOCKCHAIN_DATA_PATH="
    "/mnt/seymour-storage/monero-mainnet"
    in text
)
assert "LOCAL_DATA_PATH" not in text
assert "BLOCKS_PATH" not in text

hybrid = module.RuntimeBinding(
    provider_id="bitcoin-cash-mainnet",
    app_id="seymour-bch-node",
    mode=module.RuntimeBindingMode.HYBRID_BLOCKS,
    local_data_path=Path(
        "/home/umbrel/umbrel/app-data/"
        "seymour-bch-node/data/node"
    ),
    blocks_path=Path(
        "/mnt/seymour-storage/"
        "bitcoin-cash-mainnet/blocks"
    ),
)

text = module.serialize_runtime_binding(hybrid)

assert (
    "SEYMOUR_BLOCKCHAIN_LOCAL_DATA_PATH="
    in text
)
assert (
    "SEYMOUR_BLOCKCHAIN_BLOCKS_PATH="
    in text
)
assert "SEYMOUR_BLOCKCHAIN_DATA_PATH=" not in text

print("PASS: single-path contract")
print("PASS: hybrid-blocks contract")
PY

echo "SBP-075.1 DOCTOR PASS"
