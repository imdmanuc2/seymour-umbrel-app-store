#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$ROOT"

TARGET="/home/umbrel/umbrel/app-data/seymour-blockchain-manager/data/shared/blockchain_install"
BINDING="/home/umbrel/umbrel/app-data/seymour-blockchain-manager/data/evidence/runtime-bindings/seymour-monero-node.env"

echo "===== SBP-075.4 VERIFY ====="

for FILE in \
  runtime_binding.py \
  runtime_binding_materializer.py \
  runtime_binding_reconciler.py
do
  test -f "$TARGET/$FILE"
  echo "PASS: installed $FILE"
done

PYTHONPATH="/home/umbrel/umbrel/app-data/seymour-blockchain-manager/data" \
python3 - <<'PY'
from pathlib import Path

from shared.blockchain_install.runtime_binding_reconciler import (
    reconcile_installed_runtime_binding,
)

result = reconcile_installed_runtime_binding(
    data_directory=Path("/home/umbrel/umbrel"),
    binding_path=Path(
        "/home/umbrel/umbrel/app-data/"
        "seymour-blockchain-manager/data/evidence/"
        "runtime-bindings/seymour-monero-node.env"
    ),
)

print(result)

assert result["providerId"] == "monero-mainnet"
assert result["appId"] == "seymour-monero-node"
assert result["anchorsResolved"] == 2
assert result["anchorsExpected"] == 2
assert result["changed"] is False

print("PASS: installed Monero binding reconciles idempotently")
PY

sudo docker inspect \
  seymour-monero-node_node_1 \
  --format 'status={{.State.Status}} health={{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}} restarts={{.RestartCount}}'

echo "PASS: verify"
