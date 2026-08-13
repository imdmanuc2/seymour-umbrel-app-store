#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"

echo "SBP-056 verify: blockchain storage binding plan"

python3 -m py_compile   "$ROOT/shared/blockchain_install/binding.py"   "$ROOT/shared/blockchain_install/__init__.py"

cd "$ROOT"

PYTHONPATH="$ROOT" python3 - <<'PY'
from shared.blockchain_install import (
    StorageTarget,
    StorageTargetType,
)
from shared.blockchain_install.binding import build_binding_plan, provider_storage_name

attached = StorageTarget(
    target_id="attached-test",
    target_type=StorageTargetType.ATTACHED,
    host="debian",
    path="/mnt/umbrel-disk",
    filesystem="ext4",
    source="/dev/sdb1",
    total_bytes=5_500_000_000_000,
    used_bytes=100_000_000_000,
    free_bytes=5_400_000_000_000,
    writable=True,
    persistent=True,
    reachable=True,
)

plan = build_binding_plan(
    provider_id="bitcoin-mainnet",
    runtime_host="192.168.1.154",
    storage_target=attached,
)

print(plan.to_dict())
assert plan.eligible
assert plan.data_path == "/mnt/umbrel-disk/seymour-data/bitcoin-mainnet"

remote = StorageTarget(
    target_id="remote-test",
    target_type=StorageTargetType.REMOTE,
    host="umbrel",
    path="/mnt/seymour-remote",
    filesystem="nfs4",
    source="192.168.1.155:/mnt/umbrel-disk/seymour-data",
    total_bytes=5_500_000_000_000,
    used_bytes=100_000_000_000,
    free_bytes=5_400_000_000_000,
    writable=True,
    persistent=True,
    reachable=True,
    remote_host="192.168.1.155",
)

remote_plan = build_binding_plan(
    provider_id="bitcoin-mainnet",
    runtime_host="192.168.1.154",
    storage_target=remote,
)

print(remote_plan.to_dict())
assert remote_plan.eligible
assert remote_plan.storage_type == "remote"
assert remote_plan.remote_host == "192.168.1.155"

try:
    provider_storage_name("../bitcoin")
except ValueError:
    pass
else:
    raise AssertionError("unsafe provider path accepted")

print("SBP-056 standard-library binding tests: PASS")
PY

echo "SBP-056 attached storage binding contract: PASS"
echo "SBP-056 remote storage binding contract: PASS"
echo "SBP-056 safe provider path contract: PASS"
echo "SBP-056 final verification: PASS"
echo "No live blockchain runtime or storage mount was modified."
