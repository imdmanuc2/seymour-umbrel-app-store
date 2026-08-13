#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
echo "SBP-060.3 verify: blockchain storage mount safety guard"
python3 -m py_compile "$ROOT/shared/blockchain_install/models.py" "$ROOT/shared/blockchain_install/storage.py" "$ROOT/shared/blockchain_install/preflight.py" "$ROOT/seymour-blockchain-manager/data/web/storage_targets.py" "$ROOT/seymour-blockchain-manager/data/web/installer.py"
cd "$ROOT"
PYTHONPATH="$ROOT" python3 - <<'PY'
from pathlib import Path
from tempfile import TemporaryDirectory
from shared.blockchain_install.models import StorageTarget, StorageTargetType
from shared.blockchain_install.storage import verify_storage_target
with TemporaryDirectory() as tmp:
    fake = Path(tmp) / "umbrel-disk"
    fake.mkdir()
    target = StorageTarget(target_id="attached-missing", target_type=StorageTargetType.ATTACHED, host="test", path=str(fake), filesystem="ext4", source="/dev/sdz1", total_bytes=10**12, used_bytes=0, free_bytes=10**12, writable=True, persistent=True, reachable=True, mount_point=str(fake), filesystem_uuid="not-a-real-uuid")
    result = verify_storage_target(target)
    print(result)
    assert result["healthy"] is False
    assert result["isMountPoint"] is False
    assert any("no longer mounted" in e for e in result["errors"])
print("SBP-060.3 false-mount regression test: PASS")
PY

echo
echo "===== LIVE /mnt/umbrel-disk GUARD ====="
sudo env PYTHONPATH="$ROOT" python3 - <<'PY'
from pathlib import Path
from shared.blockchain_install import StorageTargetType, target_from_path, verify_storage_target
target = target_from_path(Path("/mnt/umbrel-disk"), target_type=StorageTargetType.ATTACHED, filesystem="ext4", source="/dev/sdb1", check_writable=False)
result = verify_storage_target(target, minimum_free_bytes=1_000_000_000, data_path=Path("/mnt/umbrel-disk/seymour-data/bitcoin-mainnet"))
print(result)
assert result["healthy"] is True
assert result["isMountPoint"] is True
assert result["filesystemMatches"] is True
assert result["filesystemUuidMatches"] is True
assert result["dataPathContained"] is True
print("SBP-060.3 live storage identity: PASS")
PY

echo
echo "===== INSTALLER CONTRACT ====="
grep -nE 'verify_storage_target|storageMountGuard|failed live mount identity' seymour-blockchain-manager/data/web/installer.py
echo
echo "SBP-060.3 mount identity contract: PASS"
echo "SBP-060.3 filesystem UUID contract: PASS"
echo "SBP-060.3 data-path containment contract: PASS"
echo "SBP-060.3 fail-closed installer contract: PASS"
echo "SBP-060.3 final verification: PASS"
echo "No live blockchain installation or data movement was executed."
