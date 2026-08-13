#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"

echo "SBP-054 verify: shared blockchain install foundation"

python3 -m py_compile \
  "$ROOT"/shared/blockchain_install/*.py

echo
echo "===== STANDARD-LIBRARY CONTRACT TESTS ====="

PYTHONPATH="$ROOT" python3 - <<'PY'
from pathlib import Path
from tempfile import TemporaryDirectory

from shared.blockchain_install import (
    HostProfile,
    StorageTarget,
    StorageTargetType,
    capacity_policy,
    evaluate,
    probe_writable,
    target_from_path,
)

provider = {
    "providerId": "bitcoin-mainnet",
    "supportedArchitectures": ["amd64", "arm64"],
    "estimatedDiskBytes": 800_000_000_000,
}

host = HostProfile(
    hostname="umbrel-test",
    architecture="amd64",
    cpu_count=4,
    memory_total_bytes=8_000_000_000,
    docker_available=True,
    umbrel_available=True,
)

policy = capacity_policy(800_000_000_000)

assert policy.reserve_bytes == 160_000_000_000
assert policy.required_bytes == 960_000_000_000

remote = StorageTarget(
    target_id="remote-test",
    target_type=StorageTargetType.REMOTE,
    host="umbrel-test",
    path="/mnt/seymour-btc",
    filesystem="nfs4",
    source="192.168.1.155:/btc",
    total_bytes=5_500_000_000_000,
    used_bytes=200_000_000_000,
    free_bytes=5_300_000_000_000,
    writable=True,
    persistent=True,
    reachable=True,
    mount_point="/mnt/seymour-btc",
    remote_host="192.168.1.155",
)

result = evaluate(
    provider=provider,
    host=host,
    storage_target=remote,
)

assert result.compatible is True
assert result.storage_target["type"] == "remote"

small = StorageTarget(
    target_id="small",
    target_type=StorageTargetType.LOCAL,
    host="umbrel-test",
    path="/data",
    filesystem="ext4",
    source="/dev/sda",
    total_bytes=1_000_000_000_000,
    used_bytes=200_000_000_000,
    free_bytes=800_000_000_000,
    writable=True,
    persistent=True,
    reachable=True,
)

blocked = evaluate(
    provider=provider,
    host=host,
    storage_target=small,
)

assert blocked.compatible is False
assert blocked.checks["storageCapacityHealthy"] is False

with TemporaryDirectory() as tmp:
    path = Path(tmp)

    assert probe_writable(path) is True

    target = target_from_path(
        path,
        target_type=StorageTargetType.ATTACHED,
        filesystem="ext4",
        source="/dev/test",
        check_writable=True,
    )

    assert target.writable is True
    assert target.free_bytes > 0

print("SBP-054 standard-library contract tests: PASS")
PY

echo
echo "===== LIVE DISCOVERY SMOKE TEST ====="

PYTHONPATH="$ROOT" python3 - <<'PY'
from pathlib import Path

from shared.blockchain_install.storage import discover

targets = discover(
    local_path=Path("/"),
    check_writable=False,
)

print("targets:", len(targets))

for target in targets[:8]:
    print(target.to_dict())

assert targets
PY

echo
echo "SBP-054 provider-neutral preflight tests: PASS"
echo "SBP-054 local/attached/remote storage model: PASS"
echo "SBP-054 safety reserve policy: PASS"
echo "SBP-054 read-only discovery smoke test: PASS"
echo "SBP-054 final verification: PASS"
echo "No blockchain installation or storage migration was executed."
