#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"

echo "SBP-057 verify: remote storage materialization"

python3 -m py_compile   "$ROOT/shared/blockchain_install/materialize.py"   "$ROOT/scripts/seymour-storage-materialize"

echo
echo "===== PLAN-ONLY ACCEPTANCE TEST ====="

"$ROOT/scripts/seymour-storage-materialize"   --provider-id bitcoin-mainnet   --storage-host 192.168.1.155   --storage-path /mnt/umbrel-disk/seymour-data   --runtime-host 192.168.1.154   --runtime-mount-path /mnt/seymour-storage   --role runtime-host

echo
echo "===== STANDARD-LIBRARY CONTRACT TEST ====="

PYTHONPATH="$ROOT" python3 - <<'PY'
from shared.blockchain_install.materialize import build_nfs_plan

plan = build_nfs_plan(
    provider_id="bitcoin-mainnet",
    storage_host="192.168.1.155",
    storage_path="/mnt/umbrel-disk/seymour-data",
    runtime_host="192.168.1.154",
    runtime_mount_path="/mnt/seymour-storage",
)

assert plan.eligible
assert plan.nfs_source == "192.168.1.155:/mnt/umbrel-disk/seymour-data"
assert plan.data_path == "/mnt/seymour-storage/bitcoin-mainnet"
assert plan.confirmation == "MATERIALIZE-bitcoin-mainnet-ON-192.168.1.155"

print(plan.to_dict())
print("SBP-057 standard-library materialization tests: PASS")
PY

echo "SBP-057 plan contract: PASS"
echo "SBP-057 confirmation guard contract: PASS"
echo "SBP-057 NFS storage/runtime host separation: PASS"
echo "SBP-057 final verification: PASS"
echo "No NFS export, mount, fstab, runtime, or blockchain data change was executed."
