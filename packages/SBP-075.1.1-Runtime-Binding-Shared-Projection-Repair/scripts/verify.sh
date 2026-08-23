#!/usr/bin/env bash
set -euo pipefail

PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT="$(cd "$PKG/../.." && pwd)"

CANONICAL="$ROOT/shared/blockchain_install/runtime_binding.py"
MANAGER="$ROOT/seymour-blockchain-manager/data/shared/blockchain_install/runtime_binding.py"
PAYLOAD="$PKG/payload/shared/blockchain_install/runtime_binding.py"

echo "===== SBP-075.1.1 VERIFY ====="

test -f "$CANONICAL"
test -f "$MANAGER"

python3 - "$CANONICAL" "$MANAGER" <<'PYTHON'
from pathlib import Path
import sys

for filename in sys.argv[1:]:
    source = Path(filename).read_text()
    compile(source, filename, "exec")

print("PASS: Python syntax")
PYTHON

cmp "$PAYLOAD" "$CANONICAL"
cmp "$CANONICAL" "$MANAGER"

echo "PASS: canonical and Manager projections identical"

PYTHONPATH="$ROOT/seymour-blockchain-manager/data" \
python3 - <<'PY'
from pathlib import Path

from shared.blockchain_install.runtime_binding import (
    RuntimeBinding,
    RuntimeBindingMode,
    serialize_runtime_binding,
)

binding = RuntimeBinding(
    provider_id="monero-mainnet",
    app_id="seymour-monero-node",
    mode=RuntimeBindingMode.SINGLE_PATH,
    data_path=Path(
        "/mnt/seymour-storage/monero-mainnet"
    ),
)

text = serialize_runtime_binding(binding)

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

print("PASS: Blockchain Manager import contract")
PY

echo
echo "===== LIVE RUNTIME NON-INTERFERENCE ====="

sudo docker inspect seymour-monero-node_node_1 \
  --format 'status={{.State.Status}} health={{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}} restarts={{.RestartCount}}'

echo
echo "SBP-075.1.1 VERIFY PASS"
